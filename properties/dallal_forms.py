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
            'name', 'description', 'company_type',
            'phone', 'whatsapp', 'email', 'website',
            'facebook', 'instagram', 'twitter', 'telegram',
            'governorate', 'city', 'address',
            'cover_image', 'logo',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم شركة السفر'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'اكتب وصف الشركة هنا...'}),
            'company_type': forms.Select(attrs={'class': 'form-control', 'placeholder': 'اختر نوع الشركة'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07xxxxxxxxx'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07xxxxxxxxx'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'website': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'facebook': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'twitter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/...'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'governorate': forms.Select(attrs={'class': 'form-control', 'placeholder': 'اختر المحافظة'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المدينة'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العنوان التفصيلي'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required at Django level, not HTML level
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['company_type'].required = True
        self.fields['phone'].required = True
        self.fields['email'].required = True
        self.fields['governorate'].required = True
        self.fields['city'].required = True
        self.fields['address'].required = True
        self.fields['logo'].required = True
        self.fields['cover_image'].required = True
        
        # Optional fields
        self.fields['website'].required = False
        self.fields['facebook'].required = False
        self.fields['instagram'].required = False
        self.fields['twitter'].required = False
        self.fields['telegram'].required = False
        self.fields['whatsapp'].required = False
        
        # Add empty label for select fields
        self.fields['company_type'].empty_label = 'اختر نوع الشركة'
        self.fields['governorate'].empty_label = 'اختر المحافظة'


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
