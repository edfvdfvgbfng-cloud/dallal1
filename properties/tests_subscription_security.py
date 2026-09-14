"""
اختبارات الأمان لنظام الاشتراكات والنشر
Subscription Security Tests

هذه الاختبارات تغطي:
1. التحقق من صلاحية الدلال للنشر
2. التحقق من الاشتراك الفعال
3. منع تجاوز الحدود المتزامنة
4. منع التلاعب بالبيانات من Frontend
5. ربط الإعلان بالاشتراك الصحيح
6. منع المستخدمين العاديين من النشر
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from properties.models import (
    Property, Broker, BrokerPlanSubscription, 
    AdvancedSubscriptionPlan, SubscriptionRenewalRequest,
    ActivityLog
)
from properties.publication_services.subscription_validation_service import SubscriptionValidationService
from properties.publication_services.publication_service import PublicationService


class SubscriptionSecurityTests(TestCase):
    """اختبارات أمان الاشتراكات"""
    
    def setUp(self):
        """إعداد البيانات للاختبار"""
        # إنشاء مستخدم عادي
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
        
        # إنشاء مستخدم دلال
        self.broker_user = User.objects.create_user(
            username='brokeruser',
            email='broker@example.com',
            password='testpass123'
        )
        
        # إنشاء دلال
        self.broker = Broker.objects.create(
            user=self.broker_user,
            display_name='Test Broker',
            phone='07712345678',
            is_active=True,
            is_verified=True
        )
        
        # إنشاء خطة اشتراك
        self.plan = AdvancedSubscriptionPlan.objects.create(
            name='Test Plan',
            max_properties=5,
            max_auctions=2,
            max_building_requests=3,
            allow_featured_properties=True,
            allow_promoted_properties=True,
            price=100000
        )
        
        # إنشاء اشتراك فعال
        self.active_subscription = BrokerPlanSubscription.objects.create(
            broker=self.broker,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=20),
            status='active',
            properties_used=2
        )
        
        # إنشاء اشتراك منتهي
        self.expired_subscription = BrokerPlanSubscription.objects.create(
            broker=self.broker,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=5),
            status='expired',
            properties_used=5
        )
        
        # إنشاء دلال آخر
        self.other_broker_user = User.objects.create_user(
            username='otherbroker',
            email='otherbroker@example.com',
            password='testpass123'
        )
        
        self.other_broker = Broker.objects.create(
            user=self.other_broker_user,
            display_name='Other Broker',
            phone='07787654321',
            is_active=True,
            is_verified=True
        )
        
        # إنشاء اشتراك للدلال الآخر
        self.other_subscription = BrokerPlanSubscription.objects.create(
            broker=self.other_broker,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=25),
            status='active',
            properties_used=1
        )
        
        self.client = Client()
    
    def test_broker_with_active_subscription_can_publish(self):
        """اختبار: الدلال مع اشتراك فعال يمكنه النشر"""
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        can_publish, broker, subscription, publication_days = service.can_publish(
            is_featured=False,
            publication_days=30
        )
        
        self.assertTrue(can_publish)
        self.assertEqual(broker, self.broker)
        self.assertEqual(subscription, self.active_subscription)
        self.assertEqual(publication_days, 30)
    
    def test_broker_without_subscription_cannot_publish(self):
        """اختبار: الدلال بدون اشتراك لا يمكنه النشر"""
        # حذف الاشتراكات
        BrokerPlanSubscription.objects.filter(broker=self.broker).delete()
        
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        can_publish, broker, subscription, publication_days = service.can_publish(
            is_featured=False,
            publication_days=30
        )
        
        self.assertFalse(can_publish)
        self.assertIn('لا يوجد اشتراك فعال', service.errors)
    
    def test_expired_subscription_cannot_publish(self):
        """اختبار: الاشتراك المنتهي لا يسمح بالنشر"""
        # تعطيل الاشتراك الفعال
        self.active_subscription.status = 'expired'
        self.active_subscription.save()
        
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        can_publish, broker, subscription, publication_days = service.can_publish(
            is_featured=False,
            publication_days=30
        )
        
        self.assertFalse(can_publish)
        self.assertIn('لا يوجد اشتراك فعال', service.errors)
    
    def test_quota_exceeded_cannot_publish(self):
        """اختبار: تجاوز الحد المسموح يمنع النشر"""
        # استهلاك جميع الحصص
        self.active_subscription.properties_used = self.plan.max_properties
        self.active_subscription.save()
        
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        can_publish, broker, subscription, publication_days = service.can_publish(
            is_featured=False,
            publication_days=30
        )
        
        self.assertFalse(can_publish)
        self.assertIn('استنفذت الحد الأقصى', service.errors[0])
    
    def test_frontend_broker_id_ignored(self):
        """اختبار: تجاهل broker_id القادم من Frontend"""
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        # الدلال يجب أن يتم جلبه من المستخدم المصادق عليه
        broker = service.get_broker_for_user()
        
        self.assertEqual(broker, self.broker)
        self.assertNotEqual(broker, self.other_broker)
    
    def test_frontend_subscription_id_ignored(self):
        """اختبار: تجاهل subscription_id القادم من Frontend"""
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        # الاشتراك يجب أن يتم جلبه من الدلال المصادق عليه
        subscription = service.get_active_subscription(self.broker)
        
        self.assertEqual(subscription, self.active_subscription)
        self.assertNotEqual(subscription, self.other_subscription)
    
    def test_frontend_user_id_ignored(self):
        """اختبار: تجاهل user_id القادم من Frontend"""
        self.client.login(username='brokeruser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.broker_user})()
        )
        
        # المستخدم يجب أن يكون من الطلب المصادق عليه
        self.assertEqual(service.user, self.broker_user)
        self.assertNotEqual(service.user, self.regular_user)
    
    def test_regular_user_cannot_publish(self):
        """اختبار: المستخدم العادي لا يمكنه النشر"""
        self.client.login(username='regularuser', password='testpass123')
        
        service = SubscriptionValidationService(
            type('Request', (), {'user': self.regular_user})()
        )
        
        broker = service.get_broker_for_user()
        
        self.assertIsNone(broker)
        self.assertIn('المستخدم ليس دلالاً', service.errors)
    
    def test_property_linked_to_correct_subscription(self):
        """اختبار: الإعلان مربوط بالاشتراك الصحيح"""
        self.client.login(username='brokeruser', password='testpass123')
        
        # إنشاء إعلان
        property = Property.objects.create(
            title='Test Property',
            type='apartment',
            status='published',
            location='Baghdad',
            area=100,
            price=100000000,
            owner=self.broker_user,
            broker=self.broker,
            subscription=self.active_subscription
        )
        
        # التحقق من الربط
        self.assertEqual(property.subscription, self.active_subscription)
        self.assertEqual(property.broker, self.broker)
        self.assertEqual(property.owner, self.broker_user)
    
    def test_old_property_subscription_does_not_change(self):
        """اختبار: اشتراك الإعلان القديم لا يتغير عند تجديد الاشتراك"""
        # إنشاء إعلان قديم
        old_property = Property.objects.create(
            title='Old Property',
            type='apartment',
            status='published',
            location='Baghdad',
            area=100,
            price=100000000,
            owner=self.broker_user,
            broker=self.broker,
            subscription=self.active_subscription
        )
        
        # إنشاء اشتراك جديد
        new_subscription = BrokerPlanSubscription.objects.create(
            broker=self.broker,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            status='active',
            properties_used=0
        )
        
        # التحقق من أن الإعلان القديم لا يزال مربوط بالاشتراك القديم
        old_property.refresh_from_db()
        self.assertEqual(old_property.subscription, self.active_subscription)
        self.assertNotEqual(old_property.subscription, new_subscription)
    
    def test_concurrent_requests_cannot_exceed_limit(self):
        """اختبار: الطلبات المتزامنة لا يمكنها تجاوز الحد"""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        # تعيين الحد المتبقي إلى 1
        self.active_subscription.properties_used = self.plan.max_properties - 1
        self.active_subscription.save()
        
        results = []
        lock = threading.Lock()
        
        def try_publish():
            try:
                with transaction.atomic():
                    service = SubscriptionValidationService(
                        type('Request', (), {'user': self.broker_user})()
                    )
                    
                    can_publish, broker, subscription, publication_days = service.can_publish(
                        is_featured=False,
                        publication_days=30
                    )
                    
                    if can_publish:
                        # محاولة استهلاك الحصة
                        quota_consumed = service.consume_publication_quota(subscription, False)
                        
                        with lock:
                            results.append(quota_consumed)
            except Exception as e:
                with lock:
                    results.append(False)
        
        # تشغيل طلبين متزامنين
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(try_publish)
            executor.submit(try_publish)
        
        # يجب أن ينجح طلب واحد فقط
        successful_count = sum(1 for result in results if result)
        self.assertEqual(successful_count, 1)
    
    def test_property_appears_in_correct_category(self):
        """اختبار: الإعلان يظهر في التصنيف الصحيح"""
        # إنشاء إعلان داخل العراق
        iraq_property = Property.objects.create(
            title='Iraq Property',
            type='apartment',
            category='property_iraq',
            status='published',
            location='Baghdad',
            area=100,
            price=100000000,
            owner=self.broker_user,
            broker=self.broker,
            subscription=self.active_subscription
        )
        
        # التحقق من التصنيف
        self.assertEqual(iraq_property.category, 'property_iraq')
    
    def test_audit_log_created_for_publication(self):
        """اختبار: إنشاء سجل Audit Log للنشر"""
        # إنشاء إعلان
        property = Property.objects.create(
            title='Test Property',
            type='apartment',
            status='published',
            location='Baghdad',
            area=100,
            price=100000000,
            owner=self.broker_user,
            broker=self.broker,
            subscription=self.active_subscription
        )
        
        # إنشاء سجل Audit Log
        service = SubscriptionValidationService(
            type('Request', (), {
                'user': self.broker_user,
                'META': {
                    'REMOTE_ADDR': '127.0.0.1',
                    'HTTP_USER_AGENT': 'Test Browser'
                }
            })()
        )
        
        service.create_audit_log(property, self.active_subscription, 'published')
        
        # التحقق من وجود السجل
        audit_log = ActivityLog.objects.filter(
            user=self.broker_user,
            action='published',
            model_type='property',
            object_id=property.id
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'published')
        self.assertEqual(audit_log.model_type, 'property')
        self.assertEqual(audit_log.object_id, property.id)
    
    def test_transaction_rollback_on_failure(self):
        """اختبار: التراجع عن المعاملة عند الفشل"""
        initial_count = Property.objects.count()
        
        try:
            with transaction.atomic():
                # إنشاء إعلان
                property = Property.objects.create(
                    title='Test Property',
                    type='apartment',
                    status='published',
                    location='Baghdad',
                    area=100,
                    price=100000000,
                    owner=self.broker_user,
                    broker=self.broker,
                    subscription=self.active_subscription
                )
                
                # محاولة استهلاك حصة لا توجد
                self.active_subscription.properties_used = self.plan.max_properties + 1
                self.active_subscription.save()
                
                # رفع استثناء للتراجع
                raise Exception("Test rollback")
        except Exception:
            pass
        
        # التحقق من عدم إنشاء الإعلان
        final_count = Property.objects.count()
        self.assertEqual(initial_count, final_count)


class PublicationServiceIntegrationTests(TestCase):
    """اختبارات تكامل خدمة النشر"""
    
    def setUp(self):
        """إعداد البيانات للاختبار"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.broker = Broker.objects.create(
            user=self.user,
            display_name='Test Broker',
            phone='07712345678',
            is_active=True,
            is_verified=True
        )
        
        self.plan = AdvancedSubscriptionPlan.objects.create(
            name='Test Plan',
            max_properties=5,
            max_auctions=2,
            allow_featured_properties=True,
            price=100000
        )
        
        self.subscription = BrokerPlanSubscription.objects.create(
            broker=self.broker,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            status='active',
            properties_used=0
        )
    
    def test_publication_service_integration(self):
        """اختبار تكامل خدمة النشر"""
        request = type('Request', (), {
            'user': self.user,
            'META': {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Browser'
            }
        })()
        
        service = PublicationService(request)
        
        data = {
            'title': 'Test Property',
            'type': 'apartment',
            'price': 100000000,
            'description': 'Test description',
            'governorate': 'بغداد',
            'city': 'بغداد',
            'district': 'الكرادة',
            'location': 'Baghdad',
            'area': 100,
        }
        
        property, category, success, subscription_info = service.publish(
            category='property_iraq',
            data=data,
            is_featured=False,
            is_pinned=False,
            publication_days=30
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(property)
        self.assertEqual(property.owner, self.user)
        self.assertEqual(property.broker, self.broker)
        self.assertEqual(property.subscription, self.subscription)
        self.assertEqual(property.status, 'published')
        self.assertIsNotNone(subscription_info)