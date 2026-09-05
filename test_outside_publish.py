import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from properties.models import Property, OutsideProperty, Broker
from properties.views import dynamic_add_property
from decimal import Decimal

# Create test user
user, created = User.objects.get_or_create(
    username='test_publisher',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('test123')
    user.save()

# Create or get broker
broker, created = Broker.objects.get_or_create(
    user=user,
    defaults={'phone': '07700000000', 'is_active': True}
)

# Test data
test_data = {
    'title': 'Test Outside Property',
    'description': 'This is a test property outside Iraq',
    'price': '150000',
    'currency': 'IQD',
    'type': 'outside_apartment',
    'purpose': 'sale',
    'country': 'UAE',
    'city': 'Dubai',
    'area': '120',
    'bedrooms': '2',
    'bathrooms': '2',
    'category': 'outside_iraq',
    'status': 'published',
}

print("Testing Outside Property Publishing System")
print("=" * 60)
print(f"Test User: {user.username}")
print(f"Broker: {broker}")
print(f"Test Data: {test_data}")
print("=" * 60)

# Simulate form submission
client = Client()
client.login(username='test_publisher', password='test123')

response = client.post('/dynamic-add-property/', test_data)

print(f"Response Status: {response.status_code}")
print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")

# Check if property was created
properties = Property.objects.filter(title='Test Outside Property')
print(f"Properties Created: {properties.count()}")

if properties.exists():
    prop = properties.first()
    print(f"Property ID: {prop.id}")
    print(f"Property Title: {prop.title}")
    print(f"Property Status: {prop.status}")
    print(f"Property Category: {prop.category}")
    print(f"Property Price: {prop.price}")

    # Check OutsideProperty
    outside_prop = OutsideProperty.objects.filter(property=prop)
    print(f"OutsideProperty Created: {outside_prop.exists()}")

print("=" * 60)
print("Test Complete!")
