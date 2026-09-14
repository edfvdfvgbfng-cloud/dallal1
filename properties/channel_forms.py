"""
نماذج القنوات المتقدمة
Advanced Channel Forms
"""

from django import forms
from django.contrib.auth.models import User
from .models import BrokerChannel, ChannelSubscription, ChannelContent, ChannelBroadcast, ChannelCollaboration, ChannelAdvertisement
from .constants import IRAQ_GOVERNORATES


class ChannelSubscriptionForm(forms.ModelForm):
    """نموذج اشتراك القناة"""
    
    class Meta:
        model = ChannelSubscription
        fields = [
            'plan', 'billing_cycle', 'auto_renew'
        ]
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-control'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].choices = [
            ('free', 'مجاني - 0 د.ع'),
            ('basic', 'أساسي - 50,000 د.ع/شهر'),
            ('pro', 'احترافي - 150,000 د.ع/شهر'),
            ('enterprise', 'مؤسسي - 500,000 د.ع/شهر'),
        ]


class ChannelContentForm(forms.ModelForm):
    """نموذج محتوى القناة"""
    
    class Meta:
        model = ChannelContent
        fields = [
            'content_type', 'title', 'content', 'image', 'video',
            'property', 'building_advertisement', 'tags', 'category',
            'status', 'scheduled_at', 'allow_comments', 'allow_sharing',
            'is_pinned', 'is_featured', 'meta_title', 'meta_description'
        ]
        widgets = {
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'property': forms.Select(attrs={'class': 'form-control'}),
            'building_advertisement': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit property choices to channel's properties
        if 'channel' in self.initial:
            channel = self.initial['channel']
            self.fields['property'].queryset = channel.broker.properties.all()
            self.fields['building_advertisement'].queryset = channel.broker.user.building_ads.all()


class ChannelBroadcastForm(forms.ModelForm):
    """نموذج البث المباشر للقناة"""
    
    class Meta:
        model = ChannelBroadcast
        fields = [
            'title', 'description', 'thumbnail', 'stream_url', 'stream_key',
            'property', 'scheduled_at', 'duration_minutes', 'allow_chat',
            'allow_questions', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'stream_url': forms.URLInput(attrs={'class': 'form-control'}),
            'stream_key': forms.TextInput(attrs={'class': 'form-control'}),
            'property': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_chat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'channel' in self.initial:
            channel = self.initial['channel']
            self.fields['property'].queryset = channel.broker.properties.all()


class ChannelCollaborationForm(forms.ModelForm):
    """نموذج التعاون بين القنوات"""
    
    class Meta:
        model = ChannelCollaboration
        fields = [
            'collaboration_type', 'title', 'description', 'commission_rate',
            'duration_days'
        ]
        widgets = {
            'collaboration_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ChannelAdvertisementForm(forms.ModelForm):
    """نموذج إعلان القناة"""
    
    class Meta:
        model = ChannelAdvertisement
        fields = [
            'title', 'content', 'image', 'video', 'target_url', 'position',
            'start_date', 'end_date', 'budget', 'currency'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'target_url': forms.URLInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['currency'].choices = [
            ('IQD', 'دينار عراقي'),
            ('USD', 'دولار أمريكي'),
        ]


class ChannelSearchForm(forms.Form):
    """نموذج البحث في القنوات"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث في القنوات...'
        })
    )
    
    governorate = forms.ChoiceField(
        required=False,
        choices=[('', 'كل المحافظات')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    channel_type = forms.ChoiceField(
        required=False,
        choices=[('', 'كل الأنواع')] + [
            ('basic', 'أساسي'),
            ('premium', 'مميز'),
            ('elite', 'نخبوي'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'كل التصنيفات')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('followers', 'الأكثر متابعة'),
            ('rating', 'الأعلى تقييماً'),
            ('properties', 'الأكثر عقارات'),
            ('newest', 'الأحدث'),
        ],
        initial='followers',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_verified = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['governorate'].choices = [('', 'كل المحافظات')] + list(IRAQ_GOVERNORATES)
        self.fields['category'].choices = [('', 'كل التصنيفات')] + [
            ('properties_iraq', '🏠 عقارات داخل العراق'),
            ('properties_foreign', '🌍 عقارات خارج العراق'),
            ('hotels_iraq', '🏨🇮🇶 فنادق داخل العراق'),
            ('hotels_foreign', '🏨🌍 فنادق خارج العراق'),
            ('resorts_iraq', '🏝️🇮🇶 منتجعات داخل العراق'),
            ('resorts_foreign', '🏝️🌍 منتجعات خارج العراق'),
            ('travel_agency', '✈️ شركة سفر'),
            ('jobs', '➕ وظائف'),
            ('building_requests', '🏗️ طلبات بناء'),
            ('services', '🔧 خدمات'),
            ('auctions', '🔨 مزادات'),
        ]