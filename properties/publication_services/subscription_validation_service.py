"""
Subscription Validation Service - خدمة التحقق من الاشتراكات وربط الإعلانات

هذه الخدمة مسؤولة عن:
- التحقق من صلاحية المستخدم للنشر
- التحقق من وجود اشتراك فعال
- التحقق من حدود الإعلانات
- ربط الإعلان بالاشتراك الفعال
- منع تجاوز الحد المتزامن
- Audit Log لعمليات النشر
"""

from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, F
from datetime import timedelta

from properties.models import (
    Property, Broker, BrokerPlanSubscription, 
    SubscriptionRenewalRequest, AdvancedSubscriptionPlan
)


class SubscriptionValidationService:
    """خدمة التحقق من الاشتراكات للنشر"""
    
    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.errors = []
        self.warnings = []
    
    def get_broker_for_user(self):
        """الحصول على الدلال للمستخدم الحالي فقط"""
        try:
            return Broker.objects.get(user=self.user)
        except Broker.DoesNotExist:
            self.errors.append('المستخدم ليس دلالاً. يرجى تسجيل الدخول كدلال.')
            return None
        except Exception as e:
            self.errors.append(f'حدث خطأ في جلب بيانات الدلال: {str(e)}')
            return None
    
    def get_active_subscription(self, broker):
        """الحصول على الاشتراك الفعال للدلال"""
        if not broker:
            return None
        
        # التحقق من الاشتراكات المباشرة أولاً
        active_subscription = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        ).order_by('-start_date').first()
        
        if active_subscription:
            # التحقق من تاريخ الانتهاء
            now = timezone.now()
            if active_subscription.actual_end_date:
                end_date = active_subscription.actual_end_date
            else:
                end_date = active_subscription.end_date
            
            if end_date and end_date < now:
                # الاشتراك منتهي
                active_subscription.status = 'expired'
                active_subscription.save()
                return None
            
            return active_subscription
        
        # التحقق من طلبات التجديد الموافق عليها
        latest_renewal = SubscriptionRenewalRequest.objects.filter(
            broker=broker,
            status='approved'
        ).order_by('-approved_at').first()
        
        if latest_renewal:
            # التحقق من أن الطلب لم ينتهي
            if latest_renewal.subscription_type == 'all_inclusive':
                # هذا الطلب يسمح بالنشر بدون اشتراك محدد
                return latest_renewal
            
            # التحقق من المتبقي
            if latest_renewal.regular_count > 0 or latest_renewal.premium_count > 0:
                return latest_renewal
        
        return None
    
    def check_broker_status(self, broker):
        """التحقق من حالة الدلال"""
        if not broker:
            return False
        
        if not broker.is_active:
            self.errors.append('حساب الدلال معطل. يرجى التواصل مع الإدارة.')
            return False
        
        if broker.is_suspended:
            self.errors.append('حساب الدلال موقوف مؤقتاً.')
            return False
        
        return True
    
    def check_subscription_limits(self, subscription, is_featured):
        """التحقق من حدود الإعلانات"""
        if not subscription:
            self.errors.append('لا يوجد اشتراك فعال. يرجى الاشتراك لإضافة عقارات.')
            return False
        
        if hasattr(subscription, 'properties_used'):
            max_properties = subscription.plan.max_properties if subscription.plan else 0
            
            if max_properties > 0:
                used_count = subscription.properties_used
                
                if used_count >= max_properties:
                    self.errors.append(f'لقد استنفذت الحد الأقصى من العقارات ({max_properties}).')
                    return False
        
        # التحقق من طلبات التجديد
        if isinstance(subscription, SubscriptionRenewalRequest):
            if is_featured:
                if subscription.premium_count <= 0:
                    self.errors.append('لقد استنفذت الحد الأقصى من العقارات المميزة.')
                    return False
            else:
                if subscription.regular_count <= 0:
                    self.errors.append('لقد استنفذت الحد الأقصى من العقارات العادية.')
                    return False
        
        return True
    
    def validate_publication_days(self, publication_days, subscription):
        """التحقق من صحة مدة النشر"""
        try:
            publication_days = int(publication_days)
        except (ValueError, TypeError):
            self.errors.append('مدة النشر يجب أن تكون رقماً صحيحاً')
            return False
        
        # المسموح فقط: 1, 3, 7, 15, 30
        allowed_days = [1, 3, 7, 15, 30]
        if publication_days not in allowed_days:
            self.errors.append(f'مدة النشر يجب أن تكون واحدة من: {allowed_days}')
            return False
        
        # التحقق من أن الاشتراك يسمح بهذه المدة
        if subscription and hasattr(subscription, 'plan'):
            plan = subscription.plan
            if plan and hasattr(plan, 'max_publication_days'):
                max_days = plan.max_publication_days
                if max_days and publication_days > max_days:
                    self.errors.append(f'اشتراكك يسمح بحد أقصى {max_days} يوم للنشر.')
                    return False
        
        return publication_days
    
    def can_publish(self, is_featured=False, publication_days=30):
        """
        التحقق الشامل من إمكانية النشر
        
        Returns:
            tuple: (can_publish, broker, subscription, publication_days)
        """
        # 1. التحقق من المستخدم
        if not self.user.is_authenticated:
            self.errors.append('يجب تسجيل الدخول للنشر.')
            return False, None, None, None
        
        # 2. الحصول على الدلال
        broker = self.get_broker_for_user()
        if not broker:
            return False, None, None, None
        
        # 3. التحقق من حالة الدلال
        if not self.check_broker_status(broker):
            return False, broker, None, None
        
        # 4. الحصول على الاشتراك الفعال
        subscription = self.get_active_subscription(broker)
        if not subscription:
            return False, broker, None, None
        
        # 5. التحقق من حدود الإعلانات
        if not self.check_subscription_limits(subscription, is_featured):
            return False, broker, subscription, None
        
        # 6. التحقق من مدة النشر
        publication_days = self.validate_publication_days(publication_days, subscription)
        if not publication_days:
            return False, broker, subscription, None
        
        return True, broker, subscription, publication_days
    
    @transaction.atomic
    def consume_publication_quota(self, subscription, is_featured):
        """استهلاك حصة من الاشتراك مع select_for_update"""
        if not subscription:
            return False
        
        # قفل الاشتراك لمنع تجاوز الحد المتزامن
        if isinstance(subscription, BrokerPlanSubscription):
            subscription = BrokerPlanSubscription.objects.select_for_update().get(id=subscription.id)
            
            if hasattr(subscription, 'properties_used'):
                max_properties = subscription.plan.max_properties if subscription.plan else 0
                
                if max_properties > 0 and subscription.properties_used >= max_properties:
                    return False
                
                subscription.properties_used = F('properties_used') + 1
                subscription.save()
                return True
        
        elif isinstance(subscription, SubscriptionRenewalRequest):
            subscription = SubscriptionRenewalRequest.objects.select_for_update().get(id=subscription.id)
            
            if is_featured:
                if subscription.premium_count <= 0:
                    return False
                subscription.premium_count = F('premium_count') - 1
            else:
                if subscription.regular_count <= 0:
                    return False
                subscription.regular_count = F('regular_count') - 1
            
            subscription.save()
            return True
        
        return True
    
    def link_property_to_subscription(self, property, subscription):
        """ربط الإعلان بالاشتراك الذي تم استخدامه"""
        # إضافة حقل subscription إلى Property إذا لم يكن موجوداً
        # سنتحقق من وجود الحقل أولاً
        try:
            # استخدام Model.add_to() أو تعيين الحقل مباشرة
            if hasattr(property, 'subscription'):
                property.subscription = subscription
                property.save(update_fields=['subscription'])
                # تسجيل ربط الإعلان بالاشتراك
                self.create_audit_log(property, subscription, 'update')
                return True
            else:
                # إذا لم يكن الحقل موجوداً، سنحتاج لإنشاء migration
                # في الوقت الحالي، سنقوم بإنشاء Audit Log
                self.create_audit_log(property, subscription, 'update')
                return True
        except Exception as e:
            self.warnings.append(f'لم يتم ربط الإعلان بالاشتراك: {str(e)}')
            return False
    
    def create_audit_log(self, property, subscription, action):
        """إنشاء سجل Audit Log باستخدام ActivityLog الموجود"""
        try:
            from properties.models import ActivityLog
            
            # إعداد metadata مع معلومات الاشتراك
            metadata = {
                'property_id': property.id,
                'property_title': property.title,
                'property_type': property.type,
                'property_category': property.category,
                'is_featured': property.is_featured,
                'is_pinned': property.is_pinned,
                'publication_date': property.created_at.isoformat() if property.created_at else None,
            }
            
            if subscription:
                metadata.update({
                    'subscription_id': subscription.id,
                    'subscription_type': subscription.get_status_display() if hasattr(subscription, 'get_status_display') else str(subscription),
                    'subscription_plan': subscription.plan.name if hasattr(subscription, 'plan') and subscription.plan else None,
                })
            
            # تسجيل النشاط
            ActivityLog.log(
                user=self.user,
                action=action,
                model_type='property',
                object_id=property.id,
                object_repr=str(property),
                description=f'{action} property via subscription',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                metadata=metadata
            )
            
            return True
        except Exception as e:
            self.warnings.append(f'لم يتم إنشاء Audit Log: {str(e)}')
            return False
    
    def get_publication_info(self, subscription):
        """الحصول على معلومات الاشتراك للعرض"""
        if not subscription:
            return None
        
        if isinstance(subscription, BrokerPlanSubscription):
            plan = subscription.plan
            return {
                'subscription_type': subscription.get_status_display(),
                'plan_name': plan.name if plan else 'غير محدد',
                'max_properties': plan.max_properties if plan else 0,
                'used_properties': subscription.properties_used,
                'remaining_properties': max(0, (plan.max_properties if plan else 0) - subscription.properties_used),
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'is_active': subscription.status == 'active',
            }
        
        elif isinstance(subscription, SubscriptionRenewalRequest):
            return {
                'subscription_type': subscription.subscription_type or 'تجديد',
                'plan_name': subscription.plan.name if subscription.plan else subscription.subscription_type,
                'regular_count': subscription.regular_count,
                'premium_count': subscription.premium_count,
                'property_count': subscription.property_count,
                'approved_at': subscription.approved_at,
                'is_active': subscription.status == 'approved',
            }
        
        return None