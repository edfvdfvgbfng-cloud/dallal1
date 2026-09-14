from django.core.management.base import BaseCommand
from properties.models import AdvancedSubscriptionPlan


class Command(BaseCommand):
    help = 'Create realistic subscription plans'

    def handle(self, *args, **options):
        # Create realistic subscription plans
        
        # Basic Plan
        BasicPlan, created = AdvancedSubscriptionPlan.objects.get_or_create(
            name='الخطة الأساسية',
            defaults={
                'plan_type': 'combined',
                'tier': 'regular',
                'price_per_day': 30,
                'price_per_month': 900,
                'price_per_year': 10800,
                'max_properties': 20,
                'max_properties_regular': 18,
                'max_properties_premium': 2,
                'max_auctions': 5,
                'max_auctions_regular': 4,
                'max_auctions_premium': 1,
                'max_building_requests': 5,
                'max_jobs': 5,
                'max_services': 5,
                'max_hotels': 2,
                'max_resorts': 2,
                'allow_property_replacement': True,
                'allow_subscription_renewal': True,
                'allow_expired_renewal': True,
                'is_active': True,
                'description': 'خطة أساسية للمبتدئين مع حدود معقولة'
            }
        )
        
        # Professional Plan
        ProfessionalPlan, created = AdvancedSubscriptionPlan.objects.get_or_create(
            name='الخطة الاحترافية',
            defaults={
                'plan_type': 'combined',
                'tier': 'premium',
                'price_per_day': 100,
                'price_per_month': 3000,
                'price_per_year': 36000,
                'max_properties': 100,
                'max_properties_regular': 70,
                'max_properties_premium': 30,
                'max_auctions': 25,
                'max_auctions_regular': 18,
                'max_auctions_premium': 7,
                'max_building_requests': 20,
                'max_jobs': 20,
                'max_services': 20,
                'max_hotels': 10,
                'max_resorts': 10,
                'allow_property_replacement': True,
                'allow_subscription_renewal': True,
                'allow_expired_renewal': True,
                'is_active': True,
                'description': 'خطة احترافية للمستخدمين المتقدمين'
            }
        )
        
        # Business Plan
        BusinessPlan, created = AdvancedSubscriptionPlan.objects.get_or_create(
            name='الخطة التجارية',
            defaults={
                'plan_type': 'combined',
                'tier': 'premium',
                'price_per_day': 250,
                'price_per_month': 7500,
                'price_per_year': 90000,
                'max_properties': 250,
                'max_properties_regular': 150,
                'max_properties_premium': 100,
                'max_auctions': 50,
                'max_auctions_regular': 35,
                'max_auctions_premium': 15,
                'max_building_requests': 50,
                'max_jobs': 50,
                'max_services': 50,
                'max_hotels': 25,
                'max_resorts': 25,
                'allow_property_replacement': True,
                'allow_subscription_renewal': True,
                'allow_expired_renewal': True,
                'is_active': True,
                'description': 'خطة تجارية للشركات والمكاتب العقارية'
            }
        )
        
        # Properties Iraq Plan
        PropertiesIraqPlan, created = AdvancedSubscriptionPlan.objects.get_or_create(
            name='عقارات داخل العراق',
            defaults={
                'plan_type': 'properties_iraq',
                'tier': 'regular',
                'price_per_day': 40,
                'price_per_month': 1200,
                'price_per_year': 14400,
                'max_properties': 30,
                'max_properties_regular': 25,
                'max_properties_premium': 5,
                'max_auctions': 0,
                'max_auctions_regular': 0,
                'max_auctions_premium': 0,
                'max_building_requests': 10,
                'max_jobs': 0,
                'max_services': 0,
                'max_hotels': 0,
                'max_resorts': 0,
                'allow_property_replacement': True,
                'allow_subscription_renewal': True,
                'allow_expired_renewal': True,
                'is_active': True,
                'description': 'خطة متخصصة للعقارات داخل العراق'
            }
        )
        
        # Services Plan
        ServicesPlan, created = AdvancedSubscriptionPlan.objects.get_or_create(
            name='خدمات ومهن',
            defaults={
                'plan_type': 'combined',
                'tier': 'regular',
                'price_per_day': 25,
                'price_per_month': 750,
                'price_per_year': 9000,
                'max_properties': 0,
                'max_properties_regular': 0,
                'max_properties_premium': 0,
                'max_auctions': 0,
                'max_auctions_regular': 0,
                'max_auctions_premium': 0,
                'max_building_requests': 0,
                'max_jobs': 20,
                'max_services': 20,
                'max_hotels': 0,
                'max_resorts': 0,
                'allow_property_replacement': False,
                'allow_subscription_renewal': True,
                'allow_expired_renewal': True,
                'is_active': True,
                'description': 'خطة متخصصة للخدمات والمهن'
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created realistic subscription plans')
        )