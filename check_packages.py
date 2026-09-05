import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import TravelCompany, TravelPackage

# Check company ID 2
company = TravelCompany.objects.filter(id=2).first()
if company:
    print(f'Company: {company.name} (ID: {company.id})')
    print(f'is_active: {company.is_active}')
    
    # Get all packages
    all_packages = company.travel_packages.all()
    print(f'Total packages: {all_packages.count()}')
    
    # Get published packages
    published_packages = company.travel_packages.filter(status='published')
    print(f'Published packages: {published_packages.count()}')
    
    for p in all_packages:
        print(f'  - Package: {p.title}, status: {p.status}')
else:
    print('Company not found')
