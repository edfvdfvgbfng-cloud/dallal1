from properties.models import TravelCompany, TravelPackage

companies = TravelCompany.objects.filter(is_active=True)
print(f'Active companies: {companies.count()}')

for c in companies:
    packages = c.travel_packages.filter(status='published')
    print(f'Company: {c.name} (ID: {c.id}), Packages: {packages.count()}')
    for p in packages:
        print(f'  - Package: {p.title}')
