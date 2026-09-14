import logging
import json
import random
import django
import sys
from datetime import datetime, timedelta, date
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .decorators import admin_required, broker_required, user_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from .utils import match_advertisement_with_targets
from .channel_views import ChannelListView, ChannelDetailView
from .models import Property, PropertyVerification, Hotel, Resort, ServiceProvider, ServiceAdvertisement, Auction, UserProfile, Conversation, RealEstateContract, Customer, Agent
# These models might not exist in all databases, import conditionally
try:
    from .models import Job
except ImportError:
    Job = None
try:
    from .models import Backup
except ImportError:
    Backup = None
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_GET

# REST Framework imports for API views
try:
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import AllowAny, IsAuthenticated
except ImportError:
    api_view = permission_classes = AllowAny = IsAuthenticated = None
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

# Advertising system imports
from .models import BuildingAdvertisement, AdResponse, AdMatch, AdNotificationSettings, Property, Broker, BrokerConversation, BrokerMessage
from .forms import BuildingAdvertisementForm, BuildingAdvertisementUpdateForm, AdResponseForm, AdSearchForm, AdNotificationSettingsForm, BrokerMessageForm, BrokerConversationForm, RealEstateContractForm, ContractPaymentForm, ContractDocumentForm, ContractReminderForm, CustomerForm, AgentForm


# ==================== Targeted Advertising Views ====================

from django.views import View

class AdvertisementListView(View):
    """قائمة إعلانات البناء"""
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        search_form = AdSearchForm(request.GET)
        advertisements = BuildingAdvertisement.objects.filter(is_public=True)
        
        # Apply filters
        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            governorate = search_form.cleaned_data.get('governorate')
            property_type = search_form.cleaned_data.get('property_type')
            ad_type = search_form.cleaned_data.get('ad_type')
            min_budget = search_form.cleaned_data.get('min_budget')
            max_budget = search_form.cleaned_data.get('max_budget')
            is_featured = search_form.cleaned_data.get('is_featured')
            sort = search_form.cleaned_data.get('sort', 'newest')
            
            if q:
                advertisements = advertisements.filter(
                    Q(title__icontains=q) | Q(description__icontains=q)
                )
            
            if governorate:
                advertisements = advertisements.filter(governorate=governorate)
            
            if property_type:
                advertisements = advertisements.filter(property_type=property_type)
            
            if ad_type:
                advertisements = advertisements.filter(ad_type=ad_type)
            
            if min_budget:
                advertisements = advertisements.filter(min_budget__gte=min_budget)
            
            if max_budget:
                advertisements = advertisements.filter(max_budget__lte=max_budget)
            
            if is_featured:
                advertisements = advertisements.filter(is_featured=True)
            
            # Apply sorting
            if sort == 'newest':
                advertisements = advertisements.order_by('-created_at')
            elif sort == 'budget_asc':
                advertisements = advertisements.order_by('min_budget')
            elif sort == 'budget_desc':
                advertisements = advertisements.order_by('-min_budget')
            elif sort == 'popular':
                advertisements = advertisements.order_by('-views_count')
        
        # Only show active ads
        advertisements = advertisements.filter(status='active')
        
        # Check expiration
        advertisements = advertisements.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(advertisements, 12)
        page_obj = paginator.get_page(page)
        
        context = {
            'advertisements': page_obj,
            'search_form': search_form,
            'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        }
        
        if context['is_ajax']:
            return JsonResponse({
                'ads': [
                    {
                        'id': ad.id,
                        'title': ad.title,
                        'description': ad.description[:200],
                        'project_type': ad.project_type,
                        'property_type': ad.get_property_type_display(),
                        'governorate': ad.get_governorate_display(),
                        'min_budget': ad.min_budget,
                        'max_budget': ad.max_budget,
                        'estimated_area': ad.estimated_area,
                        'timeline_months': ad.timeline_months,
                        'is_featured': ad.is_featured,
                        'views_count': ad.views_count,
                        'responses_count': ad.responses_count,
                        'created_at': ad.created_at.strftime('%Y-%m-%d'),
                        'url': ad.get_absolute_url()
                    }
                    for ad in page_obj
                ],
                'pagination': {
                    'page': page,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            })
        
        return render(request, 'properties/advertisement_list.html', context)


class AdvertisementDetailView(View):
    """تفاصيل إعلان البناء"""
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, ad_id):
        advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id)
        
        # Increment view counter
        if not request.user.is_authenticated or request.user != advertisement.user:
            advertisement.increment_views()
        
        # Get related ads
        related_ads = BuildingAdvertisement.objects.filter(
            is_public=True,
            status='active',
            governorate=advertisement.governorate,
            property_type=advertisement.property_type
        ).exclude(id=advertisement.id)[:4]
        
        # Get responses if user is the ad owner
        user_responses = []
        if request.user.is_authenticated and request.user == advertisement.user:
            user_responses = advertisement.responses.all()
        
        context = {
            'advertisement': advertisement,
            'related_ads': related_ads,
            'user_responses': user_responses,
            'is_owner': request.user.is_authenticated and request.user == advertisement.user,
            'can_respond': request.user.is_authenticated and request.user != advertisement.user
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'id': advertisement.id,
                'title': advertisement.title,
                'description': advertisement.description,
                'project_type': advertisement.project_type,
                'property_type': advertisement.get_property_type_display(),
                'governorate': advertisement.get_governorate_display(),
                'city': advertisement.city,
                'district': advertisement.district,
                'area': advertisement.area,
                'min_budget': advertisement.min_budget,
                'max_budget': advertisement.max_budget,
                'estimated_area': advertisement.estimated_area,
                'timeline_months': advertisement.timeline_months,
                'ad_type': advertisement.get_ad_type_display(),
                'status': advertisement.get_status_display(),
                'phone': advertisement.phone,
                'email': advertisement.email,
                'preferred_contact_method': advertisement.get_preferred_contact_method_display(),
                'is_featured': advertisement.is_featured,
                'views_count': advertisement.views_count,
                'responses_count': advertisement.responses_count,
                'matched_count': advertisement.matched_count,
                'created_at': advertisement.created_at.strftime('%Y-%m-%d'),
                'user': advertisement.user.username,
                'is_owner': context['is_owner'],
                'can_respond': context['can_respond']
            })
        
        return render(request, 'properties/advertisement_detail.html', context)


@login_required
def create_advertisement(request):
    """إنشاء إعلان بناء جديد"""
    if request.method == 'POST':
        form = BuildingAdvertisementForm(request.POST)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.user = request.user
            advertisement.status = 'pending'
            advertisement.save()
            
            # Run smart matching
            try:
                match_advertisement_with_targets(advertisement)
            except Exception as e:
                # Log error but don't fail the creation
                pass
            
            messages.success(request, 'تم إنشاء الإعلان بنجاح! سيتم مراجعته وعرضه قريباً.')
            return redirect('advertisement_detail', ad_id=advertisement.id)
    else:
        form = BuildingAdvertisementForm()
    
    return render(request, 'properties/advertisement_create.html', {'form': form})


@login_required
def update_advertisement(request, ad_id):
    """تحديث إعلان بناء"""
    advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id, user=request.user)
    
    if request.method == 'POST':
        form = BuildingAdvertisementUpdateForm(request.POST, instance=advertisement)
        if form.is_valid():
            form.save()
            
            # Re-run matching if status changed to active
            if advertisement.status == 'active':
                try:
                    match_advertisement_with_targets(advertisement)
                except Exception as e:
                    # Log error but don't fail the update
                    pass
            
            messages.success(request, 'تم تحديث الإعلان بنجاح!')
            return redirect('advertisement_detail', ad_id=advertisement.id)
    else:
        form = BuildingAdvertisementUpdateForm(instance=advertisement)
    
    return render(request, 'properties/advertisement_update.html', {
        'form': form,
        'advertisement': advertisement
    })


@login_required
def delete_advertisement(request, ad_id):
    """حذف إعلان بناء"""
    advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id, user=request.user)
    
    if request.method == 'POST':
        advertisement.delete()
        messages.success(request, 'تم حذف الإعلان بنجاح!')
        return redirect('user_advertisements')
    
    return render(request, 'properties/advertisement_delete.html', {
        'advertisement': advertisement
    })


@login_required
def user_advertisements(request):
    """إعلانات المستخدم"""
    advertisements = BuildingAdvertisement.objects.filter(user=request.user)
    
    # Get statistics
    stats = {
        'total': advertisements.count(),
        'active': advertisements.filter(status='active').count(),
        'pending': advertisements.filter(status='pending').count(),
        'completed': advertisements.filter(status='completed').count(),
        'total_views': advertisements.aggregate(total_views=AggregateSum('views_count'))['total_views'] or 0,
        'total_responses': advertisements.aggregate(total_responses=AggregateSum('responses_count'))['total_responses'] or 0,
    }
    
    return render(request, 'properties/user_advertisements.html', {
        'advertisements': advertisements,
        'stats': stats
    })


@login_required
def respond_to_advertisement(request, ad_id):
    """الرد على إعلان بناء"""
    advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id)
    
    if request.user == advertisement.user:
        messages.error(request, 'لا يمكنك الرد على إعلانك الخاص!')
        return redirect('advertisement_detail', ad_id=ad_id)
    
    if request.method == 'POST':
        form = AdResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.advertisement = advertisement
            response.responder = request.user
            response.save()
            
            # Increment response counter
            advertisement.increment_responses()
            
            messages.success(request, 'تم إرسال ردك بنجاح!')
            return redirect('advertisement_detail', ad_id=ad_id)
    else:
        form = AdResponseForm()
    
    return render(request, 'properties/advertisement_response.html', {
        'form': form,
        'advertisement': advertisement
    })


@login_required
def advertisement_responses(request, ad_id):
    """عرض الردود على إعلان"""
    advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id, user=request.user)
    responses = advertisement.responses.all()
    
    return render(request, 'properties/advertisement_responses.html', {
        'advertisement': advertisement,
        'responses': responses
    })


@login_required
def handle_response(request, response_id):
    """معالجة الرد على إعلان (قبول/رفض)"""
    response = get_object_or_404(AdResponse, id=response_id)
    advertisement = response.advertisement
    
    if request.user != advertisement.user:
        messages.error(request, 'ليس لديك صلاحية معالجة هذا الرد!')
        return redirect('advertisement_detail', ad_id=advertisement.id)
    
    action = request.POST.get('action')
    
    if action == 'accept':
        response.status = 'accepted'
        response.save()
        messages.success(request, 'تم قبول الرد بنجاح!')
        
    elif action == 'reject':
        response.status = 'rejected'
        response.save()
        messages.success(request, 'تم رفض الرد بنجاح!')
    
    return redirect('advertisement_responses', ad_id=advertisement.id)


@login_required
def advertisement_matches(request, ad_id):
    """عرض المطابقات للإعلان"""
    advertisement = get_object_or_404(BuildingAdvertisement, id=ad_id, user=request.user)
    matches = advertisement.matches.all()
    
    return render(request, 'properties/advertisement_matches.html', {
        'advertisement': advertisement,
        'matches': matches
    })


@login_required
def notification_settings(request):
    """إعدادات إشعارات الإعلانات"""
    settings_obj, created = AdNotificationSettings.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = AdNotificationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث إعدادات الإشعارات بنجاح!')
            return redirect('notification_settings')
    else:
        form = AdNotificationSettingsForm(instance=settings_obj)
    
    return render(request, 'properties/ad_notification_settings.html', {
        'form': form
    })


from .decorators import broker_required
from .forms import MessageForm, PropertyForm, PropertySearchForm, SiteSettingsForm, PropertyNoteForm, VirtualTour360Form, AuctionForm, BidForm, ReportForm, FinancialTransactionForm, ExpenseForm, ProfitForm, SubscriptionPlanForm, UserProfileForm, UserBasicInfoForm, UserSecurityForm, UserNotificationForm, UserPrivacyForm, UserPreferencesForm, BlockUserForm, SavedSearchForm, AutoBidForm, AuctionRatingForm, AuctionLiveStreamForm, AuctionAdvertisementForm, HotelSearchForm, ResortSearchForm, PropertyPublicationForm, PropertyPaymentForm, ServiceProviderForm, ServiceAdvertisementForm, DynamicPropertyForm, PropertyInsideIraqForm, PropertyOutsideIraqForm, PropertyHotelForm, PropertyResortForm, JobForm, SupportMessageForm
from .enhanced_forms import EnhancedPropertyForm, EnhancedOutsidePropertyForm
from .enhanced_forms import EnhancedPropertyForm
from .models import Message, Property, PropertyImage, SiteSettings, PropertyNote, Notification, VirtualTour360, Auction, Bid, FinancialTransaction, Expense, Payment, OfficeWallet, WalletTransaction, Broker, Report, ReportAction, PropertyLike, PropertySave, PropertyComment, VirtualTourPoint, VirtualTourConnection, Profit, SubscriptionPlan, ActivityLog, UserSettings, BlockedUser, SavedSearch, AutoBid, AuctionNotification, AuctionRating, AuctionStats, AuctionLiveStream, AuctionAdvertisement, Hotel, Resort, BrokerChannel, ChannelFollow, ChannelSave, PaymentMethod, PropertyPayment, PropertyNotification, ChannelPost, ChannelVideo, AdvancedSubscriptionPlan, BrokerPlanSubscription, SubscriptionRenewalRequest, ServiceProvider, ServiceAdvertisement, AuctionInvitation, JobCategory, Job, JobApplication, SupportMessage, Country
from .permissions import (
    can_access_dashboard,
    can_add_property,
    can_delete_property,
    can_edit_property,
    can_manage_brokers,
    can_manage_site_settings,
    can_replace_property,
    get_accessible_messages,
    get_accessible_properties,
    get_broker,
    get_broker_stats,
    get_managed_brokers,
    is_platform_admin,
    can_post_job,
    can_edit_job,
    can_delete_job,
    can_apply_for_job
)
from .utils import filter_properties, get_public_properties, save_gallery_images, save_gallery_videos, sort_properties, PUBLIC_STATUSES

# Import hotel and travel views
try:
    from . import hotel_travel_views
    HOTEL_TRAVEL_AVAILABLE = True
except ImportError:
    HOTEL_TRAVEL_AVAILABLE = False

logger = logging.getLogger('properties')

# ==================== User Experience Views ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def discover_view(request):
    """صفحة الاكتشاف العالمية - تجربة مثل Instagram"""
    category = request.GET.get('category', 'all')
    
    # Get all feed items based on category
    feed_items = []
    
    if category in ['all', 'properties']:
        # Get properties
        properties = Property.objects.filter(status='published').order_by('-created_at')[:20]
        for prop in properties:
            feed_items.append({
                'id': prop.id,
                'type': 'property',
                'title': prop.title,
                'description': prop.description[:200] if prop.description else '',
                'price': str(prop.price) if prop.price else 'غير محدد',
                'location': prop.district or prop.city or 'غير محدد',
                'image': prop.main_image.url if prop.main_image else '/static/img/placeholder-property.svg',
                'url': prop.get_absolute_url(),
                'is_featured': prop.is_featured,
                'views_count': prop.views_count if hasattr(prop, 'views_count') else 0,
                'country': prop.country.name if prop.country else 'غير محدد',
                'property_type': prop.get_property_type_display() if prop.property_type else 'غير محدد',
                'created_at': prop.created_at.isoformat() if prop.created_at else None
            })
    
    if category in ['all', 'hotels']:
        # Get hotels
        hotels = Hotel.objects.filter(status='active').order_by('-created_at')[:20]
        for hotel in hotels:
            feed_items.append({
                'id': hotel.id,
                'type': 'hotel',
                'title': hotel.name,
                'description': hotel.description[:200] if hotel.description else '',
                'price': str(hotel.price_per_night) if hotel.price_per_night else 'غير محدد',
                'location': hotel.city or 'غير محدد',
                'image': hotel.main_image.url if hotel.main_image else '/static/img/placeholder-hotel.svg',
                'url': hotel.get_absolute_url(),
                'is_featured': hotel.is_featured if hasattr(hotel, 'is_featured') else False,
                'views_count': hotel.views_count if hasattr(hotel, 'views_count') else 0,
                'country': hotel.country.name if hotel.country else 'غير محدد',
                'hotel_type': hotel.get_hotel_type_display() if hotel.hotel_type else 'غير محدد',
                'created_at': hotel.created_at.isoformat() if hotel.created_at else None
            })
    
    if category in ['all', 'resorts']:
        # Get resorts
        resorts = Resort.objects.filter(status='active').order_by('-created_at')[:20]
        for resort in resorts:
            feed_items.append({
                'id': resort.id,
                'type': 'resort',
                'title': resort.name,
                'description': resort.description[:200] if resort.description else '',
                'price': str(resort.price_per_night) if resort.price_per_night else 'غير محدد',
                'location': resort.city or 'غير محدد',
                'image': resort.main_image.url if resort.main_image else '/static/img/placeholder-resort.svg',
                'url': resort.get_absolute_url(),
                'is_featured': resort.is_featured if hasattr(resort, 'is_featured') else False,
                'views_count': resort.views_count if hasattr(resort, 'views_count') else 0,
                'country': resort.country.name if resort.country else 'غير محدد',
                'resort_type': resort.get_resort_type_display() if resort.resort_type else 'غير محدد',
                'created_at': resort.created_at.isoformat() if resort.created_at else None
            })
    
    if category in ['all', 'jobs']:
        # Get jobs
        jobs = Job.objects.filter(status='active').order_by('-created_at')[:20]
        for job in jobs:
            feed_items.append({
                'id': job.id,
                'type': 'job',
                'title': job.title,
                'description': job.description[:200] if job.description else '',
                'price': str(job.salary) if job.salary else 'غير محدد',
                'location': job.location or 'غير محدد',
                'image': job.company_logo.url if job.company_logo else '/static/img/placeholder-job.svg',
                'url': job.get_absolute_url(),
                'is_featured': job.is_featured if hasattr(job, 'is_featured') else False,
                'views_count': job.views_count if hasattr(job, 'views_count') else 0,
                'country': job.country.name if job.country else 'غير محدد',
                'job_type': job.get_job_type_display() if job.job_type else 'غير محدد',
                'created_at': job.created_at.isoformat() if job.created_at else None
            })
    
    # Sort by featured first, then by date
    feed_items.sort(key=lambda x: (not x['is_featured'], x['created_at'] or ''), reverse=True)
    
    context = {
        'feed_data': json.dumps(feed_items),
        'category': category
    }
    
    return render(request, 'properties/discover.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def discover_api(request):
    """API endpoint for discover feed"""
    category = request.GET.get('category', 'all')
    filter_type = request.GET.get('filter', 'featured')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    feed_items = []
    
    # Get items based on category and filter
    if category in ['all', 'properties']:
        queryset = Property.objects.filter(status='published')
        if filter_type == 'featured':
            queryset = queryset.filter(is_featured=True)
        elif filter_type == 'new':
            queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
        
        properties = queryset.order_by('-created_at')[(page-1)*per_page:page*per_page]
        for prop in properties:
            feed_items.append({
                'id': prop.id,
                'type': 'property',
                'title': prop.title,
                'description': prop.description[:200] if prop.description else '',
                'price': str(prop.price) if prop.price else 'غير محدد',
                'location': prop.district or prop.city or 'غير محدد',
                'image': prop.main_image.url if prop.main_image else '/static/img/placeholder-property.svg',
                'url': prop.get_absolute_url(),
                'is_featured': prop.is_featured,
                'views_count': prop.views_count if hasattr(prop, 'views_count') else 0,
                'country': prop.country.name if prop.country else 'غير محدد',
                'property_type': prop.get_property_type_display() if prop.property_type else 'غير محدد',
                'created_at': prop.created_at.isoformat() if prop.created_at else None
            })
    
    # Similar logic for hotels, resorts, jobs...
    
    return Response({
        'items': feed_items,
        'page': page,
        'has_more': len(feed_items) == per_page
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_properties_api(request):
    """API endpoint for trending properties"""
    try:
        # Get properties with most views in the last 7 days
        trending = Property.objects.filter(
            status='published',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-views_count')[:10]
        
        items = []
        for prop in trending:
            items.append({
                'id': prop.id,
                'type': 'property',
                'title': prop.title,
                'price': str(prop.price) if prop.price else 'غير محدد',
                'location': prop.district or prop.city or 'غير محدد',
                'image': prop.main_image.url if prop.main_image else '/static/img/placeholder-property.svg',
                'url': prop.get_absolute_url(),
                'views_count': prop.views_count if hasattr(prop, 'views_count') else 0,
                'country': prop.country.name if prop.country else 'غير محدد'
            })
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in trending_properties_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def international_hotels_api(request):
    """API endpoint for international hotels"""
    try:
        from .models import Country
        iraq_country = Country.objects.filter(code='IQ').first()
        
        hotels = Hotel.objects.filter(status='active')
        if iraq_country:
            hotels = hotels.exclude(country=iraq_country)
        
        hotels = hotels.order_by('-created_at')[:10]
        
        items = []
        for hotel in hotels:
            items.append({
                'id': hotel.id,
                'type': 'hotel',
                'title': hotel.name,
                'price': str(hotel.price_per_night) if hotel.price_per_night else 'غير محدد',
                'location': hotel.city or 'غير محدد',
                'image': hotel.main_image.url if hotel.main_image else '/static/img/placeholder-hotel.svg',
                'url': hotel.get_absolute_url(),
                'country': hotel.country.name if hotel.country else 'غير محدد',
                'hotel_type': hotel.get_hotel_type_display() if hotel.hotel_type else 'غير محدد'
            })
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in international_hotels_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def luxury_resorts_api(request):
    """API endpoint for luxury resorts"""
    try:
        resorts = Resort.objects.filter(
            status='active',
            is_featured=True
        ).order_by('-created_at')[:10]
        
        items = []
        for resort in resorts:
            items.append({
                'id': resort.id,
                'type': 'resort',
                'title': resort.name,
                'price': str(resort.price_per_night) if resort.price_per_night else 'غير محدد',
                'location': resort.city or 'غير محدد',
                'image': resort.main_image.url if resort.main_image else '/static/img/placeholder-resort.svg',
                'url': resort.get_absolute_url(),
                'country': resort.country.name if resort.country else 'غير محدد',
                'resort_type': resort.get_resort_type_display() if resort.resort_type else 'غير محدد'
            })
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in luxury_resorts_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def international_jobs_api(request):
    """API endpoint for international jobs"""
    try:
        from .models import Country
        iraq_country = Country.objects.filter(code='IQ').first()
        
        jobs = Job.objects.filter(status='active')
        if iraq_country:
            jobs = jobs.exclude(country=iraq_country)
        
        jobs = jobs.order_by('-created_at')[:10]
        
        items = []
        for job in jobs:
            items.append({
                'id': job.id,
                'type': 'job',
                'title': job.title,
                'salary': str(job.salary) if job.salary else 'غير محدد',
                'location': job.location or 'غير محدد',
                'image': job.company_logo.url if job.company_logo else '/static/img/placeholder-job.svg',
                'url': job.get_absolute_url(),
                'country': job.country.name if job.country else 'غير محدد',
                'job_type': job.get_job_type_display() if job.job_type else 'غير محدد'
            })
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in international_jobs_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_user_behavior(request):
    """API endpoint to track user behavior"""
    try:
        action = request.data.get('action')
        item_id = request.data.get('item_id')
        item_type = request.data.get('item_type')
        metadata = request.data.get('metadata', {})
        
        # Create user behavior record
        from .models import UserBehavior
        behavior = UserBehavior.objects.create(
            user=request.user,
            action=action,
            item_id=item_id,
            item_type=item_type,
            metadata=metadata
        )
        
        return Response({'success': True, 'behavior_id': behavior.id})
    except Exception as e:
        logger.error(f"Error in track_user_behavior: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_recommendations_api(request):
    """API endpoint for personalized recommendations"""
    try:
        from .models import UserBehavior
        
        # Get user's recent behavior
        recent_behavior = UserBehavior.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        
        # Extract preferences
        preferred_types = set()
        preferred_locations = set()
        price_range = {'min': None, 'max': None}
        
        for behavior in recent_behavior:
            if behavior.item_type:
                preferred_types.add(behavior.item_type)
            if behavior.metadata and 'location' in behavior.metadata:
                preferred_locations.add(behavior.metadata['location'])
            if behavior.metadata and 'price' in behavior.metadata:
                price = behavior.metadata['price']
                if price_range['min'] is None or price < price_range['min']:
                    price_range['min'] = price
                if price_range['max'] is None or price > price_range['max']:
                    price_range['max'] = price
        
        # Get recommendations based on preferences
        recommendations = []
        
        if 'property' in preferred_types:
            properties = Property.objects.filter(status='published')
            if preferred_locations:
                properties = properties.filter(district__in=preferred_locations)
            if price_range['min']:
                properties = properties.filter(price__gte=price_range['min'])
            if price_range['max']:
                properties = properties.filter(price__lte=price_range['max'])
            
            properties = properties.order_by('-created_at')[:5]
            for prop in properties:
                recommendations.append({
                    'id': prop.id,
                    'type': 'property',
                    'title': prop.title,
                    'price': str(prop.price) if prop.price else 'غير محدد',
                    'location': prop.district or prop.city or 'غير محدد',
                    'image': prop.main_image.url if prop.main_image else '/static/img/placeholder-property.svg',
                    'url': prop.get_absolute_url(),
                    'reason': 'بناءً على اهتماماتك في العقارات'
                })
        
        return Response({'recommendations': recommendations})
    except Exception as e:
        logger.error(f"Error in user_recommendations_api: {e}")
        return Response({'recommendations': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_behavior_insights_api(request):
    """API endpoint for user behavior insights"""
    try:
        from .models import UserBehavior
        
        behavior = UserBehavior.objects.filter(user=request.user)
        
        insights = {
            'total_views': behavior.filter(action='view').count(),
            'total_saves': behavior.filter(action='save').count(),
            'total_shares': behavior.filter(action='share').count(),
            'top_types': list(behavior.values('item_type').annotate(count=Count('id')).order_by('-count')[:5]),
            'behavior_pattern': analyze_behavior_pattern(behavior)
        }
        
        return Response(insights)
    except Exception as e:
        logger.error(f"Error in user_behavior_insights_api: {e}")
        return Response({}, status=500)


def analyze_behavior_pattern(behavior_queryset):
    """Analyze user behavior pattern"""
    total = behavior_queryset.count()
    if total == 0:
        return 'explorer'
    
    save_count = behavior_queryset.filter(action='save').count()
    view_count = behavior_queryset.filter(action='view').count()
    
    save_ratio = save_count / total if total > 0 else 0
    view_ratio = view_count / total if total > 0 else 0
    
    if save_ratio > 0.3:
        return 'decisive'
    elif view_ratio > 0.7:
        return 'explorer'
    else:
        return 'focused'

staff_required = user_passes_test(lambda u: u.is_authenticated and can_access_dashboard(u))


def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def home(request):
    logger.info(f"Home view called - Path: {request.path}, Host: {request.get_host()}")
    
    # Check if migrations are applied
    try:
        from django.core.management import call_command
        from io import StringIO
        output = StringIO()
        call_command('showmigrations', 'properties', verbosity=0, stdout=output)
        migrations_status = output.getvalue()
        logger.info(f"Properties migrations: {migrations_status[:100]}")
    except Exception as e:
        logger.error(f"Error checking migrations: {e}")
    
    # Calculate real statistics
    from .models import Property, Broker, BrokerChannel, User, Hotel, Resort, Job, ServiceProvider, ServiceAdvertisement, Auction
    stats = {
        'total_properties': 0,
        'total_brokers': 0,
        'total_channels': 0,
        'total_users': 0,
        'total_views': 0,
        'successful_transactions': 0,
        'iraq_properties': 0,
        'foreign_properties': 0,
        'iraq_hotels': 0,
        'foreign_hotels': 0,
        'iraq_resorts': 0,
        'foreign_resorts': 0,
        'total_jobs': 0,
        'building_requests': 0,
        'service_providers': 0,
        'service_advertisements': 0,
        'auctions': 0,
    }
    
    try:
        stats['total_properties'] = Property.objects.filter(status='published').count()
        stats['total_brokers'] = Broker.objects.filter(is_active=True).count()
        stats['total_channels'] = BrokerChannel.objects.filter(status='active').count()
        stats['total_users'] = User.objects.filter(is_active=True).count()
        
        # Property locations
        try:
            from .models import Country
            iraq_country = Country.objects.filter(code='IQ').first()
            if iraq_country:
                stats['iraq_properties'] = Property.objects.filter(status='published', country=iraq_country).count()
                stats['foreign_properties'] = Property.objects.filter(status='published').exclude(country=iraq_country).count()
                stats['iraq_hotels'] = Hotel.objects.filter(country=iraq_country).count()
                stats['foreign_hotels'] = Hotel.objects.exclude(country=iraq_country).count()
                stats['iraq_resorts'] = Resort.objects.filter(country=iraq_country).count()
                stats['foreign_resorts'] = Resort.objects.exclude(country=iraq_country).count()
            else:
                # Fallback if Iraq country doesn't exist
                stats['iraq_properties'] = 0
                stats['foreign_properties'] = Property.objects.filter(status='published').count()
                stats['iraq_hotels'] = 0
                stats['foreign_hotels'] = Hotel.objects.count()
                stats['iraq_resorts'] = 0
                stats['foreign_resorts'] = Resort.objects.count()
        except Exception as e:
            logger.warning(f"Error calculating location stats: {e}")
            stats['iraq_properties'] = 0
            stats['foreign_properties'] = Property.objects.filter(status='published').count()
            stats['iraq_hotels'] = 0
            stats['foreign_hotels'] = Hotel.objects.count()
            stats['iraq_resorts'] = 0
            stats['foreign_resorts'] = Resort.objects.count()
        
        # Jobs
        stats['total_jobs'] = Job.objects.count()
        
        # Services
        stats['service_providers'] = ServiceProvider.objects.count()
        stats['service_advertisements'] = ServiceAdvertisement.objects.count()
        
        # Auctions
        stats['auctions'] = Auction.objects.count()
        
        # Calculate total views from PropertyViewStats
        try:
            from .models import PropertyViewStats
            if PropertyViewStats.objects.exists():
                total_views = PropertyViewStats.objects.aggregate(total_views=Sum('total_views'))
                stats['total_views'] = total_views['total_views'] or 0
            else:
                stats['total_views'] = 0
        except Exception as e:
            logger.warning(f"Error calculating total views: {e}")
            stats['total_views'] = 0
        
        # Fallback: calculate total views from PropertyViewStats objects
        if stats['total_views'] == 0:
            try:
                from .models import PropertyViewStats
                total_views = PropertyViewStats.objects.aggregate(total_views=Sum('total_views'))
                stats['total_views'] = total_views['total_views'] or 0
            except Exception as e:
                logger.warning(f"Error calculating total views from property view stats: {e}")
                stats['total_views'] = 0
        
        # Calculate successful transactions (using Message count as proxy)
        try:
            from .models import Message
            stats['successful_transactions'] = Message.objects.filter(message_type='inquiry').count()
        except:
            stats['successful_transactions'] = 0
            
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
    
    try:
        from .utils import expire_featured_and_publications
        expire_featured_and_publications()
        properties = get_public_properties()
        form = PropertySearchForm(request.GET)
        properties = filter_properties(properties, request.GET)
        properties = sort_properties(properties, request.GET.get('sort'))
        
        # Get featured and promoted before pagination to avoid N+1 queries
        featured_properties = [p for p in properties if p.is_featured][:6]
        promoted_properties = [p for p in properties if p.is_promoted][:4]
        
        # Get dallal properties if system is enabled
        dallal_properties = []
        try:
            from .dallal_logic import get_dallal_properties_for_display
            dallal_properties = get_dallal_properties_for_display()[:8]
        except Exception:
            dallal_properties = []
        
        paginator = Paginator(properties, 12)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        query_string = request.GET.urlencode()
        
        logger.info(f"Rendering home.html with {len(page_obj)} properties")
        from .constants import IRAQ_GOVERNORATES
        return render(request, 'properties/home.html', {
            'properties': page_obj,
            'page_obj': page_obj,
            'form': form,
            'featured_properties': featured_properties,
            'promoted_properties': promoted_properties,
            'dallal_properties': dallal_properties,
            'query_string': query_string,
            'governorates': IRAQ_GOVERNORATES,
            'stats': stats,
        })
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        return render(request, 'properties/home.html', {
            'properties': [],
            'page_obj': None,
            'form': PropertySearchForm(),
            'featured_properties': [],
            'promoted_properties': [],
            'dallal_properties': [],
            'query_string': '',
            'stats': stats,
        })


def property_detail(request, slug):
    property_obj = get_object_or_404(Property, slug=slug)
    if property_obj.status not in PUBLIC_STATUSES and not can_access_dashboard(request.user):
        messages.warning(request, 'هذا العقار غير متاح حالياً.')
        return redirect('home')

    property_obj.increment_views()
    images = property_obj.get_all_images()
    videos = property_obj.gallery_videos.all()
    
    # Track views for broker statistics
    if property_obj.broker:
        from .models import BrokerIndividualStats
        stats, created = BrokerIndividualStats.objects.get_or_create(broker=property_obj.broker)
        stats.update_views_stats()
    
    # Get virtual tours
    try:
        virtual_tours = property_obj.virtual_tours.filter(is_active=True)
    except Exception:
        virtual_tours = []

    public_props = get_public_properties()
    related = [
        p for p in public_props
        if p.pk != property_obj.pk and (p.district == property_obj.district or p.type == property_obj.type)
    ][:4]

    message_form = MessageForm()
    return render(request, 'properties/property_detail.html', {
        'property': property_obj,
        'images': images,
        'videos': videos,
        'virtual_tours': virtual_tours,
        'related_properties': related,
        'message_form': message_form,
    })


def property_detail_legacy(request, property_id):
    prop = get_object_or_404(Property, pk=property_id)
    return redirect(prop.get_absolute_url(), permanent=True)


def about_page(request):
    settings = SiteSettings.get_solo()
    return render(request, 'properties/about.html', {
        'site_settings': settings,
        'total_properties': len(get_public_properties()),
    })


def service_categories_view(request):
    """Service categories page - professional service sections"""
    return render(request, 'properties/service_categories.html')


def navigation_error_view(request):
    """Navigation error page - shown when route is not found"""
    return render(request, 'properties/navigation_error.html', status=404)


def interactive_map_view(request):
    """Interactive map page for property search and visualization - SECURE VERSION"""
    try:
        from .permissions import get_user_type
        
        # Get filter parameters
        governorate = request.GET.get('governorate')
        city = request.GET.get('city')
        
        # Base queryset - only published properties with valid coordinates
        properties = Property.objects.filter(
            is_published=True,
            status__in=PUBLIC_STATUSES,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker', 'owner').prefetch_related('gallery_images').order_by('-created_at')[:100]
        
        # Apply filters from Backend
        if governorate:
            properties = properties.filter(governorate=governorate)
        if city:
            properties = properties.filter(city=city)
        
        # Check user permissions
        user_type = get_user_type(request.user) if request.user.is_authenticated else None
        
        property_data = []
        for prop in properties:
            try:
                # Validate coordinates are reasonable
                lat = float(prop.latitude)
                lng = float(prop.longitude)
                
                # Skip invalid coordinates (0,0)
                if lat == 0 and lng == 0:
                    continue
                
                # Skip coordinates outside valid ranges
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue
                
                # Build property data - MINIMAL PUBLIC DATA ONLY
                prop_data = {
                    'id': prop.id,
                    'title': prop.title,
                    'slug': prop.slug,
                    'price': prop.price,
                    'currency': prop.currency,
                    'property_type': prop.property_type,
                    'transaction_type': prop.transaction_type,
                    'area': prop.area,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'governorate': prop.governorate,
                    'city': prop.city,
                    'latitude': lat,
                    'longitude': lng,
                    'url': f'/property/{prop.slug}/' if prop.slug else '',
                }
                
                # Add image safely
                if prop.main_image:
                    prop_data['image'] = f'/media/{prop.main_image.name}'
                
                # SECURITY: Only add broker data for authorized users
                if user_type in ['admin', 'broker']:
                    if prop.broker:
                        prop_data['broker_name'] = prop.broker.display_name
                
                property_data.append(prop_data)
                
            except Exception:
                continue

        return render(request, 'properties/interactive_map.html', {
            'initial_properties': property_data,
        })
    except Exception as e:
        logger.exception(f'Error loading map view: {e}')
        return render(request, 'properties/interactive_map.html', {
            'initial_properties': [],
        })


def map_api_properties(request):
    """API endpoint to get properties for the map - SECURE VERSION"""
    try:
        from .permissions import get_user_type
        import json
        
        # Get filter parameters
        governorate = request.GET.get('governorate')
        city = request.GET.get('city')
        property_type = request.GET.get('property_type')
        transaction_type = request.GET.get('transaction_type')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        bounds = request.GET.get('bounds')
        
        # Base queryset - only published properties with valid coordinates
        properties = Property.objects.filter(
            is_published=True,
            status__in=PUBLIC_STATUSES,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker', 'owner').prefetch_related('gallery_images').order_by('-created_at')[:200]
        
        # Apply filters from Backend (not just JavaScript)
        if governorate:
            properties = properties.filter(governorate=governorate)
        if city:
            properties = properties.filter(city=city)
        if property_type:
            properties = properties.filter(property_type=property_type)
        if transaction_type:
            properties = properties.filter(transaction_type=transaction_type)
        if price_min:
            try:
                properties = properties.filter(price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                properties = properties.filter(price__lte=float(price_max))
            except ValueError:
                pass
        
        # Apply bounding box filter for performance
        if bounds:
            try:
                bounds_data = json.loads(bounds)
                south = float(bounds_data.get('south'))
                north = float(bounds_data.get('north'))
                west = float(bounds_data.get('west'))
                east = float(bounds_data.get('east'))
                properties = properties.filter(
                    latitude__gte=south,
                    latitude__lte=north,
                    longitude__gte=west,
                    longitude__lte=east
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Check user permissions
        user_type = get_user_type(request.user) if request.user.is_authenticated else None
        
        property_data = []
        for prop in properties:
            try:
                # Validate coordinates are reasonable
                lat = float(prop.latitude)
                lng = float(prop.longitude)
                
                # Skip invalid coordinates (0,0)
                if lat == 0 and lng == 0:
                    continue
                
                # Skip coordinates outside valid ranges
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue
                
                # Build property data - MINIMAL PUBLIC DATA ONLY
                prop_data = {
                    'id': prop.id,
                    'title': prop.title,
                    'slug': prop.slug,
                    'price': prop.price,
                    'currency': prop.currency,
                    'property_type': prop.property_type,
                    'transaction_type': prop.transaction_type,
                    'area': prop.area,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'governorate': prop.governorate,
                    'city': prop.city,
                    'latitude': lat,
                    'longitude': lng,
                    'url': f'/property/{prop.slug}/' if prop.slug else '',
                }
                
                # Add image safely - don't expose full URL
                if prop.main_image:
                    prop_data['image'] = f'/media/{prop.main_image.name}'
                
                # SECURITY: Only add broker data for authorized users
                if user_type in ['admin', 'broker']:
                    if prop.broker:
                        prop_data['broker_name'] = prop.broker.display_name
                
                property_data.append(prop_data)
                
            except Exception:
                continue

        return JsonResponse({
            'success': True,
            'properties': property_data,
            'total': len(property_data),
            'filtered': len(property_data)
        })
    except Exception as e:
        logger.exception(f"Error fetching map properties: {e}")
        return JsonResponse({
            'success': False,
            'error': 'تعذر تحميل العقارات حالياً',
            'properties': [],
            'total': 0
        }, status=500)


def map_api_search(request):
    """API endpoint to search properties on the map - SECURE VERSION"""
    try:
        from .permissions import get_user_type
        
        governorate = request.GET.get('governorate')
        city = request.GET.get('city')
        property_type = request.GET.get('property_type')
        transaction_type = request.GET.get('transaction_type')
        max_price = request.GET.get('max_price')
        min_area = request.GET.get('min_area')

        properties = Property.objects.filter(
            is_published=True,
            status__in=PUBLIC_STATUSES,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker', 'owner').prefetch_related('gallery_images')

        if governorate:
            properties = properties.filter(governorate__icontains=governorate)
        if city:
            properties = properties.filter(city__icontains=city)
        if property_type:
            properties = properties.filter(property_type=property_type)
        if transaction_type:
            properties = properties.filter(transaction_type=transaction_type)
        if max_price:
            try:
                properties = properties.filter(price__lte=float(max_price))
            except ValueError:
                pass
        if min_area:
            try:
                properties = properties.filter(area__gte=float(min_area))
            except ValueError:
                pass

        properties = properties.order_by('-created_at')[:200]
        
        # Check user permissions
        user_type = get_user_type(request.user) if request.user.is_authenticated else None

        property_data = []
        for prop in properties:
            try:
                # Validate coordinates are reasonable
                lat = float(prop.latitude)
                lng = float(prop.longitude)
                
                # Skip invalid coordinates (0,0)
                if lat == 0 and lng == 0:
                    continue
                
                # Skip coordinates outside valid ranges
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue
                
                # Build property data - MINIMAL PUBLIC DATA ONLY
                prop_data = {
                    'id': prop.id,
                    'title': prop.title,
                    'slug': prop.slug,
                    'price': prop.price,
                    'currency': prop.currency,
                    'property_type': prop.property_type,
                    'transaction_type': prop.transaction_type,
                    'area': prop.area,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'governorate': prop.governorate,
                    'city': prop.city,
                    'latitude': lat,
                    'longitude': lng,
                    'url': f'/property/{prop.slug}/' if prop.slug else '',
                }
                
                # Add image safely
                if prop.main_image:
                    prop_data['image'] = f'/media/{prop.main_image.name}'
                
                # SECURITY: Only add broker data for authorized users
                if user_type in ['admin', 'broker']:
                    if prop.broker:
                        prop_data['broker_name'] = prop.broker.display_name
                
                property_data.append(prop_data)
            except Exception:
                pass

        return JsonResponse({
            'success': True,
            'properties': property_data,
            'total': len(property_data)
        })
    except Exception as e:
        logger.exception(f'Error searching map properties: {e}')
        return JsonResponse({
            'success': False,
            'error': 'تعذر تحميل العقارات حالياً',
            'properties': [],
            'total': 0
        }, status=500)


def map_api_nearby(request):
    """API endpoint to get properties near a location"""
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 5))  # km

        from math import radians, cos, sin, sqrt, asin

        # Simple distance calculation
        def distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dLat = radians(lat2 - lat1)
            dLon = radians(lon2 - lon1)
            a = sin(dLat/2) * sin(dLat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2) * sin(dLon/2)
            c = 2 * asin(sqrt(a))
            return R * c

        properties = Property.objects.filter(
            is_published=True,
            status='available',
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker')

        nearby_properties = []
        for prop in properties:
            try:
                dist = distance(lat, lng, float(prop.latitude), float(prop.longitude))
                if dist <= radius:
                    nearby_properties.append({
                        'id': prop.id,
                        'title': prop.title,
                        'slug': prop.slug,
                        'price': prop.price,
                        'currency': prop.currency,
                        'property_type': prop.property_type,
                        'transaction_type': prop.transaction_type,
                        'area': prop.area,
                        'latitude': float(prop.latitude),
                        'longitude': float(prop.longitude),
                        'distance': round(dist, 2),
                        'main_image': prop.main_image.url if prop.main_image else None,
                    })
            except Exception:
                pass

        nearby_properties.sort(key=lambda x: x['distance'])

        return JsonResponse({
            'success': True,
            'properties': nearby_properties[:50],
            'total': len(nearby_properties)
        })
    except Exception as e:
        logger.exception(f'Error fetching nearby properties: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'properties': [],
            'total': 0
        }, status=500)


def map_api_stats(request):
    """API endpoint to get area statistics"""
    try:
        governorate = request.GET.get('governorate')

        properties = Property.objects.filter(
            is_published=True,
            status='available'
        )

        if governorate:
            properties = properties.filter(governorate__icontains=governorate)

        try:
            total_count = properties.count()
        except Exception:
            total_count = 0

        try:
            prices = [p.price for p in properties if p.price]
            avg_price = sum(prices) / len(prices) if prices else 0
        except Exception:
            avg_price = 0

        try:
            property_types = {}
            for prop in properties:
                if prop.property_type:
                    property_types[prop.property_type] = property_types.get(prop.property_type, 0) + 1
        except Exception:
            property_types = {}

        return JsonResponse({
            'success': True,
            'stats': {
                'total_properties': total_count,
                'average_price': avg_price,
                'property_types': property_types,
                'price_trend': 'stable'  # Placeholder
            }
        })
    except Exception as e:
        logger.exception(f'Error fetching map stats: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'stats': {
                'total_properties': 0,
                'average_price': 0,
                'property_types': {},
                'price_trend': 'unknown'
            }
        }, status=500)
    """API endpoint to get properties for the map"""
    try:
        properties = []
        try:
            properties = Property.objects.filter(
                is_published=True,
                status='available'
            ).select_related('broker').order_by('-created_at')[:200]
        except Exception:
            pass

        property_data = []
        for prop in properties:
            try:
                if prop.latitude and prop.longitude:
                    property_data.append({
                        'id': prop.id,
                        'title': prop.title,
                        'slug': prop.slug,
                        'price': prop.price,
                        'currency': prop.currency,
                        'property_type': prop.property_type,
                        'transaction_type': prop.transaction_type,
                        'area': prop.area,
                        'bedrooms': prop.bedrooms,
                        'bathrooms': prop.bathrooms,
                        'governorate': prop.governorate,
                        'city': prop.city,
                        'latitude': float(prop.latitude),
                        'longitude': float(prop.longitude),
                        'main_image': prop.main_image.url if prop.main_image else None,
                        'broker_name': prop.broker.display_name if prop.broker else None,
                        'created_at': prop.created_at.isoformat() if prop.created_at else None,
                    })
            except Exception:
                pass

        return JsonResponse({
            'success': True,
            'properties': property_data,
            'total': len(property_data)
        })
    except Exception as e:
        logger.exception(f'Error fetching map properties: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'properties': [],
            'total': 0
        }, status=500)


def map_api_search(request):
    """API endpoint to search properties on the map - SECURE VERSION"""
    try:
        from .permissions import get_user_type
        
        governorate = request.GET.get('governorate')
        city = request.GET.get('city')
        property_type = request.GET.get('property_type')
        transaction_type = request.GET.get('transaction_type')
        max_price = request.GET.get('max_price')
        min_area = request.GET.get('min_area')

        properties = Property.objects.filter(
            is_published=True,
            status__in=PUBLIC_STATUSES,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker', 'owner').prefetch_related('gallery_images')

        if governorate:
            properties = properties.filter(governorate__icontains=governorate)
        if city:
            properties = properties.filter(city__icontains=city)
        if property_type:
            properties = properties.filter(property_type=property_type)
        if transaction_type:
            properties = properties.filter(transaction_type=transaction_type)
        if max_price:
            try:
                properties = properties.filter(price__lte=float(max_price))
            except ValueError:
                pass
        if min_area:
            try:
                properties = properties.filter(area__gte=float(min_area))
            except ValueError:
                pass

        properties = properties.order_by('-created_at')[:200]
        
        # Check user permissions
        user_type = get_user_type(request.user) if request.user.is_authenticated else None

        property_data = []
        for prop in properties:
            try:
                # Validate coordinates are reasonable
                lat = float(prop.latitude)
                lng = float(prop.longitude)
                
                # Skip invalid coordinates (0,0)
                if lat == 0 and lng == 0:
                    continue
                
                # Skip coordinates outside valid ranges
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue
                
                # Build property data - MINIMAL PUBLIC DATA ONLY
                prop_data = {
                    'id': prop.id,
                    'title': prop.title,
                    'slug': prop.slug,
                    'price': prop.price,
                    'currency': prop.currency,
                    'property_type': prop.property_type,
                    'transaction_type': prop.transaction_type,
                    'area': prop.area,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'governorate': prop.governorate,
                    'city': prop.city,
                    'latitude': lat,
                    'longitude': lng,
                    'url': f'/property/{prop.slug}/' if prop.slug else '',
                }
                
                # Add image safely
                if prop.main_image:
                    prop_data['image'] = f'/media/{prop.main_image.name}'
                
                # SECURITY: Only add broker data for authorized users
                if user_type in ['admin', 'broker']:
                    if prop.broker:
                        prop_data['broker_name'] = prop.broker.display_name
                
                property_data.append(prop_data)
            except Exception:
                pass

        return JsonResponse({
            'success': True,
            'properties': property_data,
            'total': len(property_data)
        })
    except Exception as e:
        logger.exception(f'Error searching map properties: {e}')
        return JsonResponse({
            'success': False,
            'error': 'تعذر تحميل العقارات حالياً',
            'properties': [],
            'total': 0
        }, status=500)


def map_api_nearby(request):
    """API endpoint to get properties near a location"""
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 5))  # km

        from django.db.models import F
        from math import radians, cos, sin, sqrt, asin

        # Simple distance calculation
        def distance(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dLat = radians(lat2 - lat1)
            dLon = radians(lon2 - lon1)
            a = sin(dLat/2) * sin(dLat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2) * sin(dLon/2)
            c = 2 * asin(sqrt(a))
            return R * c

        properties = Property.objects.filter(
            is_published=True,
            status='available',
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('broker')

        nearby_properties = []
        for prop in properties:
            try:
                dist = distance(lat, lng, float(prop.latitude), float(prop.longitude))
                if dist <= radius:
                    nearby_properties.append({
                        'id': prop.id,
                        'title': prop.title,
                        'slug': prop.slug,
                        'price': prop.price,
                        'currency': prop.currency,
                        'property_type': prop.property_type,
                        'transaction_type': prop.transaction_type,
                        'area': prop.area,
                        'latitude': float(prop.latitude),
                        'longitude': float(prop.longitude),
                        'distance': round(dist, 2),
                        'main_image': prop.main_image.url if prop.main_image else None,
                    })
            except Exception:
                pass

        nearby_properties.sort(key=lambda x: x['distance'])

        return JsonResponse({
            'success': True,
            'properties': nearby_properties[:50],
            'total': len(nearby_properties)
        })
    except Exception as e:
        logger.exception(f'Error fetching nearby properties: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'properties': [],
            'total': 0
        }, status=500)


def map_api_stats(request):
    """API endpoint to get area statistics"""
    try:
        governorate = request.GET.get('governorate')

        properties = Property.objects.filter(
            is_published=True,
            status='available'
        )

        if governorate:
            properties = properties.filter(governorate__icontains=governorate)

        try:
            total_count = properties.count()
        except Exception:
            total_count = 0

        try:
            prices = [p.price for p in properties if p.price]
            avg_price = sum(prices) / len(prices) if prices else 0
        except Exception:
            avg_price = 0

        try:
            property_types = {}
            for prop in properties:
                if prop.property_type:
                    property_types[prop.property_type] = property_types.get(prop.property_type, 0) + 1
        except Exception:
            property_types = {}

        return JsonResponse({
            'success': True,
            'stats': {
                'total_properties': total_count,
                'average_price': avg_price,
                'property_types': property_types,
                'price_trend': 'stable'  # Placeholder
            }
        })
    except Exception as e:
        logger.exception(f'Error fetching map stats: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'stats': {
                'total_properties': 0,
                'average_price': 0,
                'property_types': {},
                'price_trend': 'unknown'
            }
        }, status=500)


def contact_page(request):
    try:
        settings = SiteSettings.get_solo()
    except Exception:
        settings = None
    form = MessageForm()
    return render(request, 'properties/contact.html', {
        'settings': settings,
        'form': form,
    })


def subscription_plans(request):
    """Display subscription plans page."""
    try:
        settings = SiteSettings.get_solo()
    except Exception:
        settings = None
    return render(request, 'properties/subscription_plans.html', {
        'site_settings': settings,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscription_expire_notification(request):
    """Handle subscription expiration notification from client."""
    if not request.user.is_authenticated or not hasattr(request.user, 'broker_profile'):
        return Response({'error': 'Unauthorized'}, status=401)
    
    broker = request.user.broker_profile
    
    # Create notification for broker
    from django.core.mail import send_mail
    
    # Send email notification to broker
    if broker.user.email:
        send_mail(
            'انتهاء اشتراكك في دلال',
            'عزيزي الدلال،\n\nاشتراكك في منصة دلال قد انتهى. يرجى تجديده للمتابعة في استخدام الخدمة.\n\nيمكنك تجديد اشتراكك من خلال الرابط التالي:\nhttps://yourdomain.com/subscription-plans/\n\nشكراً لاستخدامك منصة دلال.',
            settings.DEFAULT_FROM_EMAIL,
            [broker.user.email],
            fail_silently=True,
        )
    
    # Send notification to admin
    admin_users = User.objects.filter(is_superuser=True, email__isnull=False)
    for admin in admin_users:
        if admin.email:
            send_mail(
                f'انتهاء اشتراك الدلال: {broker.display_name}',
                f'اشتراك الدلال {broker.display_name} قد انتهى.\n\nرقم الهاتف: {broker.phone}\nتاريخ الانتهاء: {broker.subscription_end_date}',
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],
                fail_silently=True,
            )
    
    return Response({'success': True, 'message': 'Notification sent successfully'})


@login_required
def admin_brokers_management(request):
    """Professional broker management panel for admin"""
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    
    from .models import Broker, BrokerChannel, Property
    from django.core.paginator import Paginator
    from .constants import IRAQ_GOVERNORATES
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    verified_filter = request.GET.get('verified', '')
    role_filter = request.GET.get('role', '')
    subscription_filter = request.GET.get('subscription', '')
    governorate_filter = request.GET.get('governorate', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # Base queryset
    brokers = Broker.objects.select_related('user').all()
    
    # Apply filters
    if search_query:
        brokers = brokers.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if status_filter == 'active':
        brokers = brokers.filter(is_active=True)
    elif status_filter == 'inactive':
        brokers = brokers.filter(is_active=False)
    elif status_filter == 'expired':
        # Filter by expired subscriptions
        brokers = brokers.filter(
            subscription_end_date__lt=timezone.now().date()
        )
    
    if verified_filter == 'verified':
        brokers = brokers.filter(is_verified=True)
    elif verified_filter == 'unverified':
        brokers = brokers.filter(is_verified=False)
    
    if role_filter == 'admin':
        brokers = brokers.filter(role=Broker.ROLE_ADMIN)
    elif role_filter == 'main':
        brokers = brokers.filter(role=Broker.ROLE_MAIN)
    elif role_filter == 'sub':
        brokers = brokers.filter(role=Broker.ROLE_SUB)
    
    if subscription_filter:
        brokers = brokers.filter(subscription_plan__plan_type=subscription_filter)
    
    if governorate_filter:
        brokers = brokers.filter(governorate=governorate_filter)
    
    # Sorting
    if sort_by == 'newest':
        brokers = brokers.order_by('-id')
    elif sort_by == 'oldest':
        brokers = brokers.order_by('id')
    elif sort_by == 'name':
        brokers = brokers.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'properties':
        brokers = brokers.annotate(
            property_count=Count('property')
        ).order_by('-property_count')
    elif sort_by == 'performance':
        brokers = brokers.order_by('-performance_rating')
    elif sort_by == 'revenue':
        brokers = brokers.order_by('-total_commissions')
    
    # Pagination
    paginator = Paginator(brokers, 25)
    page = request.GET.get('page', 1)
    brokers_page = paginator.get_page(page)
    
    # Statistics
    total_brokers = Broker.objects.count()
    verified_brokers = Broker.objects.filter(is_verified=True).count()
    total_properties = Property.objects.filter(broker__isnull=False).count()
    active_brokers = Broker.objects.filter(is_active=True).count()
    expired_subscriptions = Broker.objects.filter(
        subscription_end_date__lt=timezone.now().date()
    ).count()
    
    # Revenue calculation
    from django.db.models import Sum
    total_revenue = Broker.objects.aggregate(
        total=Sum('total_commissions')
    )['total'] or 0
    
    # Geographic distribution
    governorate_stats = []
    for code, name in IRAQ_GOVERNORATES:
        count = Broker.objects.filter(governorate=code).count()
        if count > 0:
            governorate_stats.append({
                'code': code,
                'name': name,
                'count': count
            })
    
    governorate_stats.sort(key=lambda x: x['count'], reverse=True)
    
    context = {
        'brokers': brokers_page,
        'total_brokers': total_brokers,
        'verified_brokers': verified_brokers,
        'total_properties': total_properties,
        'active_brokers': active_brokers,
        'expired_subscriptions': expired_subscriptions,
        'total_revenue': total_revenue,
        'governorate_stats': governorate_stats,
        'governorates': IRAQ_GOVERNORATES,
        'search_query': search_query,
        'status_filter': status_filter,
        'verified_filter': verified_filter,
        'role_filter': role_filter,
        'subscription_filter': subscription_filter,
        'governorate_filter': governorate_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'properties/admin_brokers_management.html', context)


@login_required
def main_broker_panel(request):
    """Main broker panel to manage sub brokers and their properties"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلالاً للوصول إلى هذه الصفحة')
        return redirect('home')
    
    broker = request.user.broker_profile
    
    # Check if user is main broker
    if broker.role != Broker.ROLE_MAIN and broker.role != Broker.ROLE_ADMIN:
        messages.error(request, 'يجب أن تكون دلالاً رئيسياً للوصول إلى هذه الصفحة')
        return redirect('home')
    
    # Get sub brokers
    sub_brokers = broker.sub_brokers.filter(is_active=True)
    
    # Get all properties from sub brokers
    from django.db.models import Count, Q
    sub_broker_properties = Property.objects.filter(
        Q(broker__in=sub_brokers) | Q(owner__in=[b.user for b in sub_brokers])
    ).select_related('broker', 'owner')
    
    # Statistics
    total_sub_brokers = sub_brokers.count()
    total_properties = sub_broker_properties.count()
    active_properties = sub_broker_properties.filter(status__in=PUBLIC_STATUSES).count()
    
    # Recent activity
    recent_properties = sub_broker_properties.order_by('-created_at')[:10]
    
    # Get recent appointments for broker and sub-brokers
    from .models import BrokerAppointment
    all_brokers = [broker] + list(sub_brokers)
    recent_appointments = BrokerAppointment.objects.filter(
        broker__in=all_brokers
    ).select_related('user', 'property').order_by('-created_at')[:10]
    
    context = {
        'broker': broker,
        'sub_brokers': sub_brokers,
        'sub_broker_properties': sub_broker_properties,
        'total_sub_brokers': total_sub_brokers,
        'total_properties': total_properties,
        'active_properties': active_properties,
        'recent_properties': recent_properties,
        'recent_appointments': recent_appointments,
    }
    
    return render(request, 'properties/main_broker_panel.html', context)


def broker_profile(request, username):
    """Display broker's profile with their properties only."""
    broker = get_object_or_404(Broker, user__username=username)
    
    # Get only this broker's properties
    properties = Property.objects.filter(
        Q(broker=broker) | Q(owner=broker.user),
        status__in=PUBLIC_STATUSES
    ).select_related().prefetch_related('gallery_images')
    
    # Apply search filters
    properties = filter_properties(properties, request.GET)
    properties = sort_properties(properties, request.GET.get('sort'))
    
    # Pagination
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    query_string = request.GET.urlencode()
    
    # Get broker stats
    property_count = broker.get_published_properties_count()
    property_limit = broker.get_property_limit()
    remaining_properties = broker.get_remaining_properties()
    days_elapsed = broker.get_days_elapsed()
    days_remaining = broker.get_days_remaining()
    
    return render(request, 'properties/broker_profile.html', {
        'broker': broker,
        'properties': page_obj,
        'page_obj': page_obj,
        'query_string': query_string,
        'property_count': property_count,
        'property_limit': property_limit,
        'remaining_properties': remaining_properties,
        'days_elapsed': days_elapsed,
        'days_remaining': days_remaining,
    })


def broker_standalone_page(request, slug):
    """Display broker's standalone page with their properties only."""
    broker = get_object_or_404(Broker, slug=slug)
    
    # Check if broker has standalone page enabled (allow owner to preview regardless)
    is_owner = request.user.is_authenticated and request.user == broker.user
    if not is_owner and broker.page_display_mode not in ['standalone_only', 'both']:
        # If not, show a message or redirect
        from django.contrib import messages
        messages.warning(request, 'هذا الدلال لم يفعّل الصفحة المستقلة بعد')
        return redirect('home')
    
    # Get only this broker's properties
    properties = Property.objects.filter(
        Q(broker=broker) | Q(owner=broker.user),
        status__in=PUBLIC_STATUSES
    ).select_related().prefetch_related('gallery_images')
    
    # Apply search filters
    properties = filter_properties(properties, request.GET)
    properties = sort_properties(properties, request.GET.get('sort'))
    
    # Pagination
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    query_string = request.GET.urlencode()
    
    # Get broker stats
    property_count = broker.get_published_properties_count()
    property_limit = broker.get_property_limit()
    remaining_properties = broker.get_remaining_properties()
    days_elapsed = broker.get_days_elapsed()
    days_remaining = broker.get_days_remaining()
    
    # Generate QR Code
    import qrcode
    from io import BytesIO
    import base64
    
    # Build the full URL for the broker's standalone page
    protocol = 'https' if request.is_secure() else 'http'
    broker_url = f"{protocol}://{request.get_host()}/d/{broker.slug}/"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(broker_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'properties/broker_standalone_page.html', {
        'broker': broker,
        'properties': page_obj,
        'page_obj': page_obj,
        'query_string': query_string,
        'property_count': property_count,
        'property_limit': property_limit,
        'remaining_properties': remaining_properties,
        'days_elapsed': days_elapsed,
        'days_remaining': days_remaining,
        'qr_code': qr_image_base64,
    })


@login_required
@broker_required
def broker_standalone_settings(request):
    """Handle broker standalone page settings."""
    broker = get_broker(request.user)
    
    # Generate auto slug if not exists
    if not broker.slug:
        # Generate slug from display name
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s_-]', '', broker.display_name.lower())
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # If still empty, use random
        if not slug:
            import random
            import string
            slug = 'broker-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while Broker.objects.filter(slug=slug).exclude(id=broker.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        broker.slug = slug
        broker.save()
    
    if request.method == 'POST':
        # Update page display mode
        page_display_mode = request.POST.get('page_display_mode', 'main_only')
        broker.page_display_mode = page_display_mode
        
        # Update site information
        broker.site_name = request.POST.get('site_name', '')
        broker.job_title = request.POST.get('job_title', '')
        broker.mission = request.POST.get('mission', '')
        broker.vision = request.POST.get('vision', '')
        broker.years_of_experience = int(request.POST.get('years_of_experience', 0)) if request.POST.get('years_of_experience') else 0
        broker.clients_count = int(request.POST.get('clients_count', 0)) if request.POST.get('clients_count') else 0
        broker.working_governorates = request.POST.get('working_governorates', '')
        
        # Update contact information
        broker.whatsapp = request.POST.get('whatsapp', '')
        broker.telegram = request.POST.get('telegram', '')
        broker.email = request.POST.get('email', '')
        broker.website = request.POST.get('website', '')
        broker.address = request.POST.get('address', '')
        broker.working_hours = request.POST.get('working_hours', '')
        broker.google_maps_url = request.POST.get('google_maps_url', '')
        
        # Update social media
        broker.facebook = request.POST.get('facebook', '')
        broker.instagram = request.POST.get('instagram', '')
        broker.tiktok = request.POST.get('tiktok', '')
        broker.snapchat = request.POST.get('snapchat', '')
        broker.twitter = request.POST.get('twitter', '')
        broker.youtube = request.POST.get('youtube', '')
        broker.linkedin = request.POST.get('linkedin', '')
        
        # Update SEO
        broker.seo_title = request.POST.get('seo_title', '')
        broker.seo_description = request.POST.get('seo_description', '')
        broker.seo_keywords = request.POST.get('seo_keywords', '')
        
        # Update customization
        broker.page_color = request.POST.get('page_color', '#FF7A00')
        broker.button_color = request.POST.get('button_color', '#FF7A00')
        broker.text_color = request.POST.get('text_color', '#333333')
        broker.background_color = request.POST.get('background_color', '#FFFFFF')
        broker.font_family = request.POST.get('font_family', 'Cairo')
        
        # Update display settings
        broker.show_phone = request.POST.get('show_phone') == 'on'
        broker.show_email = request.POST.get('show_email') == 'on'
        broker.show_whatsapp = request.POST.get('show_whatsapp') == 'on'
        broker.show_social_media = request.POST.get('show_social_media') == 'on'
        broker.show_address = request.POST.get('show_address') == 'on'
        broker.show_properties = request.POST.get('show_properties') == 'on'
        broker.show_stats = request.POST.get('show_stats') == 'on'
        broker.show_ratings = request.POST.get('show_ratings') == 'on'
        broker.show_working_hours = request.POST.get('show_working_hours') == 'on'
        
        # Update images if provided
        if 'logo' in request.FILES:
            broker.logo = request.FILES['logo']
        if 'cover_image' in request.FILES:
            broker.cover_image = request.FILES['cover_image']
        if 'profile_image' in request.FILES:
            broker.profile_image = request.FILES['profile_image']
        if 'og_image' in request.FILES:
            broker.og_image = request.FILES['og_image']
        if 'background_image' in request.FILES:
            broker.background_image = request.FILES['background_image']
        if 'banner_image' in request.FILES:
            broker.banner_image = request.FILES['banner_image']
        
        # Update bio
        broker.bio = request.POST.get('bio', '').strip()
        
        broker.save()
        
        messages.success(request, 'تم حفظ الإعدادات بنجاح')
        
        return redirect('broker_standalone_settings')
    
    # Generate auto slug for display
    import re
    broker_slug_auto = re.sub(r'[^a-zA-Z0-9\s_-]', '', broker.display_name.lower())
    broker_slug_auto = re.sub(r'\s+', '-', broker_slug_auto)
    broker_slug_auto = re.sub(r'-+', '-', broker_slug_auto)
    broker_slug_auto = broker_slug_auto.strip('-') or 'ahmed-broker'
    
    return render(request, 'properties/broker_standalone_settings.html', {
        'broker': broker,
        'broker_slug_auto': broker_slug_auto,
    })


def login_view(request):
    """Login view with CSRF protection enabled and rate limiting"""
    from .permissions import get_redirect_after_login, get_user_type, can_access_dashboard, get_broker
    from django.core.cache import cache
    from django.utils import timezone

    if request.user.is_authenticated:
        redirect_url = get_redirect_after_login(request.user)
        return redirect(redirect_url)

    # Rate limiting - prevent brute force attacks
    client_ip = get_client_ip(request)
    rate_limit_key = f'login_attempts_{client_ip}'
    attempts = cache.get(rate_limit_key, 0)
    
    if attempts >= 5:
        # Block for 15 minutes
        block_key = f'login_blocked_{client_ip}'
        if not cache.get(block_key):
            cache.set(block_key, True, 900)  # 15 minutes
            logger.warning('IP blocked due to too many login attempts: %s', client_ip)
            messages.error(request, 'تم حظر IP الخاص بك لمدة 15 دقيقة بسبب محاولات تسجيل دخول كثيرة')
            return render(request, 'properties/login.html')
        else:
            messages.error(request, 'تم حظر IP الخاص بك مؤقتاً. يرجى المحاولة لاحقاً')
            return render(request, 'properties/login.html')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Check if user is active
                if not user.is_active:
                    messages.error(request, 'تم تعطيل حسابك. يرجى التواصل مع الإدارة')
                    logger.warning('Login attempt for inactive user: %s', username)
                    # Increment failed attempts
                    cache.set(rate_limit_key, attempts + 1, 900)
                    return render(request, 'properties/login.html')
                
                # Clear failed attempts on successful login
                cache.delete(rate_limit_key)
                
                login(request, user)
                user_type = get_user_type(user)
                
                # Log successful login
                from .models import ActivityLog
                ActivityLog.log(
                    user=user,
                    action='login',
                    model_type='user',
                    object_id=user.id,
                    object_repr=user.username,
                    description=f'تسجيل دخول ناجح: {user.username}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'user_type': user_type}
                )
                
                # Redirect based on user type
                # Special case: muq 1234 always goes to admin panel
                if user.username == 'muq 1234':
                    messages.success(request, 'مرحباً بك في لوحة الإدارة')
                    return redirect('admin_panel')
                elif user_type == 'admin':
                    messages.success(request, 'مرحباً بك في لوحة الإدارة')
                    return redirect('admin_panel')
                elif user_type == 'broker':
                    broker = get_broker(user)
                    if broker and not broker.is_active:
                        messages.error(request, 'تم تعطيل حساب الدلال. يرجى التواصل مع الإدارة')
                        logout(request)
                        return render(request, 'properties/login.html')
                    messages.success(request, 'مرحباً بك في لوحة الدلال')
                    return redirect('broker_panel')
                else:  # user_type == 'user'
                    messages.success(request, 'مرحباً بك')
                    return redirect('user_dashboard')
            else:
                # Increment failed attempts
                cache.set(rate_limit_key, attempts + 1, 900)
                messages.error(request, 'بيانات الدخول غير صحيحة')
                logger.warning('Failed login attempt for user: %s (attempt %d)', username, attempts + 1)
    
    return render(request, 'properties/login.html')


def register_view(request):
    """Register a new user account with email verification and proper validation."""
    from django.contrib.auth.models import User
    from django.core.cache import cache
    import secrets
    import re
    
    if request.user.is_authenticated:
        return redirect('home')
    
    # Rate limiting for registration
    client_ip = get_client_ip(request)
    rate_limit_key = f'register_attempts_{client_ip}'
    attempts = cache.get(rate_limit_key, 0)
    
    if attempts >= 3:
        messages.error(request, 'محاولات تسجيل كثيرة. يرجى المحاولة بعد 15 دقيقة')
        return render(request, 'properties/register.html')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        birth_date = request.POST.get('birth_date', '').strip()
        city = request.POST.get('city', '').strip()
        governorate = request.POST.get('governorate', '').strip()
        address = request.POST.get('address', '').strip()
        profile_image = request.FILES.get('profile_image')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password or not phone:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
        elif len(username) < 3:
            messages.error(request, 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل')
        elif len(username) > 20:
            messages.error(request, 'اسم المستخدم يجب أن يكون 20 حرف كحد أقصى')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            messages.error(request, 'اسم المستخدم يجب أن يحتوي على أحرف وأرقام وشرطات سفلية فقط')
        elif password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
        elif len(password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        elif not re.search(r'[A-Z]', password):
            messages.error(request, 'كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل')
        elif not re.search(r'[a-z]', password):
            messages.error(request, 'كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل')
        elif not re.search(r'[0-9]', password):
            messages.error(request, 'كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم بالفعل')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
        else:
            # SECURITY: Ignore any frontend-provided role/permission fields
            # We explicitly set is_staff=False and don't allow any role escalation
            # All role-related fields from POST are ignored
            
            # Check for duplicate phone in Broker profiles
            from .models import Broker, UserProfile
            if Broker.objects.filter(phone=phone).exists():
                messages.error(request, 'رقم الهاتف مستخدم بالفعل')
            else:
                # Increment registration attempts
                cache.set(rate_limit_key, attempts + 1, 900)
                
                # SECURITY: Create regular user ONLY - no broker profile allowed
                # All frontend-provided role fields (is_staff, is_superuser, etc.) are ignored
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_staff=False,  # Force False - never from frontend
                    is_superuser=False,  # Force False - never from frontend
                    is_active=False  # Require email verification
                )
                
                # Generate verification token
                verification_token = secrets.token_urlsafe(32)
                
                # Store verification token in session (in production, use database with expiry)
                request.session[f'email_verification_{user.id}'] = {
                    'token': verification_token,
                    'email': email,
                    'created_at': timezone.now().isoformat(),
                }
                
                # Create or update UserProfile with additional information
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                user_profile.user_type = UserProfile.USER_TYPE_USER  # Force USER type
                user_profile.phone = phone
                if gender:
                    user_profile.gender = gender
                if birth_date:
                    user_profile.birth_date = birth_date
                if city:
                    user_profile.city = city
                if governorate:
                    user_profile.governorate = governorate
                if address:
                    user_profile.address = address
                if profile_image:
                    user_profile.profile_image = profile_image
                user_profile.save()

                # Create notification for admins
                from .utils import create_notification
                admins = User.objects.filter(is_superuser=True)
                
                for admin in admins:
                    create_notification(
                        user=admin,
                        notification_type='system',
                        title='مستخدم جديد يحتاج تفعيل',
                        message=f'مستخدم جديد ينتظر التفعيل: {user.get_full_name() or user.username}',
                        link=f'/admin/auth/user/{user.id}/change/',
                        metadata={'user_id': user.id, 'requires_verification': True}
                    )
                
                # Log activity
                from .models import ActivityLog
                ActivityLog.log(
                    user=user,
                    action='create',
                    model_type='user',
                    object_id=user.id,
                    object_repr=user.username,
                    description=f'إنشاء حساب مستخدم جديد (غير مفعل): {user.username}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'account_type': 'user', 'requires_verification': True}
                )
                
                # Send verification email
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    verification_link = f"{request.build_absolute_uri('/verify-email/')}?user_id={user.id}&token={verification_token}"
                    
                    subject = 'تفعيل حسابك - دلال'
                    message = f'''
مرحباً {user.get_full_name() or user.username}،

شكراً لتسجيلك في دلال. لتفعيل حسابك، يرجى الضغط على الرابط التالي:
{verification_link}

إذا لم تقم بالتسجيل، يرجى تجاهل هذا البريد الإلكتروني.

رابط التفعيل صالح لمدة 24 ساعة.

مع تحيات،
فريق دلال
                    '''
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, 'تم إنشاء الحساب بنجاح. يرجى فحص بريدك الإلكتروني لتفعيل الحساب')
                    logger.info('Registration successful for user: %s, verification email sent', user.username)
                    
                except Exception as e:
                    logger.error('Failed to send verification email: %s', str(e))
                    # Allow registration even if email fails, but warn the user
                    messages.warning(request, 'تم إنشاء الحساب ولكن لم نتمكن من إرسال بريد التفعيل. يرجى التواصل مع الإدارة.')
                
                return redirect('login')
    
    return render(request, 'properties/register.html')


def verify_email(request):
    """Handle email verification for new user accounts."""
    user_id = request.GET.get('user_id')
    token = request.GET.get('token')
    
    if not user_id or not token:
        messages.error(request, 'رابط التفعيل غير صالح')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        
        # Check if user is already active
        if user.is_active:
            messages.info(request, 'حسابك مفعل بالفعل. يمكنك تسجيل الدخول')
            return redirect('login')
        
        # Validate token from session
        session_data = request.session.get(f'email_verification_{user_id}')
        if not session_data:
            messages.error(request, 'رابط التفعيل منتهي الصلاحية')
            return redirect('login')
        
        stored_token = session_data.get('token')
        stored_email = session_data.get('email')
        created_at = session_data.get('created_at')
        
        if stored_token != token:
            messages.error(request, 'رابط التفعيل غير صالح')
            return redirect('login')
        
        # Check if token is expired (24 hours)
        from datetime import datetime, timedelta
        token_age = datetime.now() - datetime.fromisoformat(created_at)
        if token_age > timedelta(hours=24):
            messages.error(request, 'رابط التفعيل منتهي الصلاحية')
            return redirect('login')
        
        # Verify email matches
        if user.email != stored_email:
            messages.error(request, 'رابط التفعيل غير صالح')
            return redirect('login')
        
        # Activate user
        user.is_active = True
        user.save()
        
        # Clear verification token
        del request.session[f'email_verification_{user_id}']
        
        # Log activation
        from .models import ActivityLog
        ActivityLog.log(
            user=user,
            action='update',
            model_type='user',
            object_id=user.id,
            object_repr=user.username,
            description=f'تفعيل حساب المستخدم: {user.username}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'method': 'email_verification'}
        )
        
        # Create notification for admins
        from .utils import create_notification
        admins = User.objects.filter(is_superuser=True)
        
        for admin in admins:
            create_notification(
                user=admin,
                notification_type='system',
                title='تفعيل حساب جديد',
                message=f'تم تفعيل حساب المستخدم: {user.get_full_name() or user.username}',
                link=f'/admin/auth/user/{user.id}/change/',
                metadata={'user_id': user.id}
            )
        
        messages.success(request, 'تم تفعيل حسابك بنجاح. يمكنك الآن تسجيل الدخول')
        return redirect('login')
        
    except User.DoesNotExist:
        messages.error(request, 'رابط التفعيل غير صالح')
        return redirect('login')


def logout_view(request):
    """Logout view with session cleanup"""
    from django.contrib.auth import logout
    # Log logout before logout
    from .models import ActivityLog
    ActivityLog.log(
        user=request.user,
        action='logout',
        model_type='user',
        object_id=request.user.id,
        object_repr=request.user.username,
        description=f'تسجيل خروج: {request.user.username}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('home')


def password_reset_request(request):
    """Handle password reset request with actual email sending."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
        else:
            from django.contrib.auth.models import User
            from django.utils.crypto import get_random_string
            from django.core.mail import send_mail
            from django.conf import settings
            from django.utils import timezone
            import secrets
            
            try:
                user = User.objects.get(email=email)
                
                # Generate secure token
                token = secrets.token_urlsafe(32)
                
                # Store token in session (in production, use database with expiry)
                request.session[f'password_reset_token_{user.id}'] = {
                    'token': token,
                    'created_at': timezone.now().isoformat(),
                }
                
                # Create reset link
                reset_link = f"{request.build_absolute_uri('/password-reset-confirm/')}?user_id={user.id}&token={token}"
                
                # Send email
                subject = 'إعادة تعيين كلمة المرور - دلال'
                message = f'''
مرحباً {user.get_full_name() or user.username}،

لقد طلبت إعادة تعيين كلمة المرور لحسابك في دلال.

اضغط على الرابط التالي لإعادة تعيين كلمة المرور:
{reset_link}

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد الإلكتروني.

رابط إعادة تعيين كلمة المرور صالح لمدة ساعة واحدة.

مع تحيات،
فريق دلال
                '''
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني')
                    logger.info('Password reset email sent to user: %s', user.username)
                except Exception as e:
                    logger.error('Failed to send password reset email: %s', str(e))
                    messages.error(request, 'حدث خطأ في إرسال البريد الإلكتروني. يرجى المحاولة لاحقاً')
                    
                return redirect('login')
                
            except User.DoesNotExist:
                # For security, don't reveal if email exists
                messages.success(request, 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني')
                logger.info('Password reset requested for non-existent email: %s', email)
    
    return render(request, 'properties/password_reset.html')


def password_reset_confirm(request):
    """Handle password reset confirmation."""
    if request.user.is_authenticated:
        return redirect('home')
    
    user_id = request.GET.get('user_id')
    token = request.GET.get('token')
    
    if not user_id or not token:
        messages.error(request, 'رابط إعادة تعيين كلمة المرور غير صالح')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        
        # Validate token from session
        session_data = request.session.get(f'password_reset_token_{user_id}')
        if not session_data:
            messages.error(request, 'رابط إعادة تعيين كلمة المرور منتهي الصلاحية')
            return redirect('login')
        
        stored_token = session_data.get('token')
        created_at = session_data.get('created_at')
        
        if stored_token != token:
            messages.error(request, 'رابط إعادة تعيين كلمة المرور غير صالح')
            return redirect('login')
        
        # Check if token is expired (1 hour)
        from datetime import datetime, timedelta
        token_age = datetime.now() - datetime.fromisoformat(created_at)
        if token_age > timedelta(hours=1):
            messages.error(request, 'رابط إعادة تعيين كلمة المرور منتهي الصلاحية')
            return redirect('login')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not new_password or not confirm_password:
                messages.error(request, 'يرجى ملء جميع الحقول')
            elif new_password != confirm_password:
                messages.error(request, 'كلمات المرور غير متطابقة')
            elif len(new_password) < 8:
                messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
            else:
                user.set_password(new_password)
                user.save()
                
                # Clear the token
                del request.session[f'password_reset_token_{user_id}']
                
                # Log password reset
                from .models import ActivityLog
                ActivityLog.log(
                    user=user,
                    action='update',
                    model_type='user',
                    object_id=user.id,
                    object_repr=user.username,
                    description=f'إعادة تعيين كلمة المرور: {user.username}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'method': 'email_reset'}
                )
                
                messages.success(request, 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول')
                return redirect('login')
        
        return render(request, 'properties/password_reset_confirm.html', {
            'user_id': user_id,
            'token': token,
        })
        
    except User.DoesNotExist:
        messages.error(request, 'رابط إعادة تعيين كلمة المرور غير صالح')
        return redirect('login')


@login_required
def password_change(request):
    """Handle password change for logged in users with proper validation."""
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not old_password or not new_password:
            messages.error(request, 'يرجى ملء جميع الحقول')
        elif not request.user.check_password(old_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة')
        elif new_password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
        elif len(new_password) < 8:
            messages.error(request, 'كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل')
        elif old_password == new_password:
            messages.error(request, 'كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة')
        else:
            # Validate password strength
            import re
            if not re.search(r'[A-Z]', new_password):
                messages.error(request, 'كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل')
            elif not re.search(r'[a-z]', new_password):
                messages.error(request, 'كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل')
            elif not re.search(r'[0-9]', new_password):
                messages.error(request, 'كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
            else:
                request.user.set_password(new_password)
                request.user.save()
                
                # Log password change
                from .models import ActivityLog
                ActivityLog.log(
                    user=request.user,
                    action='update',
                    model_type='user',
                    object_id=request.user.id,
                    object_repr=request.user.username,
                    description=f'تغيير كلمة المرور: {request.user.username}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'method': 'self_change'}
                )
                
                messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                return redirect('user_settings')
    
    return render(request, 'properties/password_change.html')


@login_required
def account_delete(request):
    """Handle account deletion with proper confirmation and security."""
    import secrets
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirmation = request.POST.get('confirmation', '')
        
        if not password:
            messages.error(request, 'يرجى إدخال كلمة المرور للتأكيد')
        elif not request.user.check_password(password):
            messages.error(request, 'كلمة المرور غير صحيحة')
        elif confirmation != 'DELETE':
            messages.error(request, 'يرجى كتابة DELETE للتأكيد')
        else:
            # Log account deletion
            from .models import ActivityLog
            ActivityLog.log(
                user=request.user,
                action='delete',
                model_type='user',
                object_id=request.user.id,
                object_repr=request.user.username,
                description=f'حذف حساب المستخدم: {request.user.username}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            # Anonymize user data
            username = f'deleted_user_{request.user.id}_{secrets.token_hex(8)}'
            request.user.username = username
            request.user.email = f'deleted_{request.user.id}@deleted.local'
            request.user.first_name = 'Deleted'
            request.user.last_name = 'User'
            request.user.is_active = False
            request.user.save()
            
            # Logout user
            logout(request)
            
            messages.success(request, 'تم حذف حسابك بنجاح')
            return redirect('home')
    
    return render(request, 'properties/account_delete.html')


@login_required
@user_required
def user_dashboard(request):
    """لوحة تحكم المستخدمين العاديين"""
    # Get user's saved properties
    saved_properties = []
    try:
        from .models import SavedProperty
        saved_properties = SavedProperty.objects.filter(user=request.user).select_related('property', 'property__owner', 'property__broker')
    except Exception:
        saved_properties = []

    # Get user's notifications
    notifications = []
    unread_notifications_count = 0
    try:
        notifications = Notification.objects.filter(user=request.user)[:20]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        notifications = []
        unread_notifications_count = 0

    # Get auctions user has joined
    user_auctions = []
    try:
        from .models import AuctionParticipant
        user_auctions = AuctionParticipant.objects.filter(user=request.user, verified=True).select_related('auction', 'auction__property')
    except Exception:
        user_auctions = []

    # Get user's activity logs
    activity_logs = []
    try:
        activity_logs = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:20]
    except Exception:
        activity_logs = []

    return render(request, 'properties/user_dashboard.html', {
        'saved_properties': saved_properties,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'user_auctions': user_auctions,
        'activity_logs': activity_logs,
    })


@login_required
def user_dashboard_enhanced(request):
    """لوحة تحكم المستخدمين المحسنة - تجربة عصرية"""
    # Calculate statistics
    stats = {
        'saved_properties': 0,
        'saved_searches': 0,
        'viewed_properties': 0,
        'unread_notifications': 0,
        'unread_messages': 0,
        'upcoming_viewings': 0,
    }

    try:
        from .models import SavedProperty, SavedSearch, UserViewHistory, Notification, Conversation, ViewingRequest
        
        stats['saved_properties'] = SavedProperty.objects.filter(user=request.user).count()
        stats['saved_searches'] = SavedSearch.objects.filter(user=request.user).count()
        stats['viewed_properties'] = UserViewHistory.objects.filter(user=request.user).count()
        stats['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()
        stats['unread_messages'] = Conversation.objects.filter(
            participants=request.user,
            messages__recipient=request.user,
            messages__is_read=False
        ).count()
        stats['upcoming_viewings'] = ViewingRequest.objects.filter(
            user=request.user,
            status='confirmed',
            viewing_date__gte=timezone.now()
        ).count()
    except Exception as e:
        logger.error(f"Error calculating dashboard stats: {e}")
        # Use fallback values if models don't exist yet
        stats = {
            'saved_properties': 0,
            'saved_searches': 0,
            'viewed_properties': 0,
            'unread_notifications': 0,
            'unread_messages': 0,
            'upcoming_viewings': 0,
        }

    # Get recent activity
    recent_activity = []
    try:
        recent_activity = ActivityLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        recent_activity = [
            {
                'icon': '📝',
                'title': log.action,
                'description': log.description,
                'time': log.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for log in recent_activity
        ]
    except Exception as e:
        logger.error(f"Error loading recent activity: {e}")
        recent_activity = []

    return render(request, 'properties/user_dashboard_enhanced.html', {
        'stats': stats,
        'recent_activity': recent_activity,
    })


# ==================== USER DASHBOARD API ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_api(request):
    """API مخصص للوحة المستخدم المحسنة"""
    try:
        # Calculate statistics
        stats = {
            'saved_properties': 0,
            'saved_searches': 0,
            'viewed_properties': 0,
            'unread_notifications': 0,
            'unread_messages': 0,
            'upcoming_viewings': 0,
        }

        try:
            from .models import SavedProperty, SavedSearch, UserViewHistory, Notification, Conversation, ViewingRequest
            
            stats['saved_properties'] = SavedProperty.objects.filter(user=request.user).count()
            stats['saved_searches'] = SavedSearch.objects.filter(user=request.user).count()
            stats['viewed_properties'] = UserViewHistory.objects.filter(user=request.user).count()
            stats['unread_notifications'] = Notification.objects.filter(user=request.user, is_read=False).count()
            stats['unread_messages'] = Conversation.objects.filter(
                participants=request.user,
                messages__recipient=request.user,
                messages__is_read=False
            ).count()
            stats['upcoming_viewings'] = ViewingRequest.objects.filter(
                user=request.user,
                status='confirmed',
                viewing_date__gte=timezone.now()
            ).count()
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {e}")

        # Get recent activity
        recent_activity = []
        try:
            recent_activity = ActivityLog.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
            
            recent_activity = [
                {
                    'icon': '📝',
                    'title': log.action,
                    'description': log.description,
                    'time': log.created_at.strftime('%Y-%m-%d %H:%M')
                }
                for log in recent_activity
            ]
        except Exception as e:
            logger.error(f"Error loading recent activity: {e}")

        return Response({
            'stats': stats,
            'recent_activity': recent_activity
        })
    except Exception as e:
        logger.error(f"Error in user_dashboard_api: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_saved_items_api(request):
    """API للحصول على العناصر المحفوظة"""
    try:
        from .models import SavedProperty
        
        saved_properties = SavedProperty.objects.filter(
            user=request.user
        ).select_related('property').order_by('-saved_at')[:20]
        
        items = []
        for saved in saved_properties:
            try:
                items.append({
                    'id': saved.property.id,
                    'title': saved.property.title,
                    'price': str(saved.property.price) if saved.property.price else 'غير محدد',
                    'location': f"{saved.property.city}, {saved.property.governorate}" if saved.property.city else 'غير محدد',
                    'image': saved.property.main_image.url if saved.property.main_image else '/static/img/placeholder.svg',
                    'url': saved.property.get_absolute_url(),
                    'saved_at': saved.saved_at.strftime('%Y-%m-%d %H:%M')
                })
            except Exception as e:
                logger.error(f"Error processing saved property {saved.id}: {e}")
                continue
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in user_saved_items_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_saved_searches_api(request):
    """API للحصول على عمليات البحث المحفوظة"""
    try:
        from .models import SavedSearch
        
        saved_searches = SavedSearch.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        searches = []
        for search in saved_searches:
            try:
                searches.append({
                    'id': search.id,
                    'name': search.name,
                    'filters_summary': str(search.filters)[:100] if search.filters else 'فلاتر عامة',
                    'last_used': search.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'created_at': search.created_at.strftime('%Y-%m-%d')
                })
            except Exception as e:
                logger.error(f"Error processing saved search {search.id}: {e}")
                continue
        
        return Response({'searches': searches})
    except Exception as e:
        logger.error(f"Error in user_saved_searches_api: {e}")
        return Response({'searches': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_viewed_items_api(request):
    """API للحصول على العناصر المشاهدة"""
    try:
        from .models import UserViewHistory
        
        viewed_items = UserViewHistory.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        items = []
        for viewed in viewed_items:
            try:
                items.append({
                    'id': viewed.item_id,
                    'title': viewed.item_title or 'عنصر',
                    'price': 'غير محدد',
                    'location': 'غير محدد',
                    'image': viewed.item_image or '/static/img/placeholder.svg',
                    'url': f'/property/{viewed.item_id}/',
                    'viewed_at': viewed.created_at.strftime('%Y-%m-%d %H:%M')
                })
            except Exception as e:
                logger.error(f"Error processing viewed item {viewed.id}: {e}")
                continue
        
        return Response({'items': items})
    except Exception as e:
        logger.error(f"Error in user_viewed_items_api: {e}")
        return Response({'items': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_viewings_api(request):
    """API للحصول على طلبات المعاينة"""
    try:
        from .models import ViewingRequest
        
        viewings = ViewingRequest.objects.filter(
            user=request.user
        ).select_related('property').order_by('-viewing_date')[:20]
        
        items = []
        for viewing in viewings:
            try:
                items.append({
                    'id': viewing.id,
                    'property_title': viewing.property.title if viewing.property else 'عقار محذوف',
                    'property_url': viewing.property.get_absolute_url() if viewing.property else '#',
                    'date': viewing.viewing_date.strftime('%Y-%m-%d'),
                    'time': viewing.viewing_time.strftime('%H:%M'),
                    'status': viewing.status,
                    'status_display': viewing.get_status_display()
                })
            except Exception as e:
                logger.error(f"Error processing viewing {viewing.id}: {e}")
                continue
        
        return Response({'viewings': items})
    except Exception as e:
        logger.error(f"Error in user_viewings_api: {e}")
        return Response({'viewings': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookings_api(request):
    """API للحصول على الحجوزات"""
    try:
        from .models import HotelBooking
        
        bookings = HotelBooking.objects.filter(
            user=request.user
        ).select_related('hotel').order_by('-check_in')[:20]
        
        items = []
        for booking in bookings:
            try:
                items.append({
                    'id': booking.id,
                    'hotel_name': booking.hotel.name if booking.hotel else 'فندق محذوف',
                    'url': booking.hotel.get_absolute_url() if booking.hotel else '#',
                    'check_in': booking.check_in.strftime('%Y-%m-%d'),
                    'check_out': booking.check_out.strftime('%Y-%m-%d'),
                    'total_price': str(booking.total_price),
                    'status': booking.status,
                    'status_display': booking.get_status_display()
                })
            except Exception as e:
                logger.error(f"Error processing booking {booking.id}: {e}")
                continue
        
        return Response({'bookings': items})
    except Exception as e:
        logger.error(f"Error in user_bookings_api: {e}")
        return Response({'bookings': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_conversations_api(request):
    """API للحصول على المحادثات"""
    try:
        from .models import Conversation
        
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'messages').order_by('-updated_at')[:20]
        
        items = []
        for conv in conversations:
            try:
                other_user = conv.participants.exclude(id=request.user.id).first()
                last_message = conv.messages.last() if conv.messages.exists() else None
                
                items.append({
                    'id': conv.id,
                    'other_user': other_user.username if other_user else 'مستخدم محذوف',
                    'last_message': last_message.content[:100] if last_message else 'لا توجد رسائل',
                    'last_message_time': last_message.created_at.strftime('%Y-%m-%d %H:%M') if last_message else '',
                    'unread': not (last_message and last_message.is_read and last_message.sender == request.user),
                    'url': f'/messages/{conv.id}/'
                })
            except Exception as e:
                logger.error(f"Error processing conversation {conv.id}: {e}")
                continue
        
        return Response({'conversations': items})
    except Exception as e:
        logger.error(f"Error in user_conversations_api: {e}")
        return Response({'conversations': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_notifications_api(request):
    """API للحصول على الإشعارات"""
    try:
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]
        
        items = []
        for notif in notifications:
            try:
                items.append({
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message[:200],
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
                    'link': notif.link if hasattr(notif, 'link') else None
                })
            except Exception as e:
                logger.error(f"Error processing notification {notif.id}: {e}")
                continue
        
        return Response({'notifications': items})
    except Exception as e:
        logger.error(f"Error in user_notifications_api: {e}")
        return Response({'notifications': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_alerts_api(request):
    """API للحصول على التنبيهات"""
    try:
        from .models import PriceAlert, PropertyAlert
        
        price_alerts = PriceAlert.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        property_alerts = PropertyAlert.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        price_items = []
        for alert in price_alerts:
            try:
                price_items.append({
                    'id': alert.id,
                    'title': f'تنبيه سعر - {alert.location or "الكل"}',
                    'description': f'من {alert.min_price or 0} إلى {alert.max_price or "غير محدود"}',
                    'is_active': alert.is_active,
                    'created_at': alert.created_at.strftime('%Y-%m-%d')
                })
            except Exception as e:
                logger.error(f"Error processing price alert {alert.id}: {e}")
                continue
        
        property_items = []
        for alert in property_alerts:
            try:
                property_items.append({
                    'id': alert.id,
                    'title': alert.name,
                    'description': str(alert.filters)[:100] if alert.filters else 'فلاتر عامة',
                    'is_active': alert.is_active,
                    'created_at': alert.created_at.strftime('%Y-%m-%d')
                })
            except Exception as e:
                logger.error(f"Error processing property alert {alert.id}: {e}")
                continue
        
        return Response({
            'price_alerts': price_items,
            'property_alerts': property_items
        })
    except Exception as e:
        logger.error(f"Error in user_alerts_api: {e}")
        return Response({'price_alerts': [], 'property_alerts': []}, status=500)


@login_required
def user_dashboard_enhanced(request):
    """لوحة تحكم المستخدمين المحسنة - تجربة عصرية"""
    from .models import (
        SavedProperty, SavedSearch, PropertyComparison, 
        UserViewHistory, UserBehavior, SmartNotification
    )
    
    # Calculate statistics
    stats = {
        'saved_properties': 0,
        'saved_searches': 0,
        'viewed_properties': 0,
        'unread_notifications': 0,
        'unread_messages': 0,
        'upcoming_viewings': 0,
    }
    
    try:
        stats['saved_properties'] = SavedProperty.objects.filter(user=request.user).count()
    except Exception:
        pass
    
    try:
        stats['saved_searches'] = SavedSearch.objects.filter(user=request.user).count()
    except Exception:
        pass
    
    try:
        stats['viewed_properties'] = UserViewHistory.objects.filter(user=request.user).count()
    except Exception:
        pass
    
    try:
        stats['unread_notifications'] = SmartNotification.objects.filter(
            user=request.user, is_read=False
        ).count()
    except Exception:
        pass
    
    try:
        from .models import Conversation
        stats['unread_messages'] = Conversation.objects.filter(
            participants=request.user,
            messages__recipient=request.user,
            messages__is_read=False
        ).count()
    except Exception:
        pass
    
    # Get recent activity
    recent_activity = []
    try:
        recent_behaviors = UserBehavior.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        for behavior in recent_behaviors:
            recent_activity.append({
                'icon': self.get_behavior_icon(behavior.action),
                'title': self.get_behavior_title(behavior.action),
                'description': self.get_behavior_description(behavior),
                'time': behavior.created_at.isoformat()
            })
    except Exception:
        pass
    
    context = {
        'stats': stats,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'properties/user_dashboard_enhanced.html', context)


def get_behavior_icon(action):
    icons = {
        'view': '👁️',
        'save': '❤️',
        'share': '📤',
        'like': '👍',
        'comment': '💬',
        'search': '🔍',
        'filter': '⚙️',
    }
    return icons.get(action, '📝')


def get_behavior_title(action):
    titles = {
        'view': 'عرض عقار',
        'save': 'حفظ عقار',
        'share': 'مشاركة عقار',
        'like': 'إعجاب بعقار',
        'comment': 'تعليق على عقار',
        'search': 'بحث',
        'filter': 'فلترة',
    }
    return titles.get(action, 'نشاط')


def get_behavior_description(behavior):
    item_types = {
        'property': 'عقار',
        'hotel': 'فندق',
        'resort': 'منتجع',
        'job': 'وظيفة',
        'service': 'خدمة',
    }
    
    item_type = item_types.get(behavior.item_type, 'عنصر')
    return f'{item_type} #{behavior.item_id}'


@login_required
def dashboard(request):
    """لوحة تحكم الإدارة والدلال - Simple version to avoid 500 errors"""
    # Check if user is admin or broker
    if not request.user.is_superuser and not request.user.is_staff and not get_broker(request.user):
        return redirect('user_dashboard')
    
    # Simple minimal dashboard to avoid 500 errors
    try:
        broker = get_broker(request.user)
    except Exception:
        broker = None
    
    from .constants import IRAQ_GOVERNORATES
    
    return render(request, 'properties/dashboard.html', {
        'properties': [],
        'messages_list': [],
        'notes_list': [],
        'notifications_list': [],
        'auctions_list': [],
        'building_requests_list': [],
        'activity_logs': [],
        'settings_form': None,
        'property_form': None,
        'note_form': None,
        'stats': {
            'pending_notes': 0,
            'unread_notifications': 0,
            'total': 0,
            'featured': 0,
            'unread_messages': 0
        },
        'broker': broker,
        'can_manage_brokers': can_manage_brokers(request.user),
        'can_manage_settings': can_manage_site_settings(request.user),
        'managed_brokers': [],
        'brokers_stats': {},
        'total_properties_count': 0,
        'all_conversations': [],
        'all_reports': [],
        'all_users': [],
        'active_users_count': 0,
        'inactive_users_count': 0,
        'superusers_count': 0,
        'subscription_plans': [],
        'platform_stats': {},
        'pending_properties': [],
        'recent_payments': [],
        'staff_users': [],
        'backups': [],
        'support_tickets': [],
        'subscription_requests': [],
        'governorates': IRAQ_GOVERNORATES,
    })


@login_required
@broker_required
def my_posts(request):
    """صفحة منشوراتي - عرض جميع منشورات الدلال مع الوقت المتبقي ومعلومات الاشتراك"""
    try:
        from django.utils import timezone
        from .models import BrokerPlanSubscription
        from .publication_services.subscription_validation_service import SubscriptionValidationService
    except ImportError:
        messages.error(request, 'مكونات النظام غير متوفرة')
        return redirect('dashboard')
    
    try:
        broker = get_broker(request.user)
    except Exception:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # Use SubscriptionValidationService to get subscription info
    subscription_service = SubscriptionValidationService(request)
    subscription = subscription_service.get_active_subscription(broker)
    subscription_info = subscription_service.get_publication_info(subscription) if subscription else None
    
    # Get user's active subscriptions with error handling
    try:
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
    except Exception:
        active_subscriptions = []
    
    # Check if user has featured/promoted capability
    has_featured = False
    subscription_end_date = None
    
    try:
        for sub in active_subscriptions:
            if sub.is_active():
                if sub.plan.allow_featured_properties:
                    has_featured = True
                if subscription_end_date is None or sub.end_date > subscription_end_date:
                    subscription_end_date = sub.end_date
    except Exception:
        has_featured = False
        subscription_end_date = None
    
    # Get all user's properties with subscription information
    try:
        properties = Property.objects.filter(owner=request.user).select_related('subscription', 'broker')
    except Exception:
        properties = []
    
    # Count properties by status
    total_properties = properties.count()
    featured_count = properties.filter(is_featured=True).count()
    promoted_count = properties.filter(is_promoted=True).count()
    active_count = properties.filter(status='published').count()
    
    # Simple version to avoid errors - return with subscription info
    return render(request, 'properties/my_posts.html', {
        'page_obj': None,
        'has_featured': has_featured,
        'subscription_end_date': subscription_end_date,
        'total_properties': total_properties,
        'featured_count': featured_count,
        'promoted_count': promoted_count,
        'active_count': active_count,
        'subscription_info': subscription_info,
        'broker': broker,
    })


@login_required
def toggle_property_featured(request, property_id):
    """Toggle featured status of a property"""
    from django.http import JsonResponse
    
    prop = get_object_or_404(Property, pk=property_id)
    if not can_edit_property(request.user, prop):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية تعديل هذا العقار'})
    
    # Check if user has featured capability
    broker = get_broker(request.user)
    if broker:
        from .models import BrokerPlanSubscription
        has_featured = False
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        for sub in active_subscriptions:
            if sub.is_active() and sub.plan.allow_featured_properties:
                has_featured = True
                break
        
        if not has_featured:
            return JsonResponse({'success': False, 'error': 'اشتراكك لا يسمح بتمييز العقارات'})
    
    is_featured = request.POST.get('is_featured', 'true').lower() == 'true'
    prop.is_featured = is_featured
    prop.save()
    
    return JsonResponse({'success': True, 'is_featured': is_featured})


@login_required
def toggle_property_promoted(request, property_id):
    """Toggle promoted status of a property"""
    from django.http import JsonResponse
    
    prop = get_object_or_404(Property, pk=property_id)
    if not can_edit_property(request.user, prop):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية تعديل هذا العقار'})
    
    # Check if user has promoted capability
    broker = get_broker(request.user)
    if broker:
        from .models import BrokerPlanSubscription
        has_promoted = False
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        for sub in active_subscriptions:
            if sub.is_active() and sub.plan.allow_promoted_properties:
                has_promoted = True
                break
        
        if not has_promoted:
            return JsonResponse({'success': False, 'error': 'اشتراكك لا يسمح بتمويل العقارات'})
    
    is_promoted = request.POST.get('is_promoted', 'true').lower() == 'true'
    prop.is_promoted = is_promoted
    prop.save()
    
    return JsonResponse({'success': True, 'is_promoted': is_promoted})


@login_required
def advanced_reports(request):
    """صفحة التقارير المتقدمة"""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Sum, Avg
    
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية الوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date() - timedelta(days=30)
    
    if end_date:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
    
    # Calculate stats
    total_properties = Property.objects.filter(
        created_at__range=[start_date, end_date]
    ).count()
    
    total_users = User.objects.filter(
        date_joined__range=[start_date, end_date]
    ).count()
    
    # Generate detailed data
    detailed_data = []
    current_date = start_date
    while current_date <= end_date:
        day_properties = Property.objects.filter(
            created_at__date=current_date
        ).count()
        
        day_users = User.objects.filter(
            date_joined__date=current_date
        ).count()
        
        detailed_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'new_properties': day_properties,
            'new_users': day_users,
            'revenue': day_properties * 10000,  # Mock revenue
            'sales': int(day_properties * 0.3),  # Mock sales
            'conversion_rate': 15.5  # Mock conversion rate
        })
        
        current_date += timedelta(days=1)
    
    return render(request, 'properties/advanced_reports.html', {
        'total_properties': total_properties,
        'total_users': total_users,
        'total_revenue': total_properties * 10000,
        'conversion_rate': 15.5,
        'monthly_growth': 12.5,
        'user_growth': 8.3,
        'revenue_growth': 15.2,
        'conversion_growth': 5.8,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'detailed_data': detailed_data,
    })


@login_required
@staff_required
@require_POST
def update_site_settings(request):
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    form = SiteSettingsForm(request.POST, instance=settings)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ إعدادات الموقع')
    else:
        messages.error(request, 'تحقق من الحقول المدخلة')
    return redirect('dashboard')


@login_required
@staff_required
def settings_general(request):
    """General settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    
    settings = SiteSettings.get_solo()
    
    if request.method == 'POST':
        try:
            # Basic site information
            settings.site_name = request.POST.get('site_name', 'دلال')
            settings.tagline = request.POST.get('tagline', '')
            settings.site_description = request.POST.get('site_description', '')
            
            # File uploads with validation
            if 'favicon' in request.FILES:
                favicon = request.FILES['favicon']
                if favicon.size > 1024 * 1024:  # 1MB limit
                    messages.error(request, 'حجم الأيقونة يجب أن يكون أقل من 1MB')
                else:
                    settings.favicon = favicon
            
            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                if logo.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, 'حجم الشعار يجب أن يكون أقل من 5MB')
                else:
                    settings.logo = logo
            
            # Contact information with validation
            contact_email = request.POST.get('contact_email', '').strip()
            if contact_email:
                from django.core.validators import validate_email
                try:
                    validate_email(contact_email)
                    settings.contact_email = contact_email
                except:
                    messages.error(request, 'البريد الإلكتروني غير صالح')
            else:
                settings.contact_email = ''
            
            settings.contact_phone = request.POST.get('contact_phone', '').strip()
            settings.contact_address = request.POST.get('contact_address', '').strip()
            settings.contact_city = request.POST.get('contact_city', '').strip()
            settings.contact_country = request.POST.get('contact_country', '').strip()
            
            # Social media with URL validation
            social_fields = {
                'facebook_url': request.POST.get('facebook_url', ''),
                'twitter_url': request.POST.get('twitter_url', ''),
                'instagram_url': request.POST.get('instagram_url', ''),
                'linkedin_url': request.POST.get('linkedin_url', ''),
                'telegram_url': request.POST.get('telegram_url', ''),
                'tiktok_url': request.POST.get('tiktok_url', ''),
                'youtube_url': request.POST.get('youtube_url', ''),
                'snapchat_url': request.POST.get('snapchat_url', '')
            }
            
            from django.core.validators import URLValidator
            url_validator = URLValidator()
            
            for field, value in social_fields.items():
                if value.strip():
                    try:
                        url_validator(value.strip())
                        setattr(settings, field, value.strip())
                    except:
                        messages.warning(request, f'رابط {field} غير صالح، تم تجاهله')
                        setattr(settings, field, '')
                else:
                    setattr(settings, field, '')
            
            # Locale settings
            settings.default_language = request.POST.get('default_language', 'ar')
            settings.timezone = request.POST.get('timezone', 'Asia/Baghdad')
            settings.date_format = request.POST.get('date_format', 'Y-m-d')
            settings.time_format = request.POST.get('time_format', 'H:i')
            
            # Advanced settings
            settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            settings.maintenance_message = request.POST.get('maintenance_message', '')
            settings.allow_registration = request.POST.get('allow_registration') == 'on'
            settings.require_email_verification = request.POST.get('require_email_verification') == 'on'
            
            settings.save()
            
            # Log the action
            from .models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='تحديث الإعدادات العامة',
                details=f'تم تحديث إعدادات الموقع بواسطة {request.user.username}'
            )
            
            messages.success(request, 'تم تحديث الإعدادات العامة بنجاح')
            return redirect('settings_general')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الإعدادات: {str(e)}')
    
    return render(request, 'properties/settings_general.html', {'settings': settings, 'section': 'general'})


@login_required
@staff_required
def settings_maintenance(request):
    """Maintenance mode settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    
    settings = SiteSettings.get_solo()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_maintenance':
            old_status = settings.maintenance_mode
            settings.maintenance_mode = not settings.maintenance_mode
            settings.save()
            
            # Log the action
            from .models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action=f"تغيير وضع الصيانة من {'مفعل' if old_status else 'معطل'} إلى {'مفعل' if settings.maintenance_mode else 'معطل'}",
                details=f"تم تغيير وضع الصيانة بواسطة {request.user.username}"
            )
            
            status_text = 'تفعيل' if settings.maintenance_mode else 'إلغاء'
            messages.success(request, f'تم {status_text} وضع الصيانة بنجاح')
            
        elif action == 'update_message':
            settings.maintenance_message = request.POST.get('maintenance_message', settings.maintenance_message)
            settings.maintenance_end_time = request.POST.get('maintenance_end_time') or None
            settings.allow_admins_during_maintenance = request.POST.get('allow_admins_during_maintenance') == 'on'
            settings.save()
            messages.success(request, 'تم تحديث إعدادات الصيانة بنجاح')
        
        return redirect('settings_maintenance')
    
    return render(request, 'properties/settings_maintenance.html', {'settings': settings, 'section': 'maintenance'})


@login_required
@staff_required
def admin_channels_list(request):
    """Admin view to manage all broker channels."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    channels = BrokerChannel.objects.all().select_related('broker', 'broker__user')
    
    if status_filter != 'all':
        channels = channels.filter(status=status_filter)
    
    if search_query:
        channels = channels.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(broker__display_name__icontains=search_query) |
            Q(broker__user__username__icontains=search_query)
        )
    
    channels = channels.order_by('-created_at')
    
    return render(request, 'properties/admin_channels_list.html', {
        'channels': channels,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@login_required
@staff_required
def admin_channel_approve(request, channel_id):
    """Approve a broker channel."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = 'active'
    channel.save()
    
    messages.success(request, f'تم تفعيل قناة {channel.name} بنجاح')
    return redirect('admin_channels_list')


@login_required
@staff_required
def admin_channel_reject(request, channel_id):
    """Reject/suspend a broker channel."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = 'suspended'
    channel.save()
    
    messages.success(request, f'تم إيقاف قناة {channel.name}')
    return redirect('admin_channels_list')


@login_required
@staff_required
def admin_channel_verify(request, channel_id):
    """Verify a broker channel."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.is_verified = True
    channel.save()
    
    messages.success(request, f'تم توثيق قناة {channel.name}')
    return redirect('admin_channels_list')


@login_required
@staff_required
def admin_channel_delete(request, channel_id):
    """Delete a broker channel."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel_name = channel.name
    channel.delete()
    
    messages.success(request, f'تم حذف قناة {channel_name}')
    return redirect('admin_channels_list')


@login_required
@staff_required
def admin_channel_activate(request, channel_id):
    """Activate a suspended broker channel."""
    from .models import BrokerChannel
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = 'active'
    channel.save()
    
    messages.success(request, f'تم تفعيل قناة {channel.name}')
    return redirect('admin_channels_list')


@login_required
@staff_required
def admin_channel_properties(request, channel_id):
    """View and manage properties in a broker channel."""
    from .models import BrokerChannel, Property
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    properties = Property.objects.filter(broker=channel.broker).select_related('owner', 'broker')
    
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        properties = properties.filter(status=status_filter)
    
    properties = properties.order_by('-created_at')
    
    return render(request, 'properties/admin_channel_properties.html', {
        'channel': channel,
        'properties': properties,
        'status_filter': status_filter,
    })


@login_required
@staff_required
def admin_channel_property_delete(request, channel_id, property_id):
    """Delete a property from a broker channel."""
    from .models import BrokerChannel, Property
    
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    property = get_object_or_404(Property, id=property_id, broker=channel.broker)
    
    property_title = property.title
    property.delete()
    
    # Update channel stats
    channel.update_stats()
    
    messages.success(request, f'تم حذف عقار {property_title}')
    return redirect('admin_channel_properties', channel_id=channel.id)


@login_required
def my_channel_view(request):
    """View for broker's own channel management."""
    from .models import BrokerChannel, Broker, ChannelPost, ChannelVideo, ChannelFollow, Message
    
    broker = get_broker(request.user)
    
    if not broker:
        messages.error(request, 'ليس لديك قناة')
        return redirect('dashboard')
    
    # Get or create channel
    channel, created = BrokerChannel.objects.get_or_create(
        broker=broker,
        defaults={
            'name': f'قناة {broker.display_name}',
            'description': f'قناة الدلال {broker.display_name}',
            'status': 'active',
            'category': 'properties_iraq',
            'channel_type': 'basic'
        }
    )
    
    # Update existing channel to active if it was pending
    if not created and channel.status == 'pending':
        channel.status = 'active'
        channel.category = 'properties_iraq'
        channel.channel_type = 'basic'
        channel.save()
    
    # Get channel properties first
    properties = Property.objects.filter(broker=broker).select_related('owner', 'broker')
    
    # Update channel stats with real data
    channel.properties_count = properties.count()
    channel.save()
    
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        properties = properties.filter(status=status_filter)
    
    properties = properties.order_by('-created_at')
    
    # Get channel posts and videos
    posts = ChannelPost.objects.filter(channel=channel).order_by('-is_pinned', '-created_at')
    videos = ChannelVideo.objects.filter(channel=channel).order_by('-is_featured', '-created_at')
    
    # Get last activity items
    last_property = properties.first() if properties.exists() else None
    last_post = posts.first() if posts.exists() else None
    
    # Get last message (if Message model exists)
    try:
        last_message = Message.objects.filter(channel=channel).order_by('-created_at').first()
    except:
        last_message = None
    
    # Get last follower
    try:
        last_follower = ChannelFollow.objects.filter(channel=channel).order_by('-created_at').first()
    except:
        last_follower = None
    
    return render(request, 'properties/my_channel.html', {
        'channel': channel,
        'properties': properties,
        'posts': posts,
        'videos': videos,
        'status_filter': status_filter,
        'broker': broker,
        'last_property': last_property,
        'last_post': last_post,
        'last_message': last_message,
        'last_follower': last_follower,
    })


@login_required
def update_channel_media(request):
    """Update channel cover and logo images."""
    from .models import BrokerChannel, Broker
    
    broker = get_broker(request.user)
    
    if not broker:
        messages.error(request, 'ليس لديك قناة')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, broker=broker)
    
    if request.method == 'POST':
        cover_image = request.FILES.get('cover_image')
        logo = request.FILES.get('logo')
        
        if cover_image:
            channel.cover_image = cover_image
        
        if logo:
            channel.logo = logo
        
        channel.save()
        messages.success(request, 'تم تحديث صور القناة بنجاح')
        return redirect('my_channel')
    
    return render(request, 'properties/update_channel_media.html', {
        'channel': channel,
    })


@login_required
def channel_update_media_api(request):
    """API endpoint for updating channel media via AJAX."""
    from .models import BrokerChannel, Broker
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    broker = get_broker(request.user)
    
    if not broker:
        return JsonResponse({'success': False, 'error': 'ليس لديك قناة'})
    
    channel = get_object_or_404(BrokerChannel, broker=broker)
    
    cover_image = request.FILES.get('cover_image')
    logo = request.FILES.get('logo')
    
    if cover_image:
        channel.cover_image = cover_image
    
    if logo:
        channel.logo = logo
    
    channel.save()
    
    return JsonResponse({'success': True, 'message': 'تم تحديث الصورة بنجاح'})


@login_required
def create_channel_post(request):
    """Create a new post in the channel."""
    from .models import BrokerChannel, Broker, ChannelPost, Property
    
    broker = get_broker(request.user)
    
    if not broker:
        messages.error(request, 'ليس لديك قناة')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, broker=broker)
    
    if request.method == 'POST':
        post_type = request.POST.get('post_type', 'text')
        content = request.POST.get('content', '')
        property_id = request.POST.get('property_id')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        is_pinned = request.POST.get('is_pinned') == 'on'
        is_advertisement = request.POST.get('is_advertisement') == 'on'
        
        post = ChannelPost.objects.create(
            channel=channel,
            post_type=post_type,
            content=content,
            image=image,
            video=video,
            is_pinned=is_pinned,
            is_advertisement=is_advertisement
        )
        
        if property_id:
            try:
                property = Property.objects.get(id=property_id, broker=broker)
                post.property = property
                post.save()
            except Property.DoesNotExist:
                pass
        
        # Notify followers
        from .utils import create_notification
        followers = channel.followers.all()
        for follower in followers:
            create_notification(
                user=follower.user,
                notification_type='channel_post',
                title='منشور جديد في قناة متابعتك',
                message=f'نشر {broker.display_name} منشوراً جديداً',
                link=f'/channel/{channel.id}/'
            )
        
        messages.success(request, 'تم نشر المنشور بنجاح')
        return redirect('my_channel')
    
    # Get broker's properties for selection
    broker_properties = Property.objects.filter(broker=broker, status__in=PUBLIC_STATUSES)
    
    return render(request, 'properties/create_channel_post.html', {
        'channel': channel,
        'broker_properties': broker_properties,
    })


@login_required
def create_channel_video(request):
    """Create a new short video in the channel."""
    from .models import BrokerChannel, Broker, ChannelVideo
    
    broker = get_broker(request.user)
    
    if not broker:
        messages.error(request, 'ليس لديك قناة')
        return redirect('dashboard')
    
    channel = get_object_or_404(BrokerChannel, broker=broker)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        video_file = request.FILES.get('video_file')
        thumbnail = request.FILES.get('thumbnail')
        duration = request.POST.get('duration', 0)
        is_featured = request.POST.get('is_featured') == 'on'
        tags = request.POST.get('tags', '')
        
        video = ChannelVideo.objects.create(
            channel=channel,
            title=title,
            description=description,
            video_file=video_file,
            thumbnail=thumbnail,
            duration=int(duration),
            is_featured=is_featured,
            tags=tags
        )
        
        # Notify followers
        from .utils import create_notification
        followers = channel.followers.all()
        for follower in followers:
            create_notification(
                user=follower.user,
                notification_type='channel_video',
                title='فيديو جديد في قناة متابعتك',
                message=f'رفع {broker.display_name} فيديو جديداً',
                link=f'/channel/{channel.id}/videos/'
            )
        
        messages.success(request, 'تم رفع الفيديو بنجاح')
        return redirect('my_channel')
    
    return render(request, 'properties/create_channel_video.html', {
        'channel': channel,
    })


@login_required
def toggle_post_like(request, post_id):
    """Toggle like on a channel post."""
    from .models import ChannelPost, ChannelPostLike
    
    post = get_object_or_404(ChannelPost, id=post_id)
    like, created = ChannelPostLike.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        post.likes_count -= 1
        post.save(update_fields=['likes_count'])
        return JsonResponse({'liked': False, 'likes_count': post.likes_count})
    else:
        post.likes_count += 1
        post.save(update_fields=['likes_count'])
        
        # Notify post author
        if post.channel.broker.user != request.user:
            from .utils import create_notification
            create_notification(
                user=post.channel.broker.user,
                notification_type='post_like',
                title='إعجاب جديد على منشورك',
                message=f'أعجب {request.user.get_full_name() or request.user.username} بمنشورك',
                link=f'/channel/{post.channel.id}/'
            )
        
        return JsonResponse({'liked': True, 'likes_count': post.likes_count})


@login_required
def toggle_video_like(request, video_id):
    """Toggle like on a channel video."""
    from .models import ChannelVideo, ChannelVideoLike
    
    video = get_object_or_404(ChannelVideo, id=video_id)
    like, created = ChannelVideoLike.objects.get_or_create(
        user=request.user,
        video=video
    )
    
    if not created:
        like.delete()
        video.likes_count -= 1
        video.save(update_fields=['likes_count'])
        return JsonResponse({'liked': False, 'likes_count': video.likes_count})
    else:
        video.likes_count += 1
        video.save(update_fields=['likes_count'])
        
        # Notify video author
        if video.channel.broker.user != request.user:
            from .utils import create_notification
            create_notification(
                user=video.channel.broker.user,
                notification_type='video_like',
                title='إعجاب جديد على فيديوك',
                message=f'أعجب {request.user.get_full_name() or request.user.username} بفيديوك',
                link=f'/channel/{video.channel.id}/videos/'
            )
        
        return JsonResponse({'liked': True, 'likes_count': video.likes_count})


@login_required
def channel_public_view(request, channel_id):
    """Public view of a broker's channel for users."""
    from .models import BrokerChannel, ChannelPost, ChannelVideo, Property, Auction, Hotel, Resort, ChannelReview, ChannelFollow
    
    channel = get_object_or_404(BrokerChannel, id=channel_id, status='active')
    
    # Check if user is following
    is_following = False
    if request.user.is_authenticated:
        is_following = ChannelFollow.objects.filter(
            user=request.user,
            channel=channel
        ).exists()
    
    # Get filter parameters
    tab = request.GET.get('tab', 'home')
    property_type = request.GET.get('type', 'all')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('q', '')
    
    # Get properties
    properties = Property.objects.filter(broker=channel.broker)
    
    # Apply filters
    if property_type == 'sale':
        properties = properties.filter(status__in=PUBLIC_STATUSES)
    elif property_type == 'rent':
        properties = properties.filter(status='rent')
    elif property_type == 'auction':
        properties = properties.filter(status='auction')
    
    # Apply search
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'newest':
        properties = properties.order_by('-created_at')
    elif sort_by == 'price_high':
        properties = properties.order_by('-price')
    elif sort_by == 'price_low':
        properties = properties.order_by('price')
    elif sort_by == 'most_viewed':
        properties = properties.order_by('-views_count')
    
    # Get posts and videos
    posts = ChannelPost.objects.filter(channel=channel, is_published=True).order_by('-is_pinned', '-created_at')
    videos = ChannelVideo.objects.filter(channel=channel, is_published=True).order_by('-is_featured', '-created_at')
    
    # Get auctions
    auctions = Auction.objects.filter(broker=channel.broker, approval_status='approved').order_by('-created_at')
    
    # Get hotels and resorts
    hotels = Hotel.objects.filter(broker=channel.broker, is_published=True).order_by('-created_at')
    resorts = Resort.objects.filter(broker=channel.broker, is_published=True).order_by('-created_at')
    
    # Get reviews
    reviews = ChannelReview.objects.filter(channel=channel).order_by('-created_at')
    
    # Calculate real stats
    properties_count = Property.objects.filter(broker=channel.broker).count()
    posts_count = ChannelPost.objects.filter(channel=channel, is_published=True).count()
    auctions_count = Auction.objects.filter(broker=channel.broker, approval_status='approved').count()
    hotels_count = Hotel.objects.filter(broker=channel.broker, is_published=True).count()
    resorts_count = Resort.objects.filter(broker=channel.broker, is_published=True).count()
    
    # Update channel stats
    channel.properties_count = properties_count
    channel.save(update_fields=['properties_count'])
    
    # Increment channel views
    channel.increment_views()
    
    context = {
        'channel': channel,
        'posts': posts,
        'videos': videos,
        'properties': properties,
        'auctions': auctions,
        'hotels': hotels,
        'resorts': resorts,
        'reviews': reviews,
        'is_following': is_following,
        'tab': tab,
        'property_type': property_type,
        'sort_by': sort_by,
        'search_query': search_query,
        'properties_count': properties_count,
        'posts_count': posts_count,
        'auctions_count': auctions_count,
        'hotels_count': hotels_count,
        'resorts_count': resorts_count,
    }
    
    return render(request, 'properties/channel_public.html', context)


@login_required
@staff_required
def user_details_api(request, user_id):
    """API endpoint to get user details for modal."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get user activities
        activities = []
        try:
            from .models import ActivityLog
            user_activities = ActivityLog.objects.filter(user=user).order_by('-created_at')[:10]
            for activity in user_activities:
                activities.append({
                    'action': activity.action,
                    'date': activity.created_at.strftime('%Y-%m-%d %H:%M'),
                    'ip': activity.ip_address or '--'
                })
        except Exception:
            pass
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'avatar': None,  # Add avatar field if exists
            'password': '••••••••',  # Never send real password
            'conversations_count': user.conversationparticipant_set.count(),
            'messages_count': 0,  # Add if message model exists
            'reports_count': user.messagereport_reporter.count(),
            'properties_count': 0,  # Add if property relation exists
            'activities': activities
        }
        
        return JsonResponse({'success': True, 'user': user_data})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المستخدم غير موجود'}, status=404)
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
def toggle_user_status_api(request, user_id):
    """API endpoint to toggle user status."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'المستخدم غير موجود'}, status=404)
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
def subscription_plan_details_api(request, plan_id):
    """API endpoint to get subscription plan details."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        from .models import SubscriptionPlan
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        plan_data = {
            'id': plan.id,
            'name': plan.name,
            'period': plan.period,
            'ads_limit': plan.ads_limit,
            'price': str(plan.price),
            'price_per_property': str(plan.price_per_property),
            'color': plan.color,
            'is_active': plan.is_active,
            'subscribers_count': plan.broker_set.count()
        }
        
        return JsonResponse({'success': True, 'plan': plan_data})
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الخطة غير موجودة'}, status=404)
    except Exception as e:
        logger.error(f"Error getting plan details: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
@require_POST
def subscription_plan_create_api(request):
    """API endpoint to create subscription plan."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        from .models import SubscriptionPlan
        data = json.loads(request.body)
        
        # Validate required fields
        name = data.get('name', '').strip()
        period = data.get('period', '').strip()
        ads_limit = data.get('ads_limit')
        price = data.get('price', 0)
        price_per_property = data.get('price_per_property', 50.00)
        color = data.get('color', '#FF6B35').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': 'اسم الخطة مطلوب'}, status=400)
        if not period:
            return JsonResponse({'success': False, 'error': 'فترة الاشتراك مطلوبة'}, status=400)
        if ads_limit is None or ads_limit < 0:
            return JsonResponse({'success': False, 'error': 'حد الإعلانات يجب أن يكون رقماً موجباً'}, status=400)
        
        try:
            ads_limit = int(ads_limit)
            price = float(price)
            price_per_property = float(price_per_property)
            if price < 0 or price_per_property < 0:
                return JsonResponse({'success': False, 'error': 'السعر يجب أن يكون رقماً موجباً'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'قيم غير صحيحة'}, status=400)
        
        plan = SubscriptionPlan.objects.create(
            name=name,
            period=period,
            ads_limit=ads_limit,
            price=price,
            price_per_property=price_per_property,
            color=color,
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({'success': True, 'plan_id': plan.id})
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
@require_POST
def subscription_plan_update_api(request, plan_id):
    """API endpoint to update subscription plan."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        from .models import SubscriptionPlan
        plan = SubscriptionPlan.objects.get(id=plan_id)
        data = json.loads(request.body)
        
        # Validate and update fields
        name = data.get('name', '').strip()
        period = data.get('period', '').strip()
        ads_limit = data.get('ads_limit')
        price = data.get('price')
        price_per_property = data.get('price_per_property')
        color = data.get('color', '').strip()
        is_active = data.get('is_active')
        
        if name:
            plan.name = name
        if period:
            plan.period = period
        if ads_limit is not None:
            try:
                ads_limit = int(ads_limit)
                if ads_limit < 0:
                    return JsonResponse({'success': False, 'error': 'حد الإعلانات يجب أن يكون رقماً موجباً'}, status=400)
                plan.ads_limit = ads_limit
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'قيمة غير صحيحة لحد الإعلانات'}, status=400)
        if price is not None:
            try:
                price = float(price)
                if price < 0:
                    return JsonResponse({'success': False, 'error': 'السعر يجب أن يكون رقماً موجباً'}, status=400)
                plan.price = price
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'قيمة غير صحيحة للسعر'}, status=400)
        if price_per_property is not None:
            try:
                price_per_property = float(price_per_property)
                if price_per_property < 0:
                    return JsonResponse({'success': False, 'error': 'سعر العقار يجب أن يكون رقماً موجباً'}, status=400)
                plan.price_per_property = price_per_property
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'قيمة غير صحيحة لسعر العقار'}, status=400)
        if color:
            plan.color = color
        if is_active is not None:
            plan.is_active = bool(is_active)
        
        plan.save()
        
        return JsonResponse({'success': True})
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الخطة غير موجودة'}, status=404)
    except Exception as e:
        logger.error(f"Error updating plan: {e}")
        return JsonResponse({'success': False, 'error': 'حدث خطأ أثناء تحديث الخطة'}, status=500)


@login_required
@staff_required
@require_POST
def subscription_plan_toggle_status_api(request, plan_id):
    """API endpoint to toggle subscription plan status."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        from .models import SubscriptionPlan
        plan = SubscriptionPlan.objects.get(id=plan_id)
        plan.is_active = not plan.is_active
        plan.save()
        return JsonResponse({'success': True})
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الخطة غير موجودة'}, status=404)
    except Exception as e:
        logger.error(f"Error toggling plan status: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
@require_POST
def subscription_request_approve_api(request, request_id):
    """API endpoint to approve subscription request."""
    from .permissions import is_platform_admin

    if not (request.user.is_superuser or request.user.is_staff or is_platform_admin(request.user)):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)

    try:
        from .models import SubscriptionRequest
        sub_request = SubscriptionRequest.objects.select_related(
            'broker', 'broker__user', 'requested_plan'
        ).get(id=request_id)

        if sub_request.status == SubscriptionRequest.STATUS_APPROVED:
            return JsonResponse({'success': True, 'message': 'الطلب موافق عليه مسبقاً'})

        if not sub_request.broker:
            return JsonResponse({'success': False, 'error': 'الطلب غير مرتبط بدلال'}, status=400)

        sub_request.approve(request.user)
        return JsonResponse({'success': True})
    except SubscriptionRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الطلب غير موجود'}, status=404)
    except ValueError as e:
        logger.error(f"Error approving request (validation): {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception(f"Error approving request: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@staff_required
@require_POST
def subscription_request_reject_api(request, request_id):
    """API endpoint to reject subscription request."""
    from .permissions import is_platform_admin

    if not (request.user.is_superuser or request.user.is_staff or is_platform_admin(request.user)):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)

    try:
        from .models import SubscriptionRequest
        sub_request = SubscriptionRequest.objects.get(id=request_id)
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}
        notes = data.get('notes', '')
        sub_request.reject(request.user, notes)
        return JsonResponse({'success': True})
    except SubscriptionRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'الطلب غير موجود'}, status=404)
    except Exception as e:
        logger.exception(f"Error rejecting request: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def subscription_request_create_api(request):
    """API endpoint for users to create subscription requests."""
    try:
        from .models import SubscriptionRequest, Broker, SubscriptionPlan
        data = json.loads(request.body)
        
        # Check if user has a broker profile
        broker = get_broker(request.user)
        if not broker:
            return JsonResponse({'success': False, 'error': 'ليس لديك ملف دلال'}, status=400)
        
        # Validate input data
        plan_id = data.get('plan_id')
        custom_plan_name = data.get('custom_plan_name', '').strip()
        custom_price = data.get('custom_price')
        custom_duration = data.get('custom_duration', '').strip()
        custom_properties_limit = data.get('custom_properties_limit')
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not plan_id and not custom_plan_name:
            return JsonResponse({'success': False, 'error': 'يجب اختيار خطة أو تحديد خطة مخصصة'}, status=400)
        
        # Get requested plan if provided
        requested_plan = None
        if plan_id:
            try:
                requested_plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'الخطة المختارة غير موجودة'}, status=400)
        
        # Validate custom plan data
        if custom_plan_name:
            if not custom_price or not custom_duration or not custom_properties_limit:
                return JsonResponse({'success': False, 'error': 'الخطة المخصصة يجب أن تحتوي على السعر والمدة وعدد العقارات'}, status=400)
            
            try:
                custom_price = float(custom_price)
                custom_properties_limit = int(custom_properties_limit)
                if custom_price < 0 or custom_properties_limit < 0:
                    return JsonResponse({'success': False, 'error': 'السعر وعدد العقارات يجب أن يكونا أرقاماً موجبة'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'قيم غير صحيحة للسعر أو عدد العقارات'}, status=400)
        
        # Check if there's already a pending request
        existing_request = SubscriptionRequest.objects.filter(
            broker=broker,
            status=SubscriptionRequest.STATUS_PENDING
        ).first()
        
        if existing_request:
            return JsonResponse({'success': False, 'error': 'لديك طلب قيد الانتظار بالفعل'}, status=400)
        
        # Create request
        sub_request = SubscriptionRequest.objects.create(
            broker=broker,
            requested_plan=requested_plan,
            custom_plan_name=custom_plan_name,
            custom_price=custom_price,
            custom_duration=custom_duration,
            custom_properties_limit=custom_properties_limit,
            message=message,
            status=SubscriptionRequest.STATUS_PENDING
        )
        
        return JsonResponse({'success': True, 'request_id': sub_request.id})
    except Exception as e:
        logger.error(f"Error creating subscription request: {e}")
        return JsonResponse({'success': False, 'error': 'حدث خطأ أثناء إنشاء الطلب'}, status=500)


@login_required
@staff_required
def settings_theme(request):
    """Theme settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.theme_mode = request.POST.get('theme_mode', 'light')
        settings.primary_color = request.POST.get('primary_color', '#0d9488')
        settings.secondary_color = request.POST.get('secondary_color', '#f97316')
        settings.font_family = request.POST.get('font_family', 'Cairo')
        settings.font_size = int(request.POST.get('font_size', 16))
        settings.button_style = request.POST.get('button_style', 'rounded')
        settings.layout_style = request.POST.get('layout_style', 'boxed')
        settings.save()
        messages.success(request, 'تم تحديث إعدادات المظهر بنجاح')
        return redirect('settings_theme')
    
    return render(request, 'properties/settings_theme.html', {'settings': settings, 'section': 'theme'})


@login_required
@staff_required
def settings_homepage(request):
    """Homepage settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.hero_banner_title = request.POST.get('hero_banner_title', '')
        settings.hero_banner_subtitle = request.POST.get('hero_banner_subtitle', '')
        settings.show_featured_properties = request.POST.get('show_featured_properties') == 'on'
        settings.show_latest_properties = request.POST.get('show_latest_properties') == 'on'
        settings.show_brokers_section = request.POST.get('show_brokers_section') == 'on'
        settings.featured_properties_count = int(request.POST.get('featured_properties_count', 6))
        settings.latest_properties_count = int(request.POST.get('latest_properties_count', 12))
        if 'hero_banner_image' in request.FILES:
            settings.hero_banner_image = request.FILES['hero_banner_image']
        settings.save()
        messages.success(request, 'تم تحديث إعدادات الصفحة الرئيسية بنجاح')
        return redirect('settings_homepage')
    
    return render(request, 'properties/settings_homepage.html', {'settings': settings, 'section': 'homepage'})


@login_required
@staff_required
def settings_users(request):
    """User and permissions settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.allow_registration = request.POST.get('allow_registration') == 'on'
        settings.require_email_verification = request.POST.get('require_email_verification') == 'on'
        settings.require_phone_verification = request.POST.get('require_phone_verification') == 'on'
        settings.auto_activate_accounts = request.POST.get('auto_activate_accounts') == 'on'
        settings.default_user_role = request.POST.get('default_user_role', 'user')
        settings.save()
        messages.success(request, 'تم تحديث إعدادات المستخدمين بنجاح')
        return redirect('settings_users')
    
    return render(request, 'properties/settings_users.html', {'settings': settings, 'section': 'users'})


@login_required
@staff_required
def settings_properties(request):
    """Property settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.default_currency = request.POST.get('default_currency', 'IQD')
        settings.area_unit = request.POST.get('area_unit', 'm2')
        settings.max_images_per_property = int(request.POST.get('max_images_per_property', 20))
        settings.allow_video_upload = request.POST.get('allow_video_upload') == 'on'
        settings.allow_virtual_tours = request.POST.get('allow_virtual_tours') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات العقارات بنجاح')
        return redirect('settings_properties')
    
    return render(request, 'properties/settings_properties.html', {'settings': settings, 'section': 'properties'})


@login_required
@staff_required
def settings_media(request):
    """Media settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.max_image_size = int(request.POST.get('max_image_size', 5242880))
        settings.allowed_image_types = request.POST.get('allowed_image_types', 'jpg,jpeg,png,webp')
        settings.max_video_size = int(request.POST.get('max_video_size', 52428800))
        settings.allowed_video_types = request.POST.get('allowed_video_types', 'mp4,webm')
        settings.save()
        messages.success(request, 'تم تحديث إعدادات الوسائط بنجاح')
        return redirect('settings_media')
    
    return render(request, 'properties/settings_media.html', {'settings': settings, 'section': 'media'})


@login_required
@staff_required
def settings_notifications(request):
    """Notification settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.enable_site_notifications = request.POST.get('enable_site_notifications') == 'on'
        settings.enable_email_notifications = request.POST.get('enable_email_notifications') == 'on'
        settings.enable_sms_notifications = request.POST.get('enable_sms_notifications') == 'on'
        settings.enable_push_notifications = request.POST.get('enable_push_notifications') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات الإشعارات بنجاح')
        return redirect('settings_notifications')
    
    return render(request, 'properties/settings_notifications.html', {'settings': settings, 'section': 'notifications'})


@login_required
@staff_required
def settings_payments(request):
    """Payment settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.payment_methods = request.POST.get('payment_methods', 'cash,bank_transfer')
        settings.enable_subscriptions = request.POST.get('enable_subscriptions') == 'on'
        settings.subscription_price_monthly = Decimal(request.POST.get('subscription_price_monthly', 0))
        settings.subscription_price_yearly = Decimal(request.POST.get('subscription_price_yearly', 0))
        settings.enable_invoices = request.POST.get('enable_invoices') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات المدفوعات بنجاح')
        return redirect('settings_payments')
    
    return render(request, 'properties/settings_payments.html', {'settings': settings, 'section': 'payments'})


@login_required
@staff_required
def settings_security(request):
    """Security settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.enable_two_factor = request.POST.get('enable_two_factor') == 'on'
        settings.password_min_length = int(request.POST.get('password_min_length', 8))
        settings.require_special_chars = request.POST.get('require_special_chars') == 'on'
        settings.session_timeout = int(request.POST.get('session_timeout', 3600))
        settings.log_login_attempts = request.POST.get('log_login_attempts') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات الأمان بنجاح')
        return redirect('settings_security')
    
    return render(request, 'properties/settings_security.html', {'settings': settings, 'section': 'security'})


@login_required
@staff_required
def social_auth_diagnostics(request):
    """OAuth Diagnostics page for admin."""
    from django.conf import settings
    import os
    
    # Check environment variables
    diagnostics = {
        'google': {
            'client_id': bool(settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY),
            'client_secret': bool(settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET),
            'redirect_uri': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI,
            'status': 'configured' if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET else 'missing_keys'
        },
        'facebook': {
            'client_id': bool(settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_KEY),
            'client_secret': bool(settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_SECRET),
            'redirect_uri': settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI,
            'status': 'configured' if settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_KEY and settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_SECRET else 'missing_keys'
        },
        'environment': {
            'debug': settings.DEBUG,
            'railway_domain': os.getenv('RAILWAY_PUBLIC_DOMAIN', 'Not set'),
            'base_url': getattr(settings, 'BASE_URL', 'Not set'),
        },
        'backends': settings.AUTHENTICATION_BACKENDS,
        'pipeline': settings.SOCIAL_AUTH_PIPELINE,
    }
    
    return render(request, 'properties/social_auth_diagnostics.html', {
        'diagnostics': diagnostics,
        'section': 'social_auth',
    })


@login_required
def social_settings(request):
    """Social authentication settings page."""
    from social_django.models import UserSocialAuth
    
    google_association = None
    facebook_association = None
    
    try:
        google_association = UserSocialAuth.objects.get(
            user=request.user,
            provider='google-oauth2'
        )
    except UserSocialAuth.DoesNotExist:
        pass
    
    try:
        facebook_association = UserSocialAuth.objects.get(
            user=request.user,
            provider='facebook'
        )
    except UserSocialAuth.DoesNotExist:
        pass
    
    return render(request, 'properties/social_settings.html', {
        'google_association': google_association,
        'facebook_association': facebook_association,
    })



@login_required
@staff_required
def settings_reports(request):
    """Report settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.enable_reports = request.POST.get('enable_reports') == 'on'
        settings.auto_review_reports = request.POST.get('auto_review_reports') == 'on'
        settings.report_priority_threshold = request.POST.get('report_priority_threshold', 'high')
        settings.save()
        messages.success(request, 'تم تحديث إعدادات البلاغات بنجاح')
        return redirect('settings_reports')
    
    return render(request, 'properties/settings_reports.html', {'settings': settings, 'section': 'reports'})


@login_required
@staff_required
def settings_backup(request):
    """Backup settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    from .models import Backup
    backups = Backup.objects.select_related('created_by').order_by('-created_at')[:50]
    if request.method == 'POST':
        settings.auto_backup_enabled = request.POST.get('auto_backup_enabled') == 'on'
        settings.backup_frequency = request.POST.get('backup_frequency', 'daily')
        settings.backup_retention_days = int(request.POST.get('backup_retention_days', 30))
        settings.save()
        messages.success(request, 'تم تحديث إعدادات النسخ الاحتياطي بنجاح')
        return redirect('settings_backup')
    
    return render(request, 'properties/settings_backup.html', {
        'settings': settings,
        'section': 'backup',
        'backups': backups,
    })


@login_required
@staff_required
def settings_seo(request):
    """SEO settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.seo_title = request.POST.get('seo_title', '')
        settings.seo_description = request.POST.get('seo_description', '')
        settings.seo_keywords = request.POST.get('seo_keywords', '')
        settings.enable_og_tags = request.POST.get('enable_og_tags') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات SEO بنجاح')
        return redirect('settings_seo')
    
    return render(request, 'properties/settings_seo.html', {'settings': settings, 'section': 'seo'})


@login_required
@staff_required
def settings_api(request):
    """API settings page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.enable_api = request.POST.get('enable_api') == 'on'
        settings.api_rate_limit = int(request.POST.get('api_rate_limit', 1000))
        settings.api_key_required = request.POST.get('api_key_required') == 'on'
        settings.save()
        messages.success(request, 'تم تحديث إعدادات API بنجاح')
        return redirect('settings_api')
    
    return render(request, 'properties/settings_api.html', {'settings': settings, 'section': 'api'})


@login_required
@staff_required
def settings_system(request):
    """System info page."""
    if not can_manage_site_settings(request.user):
        messages.error(request, 'ليس لديك صلاحية تعديل إعدادات الموقع')
        return redirect('dashboard')
    settings = SiteSettings.get_solo()
    if request.method == 'POST':
        settings.system_version = request.POST.get('system_version', '1.0.0')
        settings.license_key = request.POST.get('license_key', '')
        settings.save()
        messages.success(request, 'تم تحديث معلومات النظام بنجاح')
        return redirect('settings_system')
    
    return render(request, 'properties/settings_system.html', {'settings': settings, 'section': 'system'})


def explore_view(request):
    """TikTok-style property browsing page."""
    # Get filters from query parameters
    content_type = request.GET.get('type', 'all')  # all, video, photo
    property_type = request.GET.get('property_type', 'all')  # all, villa, apartment, land, office
    listing_type = request.GET.get('listing_type', 'all')  # all, sale, rent
    user_only = request.GET.get('user_only', 'false') == 'true'  # show user's properties only
    
    # Get properties with videos or images
    properties = get_public_properties()
    
    # Filter by user if requested
    if user_only and request.user.is_authenticated:
        properties = [p for p in properties if p.owner == request.user or (p.broker and p.broker.user == request.user)]
    
    # Apply filters (handle list input)
    if content_type == 'video':
        properties = [p for p in properties if p.videos.exists()]
    elif content_type == 'photo':
        properties = [p for p in properties if p.gallery_images.exists()]
    
    if property_type != 'all':
        properties = [p for p in properties if p.type == property_type]
    
    if listing_type == 'sale':
        properties = [p for p in properties if p.status in PUBLIC_STATUSES]
    elif listing_type == 'rent':
        properties = [p for p in properties if p.status == 'rent']
    
    # Order by views or random for variety
    properties = sorted(properties, key=lambda x: x.created_at, reverse=True)[:50]
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/explore.html', {
        'properties': properties,
        'content_type': content_type,
        'property_type': property_type,
        'listing_type': listing_type,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'user_only': user_only,
    })


def properties_outside_iraq_view(request):
    """View for properties, resorts, and hotels outside Iraq with advanced filters."""
    from properties.models import Resort, Hotel, Country, City, Area
    from properties.constants import OUTSIDE_IRAQ_PROPERTY_TYPES
    
    # Get filters from query parameters
    category = request.GET.get('category', 'all')  # all, properties, resorts, hotels
    content_type = request.GET.get('type', 'all')
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    user_only = request.GET.get('user_only', 'false') == 'true'
    
    # Advanced filters
    country_id = request.GET.get('country', '')
    city_id = request.GET.get('city', '')
    area_id = request.GET.get('area', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    currency = request.GET.get('currency', '')
    area_min = request.GET.get('area_min', '')
    area_max = request.GET.get('area_max', '')
    bedrooms = request.GET.get('bedrooms', '')
    bathrooms = request.GET.get('bathrooms', '')
    year_built = request.GET.get('year_built', '')
    broker_name = request.GET.get('broker_name', '')
    featured_only = request.GET.get('featured_only', 'false') == 'true'
    min_rating = request.GET.get('min_rating', '')
    
    properties_list = []
    resorts_list = []
    hotels_list = []
    
    # Get all countries for the filter dropdown
    countries = Country.objects.all().order_by('order', 'name_ar')
    cities = []
    areas = []
    
    if country_id:
        cities = City.objects.filter(country_id=country_id).order_by('name_ar')
    if city_id:
        areas = Area.objects.filter(city_id=city_id).order_by('name_ar')
    
    # Get properties outside Iraq
    if category in ['all', 'properties']:
        properties = get_public_properties()
        properties = [p for p in properties if p.country and p.country.code != 'IQ']
        
        # Filter by country
        if country_id:
            properties = [p for p in properties if p.country_id == int(country_id)]
        
        # Filter by city
        if city_id:
            properties = [p for p in properties if p.city_id == int(city_id)]
        
        # Filter by area
        if area_id:
            properties = [p for p in properties if p.area_outside_id == int(area_id)]
        
        # Filter by currency
        if currency:
            properties = [p for p in properties if p.currency == currency]
        
        # Filter by price range
        if price_min:
            properties = [p for p in properties if p.price >= int(price_min)]
        if price_max:
            properties = [p for p in properties if p.price <= int(price_max)]
        
        # Filter by area range
        if area_min:
            properties = [p for p in properties if p.area >= int(area_min)]
        if area_max:
            properties = [p for p in properties if p.area <= int(area_max)]
        
        # Filter by bedrooms
        if bedrooms:
            properties = [p for p in properties if p.bedrooms == int(bedrooms)]
        
        # Filter by bathrooms
        if bathrooms:
            properties = [p for p in properties if p.bathrooms == int(bathrooms)]
        
        # Filter by year built
        if year_built:
            properties = [p for p in properties if p.year_built == int(year_built)]
        
        # Filter by broker name
        if broker_name:
            properties = [p for p in properties if p.broker and broker_name.lower() in p.broker.display_name.lower()]
        
        # Filter by featured only
        if featured_only:
            properties = [p for p in properties if p.is_featured]
        
        # Filter by minimum rating
        if min_rating:
            properties = [p for p in properties if hasattr(p, 'average_rating') and p.average_rating >= float(min_rating)]
        
        # Filter by user if requested
        if user_only and request.user.is_authenticated:
            properties = [p for p in properties if p.owner == request.user or (p.broker and p.broker.user == request.user)]
        
        # Apply content type filters
        if content_type == 'video':
            properties = [p for p in properties if p.videos.exists()]
        elif content_type == 'photo':
            properties = [p for p in properties if p.gallery_images.exists()]
        
        # Apply property type filter
        if property_type != 'all':
            properties = [p for p in properties if p.type == property_type]
        
        # Apply listing type filter
        if listing_type == 'sale':
            properties = [p for p in properties if p.status in PUBLIC_STATUSES]
        elif listing_type == 'rent':
            properties = [p for p in properties if p.status == 'rent']
        
        # Order by creation date
        properties_list = sorted(properties, key=lambda x: x.created_at, reverse=True)[:50]
    
    # Get resorts outside Iraq
    if category in ['all', 'resorts']:
        resorts = Resort.objects.filter(status='active')
        resorts = [r for r in resorts if r.country and r.country.code != 'IQ']
        
        # Filter by country
        if country_id:
            resorts = [r for r in resorts if r.country_id == int(country_id)]
        
        # Filter by city
        if city_id:
            resorts = [r for r in resorts if r.city_id == int(city_id)]
        
        if user_only and request.user.is_authenticated:
            resorts = [r for r in resorts if r.owner == request.user]
        
        resorts_list = sorted(resorts, key=lambda x: x.created_at, reverse=True)[:50]
    
    # Get hotels outside Iraq
    if category in ['all', 'hotels']:
        hotels = Hotel.objects.all()
        hotels = [h for h in hotels if h.country and h.country.code != 'IQ']
        
        # Filter by country
        if country_id:
            hotels = [h for h in hotels if h.country_id == int(country_id)]
        
        # Filter by city
        if city_id:
            hotels = [h for h in hotels if h.city_id == int(city_id)]
        
        if user_only and request.user.is_authenticated:
            hotels = [h for h in hotels if h.owner == request.user]
        
        hotels_list = sorted(hotels, key=lambda x: x.created_at, reverse=True)[:50]
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/explore.html', {
        'properties': properties_list,
        'resorts': resorts_list,
        'hotels': hotels_list,
        'content_type': content_type,
        'property_type': property_type,
        'listing_type': listing_type,
        'category': category,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'user_only': user_only,
        'page_title': 'تصفح',
        'countries': countries,
        'cities': cities,
        'areas': areas,
        'selected_country': country_id,
        'selected_city': city_id,
        'selected_area': area_id,
        'price_min': price_min,
        'price_max': price_max,
        'currency': currency,
        'area_min': area_min,
        'area_max': area_max,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'year_built': year_built,
        'broker_name': broker_name,
        'featured_only': featured_only,
        'min_rating': min_rating,
        'OUTSIDE_IRAQ_PROPERTY_TYPES': OUTSIDE_IRAQ_PROPERTY_TYPES,
        'is_outside_iraq': True,
    })


def unified_search_view(request):
    """Unified search view for properties, hotels, resorts, services, building requests, auctions, and jobs."""
    form = PropertySearchForm(request.GET)
    category = request.GET.get('category', '')
    q = request.GET.get('q', '')

    # Initialize result containers
    properties = []
    hotels = []
    resorts = []
    services = []
    building_requests = []
    auctions = []
    jobs = []

    # Search in Properties (Iraq and outside Iraq)
    try:
        if category in ['', 'property_iraq', 'property_outside']:
            property_queryset = get_public_properties()

            # Filter by category (Iraq vs outside Iraq)
            if category == 'property_iraq':
                property_queryset = [p for p in property_queryset if p.country == 'Iraq' or not hasattr(p, 'country')]
            elif category == 'property_outside':
                property_queryset = [p for p in property_queryset if hasattr(p, 'country') and p.country != 'Iraq']

            # Apply text search
            if q:
                property_queryset = [
                    p for p in property_queryset
                    if q.lower() in p.title.lower() or
                   q.lower() in p.district.lower() or
                   q.lower() in p.location.lower() or
                   (p.broker and q.lower() in p.broker.display_name.lower())
                ]

            # Apply filters
            governorate = request.GET.get('governorate')
            if governorate:
                property_queryset = [
                    p for p in property_queryset
                    if (getattr(p, 'governorate', None) and governorate in p.governorate)
                    or (getattr(p, 'district', None) and governorate in p.district)
                    or (getattr(p, 'region', None) and governorate in (p.region or ''))
                ]

            district = request.GET.get('district')
            if district:
                property_queryset = [p for p in property_queryset if district.lower() in p.district.lower()]

            city = request.GET.get('city')
            if city:
                property_queryset = [p for p in property_queryset if city.lower() in p.location.lower()]

            country = request.GET.get('country')
            if country:
                property_queryset = [p for p in property_queryset if hasattr(p, 'country') and country.lower() in p.country.lower()]

            property_type = request.GET.get('type')
            if property_type:
                property_queryset = [p for p in property_queryset if p.type == property_type]

            status = request.GET.get('status')
            if status:
                property_queryset = [p for p in property_queryset if p.status == status]

            purpose = request.GET.get('purpose')
            if purpose:
                property_queryset = [p for p in property_queryset if p.purpose == purpose]

            verification_status = request.GET.get('verification_status')
            if verification_status:
                property_queryset = [
                    p for p in property_queryset
                    if hasattr(p, 'verification') and p.verification and p.verification.verification_status == verification_status
                ]

            furnishing_status = request.GET.get('furnishing_status')
            if furnishing_status:
                property_queryset = [p for p in property_queryset if p.furnishing_status == furnishing_status]

            price_min = request.GET.get('price_min')
            if price_min:
                property_queryset = [p for p in property_queryset if p.price >= int(price_min)]

            price_max = request.GET.get('price_max')
            if price_max:
                property_queryset = [p for p in property_queryset if p.price <= int(price_max)]

            area_min = request.GET.get('area_min')
            if area_min:
                property_queryset = [p for p in property_queryset if p.area >= int(area_min)]

            area_max = request.GET.get('area_max')
            if area_max:
                property_queryset = [p for p in property_queryset if p.area <= int(area_max)]

            bedrooms = request.GET.get('bedrooms')
            if bedrooms:
                property_queryset = [p for p in property_queryset if p.bedrooms == int(bedrooms)]
        
        bathrooms = request.GET.get('bathrooms')
        if bathrooms:
            property_queryset = [p for p in property_queryset if p.bathrooms == int(bathrooms)]

        floors = request.GET.get('floors')
        if floors:
            property_queryset = [p for p in property_queryset if p.floors == int(floors)]
        
        year_built = request.GET.get('year_built')
        if year_built:
            property_queryset = [p for p in property_queryset if p.year_built == int(year_built)]
        
        featured_only = request.GET.get('featured_only')
        if featured_only:
            property_queryset = [p for p in property_queryset if p.is_featured]
        
        verified_only = request.GET.get('verified_only')
        if verified_only:
            property_queryset = [p for p in property_queryset if p.broker and p.broker.is_verified]
        
        new_only = request.GET.get('new_only')
        if new_only:
            from datetime import timedelta
            from django.utils import timezone
            week_ago = timezone.now() - timedelta(days=7)
            property_queryset = [p for p in property_queryset if p.created_at >= week_ago]
        
        broker_name = request.GET.get('broker_name')
        if broker_name:
            property_queryset = [p for p in property_queryset if p.broker and broker_name.lower() in p.broker.display_name.lower()]
        
        rating_min = request.GET.get('rating_min')
        if rating_min:
            property_queryset = [p for p in property_queryset if hasattr(p, 'average_rating') and p.average_rating >= int(rating_min)]
        
        # New filters for amenities
        has_elevator = request.GET.get('has_elevator')
        if has_elevator:
            property_queryset = [p for p in property_queryset if p.has_elevator]
        
        has_garage = request.GET.get('has_garage')
        if has_garage:
            property_queryset = [p for p in property_queryset if p.has_garage]
        
        has_security_system = request.GET.get('has_security_system')
        if has_security_system:
            property_queryset = [p for p in property_queryset if p.has_security_system]
        
        has_generator = request.GET.get('has_generator')
        if has_generator:
            property_queryset = [p for p in property_queryset if p.has_private_generator]
        
        # Rental filters
        allows_pets = request.GET.get('allows_pets')
        if allows_pets:
            property_queryset = [p for p in property_queryset if p.allows_pets]
        
        allows_families = request.GET.get('allows_families')
        if allows_families:
            property_queryset = [p for p in property_queryset if p.allows_families]
        
        allows_students = request.GET.get('allows_students')
        if allows_students:
            property_queryset = [p for p in property_queryset if p.allows_students]
        
        allows_companies = request.GET.get('allows_companies')
        if allows_companies:
            property_queryset = [p for p in property_queryset if p.allows_companies]
        
        # Monthly rent filters
        monthly_rent_min = request.GET.get('monthly_rent_min')
        if monthly_rent_min:
            property_queryset = [p for p in property_queryset if p.monthly_rent and p.monthly_rent >= int(monthly_rent_min)]
        
        monthly_rent_max = request.GET.get('monthly_rent_max')
        if monthly_rent_max:
            property_queryset = [p for p in property_queryset if p.monthly_rent and p.monthly_rent <= int(monthly_rent_max)]
        
        # Complex name filter
        complex_name = request.GET.get('complex_name')
        if complex_name:
            property_queryset = [p for p in property_queryset if p.complex_name and complex_name.lower() in p.complex_name.lower()]
        
        # Broker and office filters
        broker_id = request.GET.get('broker_id')
        if broker_id:
            property_queryset = [p for p in property_queryset if p.broker and p.broker.id == int(broker_id)]
        
        office_id = request.GET.get('office_id')
        if office_id:
            property_queryset = [p for p in property_queryset if p.office and p.office.id == int(office_id)]
        
        # Apply sorting
        sort = request.GET.get('sort')
        if sort == 'newest':
            property_queryset = sorted(property_queryset, key=lambda x: x.created_at, reverse=True)
        elif sort == 'oldest':
            property_queryset = sorted(property_queryset, key=lambda x: x.created_at)
        elif sort == 'price_asc':
            property_queryset = sorted(property_queryset, key=lambda x: x.price)
        elif sort == 'price_desc':
            property_queryset = sorted(property_queryset, key=lambda x: x.price, reverse=True)
        elif sort == 'views':
            property_queryset = sorted(property_queryset, key=lambda x: x.views_count, reverse=True)
        elif sort == 'rating':
            property_queryset = sorted(property_queryset, key=lambda x: getattr(x, 'average_rating', 0), reverse=True)

        properties = property_queryset
    except Exception:
        properties = []

    # Search in Hotels
    if category in ['', 'hotel']:
        try:
            hotel_queryset = Hotel.objects.filter(is_active=True)

            if q:
                hotel_queryset = hotel_queryset.filter(
                    Q(name__icontains=q) |
                    Q(description__icontains=q) |
                    Q(city__icontains=q)
                )

            city = request.GET.get('city')
            if city:
                hotel_queryset = hotel_queryset.filter(city__icontains=city)

            price_range = request.GET.get('price_range')
            if price_range:
                hotel_queryset = hotel_queryset.filter(price_range=price_range)

            star_rating = request.GET.get('star_rating')
            if star_rating:
                hotel_queryset = hotel_queryset.filter(star_rating=int(star_rating))

            featured_only = request.GET.get('featured_only')
            if featured_only:
                hotel_queryset = hotel_queryset.filter(is_featured=True)

            hotels = list(hotel_queryset)
        except Exception:
            hotels = []
    
    # Search in Resorts
    if category in ['', 'resort']:
        try:
            resort_queryset = Resort.objects.filter(status='active')

            if q:
                resort_queryset = resort_queryset.filter(
                    Q(name__icontains=q) |
                    Q(description__icontains=q) |
                    Q(city__icontains=q)
                )

            governorate = request.GET.get('governorate')
            if governorate:
                resort_queryset = resort_queryset.filter(governorate=governorate)

            city = request.GET.get('city')
            if city:
                resort_queryset = resort_queryset.filter(city__icontains=city)

            resort_type = request.GET.get('resort_type')
            if resort_type:
                resort_queryset = resort_queryset.filter(resort_type=resort_type)

            featured_only = request.GET.get('featured_only')
            if featured_only:
                resort_queryset = resort_queryset.filter(is_featured=True)

            resorts = list(resort_queryset)
        except Exception:
            resorts = []
    
    # Search in Services
    if category in ['', 'service']:
        try:
            service_queryset = ServiceAdvertisement.objects.filter(status='active')

            if q:
                service_queryset = service_queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(location__icontains=q)
                )

            governorate = request.GET.get('governorate')
            if governorate:
                service_queryset = service_queryset.filter(governorate=governorate)

            service_type = request.GET.get('service_type')
            if service_type:
                service_queryset = service_queryset.filter(service_type=service_type)

            price_min = request.GET.get('price_min')
            if price_min:
                service_queryset = service_queryset.filter(price__gte=price_min)

            price_max = request.GET.get('price_max')
            if price_max:
                service_queryset = service_queryset.filter(price__lte=price_max)

            services = list(service_queryset)
        except Exception:
            services = []
    
    # Search in Building Requests
    # Search in Auctions
    if category in ['', 'auction']:
        try:
            auction_queryset = Auction.objects.filter(status='active')

            if q:
                auction_queryset = auction_queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q)
                )

            auction_type = request.GET.get('auction_type')
            if auction_type:
                auction_queryset = auction_queryset.filter(auction_type=auction_type)

            price_min = request.GET.get('price_min')
            if price_min:
                auction_queryset = auction_queryset.filter(starting_price__gte=price_min)

            price_max = request.GET.get('price_max')
            if price_max:
                auction_queryset = auction_queryset.filter(starting_price__lte=price_max)

            auctions = list(auction_queryset)
        except Exception:
            auctions = []
    
    # Search in Jobs
    if category in ['', 'job']:
        try:
            job_queryset = Job.objects.filter(status='active')

            if q:
                job_queryset = job_queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q) |
                    Q(location__icontains=q)
                )

            governorate = request.GET.get('governorate')
            if governorate:
                job_queryset = job_queryset.filter(governorate=governorate)

            job_type = request.GET.get('job_type')
            if job_type:
                job_queryset = job_queryset.filter(job_type=job_type)

            salary_min = request.GET.get('price_min')
            if salary_min:
                job_queryset = job_queryset.filter(salary_min__gte=salary_min)

            salary_max = request.GET.get('price_max')
            if salary_max:
                job_queryset = job_queryset.filter(salary_max__lte=salary_max)

            jobs = list(job_queryset)
        except Exception:
            jobs = []
    
    # Combine all results for pagination
    all_results = []
    for p in properties:
        all_results.append({
            'type': 'property',
            'object': p,
            'title': p.display_title,
            'price': p.price,
            'location': p.district,
            'image': p.get_main_image if hasattr(p, 'get_main_image') else None,
            'created_at': p.created_at,
        })
    
    for h in hotels:
        all_results.append({
            'type': 'hotel',
            'object': h,
            'title': h.name,
            'price': 0,  # Hotels use price_range instead
            'location': h.city,
            'image': h.image.url if h.image else None,
            'created_at': h.created_at if hasattr(h, 'created_at') else None,
        })
    
    for r in resorts:
        all_results.append({
            'type': 'resort',
            'object': r,
            'title': r.name,
            'price': 0,  # Resorts use price_range instead
            'location': r.city,
            'image': r.image.url if r.image else None,
            'created_at': r.created_at,
        })
    
    for s in services:
        all_results.append({
            'type': 'service',
            'object': s,
            'title': s.title,
            'price': s.price if hasattr(s, 'price') else 0,
            'location': s.location if hasattr(s, 'location') else s.governorate,
            'image': s.image.url if hasattr(s, 'image') and s.image else None,
            'created_at': s.created_at if hasattr(s, 'created_at') else None,
        })
    
    for b in building_requests:
        all_results.append({
            'type': 'building_request',
            'object': b,
            'title': b.project_type if hasattr(b, 'project_type') else 'طلب بناء',
            'price': b.estimated_budget if hasattr(b, 'estimated_budget') else 0,
            'location': b.city if hasattr(b, 'city') else b.governorate,
            'image': None,
            'created_at': b.created_at if hasattr(b, 'created_at') else None,
        })
    
    for a in auctions:
        all_results.append({
            'type': 'auction',
            'object': a,
            'title': a.title,
            'price': a.starting_price,
            'location': a.property.district if hasattr(a, 'property') and a.property else '',
            'image': a.property.get_main_image() if hasattr(a, 'property') and a.property else None,
            'created_at': a.created_at if hasattr(a, 'created_at') else None,
        })
    
    for j in jobs:
        all_results.append({
            'type': 'job',
            'object': j,
            'title': j.title,
            'price': j.salary_min if hasattr(j, 'salary_min') else 0,
            'location': j.location if hasattr(j, 'location') else j.governorate,
            'image': j.image.url if hasattr(j, 'image') and j.image else None,
            'created_at': j.created_at if hasattr(j, 'created_at') else None,
        })
    
    # Sort combined results
    sort = request.GET.get('sort')
    if sort == 'newest':
        all_results = sorted(all_results, key=lambda x: x['created_at'] or timezone.now(), reverse=True)
    elif sort == 'oldest':
        all_results = sorted(all_results, key=lambda x: x['created_at'] or timezone.now())
    
    # Pagination
    paginator = Paginator(all_results, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get user's likes and saves
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        try:
            user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
            user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
        except Exception:
            user_likes = set()
            user_saves = set()
    
    return render(request, 'properties/unified_search.html', {
        'form': form,
        'results': page_obj,
        'page_obj': page_obj,
        'properties': properties,
        'hotels': hotels,
        'resorts': resorts,
        'services': services,
        'building_requests': building_requests,
        'auctions': auctions,
        'jobs': jobs,
        'category': category,
        'q': q,
        'user_likes': user_likes,
        'user_saves': user_saves,
    })


def channel_brokers_view(request):
    """Channel page for broker properties with district filter."""
    from .models import Broker
    
    district = request.GET.get('district', '')
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    
    # Get all brokers
    brokers = Broker.objects.filter(is_active=True, is_verified=True)
    
    # Get broker properties
    properties = Property.objects.filter(
        broker__isnull=False,
        broker__is_active=True,
        status__in=PUBLIC_STATUSES
    ).select_related('owner', 'broker', 'broker__user').prefetch_related('gallery_images')
    
    # Filter by district
    if district:
        properties = properties.filter(district__icontains=district)
    
    # Filter by property type
    if property_type != 'all':
        properties = properties.filter(type=property_type)
    
    # Filter by listing type
    if listing_type == 'sale':
        properties = properties.filter(status__in=PUBLIC_STATUSES)
    elif listing_type == 'rent':
        properties = properties.filter(status='rent')
    
    # Order by created date
    properties = properties.order_by('-created_at')[:50]
    
    # Get all districts for filter
    districts = Property.objects.values_list('district', flat=True).distinct()
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/channel_brokers.html', {
        'properties': properties,
        'district': district,
        'property_type': property_type,
        'listing_type': listing_type,
        'districts': districts,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'channel_name': 'الدلالين',
        'channel_icon': '🧑‍💼',
    })


def channel_users_view(request):
    """Channel page for user properties with district filter."""
    district = request.GET.get('district', '')
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    
    # Get user properties (properties without broker)
    properties = Property.objects.filter(
        broker__isnull=True,
        status__in=PUBLIC_STATUSES
    ).select_related('owner').prefetch_related('gallery_images')
    
    # Filter by district
    if district:
        properties = properties.filter(district__icontains=district)
    
    # Filter by property type
    if property_type != 'all':
        properties = properties.filter(type=property_type)
    
    # Filter by listing type
    if listing_type == 'sale':
        properties = properties.filter(status__in=PUBLIC_STATUSES)
    elif listing_type == 'rent':
        properties = properties.filter(status='rent')
    
    # Order by created date
    properties = properties.order_by('-created_at')[:50]
    
    # Get all districts for filter
    districts = Property.objects.values_list('district', flat=True).distinct()
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/channel_users.html', {
        'properties': properties,
        'district': district,
        'property_type': property_type,
        'listing_type': listing_type,
        'districts': districts,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'channel_name': 'المستخدمين',
        'channel_icon': '👤',
    })


def channel_admin_view(request):
    """Channel page for all properties (admin view) with district filter."""
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه الصفحة')
        return redirect('home')
    
    district = request.GET.get('district', '')
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    
    # Get all properties
    properties = Property.objects.select_related('owner', 'broker', 'broker__user').prefetch_related('gallery_images')
    
    # Filter by district
    if district:
        properties = properties.filter(district__icontains=district)
    
    # Filter by property type
    if property_type != 'all':
        properties = properties.filter(type=property_type)
    
    # Filter by listing type
    if listing_type == 'sale':
        properties = properties.filter(status__in=PUBLIC_STATUSES)
    elif listing_type == 'rent':
        properties = properties.filter(status='rent')
    
    # Order by created date
    properties = properties.order_by('-created_at')[:50]
    
    # Get all districts for filter
    districts = Property.objects.values_list('district', flat=True).distinct()
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/channel_admin.html', {
        'properties': properties,
        'district': district,
        'property_type': property_type,
        'listing_type': listing_type,
        'districts': districts,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'channel_name': 'مدير المنصة',
        'channel_icon': '👑',
    })


def channels_view(request):
    """Main channels page listing all available channels."""
    from .models import Broker, BrokerChannel
    
    # Get channel statistics
    broker_properties_count = Property.objects.filter(
        broker__isnull=False,
        broker__is_active=True,
        status__in=PUBLIC_STATUSES
    ).count()
    
    user_properties_count = Property.objects.filter(
        broker__isnull=True,
        status__in=PUBLIC_STATUSES
    ).count()
    
    all_properties_count = Property.objects.count()
    
    brokers_count = Broker.objects.filter(is_active=True, is_verified=True).count()
    
    channels = [
        {
            'name': 'الدلالين',
            'icon': '🧑‍💼',
            'description': 'تصفح جميع العقارات المعروضة من قبل الدلالين المعتمدين',
            'url': 'channel_brokers',
            'color': 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
            'properties_count': broker_properties_count,
            'members_count': brokers_count,
        },
    ]
    
    # Add individual broker channels
    try:
        broker_channels = BrokerChannel.objects.filter(
            status='active',
            is_verified=True
        ).select_related('broker', 'broker__user').prefetch_related('broker__user__owned_properties')
        
        for channel in broker_channels:
            channels.append({
                'name': channel.name,
                'icon': '📺',
                'description': channel.description or f'قناة {channel.broker.display_name}',
                'url': 'broker_channel_detail',
                'url_args': [channel.id],
                'color': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                'properties_count': channel.properties_count,
                'members_count': channel.followers_count,
                'is_broker_channel': True,
                'channel_id': channel.id,
                'logo': channel.logo.url if channel.logo else None,
                'cover': channel.cover_image.url if channel.cover_image else None,
            })
    except Exception as e:
        logger.error(f"Error loading broker channels: {e}")
    
    # Add admin channel only for superusers
    if request.user.is_superuser:
        channels.append({
            'name': 'مدير المنصة',
            'icon': '👑',
            'description': 'تصفح جميع العقارات في المنصة (عرض المدير)',
            'url': 'channel_admin',
            'color': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'properties_count': all_properties_count,
            'members_count': 1,
        })
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        channels = [c for c in channels if search_query.lower() in c['name'].lower()]
    
    return render(request, 'properties/channels.html', {
        'channels': channels,
        'search_query': search_query,
    })


def broker_channel_detail(request, channel_id):
    """Individual broker channel page showing all properties from that broker."""
    from .models import BrokerChannel, ChannelPost
    
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    
    # Increment views
    channel.increment_views()
    
    district = request.GET.get('district', '')
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    
    # Get broker properties
    properties = Property.objects.filter(
        broker=channel.broker,
        status__in=PUBLIC_STATUSES
    ).select_related('owner', 'broker', 'broker__user').prefetch_related('gallery_images')
    
    # Filter by district
    if district:
        properties = properties.filter(district__icontains=district)
    
    # Filter by property type
    if property_type != 'all':
        properties = properties.filter(type=property_type)
    
    # Filter by listing type
    if listing_type == 'sale':
        properties = properties.filter(status__in=PUBLIC_STATUSES)
    elif listing_type == 'rent':
        properties = properties.filter(status='rent')
    
    # Order by created date
    properties = properties.order_by('-created_at')[:50]
    
    # Get all districts for filter
    districts = Property.objects.filter(broker=channel.broker).values_list('district', flat=True).distinct()
    
    # Get channel posts
    channel_posts = ChannelPost.objects.filter(
        channel=channel,
        status='published'
    ).select_related('author').prefetch_related('likes', 'comments').order_by('-is_pinned', '-created_at')[:20]
    
    # Get featured properties
    featured_properties = Property.objects.filter(
        broker=channel.broker,
        status__in=PUBLIC_STATUSES,
        is_featured=True
    ).select_related('owner', 'broker').prefetch_related('gallery_images')[:6]
    
    # Get most viewed properties
    most_viewed_properties = Property.objects.filter(
        broker=channel.broker,
        status__in=PUBLIC_STATUSES
    ).select_related('owner', 'broker').prefetch_related('gallery_images').order_by('-views_count')[:6]
    
    # Get new properties
    new_properties = Property.objects.filter(
        broker=channel.broker,
        status__in=PUBLIC_STATUSES
    ).select_related('owner', 'broker').prefetch_related('gallery_images').order_by('-created_at')[:6]
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    is_following = False
    notifications_enabled = False
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
        # Check if user is following this channel
        from .models import BrokerSubscription
        is_following = BrokerSubscription.objects.filter(
            user=request.user,
            broker=channel.broker,
            is_active=True
        ).exists()
    
    return render(request, 'properties/broker_channel_detail.html', {
        'channel': channel,
        'properties': properties,
        'district': district,
        'property_type': property_type,
        'listing_type': listing_type,
        'districts': districts,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'is_following': is_following,
        'channel_posts': channel_posts,
        'featured_properties': featured_properties,
        'most_viewed_properties': most_viewed_properties,
        'new_properties': new_properties,
    })


@login_required
def like_property(request, property_id):
    """Like or unlike a property."""
    property = get_object_or_404(Property, id=property_id)
    like, created = PropertyLike.objects.get_or_create(
        property=property,
        user=request.user
    )
    
    if not created:
        like.delete()
        return JsonResponse({'liked': False, 'count': property.likes.count()})
    
    return JsonResponse({'liked': True, 'count': property.likes.count()})


@login_required
def save_property(request, property_id):
    """Save or unsave a property."""
    property = get_object_or_404(Property, id=property_id)
    save, created = PropertySave.objects.get_or_create(
        property=property,
        user=request.user
    )
    
    if not created:
        save.delete()
        return JsonResponse({'saved': False})
    
    return JsonResponse({'saved': True})


@login_required
def add_comment(request, property_id):
    """Add a comment to a property."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    property = get_object_or_404(Property, id=property_id)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    
    comment = PropertyComment.objects.create(
        property=property,
        user=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })


@login_required
def favorites_view(request):
    """Display user's favorite/saved properties."""
    saved_properties = PropertySave.objects.filter(user=request.user).select_related('property').order_by('-created_at')
    properties = [save.property for save in saved_properties]
    
    return render(request, 'properties/favorites.html', {
        'properties': properties,
        'saved_properties': saved_properties,
    })


@login_required
def add_virtual_tour(request, property_id):
    """Add a virtual tour to a property."""
    property = get_object_or_404(Property, id=property_id)
    
    if not can_edit_property(request.user, property):
        messages.error(request, 'ليس لديك صلاحية إضافة جولة لهذا العقار')
        return redirect('property_detail', property.slug)
    
    if request.method == 'POST':
        form = VirtualTour360Form(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.property = property
            tour.save()
            messages.success(request, 'تم إضافة الجولة الافتراضية بنجاح')
            return redirect('property_detail', property.slug)
    else:
        form = VirtualTour360Form()
    
    return render(request, 'properties/add_virtual_tour.html', {
        'form': form,
        'property': property,
    })


@login_required
def edit_virtual_tour(request, tour_id):
    """Edit a virtual tour."""
    tour = get_object_or_404(VirtualTour360, id=tour_id)
    
    if not can_edit_property(request.user, tour.property):
        messages.error(request, 'ليس لديك صلاحية تعديل هذه الجولة')
        return redirect('property_detail', tour.property.slug)
    
    if request.method == 'POST':
        form = VirtualTour360Form(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الجولة الافتراضية بنجاح')
            return redirect('property_detail', tour.property.slug)
    else:
        form = VirtualTour360Form(instance=tour)
    
    return render(request, 'properties/edit_virtual_tour.html', {
        'form': form,
        'tour': tour,
        'property': tour.property,
    })


@login_required
def delete_virtual_tour(request, tour_id):
    """Delete a virtual tour."""
    tour = get_object_or_404(VirtualTour360, id=tour_id)
    property_slug = tour.property.slug
    
    if not can_edit_property(request.user, tour.property):
        messages.error(request, 'ليس لديك صلاحية حذف هذه الجولة')
        return redirect('property_detail', property_slug)
    
    tour.delete()
    messages.success(request, 'تم حذف الجولة الافتراضية بنجاح')
    return redirect('property_detail', property_slug)


@login_required
def add_tour_point(request, tour_id):
    """Add a point to a virtual tour."""
    tour = get_object_or_404(VirtualTour360, id=tour_id)
    
    if not can_edit_property(request.user, tour.property):
        messages.error(request, 'ليس لديك صلاحية إضافة نقطة لهذه الجولة')
        return redirect('property_detail', tour.property.slug)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        
        if name:
            point = VirtualTourPoint.objects.create(
                virtual_tour=tour,
                name=name,
                description=description,
                image=image
            )
            messages.success(request, 'تم إضافة النقطة بنجاح')
            return redirect('property_detail', tour.property.slug)
    
    return render(request, 'properties/add_tour_point.html', {
        'tour': tour,
        'property': tour.property,
    })


@login_required
def edit_tour_point(request, point_id):
    """Edit a tour point."""
    point = get_object_or_404(VirtualTourPoint, id=point_id)
    
    if not can_edit_property(request.user, point.virtual_tour.property):
        messages.error(request, 'ليس لديك صلاحية تعديل هذه النقطة')
        return redirect('property_detail', point.virtual_tour.property.slug)
    
    if request.method == 'POST':
        point.name = request.POST.get('name', point.name)
        point.description = request.POST.get('description', point.description)
        image = request.FILES.get('image')
        if image:
            point.image = image
        point.save()
        messages.success(request, 'تم تحديث النقطة بنجاح')
        return redirect('property_detail', point.virtual_tour.property.slug)
    
    return render(request, 'properties/edit_tour_point.html', {
        'point': point,
        'tour': point.virtual_tour,
        'property': point.virtual_tour.property,
    })


@login_required
def delete_tour_point(request, point_id):
    """Delete a tour point."""
    point = get_object_or_404(VirtualTourPoint, id=point_id)
    property_slug = point.virtual_tour.property.slug
    
    if not can_edit_property(request.user, point.virtual_tour.property):
        messages.error(request, 'ليس لديك صلاحية حذف هذه النقطة')
        return redirect('property_detail', property_slug)
    
    point.delete()
    messages.success(request, 'تم حذف النقطة بنجاح')
    return redirect('property_detail', property_slug)


@login_required
def jobs_list(request):
    """List all jobs."""
    jobs = Job.objects.filter(status='active').order_by('-created_at')
    return render(request, 'properties/jobs_list.html', {'jobs': jobs})


@login_required
def job_create(request):
    """Create a new job."""
    if request.method == 'POST':
        # Simple redirect to add property for now
        messages.info(request, 'وظائف - يرجى استخدام نموذج إضافة العقار')
        return redirect('add_property')
    return render(request, 'properties/job_create.html')


@login_required
def my_jobs(request):
    """List user's jobs."""
    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
    return render(request, 'properties/my_jobs.html', {'jobs': jobs})


@login_required
def job_edit(request, pk):
    """Edit a job."""
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        messages.info(request, 'تعديل الوظيفة - تحت قيد التطوير')
        return redirect('job_detail', pk=pk)
    return render(request, 'properties/job_edit.html', {'job': job})


@login_required
def job_delete(request, pk):
    """Delete a job."""
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'تم حذف الوظيفة بنجاح')
        return redirect('my_jobs')
    return render(request, 'properties/job_delete.html', {'job': job})


@login_required
def job_detail(request, pk):
    """View job details."""
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'properties/job_detail.html', {'job': job})


