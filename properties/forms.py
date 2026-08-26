from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.utils import timezone

from .constants import COMMON_NASIRIYAH_DISTRICTS, IRAQ_GOVERNORATES
from .models import Property, Message, SiteSettings, PropertyImage, PropertyVideo, PropertyNote, VirtualTour360, Auction, Bid, FinancialTransaction, Expense, Payment, Report, Profit, SubscriptionPlan, UserSettings, BlockedUser, SavedSearch, OfficePresence, PresenceNotification, BrokerSubscription, BrokerNotificationSettings, AutoBid, AuctionRating, AuctionLiveStream, AuctionAdvertisement, Hotel, Resort, PaymentMethod, PropertyPayment, PropertyNotification, SubscriptionRequest, BrokerChannel, ChannelRating, ChannelReview, ChannelReviewReply, ChannelMilestone, OutsideProperty, PropertyHotel, PropertyResort, PropertyDocument, PropertyMediaStats, WhatsAppMessage, TelegramMessage, AppointmentBooking, PropertyInquiry, LiveStream, LiveStreamComment, UserProfile, ServiceProvider, ServiceAdvertisement, HotelPage, HotelPost, HotelRoom, HotelOffer, HotelBooking, ServiceProviderCategory, ServiceProviderPage, ServiceProviderWork, ServiceProviderService, ServiceProviderGallery, ServiceProviderVideo, ServiceProvider360, ServiceProviderFollower, ServiceProviderRating, ServiceProviderContact, ServiceProviderQuote, Job, JobCategory, JobImage, JobVideo, BuildingAdvertisement, AdResponse, AdNotificationSettings, ChannelSubscription, ChannelContent, ChannelBroadcast, ChannelCollaboration, ChannelAdvertisement, SupportMessage, Notification, NotificationRecipient, Broker, BrokerConversation, BrokerMessage, RealEstateContract, ContractPayment, ContractDocument, ContractReminder, TravelPackage, TravelPackageImage, TravelPackageBooking, TravelPackageReview


def _fc(placeholder=''):
    attrs = {'class': 'form-control'}
    if placeholder:
        attrs['placeholder'] = placeholder
    return attrs


class MessageForm(forms.Form):
    """نموذج رسالة التواصل البسيط"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
        label='الاسم'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
        label='البريد الإلكتروني'
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
        label='رقم الهاتف',
        required=False
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'اكتب رسالتك هنا...'}),
        label='الرسالة'
    )


class SupportMessageForm(forms.ModelForm):
    """نموذج إرسال رسالة الدعم الفني"""
    
    class Meta:
        model = SupportMessage
        fields = ['message_type', 'subject', 'content', 'priority']
        widgets = {
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'موضوع الرسالة'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'اكتب رسالتك هنا...'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'message_type': 'نوع الرسالة',
            'subject': 'الموضوع',
            'content': 'المحتوى',
            'priority': 'الأولوية',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message_type'].choices = [
            ('inquiry', 'استفسار'),
            ('complaint', 'شكوى'),
            ('suggestion', 'اقتراح'),
            ('technical', 'مشكلة تقنية'),
            ('other', 'أخرى'),
        ]
        self.fields['priority'].choices = [
            ('low', 'منخفضة'),
            ('medium', 'متوسطة'),
            ('high', 'عالية'),
            ('urgent', 'عاجلة'),
        ]


class PropertyForm(forms.ModelForm):
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


class PropertySearchForm(forms.Form):
    q = forms.CharField(required=False, label='بحث', widget=forms.TextInput(attrs=_fc('ابحث عن عقار، فندق، منتجع...')))
    governorate = forms.ChoiceField(required=False, label='المحافظة', choices=[('', 'كل المحافظات')] + list(IRAQ_GOVERNORATES))
    district = forms.CharField(required=False, label='الحي/المنطقة', widget=forms.TextInput(attrs=_fc('الحي/المنطقة')))
    city = forms.CharField(required=False, label='المدينة', widget=forms.TextInput(attrs=_fc('المدينة')))
    country = forms.CharField(required=False, label='الدولة', widget=forms.TextInput(attrs=_fc('الدولة')))
    street = forms.CharField(required=False, label='الشارع', widget=forms.TextInput(attrs=_fc('الشارع')))
    type = forms.ChoiceField(required=False, label='نوع العقار', choices=[('', 'كل الأنواع')])
    status = forms.ChoiceField(required=False, label='الحالة', choices=[('', 'كل الحالات')])
    price_min = forms.IntegerField(required=False, label='السعر من', validators=[MinValueValidator(0)])
    price_max = forms.IntegerField(required=False, label='السعر إلى', validators=[MinValueValidator(0)])
    currency = forms.ChoiceField(required=False, label='العملة', choices=[('', 'كل العملات'), ('IQD', 'دينار عراقي'), ('USD', 'دولار أمريكي')])
    area_min = forms.IntegerField(required=False, label='المساحة من', validators=[MinValueValidator(0)])
    area_max = forms.IntegerField(required=False, label='المساحة إلى', validators=[MinValueValidator(0)])
    bedrooms = forms.IntegerField(required=False, label='الغرف', validators=[MinValueValidator(0)])
    bathrooms = forms.IntegerField(required=False, label='الحمامات', validators=[MinValueValidator(0)])
    floors = forms.IntegerField(required=False, label='الطوابق', validators=[MinValueValidator(0)])
    year_built = forms.IntegerField(required=False, label='سنة البناء', validators=[MinValueValidator(0)])
    property_condition = forms.ChoiceField(required=False, label='حالة العقار', choices=[('', 'كل الحالات'), ('new', 'جديد'), ('used', 'مستعمل'), ('under_construction', 'قيد البناء')])
    category = forms.ChoiceField(required=False, label='القسم', choices=[
        ('', 'كل الأقسام'),
        ('property_iraq', 'عقار داخل العراق'),
        ('property_outside', 'عقار خارج العراق'),
        ('hotel', 'فندق'),
        ('resort', 'منتجع'),
        ('service', 'خدمات'),

        ('auction', 'مزادات'),
        ('job', 'فرص العمل')
    ])
    featured_only = forms.BooleanField(required=False, label='المميزة فقط')
    verified_only = forms.BooleanField(required=False, label='الموثقة فقط')
    new_only = forms.BooleanField(required=False, label='الجديدة فقط')


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'


class PropertyNoteForm(forms.ModelForm):
    class Meta:
        model = PropertyNote
        fields = '__all__'


class VirtualTour360Form(forms.ModelForm):
    class Meta:
        model = VirtualTour360
        fields = '__all__'


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        exclude = ['governorate', 'city', 'district', 'subdistrict', 'area', 'neighborhood', 'mahalla', 'block', 'street', 'alley', 'house_number', 'property_number', 'landmark', 'latitude', 'longitude']


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = '__all__'


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = '__all__'


class FinancialTransactionForm(forms.ModelForm):
    class Meta:
        model = FinancialTransaction
        fields = '__all__'


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'


class ProfitForm(forms.ModelForm):
    class Meta:
        model = Profit
        fields = '__all__'


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserBasicInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UserSecurityForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label='كلمة المرور الحالية')
    new_password = forms.CharField(widget=forms.PasswordInput, label='كلمة المرور الجديدة')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='تأكيد كلمة المرور')


class UserNotificationForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = '__all__'


class UserPrivacyForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = '__all__'


class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = '__all__'


class BlockUserForm(forms.ModelForm):
    class Meta:
        model = BlockedUser
        fields = '__all__'


class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = '__all__'


class AutoBidForm(forms.ModelForm):
    class Meta:
        model = AutoBid
        fields = '__all__'


class AuctionRatingForm(forms.ModelForm):
    class Meta:
        model = AuctionRating
        fields = '__all__'


class AuctionLiveStreamForm(forms.ModelForm):
    class Meta:
        model = AuctionLiveStream
        fields = '__all__'


class AuctionAdvertisementForm(forms.ModelForm):
    class Meta:
        model = AuctionAdvertisement
        fields = '__all__'


class HotelSearchForm(forms.Form):
    q = forms.CharField(required=False, label='بحث', widget=forms.TextInput(attrs=_fc('ابحث عن فندق...')))
    governorate = forms.ChoiceField(required=False, label='المحافظة', choices=[('', 'كل المحافظات')] + list(IRAQ_GOVERNORATES))
    city = forms.CharField(required=False, label='المدينة', widget=forms.TextInput(attrs=_fc('المدينة')))
    stars = forms.IntegerField(required=False, label='عدد النجوم', validators=[MinValueValidator(0)])
    price_min = forms.IntegerField(required=False, label='السعر من', validators=[MinValueValidator(0)])
    price_max = forms.IntegerField(required=False, label='السعر إلى', validators=[MinValueValidator(0)])


class ResortSearchForm(forms.Form):
    q = forms.CharField(required=False, label='بحث', widget=forms.TextInput(attrs=_fc('ابحث عن منتجع...')))
    governorate = forms.ChoiceField(required=False, label='المحافظة', choices=[('', 'كل المحافظات')] + list(IRAQ_GOVERNORATES))
    city = forms.CharField(required=False, label='المدينة', widget=forms.TextInput(attrs=_fc('المدينة')))
    price_min = forms.IntegerField(required=False, label='السعر من', validators=[MinValueValidator(0)])
    price_max = forms.IntegerField(required=False, label='السعر إلى', validators=[MinValueValidator(0)])


class PropertyPublicationForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['publication_type', 'publication_days', 'is_featured', 'is_promoted', 'promotion_until', 'is_pinned', 'pinned_until']


class PropertyPaymentForm(forms.ModelForm):
    class Meta:
        model = PropertyPayment
        fields = '__all__'


class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'licenses': forms.Textarea(attrs={'rows': 3}),
            'address': forms.TextInput(attrs={'placeholder': 'العنوان التفصيلي'}),
            'working_hours': forms.TextInput(attrs={'placeholder': 'مثال: 9:00 - 17:00'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'}),
            'latitude': forms.NumberInput(attrs={'step': '0.0000001', 'placeholder': 'مثال: 33.3152'}),
            'longitude': forms.NumberInput(attrs={'step': '0.0000001', 'placeholder': 'مثال: 44.3661'}),
        }


class ServiceAdvertisementForm(forms.ModelForm):
    class Meta:
        model = ServiceAdvertisement
        exclude = ['city', 'district', 'subdistrict', 'area', 'neighborhood', 'mahalla', 'block', 'street', 'alley', 'house_number', 'property_number', 'landmark', 'latitude', 'longitude']


class OfficePresenceForm(forms.ModelForm):
    class Meta:
        model = OfficePresence
        fields = '__all__'


class QuickStatusForm(forms.ModelForm):
    class Meta:
        model = OfficePresence
        fields = '__all__'


class PresenceNotificationForm(forms.ModelForm):
    class Meta:
        model = PresenceNotification
        fields = '__all__'


class BrokerNotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = BrokerNotificationSettings
        fields = '__all__'


class HotelPageForm(forms.ModelForm):
    class Meta:
        model = HotelPage
        fields = '__all__'


class HotelPostForm(forms.ModelForm):
    class Meta:
        model = HotelPost
        fields = '__all__'


class HotelRoomForm(forms.ModelForm):
    class Meta:
        model = HotelRoom
        fields = '__all__'


class HotelOfferForm(forms.ModelForm):
    class Meta:
        model = HotelOffer
        fields = '__all__'


class HotelBookingForm(forms.ModelForm):
    class Meta:
        model = HotelBooking
        fields = '__all__'


class ServiceProviderPageForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderPage
        fields = '__all__'


class ServiceProviderWorkForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderWork
        fields = '__all__'


class ServiceProviderServiceForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderService
        fields = '__all__'


class ServiceProviderGalleryForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderGallery
        fields = '__all__'


class ServiceProviderVideoForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderVideo
        fields = '__all__'


class ServiceProvider360Form(forms.ModelForm):
    class Meta:
        model = ServiceProvider360
        fields = '__all__'


class ServiceProviderRatingForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderRating
        fields = '__all__'


class ServiceProviderContactForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderContact
        fields = '__all__'


class ServiceProviderQuoteForm(forms.ModelForm):
    class Meta:
        model = ServiceProviderQuote
        fields = '__all__'


class DynamicPropertyForm(forms.Form):
    """نموذج ديناميكي لاختيار نوع العقار"""
    category = forms.ChoiceField(
        choices=[
            ('property_iraq', 'عقار داخل العراق'),
            ('property_outside', 'عقار خارج العراق'),
            ('hotel', 'فندق'),
            ('resort', 'منتجع'),
        ],
        label='نوع العقار',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PropertyInsideIraqForm(forms.ModelForm):
    """نموذج إضافة عقار داخل العراق"""
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


class PropertyOutsideIraqForm(forms.ModelForm):
    """نموذج إضافة عقار خارج العراق"""
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


class PropertyHotelForm(forms.ModelForm):
    """نموذج إضافة فندق"""
    class Meta:
        model = PropertyHotel
        fields = '__all__'
        widgets = {
            'hotel_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الفندق'}),
            'star_rating': forms.Select(attrs={'class': 'form-control'}),
            'classification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'التصنيف'}),
            'total_rooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'suites': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'family_rooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة'}),
            'booking_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط الحجز'}),
        }


class PropertyResortForm(forms.ModelForm):
    """نموذج إضافة منتجع"""
    class Meta:
        model = PropertyResort
        fields = '__all__'
        widgets = {
            'resort_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المنتجع'}),
            'resort_type': forms.Select(attrs={'class': 'form-control'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المحافظة'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'القضاء'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'العنوان التفصيلي'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_rooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_week': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_per_month': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة'}),
            'min_booking_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_booking_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control'}),
        }


class JobForm(forms.ModelForm):
    """نموذج إضافة فرصة عمل"""
    class Meta:
        model = Job
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المسمى الوظيفي'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الشركة'}),
            'company_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'وصف الشركة'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-control'}),
            'governorate': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'other_country_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الدولة الأخرى'}),
            'outside_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة (خارج العراق)'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العنوان'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salary_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة'}),
            'salary_period': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'وصف الوظيفة'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'المتطلبات'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'المسؤوليات'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'المزايا'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'المهارات المطلوبة (مفصولة بفواصل)'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم جهة الاتصال'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'work_environment': forms.Select(attrs={'class': 'form-control'}),
            'work_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ساعات العمل'}),
            'gender_requirement': forms.Select(attrs={'class': 'form-control'}),
            'education_requirement': forms.Select(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'number_of_positions': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'external_application_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط التقديم الخارجي'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set field classes
        for field_name, field in self.fields.items():
            if 'widget' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


# ==================== Targeted Advertising Forms ====================

class BuildingAdvertisementForm(forms.ModelForm):
    """نموذج إنشاء إعلان بناء"""
    
    class Meta:
        model = BuildingAdvertisement
        fields = [
            'title', 'description', 'project_type', 'property_type',
            'governorate', 'city', 'district', 'area',
            'min_budget', 'max_budget', 'estimated_area', 'timeline_months',
            'ad_type', 'target_contractors', 'target_property_owners',
            'target_building_companies', 'phone', 'email',
            'preferred_contact_method', 'is_public', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان الإعلان'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'وصف المشروع بالتفصيل'
            }),
            'project_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: بناء منزل سكني'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'governorate': forms.Select(attrs={
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'القضاء'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المنطقة'
            }),
            'min_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحد الأدنى',
                'min': 0
            }),
            'max_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحد الأقصى',
                'min': 0
            }),
            'estimated_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'المساحة بالمتر المربع',
                'min': 0
            }),
            'timeline_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدة بالأشهر',
                'min': 1
            }),
            'ad_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني'
            }),
            'preferred_contact_method': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['governorate'].choices = [('', 'اختر المحافظة')] + list(IRAQ_GOVERNORATES)
        
        # Add styling for checkboxes
        for field in ['target_contractors', 'target_property_owners', 
                     'target_building_companies', 'is_public', 'is_featured']:
            self.fields[field].widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        min_budget = cleaned_data.get('min_budget')
        max_budget = cleaned_data.get('max_budget')
        
        if min_budget and max_budget and min_budget > max_budget:
            raise forms.ValidationError(
                'الحد الأدنى للميزانية يجب أن يكون أقل من الحد الأقصى'
            )
        
        return cleaned_data


class BuildingAdvertisementUpdateForm(forms.ModelForm):
    """نموذج تحديث إعلان بناء"""
    
    class Meta:
        model = BuildingAdvertisement
        fields = [
            'title', 'description', 'project_type', 'property_type',
            'governorate', 'city', 'district', 'area',
            'min_budget', 'max_budget', 'estimated_area', 'timeline_months',
            'status', 'ad_type', 'target_contractors', 'target_property_owners',
            'target_building_companies', 'phone', 'email',
            'preferred_contact_method', 'is_public', 'is_featured', 'expires_at'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان الإعلان'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'وصف المشروع بالتفصيل'
            }),
            'project_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: بناء منزل سكني'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'governorate': forms.Select(attrs={
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'القضاء'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المنطقة'
            }),
            'min_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحد الأدنى',
                'min': 0
            }),
            'max_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحد الأقصى',
                'min': 0
            }),
            'estimated_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'المساحة بالمتر المربع',
                'min': 0
            }),
            'timeline_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدة بالأشهر',
                'min': 1
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ad_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني'
            }),
            'preferred_contact_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['governorate'].choices = [('', 'اختر المحافظة')] + list(IRAQ_GOVERNORATES)
        
        # Add styling for checkboxes
        for field in ['target_contractors', 'target_property_owners', 
                     'target_building_companies', 'is_public', 'is_featured']:
            self.fields[field].widget.attrs['class'] = 'form-check-input'


class AdResponseForm(forms.ModelForm):
    """نموذج الرد على إعلان بناء"""
    
    class Meta:
        model = AdResponse
        fields = [
            'response_type', 'message', 'proposed_price', 'proposed_timeline',
            'preferred_meeting_date', 'meeting_location'
        ]
        widgets = {
            'response_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'رسالة الرد'
            }),
            'proposed_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'السعر المقترح',
                'min': 0
            }),
            'proposed_timeline': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدة المقترحة بالأشهر',
                'min': 1
            }),
            'preferred_meeting_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'meeting_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موقع الاجتماع'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        response_type = cleaned_data.get('response_type')
        
        if response_type == 'quote':
            if not cleaned_data.get('proposed_price'):
                raise forms.ValidationError(
                    'يجب تحديد السعر المقترح لعرض السعر'
                )
        
        if response_type == 'meeting':
            if not cleaned_data.get('preferred_meeting_date'):
                raise forms.ValidationError(
                    'يجب تحديد تاريخ الاجتماع المفضل لطلب الاجتماع'
                )
        
        return cleaned_data


class AdSearchForm(forms.Form):
    """نموذج البحث في الإعلانات"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث في الإعلانات...'
        })
    )
    
    governorate = forms.ChoiceField(
        required=False,
        choices=[('', 'كل المحافظات')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    property_type = forms.ChoiceField(
        required=False,
        choices=[('', 'كل الأنواع')] + [
            ('house', 'بيت'),
            ('apartment', 'شقة'),
            ('villa', 'فيلا'),
            ('building', 'بناية'),
            ('commercial', 'تجاري'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    ad_type = forms.ChoiceField(
        required=False,
        choices=[('', 'كل الأنواع')] + [
            ('general', 'عام'),
            ('specific', 'محدد'),
            ('urgent', 'عاجل'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_budget = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'الحد الأدنى'
        })
    )
    
    max_budget = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'الحد الأقصى'
        })
    )
    
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('newest', 'الأحدث'),
            ('budget_asc', 'الميزانية من الأقل للأعلى'),
            ('budget_desc', 'الميزانية من الأعلى للأقل'),
            ('popular', 'الأكثر مشاهدة'),
        ],
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['governorate'].choices = [('', 'كل المحافظات')] + list(IRAQ_GOVERNORATES)


class AdNotificationSettingsForm(forms.ModelForm):
    """نموذج إعدادات إشعارات الإعلانات"""
    
    class Meta:
        model = AdNotificationSettings
        fields = [
            'email_new_matches', 'email_new_responses',
            'push_notifications', 'sms_notifications',
            'notification_frequency', 'quiet_hours_start', 'quiet_hours_end'
        ]
        widgets = {
            'email_new_matches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_new_responses': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_frequency': forms.Select(attrs={'class': 'form-control'}),
            'quiet_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }
        labels = {
            'email_new_matches': 'إشعارات البريد الإلكتروني للمطابقات الجديدة',
            'email_new_responses': 'إشعارات البريد الإلكتروني للردود الجديدة',
            'push_notifications': 'إشعارات Push',
            'sms_notifications': 'إشعارات SMS',
            'notification_frequency': 'تكرار الإشعارات',
            'quiet_hours_start': 'بداية ساعات الصمت',
            'quiet_hours_end': 'نهاية ساعات الصمت',
        }


class AdminNotificationForm(forms.Form):
    """نموذج إرسال الإشعارات من لوحة الإدارة"""
    
    # Target Audience
    TARGET_CHOICES = [
        ('all_users', 'جميع المستخدمين'),
        ('all_brokers', 'جميع الدلالين'),
        ('both', 'المستخدمين والدلالين معاً'),
        ('specific_users', 'مستخدمين محددين'),
        ('specific_brokers', 'دلالين محددين'),
    ]
    
    target_audience = forms.ChoiceField(
        choices=TARGET_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='الجمهور المستهدف'
    )
    
    specific_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        label='المستخدمين المحددون',
        required=False
    )
    
    specific_brokers = forms.ModelMultipleChoiceField(
        queryset=Broker.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        label='الدلالين المحددون',
        required=False
    )
    
    # Notification Content
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الإشعار'}),
        label='العنوان'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'محتوى الإشعار'}),
        label='المحتوى'
    )
    
    # Notification Settings
    notification_type = forms.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='نوع الإشعار',
        initial='info'
    )
    
    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='الأولوية',
        initial='normal'
    )
    
    icon = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '🔔'}),
        label='الأيقونة',
        required=False
    )
    
    color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        label='اللون',
        initial='#0d9488'
    )
    
    action_url = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        label='رابط الإجراء',
        required=False
    )
    
    action_text = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عرض التفاصيل'}),
        label='نص الإجراء',
        required=False
    )
    
    # Delivery Options
    send_immediately = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='إرسال فوري',
        required=False,
        initial=True
    )
    
    schedule_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        label='تاريخ الجدولة',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make specific fields conditional based on target audience
        if 'target_audience' in self.data:
            target = self.data['target_audience']
            if target != 'specific_users':
                self.fields['specific_users'].required = False
            if target != 'specific_brokers':
                self.fields['specific_brokers'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        target_audience = cleaned_data.get('target_audience')
        specific_users = cleaned_data.get('specific_users')
        specific_brokers = cleaned_data.get('specific_brokers')
        send_immediately = cleaned_data.get('send_immediately')
        schedule_date = cleaned_data.get('schedule_date')
        
        # Validate target audience selection
        if target_audience == 'specific_users' and not specific_users:
            raise forms.ValidationError('يجب اختيار مستخدمين محددين عند اختيار "مستخدمين محددين"')
        
        if target_audience == 'specific_brokers' and not specific_brokers:
            raise forms.ValidationError('يجب اختيار دلالين محددين عند اختيار "دلالين محددين"')
        
        # Validate scheduling
        if not send_immediately and not schedule_date:
            raise forms.ValidationError('يجب تحديد تاريخ الجدولة عند عدم اختيار الإرسال الفوري')
        
        if schedule_date and schedule_date < timezone.now():
            raise forms.ValidationError('تاريخ الجدولة يجب أن يكون في المستقبل')
        
        return cleaned_data


class BrokerMessageForm(forms.ModelForm):
    """نموذج إرسال رسالة للدلال"""
    
    class Meta:
        model = BrokerMessage
        fields = ['content', 'message_type', 'image', 'file', 'property_ref']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'اكتب رسالتك هنا...'
            }),
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'property_ref': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'content': 'محتوى الرسالة',
            'message_type': 'نوع الرسالة',
            'image': 'صورة',
            'file': 'ملف',
            'property_ref': 'عقار',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter properties to show only user's properties if user is provided
        if user:
            self.fields['property_ref'].queryset = Property.objects.filter(user=user)
            self.fields['property_ref'].required = False
        else:
            self.fields['property_ref'].queryset = Property.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type')
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        file = cleaned_data.get('file')
        property_ref = cleaned_data.get('property_ref')
        
        # Validate based on message type
        if message_type == 'text' and not content:
            raise forms.ValidationError('يجب إدخال محتوى الرسالة')
        
        if message_type == 'image' and not image:
            raise forms.ValidationError('يجب إرفاق صورة')
        
        if message_type == 'file' and not file:
            raise forms.ValidationError('يجب إرفاق ملف')
        
        if message_type == 'property' and not property_ref:
            raise forms.ValidationError('يجب اختيار عقار')
        
        return cleaned_data


class BrokerConversationForm(forms.ModelForm):
    """نموذج إنشاء محادثة مع دلال"""
    
    class Meta:
        model = BrokerConversation
        fields = []
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.broker = kwargs.pop('broker', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        conversation = super().save(commit=False)
        
        if self.user and self.broker:
            conversation.user = self.user
            conversation.broker = self.broker
            conversation.save()
        
        return conversation


class RealEstateContractForm(forms.ModelForm):
    """نموذج إنشاء وتعديل العقود العقارية"""
    
    class Meta:
        model = RealEstateContract
        fields = [
            'contract_type', 'property', 'broker', 'client',
            'second_party_name', 'second_party_phone', 'second_party_email',
            'amount', 'deposit', 'commission_rate', 'commission_amount',
            'start_date', 'end_date', 'signing_date',
            'payment_frequency', 'payment_terms',
            'terms_and_conditions', 'special_clauses', 'renewal_clause', 'termination_clause',
            'notes'
        ]
        exclude = ['contract_number']
        widgets = {
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'property': forms.Select(attrs={'class': 'form-control'}),
            'broker': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'second_party_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم الطرف الثاني'}),
            'second_party_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'second_party_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'البريد الإلكتروني'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'قيمة العقد'}),
            'deposit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'العربون'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'نسبة العمولة (%)'}),
            'commission_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'قيمة العمولة'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'signing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_frequency': forms.Select(attrs={'class': 'form-control'}),
            'payment_terms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'شروط الدفع'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'الشروط والأحكام'}),
            'special_clauses': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'البنود الخاصة'}),
            'renewal_clause': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'termination_clause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'بند الإنهاء'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات'}),
        }
        labels = {
            'contract_type': 'نوع العقد',
            'property': 'العقار',
            'broker': 'الدلال',
            'client': 'العميل',
            'second_party_name': 'اسم الطرف الثاني',
            'second_party_phone': 'هاتف الطرف الثاني',
            'second_party_email': 'بريد الطرف الثاني',
            'amount': 'قيمة العقد',
            'deposit': 'العربون',
            'commission_rate': 'نسبة العمولة (%)',
            'commission_amount': 'قيمة العمولة',
            'start_date': 'تاريخ البدء',
            'end_date': 'تاريخ الانتهاء',
            'signing_date': 'تاريخ التوقيع',
            'payment_frequency': 'تكرار الدفع',
            'payment_terms': 'شروط الدفع',
            'terms_and_conditions': 'الشروط والأحكام',
            'special_clauses': 'البنود الخاصة',
            'renewal_clause': 'بند التجديد',
            'termination_clause': 'بند الإنهاء',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add contract_number as read-only field
        if self.instance and self.instance.contract_number:
            self.fields['contract_number'] = forms.CharField(
                required=False,
                initial=self.instance.contract_number,
                widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
                label='رقم العقد'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('تاريخ الانتهاء يجب أن يكون بعد تاريخ البدء')
        
        return cleaned_data


class ContractPaymentForm(forms.ModelForm):
    """نموذج إدارة مدفوعات العقود"""
    
    class Meta:
        model = ContractPayment
        fields = ['payment_number', 'amount', 'payment_method', 'due_date', 'notes']
        widgets = {
            'payment_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الدفعة'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المبلغ'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات'}),
        }
        labels = {
            'payment_number': 'رقم الدفعة',
            'amount': 'المبلغ',
            'payment_method': 'طريقة الدفع',
            'due_date': 'تاريخ الاستحقاق',
            'notes': 'ملاحظات',
        }
    
    def __init__(self, *args, **kwargs):
        contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)
        
        if contract:
            # Auto-generate payment number if not provided
            if not self.instance.pk:
                payment_count = ContractPayment.objects.filter(contract=contract).count()
                self.fields['payment_number'].initial = f'PAY-{contract.contract_number}-{payment_count + 1:03d}'


class ContractDocumentForm(forms.ModelForm):
    """نموذج إدارة وثائق العقود"""
    
    class Meta:
        model = ContractDocument
        fields = ['document_type', 'title', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الوثيقة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'الوصف'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'document_type': 'نوع الوثيقة',
            'title': 'عنوان الوثيقة',
            'description': 'الوصف',
            'file': 'الملف',
        }


class ContractReminderForm(forms.ModelForm):
    """نموذج إدارة تذكيرات العقود"""
    
    class Meta:
        model = ContractReminder
        fields = ['reminder_type', 'title', 'description', 'reminder_date', 'reminder_days_before']
        widgets = {
            'reminder_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان التذكير'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'الوصف'}),
            'reminder_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reminder_days_before': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'أيام قبل التذكير'}),
        }
        labels = {
            'reminder_type': 'نوع التذكير',
            'title': 'عنوان التذكير',
            'description': 'الوصف',
            'reminder_date': 'تاريخ التذكير',
            'reminder_days_before': 'أيام قبل التذكير',
        }


class TravelPackageForm(forms.ModelForm):
    """نموذج إنشاء وتعديل رحلات السفر"""
    
    class Meta:
        model = TravelPackage
        fields = [
            'title', 'title_en', 'description', 'description_en',
            'travel_type', 'destination', 'destination_en',
            'duration_days', 'duration_nights',
            'price', 'price_currency', 'discount_price',
            'max_participants', 'current_participants',
            'departure_date', 'return_date', 'booking_deadline',
            'inclusions', 'exclusions', 'itinerary',
            'cover_image', 'gallery',
            'status', 'is_featured', 'is_active',
            'slug', 'meta_title', 'meta_description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الرحلة'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Travel Package Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف الرحلة'}),
            'description_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Package Description'}),
            'travel_type': forms.Select(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الوجهة'}),
            'destination_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Destination'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'عدد الأيام'}),
            'duration_nights': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'عدد الليالي'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'placeholder': 'السعر'}),
            'price_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'العملة'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'placeholder': 'سعر الخصم'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'الحد الأقصى للمشاركين'}),
            'current_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'عدد المشاركين الحالي'}),
            'departure_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'return_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'booking_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'inclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ما يشمله العرض (JSON format)', 'initial': ''}),
            'exclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ما لا يشمله العرض (JSON format)', 'initial': ''}),
            'itinerary': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'البرنامج الزمني (JSON format)', 'initial': ''}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'gallery': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'معرض الصور (JSON format)', 'initial': ''}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الرابط المختصر'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان SEO'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'وصف SEO'}),
        }
        labels = {
            'title': 'عنوان الرحلة',
            'title_en': 'عنوان الرحلة بالإنجليزية',
            'description': 'وصف الرحلة',
            'description_en': 'وصف الرحلة بالإنجليزية',
            'travel_type': 'نوع الرحلة',
            'destination': 'الوجهة',
            'destination_en': 'الوجهة بالإنجليزية',
            'duration_days': 'مدة الرحلة بالأيام',
            'duration_nights': 'عدد الليالي',
            'price': 'السعر',
            'price_currency': 'عملة السعر',
            'discount_price': 'سعر الخصم',
            'max_participants': 'الحد الأقصى للمشاركين',
            'current_participants': 'عدد المشاركين الحالي',
            'departure_date': 'تاريخ الانطلاق',
            'return_date': 'تاريخ العودة',
            'booking_deadline': 'موعد انتهاء الحجز',
            'inclusions': 'ما يشمله العرض',
            'exclusions': 'ما لا يشمله العرض',
            'itinerary': 'البرنامج الزمني',
            'cover_image': 'صورة الغلاف',
            'gallery': 'معرض الصور',
            'status': 'الحالة',
            'is_featured': 'مميز',
            'is_active': 'نشط',
            'slug': 'الرابط المختصر',
            'meta_title': 'عنوان SEO',
            'meta_description': 'وصف SEO',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for JSON fields to empty string
        json_fields = ['inclusions', 'exclusions', 'itinerary', 'gallery']
        for field in json_fields:
            if not self.instance.pk:  # Only for new instances
                self.fields[field].initial = ''