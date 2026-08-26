"""نماذج إدارة نظام الدلال"""

from django import forms
from .models import DallalGlobalSettings, BasicDallalSettings, PremiumDallalSettings, DallalSubscription, TravelCompany, ServiceProviderPage, ServiceProviderService, ServiceBooking, ServiceProviderReview


class DallalGlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = DallalGlobalSettings
        fields = '__all__'
        widgets = {
            'is_dallal_system_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_brokers_per_user': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_properties_per_dallal': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'show_dallal_on_homepage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dallal_display_order': forms.Select(attrs={'class': 'form-control'}),
            'show_expired_dallal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BasicDallalSettingsForm(forms.ModelForm):
    class Meta:
        model = BasicDallalSettings
        fields = '__all__'
        widgets = {
            'max_properties': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'impressions_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PremiumDallalSettingsForm(forms.ModelForm):
    class Meta:
        model = PremiumDallalSettings
        fields = '__all__'
        widgets = {
            'max_properties': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'priority_display': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'impressions_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visual_badge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'highlight_effect': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DallalSubscriptionForm(forms.ModelForm):
    class Meta:
        model = DallalSubscription
        fields = ['broker', 'subscription_type', 'start_date', 'end_date', 'auto_renewal']
        widgets = {
            'broker': forms.Select(attrs={'class': 'form-control'}),
            'subscription_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TravelCompanyForm(forms.ModelForm):
    """نموذج إنشاء شركة سفر للدلالين"""
    class Meta:
        model = TravelCompany
        fields = [
            'name', 'name_en', 'description', 'description_en',
            'company_type', 'travel_types', 'travel_scope', 'travel_type',
            'departure_time', 'price', 'price_currency',
            'destinations', 'facilities', 'services',
            'has_branches', 'branches_count', 'branch_locations',
            'booking_methods', 'advance_booking_days', 'cancellation_policy', 'cancellation_policy_en',
            'daily_capacity', 'monthly_capacity',
            'certifications', 'partners',
            'has_special_offers', 'special_offers',
            'working_hours',
            'phone', 'whatsapp', 'email', 'website',
            'facebook', 'instagram', 'twitter', 'telegram',
            'address', 'governorate', 'city',
            'latitude', 'longitude',
            'logo', 'cover_image', 'additional_images', 'video_url',
            'rating', 'reviews_count',
            'is_verified', 'is_featured', 'is_active',
            # Payment Information
            'payment_methods', 'accepts_installments', 'installment_options',
            # Insurance Information
            'provides_travel_insurance', 'insurance_providers', 'insurance_coverage',
            # Visa Services
            'provides_visa_services', 'visa_countries', 'visa_processing_time',
            # Hotel Partnerships
            'has_hotel_partnerships', 'hotel_partners', 'hotel_discounts',
            # Customer Support
            'support_phone', 'support_email', 'support_hours', 'has_24_7_support',
            # Emergency Contacts
            'emergency_phone', 'emergency_contacts',
            # Language Support
            'languages_spoken', 'has_multilingual_staff',
            # Vehicle Fleet
            'fleet_information', 'vehicle_types', 'fleet_maintenance',
            # Tour Packages
            'offers_packages', 'tour_packages', 'custom_packages',
            # Seasonal Offers
            'has_seasonal_offers', 'seasonal_offers',
            # Loyalty Program
            'has_loyalty_program', 'loyalty_benefits', 'points_system',
            # Refund Policy
            'refund_policy', 'refund_policy_en', 'refund_processing_days',
            # Terms and Conditions
            'terms_conditions', 'terms_conditions_en',
            # Safety Protocols
            'safety_measures', 'emergency_protocols', 'has_safety_certification',
            # COVID-19 Measures
            'covid_measures', 'health_guidelines',
            # Customer Testimonials
            'featured_testimonials',
            # Awards and Recognitions
            'awards', 'recognitions',
            # License Information
            'license_number', 'license_expiry', 'issuing_authority',
            # Service Coverage
            'service_areas', 'international_coverage',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الشركة بالعربية'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name in English'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف الشركة بالعربية'}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Company Description in English'}),
            'company_type': forms.Select(attrs={'class': 'form-control'}),
            'travel_types': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'أنواع السفر المدعومة (JSON format)', 'initial': ''}),
            'travel_scope': forms.Select(attrs={'class': 'form-control'}),
            'travel_type': forms.Select(attrs={'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'placeholder': 'السعر'}),
            'price_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة (IQD, USD, etc.)'}),
            'destinations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'الوجهات (JSON format: ["بغداد", "البصرة", "اربيل"])', 'initial': ''}),
            'facilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'المرافق (JSON format: ["حافلات", "فنادق", "مطاعم"])', 'initial': ''}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'الخدمات (JSON format: ["تأشيرات", "حجوزات", "تأمين"])', 'initial': ''}),
            'has_branches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'branches_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'عدد الفروع'}),
            'branch_locations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'مواقع الفروع (JSON format: [{"city": "بغداد", "address": "..."}])', 'initial': ''}),
            'booking_methods': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'طرق الحجز (JSON format: ["online", "phone", "office"])', 'initial': ''}),
            'advance_booking_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'أيام الحجز المسبق'}),
            'cancellation_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'سياسة الإلغاء بالعربية'}),
            'cancellation_policy_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cancellation Policy in English'}),
            'daily_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'السعة اليومية'}),
            'monthly_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'السعة الشهرية'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الشهادات (JSON format: ["ISO 9001", "وزارة السياحة"])', 'initial': ''}),
            'partners': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الشركاء (JSON format: ["شركة الطيران العراقية", "فنادق راديسون"])', 'initial': ''}),
            'has_special_offers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_offers': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'العروض الخاصة (JSON format: [{"title": "عرض رمضان", "discount": "20%"}])', 'initial': ''}),
            'working_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ساعات العمل (JSON format: {"saturday": "9-17", "sunday": "9-17"})', 'initial': ''}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الواتساب'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'الموقع الإلكتروني'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'فيسبوك'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'انستغرام'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'تويتر'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تيليجرام'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العنوان'}),
            'governorate': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'placeholder': 'خط العرض'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'placeholder': 'خط الطول'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'additional_images': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'صور إضافية (JSON format: ["url1", "url2"])', 'initial': ''}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط الفيديو'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5, 'step': 0.1}),
            'reviews_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Payment Information
            'payment_methods': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'طرق الدفع (JSON format: ["cash", "card", "bank_transfer"])', 'initial': ''}),
            'accepts_installments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installment_options': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'خيارات التقسيط (JSON format)', 'initial': ''}),
            # Insurance Information
            'provides_travel_insurance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurance_providers': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'شركات التأمين (JSON format)', 'initial': ''}),
            'insurance_coverage': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'تغطية التأمين'}),
            # Visa Services
            'provides_visa_services': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visa_countries': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'دول التأشيرة (JSON format)', 'initial': ''}),
            'visa_processing_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'وقت معالجة التأشيرة'}),
            # Hotel Partnerships
            'has_hotel_partnerships': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hotel_partners': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الفنادق الشريكة (JSON format)', 'initial': ''}),
            'hotel_discounts': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'خصومات الفنادق'}),
            # Customer Support
            'support_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'هاتف الدعم'}),
            'support_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'بريد الدعم'}),
            'support_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ساعات الدعم'}),
            'has_24_7_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Emergency Contacts
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'هاتف الطوارئ'}),
            'emergency_contacts': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'جهات اتصال الطوارئ (JSON format)', 'initial': ''}),
            # Language Support
            'languages_spoken': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'اللغات المتحدثة (JSON format: ["العربية", "الإنجليزية"])', 'initial': ''}),
            'has_multilingual_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Vehicle Fleet
            'fleet_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'معلومات الأسطول (JSON format)', 'initial': ''}),
            'vehicle_types': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'أنواع المركبات (JSON format)', 'initial': ''}),
            'fleet_maintenance': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'صيانة الأسطول'}),
            # Tour Packages
            'offers_packages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tour_packages': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'الباقات السياحية (JSON format)', 'initial': ''}),
            'custom_packages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Seasonal Offers
            'has_seasonal_offers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'seasonal_offers': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'العروض الموسمية (JSON format)', 'initial': ''}),
            # Loyalty Program
            'has_loyalty_program': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'loyalty_benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'مزايا الولاء'}),
            'points_system': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'نظام النقاط (JSON format)', 'initial': ''}),
            # Refund Policy
            'refund_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'سياسة الاسترداد'}),
            'refund_policy_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Refund Policy in English'}),
            'refund_processing_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'أيام معالجة الاسترداد'}),
            # Terms and Conditions
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'الشروط والأحكام'}),
            'terms_conditions_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Terms and Conditions in English'}),
            # Safety Protocols
            'safety_measures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'إجراءات السلامة'}),
            'emergency_protocols': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'بروتوكولات الطوارئ'}),
            'has_safety_certification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # COVID-19 Measures
            'covid_measures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'إجراءات كوفيد-19'}),
            'health_guidelines': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'إرشادات صحية'}),
            # Customer Testimonials
            'featured_testimonials': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'شهادات العملاء المميزة (JSON format)', 'initial': ''}),
            # Awards and Recognitions
            'awards': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الجوائز والتقديرات (JSON format)', 'initial': ''}),
            'recognitions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الاعترافات (JSON format)', 'initial': ''}),
            # License Information
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الترخيص'}),
            'license_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'issuing_authority': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'جهة الإصدار'}),
            # Service Coverage
            'service_areas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'مناطق الخدمة (JSON format)', 'initial': ''}),
            'international_coverage': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'التغطية الدولية (JSON format)', 'initial': ''}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for JSON fields to empty string
        json_fields = [
            'travel_types', 'destinations', 'facilities', 'services',
            'branch_locations', 'booking_methods', 'certifications', 'partners',
            'special_offers', 'working_hours', 'additional_images', 'payment_methods',
            'installment_options', 'insurance_providers', 'visa_countries',
            'hotel_partners', 'emergency_contacts', 'languages_spoken',
            'fleet_information', 'vehicle_types', 'tour_packages', 'seasonal_offers',
            'points_system', 'featured_testimonials', 'awards', 'recognitions',
            'service_areas', 'international_coverage'
        ]
        for field in json_fields:
            if not self.instance.pk:  # Only for new instances
                self.fields[field].initial = ''


class ServiceProviderPageForm(forms.ModelForm):
    """نموذج إنشاء صفحة مقدم خدمة"""
    class Meta:
        model = ServiceProviderPage
        fields = [
            'name', 'slug', 'page_type', 'description',
            'category', 'sub_categories', 'years_of_experience', 'projects_count', 'clients_count',
            'governorate', 'city', 'working_areas', 'latitude', 'longitude',
            'phone', 'whatsapp', 'telegram', 'facebook', 'instagram', 'website',
            'profile_image', 'cover_image', 'logo',
            'working_hours', 'availability',
            'meta_title', 'meta_description', 'meta_keywords'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم مقدم الخدمة'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الرابط المختصر'}),
            'page_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'نبذة عن مقدم الخدمة'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'projects_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'clients_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'governorate': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
            'working_areas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'المناطق التي يعمل بها'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'واتساب'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تيليجرام'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'فيسبوك'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'انستغرام'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'الموقع الإلكتروني'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'working_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'أوقات الدوام'}),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان SEO'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'وصف SEO'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'كلمات مفتاحية SEO'}),
        }


class ServiceProviderServiceForm(forms.ModelForm):
    """نموذج إضافة خدمة لمقدم الخدمة"""
    class Meta:
        model = ServiceProviderService
        fields = ['name', 'description', 'price', 'price_unit', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الخدمة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'وصف الخدمة'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'price_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'وحدة السعر'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ServiceBookingForm(forms.ModelForm):
    """نموذج حجز خدمة"""
    class Meta:
        model = ServiceBooking
        fields = [
            'service', 'provider_page', 'customer_name', 'customer_phone', 'customer_email',
            'booking_date', 'booking_time', 'duration', 'location_type', 'address',
            'total_price', 'deposit_amount', 'notes'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم العميل'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 15}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العنوان'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات إضافية'}),
        }


class ServiceProviderReviewForm(forms.ModelForm):
    """نموذج تقييم مقدم خدمة"""
    class Meta:
        model = ServiceProviderReview
        fields = [
            'provider', 'service', 'booking', 'overall_rating',
            'quality', 'professionalism', 'punctuality', 'communication', 'value_for_money',
            'title', 'comment', 'service_date', 'service_type'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان التقييم'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'اكتب تجربتك مع مقدم الخدمة'}),
            'service_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'service_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع الخدمة'}),
        }
