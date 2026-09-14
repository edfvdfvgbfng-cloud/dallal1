"""خدمات الإشعارات"""
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .models import Notification, NotificationRecipient, NotificationLog, Broker


class NotificationService:
    """خدمة إرسال الإشعارات"""
    
    def send_notification(self, notification):
        """إرسال إشعار للمستلمين المستهدفين"""
        # Get target users
        users = self.get_target_users(notification)
        
        # Create recipients
        recipients = []
        for user in users:
            recipient, created = NotificationRecipient.objects.get_or_create(
                notification=notification,
                user=user
            )
            if created:
                recipients.append(recipient)
        
        # Mark notification as sent
        notification.mark_as_sent()
        
        # Create log
        self.create_log(notification, len(recipients))
        
        return recipients
    
    def get_target_users(self, notification):
        """الحصول على المستخدمين المستهدفين"""
        from django.contrib.auth.models import User
        from django.db.models import Count
        
        users = User.objects.all()
        
        # Filter by user type
        if notification.target_all_users:
            pass  # All users
        elif notification.target_all_brokers:
            users = users.filter(broker_profile__isnull=False)
        elif notification.target_all_admins:
            users = users.filter(is_staff=True)
        elif notification.target_office_owners:
            users = users.filter(broker_profile__has_office=True)
        elif notification.target_managers:
            users = users.filter(broker_profile__role='manager')
        elif notification.target_active_users:
            users = users.filter(last_login__gte=timezone.now() - timezone.timedelta(days=30))
        elif notification.target_new_users:
            users = users.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=7))
        elif notification.target_inactive_users:
            users = users.filter(last_login__lt=timezone.now() - timezone.timedelta(days=30))
        
        # Filter by account type
        if notification.target_account_type:
            if notification.target_account_type == 'broker':
                users = users.filter(broker_profile__isnull=False)
            elif notification.target_account_type == 'user':
                users = users.filter(user_profile__isnull=False)
        
        # Filter by subscription type
        if notification.target_subscription_type:
            from .models import BrokerPlanSubscription
            broker_ids = BrokerPlanSubscription.objects.filter(
                plan__name=notification.target_subscription_type,
                status='active'
            ).values_list('broker_id', flat=True)
            users = users.filter(broker_profile__id__in=broker_ids)
        
        # Filter by account status
        if notification.target_account_status:
            if notification.target_account_status == 'active':
                users = users.filter(is_active=True)
            elif notification.target_account_status == 'inactive':
                users = users.filter(is_active=False)
        
        # Filter by properties ownership
        if notification.target_has_properties is not None:
            if notification.target_has_properties:
                users = users.filter(
                    Q(broker_profile__properties__isnull=False) |
                    Q(user_profile__properties__isnull=False)
                ).distinct()
            else:
                users = users.exclude(
                    Q(broker_profile__properties__isnull=False) |
                    Q(user_profile__properties__isnull=False)
                )
        
        # Filter by location
        if notification.target_governorate:
            users = users.filter(
                Q(user_profile__governorate=notification.target_governorate) |
                Q(broker_profile__governorate=notification.target_governorate)
            )
        
        if notification.target_city:
            users = users.filter(
                Q(user_profile__city=notification.target_city) |
                Q(broker_profile__city=notification.target_city)
            )
        
        if notification.target_area:
            users = users.filter(
                Q(user_profile__area=notification.target_area) |
                Q(broker_profile__area=notification.target_area)
            )
        
        # Filter by property type
        if notification.target_property_type:
            from .models import Property
            property_owners = Property.objects.filter(
                property_type=notification.target_property_type
            ).values_list('owner', flat=True)
            users = users.filter(id__in=property_owners)
        
        # Filter by broker criteria
        if notification.target_premium_brokers:
            from .models import BrokerPlanSubscription
            broker_ids = BrokerPlanSubscription.objects.filter(
                plan__name__icontains='premium',
                status='active'
            ).values_list('broker_id', flat=True)
            users = users.filter(broker_profile__id__in=broker_ids)
        
        if notification.target_min_properties:
            from .models import Property
            broker_ids = Property.objects.filter(
                broker__isnull=False
            ).values('broker').annotate(
                count=Count('id')
            ).filter(
                count__gte=notification.target_min_properties
            ).values_list('broker', flat=True)
            users = users.filter(broker_profile__id__in=broker_ids)
        
        if notification.target_min_rating:
            from .models import BrokerRating
            broker_ids = BrokerRating.objects.filter(
                rating__gte=notification.target_min_rating
            ).values_list('broker_id', flat=True)
            users = users.filter(broker_profile__id__in=broker_ids)
        
        return users.distinct()
    
    def create_log(self, notification, sent_count):
        """إنشاء سجل الإرسال"""
        log = NotificationLog.objects.create(
            notification=notification,
            total_sent=sent_count,
            total_delivered=sent_count,  # Assuming all delivered for now
            total_read=notification.get_read_count(),
            total_clicked=notification.get_clicked_count(),
        )
        
        # Calculate rates
        if sent_count > 0:
            log.delivery_rate = (log.total_delivered / sent_count) * 100
            log.read_rate = (log.total_read / sent_count) * 100
            log.click_rate = (log.total_clicked / sent_count) * 100
            log.save()
        
        return log
    
    def send_to_user(self, user, title, description, notification_type='info', **kwargs):
        """إرسال إشعار لمستخدم محدد"""
        notification = Notification.objects.create(
            title=title,
            description=description,
            notification_type=notification_type,
            **kwargs
        )
        
        recipient = NotificationRecipient.objects.create(
            notification=notification,
            user=user
        )
        
        notification.mark_as_sent()
        
        return recipient
    
    def send_to_users(self, users, title, description, notification_type='info', **kwargs):
        """إرسال إشعار لمجموعة مستخدمين"""
        notification = Notification.objects.create(
            title=title,
            description=description,
            notification_type=notification_type,
            **kwargs
        )
        
        recipients = []
        for user in users:
            recipient = NotificationRecipient.objects.create(
                notification=notification,
                user=user
            )
            recipients.append(recipient)
        
        notification.mark_as_sent()
        
        return recipients


# ==================== Subscription Security Service ====================

class SubscriptionService:
    """خدمة مركزية للتحقق من الاشتراكات وتأمين النظام"""
    
    @staticmethod
    def get_broker_subscription(broker):
        """الحصول على الاشتراك النشط للدلال"""
        from django.db import transaction
        from .models import BrokerPlanSubscription
        
        return BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        ).select_related('plan').first()
    
    @staticmethod
    def is_subscription_active(subscription):
        """التحقق من أن الاشتراك نشط ولم ينتهِ"""
        if not subscription:
            return False
        return subscription.is_active()
    
    @staticmethod
    def can_add_property(broker):
        """التحقق من إمكانية إضافة عقار (مع الحماية من Race Conditions)"""
        from django.db import transaction
        from .models import BrokerPlanSubscription, Property

        if not broker:
            return False, "ملف الدلال غير موجود"

        # Force expiry side-effects server-side
        try:
            broker.check_subscription_status()
        except Exception:
            pass

        if getattr(broker, 'is_suspended', False):
            return False, "الحساب موقوف"
        if not getattr(broker, 'can_add_properties', True):
            return False, "غير مسموح بإضافة عقارات"

        with transaction.atomic():
            # Prefer advanced plan subscription when available
            subscription = BrokerPlanSubscription.objects.filter(
                broker=broker,
                status='active'
            ).select_for_update().select_related('plan').first()

            if subscription:
                if not subscription.is_active():
                    return False, "الاشتراك منتهي"
                if subscription.properties_used >= subscription.plan.max_properties:
                    return False, "تجاوزت الحد الأقصى للعقارات حسب الباقة"
                return True, "يمكن إضافة عقار"

            # Fallback: classic broker subscription fields
            if not broker.is_subscription_active():
                return False, "لا يوجد اشتراك نشط"

            limit = None
            if broker.subscription_plan_id:
                limit = broker.subscription_plan.ads_limit
            if limit is None:
                # Unlimited classic plan or no hard limit set
                return True, "يمكن إضافة عقار"

            used = Property.objects.filter(broker=broker).exclude(status__in=['expired', 'rejected']).count()
            if used >= limit:
                return False, f"تجاوزت الحد الأقصى للعقارات ({limit})"

            return True, "يمكن إضافة عقار"
    
    @staticmethod
    def increment_property_count(broker):
        """زيادة عداد العقارات (مع الحماية من Race Conditions)"""
        from django.db import transaction
        from django.db.models import F
        from .models import BrokerPlanSubscription, Property

        with transaction.atomic():
            subscription = BrokerPlanSubscription.objects.filter(
                broker=broker,
                status='active'
            ).select_for_update().first()

            if subscription:
                if subscription.properties_used >= subscription.plan.max_properties:
                    raise Exception("تجاوزت الحد الأقصى للعقارات")
                subscription.properties_used = F('properties_used') + 1
                subscription.save()
                subscription.refresh_from_db()
                return subscription.properties_used

            # Classic subscription fallback — re-validate before counting
            if not broker.is_subscription_active():
                raise Exception("لا يوجد اشتراك نشط")
            if broker.subscription_plan_id:
                limit = broker.subscription_plan.ads_limit
                used = Property.objects.filter(broker=broker).exclude(status__in=['expired', 'rejected']).count()
                if used >= limit:
                    raise Exception(f"تجاوزت الحد الأقصى للعقارات ({limit})")
            return Property.objects.filter(broker=broker).count()
    
    @staticmethod
    def decrement_property_count(broker):
        """تقليل عداد العقارات (مع الحماية من Race Conditions)"""
        from django.db import transaction
        from django.db.models import F
        from .models import BrokerPlanSubscription
        
        with transaction.atomic():
            subscription = BrokerPlanSubscription.objects.filter(
                broker=broker,
                status='active'
            ).select_for_update().first()
            
            if not subscription:
                return
            
            # Use F expression to prevent race conditions
            subscription.properties_used = F('properties_used') - 1
            subscription.save()
            
            # Ensure count doesn't go negative
            subscription.refresh_from_db()
            if subscription.properties_used < 0:
                subscription.properties_used = 0
                subscription.save()
    
    @staticmethod
    def can_add_auction(broker):
        """التحقق من إمكانية إضافة مزاد"""
        from django.db import transaction
        from .models import BrokerPlanSubscription
        
        with transaction.atomic():
            subscription = BrokerPlanSubscription.objects.filter(
                broker=broker,
                status='active'
            ).select_for_update().select_related('plan').first()
            
            if not subscription:
                return False, "لا يوجد اشتراك نشط"
            
            if not subscription.is_active():
                return False, "الاشتراك منتهي"
            
            if subscription.auctions_used >= subscription.plan.max_auctions:
                return False, "تجاوزت الحد الأقصى للمزادات"
            
            return True, "يمكن إضافة مزاد"
    
    @staticmethod
    def log_bypass_attempt(user, action, ip_address, user_agent, details):
        """تسجيل محاولة تجاوز الاشتراك"""
        from .models import SecurityLog
        
        SecurityLog.objects.create(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            severity='high'
        )
    
    @staticmethod
    def check_subscription_before_action(user, action, ip_address=None, user_agent=None):
        """التحقق من الاشتراك قبل أي إجراء"""
        from .models import Broker
        
        broker = Broker.objects.filter(user=user).first()
        if not broker:
            return False, "ليس دلالاً"
        
        subscription = SubscriptionService.get_broker_subscription(broker)
        
        if not subscription:
            SubscriptionService.log_bypass_attempt(
                user, action, ip_address, user_agent,
                "محاولة إجراء بدون اشتراك نشط"
            )
            return False, "لا يوجد اشتراك نشط"
        
        if not SubscriptionService.is_subscription_active(subscription):
            SubscriptionService.log_bypass_attempt(
                user, action, ip_address, user_agent,
                "محاولة إجراء باشتراك منتهي"
            )
            return False, "الاشتراك منتهي"
        
        return True, "الاشتراك نشط"
    
    @staticmethod
    def get_subscription_stats(broker):
        """الحصول على إحصائيات الاشتراك"""
        subscription = SubscriptionService.get_broker_subscription(broker)
        
        if not subscription:
            return None
        
        return {
            'plan_name': subscription.plan.name,
            'properties_used': subscription.properties_used,
            'properties_limit': subscription.plan.max_properties,
            'properties_remaining': subscription.plan.max_properties - subscription.properties_used,
            'auctions_used': subscription.auctions_used,
            'auctions_limit': subscription.plan.max_auctions,
            'auctions_remaining': subscription.plan.max_auctions - subscription.auctions_used,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'days_remaining': subscription.get_seconds_remaining() // 86400 if subscription.get_seconds_remaining() > 0 else 0,
            'is_active': subscription.is_active(),
            'status': subscription.status
        }
    
    @staticmethod
    def validate_subscription_limits(broker, action_type):
        """التحقق من حدود الاشتراك لنوع محدد من الإجراءات"""
        actions_map = {
            'add_property': SubscriptionService.can_add_property,
            'add_auction': SubscriptionService.can_add_auction,
            'add_building_request': SubscriptionService.can_add_building_request,
        }
        
        check_function = actions_map.get(action_type)
        if not check_function:
            return False, "نوع الإجراء غير معروف"
        
        return check_function(broker)
