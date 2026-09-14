"""
Enhanced Property Form with all new fields
نموذج العقار المحسّن مع جميع الحقول الجديدة
"""

from django import forms
from .models import Property, OutsideProperty


class EnhancedPropertyForm(forms.ModelForm):
    """نموذج إضافة عقار محسّن مع جميع الحقول الجديدة"""
    
    class Meta:
        model = Property
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الإعلان'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف العقار'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الحي'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'العنوان التفصيلي'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم التواصل'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set field classes
        for field_name, field in self.fields.items():
            if 'widget' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class EnhancedOutsidePropertyForm(forms.ModelForm):
    """نموذج إضافة عقار خارج العراق محسّن مع جميع الحقول الجديدة"""
    
    class Meta:
        model = OutsideProperty
        fields = '__all__'
        widgets = {
            'state_province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الولاية أو المحافظة'}),
            'county_region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المقاطعة أو المنطقة'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الرمز البريدي'}),
            'local_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة المحلية'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الشارع'}),
            'apartment_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الشقة'}),
            'building_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم المبنى'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الحي'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'taxes': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'registration_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transfer_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stamp_duty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'legal_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'foreign_ownership_laws': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'قوانين التملك للأجانب'}),
            'ownership_restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'قيود التملك'}),
            'residency_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'متطلبات الإقامة'}),
            'visa_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'متطلبات التأشيرة'}),
            'hoa_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'property_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'annual_maintenance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'insurance_premium': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'construction_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2099}),
            'renovation_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2099}),
            'building_certification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهادة البناء'}),
            'energy_rating': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تصنيف الطاقة'}),
            'insulation_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع العزل'}),
            'utility_provider_electric': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مزود الكهرباء'}),
            'utility_provider_gas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مزود الغاز'}),
            'utility_provider_water': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مزود الماء'}),
            'utility_provider_internet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مزود الإنترنت'}),
            'monthly_utilities_estimate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'security_system': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نظام الأمان'}),
            'fire_safety': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'سلامة الحريق'}),
            'public_transport_access': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'وصول النقل العام'}),
            'distance_to_airport': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'distance_to_city_center': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'distance_to_beach': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'distance_to_ski_resort': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'average_temperature': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'متوسط درجة الحرارة'}),
            'humidity_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مستوى الرطوبة'}),
            'rental_yield_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'appreciation_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deed_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم السند'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم التسجيل'}),
            'land_registry_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم سجل الأراضي'}),
            'parking_spaces': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ensuite_bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'guest_bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'management_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'property_management_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شركة إدارة العقارات'}),
            'insurance_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شركة التأمين'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم بوليصة التأمين'}),
            'seller_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات البائع'}),
            'buyer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات المشتري'}),
            'viewing_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'تعليمات المعاينة'}),
            'pet_restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'قيود الحيوانات الأليفة'}),
            'kitchen_appliances': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'أجهزة المطبخ'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set field classes
        for field_name, field in self.fields.items():
            if 'widget' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'