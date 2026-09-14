"""
Publication Service - موحدة نظام النشر لجميع أنواع الإعلانات

هذه الخدمة مسؤولة عن:
- إنشاء الإعلانات من /add/dynamic/
- تحديد صفحة التصنيف المناسبة
- إدارة الحالات (draft, published, pending, etc.)
- التعامل مع featured و pinned
- التحقق من الاشتراكات
- استخدام transactions لضمان سلامة البيانات
"""

from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from decimal import Decimal

from properties.models import (
    Property, OutsideProperty, PropertyHotel, PropertyResort,
    Broker, SubscriptionRenewalRequest, Country, BrokerPlanSubscription
)
from properties.constants import IRAQ_GOVERNORATES
from .subscription_validation_service import SubscriptionValidationService


# ==================== Publication Constants ====================

# تصنيفات النشر
CATEGORY_PROPERTY_IRAQ = 'property_iraq'
CATEGORY_PROPERTY_OUTSIDE = 'property_outside'
CATEGORY_HOTEL = 'hotel'
CATEGORY_RESORT = 'resort'

# حالات النشر
STATUS_DRAFT = 'draft'
STATUS_PUBLISHED = 'published'
STATUS_PENDING = 'pending'
STATUS_REJECTED = 'rejected'
STATUS_EXPIRED = 'expired'

# حالات عامة للعرض
PUBLIC_STATUSES = ['published', 'renewed', 'ready']

# مدد النشر المسموحة
PUBLICATION_DAYS_CHOICES = [1, 3, 7, 15, 30]

# Mapping بين نوع النشر وصفحة التصنيف
PUBLICATION_TARGETS = {
    CATEGORY_PROPERTY_IRAQ: {
        'url_name': 'category_inside_iraq',
        'url_path': '/category/inside-iraq/',
        'display_name': 'عقارات داخل العراق',
        'icon': '🏠',
        'model': 'Property',
        'country_filter': 'IQ',
    },
    CATEGORY_PROPERTY_OUTSIDE: {
        'url_name': 'category_outside_iraq',
        'url_path': '/category/outside-iraq/',
        'display_name': 'عقارات خارج العراق',
        'icon': '🌍',
        'model': 'Property',
        'country_filter': '!IQ',
    },
    CATEGORY_HOTEL: {
        'url_name': 'category_hotels',
        'url_path': '/category/hotels/',
        'display_name': 'فنادق',
        'icon': '🏨',
        'model': 'PropertyHotel',
        'country_filter': 'both',
    },
    CATEGORY_RESORT: {
        'url_name': 'category_resorts',
        'url_path': '/category/resorts/',
        'display_name': 'منتجعات',
        'icon': '🏖️',
        'model': 'PropertyResort',
        'country_filter': 'both',
    },
}


# ==================== Publication Service ====================

class PublicationService:
    """خدمة النشر الموحدة للإعلانات"""
    
    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.errors = []
        self.warnings = []
        self.subscription_service = SubscriptionValidationService(request)
        
    def validate_publication_days(self, days):
        """التحقق من صحة مدة النشر"""
        try:
            days = int(days)
            if days not in PUBLICATION_DAYS_CHOICES:
                self.errors.append(f'مدة النشر يجب أن تكون واحدة من: {PUBLICATION_DAYS_CHOICES}')
                return False
            return days
        except (ValueError, TypeError):
            self.errors.append('مدة النشر يجب أن تكون رقماً صحيحاً')
            return False
    
    def check_subscription_limits(self, broker, is_featured):
        """التحقق من حدود الاشتراك"""
        if not broker:
            # المستخدم العادي - السماح بنشر محدود
            return True, 'user'
        
        # الحصول على آخر تجديد اشتراك
        latest_renewal = SubscriptionRenewalRequest.objects.filter(
            broker=broker,
            status='approved'
        ).order_by('-approved_at').first()
        
        if not latest_renewal:
            self.errors.append('لا يوجد اشتراك نشط')
            return False, None
        
        # التحقق من نوع الاشتراك
        is_all_inclusive = (
            latest_renewal.subscription_type == 'all_inclusive' or 
            'all_inclusive' in latest_renewal.subscription_types
        )
        
        if is_all_inclusive:
            return True, 'all_inclusive'
        
        # حساب العقارات المتبقية
        existing_properties = Property.objects.filter(owner=self.user)
        if is_featured:
            existing_count = existing_properties.filter(is_featured=True).count()
            available = latest_renewal.premium_count
        else:
            existing_count = existing_properties.filter(is_featured=False).count()
            available = latest_renewal.regular_count
        
        if existing_count >= available:
            self.errors.append(
                f'لقد استنفدت حدك الحالي. المتبقي: {max(0, available - existing_count)}'
            )
            return False, None
        
        return True, latest_renewal.subscription_type
    
    def calculate_expiry_date(self, publication_days):
        """حساب تاريخ انتهاء النشر"""
        if not publication_days:
            return None
        return timezone.now() + timedelta(days=publication_days)
    
    def calculate_pinned_expiry(self, is_pinned, publication_days):
        """حساب تاريخ انتهاء التثبيت"""
        if not is_pinned:
            return None
        # التثبيت يكون لنفس مدة النشر أو 7 أيام كحد أدنى
        pinned_days = max(publication_days or 7, 7)
        return timezone.now() + timedelta(days=pinned_days)
    
    def get_broker_for_user(self):
        """الحصول على الدلال للمستخدم"""
        try:
            return Broker.objects.get(user=self.user)
        except Broker.DoesNotExist:
            return None
    
    def get_country_by_code(self, code):
        """الحصول على الدولة بالكود"""
        try:
            return Country.objects.get(code=code)
        except Country.DoesNotExist:
            return None
    
    def validate_category_data(self, category, data):
        """التحقق من بيانات التصنيف"""
        if category == CATEGORY_PROPERTY_IRAQ:
            # التحقق من المحافظة للعقارات داخل العراق
            governorate = data.get('governorate')
            if not governorate:
                self.errors.append('يرجى اختيار المحافظة للعقارات داخل العراق')
                return False
            if governorate not in [gov[0] for gov in IRAQ_GOVERNORATES]:
                self.errors.append('المحافظة المختارة غير صالحة')
                return False
            return True
        
        elif category == CATEGORY_PROPERTY_OUTSIDE:
            # التحقق من الدولة للعقارات خارج العراق
            country_id = data.get('country')
            if not country_id:
                self.errors.append('يرجى اختيار الدولة للعقارات خارج العراق')
                return False
            return True
        
        elif category == CATEGORY_HOTEL:
            # التحقق من بيانات الفندق
            hotel_name = data.get('hotel_name')
            if not hotel_name:
                self.errors.append('يرجى إدخال اسم الفندق')
                return False
            return True
        
        elif category == CATEGORY_RESORT:
            # التحقق من بيانات المنتجع
            resort_name = data.get('resort_name')
            if not resort_name:
                self.errors.append('يرجى إدخال اسم المنتجع')
                return False
            return True
        
        return True
    
    @transaction.atomic
    def publish_property_iraq(self, data, is_featured, is_pinned, publication_days, broker, subscription):
        """نشر عقار داخل العراق"""
        from properties.models import Property
        
        # الحصول على الدولة (العراق)
        iraq = self.get_country_by_code('IQ')
        
        # حساب التواريخ
        expiry_date = self.calculate_expiry_date(publication_days)
        pinned_until = self.calculate_pinned_expiry(is_pinned, publication_days)
        
        # إنشاء العقار مع الربط بالاشتراك
        property = Property.objects.create(
            title=data.get('title', ''),
            type=data.get('type', 'apartment'),
            category=CATEGORY_PROPERTY_IRAQ,
            owner=self.user,
            broker=broker,
            subscription=subscription,
            status=STATUS_PUBLISHED,
            is_featured=is_featured,
            is_pinned=is_pinned,
            pinned_until=pinned_until,
            expiry_date=expiry_date,
            price=data.get('price', 0),
            governorate=data.get('governorate', ''),
            city=data.get('city', ''),
            district=data.get('district', ''),
            location=data.get('location', ''),
            country=iraq,
            area=data.get('area', 0),
            description=data.get('description', ''),
            # المزيد من الحقول حسب الحاجة
        )
        
        return property, CATEGORY_PROPERTY_IRAQ
    
    @transaction.atomic
    def publish_property_outside(self, data, is_featured, is_pinned, publication_days, broker, subscription):
        """نشر عقار خارج العراق"""
        from properties.models import Property, OutsideProperty
        
        # الحصول على الدولة
        country_id = data.get('country')
        try:
            country = Country.objects.get(id=country_id)
        except Country.DoesNotExist:
            self.errors.append('الدولة المختارة غير موجودة')
            return None, None
        
        # حساب التواريخ
        expiry_date = self.calculate_expiry_date(publication_days)
        pinned_until = self.calculate_pinned_expiry(is_pinned, publication_days)
        
        # إنشاء العقار مع الربط بالاشتراك
        property = Property.objects.create(
            title=data.get('title', ''),
            type=data.get('type', 'apartment'),
            category=CATEGORY_PROPERTY_OUTSIDE,
            owner=self.user,
            broker=broker,
            subscription=subscription,
            status=STATUS_PUBLISHED,
            is_featured=is_featured,
            is_pinned=is_pinned,
            pinned_until=pinned_until,
            expiry_date=expiry_date,
            price=data.get('price', 0),
            country=country,
            city_outside=data.get('city_outside'),
            area_outside=data.get('area_outside'),
            description=data.get('description', ''),
            currency=data.get('currency', 'USD'),
            # المزيد من الحقول حسب الحاجة
        )
        
        # إنشاء تفاصيل العقار الخارجي
        OutsideProperty.objects.create(
            property=property,
            state_province=data.get('state_province', ''),
            county_region=data.get('county_region', ''),
            postal_code=data.get('postal_code', ''),
            local_currency=data.get('local_currency', ''),
            street_address=data.get('street_address', ''),
            apartment_number=data.get('apartment_number', ''),
            building_number=data.get('building_number', ''),
            neighborhood=data.get('neighborhood', ''),
            # المزيد من الحقول حسب الحاجة
        )
        
        return property, CATEGORY_PROPERTY_OUTSIDE
    
    @transaction.atomic
    def publish_hotel(self, data, is_featured, is_pinned, publication_days, broker, subscription):
        """نشر فندق"""
        from properties.models import Property, PropertyHotel
        
        # تحديد الدولة
        country_code = data.get('country_code', 'IQ')
        country = self.get_country_by_code(country_code)
        
        # حساب التواريخ
        expiry_date = self.calculate_expiry_date(publication_days)
        pinned_until = self.calculate_pinned_expiry(is_pinned, publication_days)
        
        # إنشاء العقار الأساسي مع الربط بالاشتراك
        property = Property.objects.create(
            title=data.get('hotel_name', ''),
            type='hotel',
            category=CATEGORY_HOTEL,
            owner=self.user,
            broker=broker,
            subscription=subscription,
            status=STATUS_PUBLISHED,
            is_featured=is_featured,
            is_pinned=is_pinned,
            pinned_until=pinned_until,
            expiry_date=expiry_date,
            country=country,
            governorate=data.get('governorate', ''),
            city=data.get('city', ''),
            description=data.get('description', ''),
        )
        
        # إنشاء تفاصيل الفندق
        hotel = PropertyHotel.objects.create(
            property=property,
            hotel_name=data.get('hotel_name', ''),
            star_rating=data.get('star_rating', 3),
            classification=data.get('classification', ''),
            total_rooms=data.get('total_rooms', 10),
            suites=data.get('suites'),
            family_rooms=data.get('family_rooms'),
            price_per_night=data.get('price_per_night'),
            currency=data.get('currency', 'USD'),
            booking_url=data.get('booking_url', ''),
            governorate=data.get('governorate', ''),
            # المزيد من الحقول حسب الحاجة
        )
        
        return property, CATEGORY_HOTEL
    
    @transaction.atomic
    def publish_resort(self, data, is_featured, is_pinned, publication_days, broker, subscription):
        """نشر منتجع"""
        from properties.models import Property, PropertyResort
        
        # حساب التواريخ
        expiry_date = self.calculate_expiry_date(publication_days)
        pinned_until = self.calculate_pinned_expiry(is_pinned, publication_days)
        
        # إنشاء العقار الأساسي مع الربط بالاشتراك
        property = Property.objects.create(
            title=data.get('resort_name', ''),
            type='resort',
            category=CATEGORY_RESORT,
            owner=self.user,
            broker=broker,
            subscription=subscription,
            status=STATUS_PUBLISHED,
            is_featured=is_featured,
            is_pinned=is_pinned,
            pinned_until=pinned_until,
            expiry_date=expiry_date,
            governorate=data.get('governorate', ''),
            city=data.get('city', ''),
            district=data.get('district', ''),
            location=data.get('address', ''),
            description=data.get('description', ''),
        )
        
        # إنشاء تفاصيل المنتجع
        resort = PropertyResort.objects.create(
            property=property,
            resort_type=data.get('resort_type', 'resort'),
            resort_name=data.get('resort_name', ''),
            governorate=data.get('governorate', ''),
            city=data.get('city', ''),
            district=data.get('district', ''),
            address=data.get('address', ''),
            max_guests=data.get('max_guests', 10),
            min_guests=data.get('min_guests', 1),
            price_per_night=data.get('price_per_night'),
            price_per_week=data.get('price_per_week'),
            price_per_month=data.get('price_per_month'),
            currency=data.get('currency', 'USD'),
            description=data.get('description', ''),
            # المزيد من الحقول حسب الحاجة
        )
        
        return property, CATEGORY_RESORT
    

    
    @transaction.atomic
    def publish(self, category, data, is_featured=False, is_pinned=False, publication_days=30):
        """
        الدالة الرئيسية للنشر مع التحقق الكامل من الاشتراك
        
        Args:
            category: نوع التصنيف (property_iraq, property_outside, hotel, resort)
            data: بيانات الإعلان (dict)
            is_featured: هل الإعلان مميز
            is_pinned: هل الإعلان مثبت
            publication_days: مدة النشر بالأيام
        
        Returns:
            tuple: (property, category_target, success, subscription_info)
        """
        # التحقق من صحة البيانات
        if not self.validate_category_data(category, data):
            return None, None, False, None
        
        # التحقق الشامل من الاشتراك باستخدام SubscriptionValidationService
        can_publish, broker, subscription, validated_days = self.subscription_service.can_publish(
            is_featured=is_featured,
            publication_days=publication_days
        )
        
        if not can_publish:
            self.errors.extend(self.subscription_service.errors)
            return None, None, False, None
        
        # التحقق من أن المستخدم دلال (يجب أن يكون دلال للنشر)
        if not broker:
            self.errors.append('يجب أن تكون دلال للنشر. المستخدمون العاديون لا يمكنهم النشر.')
            return None, None, False, None
        
        # استخدام الاشتراك الذي تم التحقق منه
        publication_days = validated_days
        
        # استهلاك حصة الاشتراك مع select_for_update
        quota_consumed = self.subscription_service.consume_publication_quota(subscription, is_featured)
        if not quota_consumed:
            self.errors.append('لا يمكن استهلاك حصة الاشتراك. قد يكون الاشتراك قد استنفذ.')
            return None, None, False, None
        
        # النشر حسب النوع
        try:
            if category == CATEGORY_PROPERTY_IRAQ:
                property, result_category = self.publish_property_iraq(
                    data, is_featured, is_pinned, publication_days, broker, subscription
                )
            elif category == CATEGORY_PROPERTY_OUTSIDE:
                property, result_category = self.publish_property_outside(
                    data, is_featured, is_pinned, publication_days, broker, subscription
                )
            elif category == CATEGORY_HOTEL:
                property, result_category = self.publish_hotel(
                    data, is_featured, is_pinned, publication_days, broker, subscription
                )
            elif category == CATEGORY_RESORT:
                property, result_category = self.publish_resort(
                    data, is_featured, is_pinned, publication_days, broker, subscription
                )
            else:
                self.errors.append(f'نوع التصنيف غير مدعوم: {category}')
                return None, None, False, None
            
            # ربط الإعلان بالاشتراك
            self.subscription_service.link_property_to_subscription(property, subscription)
            
            # إنشاء Audit Log
            self.subscription_service.create_audit_log(property, subscription, 'published')
            
            # الحصول على معلومات الاشتراك للعرض
            subscription_info = self.subscription_service.get_publication_info(subscription)
            
            return property, result_category, True, subscription_info
            
        except Exception as e:
            self.errors.append(f'حدث خطأ أثناء النشر: {str(e)}')
            return None, None, False, None
    
    def get_publication_target(self, category):
        """الحصول على معلومات صفحة التصنيف"""
        return PUBLICATION_TARGETS.get(category, {})
    
    def get_success_message(self, property, category, subscription_info=None):
        """الحصول على رسالة النجاح مع معلومات الاشتراك"""
        target = self.get_publication_target(category)
        
        message = f'''
        ✅ تم نشر الإعلان بنجاح
        
        نوع الإعلان: {target.get('display_name', category)}
        مكان الظهور: {target.get('display_name', category)}
        رقم الإعلان: {property.property_number or property.id}
        '''
        
        # إضافة معلومات الاشتراك إذا كانت متوفرة
        if subscription_info:
            plan_name = subscription_info.get('plan_name', 'غير محدد')
            message += f'''
        
        تم ربط الإعلان باشتراكك الحالي:
        {plan_name}
        '''
        
        return message.strip()
