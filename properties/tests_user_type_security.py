"""
اختبارات أمان وفصل أنواع المستخدمين
User Type Separation and Security Tests

هذه الاختبارات تتحقق من:
1. /register/ ينشئ USER فقط
2. لا يمكن رفع الصلاحيات من Frontend
3. Broker يُنشأ من Admin فقط
4. الفصل بين لوحات التحكم
5. حماية URLs حسب النوع
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Broker, UserProfile
from .permissions import get_user_type


class RegisterViewSecurityTests(TestCase):
    """اختبارات أمان صفحة التسجيل"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
    
    def test_register_creates_user_only(self):
        """اختبار أن التسجيل ينشئ USER فقط حتى مع حقول وهمية"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
            'phone': '07712345678',
            'is_staff': 'true',  # محاولة رفع الصلاحيات
            'is_superuser': 'true',  # محاولة رفع الصلاحيات
            'user_type': 'broker',  # محاولة تغيير النوع
            'role': 'admin',  # محاولة تغيير الدور
        })
        
        # التحقق من إنشاء المستخدم
        user = User.objects.get(username='testuser')
        
        # التحقق من أن الحساب ليس staff ولا superuser
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        # التحقق من نوع المستخدم في UserProfile
        user_profile = user.user_profile
        self.assertEqual(user_profile.user_type, UserProfile.USER_TYPE_USER)
    
    def test_register_ignores_staff_field(self):
        """اختبار أن حقل is_staff يتم تجاهله من POST"""
        response = self.client.post(self.register_url, {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
            'phone': '07712345679',
            'is_staff': True,  # محاولة تعيين is_staff
        })
        
        user = User.objects.get(username='testuser2')
        self.assertFalse(user.is_staff)
    
    def test_register_creates_user_profile(self):
        """اختبار أن التسجيل ينشئ UserProfile"""
        response = self.client.post(self.register_url, {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'TestPass123',
            'confirm_password': 'TestPass123',
            'phone': '07712345670',
        })
        
        user = User.objects.get(username='testuser3')
        self.assertTrue(hasattr(user, 'user_profile'))
        self.assertEqual(user.user_profile.user_type, UserProfile.USER_TYPE_USER)


class BrokerCreationSecurityTests(TestCase):
    """اختبارات أمان إنشاء الدلال"""
    
    def setUp(self):
        self.client = Client()
        # إنشاء مستخدم عادي
        self.user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='TestPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'user_type': UserProfile.USER_TYPE_USER}
        )
        
        # إنشاء Admin
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.admin,
            defaults={'user_type': UserProfile.USER_TYPE_ADMIN}
        )
    
    def test_normal_user_cannot_create_broker(self):
        """اختبار أن المستخدم العادي لا يستطيع إنشاء دلال"""
        self.client.login(username='normaluser', password='TestPass123')
        
        broker_create_url = reverse('broker_create')
        response = self.client.get(broker_create_url)
        
        # يجب أن يتم رفض الوصول
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_admin_can_create_broker(self):
        """اختبار أن Admin يستطيع إنشاء دلال"""
        self.client.login(username='admin', password='AdminPass123')
        
        broker_create_url = reverse('broker_create')
        response = self.client.get(broker_create_url)
        
        # يجب السماح بالوصول
        self.assertEqual(response.status_code, 200)
    
    def test_broker_creation_sets_user_type(self):
        """اختبار أن إنشاء Broker يضبط user_type إلى broker"""
        self.client.login(username='admin', password='AdminPass123')
        
        broker_create_url = reverse('broker_create')
        response = self.client.post(broker_create_url, {
            'username': 'newbroker',
            'email': 'broker@example.com',
            'password': 'BrokerPass123',
            'phone': '07712345671',
            'role': Broker.ROLE_SUB,
            'first_name': 'Test',
            'last_name': 'Broker',
        })
        
        # التحقق من نوع المستخدم
        new_user = User.objects.get(username='newbroker')
        user_profile = new_user.user_profile
        self.assertEqual(user_profile.user_type, UserProfile.USER_TYPE_BROKER)
        
        # التحقق من أن الحساب ليس staff
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)


class DashboardAccessTests(TestCase):
    """اختبارات الوصول إلى لوحات التحكم"""
    
    def setUp(self):
        self.client = Client()
        
        # إنشاء USER
        self.user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='TestPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'user_type': UserProfile.USER_TYPE_USER}
        )
        
        # إنشاء BROKER
        self.broker_user = User.objects.create_user(
            username='broker',
            email='broker@example.com',
            password='BrokerPass123'
        )
        self.broker = Broker.objects.create(
            user=self.broker_user,
            phone='07712345672',
            role=Broker.ROLE_SUB,
            is_active=True
        )
        UserProfile.objects.get_or_create(
            user=self.broker_user,
            defaults={'user_type': UserProfile.USER_TYPE_BROKER}
        )
        
        # إنشاء ADMIN
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.admin,
            defaults={'user_type': UserProfile.USER_TYPE_ADMIN}
        )
    
    def test_user_cannot_access_broker_panel(self):
        """اختبار أن USER لا يستطيع الوصول إلى لوحة الدلال"""
        self.client.login(username='normaluser', password='TestPass123')
        
        response = self.client.get(reverse('broker_panel'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_user_cannot_access_admin_panel(self):
        """اختبار أن USER لا يستطيع الوصول إلى لوحة الإدارة"""
        self.client.login(username='normaluser', password='TestPass123')
        
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_broker_cannot_access_admin_panel(self):
        """اختبار أن BROKER لا يستطيع الوصول إلى لوحة الإدارة"""
        self.client.login(username='broker', password='BrokerPass123')
        
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_broker_can_access_broker_panel(self):
        """اختبار أن BROKER يستطيع الوصول إلى لوحة الدلال"""
        self.client.login(username='broker', password='BrokerPass123')
        
        response = self.client.get(reverse('broker_panel'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_access_admin_panel(self):
        """اختبار أن ADMIN يستطيع الوصول إلى لوحة الإدارة"""
        self.client.login(username='admin', password='AdminPass123')
        
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_can_access_user_dashboard(self):
        """اختبار أن USER يستطيع الوصول إلى لوحة المستخدم"""
        self.client.login(username='normaluser', password='TestPass123')
        
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)


class LoginRedirectTests(TestCase):
    """اختبارات إعادة التوجيه بعد تسجيل الدخول"""
    
    def setUp(self):
        self.client = Client()
        
        # إنشاء USER
        self.user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='TestPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'user_type': UserProfile.USER_TYPE_USER}
        )
        
        # إنشاء BROKER
        self.broker_user = User.objects.create_user(
            username='broker',
            email='broker@example.com',
            password='BrokerPass123'
        )
        self.broker = Broker.objects.create(
            user=self.broker_user,
            phone='07712345672',
            role=Broker.ROLE_SUB,
            is_active=True
        )
        UserProfile.objects.get_or_create(
            user=self.broker_user,
            defaults={'user_type': UserProfile.USER_TYPE_BROKER}
        )
        
        # إنشاء ADMIN
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.admin,
            defaults={'user_type': UserProfile.USER_TYPE_ADMIN}
        )
    
    def test_user_redirects_to_user_dashboard(self):
        """اختبار أن USER يُعيد توجيهه إلى user_dashboard"""
        response = self.client.post(reverse('login'), {
            'username': 'normaluser',
            'password': 'TestPass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/user-dashboard/'))
    
    def test_broker_redirects_to_broker_panel(self):
        """اختبار أن BROKER يُعيد توجيهه إلى broker_panel"""
        response = self.client.post(reverse('login'), {
            'username': 'broker',
            'password': 'BrokerPass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/broker-panel/'))
    
    def test_admin_redirects_to_admin_panel(self):
        """اختبار أن ADMIN يُعيد توجيهه إلى admin_panel"""
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'AdminPass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/admin-panel/'))


class UserTypeDetectionTests(TestCase):
    """اختبارات تحديد نوع المستخدم"""
    
    def setUp(self):
        # إنشاء USER
        self.user = User.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='TestPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'user_type': UserProfile.USER_TYPE_USER}
        )
        
        # إنشاء BROKER
        self.broker_user = User.objects.create_user(
            username='broker',
            email='broker@example.com',
            password='BrokerPass123'
        )
        self.broker = Broker.objects.create(
            user=self.broker_user,
            phone='07712345672',
            role=Broker.ROLE_SUB,
            is_active=True
        )
        UserProfile.objects.get_or_create(
            user=self.broker_user,
            defaults={'user_type': UserProfile.USER_TYPE_BROKER}
        )
        
        # إنشاء ADMIN
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        UserProfile.objects.get_or_create(
            user=self.admin,
            defaults={'user_type': UserProfile.USER_TYPE_ADMIN}
        )
    
    def test_get_user_type_returns_user(self):
        """اختبار أن get_user_type يُرجع 'user' للمستخدم العادي"""
        user_type = get_user_type(self.user)
        self.assertEqual(user_type, 'user')
    
    def test_get_user_type_returns_broker(self):
        """اختبار أن get_user_type يُرجع 'broker' للدلال"""
        user_type = get_user_type(self.broker_user)
        self.assertEqual(user_type, 'broker')
    
    def test_get_user_type_returns_admin(self):
        """اختبار أن get_user_type يُرجع 'admin' للإدارة"""
        user_type = get_user_type(self.admin)
        self.assertEqual(user_type, 'admin')
    
    def test_get_user_type_returns_none_for_anonymous(self):
        """اختبار أن get_user_type يُرجع None للمستخدم غير مسجل"""
        from django.contrib.auth.models import AnonymousUser
        user_type = get_user_type(AnonymousUser())
        self.assertIsNone(user_type)