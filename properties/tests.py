"""
Test suite for the properties app.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Property, Broker, Message, SiteSettings
from .constants import IRAQ_GOVERNORATES, PROPERTY_TYPES


class PropertyModelTest(TestCase):
    """Test cases for Property model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.property = Property.objects.create(
            title='Test Property',
            type='apartment',
            status='ready',
            location='Baghdad, Iraq',
            area=120,
            price=150000000,
            description='A beautiful apartment',
            phone='07712345678',
            governorate='BAG',
            district='Karrada',
            owner=self.user
        )
    
    def test_property_creation(self):
        """Test property creation"""
        self.assertEqual(self.property.title, 'Test Property')
        self.assertEqual(self.property.type, 'apartment')
        self.assertEqual(self.property.status, 'ready')
        self.assertTrue(self.property.is_active)
    
    def test_property_str(self):
        """Test property string representation"""
        self.assertEqual(str(self.property), 'Test Property')
    
    def test_property_absolute_url(self):
        """Test property URL generation"""
        url = self.property.get_absolute_url()
        self.assertIn('/property/', url)
    
    def test_property_increment_views(self):
        """Test view counter increment"""
        initial_views = self.property.views_count
        self.property.increment_views()
        self.assertEqual(self.property.views_count, initial_views + 1)


class BrokerModelTest(TestCase):
    """Test cases for Broker model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='broker',
            email='broker@example.com',
            password='brokerpass123'
        )
        
        self.broker = Broker.objects.create(
            user=self.user,
            office_name='Test Real Estate',
            phone='07712345678',
            governorate='BAG',
            is_verified=True,
            is_active=True
        )
    
    def test_broker_creation(self):
        """Test broker creation"""
        self.assertEqual(self.broker.office_name, 'Test Real Estate')
        self.assertTrue(self.broker.is_verified)
        self.assertTrue(self.broker.is_active)
    
    def test_broker_str(self):
        """Test broker string representation"""
        self.assertEqual(str(self.broker), 'Test Real Estate')
    
    def test_broker_active_properties_count(self):
        """Test broker active properties count"""
        # Create test properties
        for i in range(3):
            Property.objects.create(
                title=f'Property {i}',
                type='apartment',
                status='ready',
                location='Baghdad',
                area=100,
                price=100000000,
                description='Test',
                phone='07712345678',
                governorate='BAG',
                broker=self.broker
            )
        
        self.assertEqual(self.broker.active_properties_count(), 3)


class MessageModelTest(TestCase):
    """Test cases for Message model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='senderpass123'
        )
        
        self.property = Property.objects.create(
            title='Test Property',
            type='apartment',
            status='ready',
            location='Baghdad',
            area=100,
            price=100000000,
            description='Test',
            phone='07712345678',
            governorate='BAG',
            owner=self.user
        )
        
        self.message = Message.objects.create(
            name='Test Sender',
            email='test@example.com',
            phone='07712345678',
            message='I am interested in this property',
            property=self.property
        )
    
    def test_message_creation(self):
        """Test message creation"""
        self.assertEqual(self.message.name, 'Test Sender')
        self.assertFalse(self.message.is_read)
    
    def test_message_str(self):
        """Test message string representation"""
        expected = f"{self.message.name} - {self.message.property.title}"
        self.assertEqual(str(self.message), expected)


class ViewTest(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_home_page(self):
        """Test home page loads"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'دلال')
    
    def test_about_page(self):
        """Test about page loads"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
    
    def test_contact_page(self):
        """Test contact page loads"""
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Test login page loads"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_page(self):
        """Test register page loads"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
    
    def test_property_list(self):
        """Test property list page"""
        # Create test properties
        for i in range(5):
            Property.objects.create(
                title=f'Property {i}',
                type='apartment',
                status='ready',
                location='Baghdad',
                area=100,
                price=100000000,
                description='Test',
                phone='07712345678',
                governorate='BAG',
                owner=self.user
            )
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Property')


class APITest(TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
    
    def test_api_properties_list(self):
        """Test API properties list"""
        # Create test property
        Property.objects.create(
            title='API Test Property',
            type='apartment',
            status='ready',
            location='Baghdad',
            area=100,
            price=100000000,
            description='Test',
            phone='07712345678',
            governorate='BAG',
            owner=self.user
        )
        
        response = self.client.get('/api/properties/')
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        self.assertGreater(len(data), 0)
    
    def test_api_governorates(self):
        """Test API governorates endpoint"""
        response = self.client.get('/api/properties/governorates/')
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        self.assertIn('governorates', data)
        self.assertEqual(len(data['governorates']), len(IRAQ_GOVERNORATES))


class ConstantsTest(TestCase):
    """Test cases for constants"""
    
    def test_iraq_governorates(self):
        """Test Iraq governorates constant"""
        self.assertEqual(len(IRAQ_GOVERNORATES), 19)
        self.assertIn(('BAG', 'بغداد'), IRAQ_GOVERNORATES)
    
    def test_property_types(self):
        """Test property types constant"""
        self.assertIn('residential', PROPERTY_TYPES)
        self.assertIn('commercial', PROPERTY_TYPES)
        self.assertIn('apartment', PROPERTY_TYPES['residential'])


class SiteSettingsTest(TestCase):
    """Test cases for SiteSettings"""
    
    def test_site_settings_creation(self):
        """Test site settings creation"""
        settings = SiteSettings.get_solo()
        self.assertIsNotNone(settings)
    
    def test_site_settings_defaults(self):
        """Test site settings have reasonable defaults"""
        settings = SiteSettings.get_solo()
        self.assertIsNotNone(settings.site_name)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
    
    def test_complete_property_workflow(self):
        """Test complete property creation and display workflow"""
        # Login
        self.client.login(username='integrationuser', password='integrationpass123')
        
        # Create property
        property_data = {
            'title': 'Integration Test Property',
            'type': 'apartment',
            'status': 'ready',
            'location': 'Baghdad, Karrada',
            'area': 150,
            'price': 200000000,
            'description': 'A great apartment for testing',
            'phone': '07712345678',
            'governorate': 'BAG',
            'district': 'Karrada',
        }
        
        # Note: This would require the actual form/view implementation
        # For now, we'll create directly
        property = Property.objects.create(
            owner=self.user,
            **property_data
        )
        
        # Verify property was created
        self.assertEqual(Property.objects.count(), 1)
        
        # Test property detail page
        response = self.client.get(property.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, property.title)
        
        # Test property appears in search
        response = self.client.get(reverse('home') + f'?type=apartment')
        self.assertEqual(response.status_code, 200)


class PerformanceTest(TestCase):
    """Performance tests for critical operations"""
    
    def test_property_list_performance(self):
        """Test property list query performance"""
        import time
        from django.db import connection, reset_queries
        
        # Create test data
        user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perftest123'
        )
        
        for i in range(100):
            Property.objects.create(
                title=f'Property {i}',
                type='apartment',
                status='ready',
                location='Baghdad',
                area=100,
                price=100000000,
                description='Test',
                phone='07712345678',
                governorate='BAG',
                owner=user
            )
        
        # Test query performance
        reset_queries()
        start_time = time.time()
        
        properties = Property.objects.all().select_related('owner').prefetch_related('images')
        list(properties)  # Force evaluation
        
        end_time = time.time()
        query_time = end_time - start_time
        query_count = len(connection.queries)
        
        # Performance assertions
        self.assertLess(query_time, 1.0, "Query took too long")
        self.assertLess(query_count, 5, "Too many database queries")
        
        print(f"Property list query: {query_time:.3f}s, {query_count} queries")