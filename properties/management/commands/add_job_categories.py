from django.core.management.base import BaseCommand
from properties.models import JobCategory


class Command(BaseCommand):
    help = 'Add default job categories to the database'

    def handle(self, *args, **options):
        categories = [
            {
                'name_ar': 'وظيفة حكومية',
                'name_en': 'Government Job',
                'icon': '🏛️',
                'description': 'وظائف في القطاع الحكومي والوزارات'
            },
            {
                'name_ar': 'وظيفة في شركة',
                'name_en': 'Corporate Job',
                'icon': '🏢',
                'description': 'وظائف في الشركات الخاصة'
            },
            {
                'name_ar': 'وظيفة في متجر / محل',
                'name_en': 'Retail Job',
                'icon': '🏪',
                'description': 'وظائف في المتاجر والمحلات التجارية'
            },
            {
                'name_ar': 'عمل حر',
                'name_en': 'Freelance',
                'icon': '💼',
                'description': 'عمل حر ومشاريع مستقلة'
            },
            {
                'name_ar': 'سائق',
                'name_en': 'Driver',
                'icon': '🚗',
                'description': 'وظائف قيادة المركبات'
            },
            {
                'name_ar': 'توصيل',
                'name_en': 'Delivery',
                'icon': '🛵',
                'description': 'وظائف التوصيل والشحن'
            },
            {
                'name_ar': 'عمل ميداني / عمال',
                'name_en': 'Field Work / Labor',
                'icon': '🏗️',
                'description': 'وظائف العمل الميداني والعمالة'
            },
            {
                'name_ar': 'حرف ومهن',
                'name_en': 'Crafts and Trades',
                'icon': '🔧',
                'description': 'وظائف الحرف والمهن اليدوية'
            },
            {
                'name_ar': 'عمل عن بُعد',
                'name_en': 'Remote Work',
                'icon': '💻',
                'description': 'وظائف العمل عن بعد'
            },
            {
                'name_ar': 'عمل من المنزل',
                'name_en': 'Work from Home',
                'icon': '🏠',
                'description': 'وظائف يمكن القيام بها من المنزل'
            },
            {
                'name_ar': 'تدريب / متدرب',
                'name_en': 'Training / Internship',
                'icon': '🎓',
                'description': 'فرص التدريب والتدريب المهني'
            },
            {
                'name_ar': 'عمل إداري',
                'name_en': 'Administrative Work',
                'icon': '🧑‍💼',
                'description': 'وظائف إدارية ومكتبية'
            },
            {
                'name_ar': 'قطاع صحي',
                'name_en': 'Healthcare',
                'icon': '🏥',
                'description': 'وظائف في القطاع الصحي والطبي'
            },
            {
                'name_ar': 'تعليم / تدريس',
                'name_en': 'Education / Teaching',
                'icon': '🏫',
                'description': 'وظائف في قطاع التعليم والتدريس'
            },
            {
                'name_ar': 'مطاعم ومقاهي',
                'name_en': 'Restaurants and Cafes',
                'icon': '🍽️',
                'description': 'وظائف في المطاعم والمقاهي'
            },
            {
                'name_ar': 'فنادق وسياحة',
                'name_en': 'Hotels and Tourism',
                'icon': '🏨',
                'description': 'وظائف في الفنادق والسياحة'
            },
            {
                'name_ar': 'أمن وحراسة',
                'name_en': 'Security and Guard',
                'icon': '🛡️',
                'description': 'وظائف الأمن والحراسة'
            },
            {
                'name_ar': 'مبيعات وتسويق',
                'name_en': 'Sales and Marketing',
                'icon': '🛒',
                'description': 'وظائف المبيعات والتسويق'
            },
            {
                'name_ar': 'مخازن ومستودعات',
                'name_en': 'Warehouses',
                'icon': '📦',
                'description': 'وظائف في المخازن والمستودعات'
            },
            {
                'name_ar': 'مصانع / إنتاج',
                'name_en': 'Factories / Production',
                'icon': '🏭',
                'description': 'وظائف في المصانع والإنتاج'
            },
            {
                'name_ar': 'زراعة',
                'name_en': 'Agriculture',
                'icon': '🌾',
                'description': 'وظائف في قطاع الزراعة'
            },
            {
                'name_ar': 'منظمات / مؤسسات',
                'name_en': 'Organizations',
                'icon': '🏥',
                'description': 'وظائف في المنظمات والمؤسسات'
            },
            {
                'name_ar': 'وظائف دولية',
                'name_en': 'International Jobs',
                'icon': '🌐',
                'description': 'وظائف دولية وعبر الحدود'
            },
        ]

        created_count = 0
        updated_count = 0
        
        for category_data in categories:
            category, created = JobCategory.objects.get_or_create(
                name_ar=category_data['name_ar'],
                defaults={
                    'name_en': category_data['name_en'],
                    'icon': category_data['icon'],
                    'description': category_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                print(f'Created: {category.name_en}')
            else:
                # Update existing category
                category.name_en = category_data['name_en']
                category.icon = category_data['icon']
                category.description = category_data['description']
                category.is_active = True
                category.save()
                updated_count += 1
                print(f'Updated: {category.name_en}')
        
        print(f'Successfully added {created_count} new categories and updated {updated_count} existing categories')