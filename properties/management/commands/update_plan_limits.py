from django.core.management.base import BaseCommand
from properties.models import AdvancedSubscriptionPlan


class Command(BaseCommand):
    help = 'Update existing plan limits with realistic numbers'

    def handle(self, *args, **options):
        # Update existing plans with realistic limits
        
        # Update Basic Plan
        try:
            basic_plan = AdvancedSubscriptionPlan.objects.get(name='الخطة الأساسية')
            basic_plan.max_properties = 20
            basic_plan.max_properties_regular = 18
            basic_plan.max_properties_premium = 2
            basic_plan.max_auctions = 5
            basic_plan.max_auctions_regular = 4
            basic_plan.max_auctions_premium = 1
            basic_plan.max_building_requests = 5
            basic_plan.max_jobs = 5
            basic_plan.max_services = 5
            basic_plan.max_hotels = 2
            basic_plan.max_resorts = 2
            basic_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Basic Plan'))
        except AdvancedSubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.WARNING('Basic Plan not found'))
        
        # Update Professional Plan
        try:
            pro_plan = AdvancedSubscriptionPlan.objects.get(name='الخطة الاحترافية')
            pro_plan.max_properties = 100
            pro_plan.max_properties_regular = 70
            pro_plan.max_properties_premium = 30
            pro_plan.max_auctions = 25
            pro_plan.max_auctions_regular = 18
            pro_plan.max_auctions_premium = 7
            pro_plan.max_building_requests = 20
            pro_plan.max_jobs = 20
            pro_plan.max_services = 20
            pro_plan.max_hotels = 10
            pro_plan.max_resorts = 10
            pro_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Professional Plan'))
        except AdvancedSubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.WARNING('Professional Plan not found'))
        
        # Update Business Plan
        try:
            business_plan = AdvancedSubscriptionPlan.objects.get(name='الخطة التجارية')
            business_plan.max_properties = 250
            business_plan.max_properties_regular = 150
            business_plan.max_properties_premium = 100
            business_plan.max_auctions = 50
            business_plan.max_auctions_regular = 35
            business_plan.max_auctions_premium = 15
            business_plan.max_building_requests = 50
            business_plan.max_jobs = 50
            business_plan.max_services = 50
            business_plan.max_hotels = 25
            business_plan.max_resorts = 25
            business_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Business Plan'))
        except AdvancedSubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.WARNING('Business Plan not found'))
        
        # Update default plan if exists
        try:
            default_plan = AdvancedSubscriptionPlan.objects.get(name='خطة افتراضية')
            default_plan.max_properties = 50
            default_plan.max_properties_regular = 40
            default_plan.max_properties_premium = 10
            default_plan.max_auctions = 20
            default_plan.max_auctions_regular = 15
            default_plan.max_auctions_premium = 5
            default_plan.max_building_requests = 15
            default_plan.max_jobs = 10
            default_plan.max_services = 10
            default_plan.max_hotels = 5
            default_plan.max_resorts = 5
            default_plan.save()
            self.stdout.write(self.style.SUCCESS('Updated Default Plan'))
        except AdvancedSubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.WARNING('Default Plan not found'))
        
        self.stdout.write(self.style.SUCCESS('Successfully updated all plan limits'))