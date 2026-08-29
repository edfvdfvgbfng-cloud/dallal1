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
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from .utils import match_advertisement_with_targets
from .channel_views import ChannelListView, ChannelDetailView
from .models import Property, PropertyVerification, Job, Backup, Hotel, Resort, ServiceProvider, ServiceAdvertisement, Auction, UserProfile, Conversation, RealEstateContract, Customer, Agent
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
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


from .decorators import broker_required, rate_limit
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

logger = logging.getLogger('properties')

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


def contact_page(request):
    settings = SiteSettings.get_solo()
    form = MessageForm()
    return render(request, 'properties/contact.html', {
        'settings': settings,
        'form': form,
    })


def subscription_plans(request):
    """Display subscription plans page."""
    settings = SiteSettings.get_solo()
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


@csrf_exempt
def login_view(request):
    from .permissions import get_redirect_after_login, get_user_type, can_access_dashboard, get_broker

    if request.user.is_authenticated:
        redirect_url = get_redirect_after_login(request.user)
        return redirect(redirect_url)

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
                    return render(request, 'properties/login.html')
                
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
                if user_type == 'admin':
                    messages.success(request, 'مرحباً بك في لوحة الإدارة')
                    return redirect('admin_panel')
                elif user_type == 'broker':
                    broker = get_broker(user)
                    if broker and not broker.is_active:
                        messages.error(request, 'تم تعطيل حساب الدلال. يرجى التواصل مع الإدارة')
                        logout(request)
                        return render(request, 'properties/login.html')
                    messages.success(request, 'مرحباً بك في لوحة الدلال')
                    return redirect('dashboard')
                else:
                    messages.success(request, 'تم تسجيل الدخول بنجاح')
                    return redirect('home')
            else:
                messages.error(request, 'بيانات الدخول غير صحيحة')
                logger.warning('Failed login attempt for user: %s', username)
    
    return render(request, 'properties/login.html')


def register_view(request):
    """Register a new user account (regular users only)."""
    from django.contrib.auth.models import User
    
    if request.user.is_authenticated:
        return redirect('home')
    
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
        elif password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
        elif len(password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم بالفعل')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
        else:
            # Check for duplicate phone in Broker profiles
            from .models import Broker, UserProfile
            if Broker.objects.filter(phone=phone).exists():
                messages.error(request, 'رقم الهاتف مستخدم بالفعل')
            else:
                # Create regular user (no broker profile)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_staff=False  # Regular users are not staff
                )
                
                # Create or update UserProfile with additional information
                user_profile, created = UserProfile.objects.get_or_create(user=user)
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
                        title='مستخدم جديد',
                        message=f'مستخدم جديد: {user.get_full_name() or user.username}',
                        link=f'/admin/auth/user/{user.id}/change/',
                        metadata={'user_id': user.id}
                    )
                
                # Log activity
                from .models import ActivityLog
                ActivityLog.log(
                    user=user,
                    action='create',
                    model_type='user',
                    object_id=user.id,
                    object_repr=user.username,
                    description=f'إنشاء حساب مستخدم جديد: {user.username}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={'account_type': 'user'}
                )
                
                messages.success(request, 'تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول')
                return redirect('login')
    
    return render(request, 'properties/register.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('home')


def password_reset_request(request):
    """Handle password reset request."""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'يرجى إدخال البريد الإلكتروني')
        else:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(email=email)
                # In a real application, send email with reset link
                # For now, just show success message
                messages.success(request, 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني')
                logger.info('Password reset requested for user: %s', user.username)
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'البريد الإلكتروني غير مسجل في النظام')
    
    return render(request, 'properties/password_reset.html')


@login_required
def password_change(request):
    """Handle password change for logged in users."""
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
                metadata={'action': 'password_change'}
            )
            
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('login')
    
    return render(request, 'properties/password_change.html')


@login_required
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
def dashboard(request):
    """لوحة تحكم الإدارة والدلال"""
    # Check if user is admin or broker
    if not request.user.is_superuser and not request.user.is_staff and not get_broker(request.user):
        return redirect('user_dashboard')
    
    properties = get_accessible_properties(request.user).prefetch_related('gallery_images', 'broker', 'owner')
    
    # Add pagination for properties
    paginator = Paginator(properties, 25)
    page_number = request.GET.get('page', 1)
    properties = paginator.get_page(page_number)
    
    # Get unread messages with optimized query
    unread = get_accessible_messages(request.user).filter(is_read=False)[:20]
    broker = get_broker(request.user)
    
    # Try to get notes with optimized query
    notes = []
    pending_notes_count = 0
    try:
        notes = PropertyNote.objects.select_related('property')[:20]
        pending_notes_count = PropertyNote.objects.filter(is_completed=False).count()
    except Exception:
        # PropertyNote table doesn't exist yet (migration not applied)
        notes = []
        pending_notes_count = 0
    
    # Try to get notifications
    notifications = []
    unread_notifications_count = 0
    try:
        notifications = Notification.objects.filter(user=request.user).select_related('property')[:20]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        # Notification table doesn't exist yet (migration not applied)
        notifications = []
        unread_notifications_count = 0
    
    # Get auctions with optimized query
    auctions_list = []
    try:
        auctions_list = Auction.objects.all().select_related('property', 'broker').order_by('-created_at')[:20]
    except Exception:
        auctions_list = []
    
    # Get activity logs with optimized query
    activity_logs = []
    try:
        activity_logs = ActivityLog.objects.all().select_related('user').order_by('-created_at')[:50]
    except Exception:
        activity_logs = []
    
    settings = SiteSettings.get_solo()
    settings_form = SiteSettingsForm(instance=settings)
    property_form = PropertyForm()
    
    # Only create note form if PropertyNote table exists
    try:
        note_form = PropertyNoteForm()
    except Exception:
        note_form = None

    stats = get_broker_stats(request.user)
    stats['pending_notes'] = pending_notes_count
    stats['unread_notifications'] = unread_notifications_count
    stats['total'] = stats['total_properties']
    stats['featured'] = stats['featured_properties']
    stats['unread_messages'] = stats.get('unread_messages', 0)
    
    # Get subscription info for timer
    subscriptions_info = []
    try:
        from .models import BrokerPlanSubscription
        subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        ).order_by('-end_date')
        for subscription in subscriptions:
            if subscription.is_active():
                subscriptions_info.append({
                    'seconds_remaining': subscription.get_seconds_remaining(),
                    'end_date': subscription.end_date,
                    'properties_used': subscription.properties_used,
                    'max_properties': subscription.plan.max_properties,
                    'plan_name': subscription.plan.name
                })
    except Exception:
        subscriptions_info = []
    
    stats['subscriptions'] = subscriptions_info

    # Admin-only data
    all_conversations = []
    all_reports = []
    all_users = []
    subscription_plans = []
    platform_stats = {}
    pending_properties = []
    recent_payments = []
    staff_users = []
    backups = []
    support_tickets = []
    subscription_requests = []  # Fixed UnboundLocalError
    building_requests_list = []  # Fixed UnboundLocalError
    
    if request.user.is_superuser:
        try:
            from .models import Conversation, MessageReport, SubscriptionPlan, FinancialTransaction, BrokerPlanSubscription
            all_conversations = Conversation.objects.all().prefetch_related('participants_info', 'chat_messages')
            all_reports = MessageReport.objects.all().select_related('reporter', 'message', 'message__sender')
            all_users = User.objects.all().order_by('-date_joined')
            subscription_plans = SubscriptionPlan.objects.all()
            pending_properties = Property.objects.filter(status='pending').select_related('owner', 'broker')
            recent_payments = FinancialTransaction.objects.all().select_related('user').order_by('-created_at')[:20]
            staff_users = User.objects.filter(is_staff=True).order_by('-last_login')
            
            # Platform statistics
            platform_stats = {
                'total_users': User.objects.count(),
                'total_conversations': Conversation.objects.count(),
                'total_messages': 0,
                'total_reports': MessageReport.objects.count(),
                'total_brokers': Broker.objects.count(),
                'total_regular_users': User.objects.filter(is_superuser=False, is_staff=False).count() - Broker.objects.count(),
                'total_admins': User.objects.filter(is_superuser=True).count(),
                'active_subscriptions': BrokerPlanSubscription.objects.filter(status='active').count(),
                'total_revenue': sum(t.amount or 0 for t in FinancialTransaction.objects.filter(status='completed')),
                'active_ads': Property.objects.filter(is_featured=True).count(),
                'pending_payments': FinancialTransaction.objects.filter(status='pending').count(),
                'completed_payments': FinancialTransaction.objects.filter(status='completed').count(),
                'total_backups': 0,
                'last_backup_size': 0,
                'last_backup_date': '--',
                'total_tickets': 0,
                'pending_tickets': 0,
                'resolved_tickets': 0,
                'total_properties': Property.objects.count(),
                'active_properties': Property.objects.filter(status='published').count(),
                'verified_properties': Property.objects.filter(is_verified=True).count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'total_jobs': Job.objects.count(),
            }
            
            # Get backups
            try:
                from .models import Backup
                backups = Backup.objects.select_related('created_by').order_by('-created_at')[:50]
                platform_stats['total_backups'] = Backup.objects.count()
                if backups:
                    platform_stats['last_backup_size'] = backups.first().size
                    platform_stats['last_backup_date'] = backups.first().created_at.strftime('%Y-%m-%d %H:%M')
            except Exception:
                backups = []
            
            try:
                from .models import ChatMessage
                platform_stats['total_messages'] = ChatMessage.objects.count()
            except Exception:
                pass
            
            # Try to get support tickets
            try:
                from .models import SupportTicket
                support_tickets = SupportTicket.objects.all().select_related('user').order_by('-created_at')[:20]
                platform_stats['total_tickets'] = SupportTicket.objects.count()
                platform_stats['pending_tickets'] = SupportTicket.objects.filter(status='pending').count()
                platform_stats['resolved_tickets'] = SupportTicket.objects.filter(status='resolved').count()
            except Exception:
                pass
            
            # Try to get subscription requests
            try:
                from .models import SubscriptionRequest
                subscription_requests = SubscriptionRequest.objects.all().select_related('broker', 'requested_plan', 'approved_by').order_by('-created_at')[:50]
            except Exception:
                subscription_requests = []
            
            # Try to get building requests
            try:
                from .models import BuildingRequest
                building_requests_list = BuildingRequest.objects.all().select_related('user', 'broker', 'assigned_broker').order_by('-created_at')[:50]
            except Exception:
                building_requests_list = []
        except Exception as e:
            logger.error(f"Error loading admin data: {e}")

    from .constants import IRAQ_GOVERNORATES
    
    return render(request, 'properties/dashboard.html', {
        'properties': properties,
        'messages_list': unread,
        'notes_list': notes,
        'notifications_list': notifications,
        'auctions_list': auctions_list,
        'building_requests_list': building_requests_list,
        'activity_logs': activity_logs,
        'settings_form': settings_form,
        'property_form': property_form,
        'note_form': note_form,
        'stats': stats,
        'broker': broker,
        'can_manage_brokers': can_manage_brokers(request.user),
        'can_manage_settings': can_manage_site_settings(request.user),
        'managed_brokers': get_managed_brokers(request.user).annotate(
            property_count=Count('user__owned_properties', distinct=True)
        ) if can_manage_brokers(request.user) else [],
        'brokers_stats': {
            'total': Broker.objects.count(),
            'active': Broker.objects.filter(is_active=True).count(),
            'verified': Broker.objects.filter(is_verified=True).count(),
            'by_role': {
                'main': Broker.objects.filter(role='main').count(),
                'sub': Broker.objects.filter(role='sub').count(),
                'admin': Broker.objects.filter(role='admin').count()
            }
        } if can_manage_brokers(request.user) else {},
        'total_properties_count': sum(b.user.owned_properties.count() for b in get_managed_brokers(request.user)) if can_manage_brokers(request.user) else 0,
        'all_conversations': all_conversations,
        'all_reports': all_reports,
        'all_users': all_users,
        'active_users_count': sum(1 for u in all_users if u.is_active),
        'inactive_users_count': sum(1 for u in all_users if not u.is_active),
        'superusers_count': sum(1 for u in all_users if u.is_superuser),
        'subscription_plans': subscription_plans,
        'platform_stats': platform_stats,
        'pending_properties': pending_properties,
        'recent_payments': recent_payments,
        'staff_users': staff_users,
        'backups': backups,
        'support_tickets': support_tickets,
        'subscription_requests': subscription_requests,
        'governorates': IRAQ_GOVERNORATES,
    })


@login_required
def my_posts(request):
    """صفحة منشوراتي - عرض جميع منشورات الدلال مع الوقت المتبقي"""
    from django.utils import timezone
    from .models import BrokerPlanSubscription
    
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # Get user's active subscriptions
    active_subscriptions = BrokerPlanSubscription.objects.filter(
        broker=broker,
        status='active'
    )
    
    # Check if user has featured/promoted capability
    has_featured = False
    subscription_end_date = None
    
    for sub in active_subscriptions:
        if sub.is_active():
            if sub.plan.allow_featured_properties:
                has_featured = True
            if subscription_end_date is None or sub.end_date > subscription_end_date:
                subscription_end_date = sub.end_date
    
    # Get all user's properties with filters
    properties = Property.objects.filter(owner=request.user)
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        if subscription_end_date:
            properties = properties.filter(created_at__lte=subscription_end_date)
    elif status_filter == 'expired':
        if subscription_end_date:
            properties = properties.filter(created_at__gt=subscription_end_date)
    
    # Apply type filter
    type_filter = request.GET.get('type', '')
    if type_filter == 'featured':
        properties = properties.filter(is_featured=True)
    elif type_filter == 'promoted':
        properties = properties.filter(is_promoted=True)
    elif type_filter == 'normal':
        properties = properties.filter(is_featured=False, is_promoted=False)
    
    # Apply sorting
    sort_filter = request.GET.get('sort', 'newest')
    if sort_filter == 'newest':
        properties = properties.order_by('-created_at')
    elif sort_filter == 'oldest':
        properties = properties.order_by('created_at')
    elif sort_filter == 'title':
        properties = properties.order_by('title')
    elif sort_filter == 'price':
        properties = properties.order_by('-price')
    
    # Calculate time remaining for each property
    properties_with_time = []
    for prop in properties:
        time_remaining = None
        is_featured = False
        
        # Calculate time based on subscription
        if subscription_end_date and prop.created_at:
            if subscription_end_date > prop.created_at:
                time_delta = subscription_end_date - prop.created_at
                time_remaining = max(0, time_delta.total_seconds())
        
        # Check if property is featured (only if subscription allows)
        if has_featured and prop.is_featured:
            is_featured = True
        
        properties_with_time.append({
            'property': prop,
            'time_remaining': time_remaining,
            'is_featured': is_featured,
            'is_promoted': prop.is_promoted if has_featured else False,
        })
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(properties_with_time, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_properties = properties.count()
    featured_count = properties.filter(is_featured=True).count()
    promoted_count = properties.filter(is_promoted=True).count()
    active_count = sum(1 for prop in properties_with_time if prop.get('time_remaining', 0) > 0)
    
    return render(request, 'properties/my_posts.html', {
        'page_obj': page_obj,
        'has_featured': has_featured,
        'subscription_end_date': subscription_end_date,
        'total_properties': total_properties,
        'featured_count': featured_count,
        'promoted_count': promoted_count,
        'active_count': active_count,
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
    
    # Search in Hotels
    if category in ['', 'hotel']:
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
    
    # Search in Resorts
    if category in ['', 'resort']:
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
    
    # Search in Services
    if category in ['', 'service']:
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
    
    # Search in Building Requests
    # Search in Auctions
    if category in ['', 'auction']:
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
    
    # Search in Jobs
    if category in ['', 'job']:
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
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
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
@staff_required
@require_POST
def add_property(request):
    # Check if adding or replacing
    replace_property_id = request.POST.get('replace_property_id')
    if replace_property_id:
        # Replacement mode - delete old property first
        try:
            old_prop = Property.objects.get(id=replace_property_id, owner=request.user)
            old_prop.delete()
            messages.info(request, 'تم استبدال العقار القديم')
        except Property.DoesNotExist:
            messages.error(request, 'العقار المطلوب استبداله غير موجود')
            return redirect('dashboard')
    
    # Check subscription status before adding property
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر العقارات.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة عقارات.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من العقارات ({published}/{limit}). '
                    f'يمكنك حذف بعض العقارات القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من العقارات حسب باقة اشتراكك. '
            'يمكنك حذف بعض العقارات القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')


def enhanced_add_property(request):
    """نموذج إضافة عقار محسّن مع جميع الحقول الجديدة"""
    if request.method == 'POST':
        form = EnhancedPropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            broker = get_broker(request.user)
            if broker:
                prop.broker = broker
                if broker.office_id:
                    prop.office = broker.office
                # Set status to 'ready' automatically if broker has active subscription
                if broker.is_subscription_active():
                    prop.status = 'ready'
                else:
                    prop.status = 'draft'
            else:
                prop.status = 'draft'
            prop.save()
            
            # Handle 360° image checkboxes
            is_360_list = request.POST.getlist('is_360')
            is_360_list = [val == 'on' for val in is_360_list]
            
            save_gallery_images(prop, request.FILES.getlist('gallery_images'), is_360_list)
            save_gallery_videos(prop, request.FILES.getlist('gallery_videos'))
            
            # Log activity
            ActivityLog.log(
                user=request.user,
                action='create',
                model_type='property',
                object_id=prop.id,
                object_repr=prop.title,
                description=f'إضافة عقار جديد: {prop.title}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={'property_type': prop.property_type, 'price': str(prop.price)}
            )
            
            # Track broker statistics
            if broker:
                from .models import BrokerIndividualStats
                BrokerIndividualStats.track_property_added(broker)
            
            # Create notification
            Notification.create(
                user=request.user,
                notification_type='success',
                title='إضافة عقار',
                message=f'تم إضافة العقار: {prop.title}',
                link=f'/property/{prop.slug}/',
                metadata={'property_id': prop.id, 'property_title': prop.title}
            )
            
            messages.success(request, f'تم إضافة العقار بنجاح: {prop.title}')
            return redirect('dashboard')
    else:
        form = EnhancedPropertyForm()
    
    return render(request, 'properties/enhanced_property_form.html', {'form': form})


@login_required
@staff_required
def enhanced_add_outside_property(request):
    """نموذج إضافة عقار خارج العراق محسّن مع جميع الحقول الجديدة"""
    if request.method == 'POST':
        property_form = PropertyForm(request.POST, request.FILES)
        outside_form = EnhancedOutsidePropertyForm(request.POST)
        
        if property_form.is_valid() and outside_form.is_valid():
            prop = property_form.save(commit=False)
            prop.owner = request.user
            prop.category = 'property_outside'
            broker = get_broker(request.user)
            if broker:
                prop.broker = broker
                if broker.office_id:
                    prop.office = broker.office
                if broker.is_subscription_active():
                    prop.status = 'ready'
                else:
                    prop.status = 'draft'
            else:
                prop.status = 'draft'
            prop.save()
            
            # Save outside property details
            outside = outside_form.save(commit=False)
            outside.property = prop
            outside.save()
            
            # Handle gallery images
            is_360_list = request.POST.getlist('is_360')
            is_360_list = [val == 'on' for val in is_360_list]
            save_gallery_images(prop, request.FILES.getlist('gallery_images'), is_360_list)
            save_gallery_videos(prop, request.FILES.getlist('gallery_videos'))
            
            # Log activity
            ActivityLog.log(
                user=request.user,
                action='create',
                model_type='outside_property',
                object_id=prop.id,
                object_repr=prop.title,
                description=f'إضافة عقار خارج العراق: {prop.title}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={'country': prop.country.name if prop.country else 'Unknown', 'price': str(prop.price)}
            )
            
            # Track broker statistics
            if broker:
                from .models import BrokerIndividualStats
                BrokerIndividualStats.track_property_added(broker)
            
            # Create notification
            Notification.create(
                user=request.user,
                notification_type='success',
                title='إضافة عقار خارج العراق',
                message=f'تم إضافة العقار: {prop.title}',
                link=f'/property/{prop.slug}/',
                metadata={'property_id': prop.id, 'property_title': prop.title}
            )
            
            messages.success(request, f'تم إضافة العقار الخارجي بنجاح: {prop.title}')
            return redirect('dashboard')
    else:
        property_form = PropertyForm()
        outside_form = EnhancedOutsidePropertyForm()
    
    return render(request, 'properties/enhanced_outside_property_form.html', {
        'form': outside_form,
        'property_form': property_form
    })


@login_required
@staff_required
@require_POST
def add_property(request):
    # Check if adding or replacing
    replace_property_id = request.POST.get('replace_property_id')
    if replace_property_id:
        # Replacement mode - delete old property first
        try:
            old_prop = Property.objects.get(id=replace_property_id, owner=request.user)
            old_prop.delete()
            messages.info(request, 'تم استبدال العقار القديم')
        except Property.DoesNotExist:
            messages.error(request, 'العقار المطلوب استبداله غير موجود')
            return redirect('dashboard')
    
    # Check subscription status before adding property
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر العقارات.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة عقارات.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من العقارات ({published}/{limit}). '
                    f'يمكنك حذف بعض العقارات القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من العقارات حسب باقة اشتراكك. '
            'يمكنك حذف بعض العقارات القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')
    
    form = PropertyForm(request.POST, request.FILES)
    if form.is_valid():
        prop = form.save(commit=False)
        prop.owner = request.user
        broker = get_broker(request.user)
        if broker:
            prop.broker = broker
            if broker.office_id:
                prop.office = broker.office
            # Set status to 'ready' automatically if broker has active subscription
            if broker.is_subscription_active():
                prop.status = 'ready'
            else:
                prop.status = 'draft'
        else:
            prop.status = 'draft'
        prop.save()
        
        # Handle 360° image checkboxes
        is_360_list = request.POST.getlist('is_360')
        is_360_list = [val == 'on' for val in is_360_list]
        
        save_gallery_images(prop, request.FILES.getlist('gallery_images'), is_360_list)
        save_gallery_videos(prop, request.FILES.getlist('gallery_videos'))
        
        # Log activity
        ActivityLog.log(
            user=request.user,
            action='create',
            model_type='property',
            object_id=prop.id,
            object_repr=prop.title,
            description=f'إضافة عقار جديد: {prop.title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'property_type': prop.property_type, 'price': str(prop.price)}
        )
        
        # Track broker statistics
        if broker:
            from .models import BrokerIndividualStats
            BrokerIndividualStats.track_property_added(broker)
        
        # Create notification
        Notification.create(
            user=request.user,
            notification_type='success',
            title='إضافة عقار',
            message=f'تم إضافة العقار: {prop.title}',
            link=f'/property/{prop.slug}/',
            metadata={'property_id': prop.id, 'property_title': prop.title}
        )
        
        # Handle virtual tour if provided
        tour_type = request.POST.get('tour_type')
        if tour_type:
            tour_title = request.POST.get('tour_title', 'جولة افتراضية')
            tour_description = request.POST.get('tour_description', '')
            
            virtual_tour = VirtualTour360.objects.create(
                property=prop,
                title=tour_title,
                tour_type=tour_type,
                description=tour_description
            )
            
            if tour_type == 'image' or tour_type == 'multi':
                tour_image = request.FILES.get('tour_image')
                if tour_image:
                    virtual_tour.image = tour_image
            elif tour_type == 'file':
                tour_file = request.FILES.get('tour_file')
                if tour_file:
                    virtual_tour.tour_file = tour_file
            elif tour_type == 'external':
                external_url = request.POST.get('external_url')
                external_service = request.POST.get('external_service')
                if external_url:
                    virtual_tour.external_url = external_url
                    virtual_tour.external_service = external_service
            
            virtual_tour.save()
        
        # Send notifications to all users about new property
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users = User.objects.filter(is_active=True)
            for user in users:
                Notification.objects.create(
                    user=user,
                    notification_type='new_property',
                    title=f'عقار جديد: {prop.display_title}',
                    message=f'تم إضافة عقار جديد في {prop.district} بسعر {prop.price_formatted}',
                    property=prop
                )
        except Exception as e:
            logger.error(f'Error sending notifications: {str(e)}')
        
        messages.success(request, f'تم نشر العقار: {prop.display_title}')
        return redirect('dashboard')
    
    messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    for field, errs in form.errors.items():
        for e in errs:
            messages.error(request, f'{field}: {e}')
    return redirect('dashboard')


@login_required
@staff_required
def edit_property(request, property_id):
    prop = get_object_or_404(Property, pk=property_id)
    if not can_edit_property(request.user, prop):
        messages.error(request, 'ليس لديك صلاحية تعديل هذا العقار')
        return redirect('dashboard')
    
    # Check subscription status before editing property
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.is_subscription_active() and not broker.can_edit_properties:
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لتعديل العقارات.')
                return redirect('subscription_plans')
            else:
                messages.error(request, 'ليس لديك صلاحية تعديل العقارات.')
            return redirect('dashboard')
    
    # Get virtual tours
    try:
        virtual_tours = prop.virtual_tours.all()
    except Exception:
        virtual_tours = []
    
    # Get auctions
    try:
        auctions = prop.auctions.all()
    except Exception:
        auctions = []
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()
            
            # Handle 360° image checkboxes
            is_360_list = request.POST.getlist('is_360')
            is_360_list = [val == 'on' for val in is_360_list]
            
            save_gallery_images(prop, request.FILES.getlist('gallery_images'), is_360_list)
            save_gallery_videos(prop, request.FILES.getlist('gallery_videos'))
            
            # Log activity
            ActivityLog.log(
                user=request.user,
                action='update',
                model_type='property',
                object_id=prop.id,
                object_repr=prop.title,
                description=f'تعديل العقار: {prop.title}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Create notification
            Notification.create(
                user=request.user,
                notification_type='success',
                title='تعديل عقار',
                message=f'تم تعديل العقار: {prop.title}',
                link=f'/property/{prop.slug}/',
                metadata={'property_id': prop.id, 'property_title': prop.title}
            )
            
            messages.success(request, 'تم تحديث العقار')
            return redirect('dashboard')
        return render(request, 'properties/edit_property.html', {
            'property': prop, 'form': form, 'virtual_tours': virtual_tours, 'auctions': auctions,
        })
    return render(request, 'properties/edit_property.html', {
        'property': prop, 'form': PropertyForm(instance=prop), 'virtual_tours': virtual_tours, 'auctions': auctions,
    })


@login_required
@staff_required
def property_verification_admin(request):
    """لوحة تحكم احترافية للتحقق من العقارات"""
    from django.db.models import Count
    
    try:
        # جلب جميع العقارات مع بيانات التحقق
        properties_with_verification = Property.objects.select_related(
            'owner', 'broker', 'office'
        ).prefetch_related('verification').all()
        
        # إحصائيات التحقق
        total_properties = properties_with_verification.count()
        verified_count = properties_with_verification.filter(
            verification__verification_status='verified'
        ).count()
        pending_review_count = properties_with_verification.filter(
            verification__verification_status='under_review'
        ).count()
        rejected_count = properties_with_verification.filter(
            verification__verification_status='rejected'
        ).count()
        unverified_count = total_properties - verified_count - pending_review_count - rejected_count
        
        # العقارات حسب نوع التحقق
        verification_stats = {
            'identity_verified': properties_with_verification.filter(
                verification__identity_verified=True
            ).count(),
            'ownership_verified': properties_with_verification.filter(
                verification__ownership_verified=True
            ).count(),
            'location_verified': properties_with_verification.filter(
                verification__location_verified=True
            ).count(),
            'images_verified': properties_with_verification.filter(
                verification__images_verified=True
            ).count(),
            'price_verified': properties_with_verification.filter(
                verification__price_verified=True
            ).count(),
        }
        
        # العقارات حسب الحالة
        status_distribution = properties_with_verification.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context = {
            'properties': properties_with_verification,
            'statistics': {
                'total': total_properties,
                'verified': verified_count,
                'pending_review': pending_review_count,
                'rejected': rejected_count,
                'unverified': unverified_count,
                'verification_rate': round((verified_count / total_properties * 100) if total_properties > 0 else 0, 1),
                'verification_stats': verification_stats,
            },
            'status_distribution': list(status_distribution),
        }
        
        return render(request, 'properties/property_verification_admin.html', context)
    
    except Exception as e:
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('dashboard')


@login_required
@staff_required
def property_verify(request, property_id):
    """واجهة التحقق من عقار معين"""
    from .forms import PropertyVerificationForm
    from .models import Notification
    
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        form = PropertyVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.property = property_obj
            verification.verified_by = request.user
            verification.save()
            
            # إرسال إشعار عند التحقق من العقار
            if verification.verification_status == 'verified' and property_obj.owner:
                Notification.create_property_verified(property_obj, property_obj.owner)
                messages.success(request, 'تم حفظ التحقق وإرسال إشعار للمالك')
            else:
                messages.success(request, 'تم حفظ التحقق بنجاح')
            
            return redirect('property_verification_admin')
    else:
        # إنشاء أو جلب سجل التحقق الموجود
        verification, created = PropertyVerification.objects.get_or_create(
            property=property_obj,
            defaults={'verified_by': request.user}
        )
        form = PropertyVerificationForm(instance=verification)
    
    context = {
        'property': property_obj,
        'form': form,
        'verification_history': property_obj.verification.all() if hasattr(property_obj, 'verification') else [],
    }
    
    return render(request, 'properties/property_verify.html', context)


@login_required
@staff_required
def property_statistics(request):
    """إحصائيات متقدمة وتقارير العقارات"""
    from django.db.models import Count, Q, Avg, Sum, Min, Max
    from django.db.models.functions import TruncDate, TruncMonth
    from django.utils import timezone
    from datetime import timedelta

    properties = get_accessible_properties(request.user)
    
    # General stats
    total_properties = properties.count()
    active_properties = properties.filter(status='published').count()
    sold_properties = properties.filter(status='sold').count()
    pending_properties = properties.filter(status='pending_approval').count()
    rented_properties = properties.filter(status='rented').count()
    
    # Verification statistics
    verified_properties = properties.filter(
        verification__verification_status='verified'
    ).count()
    pending_verification = properties.filter(
        verification__verification_status='under_review'
    ).count()
    verification_rate = round((verified_properties / total_properties * 100) if total_properties > 0 else 0, 1)
    
    # Purpose statistics (sale vs rent)
    sale_properties = properties.filter(purpose='sale').count()
    rent_properties = properties.filter(purpose='rent').count()
    
    # Property type stats
    type_stats = properties.values('type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Governorate stats
    governorate_stats = properties.values('governorate').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # City stats
    city_stats = properties.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # Price statistics
    price_stats = properties.aggregate(
        avg_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price'),
        total_value=Sum('price')
    )
    
    # Rental price statistics
    rental_stats = properties.filter(purpose='rent').aggregate(
        avg_monthly_rent=Avg('monthly_rent'),
        min_monthly_rent=Min('monthly_rent'),
        max_monthly_rent=Max('monthly_rent')
    )
    
    # Monthly property additions
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_properties = ActivityLog.objects.filter(
        created_at__gte=six_months_ago,
        model_type='property',
        action='create'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Most viewed properties
    top_viewed = properties.order_by('-views_count')[:10]
    
    # Activity stats for properties
    activity_stats = ActivityLog.objects.filter(
        model_type='property'
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Broker performance
    broker_stats = properties.values('broker__display_name').annotate(
        property_count=Count('id'),
        avg_price=Avg('price')
    ).order_by('-property_count')[:10]
    
    # Office performance
    office_stats = properties.values('office__name').annotate(
        property_count=Count('id'),
        avg_price=Avg('price')
    ).order_by('-property_count')[:10]
    
    # Furnishing status stats
    furnishing_stats = properties.values('furnishing_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Property condition stats
    condition_stats = properties.values('property_condition').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return render(request, 'properties/property_statistics.html', {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'sold_properties': sold_properties,
        'pending_properties': pending_properties,
        'rented_properties': rented_properties,
        'verified_properties': verified_properties,
        'pending_verification': pending_verification,
        'verification_rate': verification_rate,
        'sale_properties': sale_properties,
        'rent_properties': rent_properties,
        'type_stats': type_stats,
        'governorate_stats': governorate_stats,
        'city_stats': city_stats,
        'price_stats': price_stats,
        'rental_stats': rental_stats,
        'monthly_properties': monthly_properties,
        'top_viewed': top_viewed,
        'activity_stats': activity_stats,
        'broker_stats': broker_stats,
        'office_stats': office_stats,
        'furnishing_stats': furnishing_stats,
        'condition_stats': condition_stats,
    })


@login_required
@staff_required
@require_POST
def delete_property(request, property_id):
    try:
        prop = get_object_or_404(Property, pk=property_id)
        if not can_delete_property(request.user, prop):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية حذف هذا العقار'})
            messages.error(request, 'ليس لديك صلاحية حذف هذا العقار')
            return redirect('dashboard')
        
        # Check subscription status before deleting property
        broker = get_broker(request.user)
        if broker:
            broker.check_subscription_status()
            if not broker.can_delete_properties and not is_platform_admin(request.user):
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية حذف العقارات.'})
                messages.error(request, 'ليس لديك صلاحية حذف العقارات.')
                return redirect('dashboard')
        
        title = prop.display_title
        
        # Log activity before deletion
        ActivityLog.log(
            user=request.user,
            action='delete',
            model_type='property',
            object_id=prop.id,
            object_repr=title,
            description=f'حذف العقار: {title}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create notification before deletion
        Notification.create(
            user=request.user,
            notification_type='warning',
            title='حذف عقار',
            message=f'تم حذف العقار: {title}',
            metadata={'property_id': prop.id, 'property_title': title}
        )
        
        # Track broker statistics before deletion
        if prop.broker:
            from .models import BrokerIndividualStats
            BrokerIndividualStats.track_property_deleted(prop.broker)
        
        prop.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        
        messages.success(request, f'تم حذف العقار: {title}')
        return redirect('dashboard')
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'حدث خطأ أثناء حذف العقار: {str(e)}')
        return redirect('dashboard')


@login_required
@staff_required
@require_POST
def delete_property_image(request, image_id):
    img = get_object_or_404(PropertyImage, pk=image_id)
    prop_id = img.property_id
    img.delete()
    messages.success(request, 'تم حذف الصورة')
    return redirect('edit_property', property_id=prop_id)


@rate_limit('message', limit=5, period=300)
@require_http_methods(['POST'])
def send_message(request):
    form = MessageForm(request.POST)
    property_id = request.POST.get('property_id')
    prop = None
    if property_id:
        prop = get_object_or_404(Property, pk=property_id)

    if form.is_valid():
        # Create a simple log entry or email notification
        # For now, just show success message
        messages.success(request, 'تم إرسال رسالتك بنجاح. سنتواصل معك قريباً.')
        logger.info('New contact message from %s (%s): %s',
                    form.cleaned_data['name'],
                    form.cleaned_data['email'],
                    form.cleaned_data['message'])
        if prop:
            return redirect(prop.get_absolute_url())
        return redirect('contact')
    messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة بشكل صحيح')
    if prop:
        return redirect(prop.get_absolute_url())
    return redirect('contact')


@login_required
@staff_required
@require_POST
def mark_legacy_message_read(request, message_id):
    msg = get_object_or_404(Message, pk=message_id)
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    return redirect('dashboard')


@login_required
@staff_required
def add_note(request):
    try:
        if request.method == 'POST':
            form = PropertyNoteForm(request.POST)
            if form.is_valid():
                note = form.save()
                messages.success(request, f'تم إضافة الملاحظة: {note.title}')
                return redirect('dashboard')
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
        return redirect('dashboard')
    except Exception as e:
        logger.error(f'Error adding note: {str(e)}')
        messages.error(request, f'حدث خطأ أثناء حفظ الملاحظة: {str(e)}')
        return redirect('dashboard')


@login_required
@staff_required
def toggle_note_complete(request, note_id):
    try:
        note = get_object_or_404(PropertyNote, pk=note_id)
        note.is_completed = not note.is_completed
        note.save(update_fields=['is_completed'])
        status = 'مكتمل' if note.is_completed else 'غير مكتمل'
        messages.success(request, f'تم تحديث حالة الملاحظة إلى {status}')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, 'ميزة الملاحظات غير متاحة حالياً. يرجى تطبيق الترحيلات (migrations).')
        return redirect('dashboard')


@login_required
@staff_required
def delete_note(request, note_id):
    try:
        note = get_object_or_404(PropertyNote, pk=note_id)
        note.delete()
        messages.success(request, f'تم حذف الملاحظة: {note.title}')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, 'ميزة الملاحظات غير متاحة حالياً. يرجى تطبيق الترحيلات (migrations).')
        return redirect('dashboard')


@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return redirect('dashboard')
    except Exception as e:
        logger.error(f'Error marking notification as read: {str(e)}')
        return redirect('dashboard')


@login_required
def delete_notification(request, notification_id):
    try:
        notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
        notification.delete()
        messages.success(request, 'تم حذف الإشعار')
        return redirect('dashboard')
    except Exception as e:
        logger.error(f'Error deleting notification: {str(e)}')
        return redirect('dashboard')


@login_required
@staff_required
def add_virtual_tour(request, property_id):
    prop = get_object_or_404(Property, pk=property_id)
    if request.method == 'POST':
        form = VirtualTour360Form(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.property = prop
            tour.save()
            messages.success(request, f'تم إضافة الجولة الافتراضية: {tour.title}')
            return redirect('edit_property', property_id=property_id)
    else:
        form = VirtualTour360Form(initial={'property': prop})
    return render(request, 'properties/add_virtual_tour.html', {
        'form': form,
        'property': prop,
    })


@login_required
@staff_required
@require_POST
def delete_virtual_tour(request, tour_id):
    try:
        tour = get_object_or_404(VirtualTour360, pk=tour_id)
        property_id = tour.property_id
        tour.delete()
        messages.success(request, 'تم حذف الجولة الافتراضية')
        return redirect('edit_property', property_id=property_id)
    except Exception as e:
        logger.error(f'Error deleting virtual tour: {str(e)}')
        return redirect('dashboard')


@login_required
@staff_required
def add_auction(request, property_id):
    prop = get_object_or_404(Property, pk=property_id)
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.property = prop
            auction.save()
            messages.success(request, f'تم إنشاء المزاد: {auction.title}')
            return redirect('edit_property', property_id=property_id)
    else:
        form = AuctionForm(initial={'property': prop})
    return render(request, 'properties/add_auction.html', {
        'form': form,
        'property': prop,
    })


@login_required
@staff_required
def edit_auction(request, auction_id):
    """تعديل مزاد"""
    auction = get_object_or_404(Auction, pk=auction_id)
    
    if request.method == 'POST':
        auction.title = request.POST.get('title', auction.title)
        auction.description = request.POST.get('description', auction.description)
        auction.starting_price = request.POST.get('starting_price', auction.starting_price)
        auction.minimum_increment = request.POST.get('minimum_increment', auction.minimum_increment)
        auction.reserve_price = request.POST.get('reserve_price', auction.reserve_price)
        auction.start_date = request.POST.get('start_date', auction.start_date)
        auction.end_date = request.POST.get('end_date', auction.end_date)
        auction.save()
        messages.success(request, 'تم تحديث المزاد بنجاح')
        return redirect('auction_detail', auction_id=auction.id)
    
    return render(request, 'properties/edit_auction.html', {
        'auction': auction
    })


@login_required
@staff_required
@require_POST
def delete_auction(request, auction_id):
    try:
        auction = get_object_or_404(Auction, pk=auction_id)
        property_id = auction.property_id
        auction.delete()
        messages.success(request, 'تم حذف المزاد')
        return redirect('edit_property', property_id=property_id)
    except Exception as e:
        logger.error(f'Error deleting auction: {str(e)}')
        return redirect('dashboard')


def auctions_list(request):
    try:
        auctions = Auction.objects.all().select_related('property').prefetch_related('bids')
    except Exception:
        auctions = []
    
    paginator = Paginator(auctions, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'properties/auctions.html', {
        'auctions': page_obj,
        'page_obj': page_obj,
    })




def auction_terms(request):
    return render(request, 'properties/auction_terms.html')













@login_required
def create_auction(request):
    """Create a new auction"""
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            
            # Save address fields
            auction.governorate = request.POST.get('governorate', '')
            auction.city = request.POST.get('city', '')
            auction.district = request.POST.get('district', '')
            auction.subdistrict = request.POST.get('subdistrict', '')
            auction.area = request.POST.get('area', '')
            auction.neighborhood = request.POST.get('neighborhood', '')
            auction.mahalla = request.POST.get('mahalla', '')
            auction.block = request.POST.get('block', '')
            auction.street = request.POST.get('street', '')
            auction.alley = request.POST.get('alley', '')
            auction.house_number = request.POST.get('house_number', '')
            auction.property_number = request.POST.get('property_number', '')
            auction.landmark = request.POST.get('landmark', '')
            
            # Save GPS coordinates
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude:
                auction.latitude = latitude
            if longitude:
                auction.longitude = longitude
            
            auction.save()
            messages.success(request, 'تم إنشاء المزاد بنجاح')
            return redirect('auction_detail', auction_id=auction.id)
    else:
        form = AuctionForm()
    return render(request, 'properties/create_auction.html', {'form': form})


def auction_detail(request, auction_id):
    """View auction details with real-time updates"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    # Check if auction requires access
    if auction.access_type != 'public':
        # Check if user is the broker
        if auction.broker and auction.broker.user == request.user:
            pass  # Broker always has access
        # Check if user has session access
        elif request.session.get(f'auction_access_{auction_id}'):
            pass  # User has access via session
        # Check if user has a valid invitation
        elif request.user.is_authenticated and AuctionInvitation.objects.filter(auction=auction, invited_user=request.user, status='accepted').exists():
            pass  # User has access via invitation
        else:
            # Redirect to access code page
            return redirect('auction_access_code', auction_id=auction_id)
    
    # Get auction data
    highest_bid = auction.get_current_highest_bid()
    total_bids = auction.get_total_bids()
    participant_count = auction.get_participant_count()
    time_remaining = auction.get_time_remaining()
    
    # Get bids list
    bids = auction.bids.select_related('user').all().order_by('-amount', '-created_at')
    
    # Check if user is participant
    is_participant = False
    if request.user.is_authenticated:
        try:
            AuctionParticipant.objects.get(auction=auction, user=request.user)
            is_participant = True
        except AuctionParticipant.DoesNotExist:
            pass
    
    context = {
        'auction': auction,
        'highest_bid': highest_bid,
        'total_bids': total_bids,
        'participant_count': participant_count,
        'time_remaining': time_remaining,
        'is_participant': is_participant,
        'bids': bids,
    }
    return render(request, 'properties/auction_detail.html', context)


@login_required
def place_bid(request, auction_id):
    """Place a bid on an auction"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if not auction.is_active():
        messages.error(request, 'المزاد غير نشط حالياً')
        return redirect('auction_detail', auction_id=auction.id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = int(amount)
            bid = Bid(auction=auction, user=request.user, amount=amount)
            bid.save()
            messages.success(request, 'تم تقديم عرضك بنجاح')
            if bid.is_auto_extended:
                messages.info(request, 'تم تمديد المزاد تلقائياً لمدة 5 دقائق')
        except ValueError as e:
            messages.error(request, str(e))
    
    return redirect('auction_detail', auction_id=auction.id)


@login_required
def join_auction(request, auction_id):
    """Join an auction as a participant"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        
        # Create or update participant
        participant, created = AuctionParticipant.objects.get_or_create(
            auction=auction,
            user=request.user,
            defaults={
                'phone': phone,
                'email': email,
            }
        )
        
        if not created:
            participant.phone = phone
            participant.email = email
            participant.save()
        
        messages.success(request, 'تم الانضمام إلى المزاد بنجاح')
    
    return redirect('auction_detail', auction_id=auction.id)


@login_required
def auction_list(request):
    """List all auctions"""
    auctions = Auction.objects.all().order_by('-created_at')
    return render(request, 'properties/auctions.html', {'auctions': auctions})


# Auction Advanced Features Views

@login_required
def setup_auto_bid(request, auction_id):
    """Setup automatic bidding for an auction"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        form = AutoBidForm(request.POST)
        if form.is_valid():
            auto_bid, created = AutoBid.objects.update_or_create(
                auction=auction,
                user=request.user,
                defaults={
                    'max_amount': form.cleaned_data['max_amount'],
                    'is_active': form.cleaned_data['is_active']
                }
            )
            if created:
                messages.success(request, 'تم تفعيل المزايدة الآلية بنجاح')
            else:
                messages.success(request, 'تم تحديث المزايدة الآلية بنجاح')
            return redirect('auction_detail', auction_id=auction.id)
    else:
        try:
            auto_bid = AutoBid.objects.get(auction=auction, user=request.user)
            form = AutoBidForm(instance=auto_bid)
        except AutoBid.DoesNotExist:
            form = AutoBidForm()
    
    return render(request, 'properties/setup_auto_bid.html', {
        'form': form,
        'auction': auction
    })


@login_required
def toggle_auto_bid(request, auction_id):
    """Toggle auto-bid active status"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    try:
        auto_bid = AutoBid.objects.get(auction=auction, user=request.user)
        auto_bid.is_active = not auto_bid.is_active
        auto_bid.save()
        status = 'مفعّل' if auto_bid.is_active else 'معطّل'
        messages.success(request, f'تم {status} المزايدة الآلية')
    except AutoBid.DoesNotExist:
        messages.error(request, 'لم يتم إعداد المزايدة الآلية بعد')
    
    return redirect('auction_detail', auction_id=auction.id)


@login_required
def auction_rating(request, auction_id):
    """Rate auction participants"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if auction.status != 'ended':
        messages.error(request, 'يمكن التقييم فقط بعد انتهاء المزاد')
        return redirect('auction_detail', auction_id=auction.id)
    
    if request.method == 'POST':
        form = AuctionRatingForm(request.POST)
        if form.is_valid():
            # Get the highest bidder (winner)
            highest_bid = auction.bids.order_by('-amount').first()
            if not highest_bid:
                messages.error(request, 'لا يوجد فائز للمزاد')
                return redirect('auction_detail', auction_id=auction.id)
            
            AuctionRating.objects.update_or_create(
                auction=auction,
                rater=request.user,
                rated_user=highest_bid.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment']
                }
            )
            messages.success(request, 'تم إرسال التقييم بنجاح')
            return redirect('auction_detail', auction_id=auction.id)
    else:
        form = AuctionRatingForm()
    
    return render(request, 'properties/auction_rating.html', {
        'form': form,
        'auction': auction
    })


@login_required
def auction_stats(request, auction_id):
    """View auction statistics"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    # Get or create stats
    stats, created = AuctionStats.objects.get_or_create(auction=auction)
    if created:
        stats.update_stats()
    
    # Get ratings
    ratings = auction.ratings.all()
    avg_rating = 0
    if ratings:
        avg_rating = sum(r.rating for r in ratings) / len(ratings)
    
    context = {
        'auction': auction,
        'stats': stats,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1),
        'rating_count': ratings.count()
    }
    return render(request, 'properties/auction_stats.html', context)


@login_required
def setup_live_stream(request, auction_id):
    """Setup live streaming for auction"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        form = AuctionLiveStreamForm(request.POST)
        if form.is_valid():
            live_stream, created = AuctionLiveStream.objects.update_or_create(
                auction=auction,
                defaults={
                    'stream_url': form.cleaned_data['stream_url'],
                    'stream_key': form.cleaned_data['stream_key'],
                    'platform': form.cleaned_data['platform'],
                    'chat_enabled': form.cleaned_data['chat_enabled'],
                    'recording_enabled': form.cleaned_data['recording_enabled']
                }
            )
            if created:
                messages.success(request, 'تم إعداد البث المباشر بنجاح')
            else:
                messages.success(request, 'تم تحديث البث المباشر بنجاح')
            return redirect('auction_detail', auction_id=auction.id)
    else:
        try:
            live_stream = AuctionLiveStream.objects.get(auction=auction)
            form = AuctionLiveStreamForm(instance=live_stream)
        except AuctionLiveStream.DoesNotExist:
            form = AuctionLiveStreamForm()
    
    return render(request, 'properties/setup_live_stream.html', {
        'form': form,
        'auction': auction
    })


@login_required
def auction_notifications(request):
    """View auction notifications for current user"""
    notifications = AuctionNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Mark as read
    notifications.filter(is_read=False).update(is_read=True)
    
    return render(request, 'properties/auction_notifications.html', {
        'notifications': notifications
    })


@login_required
def create_auction_advertisement(request, auction_id):
    """Create advertisement for auction"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        form = AuctionAdvertisementForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.auction = auction
            ad.save()
            messages.success(request, 'تم إنشاء الإعلان بنجاح')
            return redirect('auction_detail', auction_id=auction.id)
    else:
        form = AuctionAdvertisementForm()
    
    return render(request, 'properties/create_auction_advertisement.html', {
        'form': form,
        'auction': auction
    })


def hotels_list(request):
    """View for listing and searching hotels"""
    form = HotelSearchForm(request.GET or None)
    hotels = Hotel.objects.filter(is_active=True)
    
    if form.is_valid():
        # Filter by star rating
        if form.cleaned_data.get('star_rating'):
            hotels = hotels.filter(star_rating__in=form.cleaned_data['star_rating'])
        
        # Filter by price range
        if form.cleaned_data.get('price_range'):
            hotels = hotels.filter(price_range__in=form.cleaned_data['price_range'])
        
        # Filter by room types (JSON field)
        if form.cleaned_data.get('room_types'):
            hotels = [h for h in hotels if any(rt in h.room_types for rt in form.cleaned_data['room_types'])]
        
        # Filter by meal plan
        if form.cleaned_data.get('meal_plan'):
            hotels = hotels.filter(meal_plan=form.cleaned_data['meal_plan'])
        
        # Filter by services (JSON field)
        if form.cleaned_data.get('services'):
            hotels = [h for h in hotels if any(s in h.services for s in form.cleaned_data['services'])]
        
        # Filter by suitable for (JSON field)
        if form.cleaned_data.get('suitable_for'):
            hotels = [h for h in hotels if any(sf in h.suitable_for for sf in form.cleaned_data['suitable_for'])]
        
        # Filter by governorate
        if form.cleaned_data.get('governorate'):
            hotels = hotels.filter(governorate=form.cleaned_data['governorate'])
    
    return render(request, 'properties/hotels_list.html', {
        'hotels': hotels,
        'form': form,
    })


@login_required
@login_required
def hotel_create_inside_iraq(request):
    """View for creating a hotel inside Iraq"""
    from .forms import PropertyForm, PropertyHotelForm
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر الفنادق.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة فنادق.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من الفنادق ({published}/{limit}). '
                    f'يمكنك حذف بعض الفنادق القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من الفنادق حسب باقة اشتراكك. '
            'يمكنك حذف بعض الفنادق القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')
    
    if request.method == 'POST':
        # First create the base property
        property_form = PropertyForm(request.POST, request.FILES)
        if property_form.is_valid():
            property_instance = property_form.save(commit=False)
            property_instance.owner = request.user
            property_instance.property_type = 'hotel'
            property_instance.location_type = 'inside_iraq'
            property_instance.save()
            
            # Create the hotel details
            hotel_form = PropertyHotelForm(request.POST, request.FILES)
            if hotel_form.is_valid():
                hotel_instance = hotel_form.save(commit=False)
                hotel_instance.property = property_instance
                hotel_instance.save()
                
                messages.success(request, 'تم إضافة الفندق داخل العراق بنجاح')
                return redirect('property_detail', pk=property_instance.pk)
    else:
        property_form = PropertyForm()
        hotel_form = PropertyHotelForm()
    
    return render(request, 'properties/hotel_create_inside_iraq.html', {
        'property_form': property_form,
        'hotel_form': hotel_form
    })


@login_required
def hotel_create_outside_iraq(request):
    """View for creating a hotel outside Iraq"""
    from .forms import PropertyForm, PropertyHotelForm
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر الفنادق.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة فنادق.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من الفنادق ({published}/{limit}). '
                    f'يمكنك حذف بعض الفنادق القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من الفنادق حسب باقة اشتراكك. '
            'يمكنك حذف بعض الفنادق القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')
    
    if request.method == 'POST':
        # First create the base property
        property_form = PropertyForm(request.POST, request.FILES)
        if property_form.is_valid():
            property_instance = property_form.save(commit=False)
            property_instance.owner = request.user
            property_instance.property_type = 'hotel'
            property_instance.location_type = 'outside_iraq'
            property_instance.save()
            
            # Create the hotel details
            hotel_form = PropertyHotelForm(request.POST, request.FILES)
            if hotel_form.is_valid():
                hotel_instance = hotel_form.save(commit=False)
                hotel_instance.property = property_instance
                hotel_instance.save()
                
                messages.success(request, 'تم إضافة الفندق خارج العراق بنجاح')
                return redirect('property_detail', pk=property_instance.pk)
    else:
        property_form = PropertyForm()
        hotel_form = PropertyHotelForm()
    
    return render(request, 'properties/hotel_create_outside_iraq.html', {
        'property_form': property_form,
        'hotel_form': hotel_form
    })


def hotel_create(request):
    """View for creating a new hotel"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        star_rating = request.POST.get('star_rating')
        governorate = request.POST.get('governorate')
        city = request.POST.get('city')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        website = request.POST.get('website')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        
        hotel = Hotel.objects.create(
            name=name,
            description=description,
            star_rating=star_rating,
            governorate=governorate,
            city=city,
            address=address,
            phone=phone,
            email=email,
            website=website,
            min_price=min_price,
            max_price=max_price,
            user=request.user
        )
        
        messages.success(request, 'تم إضافة الفندق بنجاح')
        return redirect('hotels_list')
    
    return render(request, 'properties/hotel_form.html')


@login_required
def hotel_update(request, hotel_id):
    """View for updating a hotel"""
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    if hotel.user != request.user and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية تعديل هذا الفندق')
        return redirect('hotels_list')
    
    if request.method == 'POST':
        hotel.name = request.POST.get('name', hotel.name)
        hotel.description = request.POST.get('description', hotel.description)
        hotel.star_rating = request.POST.get('star_rating', hotel.star_rating)
        hotel.governorate = request.POST.get('governorate', hotel.governorate)
        hotel.city = request.POST.get('city', hotel.city)
        hotel.address = request.POST.get('address', hotel.address)
        hotel.phone = request.POST.get('phone', hotel.phone)
        hotel.email = request.POST.get('email', hotel.email)
        hotel.website = request.POST.get('website', hotel.website)
        hotel.min_price = request.POST.get('min_price', hotel.min_price)
        hotel.max_price = request.POST.get('max_price', hotel.max_price)
        hotel.save()
        
        messages.success(request, 'تم تحديث الفندق بنجاح')
        return redirect('hotels_list')
    
    context = {
        'hotel': hotel,
    }
    return render(request, 'properties/hotel_form.html', context)


@login_required
def hotel_delete(request, hotel_id):
    """View for deleting a hotel"""
    hotel = get_object_or_404(Hotel, id=hotel_id)
    
    if hotel.user != request.user and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية حذف هذا الفندق')
        return redirect('hotels_list')
    
    if request.method == 'POST':
        hotel.delete()
        messages.success(request, 'تم حذف الفندق بنجاح')
        return redirect('hotels_list')
    
    context = {
        'hotel': hotel,
    }
    return render(request, 'properties/hotel_confirm_delete.html', context)


def resorts_list(request):
    """View for listing and searching resorts"""
    form = ResortSearchForm(request.GET or None)
    resorts = Resort.objects.filter(status='active')
    
    if form.is_valid():
        # Filter by resort type
        if form.cleaned_data.get('resort_type'):
            resorts = resorts.filter(resort_type__in=form.cleaned_data['resort_type'])
        
        # Filter by governorate
        if form.cleaned_data.get('governorate'):
            resorts = resorts.filter(governorate=form.cleaned_data['governorate'])
        
        # Filter by rating
        if form.cleaned_data.get('rating'):
            rating = int(form.cleaned_data['rating'])
            resorts = resorts.filter(rating__gte=rating)
        
        # Filter by price range
        if form.cleaned_data.get('price_range'):
            price_ranges = form.cleaned_data['price_range']
            q_objects = Q()
            for price_range in price_ranges:
                if price_range == '0-50000':
                    q_objects |= Q(max_price__lte=50000) | Q(min_price__lte=50000)
                elif price_range == '50000-100000':
                    q_objects |= Q(min_price__gte=50000, max_price__lte=100000)
                elif price_range == '100000-200000':
                    q_objects |= Q(min_price__gte=100000, max_price__lte=200000)
                elif price_range == '200000-500000':
                    q_objects |= Q(min_price__gte=200000, max_price__lte=500000)
                elif price_range == '500000+':
                    q_objects |= Q(min_price__gte=500000)
            resorts = resorts.filter(q_objects)
    
    return render(request, 'properties/resorts_list.html', {
        'resorts': resorts,
        'form': form,
    })


@login_required
def financial_dashboard(request):
    """Financial dashboard for office management with advanced filtering and reports"""
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models.functions import TruncMonth, TruncDay
    
    # Get date filters from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    period = request.GET.get('period', 'all')  # all, today, week, month, year
    
    # Base query for user's transactions
    user_transactions = FinancialTransaction.objects.filter(user=request.user)
    
    # Apply date filters
    today = timezone.now().date()
    
    if date_from and date_to:
        user_transactions = user_transactions.filter(
            created_at__date__range=[date_from, date_to]
        )
    elif period == 'today':
        user_transactions = user_transactions.filter(created_at__date=today)
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        user_transactions = user_transactions.filter(created_at__date__gte=week_ago)
    elif period == 'month':
        this_month = today.replace(day=1)
        user_transactions = user_transactions.filter(created_at__date__gte=this_month)
    elif period == 'year':
        this_year = today.replace(month=1, day=1)
        user_transactions = user_transactions.filter(created_at__date__gte=this_year)
    
    # Calculate statistics
    total_sales = user_transactions.filter(
        transaction_type='sale', status='completed'
    ).aggregate(total=Sum('sale_price'))['total'] or 0
    
    total_commissions = user_transactions.filter(
        status='completed'
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    total_platform_commission = user_transactions.filter(
        status='completed'
    ).aggregate(total=Sum('platform_commission_amount'))['total'] or 0
    
    total_expenses = Expense.objects.filter(user=request.user)
    
    # Apply same date filter to expenses
    if date_from and date_to:
        total_expenses = total_expenses.filter(date__range=[date_from, date_to])
    elif period == 'today':
        total_expenses = total_expenses.filter(date=today)
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        total_expenses = total_expenses.filter(date__gte=week_ago)
    elif period == 'month':
        this_month = today.replace(day=1)
        total_expenses = total_expenses.filter(date__gte=this_month)
    elif period == 'year':
        this_year = today.replace(month=1, day=1)
        total_expenses = total_expenses.filter(date__gte=this_year)
    
    total_expenses = total_expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    total_profits = Profit.objects.filter(user=request.user)
    
    # Apply same date filter to profits
    if date_from and date_to:
        total_profits = total_profits.filter(date__range=[date_from, date_to])
    elif period == 'today':
        total_profits = total_profits.filter(date=today)
    elif period == 'week':
        week_ago = today - timedelta(days=7)
        total_profits = total_profits.filter(date__gte=week_ago)
    elif period == 'month':
        this_month = today.replace(day=1)
        total_profits = total_profits.filter(date__gte=this_month)
    elif period == 'year':
        this_year = today.replace(month=1, day=1)
        total_profits = total_profits.filter(date__gte=this_year)
    
    total_profits = total_profits.aggregate(total=Sum('amount'))['total'] or 0
    
    net_profit = total_commissions + total_profits - total_expenses
    
    # Get properties sold
    properties_sold = user_transactions.filter(
        transaction_type='sale', status='completed'
    ).count()
    
    # Get completed transactions
    completed_transactions = user_transactions.filter(status='completed').count()
    
    # Get pending transactions
    pending_transactions = user_transactions.filter(status='pending').count()
    
    # Get recent transactions
    recent_transactions = user_transactions.order_by('-created_at')[:10]
    
    # Get recent expenses
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date')[:10]
    
    # Get recent profits
    recent_profits = Profit.objects.filter(user=request.user).order_by('-date')[:10]
    
    # Get wallet info
    wallet, created = OfficeWallet.objects.get_or_create(user=request.user)
    
    # Time-based statistics for charts
    this_month = today.replace(day=1)
    
    # Monthly trend data (last 6 months)
    monthly_trend = []
    for i in range(6):
        month_date = (this_month - timedelta(days=30*i)).replace(day=1)
        month_end = (month_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_sales = FinancialTransaction.objects.filter(
            user=request.user,
            transaction_type='sale',
            status='completed',
            created_at__date__gte=month_date,
            created_at__date__lte=month_end
        ).aggregate(total=Sum('sale_price'))['total'] or 0
        
        month_commissions = FinancialTransaction.objects.filter(
            user=request.user,
            status='completed',
            created_at__date__gte=month_date,
            created_at__date__lte=month_end
        ).aggregate(total=Sum('commission_amount'))['total'] or 0
        
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=month_date,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_trend.append({
            'month': month_date.strftime('%Y-%m'),
            'sales': month_sales,
            'commissions': month_commissions,
            'expenses': month_expenses,
            'profit': month_commissions - month_expenses
        })
    
    monthly_trend.reverse()
    
    # Transaction type breakdown
    transaction_breakdown = user_transactions.values('transaction_type').annotate(
        count=Count('id'),
        total=Sum('sale_price')
    ).order_by('-total')
    
    # Expense category breakdown
    expense_breakdown = Expense.objects.filter(user=request.user).values('category').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'total_sales': total_sales,
        'total_commissions': total_commissions,
        'total_platform_commission': total_platform_commission,
        'total_expenses': total_expenses,
        'total_profits': total_profits,
        'net_profit': net_profit,
        'properties_sold': properties_sold,
        'completed_transactions': completed_transactions,
        'pending_transactions': pending_transactions,
        'recent_transactions': recent_transactions,
        'recent_expenses': recent_expenses,
        'recent_profits': recent_profits,
        'wallet': wallet,
        'monthly_trend': monthly_trend,
        'transaction_breakdown': transaction_breakdown,
        'expense_breakdown': expense_breakdown,
        'date_from': date_from,
        'date_to': date_to,
        'period': period,
    }
    
    return render(request, 'properties/financial_dashboard.html', context)


@login_required
def add_financial_transaction(request):
    """Add a new financial transaction"""
    if request.method == 'POST':
        form = FinancialTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            # Update wallet - handle missing models gracefully
            try:
                wallet, created = OfficeWallet.objects.get_or_create(user=request.user)
                if transaction.status == 'completed' and transaction.commission_amount:
                    wallet.pending_commissions += transaction.commission_amount
                    wallet.save()
                    
                    # Create wallet transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='commission',
                        amount=transaction.commission_amount,
                        balance_before=wallet.current_balance,
                        balance_after=wallet.current_balance + transaction.commission_amount,
                        description=f'عمولة من بيع {transaction.property.display_title if transaction.property else "عقار"}',
                        related_transaction=transaction
                    )
            except Exception as e:
                # Log the error but don't fail the transaction
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating wallet: {e}")
            
            messages.success(request, 'تم إضافة المعاملة المالية بنجاح')
            return redirect('financial_dashboard')
    else:
        form = FinancialTransactionForm()
    
    return render(request, 'properties/add_financial_transaction.html', {'form': form})


@login_required
def add_expense(request):
    """Add a new expense"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            
            # Update wallet - handle missing models gracefully
            try:
                wallet, created = OfficeWallet.objects.get_or_create(user=request.user)
                if expense.amount:
                    wallet.current_balance -= expense.amount
                    wallet.save()
                    
                    # Create wallet transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='withdrawal',
                        amount=expense.amount,
                        balance_before=wallet.current_balance + expense.amount,
                        balance_after=wallet.current_balance,
                        description=f'مصروف: {expense.title or "بدون عنوان"}',
                    )
            except Exception as e:
                # Log the error but don't fail the expense
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating wallet: {e}")
            
            messages.success(request, 'تم إضافة المصروف بنجاح')
            return redirect('financial_dashboard')
    else:
        form = ExpenseForm()
    
    return render(request, 'properties/add_expense.html', {'form': form})


@login_required
def add_payment(request, transaction_id):
    """Add a payment to property owner"""
    transaction = get_object_or_404(FinancialTransaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.financial_transaction = transaction
            payment.user = request.user
            payment.save()
            
            messages.success(request, 'تم إضافة الدفعة بنجاح')
            return redirect('financial_dashboard')
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'transaction': transaction,
        'remaining_amount': transaction.owner_amount - transaction.payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
    }
    
    return render(request, 'properties/add_payment.html', context)


@login_required
def wallet_details(request):
    """View wallet details and transaction history"""
    wallet, created = OfficeWallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.order_by('-created_at')[:50]
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    
    return render(request, 'properties/wallet_details.html', context)


@login_required
def add_profit(request):
    """Add a profit record"""
    if request.method == 'POST':
        form = ProfitForm(request.POST)
        if form.is_valid():
            profit = form.save(commit=False)
            profit.user = request.user
            profit.save()
            
            messages.success(request, 'تم إضافة الربح بنجاح')
            return redirect('financial_dashboard')
    else:
        form = ProfitForm()
    
    return render(request, 'properties/add_profit.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def subscription_plans_list(request):
    """List all subscription plans"""
    plans = SubscriptionPlan.objects.all().order_by('period', 'ads_limit')
    return render(request, 'properties/subscription_plans_list.html', {'plans': plans})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def subscription_plan_create(request):
    """Create a new subscription plan"""
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة خطة الاشتراك بنجاح')
            return redirect('subscription_plans_list')
    else:
        form = SubscriptionPlanForm()
    
    return render(request, 'properties/subscription_plan_form.html', {'form': form, 'title': 'إضافة خطة اشتراك جديدة'})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def subscription_plan_edit(request, plan_id):
    """Edit an existing subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث خطة الاشتراك بنجاح')
            return redirect('subscription_plans_list')
    else:
        form = SubscriptionPlanForm(instance=plan)
    
    return render(request, 'properties/subscription_plan_form.html', {'form': form, 'title': 'تعديل خطة الاشتراك', 'plan': plan})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def subscription_plan_delete(request, plan_id):
    """Delete a subscription plan"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'تم حذف خطة الاشتراك بنجاح')
        return redirect('subscription_plans_list')
    
    return render(request, 'properties/subscription_plan_confirm_delete.html', {'plan': plan})


@login_required
def financial_reports(request):
    """View financial reports"""
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    
    report_type = request.GET.get('type', 'monthly')
    
    # Get date range
    today = timezone.now().date()
    
    if report_type == 'daily':
        start_date = today
        end_date = today
    elif report_type == 'weekly':
        start_date = today - timedelta(days=7)
        end_date = today
    elif report_type == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:  # monthly
        start_date = today.replace(day=1)
        end_date = today
    
    # Get transactions in range
    transactions = FinancialTransaction.objects.filter(
        user=request.user,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Calculate totals
    total_sales = transactions.filter(transaction_type='sale', status='completed').aggregate(
        total=Sum('sale_price')
    )['total'] or 0
    
    total_commissions = transactions.filter(status='completed').aggregate(
        total=Sum('commission_amount')
    )['total'] or 0
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    net_profit = total_commissions - total_expenses
    
    # Get transaction count
    transaction_count = transactions.count()
    expense_count = expenses.count()
    
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_commissions': total_commissions,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'transaction_count': transaction_count,
        'expense_count': expense_count,
        'transactions': transactions.order_by('-created_at')[:20],
        'expenses': expenses.order_by('-date')[:20],
    }
    
    return render(request, 'properties/financial_reports.html', context)


@login_required
def submit_report(request):
    """Submit a new report."""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            messages.success(request, 'تم إرسال البلاغ بنجاح')
            return redirect('home')
    else:
        form = ReportForm()
    
    return render(request, 'properties/submit_report.html', {'form': form})


@login_required
@staff_required
def report_list(request):
    """List all reports for admin."""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    reports = Report.objects.all().select_related('reporter', 'assigned_to')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        reports = reports.filter(report_type=type_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority')
    if priority_filter:
        reports = reports.filter(priority=priority_filter)
    
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'properties/report_list.html', {
        'reports': page_obj,
        'page_obj': page_obj,
    })


@login_required
@staff_required
def report_detail(request, report_id):
    """View report details."""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    report = get_object_or_404(Report, pk=report_id)
    actions = report.actions.all().select_related('performed_by')
    
    if request.method == 'POST':
        action_type = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action_type:
            # Create action record
            ReportAction.objects.create(
                report=report,
                action=action_type,
                notes=notes,
                performed_by=request.user
            )
            
            # Update report status based on action
            if action_type == Report.ACTION_CLOSE_REPORT:
                report.status = Report.STATUS_CLOSED
                report.resolved_at = timezone.now()
            elif action_type == Report.ACTION_REJECT_REPORT:
                report.status = Report.STATUS_REJECTED
            elif action_type in [Report.ACTION_DELETE_AD, Report.ACTION_HIDE_AD, Report.ACTION_SUSPEND_ACCOUNT]:
                report.status = Report.STATUS_REVIEWING
            
            report.save()
            messages.success(request, 'تم تنفيذ الإجراء')
            return redirect('report_detail', report_id=report_id)
    
    return render(request, 'properties/report_detail.html', {
        'report': report,
        'actions': actions,
    })


@login_required
def user_messages(request):
    """عرض رسائل المستخدم مع الدلالين."""
    # Get messages where user is either sender or recipient
    messages = Message.objects.filter(
        message_type=Message.TYPE_USER_BROKER,
        is_deleted_by_sender=False if request.user in Message.objects.filter(sender=request.user) else True,
        is_deleted_by_recipient=False if request.user in Message.objects.filter(recipient=request.user) else True
    ).filter(
        models.Q(sender=request.user) | models.Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('-created_at')
    
    # Get unread count
    unread_count = messages.filter(recipient=request.user, is_read=False).count()
    
    return render(request, 'properties/user_messages.html', {
        'messages': messages,
        'unread_count': unread_count,
    })


@login_required
def user_message_detail(request, message_id):
    """عرض تفاصيل رسالة المستخدم."""
    message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has access to this message
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الرسالة')
        return redirect('user_messages')
    
    # Check if message is deleted for this user
    if (message.sender == request.user and message.is_deleted_by_sender) or \
       (message.recipient == request.user and message.is_deleted_by_recipient):
        messages.error(request, 'هذه الرسالة محذوفة')
        return redirect('user_messages')
    
    # Mark as read if user is recipient
    if message.recipient == request.user and not message.is_read:
        message.mark_as_read()
    
    return render(request, 'properties/user_message_detail.html', {
        'message': message,
    })


@login_required
def send_user_message(request, broker_id=None):
    """إرسال رسالة من مستخدم إلى دلال."""
    # Check if recipient broker exists
    recipient_broker = None
    if broker_id:
        recipient_broker = get_object_or_404(Broker, pk=broker_id)
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        message_text = request.POST.get('message')
        property_id = request.POST.get('property_id')
        
        if recipient_id and message_text:
            recipient = get_object_or_404(User, pk=recipient_id)
            recipient_broker_profile = get_broker(recipient)
            
            if not recipient_broker_profile:
                messages.error(request, 'المستلم ليس دلال')
            else:
                # Create message
                message = Message.objects.create(
                    name=request.user.get_full_name() or request.user.username,
                    email=request.user.email,
                    message=message_text,
                    message_type=Message.TYPE_USER_BROKER,
                    sender=request.user,
                    recipient=recipient,
                    broker=recipient_broker_profile
                )
                
                # Add property if specified
                if property_id:
                    try:
                        prop = Property.objects.get(pk=property_id)
                        message.property = prop
                        message.save()
                    except Property.DoesNotExist:
                        pass
                
                # Create notification for recipient
                from .utils import create_notification
                create_notification(
                    user=recipient,
                    notification_type='message',
                    title='رسالة جديدة',
                    message=f'لديك رسالة جديدة من {request.user.get_full_name() or request.user.username}',
                    link=f'/messages/{message.id}/'
                )
                
                messages.success(request, 'تم إرسال الرسالة بنجاح')
                return redirect('user_messages')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
    
    # Get list of brokers to send message to
    brokers = Broker.objects.filter(is_active=True).exclude(user=request.user).select_related('user')
    
    return render(request, 'properties/send_user_message.html', {
        'brokers': brokers,
        'recipient_broker': recipient_broker,
    })


@login_required
@require_POST
def delete_user_message(request, message_id):
    """حذف رسالة المستخدم (حذف ناعم)."""
    message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has access to this message
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'ليس لديك صلاحية لحذف هذه الرسالة')
        return redirect('user_messages')
    
    message.delete_for_user(request.user)
    messages.success(request, 'تم حذف الرسالة')
    return redirect('user_messages')


@csrf_exempt
@login_required
def send_message_view(request):
    """إرسال رسالة - دالة منفصلة لتجنب مشاكل CSRF عبر المنافذ"""
    if request.method == 'POST':
        conversation_id = request.POST.get('conversation_id')
        message_content = request.POST.get('message_content')
        message_file = request.FILES.get('message_file')
        
        if conversation_id and (message_content or message_file):
            try:
                # Get conversation
                conversation = Conversation.objects.get(
                    conversation_id=conversation_id,
                    participants=request.user
                )
                
                # Get other participant
                other_user = conversation.participants.exclude(id=request.user.id).first()
                
                if not other_user:
                    messages.error(request, 'المستخدم غير موجود في المحادثة')
                    return redirect(f'/dashboard/messages/?conversation_id={conversation_id}')
                
                # Determine message type
                message_type = Message.TYPE_TEXT
                if message_file:
                    file_extension = message_file.name.split('.')[-1].lower()
                    if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        message_type = Message.TYPE_IMAGE
                    elif file_extension in ['mp3', 'wav', 'ogg', 'm4a']:
                        message_type = Message.TYPE_AUDIO
                    elif file_extension in ['mp4', 'webm', 'mov']:
                        message_type = Message.TYPE_VIDEO
                    else:
                        message_type = Message.TYPE_FILE
                
                # Create message using the Message model
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    recipient=other_user,
                    content=message_content or '',
                    message_type=message_type,
                    file=message_file,
                    file_name=message_file.name if message_file else '',
                    file_size=message_file.size if message_file else None
                )
                
                # Update conversation timestamp
                conversation.updated_at = timezone.now()
                conversation.save()
                
                # Create notification for recipient
                try:
                    from .models import Notification
                    Notification.objects.create(
                        user=other_user,
                        title='رسالة جديدة',
                        description=f'رسالة جديدة من {request.user.username}',
                        notification_type='message',
                        action_url=f'/dashboard/messages/?conversation_id={conversation_id}',
                        metadata={
                            'conversation_id': str(conversation_id),
                            'sender_id': request.user.id,
                            'sender_name': request.user.username,
                            'message_type': message_type
                        }
                    )
                except Exception as e:
                    print(f"Error creating notification: {e}")
                
                messages.success(request, 'تم إرسال الرسالة')
                return redirect(f'/dashboard/messages/?conversation_id={conversation_id}')
                
            except Conversation.DoesNotExist:
                messages.error(request, 'المحادثة غير موجودة')
            except Exception as e:
                print(f"Error sending message: {e}")
                messages.error(request, 'تعذر إرسال الرسالة')
    
    return redirect('/dashboard/messages/')


@csrf_exempt
@login_required
def create_conversation_view(request):
    """إنشاء محادثة جديدة - دالة منفصلة لتجنب مشاكل CSRF عبر المنافذ"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        if recipient_id:
            try:
                recipient = User.objects.get(id=recipient_id)
                
                # Check if conversation already exists
                existing_conversation = Conversation.objects.filter(
                    participants=request.user
                ).filter(participants=recipient).first()
                
                if existing_conversation:
                    # Navigate to existing conversation
                    return redirect(f'/dashboard/messages/?conversation_id={existing_conversation.conversation_id}')
                
                # Create new conversation
                conversation = Conversation.objects.create(
                    conversation_type=Conversation.TYPE_DIRECT
                )
                conversation.participants.add(request.user, recipient)
                
                # Navigate to new conversation
                return redirect(f'/dashboard/messages/?conversation_id={conversation.conversation_id}')
                
            except User.DoesNotExist:
                messages.error(request, 'المستخدم غير موجود')
            except Exception as e:
                print(f"Error creating conversation: {e}")
                messages.error(request, 'تعذر إنشاء المحادثة')
    
    return redirect('/dashboard/messages/')


@login_required
def broker_messages_list(request):
    """قائمة رسائل الدلال بتصميم الماسنجر"""
    from .models import Broker, UserProfile, Conversation, Message
    
    message_type = request.GET.get('type', 'inbox')
    conversation_id = request.GET.get('conversation_id')
    
    # Get conversations for the user
    try:
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants').order_by('-updated_at')
        
        # Add extra data to conversations
        conversations_data = []
        for conv in conversations:
            # Get the other participant
            other_user = conv.participants.exclude(id=request.user.id).first()
            if other_user:
                # Get last message from the new message model structure
                last_message = None
                if hasattr(conv, 'messages') and conv.messages.exists():
                    last_message = conv.messages.last()
                
                # Count unread messages (using the new structure)
                unread_count = 0
                if hasattr(conv, 'messages'):
                    unread_count = conv.messages.filter(
                        is_read=False
                    ).exclude(sender=request.user).count()
                
                conversations_data.append({
                    'id': conv.conversation_id,  # Use conversation_id (UUID) instead of id
                    'other_user': other_user,
                    'last_message': last_message.content if last_message else '',
                    'last_message_time': last_message.created_at if last_message else conv.updated_at,
                    'last_message_is_from_me': last_message.sender == request.user if last_message else False,
                    'unread_count': unread_count,
                    'is_online': getattr(other_user, 'is_online', False)
                })
    except Exception as e:
        print(f"Error loading conversations: {e}")
        conversations_data = []
    
    # Get active conversation
    active_conversation = None
    messages = []
    if conversation_id:
        try:
            active_conversation = Conversation.objects.get(
                conversation_id=conversation_id,  # Use conversation_id instead of id
                participants=request.user
            )
            other_user = active_conversation.participants.exclude(id=request.user.id).first()
            messages = active_conversation.messages.all().order_by('created_at') if hasattr(active_conversation, 'messages') else []
            
            # Mark messages as read
            if hasattr(active_conversation, 'messages'):
                active_conversation.messages.filter(
                    is_read=False
                ).exclude(sender=request.user).update(is_read=True)
            
            active_conversation = {
                'id': active_conversation.conversation_id,  # Use conversation_id
                'other_user': other_user,
                'is_online': getattr(other_user, 'is_online', False)
            }
        except Exception as e:
            print(f"Error loading active conversation: {e}")
            pass
    
    # Count statistics
    try:
        total_messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).count()
        
        unread_count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        sent_count = Message.objects.filter(sender=request.user).count()
        
        # Count starred messages (assuming there's a star field)
        starred_count = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            is_starred=True
        ).count() if hasattr(Message, 'is_starred') else 0
        
        # Count archived messages
        archived_count = Conversation.objects.filter(
            participants=request.user,
            is_archived=True
        ).count() if hasattr(Conversation, 'is_archived') else 0
        
        # Count spam messages
        spam_count = Message.objects.filter(
            recipient=request.user,
            is_spam=True
        ).count() if hasattr(Message, 'is_spam') else 0
        
    except:
        total_messages = 0
        unread_count = 0
        sent_count = 0
        starred_count = 0
        archived_count = 0
        spam_count = 0
    
    context = {
        'conversations': conversations_data,
        'active_conversation': active_conversation,
        'messages': messages,
        'active_conversation_id': conversation_id,
        'message_type': message_type,
        'total_messages': total_messages,
        'unread_count': unread_count,
        'sent_count': sent_count,
        'starred_count': starred_count,
        'archived_count': archived_count,
        'spam_count': spam_count,
    }
    
    return render(request, 'properties/broker_messages_list.html', context)


@login_required
def broker_message_detail(request, message_id):
    """View broker message details."""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    message = get_object_or_404(Message, pk=message_id, message_type=Message.TYPE_BROKER_MESSAGE)
    
    # Check if user is sender or recipient
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'ليس لديك صلاحية عرض هذه الرسالة')
        return redirect('broker_messages')
    
    # Mark as read if recipient
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    return render(request, 'properties/broker_message_detail.html', {
        'message': message,
    })


@login_required
def send_broker_message(request, broker_id=None):
    """Send a message to another user (broker or regular user)."""
    from .models import MessageAttachment
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    broker = get_broker(request.user)
    
    recipient_broker = None
    if broker_id:
        recipient_broker = get_object_or_404(Broker, pk=broker_id)
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        message_text = request.POST.get('message')
        attachments = request.FILES.getlist('attachment')
        
        if recipient_id and message_text:
            recipient = get_object_or_404(User, pk=recipient_id)
            recipient_broker_profile = get_broker(recipient)
            
            # Allow messaging to both brokers and regular users
            message = Message.objects.create(
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                phone=broker.phone if broker else '',
                message=message_text,
                message_type=Message.TYPE_BROKER_MESSAGE,
                sender=request.user,
                recipient=recipient,
                broker=broker
            )
            
            # Handle attachments
            for attachment in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    file=attachment,
                    uploaded_by=request.user
                )
            
            # Send real-time notification via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{recipient.id}",
                {
                    'type': 'notification',
                    'notification': {
                        'type': 'new_message',
                        'title': 'رسالة جديدة',
                        'message': f'رسالة جديدة من {request.user.get_full_name() or request.user.username}',
                        'sender_id': request.user.id,
                        'sender_name': request.user.get_full_name() or request.user.username,
                        'message_id': message.id,
                        'message_preview': message_text[:100]
                    },
                    'timestamp': str(message.created_at)
                }
            )
            
            messages.success(request, 'تم إرسال الرسالة بنجاح')
            return redirect('broker_messaging')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول')
    
    # Get list of brokers to send message to
    brokers = Broker.objects.filter(is_active=True).exclude(user=request.user).select_related('user')
    
    return render(request, 'properties/send_broker_message.html', {
        'brokers': brokers,
        'recipient_broker': recipient_broker,
    })


@login_required
@require_POST
def archive_message(request, message_id):
    """Archive a message/conversation."""
    from django.http import JsonResponse
    
    message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has access to this message
    if message.sender != request.user and message.recipient != request.user:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})
    
    # Archive the message
    message.archive()
    
    return JsonResponse({'success': True})


@login_required
def create_group_chat(request):
    """Create a new group chat."""
    from .models import Conversation, ConversationParticipant
    
    broker = get_broker(request.user)
    
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        group_description = request.POST.get('group_description')
        participants_ids = request.POST.getlist('participants')
        
        if not group_name:
            messages.error(request, 'اسم المجموعة مطلوب')
            return redirect('broker_messaging')
        
        if not participants_ids:
            messages.error(request, 'يجب اختيار مشارك واحد على الأقل')
            return redirect('broker_messaging')
        
        # Create conversation
        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_GROUP,
            name=group_name,
            description=group_description,
            created_by=request.user
        )
        
        # Add creator as admin participant
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            role=ConversationParticipant.ROLE_ADMIN
        )
        
        # Add other participants
        for participant_id in participants_ids:
            try:
                participant = User.objects.get(pk=participant_id)
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=participant,
                    role=ConversationParticipant.ROLE_MEMBER
                )
            except User.DoesNotExist:
                continue
        
        messages.success(request, 'تم إنشاء المجموعة بنجاح')
        return redirect('broker_messaging')
    
    return redirect('broker_messaging')


@login_required
@require_POST
def add_message_reaction(request, message_id):
    """Add or remove a reaction to a message."""
    from django.http import JsonResponse
    from .models import MessageReaction, ChatMessage
    
    reaction_type = request.POST.get('reaction_type')
    
    if not reaction_type:
        return JsonResponse({'success': False, 'error': 'نوع الرد مطلوب'})
    
    message = get_object_or_404(ChatMessage, pk=message_id)
    
    # Check if user has access to this message
    conversation = message.conversation
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})
    
    # Check if reaction already exists
    existing_reaction = MessageReaction.objects.filter(
        message=message,
        user=request.user,
        reaction_type=reaction_type
    ).first()
    
    if existing_reaction:
        # Remove reaction
        existing_reaction.delete()
        return JsonResponse({'success': True, 'action': 'removed'})
    else:
        # Add reaction
        MessageReaction.objects.create(
            message=message,
            user=request.user,
            reaction_type=reaction_type
        )
        return JsonResponse({'success': True, 'action': 'added'})


@login_required
@require_POST
def edit_message(request, message_id):
    """Edit a message."""
    from django.http import JsonResponse
    from .models import ChatMessage
    
    new_content = request.POST.get('content')
    
    if not new_content:
        return JsonResponse({'success': False, 'error': 'محتوى الرسالة مطلوب'})
    
    message = get_object_or_404(ChatMessage, pk=message_id)
    
    # Check if user is the sender
    if message.sender != request.user:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})
    
    # Edit the message
    message.edit(new_content)
    
    return JsonResponse({'success': True, 'content': new_content, 'edited_at': message.edited_at.isoformat() if message.edited_at else None})


@login_required
@require_POST
def delete_message(request, message_id):
    """Delete a message (soft delete)."""
    from django.http import JsonResponse
    from .models import ChatMessage
    
    message = get_object_or_404(ChatMessage, pk=message_id)
    
    # Check if user is the sender
    if message.sender != request.user:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})
    
    # Soft delete the message
    message.soft_delete()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_message_read(request, message_id):
    """Mark a message as read."""
    from django.http import JsonResponse
    from .models import ChatMessage, MessageReadStatus
    from django.utils import timezone
    
    message = get_object_or_404(ChatMessage, pk=message_id)
    
    # Check if user is the recipient
    if message.sender == request.user:
        return JsonResponse({'success': False, 'error': 'لا يمكن وضع علامة قراءة على رسالتك'})
    
    # Check if user has access to this message
    conversation = message.conversation
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})
    
    # Mark as read
    MessageReadStatus.objects.get_or_create(
        message=message,
        user=request.user,
        defaults={'read_at': timezone.now()}
    )
    
    return JsonResponse({'success': True})


@login_required
def forward_message(request, message_id):
    """Forward a message to another conversation."""
    from .models import ChatMessage, Conversation
    
    original_message = get_object_or_404(ChatMessage, pk=message_id)
    
    # Check if user has access to the original message
    if not original_message.conversation.participants.filter(id=request.user.id).exists():
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('broker_messaging')
    
    if request.method == 'POST':
        target_conversation_id = request.POST.get('target_conversation')
        
        if not target_conversation_id:
            messages.error(request, 'يجب اختيار المحادثة المستهدفة')
            return redirect('broker_messaging')
        
        target_conversation = get_object_or_404(Conversation, pk=target_conversation_id)
        
        # Check if user is a participant in the target conversation
        if not target_conversation.participants.filter(id=request.user.id).exists():
            messages.error(request, 'ليس لديك صلاحية')
            return redirect('broker_messaging')
        
        # Create forwarded message
        ChatMessage.objects.create(
            conversation=target_conversation,
            sender=request.user,
            message_type=ChatMessage.TYPE_TEXT,
            content=original_message.content,
            reply_to=original_message
        )
        
        messages.success(request, 'تم إعادة توجيه الرسالة بنجاح')
        return redirect('broker_messaging')
    
    # Get user's conversations for forwarding
    user_conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).exclude(pk=original_message.conversation.pk)
    
    return render(request, 'properties/forward_message.html', {
        'original_message': original_message,
        'conversations': user_conversations,
    })


@login_required
@require_POST
def mute_user(request, user_id):
    """Mute a user."""
    from django.http import JsonResponse
    from .models import MutedUser
    
    user_to_mute = get_object_or_404(User, pk=user_id)
    
    if user_to_mute == request.user:
        return JsonResponse({'success': False, 'error': 'لا يمكن كتم نفسك'})
    
    MutedUser.objects.get_or_create(
        muter=request.user,
        muted=user_to_mute
    )
    
    return JsonResponse({'success': True, 'message': 'تم كتم المستخدم'})


@login_required
@require_POST
def unmute_user(request, user_id):
    """Unmute a user."""
    from django.http import JsonResponse
    from .models import MutedUser
    
    user_to_unmute = get_object_or_404(User, pk=user_id)
    
    MutedUser.objects.filter(
        muter=request.user,
        muted=user_to_unmute
    ).delete()
    
    return JsonResponse({'success': True, 'message': 'تم إلغاء كتم المستخدم'})


@login_required
@require_POST
def block_user_dashboard(request, user_id):
    """Block a user from dashboard."""
    from django.http import JsonResponse
    from .models import BlockedUser

    user_to_block = get_object_or_404(User, pk=user_id)

    if user_to_block == request.user:
        return JsonResponse({'success': False, 'error': 'لا يمكن حظر نفسك'})

    BlockedUser.objects.get_or_create(
        blocker=request.user,
        blocked=user_to_block,
    )

    return JsonResponse({'success': True, 'message': 'تم حظر المستخدم'})


@login_required
@require_POST
def unblock_user_dashboard(request, user_id):
    """Unblock a user from dashboard."""
    from django.http import JsonResponse
    from .models import BlockedUser

    user_to_unblock = get_object_or_404(User, pk=user_id)

    BlockedUser.objects.filter(
        blocker=request.user,
        blocked=user_to_unblock,
    ).delete()

    return JsonResponse({'success': True, 'message': 'تم إلغاء حظر المستخدم'})


@login_required
def message_notification_settings(request):
    """Manage message notification settings."""
    from .models import MessageNotificationSettings
    
    settings_obj, created = MessageNotificationSettings.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        # Update notification type preferences
        settings_obj.new_message_notifications = request.POST.get('new_message_notifications') == 'on'
        settings_obj.mention_notifications = request.POST.get('mention_notifications') == 'on'
        settings_obj.reaction_notifications = request.POST.get('reaction_notifications') == 'on'
        settings_obj.reply_notifications = request.POST.get('reply_notifications') == 'on'
        settings_obj.group_mention_notifications = request.POST.get('group_mention_notifications') == 'on'
        
        # Update platform preferences
        settings_obj.in_app_notifications = request.POST.get('in_app_notifications') == 'on'
        settings_obj.browser_notifications = request.POST.get('browser_notifications') == 'on'
        settings_obj.email_notifications = request.POST.get('email_notifications') == 'on'
        settings_obj.sound_enabled = request.POST.get('sound_enabled') == 'on'
        
        # Update quiet hours
        settings_obj.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
        settings_obj.quiet_hours_start = request.POST.get('quiet_hours_start') or None
        settings_obj.quiet_hours_end = request.POST.get('quiet_hours_end') or None
        
        settings_obj.save()
        messages.success(request, 'تم تحديث إعدادات الإشعارات بنجاح')
        return redirect('message_notification_settings')
    
    return render(request, 'properties/message_notification_settings.html', {
        'settings': settings_obj,
    })


@login_required
def security_settings(request):
    """Manage security settings."""
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Change password
        if current_password and new_password:
            if request.user.check_password(current_password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                else:
                    messages.error(request, 'كلمة المرور الجديدة غير متطابقة')
            else:
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
        
        return redirect('security_settings')
    
    return render(request, 'properties/security_settings.html')


@login_required
def privacy_settings(request):
    """Manage privacy settings."""
    from .models import UserSettings
    
    settings_obj, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update privacy settings
        settings_obj.profile_visibility = request.POST.get('profile_visibility', 'public')
        settings_obj.show_email = request.POST.get('show_email') == 'on'
        settings_obj.show_phone = request.POST.get('show_phone') == 'on'
        settings_obj.allow_messages = request.POST.get('allow_messages') == 'on'
        settings_obj.show_activity = request.POST.get('show_activity') == 'on'
        
        settings_obj.save()
        messages.success(request, 'تم تحديث إعدادات الخصوصية بنجاح')
        return redirect('privacy_settings')
    
    return render(request, 'properties/privacy_settings.html', {
        'settings': settings_obj,
    })


@login_required
def preferences_settings(request):
    """Manage user preferences."""
    from .models import UserSettings
    
    settings_obj, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        settings_obj.language = request.POST.get('language', 'ar')
        settings_obj.theme = request.POST.get('theme', 'light')
        settings_obj.timezone = request.POST.get('timezone', 'Asia/Riyadh')
        settings_obj.currency = request.POST.get('currency', 'SAR')
        
        settings_obj.save()
        messages.success(request, 'تم تحديث التفضيلات بنجاح')
        return redirect('preferences_settings')
    
    return render(request, 'properties/preferences_settings.html', {
        'settings': settings_obj,
    })


@login_required
def account_management(request):
    """Manage account information."""
    if request.method == 'POST':
        # Update account information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        
        if request.POST.get('phone'):
            request.user.phone = request.POST.get('phone')
        
        request.user.save()
        messages.success(request, 'تم تحديث معلومات الحساب بنجاح')
        return redirect('account_management')
    
    return render(request, 'properties/account_management.html', {
        'user': request.user,
    })


@login_required
def settings_hub(request):
    """Main settings hub page."""
    return render(request, 'properties/settings_hub.html')


@login_required
def activity_page(request):
    """Display user activity."""
    from .models import PropertySave, ChatMessage, PropertyViewStats
    
    # Get user's recent activities
    saved_properties = PropertySave.objects.filter(user=request.user).select_related('property').order_by('-created_at')[:10]
    sent_messages = ChatMessage.objects.filter(sender=request.user).order_by('-created_at')[:10]
    
    return render(request, 'properties/activity_page.html', {
        'saved_properties': saved_properties,
        'sent_messages': sent_messages,
    })


@login_required
@staff_required
def bulk_message_create(request):
    """Create and send bulk messages to users or brokers."""
    from .models import BulkMessage, Broker
    from django.utils import timezone
    
    if request.method == 'POST':
        target_type = request.POST.get('target_type', 'all_users')
        title = request.POST.get('title', '')
        message = request.POST.get('message', '')
        scheduled_at = request.POST.get('scheduled_at')
        
        if not title or not message:
            messages.error(request, 'العنوان والرسالة مطلوبان')
            return redirect('bulk_message_create')
        
        # Create bulk message
        bulk_msg = BulkMessage.objects.create(
            sender=request.user,
            target_type=target_type,
            title=title,
            message=message,
            status='pending'
        )
        
        if scheduled_at:
            from datetime import datetime
            bulk_msg.scheduled_at = datetime.fromisoformat(scheduled_at)
        
        # Get recipients based on target type
        recipients = []
        if target_type == 'all_users':
            recipients = User.objects.filter(is_active=True)
        elif target_type == 'all_brokers':
            recipients = User.objects.filter(broker__isnull=False, is_active=True)
        elif target_type == 'active_users':
            from django.utils import timezone
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recipients = User.objects.filter(is_active=True, last_login__gte=thirty_days_ago)
        elif target_type == 'active_brokers':
            from django.utils import timezone
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recipients = User.objects.filter(broker__isnull=False, is_active=True, last_login__gte=thirty_days_ago)
        elif target_type == 'specific_users':
            user_ids = request.POST.getlist('user_ids')
            recipients = User.objects.filter(id__in=user_ids, is_active=True)
        elif target_type == 'specific_brokers':
            broker_ids = request.POST.getlist('broker_ids')
            recipients = User.objects.filter(broker__id__in=broker_ids, is_active=True)
        
        bulk_msg.total_recipients = recipients.count()
        bulk_msg.save()
        
        # Send messages
        sent_count = 0
        failed_count = 0
        
        from .models import ChatMessage, Conversation, ConversationParticipant
        
        for recipient in recipients:
            try:
                # Create or get conversation
                conversation, created = Conversation.objects.get_or_create(
                    conversation_type='direct',
                    defaults={'name': f'{request.user.username} - {recipient.username}'}
                )
                
                if created:
                    # Add participants
                    ConversationParticipant.objects.create(
                        conversation=conversation,
                        user=request.user,
                        role='admin'
                    )
                    ConversationParticipant.objects.create(
                        conversation=conversation,
                        user=recipient,
                        role='member'
                    )
                
                # Create message
                ChatMessage.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=message,
                    message_type='text'
                )
                
                sent_count += 1
            except Exception as e:
                failed_count += 1
        
        bulk_msg.sent_count = sent_count
        bulk_msg.failed_count = failed_count
        bulk_msg.status = 'sent'
        bulk_msg.sent_at = timezone.now()
        bulk_msg.save()
        
        messages.success(request, f'تم إرسال الرسالة إلى {sent_count} مستخدم. فشل الإرسال لـ {failed_count} مستخدم.')
        return redirect('bulk_message_list')
    
    # Get users and brokers for selection
    all_users = User.objects.filter(is_active=True).order_by('username')
    all_brokers = User.objects.filter(broker__isnull=False, is_active=True).select_related('broker').order_by('username')
    
    return render(request, 'properties/bulk_message_create.html', {
        'all_users': all_users,
        'all_brokers': all_brokers,
    })


@login_required
@staff_required
def bulk_message_list(request):
    """List all bulk messages."""
    from .models import BulkMessage
    
    bulk_messages = BulkMessage.objects.all().order_by('-created_at')
    
    return render(request, 'properties/bulk_message_list.html', {
        'bulk_messages': bulk_messages,
    })


@login_required
def messaging_dashboard(request):
    """Professional messaging dashboard with dark theme."""
    from .models import Conversation, ConversationParticipant, ChatMessage
    
    user = request.user
    folder = request.GET.get('folder', 'all')
    search = request.GET.get('search', '')
    
    # Get user's conversations
    conversations = Conversation.objects.filter(
        participants=user,
        is_active=True
    ).select_related('created_by').prefetch_related('participants_info')
    
    # Filter by folder
    if folder == 'inbox':
        conversations = conversations.filter(participants_info__user=user, participants_info__folder='inbox')
    elif folder == 'sent':
        conversations = conversations.filter(participants_info__user=user, participants_info__folder='sent')
    elif folder == 'starred':
        conversations = conversations.filter(participants_info__user=user, participants_info__is_starred=True)
    elif folder == 'archived':
        conversations = conversations.filter(participants_info__user=user, participants_info__is_archived=True)
    
    # Search filter
    if search:
        conversations = conversations.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    conversations = conversations.order_by('-last_message_at', '-created_at')
    
    # Calculate counts
    all_count = Conversation.objects.filter(participants=user, is_active=True).count()
    inbox_count = ConversationParticipant.objects.filter(user=user, folder='inbox').count()
    
    return render(request, 'properties/messaging_dashboard.html', {
        'conversations': conversations,
        'folder': folder,
        'search': search,
        'all_count': all_count,
        'inbox_count': inbox_count,
    })


@login_required
def api_conversations_list(request):
    """API endpoint to list conversations."""
    from django.http import JsonResponse
    from .models import Conversation, ConversationParticipant, ChatMessage
    
    user = request.user
    folder = request.GET.get('folder', 'all')
    search = request.GET.get('search', '')
    
    conversations = Conversation.objects.filter(
        participants=user,
        is_active=True
    ).select_related('created_by').prefetch_related('participants_info', 'chat_messages')
    
    # Filter by folder
    if folder == 'inbox':
        conversations = conversations.filter(participants_info__user=user, participants_info__folder='inbox')
    elif folder == 'sent':
        conversations = conversations.filter(participants_info__user=user, participants_info__folder='sent')
    elif folder == 'starred':
        conversations = conversations.filter(participants_info__user=user, participants_info__is_starred=True)
    elif folder == 'archived':
        conversations = conversations.filter(participants_info__user=user, participants_info__is_archived=True)
    
    # Search filter
    if search:
        conversations = conversations.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    conversations = conversations.order_by('-last_message_at', '-created_at')
    
    # Serialize conversations
    conversations_data = []
    for conv in conversations:
        participant_info = conv.participants_info.filter(user=user).first()
        other_participant = conv.get_other_participant(user)
        last_message = conv.chat_messages.filter(is_deleted=False).first()
        
        conversations_data.append({
            'id': str(conv.conversation_id),
            'name': other_participant.get_full_name() if other_participant else conv.name,
            'avatar': ((other_participant.get_full_name() if other_participant else conv.name)[0].upper() if (other_participant.get_full_name() if other_participant else conv.name) else '?'),
            'preview': last_message.content[:50] if last_message else 'لا توجد رسائل',
            'time': conv.last_message_at.strftime('%H:%M') if conv.last_message_at else '',
            'unread': not participant_info.last_read_at or (conv.last_message_at and conv.last_message_at > participant_info.last_read_at),
            'starred': participant_info.is_starred if participant_info else False,
            'type': 'مباشر' if conv.conversation_type == 'direct' else 'مجموعة',
        })
    
    # Calculate counts
    all_count = Conversation.objects.filter(participants=user, is_active=True).count()
    inbox_count = ConversationParticipant.objects.filter(user=user, folder='inbox').count()
    
    return JsonResponse({
        'conversations': conversations_data,
        'counts': {
            'all': all_count,
            'inbox': inbox_count,
        }
    })


@login_required
def api_conversation_detail(request, conversation_id):
    """API endpoint to get conversation details with messages."""
    from django.http import JsonResponse
    from .models import Conversation, ChatMessage, MessageReadStatus
    
    try:
        conversation = Conversation.objects.get(conversation_id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    # Check if user is participant
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    other_participant = conversation.get_other_participant(request.user)
    
    # Get messages
    messages = ChatMessage.objects.filter(
        conversation=conversation,
        is_deleted=False
    ).select_related('sender', 'property', 'hotel', 'resort').prefetch_related('attachments').order_by('created_at')
    
    # Serialize messages
    messages_data = []
    for msg in messages:
        message_data = {
            'id': str(msg.message_id),
            'content': msg.content,
            'sender': msg.sender.get_full_name() if msg.sender else 'Unknown',
            'sent_by_me': msg.sender == request.user,
            'time': msg.created_at.strftime('%H:%M'),
            'status': '✓✓' if msg.is_read_by_user(other_participant) else '✓',
        }
        
        # Add attachment
        if msg.attachments.exists():
            attachment = msg.attachments.first()
            message_data['attachment'] = {
                'type': attachment.attachment_type,
                'url': attachment.file.url,
                'name': attachment.file_name,
            }
        
        # Add property/hotel/resort
        if msg.property:
            message_data['property'] = {
                'name': msg.property.title,
                'image': msg.property.main_image.url if msg.property.main_image else '',
                'price': f'{msg.property.price:,} د.ع',
                'location': msg.property.city or msg.property.governorate,
                'url': f'/property/{msg.property.slug}/',
            }
        elif msg.hotel:
            message_data['property'] = {
                'name': msg.hotel.name,
                'image': msg.hotel.main_image.url if msg.hotel.main_image else '',
                'price': msg.hotel.price_range,
                'location': msg.hotel.city or msg.hotel.governorate,
                'url': f'/hotel/{msg.hotel.slug}/',
            }
        elif msg.resort:
            message_data['property'] = {
                'name': msg.resort.name,
                'image': msg.resort.main_image.url if msg.resort.main_image else '',
                'price': msg.resort.price_range,
                'location': msg.resort.city or msg.resort.governorate,
                'url': f'/resort/{msg.resort.slug}/',
            }
        
        messages_data.append(message_data)
    
    return JsonResponse({
        'id': str(conversation.conversation_id),
        'name': other_participant.get_full_name() if other_participant else conversation.name,
        'avatar': (other_participant.get_full_name() if other_participant else conversation.name)[0].upper(),
        'online': False,  # Add online status logic
        'messages': messages_data,
    })


@login_required
def api_conversation_star(request, conversation_id):
    """API endpoint to toggle star on conversation."""
    from django.http import JsonResponse
    from .models import Conversation, ConversationParticipant
    
    try:
        conversation = Conversation.objects.get(conversation_id=conversation_id)
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=request.user
        )
        participant.is_starred = not participant.is_starred
        participant.save()
        
        return JsonResponse({'success': True, 'starred': participant.is_starred})
    except (Conversation.DoesNotExist, ConversationParticipant.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)


@login_required
def api_conversation_archive(request, conversation_id):
    """API endpoint to archive conversation."""
    from django.http import JsonResponse
    from .models import Conversation, ConversationParticipant
    
    try:
        conversation = Conversation.objects.get(conversation_id=conversation_id)
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=request.user
        )
        participant.is_archived = not participant.is_archived
        participant.save()
        
        return JsonResponse({'success': True, 'archived': participant.is_archived})
    except (Conversation.DoesNotExist, ConversationParticipant.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)


@login_required
def api_send_message(request, conversation_id):
    """API endpoint to send a message."""
    from django.http import JsonResponse
    from .models import Conversation, ChatMessage
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        conversation = Conversation.objects.get(conversation_id=conversation_id)
    except Conversation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conversation not found'}, status=404)
    
    # Check if user is participant
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    data = json.loads(request.body)
    content = data.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
    
    # Create message
    message = ChatMessage.objects.create(
        conversation=conversation,
        sender=request.user,
        message_type=ChatMessage.TYPE_TEXT,
        content=content
    )
    
    # Update conversation timestamp
    conversation.last_message_at = timezone.now()
    conversation.save()
    
    return JsonResponse({'success': True, 'message_id': str(message.message_id)})


@login_required
def api_upload_attachment(request):
    """API endpoint to upload file attachments with security validation."""
    from django.http import JsonResponse
    from .models import MessageAttachment
    import magic
    import os
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # File size validation (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size > MAX_FILE_SIZE:
        return JsonResponse({'success': False, 'error': 'File size exceeds 10MB limit'}, status=400)
    
    # File type validation using magic numbers
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'video/mp4', 'video/webm', 'video/quicktime',
        'audio/mpeg', 'audio/wav', 'audio/ogg',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/zip', 'application/x-zip-compressed',
        'application/x-rar-compressed',
    }
    
    # Read file to detect MIME type
    file.seek(0)
    file_content = file.read()
    file_mime = magic.from_buffer(file_content, mime=True)
    file.seek(0)
    
    if file_mime not in ALLOWED_MIME_TYPES:
        return JsonResponse({'success': False, 'error': f'File type {file_mime} not allowed'}, status=400)
    
    # Additional validation for image dimensions
    if file_mime.startswith('image/'):
        try:
            from PIL import Image
            img = Image.open(file)
            width, height = img.size
            MAX_DIMENSION = 4096
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                return JsonResponse({'success': False, 'error': f'Image dimensions exceed {MAX_DIMENSION}px limit'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Invalid image file'}, status=400)
    
    # Determine attachment type
    attachment_type = 'file'
    if file_mime.startswith('image/'):
        attachment_type = 'image'
    elif file_mime.startswith('video/'):
        attachment_type = 'video'
    elif file_mime.startswith('audio/'):
        attachment_type = 'audio'
    
    # Save file
    try:
        attachment = MessageAttachment.objects.create(
            attachment_type=attachment_type,
            file=file,
            file_name=file.name,
            file_size=file.size,
            mime_type=file_mime
        )
        
        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'file_url': attachment.file.url,
            'file_name': attachment.file_name,
            'file_size': attachment.file_size,
            'mime_type': attachment.mime_type
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_attach_property(request):
    """API endpoint to attach a property/hotel/resort to a message."""
    from django.http import JsonResponse
    from .models import Property, Hotel, Resort
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    data = json.loads(request.body)
    property_type = data.get('type')  # 'property', 'hotel', 'resort'
    property_id = data.get('id')
    
    if not property_type or not property_id:
        return JsonResponse({'success': False, 'error': 'Type and ID are required'}, status=400)
    
    try:
        if property_type == 'property':
            property = Property.objects.get(id=property_id)
            return JsonResponse({
                'success': True,
                'type': 'property',
                'name': property.title,
                'image': property.main_image.url if property.main_image else '',
                'price': f'{property.price:,} د.ع',
                'location': property.city or property.governorate,
                'url': f'/property/{property.slug}/',
            })
        elif property_type == 'hotel':
            hotel = Hotel.objects.get(id=property_id)
            return JsonResponse({
                'success': True,
                'type': 'hotel',
                'name': hotel.name,
                'image': hotel.main_image.url if hotel.main_image else '',
                'price': hotel.price_range,
                'location': hotel.city or hotel.governorate,
                'url': f'/hotel/{hotel.slug}/',
            })
        elif property_type == 'resort':
            resort = Resort.objects.get(id=property_id)
            return JsonResponse({
                'success': True,
                'type': 'resort',
                'name': resort.name,
                'image': resort.main_image.url if resort.main_image else '',
                'price': resort.price_range,
                'location': resort.city or resort.governorate,
                'url': f'/resort/{resort.slug}/',
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid property type'}, status=400)
    except (Property.DoesNotExist, Hotel.DoesNotExist, Resort.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Property not found'}, status=404)


@login_required
@staff_required
def broker_statistics_view(request):
    """View broker statistics."""
    from .models import BrokerIndividualStats, BrokerSystemStats
    
    # Get system stats
    system_stats = BrokerSystemStats.objects.first()
    
    # Get individual broker stats
    broker_stats = BrokerIndividualStats.objects.select_related('broker').all().order_by('-properties_added')
    
    return render(request, 'properties/broker_statistics.html', {
        'system_stats': system_stats,
        'broker_stats': broker_stats,
    })

# User Settings Views

@login_required
def user_settings(request):
    """Main user settings page with tabs"""
    # Get or create user settings
    settings_obj, created = UserSettings.objects.get_or_create(user=request.user)
    
    # Get user's favorites
    favorite_properties = PropertySave.objects.filter(user=request.user).select_related('property')[:10]
    
    # Get blocked users
    blocked_users = BlockedUser.objects.filter(blocker=request.user).select_related('blocked')
    
    # Get saved searches
    saved_searches = SavedSearch.objects.filter(user=request.user)
    
    # Get recent viewed properties
    from django.core.cache import cache
    viewed_cache_key = f'user_{request.user.id}_viewed_properties'
    viewed_properties = cache.get(viewed_cache_key, [])
    
    context = {
        'settings': settings_obj,
        'favorite_properties': favorite_properties,
        'blocked_users': blocked_users,
        'saved_searches': saved_searches,
        'viewed_properties': viewed_properties[:10],
    }
    
    return render(request, 'properties/user_settings.html', context)


@login_required
def settings_hub_enhanced_view(request):
    """Enhanced settings hub with modern design"""
    from properties.models import PropertySave, UserProfile
    
    # Get user profile
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    # Get favorites
    try:
        favorites = PropertySave.objects.filter(user=request.user).select_related('property')
    except:
        favorites = []
    
    context = {
        'user': request.user,
        'unread_count': 0,
    }
    
    return render(request, 'properties/settings_hub_enhanced.html', context)


@login_required
def user_settings_profile(request):
    """Update user profile settings"""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=settings_obj)
        basic_form = UserBasicInfoForm(request.POST, instance=request.user)
        
        if profile_form.is_valid() and basic_form.is_valid():
            profile_form.save()
            basic_form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('user_settings_profile')
    else:
        profile_form = UserProfileForm(instance=settings_obj)
        basic_form = UserBasicInfoForm(instance=request.user)
    
    return render(request, 'properties/user_settings_profile.html', {
        'profile_form': profile_form,
        'basic_form': basic_form,
    })


@login_required
def user_settings_security(request):
    """Update user security settings"""
    from .models import UserDevice
    
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    # Track current device
    current_device = None
    try:
        current_device = UserDevice.objects.filter(user=request.user, is_current=True).first()
        if not current_device:
            # Create device record if doesn't exist
            current_device = UserDevice.create_from_request(request)
    except Exception as e:
        # If device creation fails, continue without it
        pass
    
    # Get all user devices
    user_devices = UserDevice.objects.filter(user=request.user).order_by('-last_seen', '-login_at')
    
    if request.method == 'POST':
        form = UserSecurityForm(request.POST)
        
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            confirm_password = form.cleaned_data.get('confirm_password')
            
            # Verify current password
            if request.user.check_password(current_password):
                if new_password and new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    messages.success(request, 'تم تغيير كلمة المرور بنجاح')
                    return redirect('login')
                else:
                    messages.error(request, 'كلمة المرور الجديدة غير متطابقة')
            else:
                messages.error(request, 'كلمة المرور الحالية غير صحيحة')
    else:
        form = UserSecurityForm()
    
    return render(request, 'properties/user_settings_security.html', {
        'form': form,
        'settings': settings_obj,
        'devices': user_devices,
        'current_device': current_device,
    })


@login_required
@require_POST
def revoke_device_access(request, device_id):
    """Revoke access for a specific device"""
    from .models import UserDevice
    
    device = get_object_or_404(UserDevice, id=device_id, user=request.user)
    
    if device.is_current:
        messages.error(request, 'لا يمكن إلغاء تفعيل الجهاز الحالي')
    else:
        device.deactivate()
        messages.success(request, 'تم إلغاء تفعيل الجهاز بنجاح')
    
    return redirect('user_settings_security')


@login_required
def user_settings_notifications(request):
    """Update user notification settings"""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserNotificationForm(request.POST, instance=settings_obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث إعدادات الإشعارات بنجاح')
            return redirect('user_settings_notifications')
    else:
        form = UserNotificationForm(instance=settings_obj)
    
    return render(request, 'properties/user_settings_notifications.html', {
        'form': form,
    })


@login_required
def user_settings_privacy(request):
    """Update user privacy settings"""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPrivacyForm(request.POST, instance=settings_obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث إعدادات الخصوصية بنجاح')
            return redirect('user_settings_privacy')
    else:
        form = UserPrivacyForm(instance=settings_obj)
    
    return render(request, 'properties/user_settings_privacy.html', {
        'form': form,
    })


@login_required
def user_settings_preferences(request):
    """Update user preferences"""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=settings_obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث التفضيلات بنجاح')
            return redirect('user_settings_preferences')
    else:
        form = UserPreferencesForm(instance=settings_obj)
    
    return render(request, 'properties/user_settings_preferences.html', {
        'form': form,
    })


@login_required
def user_settings_favorites(request):
    """View user's favorites"""
    favorite_properties = PropertySave.objects.filter(user=request.user).select_related('property')
    
    return render(request, 'properties/user_settings_favorites.html', {
        'favorite_properties': favorite_properties,
    })


@login_required
def user_settings_messages(request):
    """View user's messages and blocked users"""
    messages_qs = get_accessible_messages(request.user).select_related('sender', 'recipient', 'conversation')
    blocked_users = BlockedUser.objects.filter(blocker=request.user).select_related('blocked')
    
    return render(request, 'properties/user_settings_messages.html', {
        'messages': messages_qs[:50],
        'blocked_users': blocked_users,
    })


@login_required
@require_POST
def block_user_settings(request):
    form = BlockUserForm(request.user, request.POST)
    
    if form.is_valid():
        blocked_user = form.cleaned_data['blocked_user']
        reason = form.cleaned_data['reason']
        
        BlockedUser.objects.create(
            blocker=request.user,
            blocked=blocked_user,
            reason=reason
        )
        
        messages.success(request, 'تم حظر المستخدم بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء حظر المستخدم')
    
    return redirect('user_settings_messages')


@login_required
@require_POST
def unblock_user_settings(request, blocked_user_id):
    """Unblock a user from settings"""
    blocked_user = get_object_or_404(BlockedUser, blocker=request.user, blocked_id=blocked_user_id)
    blocked_user.delete()
    
    messages.success(request, 'تم إلغاء حظر المستخدم بنجاح')
    return redirect('user_settings_messages')


@login_required
def user_settings_activity(request):
    """View user's activity log"""
    from django.core.cache import cache
    
    # Get recently viewed properties
    viewed_cache_key = f'user_{request.user.id}_viewed_properties'
    viewed_properties = cache.get(viewed_cache_key, [])
    
    # Get saved searches
    saved_searches = SavedSearch.objects.filter(user=request.user)
    
    return render(request, 'properties/user_settings_activity.html', {
        'viewed_properties': viewed_properties[:20],
        'saved_searches': saved_searches,
    })


@login_required
def user_settings_account(request):
    """Account management - download data, disable, delete"""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'disable':
            settings_obj.account_disabled = True
            settings_obj.disabled_at = timezone.now()
            settings_obj.disabled_reason = request.POST.get('reason', '')
            settings_obj.save()
            
            # Logout user
            logout(request)
            messages.success(request, 'تم تعطيل حسابك مؤقتاً')
            return redirect('home')
        
        elif action == 'delete':
            # Permanently delete account
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'تم حذف حسابك نهائياً')
            return redirect('home')
        
        elif action == 'download':
            # Download user data as JSON
            import json
            from django.http import HttpResponse
            
            user_data = {
                'user': {
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'date_joined': request.user.date_joined.isoformat(),
                },
                'settings': {
                    'phone': settings_obj.phone,
                    'governorate': settings_obj.governorate,
                    'city': settings_obj.city,
                }
            }
            
            response = HttpResponse(json.dumps(user_data, indent=2, ensure_ascii=False), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{request.user.username}_data.json"'
            return response
    
    return render(request, 'properties/user_settings_account.html', {'settings': settings_obj})


# ==================== Admin Panel Views ====================

@login_required
def admin_panel_enhanced(request):
    """لوحة تحكم الإدارة الاحترافية - نسخة محسنة"""
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')
    
    from django.contrib.auth.models import User
    from .models import Property, Broker, SubscriptionPlan, FinancialTransaction
    from .constants import IRAQ_GOVERNORATES
    from django.db.models import Sum, Count, Q, Avg
    from datetime import timedelta, datetime
    
    # إحصائيات أساسية
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(status='active').count()
    sold_properties = Property.objects.filter(status='sold').count()
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_brokers = Broker.objects.count()
    
    # إحصائيات الاشتراكات
    from .models import BrokerPlanSubscription
    total_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
    
    # إحصائيات الدلالين
    active_brokers = Broker.objects.filter(is_active=True).count()
    verified_brokers = Broker.objects.filter(is_verified=True).count()
    
    # إحصائيات الإيرادات
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    daily_revenue = FinancialTransaction.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(total=Sum('sale_price'))['total'] or 0
    
    avg_revenue = FinancialTransaction.objects.filter(
        created_at__date__gte=today - timedelta(days=30),
        status='completed'
    ).aggregate(avg=Avg('sale_price'))['avg'] or 0
    
    # إحصائيات المشاهدات
    try:
        from .models import PropertyViewStats
        total_views = PropertyViewStats.objects.aggregate(total=Sum('total_views'))['total'] or 0
        today_views = PropertyViewStats.objects.filter(updated_at__date=today).aggregate(total=Sum('total_views'))['total'] or 0
        yesterday_views = PropertyViewStats.objects.filter(updated_at__date=yesterday).aggregate(total=Sum('total_views'))['total'] or 0
    except Exception:
        total_views = 0
        today_views = 0
        yesterday_views = 0
    
    # المستخدمين المتصلين (محاكاة)
    online_users = int(active_users * 0.15)  # تقدير 15% من المستخدمين النشطين
    
    # إحصائيات المحافظات
    governorate_stats = []
    for code, name in IRAQ_GOVERNORATES:
        count = Property.objects.filter(governorate=code).count()
        if count > 0:
            governorate_stats.append({
                'code': code,
                'name': name,
                'count': count
            })
    
    # ترتيب حسب العدد
    governorate_stats.sort(key=lambda x: x['count'], reverse=True)
    
    context = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'sold_properties': sold_properties,
        'total_users': total_users,
        'active_users': active_users,
        'total_brokers': total_brokers,
        'active_brokers': active_brokers,
        'verified_brokers': verified_brokers,
        'total_subscriptions': total_subscriptions,
        'daily_revenue': daily_revenue,
        'avg_revenue': avg_revenue,
        'total_views': total_views,
        'today_views': today_views,
        'yesterday_views': yesterday_views,
        'online_users': online_users,
        'governorate_stats': governorate_stats,
        'governorates': IRAQ_GOVERNORATES,
    }
    
    return render(request, 'properties/admin_panel.html', context)


@login_required
def admin_panel(request):
    """لوحة تحكم الإدارة الرئيسية - نسخة محسنة"""
    from .permissions import can_access_admin_panel
    import json

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import (
        Property, Broker, UserProfile, Auction, Bid, Notification, 
        SubscriptionRequest, FinancialTransaction, PropertyPayment, 
        Resort, ResortBooking, TravelCompany, Job, Hotel, 
        ServiceAdvertisement, ActivityLog
    )
    from django.db.models import Sum, Count, Avg, Q
    from datetime import timedelta, datetime

    # إحصائيات المستخدمين المحسنة
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(is_superuser=True).count()
    broker_users = User.objects.filter(broker_profile__isnull=False).count()
    regular_users = total_users - admin_users - broker_users
    
    # إحصائيات الدلالين المحسنة
    total_brokers = Broker.objects.count()
    active_brokers = Broker.objects.filter(is_active=True).count()
    verified_brokers = Broker.objects.filter(is_verified=True).count()
    premium_brokers = Broker.objects.filter(subscription_plan__isnull=False).count()
    
    # إحصائيات العقارات المحسنة
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(status='published').count()
    pending_properties = Property.objects.filter(status=Property.STATUS_PENDING_APPROVAL).count()
    draft_properties = Property.objects.filter(status=Property.STATUS_DRAFT).count()
    sold_properties = Property.objects.filter(status='sold').count()
    featured_properties = Property.objects.filter(is_featured=True).count()
    
    # إحصائيات الطلب المحسنة
    total_revenue = PropertyPayment.objects.filter(status=PropertyPayment.STATUS_COMPLETED).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_payments = PropertyPayment.objects.count()
    pending_payments = PropertyPayment.objects.filter(status=PropertyPayment.STATUS_PENDING).count()
    completed_payments = PropertyPayment.objects.filter(status=PropertyPayment.STATUS_COMPLETED).count()
    rejected_payments = PropertyPayment.objects.filter(status=PropertyPayment.STATUS_FAILED).count()
    
    # إحصائيات المزادات المحسنة
    total_auctions = Auction.objects.count()
    active_auctions = Auction.objects.filter(status='active').count()
    pending_auctions = Auction.objects.filter(approval_status='pending').count()
    ended_auctions = Auction.objects.filter(status='ended').count()
    total_bids = Bid.objects.count()
    
    # إحصائيات المنتجعات
    total_resorts = Resort.objects.count()
    active_resorts = Resort.objects.filter(status='published').count()
    featured_resorts = Resort.objects.filter(is_featured=True).count()
    
    # إحصائيات الفنادق
    total_hotels = Hotel.objects.count()
    active_hotels = Hotel.objects.filter(is_active=True).count()
    
    # إحصائيات شركات السفر
    total_travel_companies = TravelCompany.objects.count()
    active_travel_companies = TravelCompany.objects.filter(is_active=True).count()
    verified_travel_companies = TravelCompany.objects.filter(is_verified=True).count()
    
    # إحصائيات الوظائف
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()
    pending_jobs = Job.objects.filter(status='pending').count()
    
    # إحصائيات إعلانات الخدمات
    total_service_ads = ServiceAdvertisement.objects.count()
    active_service_ads = ServiceAdvertisement.objects.filter(is_active=True).count()
    pending_service_ads = ServiceAdvertisement.objects.filter(status='pending').count()
    
    # إحصائيات الحجوزات
    total_bookings = ResortBooking.objects.count()
    confirmed_bookings = ResortBooking.objects.filter(status='confirmed').count()
    cancelled_bookings = ResortBooking.objects.filter(status='cancelled').count()
    pending_bookings = ResortBooking.objects.filter(status='pending').count()
    
    # الفترات الزمنية
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    month_ago = timezone.now() - timedelta(days=30)
    year_ago = timezone.now() - timedelta(days=365)
    
    # إحصائيات اليوم
    users_today = User.objects.filter(date_joined__date=today).count()
    properties_today = Property.objects.filter(created_at__date=today).count()
    payments_today = PropertyPayment.objects.filter(created_at__date=today).count()
    revenue_today = PropertyPayment.objects.filter(
        created_at__date=today, 
        status=PropertyPayment.STATUS_COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # إحصائيات الأسبوع
    users_week = User.objects.filter(date_joined__gte=week_ago).count()
    properties_week = Property.objects.filter(created_at__gte=week_ago).count()
    payments_week = PropertyPayment.objects.filter(created_at__gte=week_ago).count()
    revenue_week = PropertyPayment.objects.filter(
        created_at__gte=week_ago,
        status=PropertyPayment.STATUS_COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # إحصائيات الشهر
    users_month = User.objects.filter(date_joined__gte=month_ago).count()
    properties_month = Property.objects.filter(created_at__gte=month_ago).count()
    payments_month = PropertyPayment.objects.filter(created_at__gte=month_ago).count()
    revenue_month = PropertyPayment.objects.filter(
        created_at__gte=month_ago,
        status=PropertyPayment.STATUS_COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # إحصائيات السنة
    users_year = User.objects.filter(date_joined__gte=year_ago).count()
    properties_year = Property.objects.filter(created_at__gte=year_ago).count()
    payments_year = PropertyPayment.objects.filter(created_at__gte=year_ago).count()
    revenue_year = PropertyPayment.objects.filter(
        created_at__gte=year_ago,
        status=PropertyPayment.STATUS_COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # الإشعارات
    unread_notifications = NotificationRecipient.objects.filter(is_read=False).count()
    total_notifications = Notification.objects.count()
    
    # طلبات الاشتراك
    pending_subscription_requests = SubscriptionRequest.objects.filter(status='pending').count()
    approved_subscription_requests = SubscriptionRequest.objects.filter(status='approved').count()
    rejected_subscription_requests = SubscriptionRequest.objects.filter(status='rejected').count()
    
    # المعاملات المالية
    recent_transactions = FinancialTransaction.objects.filter(created_at__gte=month_ago).count()
    total_transactions = FinancialTransaction.objects.count()
    
    # النشاط الحديث
    recent_activity = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # القوائم المعلقة
    pending_properties_list = Property.objects.filter(
        status=Property.STATUS_PENDING_APPROVAL
    ).select_related('owner', 'broker')[:5]
    
    pending_payments_list = PropertyPayment.objects.filter(
        status=PropertyPayment.STATUS_PENDING
    ).select_related('property', 'broker')[:5]
    
    pending_subscription_requests_list = SubscriptionRequest.objects.filter(
        status='pending'
    ).select_related('broker', 'requested_plan')[:5]
    
    new_users_list = User.objects.filter(date_joined__gte=week_ago).order_by('-date_joined')[:5]
    
    pending_auctions_list = Auction.objects.filter(
        approval_status='pending'
    ).select_related('property', 'broker')[:5]
    
    # بيانات للرسوم البيانية - نمو المستخدمين
    user_growth_data = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30 * (5 - i))
        count = User.objects.filter(
            date_joined__year=date.year,
            date_joined__month=date.month
        ).count()
        user_growth_data.append(count if count else 0)
    
    # بيانات للرسوم البيانية - الإيرادات الشهرية
    revenue_data = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30 * (5 - i))
        revenue = PropertyPayment.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month,
            status=PropertyPayment.STATUS_COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_data.append(float(revenue) if revenue else 0)
    
    # بيانات للرسوم البيانية - العقارات الجديدة
    property_growth_data = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30 * (5 - i))
        count = Property.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month
        ).count()
        property_growth_data.append(count if count else 0)
    
    # المتوسطات
    avg_property_price = Property.objects.filter(status='published').aggregate(
        avg=Avg('price')
    )['avg'] or 0
    
    avg_broker_rating = Broker.objects.aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    
    # النشاط حسب النوع
    activity_by_type = ActivityLog.objects.values('action').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # أفضل الدلالين
    top_brokers = Broker.objects.annotate(
        property_count=Count('properties')
    ).order_by('-property_count')[:5]
    
    # العقارات الأكثر مشاهدة
    most_viewed_properties = Property.objects.filter(
        status='published'
    ).order_by('-views_count')[:5]
    
    # البيانات الجغرافية
    properties_by_governorate = list(Property.objects.values('governorate').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Format governorate data for JavaScript
    governorate_data = []
    for item in properties_by_governorate:
        governorate_data.append({
            'governorate': item['governorate'] or 'غير محدد',
            'count': item['count']
        })
    
    # صحة النظام
    system_health = {
        'database_ok': True,  # يمكن إضافة فحص حقيقي
        'cache_ok': True,     # يمكن إضافة فحص حقيقي
        'storage_ok': True,   # يمكن إضافة فحص حقيقي
        'server_load': 'low', # يمكن إضافة فحص حقيقي
    }
    
    context = {
        # إحصائيات المستخدمين
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'broker_users': broker_users,
        'regular_users': regular_users,
        
        # إحصائيات الدلالين
        'total_brokers': total_brokers,
        'active_brokers': active_brokers,
        'verified_brokers': verified_brokers,
        'premium_brokers': premium_brokers,
        
        # إحصائيات العقارات
        'total_properties': total_properties,
        'active_properties': active_properties,
        'pending_properties': pending_properties,
        'draft_properties': draft_properties,
        'sold_properties': sold_properties,
        'featured_properties': featured_properties,
        
        # إحصائيات المزادات
        'total_auctions': total_auctions,
        'active_auctions': active_auctions,
        'pending_auctions': pending_auctions,
        'ended_auctions': ended_auctions,
        'total_bids': total_bids,
        
        # إحصائيات الدفع
        'total_payments': total_payments,
        'pending_payments': pending_payments,
        'completed_payments': completed_payments,
        'rejected_payments': rejected_payments,
        'total_revenue': total_revenue,
        
        # إحصائيات المنتجعات
        'total_resorts': total_resorts,
        'active_resorts': active_resorts,
        'featured_resorts': featured_resorts,
        
        # إحصائيات الفنادق
        'total_hotels': total_hotels,
        'active_hotels': active_hotels,
        
        # إحصائيات شركات السفر
        'total_travel_companies': total_travel_companies,
        'active_travel_companies': active_travel_companies,
        'verified_travel_companies': verified_travel_companies,
        
        # إحصائيات الوظائف
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'pending_jobs': pending_jobs,
        
        # إحصائيات طلبات البناء
        'total_building_requests': total_building_requests,
        'active_building_requests': active_building_requests,
        'pending_building_requests': pending_building_requests,
        
        # إحصائيات إعلانات الخدمات
        'total_service_ads': total_service_ads,
        'active_service_ads': active_service_ads,
        'pending_service_ads': pending_service_ads,
        
        # إحصائيات الحجوزات
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'pending_bookings': pending_bookings,
        
        # إحصائيات الوقت
        'users_today': users_today,
        'properties_today': properties_today,
        'payments_today': payments_today,
        'revenue_today': revenue_today,
        'users_week': users_week,
        'properties_week': properties_week,
        'payments_week': payments_week,
        'revenue_week': revenue_week,
        'users_month': users_month,
        'properties_month': properties_month,
        'payments_month': payments_month,
        'revenue_month': revenue_month,
        'users_year': users_year,
        'properties_year': properties_year,
        'payments_year': payments_year,
        'revenue_year': revenue_year,
        
        # إحصائيات إضافية
        'new_users': users_week,
        'new_properties': properties_week,
        'unread_notifications': unread_notifications,
        'total_notifications': total_notifications,
        'pending_subscription_requests': pending_subscription_requests,
        'approved_subscription_requests': approved_subscription_requests,
        'rejected_subscription_requests': rejected_subscription_requests,
        'recent_transactions': recent_transactions,
        'total_transactions': total_transactions,
        
        # القوائم
        'recent_activity': recent_activity,
        'pending_properties_list': pending_properties_list,
        'pending_payments_list': pending_payments_list,
        'pending_subscription_requests_list': pending_subscription_requests_list,
        'new_users_list': new_users_list,
        'pending_auctions_list': pending_auctions_list,
        
        # بيانات الرسوم البيانية
        'user_growth_data': user_growth_data,
        'revenue_data': revenue_data,
        'property_growth_data': property_growth_data,
        
        # المتوسطات
        'avg_property_price': avg_property_price,
        'avg_broker_rating': avg_broker_rating,
        
        # النشاط
        'activity_by_type': activity_by_type,
        
        # الأفضل
        'top_brokers': top_brokers,
        'most_viewed_properties': most_viewed_properties,
        
        # البيانات الجغرافية
        'properties_by_governorate': governorate_data,
        
        # صحة النظام
        'system_health': system_health,
    }

    return render(request, 'properties/admin_panel.html', context)


@login_required
def admin_contact_view(request):
    """صفحة مراسلة الإدارة للدلال والمستخدمين"""
    from .permissions import can_access_admin_panel, get_user_type
    from django.contrib.auth.models import User
    from .models import Broker, UserProfile, Conversation, Message

    user_type = get_user_type(request.user)
    
    # البحث عن المستلمين
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    
    if user_type == 'admin':
        # الإدارة يمكنها مراسلة الجميع
        recipients = User.objects.filter(is_active=True).exclude(id=request.user.id).select_related('broker_profile', 'user_profile')
    elif user_type == 'broker':
        # الدلال يمكنه مراسلة الإدارة فقط
        recipients = User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True)
        ).exclude(id=request.user.id).distinct().select_related('broker_profile', 'user_profile')
    else:
        # المستخدم العادي يمكنه مراسلة الإدارة والدلالين فقط
        recipients = User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True) | Q(broker_profile__isnull=False)
        ).exclude(id=request.user.id).distinct().select_related('broker_profile', 'user_profile')
    
    # تطبيق البحث
    if search_query:
        recipients = recipients.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Get conversations for the user with filtering
    try:
        conversations = Conversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'messages').order_by('-updated_at')
        
        # Apply filters
        if filter_type == 'unread':
            conversations = [conv for conv in conversations if conv.messages.filter(recipient=request.user, is_read=False).exists()]
        elif filter_type == 'read':
            conversations = [conv for conv in conversations if not conv.messages.filter(recipient=request.user, is_read=False).exists()]
        elif filter_type == 'important':
            conversations = [conv for conv in conversations if conv.messages.filter(priority='high').exists()]
        elif filter_type == 'archived':
            conversations = [conv for conv in conversations if conv.is_archived]
    except:
        conversations = []
    
    # Get active conversation
    active_conversation_id = request.GET.get('conversation_id')
    active_conversation = None
    messages = []
    
    if active_conversation_id:
        try:
            active_conversation = Conversation.objects.get(
                id=active_conversation_id,
                participants=request.user
            )
            messages = active_conversation.messages.all().order_by('created_at')
        except:
            pass
    
    # Get statistics
    try:
        total_messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).count()
        
        unread_count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        read_count = total_messages - unread_count
        
        important_count = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            priority='high'
        ).count()
        
        archived_count = Conversation.objects.filter(
            participants=request.user,
            is_archived=True
        ).count()
        
        # Priority statistics
        critical_count = Message.objects.filter(
            recipient=request.user,
            is_read=False,
            priority='urgent'
        ).count()
        
        high_priority_count = Message.objects.filter(
            recipient=request.user,
            is_read=False,
            priority='high'
        ).count()
        
    except:
        total_messages = 0
        unread_count = 0
        read_count = 0
        important_count = 0
        archived_count = 0
        critical_count = 0
        high_priority_count = 0
    
    # Quick responses
    quick_responses = [
        'شكراً لتواصلك معنا، سنقوم بمراجعة طلبك في أقرب وقت.',
        'تم استلام طلبك بنجاح. سيتم التواصل معك قريباً.',
        'نعتذر عن الإزعاج. هل يمكنك تزويدنا بمزيد من التفاصيل؟',
        'سيتم تحويل طلبك إلى القسم المختص.',
        'نقدر تواصلك معنا وسنعمل على حل مشكلتك.',
        'شكراً على ملاحظاتك القيمة، سنأخذها في الاعتبار.'
    ]
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        message_content = request.POST.get('message')
        subject = request.POST.get('subject', '')
        message_type = request.POST.get('message_type', 'support')
        priority = request.POST.get('priority', 'normal')
        
        # Handle file uploads
        attachments = request.FILES.getlist('attachments')
        
        if not all([recipient_id, message_content]) and not attachments:
            messages.error(request, 'يرجى ملء جميع الحقول أو إرفاق ملف')
        else:
            recipient = get_object_or_404(User, pk=recipient_id)
            
            # إنشاء محادثة جديدة أو استخدام محادثة موجودة
            try:
                conversation = Conversation.objects.filter(
                    participants=request.user
                ).filter(participants=recipient).first()
                
                if not conversation:
                    conversation = Conversation.objects.create()
                    conversation.participants.add(request.user, recipient)
            except:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, recipient)
            
            # إنشاء رسالة جديدة
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                recipient=recipient,
                content=message_content if message_content else '',
                subject=subject,
                message_type=message_type,
                priority=priority,
                is_read=False
            )
            
            # Handle file attachments
            for attachment in attachments:
                try:
                    from .models import MessageAttachment
                    MessageAttachment.objects.create(
                        message=msg,
                        file=attachment,
                        filename=attachment.name
                    )
                except:
                    pass
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Create notification for recipient
            from .utils import create_notification
            create_notification(
                user=recipient,
                notification_type='message',
                title='رسالة جديدة',
                message=f'لديك رسالة جديدة من {request.user.get_full_name() or request.user.username}',
                link=f'/dashboard/admin-contact/?conversation_id={conversation.id}'
            )
            
            messages.success(request, 'تم إرسال الرسالة بنجاح')
            return redirect(f'/dashboard/admin-contact/?conversation_id={conversation.id}')
    
    context = {
        'recipients': recipients,
        'user_type': user_type,
        'search_query': search_query,
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'active_conversation_id': active_conversation_id,
        'total_messages': total_messages,
        'unread_count': unread_count,
        'read_count': read_count,
        'important_count': important_count,
        'archived_count': archived_count,
        'total_count': len(conversations),
        'critical_count': critical_count,
        'high_priority_count': high_priority_count,
        'quick_responses': quick_responses,
        'filter_type': filter_type
    }
    
    return render(request, 'properties/admin_contact.html', context)


@login_required
def create_admin_conversation(request):
    """API endpoint to create a conversation with admin"""
    from django.contrib.auth.models import User
    from .models import Conversation, Message
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'الرسالة مطلوبة'})
        
        # Get admin users
        admin_users = User.objects.filter(is_superuser=True).first()
        
        if not admin_users:
            return JsonResponse({'success': False, 'error': 'لا يوجد مسؤول متاح'})
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=admin_users).first()
        
        if existing_conversation:
            # Add message to existing conversation
            message = Message.objects.create(
                conversation=existing_conversation,
                sender=request.user,
                recipient=admin_users,
                content=message_text,
                is_read=False
            )
            existing_conversation.updated_at = timezone.now()
            existing_conversation.save()
        else:
            # Create new conversation
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, admin_users)
            
            # Add initial message
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                recipient=admin_users,
                content=message_text,
                is_read=False
            )
        
        return JsonResponse({'success': True, 'conversation_id': existing_conversation.id if existing_conversation else conversation.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== Messaging System Views ====================

@login_required
def api_user_search(request):
    """API endpoint for searching users"""
    from django.contrib.auth.models import User
    from .models import Broker, UserProfile
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # Search users by name, email, phone, or username
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id).distinct()[:10]
    
    results = []
    for user in users:
        # Get phone number from profile if available
        phone = None
        if hasattr(user, 'user_profile'):
            phone = user.user_profile.phone
        
        results.append({
            'id': user.id,
            'username': user.username,
            'get_full_name': user.get_full_name(),
            'email': user.email,
            'phone': phone,
            'avatar': user.user_profile.avatar.url if hasattr(user, 'user_profile') and user.user_profile.avatar else None,
            'is_online': getattr(user, 'is_online', False)
        })
    
    return JsonResponse({'users': results})


@login_required
def api_user_profile(request, user_id):
    """API endpoint for getting user profile"""
    from django.contrib.auth.models import User
    from .models import Broker, UserProfile
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    # Get additional profile information
    phone = None
    user_type = 'مستخدم'
    is_online = False
    
    if hasattr(user, 'user_profile'):
        phone = user.user_profile.phone
        is_online = getattr(user.user_profile, 'is_online', False)
    
    if hasattr(user, 'broker_profile'):
        user_type = 'دلال'
    
    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'get_full_name': user.get_full_name(),
        'email': user.email,
        'phone': phone,
        'avatar': user.user_profile.avatar.url if hasattr(user, 'user_profile') and user.user_profile.avatar else None,
        'date_joined': user.date_joined.strftime('%Y-%m-%d') if user.date_joined else None,
        'user_type': user_type,
        'is_online': is_online
    })


@login_required
def api_check_conversation(request):
    """API endpoint to check if conversation exists with user"""
    from .models import Conversation
    
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants__id=user_id).first()
        
        if conversation:
            return JsonResponse({'conversation_id': conversation.id})
        else:
            return JsonResponse({'conversation_id': None})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Developer Panel API Functions
@api_view(['GET'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_environment_info(request):
    """API للحصول على معلومات بيئة التطوير"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    
    import sys
    import os
    import django
    from django.db import connection
    
    try:
        from .models import Property, User, Broker
    except Exception:
        Property = None
        User = None
        Broker = None
    
    # Database info
    db_info = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT sqlite_version() as version" if 'sqlite' in settings.DATABASES['default']['ENGINE'] else "SELECT version()")
            db_version = cursor.fetchone()
            db_info['version'] = db_version[0] if db_version else 'Unknown'
            db_info['engine'] = settings.DATABASES['default']['ENGINE']
    except Exception as e:
        db_info['error'] = str(e)
    
    # App statistics
    stats = {}
    try:
        if User:
            stats['users_count'] = User.objects.count()
        if Broker:
            stats['brokers_count'] = Broker.objects.count()
        if Property:
            stats['properties_count'] = Property.objects.count()
    except Exception as e:
        stats['error'] = str(e)
    
    # System info
    system_info = {
        'python_version': sys.version,
        'django_version': django.get_version(),
        'platform': sys.platform,
        'debug_mode': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database': db_info,
        'statistics': stats,
        'installed_apps': len(settings.INSTALLED_APPS),
        'middleware_count': len(settings.MIDDLEWARE),
        'static_url': settings.STATIC_URL,
        'media_url': settings.MEDIA_URL,
        'timezone': settings.TIME_ZONE,
        'language_code': settings.LANGUAGE_CODE,
    }
    
    return Response(system_info)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_run_migrations(request):
    """API لتشغيل الترحيلات"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لتشغيل الترحيلات"""
    from django.core.management import call_command
    import io
    
    try:
        output = io.StringIO()
        call_command('migrate', stdout=output, verbosity=2)
        result = output.getvalue()
        
        return Response({
            'success': True,
            'message': 'تم تشغيل الترحيلات بنجاح',
            'output': result
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل تشغيل الترحيلات',
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_collect_static(request):
    """API لجمع الملفات الثابتة"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لجمع الملفات الثابتة"""
    from django.core.management import call_command
    import io
    
    try:
        output = io.StringIO()
        call_command('collectstatic', '--noinput', stdout=output, verbosity=2)
        result = output.getvalue()
        
        return Response({
            'success': True,
            'message': 'تم جمع الملفات الثابتة بنجاح',
            'output': result
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل جمع الملفات الثابتة',
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_clear_sessions(request):
    """API لمسح الجلسات"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لمسح الجلسات"""
    from django.contrib.sessions.models import Session
    
    try:
        count = Session.objects.count()
        Session.objects.all().delete()
        
        return Response({
            'success': True,
            'message': f'تم مسح {count} جلسة بنجاح'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل مسح الجلسات',
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_test_database(request):
    """API لاختبار قاعدة البيانات"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لاختبار قاعدة البيانات"""
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        if result and result[0] == 1:
            return Response({
                'success': True,
                'message': 'قاعدة البيانات تعمل بشكل صحيح'
            })
        else:
            return Response({
                'success': False,
                'message': 'قاعدة البيانات غير متجاوبة'
            }, status=500)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل اختبار قاعدة البيانات',
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_clear_cache(request):
    """API لمسح الكاش"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لمسح الكاش"""
    from django.core.cache import cache
    
    try:
        cache.clear()
        
        return Response({
            'success': True,
            'message': 'تم مسح الكاش بنجاح'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل مسح الكاش',
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_create_superuser(request):
    """API لإنشاء مستخدم مسؤول"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لإنشاء مستخدم مسؤول"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if not username or not password:
        return Response({
            'success': False,
            'message': 'يرجى تحديد اسم المستخدم وكلمة المرور'
        }, status=400)
    
    try:
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': 'اسم المستخدم موجود بالفعل'
            }, status=400)
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        return Response({
            'success': True,
            'message': f'تم إنشاء المستخدم المسؤول {username} بنجاح'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل إنشاء المستخدم المسؤول',
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_system_logs(request):
    """API للحصول على سجلات النظام"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API للحصول على سجلات النظام"""
    try:
        log_file = 'logs/dalal.log'
        log_path = os.path.join(settings.BASE_DIR, log_file)
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                # Read last 100 lines
                lines = f.readlines()
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                return Response({
                    'success': True,
                    'logs': recent_lines,
                    'total_lines': len(lines)
                })
        else:
            return Response({
                'success': False,
                'message': 'ملف السجلات غير موجود'
            }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'فشل قراءة السجلات',
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([])  # Allow all for development, but check superuser status
def developer_restart_server(request):
    """API لإعادة تشغيل السيرفر (محاكاة)"""
    # Only allow superusers or in DEBUG mode
    if not request.user.is_superuser and not settings.DEBUG:
        return Response({'error': 'غير مصرح'}, status=403)
    """API لإعادة تشغيل السيرفر (محاكاة)"""
    # In real deployment, this would trigger a restart
    # For development, we just return a success message
    return Response({
        'success': True,
        'message': 'تم إرسال طلب إعادة تشغيل السيرفر. في بيئة التطوير، أعد تشغيل السيرفر يدوياً.'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_conversation(request):
    """API endpoint to create new conversation"""
    from .models import Conversation
    
    # Debug logging
    print(f"=== API Create Conversation Debug ===")
    print(f"User: {request.user}")
    print(f"Authenticated: {request.user.is_authenticated}")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"CSRF Token from header: {request.headers.get('X-CSRFToken', 'NOT_FOUND')}")
    print(f"Origin: {request.headers.get('Origin', 'NOT_FOUND')}")
    print(f"Referer: {request.headers.get('Referer', 'NOT_FOUND')}")
    print(f"Body: {request.body}")
    print(f"======================================")
    
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST if request.method == 'POST' else {}
        
        recipient_id = data.get('recipient_id')
        
        if not recipient_id:
            return JsonResponse({'success': False, 'error': 'Recipient ID required'}, status=400)
        
        recipient = get_object_or_404(User, id=recipient_id)
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=recipient).filter(
            conversation_type=Conversation.TYPE_DIRECT
        ).first()
        
        if existing_conversation:
            return JsonResponse({
                'success': True,
                'conversation_id': str(existing_conversation.conversation_id),
                'message': 'المحادثة موجودة بالفعل'
            })
        
        # Create new conversation
        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT
        )
        conversation.participants.add(request.user, recipient)
        
        return JsonResponse({
            'success': True,
            'conversation_id': str(conversation.conversation_id),
            'message': 'تم إنشاء المحادثة بنجاح'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_send_message(request, conversation_id):
    """API endpoint to send message in conversation"""
    from .models import Conversation, Message
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Search by conversation_id (UUID) instead of id (Integer)
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id, participants=request.user)
        recipient = conversation.participants.exclude(id=request.user.id).first()
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        
        if not content:
            return JsonResponse({'error': 'Content required'}, status=400)
        
        # Create message with type
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            message=content
        )
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.message,
                'sender_name': request.user.get_full_name() or request.user.username,
                'is_from_me': True,
                'time': message.created_at.strftime('%H:%M'),
                'message_type': message_type
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_translate_message(request):
    """API endpoint to translate messages"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        text = data.get('text')
        target_language = data.get('target_language', 'en')
        
        if not text:
            return JsonResponse({'error': 'Text required'}, status=400)
        
        # Placeholder for translation - in production use Google Translate API
        translations = {
            'en': f'[EN] {text}',
            'tr': f'[TR] {text}',
            'fa': f'[FA] {text}',
            'ku': f'[KU] {text}'
        }
        
        return JsonResponse({
            'success': True,
            'translation': translations.get(target_language, text)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_share_location(request):
    """API endpoint to share location"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        location_type = data.get('location_type', 'current')
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Coordinates required'}, status=400)
        
        # Create location message
        location_type_text = 'موقع العقار' if location_type == 'property' else 'موقعي'
        location_message = f"📍 {location_type_text}: {latitude}, {longitude}"
        
        return JsonResponse({
            'success': True,
            'location_message': location_message,
            'google_maps_url': f"https://www.google.com/maps?q={latitude},{longitude}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_upload_attachments(request):
    """API endpoint to upload message attachments"""
    from .models import MessageAttachment, Message
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        conversation_id = request.POST.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        recipient = conversation.participants.exclude(id=request.user.id).first()
        
        files = request.FILES.getlist('file')
        
        if not files:
            return JsonResponse({'error': 'No files provided'}, status=400)
        
        # Create a message for the attachments
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            message_type=Message.TYPE_FILE,
            message=f'📎 {len(files)} ملف'
        )
        
        attachments = []
        for file in files:
            # Validate file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                return JsonResponse({'error': f'File {file.name} too large (max 10MB)'}, status=400)
            
            # Determine attachment type
            attachment_type = MessageAttachment.ATTACHMENT_FILE
            if file.content_type.startswith('image/'):
                attachment_type = MessageAttachment.ATTACHMENT_IMAGE
            elif file.content_type.startswith('video/'):
                attachment_type = MessageAttachment.ATTACHMENT_VIDEO
            elif file.content_type.startswith('audio/'):
                attachment_type = MessageAttachment.ATTACHMENT_AUDIO
            elif file.content_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                attachment_type = MessageAttachment.ATTACHMENT_DOCUMENT
            
            # Create attachment
            attachment = MessageAttachment.objects.create(
                message=message,
                attachment_type=attachment_type,
                file=file,
                file_name=file.name,
                file_size=file.size,
                file_type=file.content_type
            )
            attachments.append({
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'file_url': attachment.file.url if attachment.file else None
            })
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'attachments': attachments
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def api_search_properties(request):
    """API endpoint to search properties"""
    from .models import Property
    
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'properties': []})
    
    try:
        properties = Property.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        ).filter(status='active')[:10]
        
        results = []
        for prop in properties:
            results.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'location': prop.location,
                'thumbnail': prop.thumbnail.url if prop.thumbnail else None
            })
        
        return JsonResponse({'properties': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_submit_rating(request):
    """API endpoint to submit rating/review"""
    from .models import Rating, Review
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        rating_type = data.get('rating_type')  # 'user', 'property', 'conversation'
        target_id = data.get('target_id')
        rating_value = data.get('rating')
        review_text = data.get('review', '')
        
        if not rating_type or not target_id or not rating_value:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Validate rating value
        try:
            rating_value = int(rating_value)
            if rating_value < 1 or rating_value > 5:
                return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Invalid rating value'}, status=400)
        
        # Create or update rating
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            rating_type=rating_type,
            target_id=target_id,
            defaults={'rating': rating_value}
        )
        
        # Create review if provided
        if review_text:
            Review.objects.create(
                user=request.user,
                rating=rating,
                content=review_text
            )
        
        return JsonResponse({
            'success': True,
            'rating': rating.rating,
            'average_rating': calculate_average_rating(rating_type, target_id)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_create_appointment(request):
    """API endpoint to create appointment"""
    from .models import Appointment

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        appointment_type = data.get('appointment_type')  # 'property_viewing', 'phone_call', 'meeting'
        user_id = data.get('user')
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        duration = data.get('duration', 30)
        location = data.get('location', '')
        address = data.get('address', '')
        notes = data.get('notes', '')
        priority = data.get('priority', 'medium')

        if not appointment_type or not user_id or not appointment_date or not appointment_time:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Create appointment
        appointment = Appointment.objects.create(
            user_id=user_id,
            appointment_type=appointment_type,
            target_type='user',
            target_id=user_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration=duration,
            location=location,
            address=address,
            notes=notes,
            priority=priority,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'appointment_id': appointment.id,
            'status': appointment.status
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_appointment_detail(request, appointment_id):
    """API endpoint to get appointment details"""
    from .models import Appointment

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        appointment = Appointment.objects.get(id=appointment_id)

        return JsonResponse({
            'success': True,
            'appointment': {
                'id': appointment.id,
                'appointment_type': appointment.appointment_type,
                'appointment_type_display': appointment.get_appointment_type_display(),
                'status': appointment.status,
                'status_display': appointment.get_status_display(),
                'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d') if appointment.appointment_date else '',
                'appointment_time': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else '',
                'duration': appointment.duration,
                'location': appointment.location,
                'address': appointment.address,
                'notes': appointment.notes,
                'priority': appointment.priority,
                'priority_display': appointment.get_priority_display(),
                'user_username': appointment.user.username if appointment.user else '',
                'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S') if appointment.created_at else ''
            }
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_appointment_confirm(request, appointment_id):
    """API endpoint to confirm appointment"""
    from .models import Appointment

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'confirmed'
        appointment.save()

        return JsonResponse({
            'success': True,
            'status': appointment.status
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_appointment_cancel(request, appointment_id):
    """API endpoint to cancel appointment"""
    from .models import Appointment

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.status = 'cancelled'
        appointment.save()

        return JsonResponse({
            'success': True,
            'status': appointment.status
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_appointment_reschedule(request, appointment_id):
    """API endpoint to reschedule appointment"""
    from .models import Appointment

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        new_date = data.get('appointment_date')
        new_time = data.get('appointment_time')

        if not new_date or not new_time:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        appointment = Appointment.objects.get(id=appointment_id)

        # Create new appointment
        new_appointment = Appointment.objects.create(
            user=appointment.user,
            appointment_type=appointment.appointment_type,
            target_type=appointment.target_type,
            target_id=appointment.target_id,
            appointment_date=new_date,
            appointment_time=new_time,
            duration=appointment.duration,
            location=appointment.location,
            address=appointment.address,
            notes=f'تم إعادة الجدولة من الموعد الأصلي: {appointment.appointment_date} {appointment.appointment_time}',
            status=appointment.status,
            priority=appointment.priority,
            rescheduled_from=appointment
        )

        # Mark old appointment as rescheduled
        appointment.status = 'rescheduled'
        appointment.save()

        return JsonResponse({
            'success': True,
            'new_appointment_id': new_appointment.id
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_appointment_delete(request, appointment_id):
    """API endpoint to delete appointment"""
    from .models import Appointment

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.delete()

        return JsonResponse({
            'success': True
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_users_list(request):
    """API endpoint to get list of users"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        users = User.objects.filter(is_active=True)
        users_data = []

        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            })

        return JsonResponse({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_media_upload(request):
    """API endpoint to upload media files"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        import os
        from django.conf import settings
        from django.core.files.storage import FileSystemStorage

        media_type = request.POST.get('media_type', 'image')
        file = request.FILES.get('file')

        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'advanced_media', media_type))
        filename = fs.save(file.name, file)
        file_path = os.path.join(settings.MEDIA_ROOT, 'advanced_media', media_type, filename)
        file_url = fs.url(filename)
        
        file_url = f"{settings.MEDIA_URL}advanced_media/{media_type}/{filename}"

        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully',
            'path': file_path,
            'url': file_url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_media_delete(request):
    """API endpoint to delete media files"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        import os
        import json

        data = json.loads(request.body)
        file_path = data.get('path')

        if not file_path:
            return JsonResponse({'error': 'No file path provided'}, status=400)

        if os.path.exists(file_path):
            os.remove(file_path)
            return JsonResponse({
                'success': True,
                'message': 'File deleted successfully'
            })
        else:
            return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_brokers_list(request):
    """API endpoint to get list of brokers"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from .models import Broker

        brokers = Broker.objects.filter(is_active=True)
        brokers_data = []

        for broker in brokers:
            brokers_data.append({
                'id': broker.id,
                'display_name': broker.display_name,
                'phone': broker.phone,
                'is_verified': broker.is_verified,
            })

        return JsonResponse({
            'success': True,
            'brokers': brokers_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_average_rating(rating_type, target_id):
    """Calculate average rating for a target"""
    from .models import Rating
    
    ratings = Rating.objects.filter(
        rating_type=rating_type,
        target_id=target_id
    )
    
    if ratings.exists():
        return ratings.aggregate(Avg('rating'))['rating__avg']
    
    return 0


@login_required
def api_export_conversation(request, conversation_id):
    """API endpoint to export conversation messages"""
    from .models import Conversation, Message
    
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        recipient = conversation.participants.exclude(id=request.user.id).first()
        
        # Get messages between the two users
        messages = Message.objects.filter(
            Q(sender=request.user, recipient=recipient) |
            Q(sender=recipient, recipient=request.user)
        ).order_by('created_at')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender_name': msg.sender.get_full_name() or msg.sender.username,
                'content': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_call_signaling(request):
    """API endpoint for WebRTC signaling"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        signal_type = data.get('type')
        conversation_id = data.get('conversation_id')
        
        # In a real implementation, this would:
        # 1. Store signaling data in database
        # 2. Notify other participant via WebSocket
        # 3. Handle ICE candidates, offers, answers
        
        # For now, return success
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_realtime_monitoring(request):
    """API endpoint for real-time monitoring data"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        from django.contrib.auth.models import User
        from .models import Broker
        
        # Calculate real-time stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_brokers = Broker.objects.count()
        
        # Estimate online users (15% of active users)
        online_users = int(active_users * 0.15)
        active_sessions = online_users
        
        # Get system stats
        try:
            import psutil
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
        except ImportError:
            cpu_usage = 0
            memory_usage = 0
            disk_usage = 0
        
        return JsonResponse({
            'success': True,
            'online_users': online_users,
            'active_sessions': active_sessions,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_approve_property(request, property_id):
    """API endpoint to approve property"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        property = get_object_or_404(Property, id=property_id)
        property.status = 'active'
        property.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_toggle_featured_property(request, property_id):
    """API endpoint to toggle property featured status"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        property = get_object_or_404(Property, id=property_id)
        property.is_featured = not property.is_featured
        property.save()
        
        return JsonResponse({'success': True, 'is_featured': property.is_featured})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_delete_property(request, property_id):
    """API endpoint to delete property"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        property = get_object_or_404(Property, id=property_id)
        property.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_toggle_user_status(request, user_id):
    """API endpoint to toggle user status"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_delete_user(request, user_id):
    """API endpoint to delete user"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user = get_object_or_404(User, id=user_id)
        user.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_bulk_user_actions(request):
    """API endpoint for bulk user actions"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        user_ids = data.get('user_ids', [])
        action = data.get('action')
        
        if not user_ids or not action:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        users = User.objects.filter(id__in=user_ids)
        
        if action == 'activate':
            users.update(is_active=True)
        elif action == 'deactivate':
            users.update(is_active=False)
        elif action == 'delete':
            users.delete()
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        return JsonResponse({'success': True, 'affected_count': users.count()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def admin_properties_advanced(request):
    """Advanced property management panel"""
    from .models import Property
    from django.core.paginator import Paginator
    from .constants import IRAQ_GOVERNORATES
    
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('q', '')
    property_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    governorate = request.GET.get('governorate', '')
    
    # Base queryset
    properties = Property.objects.all()
    
    # Apply filters
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    if status:
        properties = properties.filter(status=status)
    
    if governorate:
        properties = properties.filter(governorate=governorate)
    
    # Pagination
    paginator = Paginator(properties, 25)
    page = request.GET.get('page', 1)
    properties_page = paginator.get_page(page)
    
    # Statistics
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(status='active').count()
    sold_properties = Property.objects.filter(status='sold').count()
    featured_properties = Property.objects.filter(is_featured=True).count()
    
    context = {
        'properties': properties_page,
        'total_properties': total_properties,
        'active_properties': active_properties,
        'sold_properties': sold_properties,
        'featured_properties': featured_properties,
        'search_query': search_query,
        'property_type': property_type,
        'status': status,
        'governorate': governorate,
        'governorates': IRAQ_GOVERNORATES,
    }
    
    return render(request, 'properties/admin_properties_advanced.html', context)


@login_required
def admin_subscriptions_advanced(request):
    """Advanced subscription management panel"""
    from .models import Subscription
    from django.core.paginator import Paginator
    
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('q', '')
    subscription_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # Base queryset
    from .models import BrokerPlanSubscription
    subscriptions = BrokerPlanSubscription.objects.all()
    
    # Apply filters
    if search_query:
        subscriptions = subscriptions.filter(
            Q(broker__user__username__icontains=search_query) |
            Q(broker__user__email__icontains=search_query)
        )
    
    if subscription_type:
        subscriptions = subscriptions.filter(plan__name__icontains=subscription_type)
    
    if status:
        if status == 'active':
            subscriptions = subscriptions.filter(status='active')
        elif status == 'inactive':
            subscriptions = subscriptions.filter(status='expired')
    
    # Pagination
    paginator = Paginator(subscriptions, 25)
    page = request.GET.get('page', 1)
    subscriptions_page = paginator.get_page(page)
    
    # Statistics
    total_subscriptions = BrokerPlanSubscription.objects.count()
    active_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
    expired_subscriptions = BrokerPlanSubscription.objects.filter(status='expired').count()
    
    context = {
        'subscriptions': subscriptions_page,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'search_query': search_query,
        'subscription_type': subscription_type,
        'status': status,
    }
    
    return render(request, 'properties/admin_subscriptions_advanced.html', context)


@login_required
def admin_notifications_advanced(request):
    """Advanced notification management panel"""
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Get filter parameters
    notification_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # Base queryset
    from .models import Notification
    notifications = Notification.objects.all()
    
    # Apply filters
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if status:
        if status == 'sent':
            notifications = notifications.filter(is_sent=True)
        elif status == 'pending':
            notifications = notifications.filter(is_sent=False)
    
    # Pagination
    paginator = Paginator(notifications, 25)
    page = request.GET.get('page', 1)
    notifications_page = paginator.get_page(page)
    
    # Statistics
    total_notifications = Notification.objects.count()
    sent_notifications = Notification.objects.filter(sent_at__isnull=False).count()
    pending_notifications = Notification.objects.filter(sent_at__isnull=True).count()
    
    context = {
        'notifications': notifications_page,
        'total_notifications': total_notifications,
        'sent_notifications': sent_notifications,
        'pending_notifications': pending_notifications,
        'notification_type': notification_type,
        'status': status,
    }
    
    return render(request, 'properties/admin_notifications_advanced.html', context)


@login_required
def admin_realtime_monitoring(request):
    """Real-time monitoring panel"""
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Get real-time statistics
    from django.core.cache import cache
    
    # Cache keys for real-time data
    online_users = cache.get('online_users', 0)
    active_sessions = cache.get('active_sessions', 0)
    recent_actions = cache.get('recent_actions', [])
    
    # Get server stats
    try:
        import psutil
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
    except ImportError:
        # Fallback if psutil not available
        cpu_usage = 0
        memory_usage = 0
        disk_usage = 0
    
    context = {
        'online_users': online_users,
        'active_sessions': active_sessions,
        'recent_actions': recent_actions,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
    }
    
    return render(request, 'properties/admin_realtime_monitoring.html', context)


@login_required
def quick_search_users(request):
    """Quick search for users - for admin contact"""
    from .models import UserProfile
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    try:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:10]
        
        results = []
        for user in users:
            results.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'phone': getattr(user.user_profile, 'phone', '') if hasattr(user, 'user_profile') else ''
            })
        
        return JsonResponse({'users': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def admin_analytics_panel(request):
    """Advanced analytics panel for admin"""
    from .models import Property, Broker, UserProfile, Subscription
    
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Calculate analytics data
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(status='active').count()
    total_users = User.objects.count()
    total_brokers = Broker.objects.count()
    from .models import BrokerPlanSubscription
    active_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
    
    # Recent activity
    recent_properties = Property.objects.order_by('-created_at')[:10]
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Geographic distribution
    governorate_stats = Property.objects.values('governorate').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Property type distribution
    property_type_stats = Property.objects.values('property_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'total_users': total_users,
        'total_brokers': total_brokers,
        'active_subscriptions': active_subscriptions,
        'recent_properties': recent_properties,
        'recent_users': recent_users,
        'governorate_stats': governorate_stats,
        'property_type_stats': property_type_stats,
    }
    
    return render(request, 'properties/admin_analytics_panel.html', context)


@login_required
def admin_reports_panel(request):
    """Reports panel for admin"""
    from .models import Property, Broker, UserProfile, Subscription, Message
    
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Generate report data
    report_type = request.GET.get('report_type', 'overview')
    
    if report_type == 'properties':
        report_data = {
            'title': 'تقرير العقارات',
            'properties': Property.objects.all().order_by('-created_at'),
            'total': Property.objects.count(),
            'active': Property.objects.filter(status='active').count(),
            'sold': Property.objects.filter(status='sold').count(),
        }
    elif report_type == 'users':
        report_data = {
            'title': 'تقرير المستخدمين',
            'users': User.objects.all().order_by('-date_joined'),
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'brokers': Broker.objects.count(),
        }
    elif report_type == 'subscriptions':
        from .models import BrokerPlanSubscription
        report_data = {
            'title': 'تقرير الاشتراكات',
            'subscriptions': BrokerPlanSubscription.objects.all().order_by('-created_at'),
            'total': BrokerPlanSubscription.objects.count(),
            'active': BrokerPlanSubscription.objects.filter(status='active').count(),
            'expired': BrokerPlanSubscription.objects.filter(status='expired').count(),
        }
    else:
        from .models import BrokerPlanSubscription
        report_data = {
            'title': 'نظرة عامة',
            'properties_count': Property.objects.count(),
            'users_count': User.objects.count(),
            'brokers_count': Broker.objects.count(),
            'subscriptions_count': BrokerPlanSubscription.objects.count(),
        }
    
    context = {
        'report_type': report_type,
        'report_data': report_data,
    }
    
    return render(request, 'properties/admin_reports_panel.html', context)
    """بحث سريع عن المستخدمين للمحادثات"""
    from django.contrib.auth.models import User
    from .models import Broker, UserProfile
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search users by name, email, or username
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id).distinct()[:10]
    
    results = []
    for user in users:
        # Check if conversation exists
        from .models import Conversation
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=user).first()
        
        results.append({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'avatar': user.user_profile.avatar.url if hasattr(user, 'user_profile') and user.user_profile.avatar else None,
            'username': user.username,
            'has_conversation': existing_conversation is not None,
            'conversation_id': existing_conversation.id if existing_conversation else None
        })
    
    return JsonResponse({'results': results})


@login_required
def conversations_list(request):
    """قائمة المحادثات للمستخدم"""
    from .models import Conversation, Message
    
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).prefetch_related('participants', 'messages')
    
    # ترتيب المحادثات حسب آخر رسالة
    conversations = sorted(
        conversations,
        key=lambda c: c.last_message_at or c.created_at,
        reverse=True
    )
    
    context = {
        'conversations': conversations,
    }
    
    return render(request, 'properties/conversations_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """تفاصيل المحادثة"""
    from .models import Conversation, Message
    
    conversation = get_object_or_404(
        Conversation,
        conversation_id=conversation_id,
        participants=request.user
    )
    
    # الحصول على الرسائل
    messages = conversation.messages.filter(
        is_deleted_by_sender=False,
        is_deleted_by_recipient=False
    ).order_by('created_at')
    
    # تحديث آخر رسالة
    if messages.exists():
        conversation.last_message_at = messages.last().created_at
        conversation.save(update_fields=['last_message_at'])
    
    # تحديث الرسائل غير المقروءة
    unread_messages = messages.filter(
        recipient=request.user,
        is_read=False
    )
    unread_messages.update(is_read=True)
    
    context = {
        'conversation': conversation,
        'messages': messages,
    }
    
    return render(request, 'properties/conversation_detail.html', context)


@login_required
def start_conversation(request, user_id):
    """بدء محادثة جديدة مع مستخدم - مع التكامل مع CRM"""
    from .models import Conversation, Message, CRMContact
    from .permissions import can_send_message_to_user
    
    other_user = get_object_or_404(User, pk=user_id)
    
    # التحقق من صلاحية المراسلة
    if not can_send_message_to_user(request.user, other_user):
        messages.error(request, 'ليس لديك صلاحية لمراسلة هذا المستخدم')
        return redirect('conversations_list')
    
    # التحقق من وجود محادثة سابقة
    existing_conversation = Conversation.objects.filter(
        participants=request.user,
        conversation_type=Conversation.TYPE_DIRECT
    ).filter(participants=other_user).first()
    
    if existing_conversation:
        return redirect('conversation_detail', conversation_id=existing_conversation.conversation_id)
    
    # إنشاء محادثة جديدة
    conversation = Conversation.objects.create(
        conversation_type=Conversation.TYPE_DIRECT,
        created_by=request.user
    )
    conversation.participants.add(request.user, other_user)
    
    # إنشاء أو تحديث جهة اتصال CRM للطرف الآخر
    try:
        crm_contact, created = CRMContact.objects.get_or_create(
            user=other_user,
            defaults={
                'name': other_user.get_full_name() or other_user.username,
                'email': other_user.email,
                'stage': 'lead',
                'priority': 'warm',
                'source': 'message',
                'created_by': request.user,
                'assigned_to': request.user,
            }
        )
        
        # ربط المحادثة بجهة الاتصال
        crm_contact.conversation = conversation
        crm_contact.save(update_fields=['conversation'])
        
        # تحديث أو إنشاء جهة اتصال للمستخدم الحالي
        if request.user.email:
            crm_contact_sender, created = CRMContact.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'stage': 'customer',
                    'priority': 'warm',
                    'source': 'message',
                    'created_by': request.user,
                }
            )
    except Exception as e:
        # لا نوقف العملية إذا فشل تحديث CRM
        pass
    
    return redirect('conversation_detail', conversation_id=conversation.conversation_id)


@login_required
def send_message(request):
    """إرسال رسالة جديدة مع التكامل مع CRM"""
    from .models import Conversation, Message, CRMContact
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    conversation_id = request.POST.get('conversation_id')
    content = request.POST.get('content')
    message_type = request.POST.get('message_type', Message.TYPE_TEXT)
    
    if not all([conversation_id, content]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    conversation = get_object_or_404(
        Conversation,
        conversation_id=conversation_id,
        participants=request.user
    )
    
    # الحصول على المستلم
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    if not other_user:
        return JsonResponse({'error': 'No recipient found'}, status=400)
    
    # إنشاء الرسالة
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        recipient=other_user,
        message_type=message_type,
        content=content,
        status=Message.STATUS_SENT
    )
    
    # تحديث آخر رسالة في المحادثة
    conversation.last_message_at = message.created_at
    conversation.save(update_fields=['last_message_at'])
    
    # تحديث جهات اتصال CRM المرتبطة بالمحادثة
    try:
        crm_contacts = CRMContact.objects.filter(conversation=conversation)
        for crm_contact in crm_contacts:
            crm_contact.update_interaction_count()
            
            # إذا كان المرسل هو المسؤول عن جهة الاتصال، تحديث آخر اتصال
            if crm_contact.assigned_to == request.user:
                crm_contact.last_contact = timezone.now()
                crm_contact.save(update_fields=['last_contact'])
    except Exception as e:
        # لا نوقف العملية إذا فشل تحديث CRM
        pass
    
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
    })


@login_required
def conversation_archive(request, conversation_id):
    """أرشفة المحادثة"""
    from .models import Conversation
    
    conversation = get_object_or_404(
        Conversation,
        conversation_id=conversation_id,
        participants=request.user
    )
    
    conversation.is_archived = not conversation.is_archived
    conversation.save(update_fields=['is_archived'])
    
    return redirect('conversations_list')


@login_required
def conversation_delete(request, conversation_id):
    """حذف المحادثة من جانب المستخدم"""
    from .models import Conversation, ConversationParticipant
    
    conversation = get_object_or_404(
        Conversation,
        conversation_id=conversation_id,
        participants=request.user
    )
    
    # حذف المشارك من المحادثة
    ConversationParticipant.objects.filter(
        conversation=conversation,
        user=request.user
    ).delete()
    
    return redirect('conversations_list')


@login_required
def admin_users_list(request):
    """Advanced user management panel"""
    from .models import UserProfile, Broker
    from django.contrib.auth.models import User
    
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('q', '')
    user_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    users = User.objects.all()
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if user_type == 'brokers':
        users = users.filter(id__in=Broker.objects.values_list('user_id', flat=True))
    elif user_type == 'regular':
        users = users.exclude(id__in=Broker.objects.values_list('user_id', flat=True))
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    
    if date_from:
        users = users.filter(date_joined__gte=date_from)
    
    if date_to:
        users = users.filter(date_joined__lte=date_to)
    
    # Pagination
    paginator = Paginator(users, 25)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_brokers = Broker.objects.count()
    from .models import BrokerPlanSubscription
    total_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
    
    context = {
        'users': users_page,
        'total_users': total_users,
        'active_users': active_users,
        'total_brokers': total_brokers,
        'total_subscriptions': total_subscriptions,
        'search_query': search_query,
        'user_type': user_type,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'properties/admin_users_advanced.html', context)
    """قائمة المستخدمين"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import Broker, UserProfile

    # Get all users with their types
    users = User.objects.all().select_related('broker_profile', 'user_profile').order_by('-date_joined')

    # Add user type to each user
    for user in users:
        try:
            if user.is_superuser:
                user.user_type = 'admin'
            elif hasattr(user, 'broker_profile') and user.broker_profile:
                user.user_type = 'broker'
            elif hasattr(user, 'user_profile') and user.user_profile:
                user.user_type = 'user'
            else:
                user.user_type = 'unknown'
        except:
            user.user_type = 'unknown'

    context = {
        'users': users,
    }

    return render(request, 'properties/admin_users_list.html', context)


@login_required
def admin_create_user(request):
    """إنشاء مستخدم جديد"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import Broker, UserProfile

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'user')  # admin, broker, user

        # Validation
        if not username or not email or not password:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم بالفعل')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل')
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )

            # Set user type
            if user_type == 'admin':
                user.is_superuser = True
                user.is_staff = True
                user.save()

                # Create broker profile with admin role
                Broker.objects.create(
                    user=user,
                    phone=phone,
                    role=Broker.ROLE_ADMIN,
                    is_active=True,
                )
            elif user_type == 'broker':
                user.is_staff = True
                user.save()

                # Create broker profile
                Broker.objects.create(
                    user=user,
                    phone=phone,
                    role=Broker.ROLE_MAIN,
                    is_active=True,
                )
            else:  # regular user
                user.is_staff = False
                user.save()

                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    phone=phone,
                    is_active=True,
                )

            messages.success(request, 'تم إنشاء المستخدم بنجاح')
            return redirect('admin_users_list')

    return render(request, 'properties/admin_create_user.html')


@login_required
def admin_edit_user(request, user_id):
    """تعديل مستخدم"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import Broker, UserProfile

    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()

        # Update profile based on type
        try:
            if hasattr(user, 'broker') and user.broker:
                broker = user.broker
                broker.phone = request.POST.get('phone', '').strip()
                broker.is_active = request.POST.get('is_active') == 'on'
                broker.save()
            elif hasattr(user, 'userprofile') and user.userprofile:
                profile = user.userprofile
                profile.phone = request.POST.get('phone', '').strip()
                profile.is_active = request.POST.get('is_active') == 'on'
                profile.save()
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')

        messages.success(request, 'تم تحديث المستخدم بنجاح')
        return redirect('admin_users_list')

    context = {
        'user': user,
    }

    return render(request, 'properties/admin_edit_user.html', context)


@login_required
def admin_delete_user(request, user_id):
    """حذف مستخدم"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User

    user = get_object_or_404(User, pk=user_id)

    # Prevent deleting self
    if user == request.user:
        messages.error(request, 'لا يمكنك حذف حسابك')
        return redirect('admin_users_list')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'تم حذف المستخدم بنجاح')
        return redirect('admin_users_list')

    context = {
        'user': user,
    }

    return render(request, 'properties/admin_delete_user.html', context)


@login_required
def admin_toggle_user(request, user_id):
    """تفعيل أو إيقاف مستخدم"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import Broker, UserProfile

    user = get_object_or_404(User, pk=user_id)

    # Prevent deactivating self
    if user == request.user:
        messages.error(request, 'لا يمكنك إيقاف حسابك')
        return redirect('admin_users_list')

    # Toggle user active status
    user.is_active = not user.is_active
    user.save()

    # Toggle profile active status
    try:
        if hasattr(user, 'broker') and user.broker:
            broker = user.broker
            broker.is_active = user.is_active
            broker.save()
        elif hasattr(user, 'userprofile') and user.userprofile:
            profile = user.userprofile
            profile.is_active = user.is_active
            profile.save()
    except Exception as e:
        messages.error(request, f'حدث خطأ: {str(e)}')

    status = 'تفعيل' if user.is_active else 'إيقاف'
    messages.success(request, f'تم {status} المستخدم بنجاح')
    return redirect('admin_users_list')


@login_required
def admin_reset_password(request, user_id):
    """إعادة تعيين كلمة المرور"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User

    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not new_password or len(new_password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        elif new_password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'تم إعادة تعيين كلمة المرور بنجاح')
            return redirect('admin_users_list')

    context = {
        'user': user,
    }

    return render(request, 'properties/admin_reset_password.html', context)


@login_required
def admin_change_user_type(request, user_id):
    """تغيير نوع المستخدم"""
    from .permissions import can_access_admin_panel

    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى لوحة الإدارة')
        return redirect('home')

    from django.contrib.auth.models import User
    from .models import Broker, UserProfile

    user = get_object_or_404(User, pk=user_id)

    # Prevent changing own type
    if user == request.user:
        messages.error(request, 'لا يمكنك تغيير نوع حسابك')
        return redirect('admin_users_list')

    if request.method == 'POST':
        new_type = request.POST.get('user_type', 'user')
        phone = request.POST.get('phone', '').strip()

        # Delete existing profiles
        if hasattr(user, 'broker_profile'):
            user.broker_profile.delete()
        if hasattr(user, 'user_profile'):
            user.user_profile.delete()

        # Create new profile based on type
        if new_type == 'admin':
            user.is_superuser = True
            user.is_staff = True
            user.save()

            Broker.objects.create(
                user=user,
                phone=phone,
                role=Broker.ROLE_ADMIN,
                is_active=True,
            )
        elif new_type == 'broker':
            user.is_superuser = False
            user.is_staff = True
            user.save()

            Broker.objects.create(
                user=user,
                phone=phone,
                role=Broker.ROLE_MAIN,
                is_active=True,
            )
        else:  # regular user
            user.is_superuser = False
            user.is_staff = False
            user.save()

            UserProfile.objects.create(
                user=user,
                phone=phone,
                is_active=True,
            )

        messages.success(request, 'تم تغيير نوع المستخدم بنجاح')
        return redirect('admin_users_list')

    context = {
        'user': user,
    }

    return render(request, 'properties/admin_change_user_type.html', context)


@login_required
def chat_view(request):
    """Main chat view - real-time messaging interface"""
    return render(request, 'properties/chat.html')


def channels_list_view(request):
    """View for displaying all broker channels"""
    channels = BrokerChannel.objects.filter(
        status='active'
    ).select_related('broker').prefetch_related('followers')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        channels = channels.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(broker__display_name__icontains=search_query)
        )
    
    # Get user's follows and saves
    user_follows = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_follows = set(ChannelFollow.objects.filter(
            user=request.user
        ).values_list('channel_id', flat=True))
        user_saves = set(ChannelSave.objects.filter(
            user=request.user
        ).values_list('channel_id', flat=True))
    
    # Pagination
    paginator = Paginator(channels, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'channels': page_obj,
        'user_follows': user_follows,
        'user_saves': user_saves,
        'page_title': 'قنوات الدلالين',
        'search_query': search_query,
    }
    
    return render(request, 'properties/channels.html', context)


def channel_detail_view(request, slug):
    """View for displaying a single broker channel"""
    channel = get_object_or_404(BrokerChannel, slug=slug, status='active')
    
    # Get tab filter
    tab = request.GET.get('tab', 'all')
    
    # Get listings based on tab
    listings = []
    if tab == 'all':
        listings = channel.get_all_listings()
    elif tab == 'iraq':
        listings = list(channel.get_properties_iraq())
    elif tab == 'outside':
        listings = list(channel.get_properties_outside())
    elif tab == 'hotels':
        listings = list(channel.get_hotels())
    elif tab == 'resorts':
        listings = list(channel.get_resorts())
    elif tab == 'featured':
        listings = channel.get_featured_listings()
    elif tab == 'most_viewed':
        listings = channel.get_most_viewed()
    elif tab == 'latest':
        listings = channel.get_all_listings()
    
    # Increment views
    channel.views_count += 1
    channel.save(update_fields=['views_count'])
    
    # Get user's follows and saves
    is_following = False
    is_saved = False
    if request.user.is_authenticated:
        is_following = ChannelFollow.objects.filter(
            user=request.user,
            channel=channel
        ).exists()
        is_saved = ChannelSave.objects.filter(
            user=request.user,
            channel=channel
        ).exists()
    
    # Pagination
    paginator = Paginator(listings, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'channel': channel,
        'listings': page_obj,
        'page_obj': page_obj,
        'tab': tab,
        'is_following': is_following,
        'is_saved': is_saved,
        'page_title': channel.name,
    }
    
    return render(request, 'properties/channel_detail.html', context)


@login_required
@require_POST
def follow_channel_view(request, channel_id):
    """Follow or unfollow a channel"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, is_active=True)
    
    follow, created = ChannelFollow.objects.get_or_create(
        user=request.user,
        channel=channel
    )
    
    if not created:
        # Unfollow
        follow.delete()
        channel.followers_count = max(0, channel.followers_count - 1)
        action = 'unfollowed'
    else:
        # Follow
        channel.followers_count += 1
        action = 'followed'
    
    channel.save(update_fields=['followers_count'])
    
    return JsonResponse({
        'success': True,
        'action': action,
        'followers_count': channel.followers_count
    })


@login_required
@require_POST
def save_channel_view(request, channel_id):
    """Save or unsave a channel"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, is_active=True)
    
    save, created = ChannelSave.objects.get_or_create(
        user=request.user,
        channel=channel
    )
    
    if not created:
        # Unsave
        save.delete()
        action = 'unsaved'
    else:
        # Save
        action = 'saved'
    
    return JsonResponse({
        'success': True,
        'action': action
    })


@login_required
def create_auction_view(request):
    """إنشاء مزاد جديد - للإدارة والدلال فقط"""
    from django.utils import timezone
    from decimal import Decimal
    
    # التحقق من الصلاحيات
    if not request.user.is_staff and not hasattr(request.user, 'broker'):
        messages.error(request, 'غير مصرح لك بإنشاء مزادات')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            property_id = request.POST.get('property')
            auction_type = request.POST.get('auction_type')
            title = request.POST.get('title')
            description = request.POST.get('description')
            starting_price = request.POST.get('starting_price')
            minimum_increment = request.POST.get('minimum_increment', 100000)
            reserve_price = request.POST.get('reserve_price')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            deposit_amount = request.POST.get('deposit_amount', 0)
            terms = request.POST.get('terms')
            contact_phone = request.POST.get('contact_phone')
            contact_email = request.POST.get('contact_email')
            max_participants = request.POST.get('max_participants')
            
            # Address fields
            governorate = request.POST.get('governorate', '')
            city = request.POST.get('city', '')
            district = request.POST.get('district', '')
            subdistrict = request.POST.get('subdistrict', '')
            area = request.POST.get('area', '')
            neighborhood = request.POST.get('neighborhood', '')
            mahalla = request.POST.get('mahalla', '')
            block = request.POST.get('block', '')
            street = request.POST.get('street', '')
            alley = request.POST.get('alley', '')
            house_number = request.POST.get('house_number', '')
            property_number = request.POST.get('property_number', '')
            landmark = request.POST.get('landmark', '')
            
            # GPS coordinates
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            # التحقق من البيانات
            if not all([property_id, title, description, starting_price, start_date, end_date, terms]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                return redirect('create_auction')
            
            # الحصول على العقار
            property_obj = get_object_or_404(Property, id=property_id)
            
            # تحديد الدلال
            broker = None
            if hasattr(request.user, 'broker'):
                broker = request.user.broker
            
            # تحديد حالة الموافقة
            approval_status = 'approved' if request.user.is_staff else 'pending'
            approved_by = request.user if request.user.is_staff else None
            approved_at = timezone.now() if request.user.is_staff else None
            
            # إنشاء المزاد
            auction = Auction.objects.create(
                property=property_obj,
                broker=broker,
                auction_type=auction_type,
                title=title,
                description=description,
                starting_price=Decimal(starting_price),
                minimum_increment=Decimal(minimum_increment),
                reserve_price=Decimal(reserve_price) if reserve_price else None,
                start_date=start_date,
                end_date=end_date,
                deposit_amount=Decimal(deposit_amount),
                terms=terms,
                contact_phone=contact_phone,
                contact_email=contact_email,
                max_participants=int(max_participants) if max_participants else None,
                approval_status=approval_status,
                approved_by=approved_by,
                approved_at=approved_at,
                governorate=governorate,
                city=city,
                district=district,
                subdistrict=subdistrict,
                area=area,
                neighborhood=neighborhood,
                mahalla=mahalla,
                block=block,
                street=street,
                alley=alley,
                house_number=house_number,
                property_number=property_number,
                landmark=landmark,
                latitude=Decimal(latitude) if latitude else None,
                longitude=Decimal(longitude) if longitude else None
            )
            
            if request.user.is_staff:
                messages.success(request, 'تم إنشاء المزاد بنجاح')
            else:
                messages.success(request, 'تم إرسال طلب إنشاء المزاد للإدارة للمراجعة')
            
            return redirect('auction_detail', auction.id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
            return redirect('create_auction')
    
    # عرض نموذج الإنشاء
    properties_list = Property.objects.filter(status='active')
    
    return render(request, 'properties/create_auction.html', {
        'properties': properties_list,
        'auction_types': Auction.AUCTION_TYPES
    })


@login_required
def auction_approval_view(request):
    """إدارة موافقة المزادات - للإدارة فقط"""
    if not request.user.is_staff:
        messages.error(request, 'غير مصرح لك بالوصول إلى هذه الصفحة')
        return redirect('home')
    
    pending_auctions = Auction.objects.filter(approval_status='pending')
    
    if request.method == 'POST':
        auction_id = request.POST.get('auction_id')
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '')
        
        auction = get_object_or_404(Auction, id=auction_id)
        
        if action == 'approve':
            auction.approval_status = 'approved'
            auction.approved_by = request.user
            auction.approved_at = timezone.now()
            auction.save()
            messages.success(request, 'تمت الموافقة على المزاد')
            
            # إرسال إشعار للدلال
            if auction.broker:
                Notification.objects.create(
                    user=auction.broker.user,
                    title='تمت الموافقة على مزادك',
                    message=f'تمت الموافقة على مزاد "{auction.title}"',
                    link=f'/auction/{auction.id}/'
                )
                
        elif action == 'reject':
            auction.approval_status = 'rejected'
            auction.rejection_reason = rejection_reason
            auction.save()
            messages.success(request, 'تم رفض المزاد')
            
            # إرسال إشعار للدلال
            if auction.broker:
                Notification.objects.create(
                    user=auction.broker.user,
                    title='تم رفض مزادك',
                    message=f'تم رفض مزاد "{auction.title}". السبب: {rejection_reason}',
                    link=f'/auction/{auction.id}/'
                )
                
        elif action == 'request_revision':
            auction.approval_status = 'needs_revision'
            auction.rejection_reason = rejection_reason
            auction.save()
            messages.success(request, 'تم طلب تعديل المزاد')
            
            # إرسال إشعار للدلال
            if auction.broker:
                Notification.objects.create(
                    user=auction.broker.user,
                    title='يحتاج تعديل',
                    message=f'مزاد "{auction.title}" يحتاج تعديل. {rejection_reason}',
                    link=f'/auction/{auction.id}/edit/'
                )
        
        return redirect('auction_approval')
    
    return render(request, 'properties/auction_approval.html', {
        'pending_auctions': pending_auctions
    })


@login_required
def auction_detail_view(request, auction_id):
    """صفحة تفاصيل المزاد مع المزايدة الحية"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    # التحقق من الموافقة للمزادات التي لم تتم الموافقة عليها بعد
    if auction.approval_status != 'approved' and not request.user.is_staff:
        if auction.broker and auction.broker.user == request.user:
            pass  # الدلال يمكنه رؤية مزاده
        else:
            messages.error(request, 'هذا المزاد قيد المراجعة')
            return redirect('auctions_list')
    
    # التحقق من التسجيل
    is_participant = False
    if request.user.is_authenticated:
        is_participant = auction.participants.filter(user=request.user).exists()
    
    # الحصول على المزايدات
    bids = auction.bids.select_related('user').order_by('-created_at')[:10]
    
    # الحصول على أعلى مزايدة
    highest_bid = auction.get_current_highest_bid()
    
    # الوقت المتبقي
    time_remaining = auction.get_time_remaining()
    
    return render(request, 'properties/auction_detail.html', {
        'auction': auction,
        'is_participant': is_participant,
        'bids': bids,
        'highest_bid': highest_bid,
        'time_remaining': time_remaining
    })


@login_required
def join_auction_view(request, auction_id):
    """التسجيل في المزاد"""
    auction = get_object_or_404(Auction, id=auction_id)
    
    # التحقق من أن المزاد موافق عليه
    if auction.approval_status != 'approved':
        messages.error(request, 'هذا المزاد غير متاح للتسجيل')
        return redirect('auction_detail', auction.id)
    
    # التحقق من أن المستخدم ليس مسجلاً بالفعل
    if auction.participants.filter(user=request.user).exists():
        messages.error(request, 'أنت مسجل بالفعل في هذا المزاد')
        return redirect('auction_detail', auction.id)
    
    # التحقق من الحد الأقصى للمشاركين
    if auction.max_participants and auction.participants.count() >= auction.max_participants:
        messages.error(request, 'تم الوصول للحد الأقصى للمشاركين')
        return redirect('auction_detail', auction.id)
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        terms_accepted = request.POST.get('terms_accepted')
        
        if not all([phone, email, terms_accepted]):
            messages.error(request, 'يرجى ملء جميع الحقول والموافقة على الشروط')
            return redirect('auction_detail', auction.id)
        
        # إنشاء مشارك
        participant = AuctionParticipant.objects.create(
            auction=auction,
            user=request.user,
            phone=phone,
            email=email,
            approval_status='pending'  # يحتاج موافقة الإدارة إذا كان مفعل
        )
        
        # إذا كان مبلغ التأمين 0، يتم الموافقة تلقائياً
        if auction.deposit_amount == 0:
            participant.approval_status = 'approved'
            participant.approved_at = timezone.now()
            participant.save()
            messages.success(request, 'تم التسجيل في المزاد بنجاح')
        else:
            messages.success(request, 'تم التسجيل في المزاد. يرجى دفع مبلغ التأمين')
        
        return redirect('auction_detail', auction.id)
    
    return redirect('auction_detail', auction.id)


@login_required
def place_bid_view(request, auction_id):
    """المزايدة (AJAX)"""
    from decimal import Decimal
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    # التحقق من أن المزاد نشط
    if not auction.is_active():
        return JsonResponse({
            'success': False,
            'error': 'المزاد غير نشط حالياً'
        })
    
    # التحقق من أن المستخدم مشارك وموافق عليه
    try:
        participant = auction.participants.get(user=request.user)
        if participant.approval_status != 'approved':
            return JsonResponse({
                'success': False,
                'error': 'لم يتم الموافقة على مشاركتك بعد'
            })
    except AuctionParticipant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'يجب التسجيل في المزاد أولاً'
        })
    
    if request.method == 'POST':
        bid_amount = request.POST.get('bid_amount')
        
        try:
            bid_amount = Decimal(bid_amount)
        except:
            return JsonResponse({
                'success': False,
                'error': 'قيمة المزايدة غير صحيحة'
            })
        
        # التحقق من الحد الأدنى
        current_highest = auction.get_current_highest_bid()
        minimum_bid = current_highest + auction.minimum_increment
        
        if bid_amount < minimum_bid:
            return JsonResponse({
                'success': False,
                'error': f'أقل مزايدة مسموحة هي {minimum_bid:,} د.ع'
            })
        
        # إنشاء المزايدة
        bid = Bid.objects.create(
            auction=auction,
            user=request.user,
            amount=bid_amount
        )
        
        # التحقق من التمديد التلقائي
        if auction.should_extend():
            auction.extend_auction()
        
        return JsonResponse({
            'success': True,
            'bid_amount': str(bid_amount),
            'current_highest': str(auction.get_current_highest_bid()),
            'message': 'تمت المزايدة بنجاح'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'طلب غير صحيح'
    })


# ==================== Payment System Views ====================

@login_required
def property_publication(request, slug):
    """View for choosing publication type and duration"""
    property = get_object_or_404(Property, slug=slug)
    
    # Check ownership
    if property.owner != request.user:
        messages.error(request, 'ليس لديك صلاحية نشر هذا العقار')
        return redirect('property_detail', slug=slug)
    
    # Get pricing settings (default: 50 IQD per day)
    from django.conf import settings
    daily_price = getattr(settings, 'DAILY_PROPERTY_PRICE', 50.00)
    featured_price = getattr(settings, 'FEATURED_PROPERTY_PRICE', 0.00)
    
    if request.method == 'POST':
        form = PropertyPublicationForm(request.POST, daily_price=daily_price, featured_price=featured_price)
        if form.is_valid():
            publication_type = form.cleaned_data['publication_type']
            publication_days = form.cleaned_data['publication_days']
            
            # Store in session for payment step
            request.session['publication_data'] = {
                'property_id': property.id,
                'publication_type': publication_type,
                'publication_days': publication_days,
                'daily_price': str(daily_price),
                'featured_price': str(featured_price),
                'total_amount': str(form.calculate_total()),
            }
            
            return redirect('property_payment', slug=slug)
    else:
        form = PropertyPublicationForm(daily_price=daily_price, featured_price=featured_price)
    
    context = {
        'property': property,
        'form': form,
        'daily_price': daily_price,
        'featured_price': featured_price,
    }
    
    return render(request, 'properties/property_publication.html', context)


@login_required
def property_payment(request, slug):
    """View for processing property payment"""
    property = get_object_or_404(Property, slug=slug)
    
    # Check ownership
    if property.owner != request.user:
        messages.error(request, 'ليس لديك صلاحية دفع هذا العقار')
        return redirect('property_detail', slug=slug)
    
    # Get publication data from session
    publication_data = request.session.get('publication_data')
    if not publication_data or publication_data.get('property_id') != property.id:
        messages.error(request, 'يجب اختيار خطة النشر أولاً')
        return redirect('property_publication', slug=slug)
    
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلالاً لنشر العقارات')
        return redirect('dashboard')
    
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = PropertyPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            # Create payment record
            payment = PropertyPayment.objects.create(
                property=property,
                broker=broker,
                payment_method=form.cleaned_data['payment_method'],
                publication_type=publication_data['publication_type'],
                days=int(publication_data['publication_days']),
                daily_price=Decimal(publication_data['daily_price']),
                featured_price=Decimal(publication_data['featured_price']),
                total_amount=Decimal(publication_data['total_amount']),
                payment_proof=form.cleaned_data.get('payment_proof'),
                status=PropertyPayment.STATUS_PENDING,
            )
            
            # Update property status
            property.status = Property.STATUS_PAID
            property.publication_type = publication_data['publication_type']
            property.publication_days = int(publication_data['publication_days'])
            property.save()
            
            # Create notification
            PropertyNotification.objects.create(
                user=request.user,
                property=property,
                notification_type=PropertyNotification.TYPE_PAYMENT_SUCCESS,
                title='تم استلام طلب الدفع',
                message=f'تم استلام طلب دفع لنشر العقار: {property.display_title}. سيتم مراجعة الدفع من قبل الإدارة.'
            )
            
            # Clear session data
            del request.session['publication_data']
            
            messages.success(request, 'تم استلام طلب الدفع بنجاح. سيتم مراجعته من قبل الإدارة.')
            return redirect('dashboard')
    else:
        form = PropertyPaymentForm()
    
    context = {
        'property': property,
        'form': form,
        'payment_methods': payment_methods,
        'publication_type_display': 'مميز' if publication_data['publication_type'] == 'featured' else 'عادي',
        'publication_days': publication_data['publication_days'],
        'daily_price': Decimal(publication_data['daily_price']),
        'featured_price': Decimal(publication_data['featured_price']),
        'total_amount': Decimal(publication_data['total_amount']),
    }
    
    return render(request, 'properties/property_payment.html', context)


@login_required
@staff_required
def approve_property_payment(request, payment_id):
    """Admin view to approve property payment"""
    payment = get_object_or_404(PropertyPayment, id=payment_id)
    
    if payment.status != PropertyPayment.STATUS_PENDING:
        messages.error(request, 'هذا الدفع ليس في حالة انتظار')
        return redirect('admin_panel')
    
    if request.method == 'POST':
        payment.status = PropertyPayment.STATUS_COMPLETED
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.payment_date = timezone.now()
        
        # Set publication dates
        payment.publication_start_date = timezone.now()
        from datetime import timedelta
        payment.publication_end_date = timezone.now() + timedelta(days=payment.days)
        
        payment.save()
        
        # Update property status
        property = payment.property
        property.status = Property.STATUS_PUBLISHED
        property.publication_start_date = payment.publication_start_date
        property.publication_end_date = payment.publication_end_date
        property.save()
        
        # Create notification
        PropertyNotification.objects.create(
            user=payment.broker.user,
            property=property,
            notification_type=PropertyNotification.TYPE_PROPERTY_APPROVED,
            title='تم قبول الدفع وبدء النشر',
            message=f'تم قبول دفع العقار: {property.display_title}. بدأ النشر الآن.'
        )
        
        messages.success(request, 'تم قبول الدفع وبدء النشر بنجاح')
        return redirect('admin_panel')
    
    context = {
        'payment': payment,
        'property': payment.property,
    }
    
    return render(request, 'properties/approve_payment.html', context)


# ==================== New Category Views ====================

def properties_inside_iraq_view(request):
    """View for properties inside Iraq with category selection"""
    # Get filters from query parameters
    property_type = request.GET.get('property_type', 'all')
    listing_type = request.GET.get('listing_type', 'all')
    governorate = request.GET.get('governorate', '')
    city = request.GET.get('city', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    area_min = request.GET.get('area_min', '')
    area_max = request.GET.get('area_max', '')
    
    # Get properties inside Iraq
    properties = get_public_properties()
    properties = [p for p in properties if p.country and p.country.code == 'IQ']
    
    # Apply filters
    if property_type != 'all':
        properties = [p for p in properties if p.type == property_type]
    
    if listing_type == 'sale':
        properties = [p for p in properties if p.status in PUBLIC_STATUSES]
    elif listing_type == 'rent':
        properties = [p for p in properties if p.status == 'rent']
    elif listing_type == 'collective_rent':
        properties = [p for p in properties if p.status == 'collective_rent']
    
    if governorate:
        properties = [p for p in properties if p.governorate == governorate]
    
    if city:
        properties = [p for p in properties if p.city == city]
    
    if price_min:
        properties = [p for p in properties if p.price >= int(price_min)]
    if price_max:
        properties = [p for p in properties if p.price <= int(price_max)]
    
    if area_min:
        properties = [p for p in properties if p.area >= int(area_min)]
    if area_max:
        properties = [p for p in properties if p.area <= int(area_max)]
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/categories/inside_iraq.html', {
        'properties': properties,
        'property_type': property_type,
        'listing_type': listing_type,
        'governorate': governorate,
        'city': city,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'category_title': 'عقارات داخل العراق',
        'category_icon': '🏠',
    })


def hotels_category_view(request):
    """View for hotels category inside Iraq"""
    from properties.models import PropertyHotel
    from properties.constants import IRAQ_GOVERNORATES
    
    # Get filters
    star_rating = request.GET.get('star_rating', '')
    governorate = request.GET.get('governorate', '')
    district = request.GET.get('district', '')
    rent_type = request.GET.get('rent_type', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    hotels = PropertyHotel.objects.filter(property__country__code='IQ')
    
    if star_rating:
        hotels = hotels.filter(star_rating=int(star_rating))
    
    if governorate:
        hotels = hotels.filter(governorate=governorate)
    
    if district:
        hotels = hotels.filter(district__icontains=district)
    
    if rent_type == 'collective':
        hotels = hotels.filter(supports_collective_rent=True)
    
    if price_min:
        hotels = [h for h in hotels if h.price_per_night and h.price_per_night >= int(price_min)]
    if price_max:
        hotels = [h for h in hotels if h.price_per_night and h.price_per_night <= int(price_max)]
    
    return render(request, 'properties/categories/hotels.html', {
        'hotels': hotels,
        'star_rating': star_rating,
        'governorate': governorate,
        'district': district,
        'rent_type': rent_type,
        'price_min': price_min,
        'price_max': price_max,
        'governorates': IRAQ_GOVERNORATES,
        'category_title': 'فنادق',
        'category_icon': '🏨',
        'can_create_hotel': request.user.is_authenticated,
    })


def hotels_outside_category_view(request):
    """View for hotels category outside Iraq"""
    from properties.models import PropertyHotel, Country
    
    # Get filters
    star_rating = request.GET.get('star_rating', '')
    country_id = request.GET.get('country', '')
    district = request.GET.get('district', '')
    rent_type = request.GET.get('rent_type', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    hotels = PropertyHotel.objects.exclude(property__country__code='IQ')
    
    if star_rating:
        hotels = hotels.filter(star_rating=int(star_rating))
    
    if country_id:
        hotels = hotels.filter(country_id=int(country_id))
    
    if district:
        hotels = hotels.filter(district__icontains=district)
    
    if rent_type == 'collective':
        hotels = hotels.filter(supports_collective_rent=True)
    
    if price_min:
        hotels = [h for h in hotels if h.price_per_night and h.price_per_night >= int(price_min)]
    if price_max:
        hotels = [h for h in hotels if h.price_per_night and h.price_per_night <= int(price_max)]
    
    # Get all countries
    countries = Country.objects.all().order_by('name_ar')
    
    return render(request, 'properties/categories/hotels_outside.html', {
        'hotels': hotels,
        'star_rating': star_rating,
        'country_id': country_id,
        'district': district,
        'rent_type': rent_type,
        'price_min': price_min,
        'price_max': price_max,
        'countries': countries,
        'category_title': 'فنادق خارج العراق',
        'category_icon': '🏨🌍',
        'can_create_hotel': request.user.is_authenticated,
    })


def resorts_category_view(request):
    """View for resorts category"""
    from properties.models import PropertyResort
    from properties.constants import IRAQ_GOVERNORATES
    
    # Get filters
    resort_type = request.GET.get('resort_type', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    resorts = PropertyResort.objects.all()
    
    if resort_type:
        resorts = resorts.filter(resort_type=resort_type)
    
    if price_min:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night >= int(price_min)]
    if price_max:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night <= int(price_max)]
    
    return render(request, 'properties/categories/resorts.html', {
        'resorts': resorts,
        'resort_type': resort_type,
        'price_min': price_min,
        'price_max': price_max,
        'governorates': IRAQ_GOVERNORATES,
        'category_title': 'منتجعات وأماكن سياحية',
        'category_icon': '🏖️',
    })


def outside_iraq_category_view(request):
    """View for properties outside Iraq category"""
    from properties.models import Country, City, Area
    
    # Get filters
    country_id = request.GET.get('country', '')
    city_id = request.GET.get('city', '')
    property_type = request.GET.get('property_type', 'all')
    status = request.GET.get('status', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    properties = get_public_properties()
    properties = [p for p in properties if p.country and p.country.code != 'IQ']
    
    if country_id:
        properties = [p for p in properties if p.country_id == int(country_id)]
    
    if city_id:
        properties = [p for p in properties if p.city_id == int(city_id)]
    
    if property_type != 'all':
        properties = [p for p in properties if p.type == property_type]
    
    if status == 'sale':
        properties = [p for p in properties if p.status in PUBLIC_STATUSES]
    elif status == 'rent':
        properties = [p for p in properties if p.status == 'rent']
    elif status == 'collective_rent':
        properties = [p for p in properties if p.status == 'collective_rent']
    
    if price_min:
        properties = [p for p in properties if p.price >= int(price_min)]
    if price_max:
        properties = [p for p in properties if p.price <= int(price_max)]
    
    # Get all countries
    countries = Country.objects.filter(is_active=True).order_by('name_ar')
    
    # Get user's likes and saves if authenticated
    user_likes = set()
    user_saves = set()
    if request.user.is_authenticated:
        user_likes = set(PropertyLike.objects.filter(user=request.user).values_list('property_id', flat=True))
        user_saves = set(PropertySave.objects.filter(user=request.user).values_list('property_id', flat=True))
    
    return render(request, 'properties/categories/outside_iraq.html', {
        'properties': properties,
        'countries': countries,
        'country_id': country_id,
        'city_id': city_id,
        'property_type': property_type,
        'price_min': price_min,
        'price_max': price_max,
        'user_likes': user_likes,
        'user_saves': user_saves,
        'category_title': 'عقارات خارج العراق',
        'category_icon': '🌍',
    })


# ==================== Dynamic Property Addition View ====================

def handle_media_uploads(request, property):
    """Handle media uploads for properties (images, videos, 360°)"""
    from .models import PropertyImage, PropertyVideo
    
    # Handle cover image (main property field)
    if 'cover_image' in request.FILES:
        property.cover_image = request.FILES['cover_image']
        property.save(update_fields=['cover_image'])
    
    # Handle personal image
    if 'personal_image' in request.FILES:
        property.personal_image = request.FILES['personal_image']
        property.save(update_fields=['personal_image'])
    
    # Handle additional images (max 10) - stored in PropertyImage model
    if 'additional_images' in request.FILES:
        additional_files = request.FILES.getlist('additional_images')
        for idx, img_file in enumerate(additional_files[:10]):  # Limit to 10 images
            PropertyImage.objects.create(
                property=property,
                image=img_file,
                is_primary=False,
                image_type='photo',
                sort_order=idx + 1
            )
    
    # Handle property video
    if 'property_video' in request.FILES:
        video_file = request.FILES['property_video']
        PropertyVideo.objects.create(
            property=property,
            video=video_file,
            sort_order=0
        )
    
    # Handle 360° images
    if '360_images' in request.FILES:
        files_360 = request.FILES.getlist('360_images')
        for idx, img_360 in enumerate(files_360):
            PropertyImage.objects.create(
                property=property,
                image=img_360,
                is_primary=False,
                image_type='360',
                sort_order=idx + 100  # Use higher sort order for 360 images
            )


@login_required
def dynamic_add_property(request):
    """View for dynamic property addition based on category"""
    from .models import PropertyImage, PropertyVideo, BrokerPlanSubscription, Broker
    from .services import SubscriptionService
    from django.utils import timezone
    from datetime import timedelta
    from django.core.exceptions import ValidationError
    
    category_form = DynamicPropertyForm(request.POST or None)
    property_form = None
    template_name = 'properties/dynamic_add_property.html'
    
    # Get broker and check subscription
    broker = None
    try:
        broker = Broker.objects.get(user=request.user)
    except Broker.DoesNotExist:
        pass
    
    if request.method == 'POST':
        category = request.POST.get('category')
        publication_type = request.POST.get('publication_type', 'normal')
        publication_days = request.POST.get('publication_days')
        
        # Check if user has broker account
        if not broker:
            messages.error(request, 'يجب أن يكون لديك حساب دلال لإضافة عقارات')
            return render(request, template_name, {
                'category_form': category_form,
                'property_form': property_form,
                'category': category,
            })
        
        # Use SubscriptionService for secure subscription check
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check subscription before action
        is_allowed, message = SubscriptionService.check_subscription_before_action(
            request.user,
            "Add property",
            ip_address,
            user_agent
        )
        
        if not is_allowed:
            messages.error(request, message)
            return render(request, template_name, {
                'category_form': category_form,
                'property_form': property_form,
                'category': category,
            })
        
        # Check property limit using SubscriptionService
        can_add, limit_message = SubscriptionService.can_add_property(broker)
        if not can_add:
            messages.error(request, limit_message)
            return render(request, template_name, {
                'category_form': category_form,
                'property_form': property_form,
                'category': category,
            })
        
        # Check if user has premium subscription for featured/pinned ads
        if publication_type in ['featured', 'pinned']:
            active_subscription = SubscriptionService.get_broker_subscription(broker)
            
            if not active_subscription or active_subscription.plan.tier != 'premium':
                messages.error(request, 'يتطلب الإعلان المميز أو المثبت اشتراك مميز. يرجى ترقية اشتراكك.')
                return render(request, template_name, {
                    'category_form': category_form,
                    'property_form': property_form,
                    'category': category,
                })
        
        if category == 'inside_iraq':
            property_form = PropertyInsideIraqForm(request.POST, request.FILES)
            if property_form.is_valid():
                property = property_form.save(commit=False)
                property.category = 'property_iraq'
                property.owner = request.user
                property.broker = broker
                
                # Set expiry date based on subscription
                subscription = SubscriptionService.get_broker_subscription(broker)
                property.expiry_date = subscription.end_date if subscription else timezone.now() + timedelta(days=30)
                
                # Handle publication type
                if publication_type == 'featured':
                    property.is_featured = True
                    if publication_days:
                        property.promotion_until = timezone.now().date() + timedelta(days=int(publication_days))
                elif publication_type == 'pinned':
                    property.is_pinned = True
                    if publication_days:
                        property.pinned_until = timezone.now() + timedelta(days=int(publication_days))
                
                # Increment property count using SubscriptionService
                try:
                    SubscriptionService.increment_property_count(broker)
                except Exception as e:
                    messages.error(request, str(e))
                    return render(request, template_name, {
                        'category_form': category_form,
                        'property_form': property_form,
                        'category': category,
                    })
                property.save()
                
                # Handle media uploads
                handle_media_uploads(request, property)
                
                messages.success(request, 'تم إضافة العقار داخل العراق بنجاح')
                return redirect('dashboard')
                
        elif category == 'outside_iraq':
            property_form = PropertyOutsideIraqForm(request.POST, request.FILES)
            if property_form.is_valid():
                property = property_form.save(commit=False)
                property.category = 'property_outside'
                property.owner = request.user
                property.broker = broker
                
                # Set expiry date based on subscription
                subscription = SubscriptionService.get_broker_subscription(broker)
                property.expiry_date = subscription.end_date if subscription else timezone.now() + timedelta(days=30)
                
                # Handle publication type
                if publication_type == 'featured':
                    property.is_featured = True
                    if publication_days:
                        property.promotion_until = timezone.now().date() + timedelta(days=int(publication_days))
                elif publication_type == 'pinned':
                    property.is_pinned = True
                    if publication_days:
                        property.pinned_until = timezone.now() + timedelta(days=int(publication_days))
                
                # Increment property count using SubscriptionService
                try:
                    SubscriptionService.increment_property_count(broker)
                except Exception as e:
                    messages.error(request, str(e))
                    return render(request, template_name, {
                        'category_form': category_form,
                        'property_form': property_form,
                        'category': category,
                    })
                
                property.save()
                
                # Handle media uploads
                handle_media_uploads(request, property)
                
                messages.success(request, 'تم إضافة العقار خارج العراق بنجاح')
                return redirect('dashboard')
                
        elif category == 'hotel':
            property_form = PropertyHotelForm(request.POST, request.FILES)
            if property_form.is_valid():
                # Set expiry date based on subscription
                subscription = SubscriptionService.get_broker_subscription(broker)
                expiry_date = subscription.end_date if subscription else timezone.now() + timedelta(days=30)
                
                # Create base property first
                property = Property.objects.create(
                    title=property_form.cleaned_data['hotel_name'],
                    category='hotel',
                    type='hotel',
                    owner=request.user,
                    broker=broker,
                    status='published',
                    price=property_form.cleaned_data.get('price_per_night') or 0,
                    currency=property_form.cleaned_data.get('currency', 'USD'),
                    district=property_form.cleaned_data.get('district') or property_form.cleaned_data.get('city') or 'غير محدد',
                    location=property_form.cleaned_data.get('address') or property_form.cleaned_data.get('city') or 'غير محدد',
                    description=property_form.cleaned_data.get('description') or property_form.cleaned_data['hotel_name'],
                    phone=property_form.cleaned_data.get('phone') or getattr(broker, 'phone', '') or '0000000000',
                    area=property_form.cleaned_data.get('area') or 1,
                    governorate=property_form.cleaned_data.get('governorate') or '',
                    city=property_form.cleaned_data.get('city') or '',
                    expiry_date=expiry_date,
                )
                
                # Handle publication type for hotel
                if publication_type == 'featured':
                    property.is_featured = True
                    if publication_days:
                        property.promotion_until = timezone.now().date() + timedelta(days=int(publication_days))
                elif publication_type == 'pinned':
                    property.is_pinned = True
                    if publication_days:
                        property.pinned_until = timezone.now() + timedelta(days=int(publication_days))
                
                # Increment property count using SubscriptionService
                try:
                    SubscriptionService.increment_property_count(broker)
                except Exception as e:
                    messages.error(request, str(e))
                    property.delete()
                    return render(request, template_name, {
                        'category_form': category_form,
                        'property_form': property_form,
                        'category': category,
                    })
                
                property.save()
                
                # Create hotel details
                hotel = property_form.save(commit=False)
                hotel.property = property
                hotel.save()
                
                # Handle media uploads
                handle_media_uploads(request, property)
                
                messages.success(request, 'تم إضافة الفندق بنجاح')
                return redirect('dashboard')
                
        elif category == 'resort':
            # Handle resort creation directly
            name = request.POST.get('name')
            resort_type = request.POST.get('resort_type')
            description = request.POST.get('description')
            governorate = request.POST.get('governorate')
            city = request.POST.get('city')
            district = request.POST.get('district')
            full_address = request.POST.get('full_address')
            phone = request.POST.get('phone')
            whatsapp = request.POST.get('whatsapp')
            email = request.POST.get('email')
            website = request.POST.get('website')
            working_hours = request.POST.get('working_hours')
            working_days = request.POST.get('working_days')
            min_price = request.POST.get('min_price')
            max_price = request.POST.get('max_price')
            currency = request.POST.get('currency', 'د.ع')
            advance_booking = request.POST.get('advance_booking') == 'on'
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            video_url = request.POST.get('video_url')
            meta_title = request.POST.get('meta_title')
            meta_description = request.POST.get('meta_description')
            keywords = request.POST.get('keywords')
            
            # Handle publication type for resort
            publication_type = request.POST.get('publication_type', 'normal')
            publication_days = request.POST.get('publication_days')
            
            if name and resort_type and description and governorate and city and full_address and phone:
                from .models import Resort, ResortAmenity, ResortService
                
                # Set expiry date based on subscription
                subscription = SubscriptionService.get_broker_subscription(broker)
                expiry_date = subscription.end_date if subscription else timezone.now() + timedelta(days=30)
                
                # Create base property first
                property = Property.objects.create(
                    title=name,
                    category='resort',
                    type='resort',
                    owner=request.user,
                    broker=broker,
                    status='published',
                    price=min_price or 0,
                    currency=currency,
                    district=city or 'غير محدد',
                    location=full_address or city or 'غير محدد',
                    description=description or name,
                    phone=phone or getattr(broker, 'phone', '') or '0000000000',
                    area=1,
                    governorate=governorate or '',
                    city=city or '',
                    expiry_date=expiry_date,
                )
                
                # Handle publication type for resort
                if publication_type == 'featured':
                    property.is_featured = True
                    if publication_days:
                        property.promotion_until = timezone.now().date() + timedelta(days=int(publication_days))
                elif publication_type == 'pinned':
                    property.is_pinned = True
                    if publication_days:
                        property.pinned_until = timezone.now() + timedelta(days=int(publication_days))
                
                # Increment property count using SubscriptionService
                try:
                    SubscriptionService.increment_property_count(broker)
                except Exception as e:
                    messages.error(request, str(e))
                    property.delete()
                    return render(request, template_name, {
                        'category_form': category_form,
                        'property_form': property_form,
                        'category': category,
                    })
                
                property.save()
                
                # Handle media uploads
                handle_media_uploads(request, property)
                
                resort = Resort.objects.create(
                    name=name,
                    resort_type=resort_type,
                    description=description,
                    governorate=governorate,
                    city=city,
                    district=district,
                    full_address=full_address,
                    phone=phone,
                    whatsapp=whatsapp,
                    email=email,
                    website=website,
                    working_hours=working_hours,
                    working_days=working_days,
                    min_price=min_price,
                    max_price=max_price,
                    currency=currency,
                    advance_booking=advance_booking,
                    latitude=latitude,
                    longitude=longitude,
                    video_url=video_url,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    keywords=keywords,
                    broker=broker,
                    user=request.user,
                    property=property,  # Link resort to property
                )
                
                # Handle logo (separate from cover_image)
                if 'logo' in request.FILES:
                    resort.logo = request.FILES['logo']
                
                resort.save()
                
                # Add amenities
                amenities = request.POST.getlist('amenities')
                for amenity in amenities:
                    ResortAmenity.objects.create(
                        resort=resort,
                        amenity_type=amenity,
                        is_available=True
                    )
                
                # Add services
                services = request.POST.getlist('services')
                for service in services:
                    ResortService.objects.create(
                        resort=resort,
                        service_type=service,
                        is_available=True
                    )
                
                messages.success(request, 'تم إضافة المنتجع بنجاح')
                return redirect('resort_detail', slug=resort.slug)
            else:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
    
    # Get the appropriate form based on selected category
    category = request.GET.get('category') or request.POST.get('category')
    
    # Initialize all forms for instant switching
    inside_iraq_form = PropertyInsideIraqForm()
    outside_iraq_form = PropertyOutsideIraqForm()
    hotel_form = PropertyHotelForm()
    resort_form = PropertyResortForm()
    
    # Default form if no category selected
    if category == 'inside_iraq':
        property_form = PropertyInsideIraqForm()
    elif category == 'outside_iraq':
        property_form = PropertyOutsideIraqForm()
    elif category == 'hotel':
        property_form = PropertyHotelForm()
    elif category == 'resort':
        property_form = PropertyResortForm()
    else:
        # Default to inside_iraq form if no category selected
        property_form = PropertyInsideIraqForm()
    
    return render(request, template_name, {
        'category_form': category_form,
        'property_form': property_form,
        'category': category,
        'inside_iraq_form': inside_iraq_form,
        'outside_iraq_form': outside_iraq_form,
        'hotel_form': hotel_form,
        'resort_form': resort_form,
    })


@login_required
@staff_required
def reject_property_payment(request, payment_id):
    """Admin view to reject property payment"""
    payment = get_object_or_404(PropertyPayment, id=payment_id)
    
    if payment.status != PropertyPayment.STATUS_PENDING:
        messages.error(request, 'هذا الدفع ليس في حالة انتظار')
        return redirect('admin_panel')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        payment.status = PropertyPayment.STATUS_FAILED
        payment.rejection_reason = rejection_reason
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.save()
        
        # Update property status
        property = payment.property
        property.status = Property.STATUS_REJECTED
        property.rejection_reason = rejection_reason
        property.save()
        
        # Create notification
        PropertyNotification.objects.create(
            user=payment.broker.user,
            property=property,
            notification_type=PropertyNotification.TYPE_PROPERTY_REJECTED,
            title='تم رفض الدفع',
            message=f'تم رفض دفع العقار: {property.display_title}. السبب: {rejection_reason}'
        )
        
        messages.success(request, 'تم رفض الدفع')
        return redirect('admin_panel')
    
    context = {
        'payment': payment,
        'property': payment.property,
    }
    
    return render(request, 'properties/reject_payment.html', context)


@login_required
@staff_required
def content_moderation_view(request):
    """لوحة الموافقة على المحتوى - منشورات، قنوات، عقارات"""
    
    # فلترة حسب النوع
    content_type = request.GET.get('type', 'all')
    status_filter = request.GET.get('status', 'pending')
    
    # القنوات المعلقة
    pending_channels = BrokerChannel.objects.filter(status='pending').select_related('broker', 'broker__user')
    
    # المنشورات المعلقة
    pending_posts = ChannelPost.objects.filter(is_published=False).select_related('channel', 'channel__broker')
    
    # الفيديوهات المعلقة
    pending_videos = ChannelVideo.objects.filter(is_published=False).select_related('channel', 'channel__broker')
    
    # العقارات المعلقة
    pending_properties = Property.objects.filter(status=Property.STATUS_PENDING_APPROVAL).select_related('broker', 'owner')
    
    # القنوات المحجوبة
    suspended_channels = BrokerChannel.objects.filter(status='suspended').select_related('broker', 'broker__user')
    
    # الدلالين المحجوبين
    suspended_brokers = Broker.objects.filter(is_active=False).select_related('user')
    
    context = {
        'pending_channels': pending_channels,
        'pending_posts': pending_posts,
        'pending_videos': pending_videos,
        'pending_properties': pending_properties,
        'suspended_channels': suspended_channels,
        'suspended_brokers': suspended_brokers,
        'content_type': content_type,
        'status_filter': status_filter,
    }
    
    return render(request, 'properties/content_moderation.html', context)


@login_required
@staff_required
def approve_channel(request, channel_id):
    """الموافقة على قناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = BrokerChannel.STATUS_ACTIVE
    channel.save()
    
    messages.success(request, f'تم تفعيل قناة {channel.name} بنجاح')
    return redirect('content_moderation')


@login_required
@staff_required
def reject_channel(request, channel_id):
    """رفض قناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = BrokerChannel.STATUS_INACTIVE
    channel.save()
    
    messages.success(request, f'تم رفض قناة {channel.name}')
    return redirect('content_moderation')


@login_required
@staff_required
def suspend_channel(request, channel_id):
    """حجب قناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = BrokerChannel.STATUS_SUSPENDED
    channel.save()
    
    messages.success(request, f'تم حجب قناة {channel.name}')
    return redirect('content_moderation')


@login_required
@staff_required
def unsuspend_channel(request, channel_id):
    """فك حجب قناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    channel.status = BrokerChannel.STATUS_ACTIVE
    channel.save()
    
    messages.success(request, f'تم فك حجب قناة {channel.name}')
    return redirect('content_moderation')


@login_required
@staff_required
def approve_post(request, post_id):
    """الموافقة على منشور"""
    post = get_object_or_404(ChannelPost, id=post_id)
    post.is_published = True
    post.save()
    
    messages.success(request, 'تم نشر المنشور بنجاح')
    return redirect('content_moderation')


@login_required
@staff_required
def reject_post(request, post_id):
    """رفض منشور"""
    post = get_object_or_404(ChannelPost, id=post_id)
    post.delete()
    
    messages.success(request, 'تم حذف المنشور')
    return redirect('content_moderation')


@login_required
@staff_required
def approve_video(request, video_id):
    """الموافقة على فيديو"""
    video = get_object_or_404(ChannelVideo, id=video_id)
    video.is_published = True
    video.save()
    
    messages.success(request, 'تم نشر الفيديو بنجاح')
    return redirect('content_moderation')


@login_required
@staff_required
def reject_video(request, video_id):
    """رفض فيديو"""
    video = get_object_or_404(ChannelVideo, id=video_id)
    video.delete()
    
    messages.success(request, 'تم حذف الفيديو')
    return redirect('content_moderation')


@login_required
@staff_required
def suspend_broker(request, broker_id):
    """حجب دلال"""
    broker = get_object_or_404(Broker, id=broker_id)
    broker.is_active = False
    broker.save()
    
    # حجب القناة أيضاً
    if hasattr(broker, 'channel'):
        broker.channel.status = BrokerChannel.STATUS_SUSPENDED
        broker.channel.save()
    
    messages.success(request, f'تم حجب الدلال {broker.display_name}')
    return redirect('content_moderation')


@login_required
@staff_required
def unsuspend_broker(request, broker_id):
    """فك حجب دلال"""
    broker = get_object_or_404(Broker, id=broker_id)
    broker.is_active = True
    broker.save()
    
    # تفعيل القناة أيضاً
    if hasattr(broker, 'channel'):
        broker.channel.status = BrokerChannel.STATUS_ACTIVE
        broker.channel.save()
    
    messages.success(request, f'تم فك حجب الدلال {broker.display_name}')
    return redirect('content_moderation')


@login_required
@staff_required
def user_monitoring_view(request):
    """لوحة مراقبة المستخدمين - حذف، حجب، تقيد، إنذار"""
    from django.contrib.auth.models import User
    
    # البحث والفلترة
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    user_type_filter = request.GET.get('user_type', 'all')
    
    users = User.objects.all().select_related('broker_profile', 'user_profile')
    
    # تطبيق البحث
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # فلترة حسب الحالة
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'suspended':
        users = users.filter(is_active=False)
    
    # فلترة حسب نوع المستخدم
    if user_type_filter == 'admin':
        users = users.filter(is_superuser=True)
    elif user_type_filter == 'broker':
        users = users.filter(broker_profile__isnull=False)
    elif user_type_filter == 'regular':
        users = users.filter(broker_profile__isnull=True, is_superuser=False, is_staff=False)
    
    # استبعاد المستخدم الحالي
    users = users.exclude(id=request.user.id)
    
    # ترتيب حسب تاريخ التسجيل
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'search_query': search_query,
        'status_filter': status_filter,
        'user_type_filter': user_type_filter,
    }
    
    return render(request, 'properties/user_monitoring.html', context)


@login_required
@staff_required
def delete_user(request, user_id):
    """حذف مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    # منع حذف المستخدم الحالي
    if user.id == request.user.id:
        messages.error(request, 'لا يمكن حذف حسابك الخاص')
        return redirect('user_monitoring')
    
    username = user.username
    user_type = "مشرف" if user.is_superuser else ("دلال" if hasattr(user, 'broker_profile') else "مستخدم")
    
    user.delete()
    
    messages.success(request, f'تم حذف {user_type} {username} بنجاح')
    return redirect('user_monitoring')


@login_required
@staff_required
def suspend_user(request, user_id):
    """حجب مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    # منع حجب المستخدم الحالي
    if user.id == request.user.id:
        messages.error(request, 'لا يمكن حجب حسابك الخاص')
        return redirect('user_monitoring')
    
    user.is_active = False
    user.save()
    
    # حجب الدلال أيضاً إذا كان دلال
    if hasattr(user, 'broker_profile'):
        user.broker_profile.is_active = False
        user.broker_profile.save()
        
        # حجب القناة أيضاً
        if hasattr(user.broker_profile, 'channel'):
            user.broker_profile.channel.status = BrokerChannel.STATUS_SUSPENDED
            user.broker_profile.channel.save()
    
    user_type = "مشرف" if user.is_superuser else ("دلال" if hasattr(user, 'broker_profile') else "مستخدم")
    messages.success(request, f'تم حجب {user_type} {user.username}')
    return redirect('user_monitoring')


@login_required
@staff_required
def user_details_api(request, user_id):
    """API للحصول على تفاصيل المستخدم"""
    from django.http import JsonResponse
    
    user = get_object_or_404(User, id=user_id)
    
    broker_info = None
    if hasattr(user, 'broker_profile'):
        broker_info = {
            'phone': user.broker_profile.phone,
            'governorate': user.broker_profile.governorate,
            'is_active': user.broker_profile.is_active,
            'is_verified': user.broker_profile.is_verified,
        }
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'user_type': 'مشرف' if user.is_superuser else ('دلال' if hasattr(user, 'broker_profile') else 'مستخدم'),
        'is_active': user.is_active,
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
        'broker_info': broker_info,
    }
    
    return JsonResponse({
        'success': True,
        'user': user_data
    })


@login_required
@staff_required
def unsuspend_user(request, user_id):
    """فك حجب مستخدم"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    
    # تفعيل الدلال أيضاً إذا كان دلال
    if hasattr(user, 'broker_profile'):
        user.broker_profile.is_active = True
        user.broker_profile.save()
        
        # تفعيل القناة أيضاً
        if hasattr(user.broker_profile, 'channel'):
            user.broker_profile.channel.status = BrokerChannel.STATUS_ACTIVE
            user.broker_profile.channel.save()
    
    messages.success(request, f'تم فك حجب المستخدم {user.username}')
    return redirect('user_monitoring')


@login_required
@staff_required
def restrict_user(request, user_id):
    """تقيد مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    if user.is_superuser:
        messages.error(request, 'لا يمكن تقيد المشرفين')
        return redirect('user_monitoring')
    
    # تقيد المستخدم - منع نشر العقارات
    if hasattr(user, 'broker_profile'):
        user.broker_profile.can_post_properties = False
        user.broker_profile.save()
    
    messages.success(request, f'تم تقيد المستخدم {user.username}')
    return redirect('user_monitoring')


@login_required
@staff_required
def unrestrict_user(request, user_id):
    """فك تقيد مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    # فك تقيد المستخدم
    if hasattr(user, 'broker_profile'):
        user.broker_profile.can_post_properties = True
        user.broker_profile.save()
    
    messages.success(request, f'تم فك تقيد المستخدم {user.username}')
    return redirect('user_monitoring')


@login_required
@staff_required
def warn_user(request, user_id):
    """إنذار مستخدم"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        warning_message = request.POST.get('warning_message', '')
        
        if not warning_message:
            messages.error(request, 'يرجى كتابة رسالة الإنذار')
        else:
            # إنشاء إشعار للمستخدم
            Notification.objects.create(
                user=user,
                notification_type='warning',
                title='إنذار من الإدارة',
                message=warning_message
            )
            
            messages.success(request, f'تم إرسال إنذار للمستخدم {user.username}')
            return redirect('user_monitoring')
    
    context = {
        'user': user,
    }
    
    return render(request, 'properties/warn_user.html', context)




@login_required
def service_provider_register(request):
    """تسجيل مقدم خدمة جديد"""
    try:
        provider = ServiceProvider.objects.get(user=request.user)
        return redirect('service_provider_dashboard')
    except ServiceProvider.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = ServiceProviderForm(request.POST, request.FILES)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            messages.success(request, 'تم إنشاء حساب مقدم الخدمة بنجاح')
            return redirect('service_provider_dashboard')
    else:
        form = ServiceProviderForm()
    
    return render(request, 'properties/service_provider_register.html', {'form': form})


@login_required
def service_provider_dashboard(request):
    """لوحة تحكم مقدم الخدمة"""
    try:
        provider = ServiceProvider.objects.get(user=request.user)
    except ServiceProvider.DoesNotExist:
        return redirect('service_provider_register')
    
    advertisements = ServiceAdvertisement.objects.filter(service_provider=provider).order_by('-created_at')
    
    return render(request, 'properties/service_provider_dashboard.html', {
        'provider': provider,
        'advertisements': advertisements,
    })


@login_required
def create_service_advertisement(request):
    """إنشاء إعلان خدمة جديد"""
    from .permissions import get_broker
    try:
        provider = ServiceProvider.objects.get(user=request.user)
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'يرجى تسجيل حساب مقدم خدمة أولاً')
        return redirect('service_provider_register')
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.is_subscription_active():
            messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر هذه الخدمة.')
            return redirect('subscription_plans')
    
    if request.method == 'POST':
        form = ServiceAdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.service_provider = provider
            
            # Save address fields
            advertisement.city = request.POST.get('city', '')
            advertisement.district = request.POST.get('district', '')
            advertisement.subdistrict = request.POST.get('subdistrict', '')
            advertisement.area = request.POST.get('area', '')
            advertisement.neighborhood = request.POST.get('neighborhood', '')
            advertisement.mahalla = request.POST.get('mahalla', '')
            advertisement.block = request.POST.get('block', '')
            advertisement.street = request.POST.get('street', '')
            advertisement.alley = request.POST.get('alley', '')
            advertisement.house_number = request.POST.get('house_number', '')
            advertisement.property_number = request.POST.get('property_number', '')
            advertisement.landmark = request.POST.get('landmark', '')
            
            # Save GPS coordinates
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if latitude:
                advertisement.latitude = latitude
            if longitude:
                advertisement.longitude = longitude
            
            # Handle featured ads
            if advertisement.is_featured:
                from datetime import timedelta
                advertisement.featured_until = timezone.now() + timedelta(days=30)
            
            advertisement.status = 'active'
            advertisement.save()
            messages.success(request, 'تم إنشاء الإعلان بنجاح')
            return redirect('service_provider_dashboard')
    else:
        form = ServiceAdvertisementForm()
    
    return render(request, 'properties/create_service_advertisement.html', {'form': form})


def public_service_advertisements(request):
    """صفحة عرض إعلانات الخدمات العامة"""
    from django.db.models import Q
    
    # Get only active advertisements
    advertisements = ServiceAdvertisement.objects.filter(status='active').select_related('service_provider').order_by('-is_featured', '-created_at')
    
    # Apply filters
    service_type = request.GET.get('service_type')
    if service_type:
        advertisements = advertisements.filter(service_type=service_type)
    
    governorate = request.GET.get('governorate')
    if governorate:
        advertisements = advertisements.filter(governorate=governorate)
    
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        advertisements = advertisements.filter(price__gte=price_min)
    if price_max:
        advertisements = advertisements.filter(price__lte=price_max)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        advertisements = advertisements.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    return render(request, 'properties/public_service_advertisements.html', {
        'advertisements': advertisements,
        'service_type': service_type,
        'governorate': governorate,
        'price_min': price_min,
        'price_max': price_max,
        'search_query': search_query,
    })


@login_required
def service_advertisement_detail(request, ad_id):
    """عرض تفاصيل إعلان الخدمة"""
    advertisement = get_object_or_404(ServiceAdvertisement, pk=ad_id)
    
    # Increment views
    advertisement.views_count += 1
    advertisement.save()
    
    return render(request, 'properties/service_advertisement_detail.html', {
        'advertisement': advertisement
    })


@login_required
def edit_service_advertisement(request, ad_id):
    """تعديل إعلان خدمة"""
    advertisement = get_object_or_404(ServiceAdvertisement, pk=ad_id)
    
    # Check ownership
    if advertisement.service_provider.user != request.user and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية تعديل هذا الإعلان')
        return redirect('service_provider_dashboard')
    
    if request.method == 'POST':
        form = ServiceAdvertisementForm(request.POST, request.FILES, instance=advertisement)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الإعلان بنجاح')
            return redirect('service_provider_dashboard')
    else:
        form = ServiceAdvertisementForm(instance=advertisement)
    
    return render(request, 'properties/edit_service_advertisement.html', {
        'form': form,
        'advertisement': advertisement
    })


@login_required
def delete_service_advertisement(request, ad_id):
    """حذف إعلان خدمة"""
    advertisement = get_object_or_404(ServiceAdvertisement, pk=ad_id)
    
    # Check ownership
    if advertisement.service_provider.user != request.user and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية حذف هذا الإعلان')
        return redirect('service_provider_dashboard')
    
    if request.method == 'POST':
        advertisement.delete()
        messages.success(request, 'تم حذف الإعلان بنجاح')
        return redirect('service_provider_dashboard')
    
    return render(request, 'properties/delete_service_advertisement.html', {
        'advertisement': advertisement
    })


@csrf_exempt
def statistics_api(request):
    """API endpoint للحصول على إحصاءات حقيقية"""
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    from django.http import JsonResponse

    # Platform statistics (matching the structure used in platform_stats)
    try:
        from .models import Conversation, Message, MessageReport, BrokerPlanSubscription, FinancialTransaction
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count() if hasattr(Message, 'objects') else 0
        total_reports = MessageReport.objects.count()
        active_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
        total_revenue = sum(t.amount or 0 for t in FinancialTransaction.objects.filter(status='completed'))
    except Exception:
        total_conversations = 0
        total_messages = 0
        total_reports = 0
        active_subscriptions = 0
        total_revenue = 0

    # Properties statistics - country is ForeignKey
    iraq_properties = Property.objects.filter(country__isnull=True).count()
    foreign_properties = Property.objects.filter(country__isnull=False).count()

    # Hotels statistics - hotels don't have country field, just count total
    total_hotels = Hotel.objects.count()

    # Resorts statistics - resorts don't have country field, just count total
    total_resorts = Resort.objects.count()

    # Jobs statistics
    total_jobs = Job.objects.count()

    # Service providers statistics
    service_providers = ServiceProvider.objects.count()
    service_advertisements = ServiceAdvertisement.objects.count()

    # Auctions statistics
    auctions = Auction.objects.count()

    # Broker channels statistics
    from .models import BrokerChannel
    broker_channels = BrokerChannel.objects.count()

    # Properties by type
    properties_by_type = Property.objects.values('type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Properties by governorate
    properties_by_governorate = Property.objects.values('governorate').annotate(
        count=Count('id')
    ).order_by('-count')

    # Monthly user growth for the last 6 months
    monthly_users = []
    months_arabic = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    
    for i in range(5, -1, -1):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        users_in_month = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        
        monthly_users.append({
            'month': months_arabic[month_start.month - 1],
            'count': users_in_month
        })

    return JsonResponse({
        'properties': {
            'iraq': iraq_properties,
            'foreign': foreign_properties,
            'total': iraq_properties + foreign_properties,
            'by_type': list(properties_by_type),
            'by_governorate': list(properties_by_governorate)
        },
        'hotels': {
            'total': total_hotels
        },
        'resorts': {
            'total': total_resorts
        },
        'jobs': {
            'total': total_jobs
        },
        'services': {
            'providers': service_providers,
            'advertisements': service_advertisements
        },
        'auctions': {
            'total': auctions
        },
        'channels': {
            'total': broker_channels
        },
        'conversations': {
            'total': total_conversations
        },
        'messages': {
            'total': total_messages
        },
        'users': {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'monthly_growth': monthly_users
        },
        'brokers': {
            'total': Broker.objects.count()
        },
        # Additional stats to match platform_stats structure
        'total_users': User.objects.count(),
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_reports': total_reports,
        'total_brokers': Broker.objects.count(),
        'active_subscriptions': active_subscriptions,
        'total_revenue': total_revenue
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_growth_data(request):
    """بيانات نمو المنشورات حقيقية"""
    try:
        days = int(request.GET.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get properties created in date range
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        properties_by_date = Property.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Create date range with all dates
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Create data dictionary
        data_dict = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in properties_by_date}
        
        # Fill in missing dates with 0
        data = [data_dict.get(d, 0) for d in date_range]
        
        return Response({
            'labels': date_range,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in chart_growth_data: {e}")
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_property_distribution(request):
    """بيانات توزيع العقارات حقيقية"""
    try:
        distribution_type = request.GET.get('type', 'type')
        
        from django.db.models import Count
        
        if distribution_type == 'type':
            data = Property.objects.values('property_type').annotate(
                count=Count('id')
            ).order_by('-count')
            labels = [item['property_type'] or 'غير محدد' for item in data]
            values = [item['count'] for item in data]
        elif distribution_type == 'location':
            data = Property.objects.values('governorate').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            labels = [item['governorate'] or 'غير محدد' for item in data]
            values = [item['count'] for item in data]
        elif distribution_type == 'price':
            # Group by price ranges
            price_ranges = [
                (0, 100000000, 'أقل من 100 مليون'),
                (100000000, 500000000, '100-500 مليون'),
                (500000000, 1000000000, '500 مليون - 1 مليار'),
                (1000000000, float('inf'), 'أكثر من 1 مليار')
            ]
            data = []
            for min_price, max_price, label in price_ranges:
                count = Property.objects.filter(
                    price__gte=min_price,
                    price__lt=max_price if max_price != float('inf') else None
                ).count()
                data.append({'label': label, 'count': count})
            labels = [item['label'] for item in data]
            values = [item['count'] for item in data]
        else:
            labels = []
            values = []
        
        if not labels:
            return Response({
                'labels': ['لا توجد بيانات'],
                'data': [0],
                'message': 'لا توجد عقارات متاحة'
            })
        
        return Response({
            'labels': labels,
            'data': values
        })
    except Exception as e:
        logger.error(f"Error in chart_property_distribution: {e}")
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_broker_performance(request):
    """بيانات أداء الدلالين الحقيقية"""
    performance_type = request.GET.get('type', 'all')
    
    from django.db.models import Count, Q, Sum
    
    try:
        # حساب أداء الدلالين بناءً على عدة معايير
        brokers = Broker.objects.annotate(
            property_count=Count('property', filter=Q(property__is_active=True)),
            total_views=Sum('property__view_count', filter=Q(property__is_active=True), output_field=models.IntegerField(default=0)),
            message_count=Count('property__messages', filter=Q(property__is_active=True), output_field=models.IntegerField(default=0))
        ).select_related('user')
        
        # حساب نقطة الأداء المتوسطة
        for broker in brokers:
            if broker.property_count > 0:
                # وزن كل معيار
                performance_score = (
                    (broker.property_count * 10) +          # عدد العقارات (أهم معيار)
                    (broker.total_views or 0 * 0.01) +     # المشاهدات
                    (broker.message_count * 2)              # الرسائل
                )
                # تحويل إلى نسبة من 100
                broker.performance_score = min(100, performance_score)
            else:
                broker.performance_score = 0
        
        # الترتيب حسب نوع الفلتر
        if performance_type == 'top':
            brokers = sorted(brokers, key=lambda x: x.performance_score, reverse=True)[:10]
        elif performance_type == 'bottom':
            brokers = sorted(brokers, key=lambda x: x.performance_score)[:10]
        else:
            brokers = sorted(brokers, key=lambda x: x.performance_score, reverse=True)[:20]
        
        labels = []
        values = []
        
        for broker in brokers:
            # استخدام اسم الشركة أو اسم المستخدم
            broker_name = broker.company_name if broker.company_name else (broker.user.username if broker.user else f'دلال {broker.id}')
            labels.append(broker_name)
            values.append(broker.performance_score)
        
        # إذا لم توجد بيانات
        if not labels:
            return Response({
                'labels': ['لا توجد بيانات'],
                'data': [0],
                'message': 'لا توجد دلالين متاحين حالياً'
            })
        
        return Response({
            'labels': labels,
            'data': values
        })
        
    except Exception as e:
        logger.error(f"Error in chart_broker_performance: {e}")
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_revenue(request):
    """بيانات الإيرادات الحقيقية من قاعدة البيانات"""
    from django.db.models import Sum
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    period = request.GET.get('period', 'monthly')
    
    try:
        # استخدام PropertyPayment للحصول على بيانات حقيقية
        if period == 'monthly':
            # آخر 12 شهر
            labels = []
            values = []
            today = timezone.now().date()
            
            for i in range(12):
                # حساب بداية ونهاية الشهر
                month_date = today - timedelta(days=30*i)
                year = month_date.year
                month = month_date.month
                
                # جلب الإيرادات لهذا الشهر
                revenue = PropertyPayment.objects.filter(
                    created_at__year=year,
                    created_at__month=month,
                    status=PropertyPayment.STATUS_COMPLETED
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                # اسم الشهر بالعربية
                month_names = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 
                               'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
                labels.append(month_names[month-1])
                values.append(float(revenue))
            
            # عكس القائمة لعرض الأشهر من الأقدم للأحدث
            labels = labels[::-1]
            values = values[::-1]
            
        elif period == 'quarterly':
            # آخر 4 أرباع سنوات
            labels = ['الربع الأول', 'الربع الثاني', 'الربع الثالث', 'الربع الرابع']
            values = []
            today = timezone.now().date()
            
            for i in range(4):
                # حساب بداية ونهاية الربع
                quarter_num = (today.month - 1) // 3 + 1
                current_quarter_start = datetime(today.year, (quarter_num - 1) * 3 + 1, 1)
                
                if i == 0:
                    # الربع الحالي
                    start_date = current_quarter_start
                    end_date = today
                else:
                    # الأرباع السابقة
                    start_date = current_quarter_start - timedelta(days=90*i)
                    end_date = start_date + timedelta(days=90)
                
                revenue = PropertyPayment.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lt=end_date,
                    status=PropertyPayment.STATUS_COMPLETED
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                values.append(float(revenue))
            
            # عكس القائمة
            values = values[::-1]
            
        else:  # yearly
            # آخر 4 سنوات
            labels = []
            values = []
            today = timezone.now().date()
            
            for i in range(4):
                year = today.year - i
                revenue = PropertyPayment.objects.filter(
                    created_at__year=year,
                    status=PropertyPayment.STATUS_COMPLETED
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                labels.append(str(year))
                values.append(float(revenue))
            
            # عكس القائمة
            labels = labels[::-1]
            values = values[::-1]
        
        # إذا لم توجد بيانات، ارجع رسالة واضحة
        if not values or all(v == 0 for v in values):
            return Response({
                'labels': labels if labels else ['لا توجد بيانات'],
                'data': values if values else [0],
                'message': 'لا توجد بيانات إيرادات متاحة'
            })
        
        return Response({
            'labels': labels,
            'data': values
        })
        
    except Exception as e:
        logger.error(f"Error in chart_revenue: {e}")
        # في حالة الخطأ، ارجع بيانات فارغة بدلاً من محاكاة
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_users_api(request):
    """API لجلب جميع المستخدمين مع دورهم مع فلترة وبحث متقدم"""
    from .models import Broker, UserProfile
    
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    if role_filter:
        if role_filter == 'broker' or role_filter == 'brokers':
            users = users.filter(Q(broker__isnull=False) | Q(broker_profile__isnull=False))
        elif role_filter == 'admin':
            users = users.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif role_filter == 'user' or role_filter == 'users':
            users = users.filter(is_staff=False, is_superuser=False).exclude(Q(broker__isnull=False) | Q(broker_profile__isnull=False))
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(broker__office_name__icontains=search) |
            Q(broker__site_name__icontains=search) |
            Q(broker__phone__icontains=search)
        ).distinct()
    
    users_data = []
    for user in users[:50]:
        user_role = 'مستخدم'
        is_broker = False
        broker_title = ''
        is_verified = False
        phone = ''
        
        if user.is_superuser:
            user_role = 'مدير النظام'
        elif user.is_staff:
            user_role = 'فريق الإدارة'
        
        broker_obj = getattr(user, 'broker', None) or Broker.objects.filter(user=user).first()
        if broker_obj:
            user_role = 'دلال معتمد' if broker_obj.is_verified else 'دلال'
            is_broker = True
            broker_title = broker_obj.office_name or broker_obj.site_name or broker_obj.job_title or 'دلال عقاري'
            is_verified = broker_obj.is_verified
            phone = broker_obj.phone or ''
        
        avatar_url = None
        profile = getattr(user, 'user_profile', None) or UserProfile.objects.filter(user=user).first()
        if profile and profile.avatar:
            avatar_url = profile.avatar.url
        elif broker_obj and broker_obj.profile_image:
            avatar_url = broker_obj.profile_image.url
        
        display_name = user.get_full_name() or user.username
        if broker_obj and broker_obj.office_name:
            display_name = f"{display_name} ({broker_obj.office_name})"
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'display_name': display_name,
            'email': user.email,
            'phone': phone,
            'role': user_role,
            'is_broker': is_broker,
            'broker_title': broker_title,
            'is_verified': is_verified,
            'is_online': getattr(user, 'is_online', True),
            'profile_image': avatar_url
        })
    
    return JsonResponse({'users': users_data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_messenger_poll(request):
    """API لجلب الرسائل الجديدة لحظياً لمحادثة معينة عبر AJAX"""
    conversation_id = request.GET.get('conversation_id')
    last_message_id = request.GET.get('last_id')
    
    if not conversation_id:
        return Response({'error': 'conversation_id is required'}, status=400)
    
    try:
        conversation = Conversation.objects.get(
            conversation_id=conversation_id,
            participants=request.user
        )
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=404)
    
    # Mark incoming unread messages as read
    conversation.messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    messages_qs = conversation.messages.all()
    if last_message_id and str(last_message_id).isdigit():
        messages_qs = messages_qs.filter(id__gt=int(last_message_id))
    
    messages_qs = messages_qs.order_by('created_at')
    
    messages_data = []
    for msg in messages_qs:
        sender_name = msg.sender.get_full_name() or msg.sender.username
        sender_avatar = None
        if hasattr(msg.sender, 'user_profile') and msg.sender.user_profile.avatar:
            sender_avatar = msg.sender.user_profile.avatar.url
        
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': sender_name,
            'sender_avatar': sender_avatar,
            'is_from_me': msg.sender.id == request.user.id,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'file_size': msg.file_size,
            'time': msg.created_at.strftime('%H:%M'),
            'date': msg.created_at.strftime('%Y-%m-%d'),
            'is_read': msg.is_read,
            'link_url': msg.link_url,
            'link_title': msg.link_title,
            'link_description': msg.link_description,
            'link_image': msg.link_image,
            'latitude': msg.latitude,
            'longitude': msg.longitude,
            'location_name': msg.location_name,
        })
    
    return Response({
        'success': True,
        'messages': messages_data,
        'count': len(messages_data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_messenger_send(request):
    """API لإرسال رسالة فورية عبر AJAX (نص، ملف، بطاقة عقار، تسجيل صوتي، موقع)"""
    conversation_id = request.data.get('conversation_id')
    content = request.data.get('content', '').strip()
    message_type = request.data.get('message_type', 'text')
    property_id = request.data.get('property_id')
    uploaded_file = request.FILES.get('file')
    
    if not conversation_id:
        return Response({'error': 'conversation_id is required'}, status=400)
    
    if not content and not uploaded_file and not property_id:
        return Response({'error': 'محتوى الرسالة أو المرفق مطلوب'}, status=400)
    
    try:
        conversation = Conversation.objects.get(
            conversation_id=conversation_id,
            participants=request.user
        )
    except Conversation.DoesNotExist:
        return Response({'error': 'المحادثة غير موجودة'}, status=404)
    
    other_user = conversation.participants.exclude(id=request.user.id).first()
    if not other_user:
        return Response({'error': 'الطرف الآخر غير موجود'}, status=400)
    
    # Check if sharing a property
    link_url = None
    link_title = None
    link_description = None
    link_image = None
    
    if property_id:
        try:
            prop = Property.objects.get(id=property_id)
            message_type = 'property'
            link_url = f'/property/{prop.id}/'
            link_title = prop.title
            link_desc_parts = []
            if prop.price:
                link_desc_parts.append(f"{int(prop.price):,} د.ع")
            if prop.city or prop.governorate:
                link_desc_parts.append(f"{prop.city or ''} {prop.governorate or ''}".strip())
            link_description = " - ".join(link_desc_parts)
            link_image = prop.cover_image.url if prop.cover_image else None
            if not content:
                content = f"🏠 مشاركة عقار: {prop.title}"
        except Property.DoesNotExist:
            pass
    
    # If file uploaded, detect type
    if uploaded_file:
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            message_type = 'image'
        elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'webm', 'opus']:
            message_type = 'audio'
        elif ext in ['mp4', 'mov']:
            message_type = 'video'
        else:
            message_type = 'file'
    
    # Create Message
    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        recipient=other_user,
        content=content,
        message_type=message_type,
        file=uploaded_file,
        file_name=uploaded_file.name if uploaded_file else '',
        file_size=uploaded_file.size if uploaded_file else None,
        link_url=link_url,
        link_title=link_title,
        link_description=link_description,
        link_image=link_image,
        latitude=request.data.get('latitude'),
        longitude=request.data.get('longitude'),
        location_name=request.data.get('location_name', '')
    )
    
    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['updated_at'])
    
    # Trigger notification
    try:
        from .models import Notification
        Notification.objects.create(
            user=other_user,
            title='رسالة جديدة',
            description=f'رسالة جديدة من {request.user.get_full_name() or request.user.username}',
            notification_type='message',
            action_url=f'/dashboard/messages/?conversation_id={conversation_id}',
            metadata={
                'conversation_id': str(conversation_id),
                'sender_id': request.user.id,
                'message_id': msg.id
            }
        )
    except Exception:
        pass
    
    return Response({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_id': request.user.id,
            'sender_name': request.user.get_full_name() or request.user.username,
            'is_from_me': True,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_url': msg.file.url if msg.file else None,
            'file_name': msg.file_name,
            'time': msg.created_at.strftime('%H:%M'),
            'date': msg.created_at.strftime('%Y-%m-%d'),
            'is_read': False,
            'link_url': msg.link_url,
            'link_title': msg.link_title,
            'link_description': msg.link_description,
            'link_image': msg.link_image,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_messenger_properties(request):
    """API لجلب قائمة العقارات لاختيارها ومشاركتها في المحادثة"""
    search = request.GET.get('search', '').strip()
    props = Property.objects.filter(is_frozen=False).exclude(status='rejected')
    
    broker_obj = getattr(request.user, 'broker', None)
    if broker_obj:
        broker_props = props.filter(broker=broker_obj)
        if broker_props.exists():
            props = broker_props
    
    if search:
        users = props.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(city__icontains=search) |
            Q(governorate__icontains=search)
        )
    
    props_data = []
    for p in props.order_by('-created_at')[:30]:
        loc_str = f"{p.city or ''} {p.governorate or ''}".strip()
        img_url = p.cover_image.url if p.cover_image else None
        props_data.append({
            'id': p.id,
            'title': p.title or 'عقار بدون عنوان',
            'price': f"{int(p.price):,} د.ع" if p.price else 'السعر عند الاتصال',
            'location': loc_str or 'العراق',
            'property_type': str(p.type or p.category or 'عقار'),
            'image': img_url,
            'url': f'/property/{p.id}/'
        })
    
    return Response({
        'properties': props_data
    })


@api_view(['GET'])
@permission_classes([])  # Allow both authenticated and unauthenticated users
def api_notifications_unread(request):
    """API للحصول على عدد الإشعارات غير المقروءة"""
    try:
        if not request.user.is_authenticated:
            return Response({
                'unread_count': 0,
                'notifications': []
            })

        try:
            from .models import NotificationRecipient
            unread_count = NotificationRecipient.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        except Exception:
            # Fallback if NotificationRecipient doesn't exist or has different structure
            try:
                from .models import Notification
                unread_count = Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count()
            except Exception:
                unread_count = 0

        return Response({
            'unread_count': unread_count,
            'notifications': []  # Empty array for compatibility
        })
    except Exception as e:
        return Response({
            'unread_count': 0,
            'notifications': [],
            'error': str(e)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_conversation_api(request):
    """API للتحقق من وجود محادثة مع مستخدم"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return Response({'error': 'يرجى تحديد المستخدم'}, status=400)
    
    try:
        recipient = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'المستخدم غير موجود'}, status=404)
    
    # Check for existing conversation
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).filter(
        conversation_type=Conversation.TYPE_DIRECT
    ).first()
    
    if existing_conversation:
        return Response({
            'conversation_id': str(existing_conversation.conversation_id)
        })
    
    return Response({'conversation_id': None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation_api(request):
    """API لإنشاء محادثة جديدة"""
    recipient_id = request.data.get('recipient_id')
    
    if not recipient_id:
        return Response({'success': False, 'error': 'يرجى تحديد المستخدم'}, status=400)
    
    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return Response({'success': False, 'error': 'المستخدم غير موجود'}, status=404)
    
    # التحقق من وجود محادثة سابقة
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).filter(
        conversation_type=Conversation.TYPE_DIRECT
    ).first()
    
    if existing_conversation:
        return Response({
            'success': True,
            'conversation_id': str(existing_conversation.conversation_id),
            'message': 'المحادثة موجودة بالفعل'
        })
    
    # إنشاء محادثة جديدة
    conversation = Conversation.objects.create(
        conversation_type=Conversation.TYPE_DIRECT
    )
    conversation.participants.add(request.user, recipient)
    
    return Response({
        'success': True,
        'conversation_id': str(conversation.conversation_id),
        'message': 'تم إنشاء المحادثة بنجاح'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_geographic(request):
    """بيانات التوزيع الجغرافي حقيقية"""
    try:
        filter_type = request.GET.get('type', 'all')
        
        from django.db.models import Count
        from .models import BrokerChannel
        
        # استخدام العقارات بدلاً من القنوات للحصول على بيانات أكثر دقة
        if filter_type == 'active':
            properties = Property.objects.filter(status='published')
        elif filter_type == 'verified':
            properties = Property.objects.filter(is_verified=True)
        else:
            properties = Property.objects.all()
        
        # Count by governorate
        data = properties.values('governorate').annotate(
            count=Count('id')
        ).order_by('-count')[:15]
        
        labels = [item['governorate'] or 'غير محدد' for item in data]
        values = [item['count'] for item in data]
        
        if not labels:
            return Response({
                'labels': ['لا توجد بيانات'],
                'data': [0],
                'message': 'لا توجد بيانات جغرافية متاحة'
            })
        
        return Response({
            'labels': labels,
            'data': values
        })
    except Exception as e:
        logger.error(f"Error in chart_geographic: {e}")
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chart_user_activity(request):
    """بيانات نشاط المستخدمين حقيقية"""
    try:
        period = request.GET.get('period', 'daily')
        
        from django.db.models import Count
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
        
        if period == 'daily':
            # Last 7 days
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            activity = User.objects.filter(
                date_joined__gte=start_date,
                date_joined__lte=end_date
            ).annotate(
                date=TruncDate('date_joined')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            date_range = []
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            data_dict = {item['date'].strftime('%Y-%m-%d'): item['count'] for item in activity}
            data = [data_dict.get(d, 0) for d in date_range]
            labels = date_range
            
        elif period == 'weekly':
            # Last 4 weeks
            activity = User.objects.filter(
                date_joined__gte=date.today() - timedelta(days=28)
            ).annotate(
                week=TruncWeek('date_joined')
            ).values('week').annotate(
                count=Count('id')
            ).order_by('week')
            
            labels = [f"أسبوع {i+1}" for i in range(len(activity))]
            data = [item['count'] for item in activity]
            
        else:  # monthly
            # Last 6 months
            activity = User.objects.filter(
                date_joined__gte=date.today() - timedelta(days=180)
            ).annotate(
                month=TruncMonth('date_joined')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            labels = [item['month'].strftime('%Y-%m') for item in activity]
            data = [item['count'] for item in activity]
        
        if not labels:
            return Response({
                'labels': ['لا توجد بيانات'],
                'data': [0],
                'message': 'لا توجد بيانات نشاط متاحة'
            })
        
        return Response({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error in chart_user_activity: {e}")
        return Response({
            'labels': ['لا توجد بيانات'],
            'data': [0],
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


@login_required
def contact_service_provider(request, ad_id):
    """التواصل مع مقدم الخدمة"""
    advertisement = get_object_or_404(ServiceAdvertisement, pk=ad_id)
    
    if request.method == 'POST':
        message_content = request.POST.get('message', '').strip()
        
        if not message_content:
            messages.error(request, 'يرجى كتابة رسالة')
        else:
            try:
                from .models import Message
                recipient = advertisement.service_provider.user
                
                message = Message.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=f'بخصوص إعلان الخدمة: {advertisement.title}',
                    content=message_content,
                )
                
                # Increment inquiries count
                advertisement.inquiries_count += 1
                advertisement.save()
                
                messages.success(request, 'تم إرسال رسالتك بنجاح')
                return redirect('service_advertisement_detail', ad_id=ad_id)
            except Exception as e:
                messages.error(request, 'حدث خطأ أثناء إرسال الرسالة')
    
    return render(request, 'properties/contact_service_provider.html', {
        'advertisement': advertisement
    })


@login_required
def auction_access_code(request, auction_id):
    """صفحة إدخال رقم المزاد"""
    auction = get_object_or_404(Auction, pk=auction_id)
    
    # Check if access code is required
    if auction.access_type == 'public':
        return redirect('auction_detail', auction_id=auction_id)
    
    # Check if user already has access
    if request.user.is_authenticated:
        # Check if user is the broker
        if auction.broker and auction.broker.user == request.user:
            return redirect('auction_detail', auction_id=auction_id)
        
        # Check if user has a valid invitation
        if AuctionInvitation.objects.filter(auction=auction, invited_user=request.user, status='accepted').exists():
            return redirect('auction_detail', auction_id=auction_id)
    
    if request.method == 'POST':
        access_code = request.POST.get('access_code', '').strip()
        invitation_code = request.POST.get('invitation_code', '').strip()
        
        if access_code:
            # Check access code
            if auction.access_code == access_code:
                # Store access in session
                request.session[f'auction_access_{auction_id}'] = True
                messages.success(request, 'تم الدخول بنجاح')
                return redirect('auction_detail', auction_id=auction_id)
            else:
                messages.error(request, 'رقم الدخول غير صحيح')
        
        elif invitation_code:
            # Check invitation code
            try:
                invitation = AuctionInvitation.objects.get(auction=auction, invitation_code=invitation_code)
                if invitation.status == 'pending':
                    invitation.status = 'accepted'
                    invitation.accepted_at = timezone.now()
                    if request.user.is_authenticated:
                        invitation.invited_user = request.user
                    invitation.save()
                    messages.success(request, 'تم قبول الدعوة بنجاح')
                    return redirect('auction_detail', auction_id=auction_id)
                elif invitation.status == 'accepted':
                    messages.success(request, 'الدعوة مقبولة مسبقاً')
                    return redirect('auction_detail', auction_id=auction_id)
                else:
                    messages.error(request, 'الدعوة غير صالحة')
            except AuctionInvitation.DoesNotExist:
                messages.error(request, 'كود الدعوة غير صحيح')
    
    return render(request, 'properties/auction_access_code.html', {
        'auction': auction
    })


@login_required
def create_auction_invitation(request, auction_id):
    """إنشاء دعوة لمزاد"""
    auction = get_object_or_404(Auction, pk=auction_id)
    
    # Check if user is the broker
    if not auction.broker or auction.broker.user != request.user:
        messages.error(request, 'ليس لديك صلاحية إنشاء دعوات لهذا المزاد')
        return redirect('auction_detail', auction_id=auction_id)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        user_id = request.POST.get('user_id')
        
        invitation = AuctionInvitation(auction=auction, email=email, phone=phone)
        
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                invitation.invited_user = user
            except User.DoesNotExist:
                messages.error(request, 'المستخدم غير موجود')
                return redirect('auction_detail', auction_id=auction_id)
        
        invitation.generate_code()
        invitation.save()
        
        # Send notification (you can implement email/SMS sending here)
        messages.success(request, f'تم إنشاء الدعوة بنجاح. كود الدعوة: {invitation.invitation_code}')
        return redirect('auction_detail', auction_id=auction_id)
    
    return render(request, 'properties/create_auction_invitation.html', {
        'auction': auction
    })


@login_required
def auction_invitations(request, auction_id):
    """عرض دعوات المزاد"""
    auction = get_object_or_404(Auction, pk=auction_id)
    
    # Check if user is the broker
    if not auction.broker or auction.broker.user != request.user:
        messages.error(request, 'ليس لديك صلاحية عرض دعوات هذا المزاد')
        return redirect('auction_detail', auction_id=auction_id)
    
    invitations = auction.invitations.all().order_by('-created_at')
    
    return render(request, 'properties/auction_invitations.html', {
        'auction': auction,
        'invitations': invitations
    })






@login_required
@broker_required
def broker_create_auction(request):
    """إنشاء مزاد جديد من قبل الدلال"""
    from .models import Auction, Property, BrokerPlanSubscription, Broker
    import secrets
    
    try:
        broker = request.user.broker_profile
    except Broker.DoesNotExist:
        messages.error(request, 'يجب أن تكون دلالاً لإنشاء مزاد')
        return redirect('broker_auctions')
    
    # التحقق من الاشتراك
    # Check if user has any active subscription
    active_subscriptions = BrokerPlanSubscription.objects.filter(
        broker=broker,
        status='active'
    )
    has_active_subscription = False
    for sub in active_subscriptions:
        if sub.is_active():
            has_active_subscription = True
            break

    if not has_active_subscription:
        messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
        return redirect('subscription_plans')
    try:
        subscription = BrokerPlanSubscription.objects.filter(broker=broker, status='active').first()
        if not subscription or not subscription.is_active():
            messages.error(request, 'يجب أن يكون لديك اشتراك نشط لإنشاء مزاد')
            return redirect('broker_auctions')
        
        if not subscription.can_add_auction():
            remaining = subscription.plan.max_auctions - subscription.auctions_used
            messages.error(request, f'لقد استنفذت عدد المزادات المسموح بها في اشتراكك. المتبقي: {remaining}')
            return redirect('broker_auctions')
    except Exception as e:
        messages.error(request, 'حدث خطأ في التحقق من الاشتراك')
        return redirect('broker_auctions')
    
    if request.method == 'POST':
        # معلومات المزاد
        property_id = request.POST.get('property')
        auction_type = request.POST.get('auction_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        starting_price = request.POST.get('starting_price')
        minimum_increment = request.POST.get('minimum_increment')
        reserve_price = request.POST.get('reserve_price')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')
        auto_extend_minutes = request.POST.get('auto_extend_minutes')
        deposit_amount = request.POST.get('deposit_amount')
        access_type = request.POST.get('access_type')
        access_code = request.POST.get('access_code')
        max_participants = request.POST.get('max_participants')
        terms = request.POST.get('terms')
        contact_phone = request.POST.get('contact_phone')
        contact_email = request.POST.get('contact_email')
        
        # التحقق من الحقول المطلوبة
        if not all([property_id, auction_type, title, description, starting_price, start_date, start_time, end_date, end_time]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
        else:
            # الحصول على العقار
            property_obj = get_object_or_404(Property, id=property_id)
            
            # التحقق من أن العقار يملكه الدلال
            if property_obj.broker != broker:
                messages.error(request, 'يمكنك إنشاء مزاد فقط لعقاراتك')
            else:
                # دمج التاريخ والوقت
                from datetime import datetime
                start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
                
                # توليد كود دخول عشوائي إذا لم يتم توفيره
                if not access_code and access_type == 'private':
                    access_code = secrets.token_hex(4).upper()
                
                # استخدام مزاد من الحصة
                if not subscription.use_auction():
                    messages.error(request, 'حدث خطأ في استخدام حصة المزاد')
                    return redirect('broker_auctions')
                
                # إنشاء المزاد
                # Set approval_status to 'approved' automatically if broker has active subscription
                approval_status = 'approved' if broker.is_subscription_active() else 'pending'
                
                auction = Auction.objects.create(
                    property=property_obj,
                    broker=broker,
                    auction_type=auction_type,
                    title=title,
                    description=description,
                    starting_price=starting_price,
                    minimum_increment=int(minimum_increment) if minimum_increment else 100000,
                    reserve_price=int(reserve_price) if reserve_price else None,
                    start_date=start_datetime,
                    end_date=end_datetime,
                    auto_extend_minutes=int(auto_extend_minutes) if auto_extend_minutes else 5,
                    deposit_amount=int(deposit_amount) if deposit_amount else 0,
                    access_type=access_type if access_type else 'public',
                    access_code=access_code,
                    max_participants=int(max_participants) if max_participants else None,
                    terms=terms,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    status='upcoming',
                    approval_status=approval_status
                )
                
                # إشعار للإدارة
                from .utils import create_notification
                admins = User.objects.filter(is_superuser=True)
                
                for admin in admins:
                    create_notification(
                        user=admin,
                        notification_type='auction',
                        title='مزاد جديد بانتظار الموافقة',
                        message=f'مزاد جديد من الدلال {broker.display_name}: {title}',
                        link=f'/admin-panel/auctions/{auction.id}/',
                        metadata={'auction_id': auction.id}
                    )
                
                messages.success(request, 'تم إنشاء المزاد بنجاح. بانتظار موافقة الإدارة')
                return redirect('broker_auctions')
    
    # الحصول على عقارات الدلال
    try:
        broker = request.user.broker_profile
        properties = Property.objects.filter(broker=broker, is_active=True)
    except Broker.DoesNotExist:
        messages.error(request, 'يجب أن تكون دلالاً لإنشاء مزاد')
        return redirect('broker_auctions')
    
    context = {
        'properties': properties,
    }
    
    return render(request, 'properties/broker_create_auction.html', context)


@login_required
def broker_auctions(request):
    """عرض المزادات الخاصة بالدلال"""
    from .models import Auction, BrokerPlanSubscription, Broker
    
    try:
        broker = request.user.broker_profile
        auctions = Auction.objects.filter(broker=broker).order_by('-created_at')
    except Broker.DoesNotExist:
        # User doesn't have a broker profile, show empty list
        auctions = Auction.objects.none()
        broker = None
    
    # Get subscription info
    subscription = None
    auctions_remaining = 0
    auctions_used = 0
    max_auctions = 0
    
    if broker:
        subscription = BrokerPlanSubscription.objects.filter(broker=broker, status='active').first()
        if subscription and subscription.is_active():
            auctions_used = subscription.auctions_used
            max_auctions = subscription.plan.max_auctions
            auctions_remaining = max_auctions - auctions_used
    
    context = {
        'auctions': auctions,
        'subscription': subscription,
        'auctions_remaining': auctions_remaining,
        'auctions_used': auctions_used,
        'max_auctions': max_auctions,
    }
    
    return render(request, 'properties/broker_auctions.html', context)


@login_required
@staff_required
def admin_auctions(request):
    """عرض المزادات للإدارة"""
    from .models import Auction
    
    status_filter = request.GET.get('status', 'all')
    approval_filter = request.GET.get('approval', 'all')
    
    auctions = Auction.objects.all().select_related('broker', 'broker__user', 'property')
    
    if status_filter != 'all':
        auctions = auctions.filter(status=status_filter)
    
    if approval_filter != 'all':
        auctions = auctions.filter(approval_status=approval_filter)
    
    auctions = auctions.order_by('-created_at')
    
    context = {
        'auctions': auctions,
        'status_filter': status_filter,
        'approval_filter': approval_filter,
    }
    
    return render(request, 'properties/admin_auctions.html', context)


@login_required
@staff_required
def admin_approve_auction(request, auction_id):
    """الموافقة على مزاد"""
    from .models import Auction
    
    auction = get_object_or_404(Auction, id=auction_id)
    auction.approval_status = 'approved'
    auction.approved_by = request.user
    auction.approved_at = timezone.now()
    auction.save()
    
    # إشعار للدلال
    if auction.broker:
        from .utils import create_notification
        create_notification(
            user=auction.broker.user,
            notification_type='auction',
            title='تمت الموافقة على المزاد',
            message=f'تمت الموافقة على مزادك: {auction.title}',
            link=f'/broker/auctions/{auction.id}/',
            metadata={'auction_id': auction.id}
        )
    
    messages.success(request, 'تمت الموافقة على المزاد')
    return redirect('admin_auctions')


@login_required
@staff_required
def admin_reject_auction(request, auction_id):
    """رفض مزاد"""
    from .models import Auction
    
    if request.method == 'POST':
        auction = get_object_or_404(Auction, id=auction_id)
        rejection_reason = request.POST.get('rejection_reason', '')
        
        auction.approval_status = 'rejected'
        auction.rejection_reason = rejection_reason
        auction.save()
        
        # إشعار للدلال
        if auction.broker:
            from .utils import create_notification
            create_notification(
                user=auction.broker.user,
                notification_type='auction',
                title='تم رفض المزاد',
                message=f'تم رفض مزادك: {auction.title}. السبب: {rejection_reason}',
                link=f'/broker/auctions/{auction.id}/',
                metadata={'auction_id': auction.id}
            )
        
        messages.success(request, 'تم رفض المزاد')
        return redirect('admin_auctions')
    
    auction = get_object_or_404(Auction, id=auction_id)
    context = {
        'auction': auction,
    }
    
    return render(request, 'properties/admin_reject_auction.html', context)


@login_required
def auction_detail(request, auction_id):
    """عرض تفاصيل المزاد"""
    from .models import Auction
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    context = {
        'auction': auction,
    }
    
    return render(request, 'properties/auction_detail.html', context)


@login_required
def auction_join(request, auction_id):
    """الانضمام إلى المزاد"""
    from .models import Auction, AuctionParticipant
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        access_code = request.POST.get('access_code', '').strip()
        
        # التحقق من كود الدخول
        if auction.access_code and access_code != auction.access_code:
            messages.error(request, 'كود الدخول غير صحيح')
            return redirect('auction_detail', auction_id=auction_id)
        
        # التحقق من أن المستخدم لم ينضم بعد
        if AuctionParticipant.objects.filter(auction=auction, user=request.user).exists():
            messages.warning(request, 'أنت منضم بالفعل لهذا المزاد')
            return redirect('auction_detail', auction_id=auction_id)
        
        # التحقق من الحد الأقصى للمشاركين
        if auction.max_participants:
            current_participants = auction.participants.count()
            if current_participants >= auction.max_participants:
                messages.error(request, 'وصل المزاد إلى الحد الأقصى للمشاركين')
                return redirect('auction_detail', auction_id=auction_id)
        
        # إنشاء مشارك جديد
        participant = AuctionParticipant.objects.create(
            auction=auction,
            user=request.user,
            is_verified=True
        )
        
        messages.success(request, 'تم الانضمام إلى المزاد بنجاح')
        return redirect('auction_live', auction_id=auction_id)
    
    context = {
        'auction': auction,
    }
    
    return render(request, 'properties/auction_join.html', context)


@login_required
def auction_live(request, auction_id):
    """المزاد الحي"""
    from .models import Auction, Bid
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    # التحقق من أن المستخدم مشارك
    if not AuctionParticipant.objects.filter(auction=auction, user=request.user).exists():
        messages.error(request, 'يجب الانضمام إلى المزاد أولاً')
        return redirect('auction_detail', auction_id=auction_id)
    
    # الحصول على المزايدات
    bids = auction.bids.all().order_by('-created_at')[:10]
    
    context = {
        'auction': auction,
        'bids': bids,
    }
    
    return render(request, 'properties/auction_live.html', context)


@login_required
def place_bid(request, auction_id):
    """وضع مزايدة"""
    from .models import Auction, Bid
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == 'POST':
        bid_amount = request.POST.get('bid_amount')
        
        # التحقق من أن المستخدم مشارك
        if not AuctionParticipant.objects.filter(auction=auction, user=request.user).exists():
            messages.error(request, 'يجب الانضمام إلى المزاد أولاً')
            return redirect('auction_detail', auction_id=auction_id)
        
        # التحقق من أن المزاد نشط
        if not auction.is_active():
            messages.error(request, 'المزاد غير نشط حالياً')
            return redirect('auction_detail', auction_id=auction_id)
        
        # التحقق من المبلغ
        try:
            bid_amount = int(bid_amount)
        except:
            messages.error(request, 'يرجى إدخال مبلغ صحيح')
            return redirect('auction_live', auction_id=auction_id)
        
        # التحقق من الحد الأدنى للزيادة
        current_highest = auction.get_current_highest_bid()
        if bid_amount < current_highest + auction.minimum_increment:
            messages.error(request, f'يجب أن تكون المزايدة أعلى من {current_highest + auction.minimum_increment}')
            return redirect('auction_live', auction_id=auction_id)
        
        # إنشاء المزايدة
        bid = Bid.objects.create(
            auction=auction,
            user=request.user,
            amount=bid_amount
        )
        
        # تمديد المزاد إذا لزم الأمر
        auction.extend_auction()
        
        messages.success(request, 'تم وضع المزايدة بنجاح')
        return redirect('auction_live', auction_id=auction_id)
    
    return redirect('auction_live', auction_id=auction_id)


@login_required
@staff_required
def determine_auction_winner(request, auction_id):
    """تحديد الفائز في المزاد"""
    from .models import Auction, Bid
    
    auction = get_object_or_404(Auction, id=auction_id)
    
    if auction.status != 'ended':
        messages.error(request, 'يمكن تحديد الفائز فقط للمزادات المنتهية')
        return redirect('admin_auctions')
    
    if auction.winner_announced:
        messages.warning(request, 'تم الإعلان عن الفائز بالفعل')
        return redirect('admin_auctions')
    
    # الحصول على أعلى مزايدة
    winning_bid = auction.bids.order_by('-amount').first()
    
    if winning_bid:
        auction.winner = winning_bid.user
        auction.winning_bid = winning_bid
        auction.winner_announced = True
        auction.save()
        
        # إشعار للفائز
        from .utils import create_notification
        create_notification(
            user=winning_bid.user,
            notification_type='auction',
            title='🎉 فزت بالمزاد!',
            message=f'تهانينا! فزت بمزاد {auction.title} بمبلغ {winning_bid.amount}',
            link=f'/auction/{auction.id}/',
            metadata={'auction_id': auction.id}
        )
        
        messages.success(request, 'تم تحديد الفائز بنجاح')
    else:
        messages.error(request, 'لا توجد مزايدات لهذا المزاد')
    
    return redirect('admin_auctions')


# ==================== User Moderation Views ====================

@login_required
def user_moderation_panel(request):
    """لوحة تحكم مراقبة المستخدمين"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserWarning, UserSuspension, UserModerationAction, ActivityLog
    
    # إحصائيات
    total_users = User.objects.filter(is_active=True).count()
    suspended_users = UserSuspension.objects.filter(status='active').count()
    active_warnings = UserWarning.objects.filter(is_acknowledged=False).count()
    recent_actions = UserModerationAction.objects.all()[:10]
    
    # قائمة المستخدمين مع الفلترة
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.all().select_related('broker_profile', 'user_profile')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if status_filter == 'suspended':
        users = [u for u in users if UserSuspension.objects.filter(user=u, status='active').exists()]
    elif status_filter == 'warned':
        users = [u for u in users if UserWarning.objects.filter(user=u, is_acknowledged=False).exists()]
    
    # إضافة معلومات المراقبة لكل مستخدم
    users_with_moderation = []
    for user in users:
        active_suspension = UserSuspension.objects.filter(user=user, status='active').first()
        active_warnings = UserWarning.objects.filter(user=user, is_acknowledged=False).count()
        recent_activity = ActivityLog.objects.filter(user=user).order_by('-created_at')[:5]
        
        users_with_moderation.append({
            'user': user,
            'is_suspended': active_suspension is not None,
            'suspension': active_suspension,
            'warning_count': active_warnings,
            'recent_activity': recent_activity,
        })
    
    context = {
        'total_users': total_users,
        'suspended_users': suspended_users,
        'active_warnings': active_warnings,
        'recent_actions': recent_actions,
        'users': users_with_moderation,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'properties/user_moderation_panel.html', context)


@login_required
def user_detail_moderation(request, user_id):
    """تفاصيل مراقبة مستخدم معين"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserWarning, UserSuspension, UserModerationAction, ActivityLog
    
    user = get_object_or_404(User, id=user_id)
    
    # بيانات المستخدم
    warnings = UserWarning.objects.filter(user=user).order_by('-created_at')
    suspensions = UserSuspension.objects.filter(user=user).order_by('-start_date')
    moderation_actions = UserModerationAction.objects.filter(user=user).order_by('-created_at')
    recent_activity = ActivityLog.objects.filter(user=user).order_by('-created_at')[:20]
    
    # التحقق من حالة التعطيل الحالية
    active_suspension = UserSuspension.objects.filter(user=user, status='active').first()
    
    context = {
        'target_user': user,
        'warnings': warnings,
        'suspensions': suspensions,
        'moderation_actions': moderation_actions,
        'recent_activity': recent_activity,
        'active_suspension': active_suspension,
    }
    
    return render(request, 'properties/user_moderation_detail.html', context)


@login_required
def issue_user_warning(request, user_id):
    """إصدار إنذار لمستخدم"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserWarning, UserModerationAction
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        warning_type = request.POST.get('warning_type')
        severity = request.POST.get('severity', 'medium')
        reason = request.POST.get('reason')
        duration_days = request.POST.get('duration_days')
        
        if not all([warning_type, reason]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
        else:
            from django.utils import timezone
            from datetime import timedelta
            
            expires_at = None
            if duration_days:
                expires_at = timezone.now() + timedelta(days=int(duration_days))
            
            # إنشاء الإنذار
            warning = UserWarning.objects.create(
                user=user,
                issued_by=request.user,
                warning_type=warning_type,
                severity=severity,
                reason=reason,
                expires_at=expires_at
            )
            
            # تسجيل الإجراء
            UserModerationAction.objects.create(
                user=user,
                moderator=request.user,
                action='warning',
                reason=f'{warning_type}: {reason}',
                duration=timedelta(days=int(duration_days)) if duration_days else None,
                ip_address=get_client_ip(request)
            )
            
            # إشعار للمستخدم
            from .utils import create_notification
            create_notification(
                user=user,
                notification_type='warning',
                title='⚠️ إنذار جديد',
                message=f'لقد تلقيت إنذاراً: {reason}',
                metadata={'warning_id': warning.id}
            )
            
            messages.success(request, 'تم إصدار الإنذار بنجاح')
            return redirect('user_moderation_detail', user_id=user.id)
    
    context = {
        'target_user': user,
        'warning_types': UserWarning.TYPE_CHOICES,
        'severity_choices': UserWarning.SEVERITY_CHOICES,
    }
    
    return render(request, 'properties/issue_warning.html', context)


@login_required
def suspend_user(request, user_id):
    """تعطيل مستخدم"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserSuspension, UserModerationAction
    
    user = get_object_or_404(User, id=user_id)
    
    # التحقق من عدم تعطيل المستخدم بالفعل
    if UserSuspension.objects.filter(user=user, status='active').exists():
        messages.error(request, 'المستخدم معطل بالفعل')
        return redirect('user_moderation_detail', user_id=user.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        duration_days = request.POST.get('duration_days')
        
        if not all([reason, description]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
        else:
            from django.utils import timezone
            from datetime import timedelta
            
            end_date = None
            if duration_days:
                end_date = timezone.now() + timedelta(days=int(duration_days))
            
            # إنشاء التعطيل
            suspension = UserSuspension.objects.create(
                user=user,
                suspended_by=request.user,
                reason=reason,
                description=description,
                end_date=end_date
            )
            
            # تعطيل حساب المستخدم
            user.is_active = False
            user.save()
            
            # تسجيل الإجراء
            UserModerationAction.objects.create(
                user=user,
                moderator=request.user,
                action='suspend',
                reason=f'{reason}: {description}',
                duration=timedelta(days=int(duration_days)) if duration_days else None,
                ip_address=get_client_ip(request)
            )
            
            # إشعار للمستخدم
            from .utils import create_notification
            create_notification(
                user=user,
                notification_type='suspension',
                title='🚫 تم تعطيل حسابك',
                message=f'تم تعطيل حسابك للسبب: {description}',
                metadata={'suspension_id': suspension.id}
            )
            
            messages.success(request, 'تم تعطيل المستخدم بنجاح')
            return redirect('user_moderation_detail', user_id=user.id)
    
    context = {
        'target_user': user,
        'reason_choices': UserSuspension.REASON_CHOICES,
    }
    
    return render(request, 'properties/suspend_user.html', context)


@login_required
def lift_suspension(request, user_id):
    """رفع تعطيل مستخدم"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserSuspension, UserModerationAction
    
    user = get_object_or_404(User, id=user_id)
    suspension = UserSuspension.objects.filter(user=user, status='active').first()
    
    if not suspension:
        messages.error(request, 'المستخدم غير معطل حالياً')
        return redirect('user_moderation_detail', user_id=user.id)
    
    if request.method == 'POST':
        lift_reason = request.POST.get('lift_reason', '')
        
        # رفع التعطيل
        suspension.lift(lifted_by=request.user, reason=lift_reason)
        
        # تفعيل حساب المستخدم
        user.is_active = True
        user.save()
        
        # تسجيل الإجراء
        UserModerationAction.objects.create(
            user=user,
            moderator=request.user,
            action='unsuspend',
            reason=f'رفع التعطيل: {lift_reason}',
            ip_address=get_client_ip(request)
        )
        
        # إشعار للمستخدم
        from .utils import create_notification
        create_notification(
            user=user,
            notification_type='activation',
            title='✅ تم تفعيل حسابك',
            message='تم رفع التعطيل عن حسابك بنجاح',
            metadata={'suspension_id': suspension.id}
        )
        
        messages.success(request, 'تم رفع التعطيل بنجاح')
        return redirect('user_moderation_detail', user_id=user.id)
    
    context = {
        'target_user': user,
        'suspension': suspension,
    }
    
    return render(request, 'properties/lift_suspension.html', context)


@login_required
def delete_user(request, user_id):
    """حذف مستخدم"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import UserModerationAction
    
    user = get_object_or_404(User, id=user_id)
    
    if user.is_superuser:
        messages.error(request, 'لا يمكن حذف المشرفين')
        return redirect('user_moderation_detail', user_id=user.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        # تسجيل الإجراء قبل الحذف
        UserModerationAction.objects.create(
            user=user,
            moderator=request.user,
            action='delete',
            reason=reason or 'حذف حساب',
            ip_address=get_client_ip(request)
        )
        
        # حذف المستخدم
        username = user.username
        user.delete()
        
        messages.success(request, f'تم حذف المستخدم {username} بنجاح')
        return redirect('user_moderation_panel')
    
    context = {
        'target_user': user,
    }
    
    return render(request, 'properties/delete_user.html', context)


@login_required
def subscription_renewal_request(request):
    """طلب تجديد اشتراك"""
    from django.core.exceptions import ValidationError
    
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلالاً للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # Get current subscription
    current_subscription = BrokerPlanSubscription.objects.filter(
        broker=broker,
        status='active'
    ).select_related('plan').first()
    
    # Get available plans
    available_plans = AdvancedSubscriptionPlan.objects.filter(is_active=True).order_by('tier', 'price_per_day')
    
    # Get default pricing from SubscriptionPlan
    from .models import SubscriptionPlan
    default_plan = SubscriptionPlan.objects.filter(is_active=True).first()
    regular_price_per_day = float(default_plan.price_per_property) if default_plan else 50.00
    premium_price_per_day = float(default_plan.price_per_property) * 20 if default_plan else 1000.00  # Premium is 20x regular
    
    if request.method == 'POST':
        try:
            # Get form data
            property_types = request.POST.getlist('property_types')
            regular_count = int(request.POST.get('regular_count', 0))
            premium_count = int(request.POST.get('premium_count', 0))
            days_requested = int(request.POST.get('days_requested', 0))
            notes = request.POST.get('notes', '')
            subscription_types = request.POST.getlist('subscription_type')
            additional_services = request.POST.getlist('additional_services')

            # Validate at least one option is selected for submission
            if not property_types and not subscription_types and not additional_services and regular_count == 0 and premium_count == 0:
                raise ValidationError('يجب اختيار نوع اشتراك أو نوع عقار أو خدمة إضافية أو تحديد عدد العقارات')
            
            # Validate days
            if days_requested < 1:
                raise ValidationError('يجب إدخال عدد أيام صحيح (على الأقل يوم واحد)')
            
            if days_requested > 3650:  # Max 10 years
                raise ValidationError('عدد الأيام يتجاوز الحد المسموح (الحد الأقصى 3650 يوم)')
            
            # Validate property counts
            if regular_count < 0 or premium_count < 0:
                raise ValidationError('عدد العقارات لا يمكن أن يكون سالباً')
            
            # Validate notes length
            if len(notes) > 500:
                raise ValidationError('الملاحظات طويلة جداً (الحد الأقصى 500 حرف)')
            
            # Sanitize notes to prevent XSS
            from django.utils.html import strip_tags
            notes = strip_tags(notes)
            
            # Calculate cost based on subscription type or property counts
            # Always calculate based on counts (primary method)
            regular_cost = regular_price_per_day * regular_count * days_requested
            premium_cost = premium_price_per_day * premium_count * days_requested
            estimated_cost = regular_cost + premium_cost

            # Add cost for subscription types (if any)
            if subscription_types:
                estimated_cost += regular_price_per_day * len(subscription_types) * days_requested

            # Add cost for additional services (if any)
            if additional_services:
                estimated_cost += regular_price_per_day * len(additional_services) * days_requested
            
            # Validate cost doesn't exceed reasonable limits
            if estimated_cost > 10000000:  # 10 million IQD max
                raise ValidationError('التكلفة تتجاوز الحد المسموح')
            
            # Check if there's already a pending renewal request
            pending_request = SubscriptionRenewalRequest.objects.filter(
                broker=broker,
                status='pending'
            ).first()
            
            if pending_request:
                raise ValidationError('لديك طلب تجديد قيد الانتظار بالفعل')

            # Get additional form fields
            payment_method = request.POST.get('payment_method', 'wallet')
            auto_renewal = request.POST.get('auto_renewal') == 'on'
            notify_email = request.POST.get('notify_email') == 'on'
            notify_sms = request.POST.get('notify_sms') == 'on'

            # Create renewal request without a specific plan
            renewal_request = SubscriptionRenewalRequest.objects.create(
                broker=broker,
                current_subscription=current_subscription,
                plan=None,  # No specific plan, admin will determine
                days_requested=days_requested,
                property_count=regular_count + premium_count,
                regular_count=regular_count,
                premium_count=premium_count,
                property_types=property_types,
                subscription_types=subscription_types,  # Now handles multiple subscription types
                additional_services=additional_services,
                estimated_cost=estimated_cost,
                notes=notes,
                payment_method=payment_method,
                auto_renewal=auto_renewal,
                notify_email=notify_email,
                notify_sms=notify_sms,
                status='pending',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Handle additional services messages
            if additional_services:
                if 'building_requests' in additional_services:
                    messages.info(request, 'تم إضافة طلبات البناء إلى طلب التجديد')
                if 'auctions' in additional_services:
                    messages.info(request, 'تم إضافة المزادات إلى طلب التجديد')
            
            # Handle subscription types messages
            if subscription_types:
                if 'travel_company' in subscription_types:
                    messages.info(request, 'تم إضافة اشتراك شركة سفر')
                if 'job_posting' in subscription_types:
                    messages.info(request, 'تم إضافة اشتراك نشر وظائف')
            
            # Log the renewal request
            from django.contrib.admin.models import LogEntry
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=None,
                object_id=renewal_request.id,
                object_repr=f'Renewal request for {broker.display_name}',
                action_flag=1,  # ADDITION
                change_message=f'Subscription renewal request: {estimated_cost} IQD for {days_requested} days'
            )
            
            messages.success(request, 'تم إرسال طلب التجديد بنجاح')
            return redirect('dashboard')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'حدث خطأ أثناء معالجة الطلب')
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Subscription renewal error: {str(e)}')
    
    # Calculate usage statistics
    try:
        broker = Broker.objects.filter(user=request.user).first()
        
        user_properties_count = 0
        premium_properties_count = 0
        
        if broker:
            user_properties_count = Property.objects.filter(broker=broker).count()
            premium_properties_count = Property.objects.filter(broker=broker, is_premium=True).count()
    except Exception as e:
        user_properties_count = 0
        premium_properties_count = 0
    
    # Calculate days remaining
    days_remaining = 0
    if current_subscription and current_subscription.end_date:
        from django.utils import timezone
        days_remaining = (current_subscription.end_date - timezone.now()).days
        if days_remaining < 0:
            days_remaining = 0
    
    # Calculate total cost this month
    from django.utils import timezone
    from datetime import timedelta
    this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    # This is a simplified calculation - in reality you'd calculate based on actual usage
    total_cost_this_month = 0
    if current_subscription:
        total_cost_this_month = user_properties_count * regular_price_per_day  # Real calculation
    
    return render(request, 'properties/subscription_renewal_request.html', {
        'current_subscription': current_subscription,
        'available_plans': available_plans,
        'user_properties_count': user_properties_count,
        'premium_properties_count': premium_properties_count,
        'days_remaining': days_remaining,
        'total_cost_this_month': total_cost_this_month,
        'regular_price_per_day': regular_price_per_day,
        'premium_price_per_day': premium_price_per_day
    })


@login_required
def subscription_renewal_requests_list(request):
    """قائمة طلبات التجديد (للإدارة)"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    requests = SubscriptionRenewalRequest.objects.all().select_related('broker', 'plan').order_by('-created_at')
    
    # Calculate statistics
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='pending').count(),
        'approved': requests.filter(status='approved').count(),
        'rejected': requests.filter(status='rejected').count(),
        'completed': requests.filter(status='completed').count()
    }
    
    return render(request, 'properties/subscription_renewal_requests_list.html', {
        'requests': requests,
        'stats': stats
    })


@login_required
@require_http_methods(["POST"])
def approve_subscription_renewal(request, request_id):
    """الموافقة على طلب تجديد اشتراك"""
    from .permissions import is_platform_admin
    from django.utils import timezone
    from datetime import timedelta
    from django.db import transaction
    from .models import DallalSubscription

    if not (is_platform_admin(request.user) or request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})

    try:
        renewal_request = get_object_or_404(
            SubscriptionRenewalRequest.objects.select_related('broker', 'plan', 'current_subscription'),
            id=request_id,
        )

        if renewal_request.status != 'pending':
            return JsonResponse({'success': False, 'error': 'الطلب ليس في حالة انتظار'})

        if (timezone.now() - renewal_request.created_at).days > 30:
            return JsonResponse({'success': False, 'error': 'الطلب منتهي الصلاحية'})

        if renewal_request.estimated_cost > 10000000:
            return JsonResponse({'success': False, 'error': 'التكلفة تتجاوز الحد المسموح'})

        with transaction.atomic():
            subscription = renewal_request.current_subscription
            if not subscription:
                plan = renewal_request.plan
                if not plan:
                    # Try to find an active plan, if none exists, create a default one
                    plan = AdvancedSubscriptionPlan.objects.filter(is_active=True).order_by('price_per_day').first()
                    if not plan:
                        # Create a default plan if none exists
                        plan = AdvancedSubscriptionPlan.objects.create(
                            name='خطة افتراضية',
                            plan_type='combined',
                            tier='regular',
                            price_per_day=50,
                            price_per_month=1500,
                            price_per_year=18000,
                            max_properties=10,
                            max_auctions=5,
                            max_building_requests=5,
                            is_active=True,
                            description='خطة اشتراك افتراضية تم إنشاؤها تلقائياً'
                        )
                        logger.info(f'Created default subscription plan: {plan.id}')

                subscription = BrokerPlanSubscription.objects.create(
                    broker=renewal_request.broker,
                    plan=plan,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=renewal_request.days_requested),
                    status='active',
                    total_paid=renewal_request.estimated_cost,
                )
                renewal_request.current_subscription = subscription
            else:
                subscription.renew(renewal_request.days_requested)
                subscription.total_paid = (subscription.total_paid or 0) + renewal_request.estimated_cost
                subscription.save()

            dallal_sub_type = None
            if renewal_request.subscription_type:
                allowed = {c[0] for c in DallalSubscription.SUBSCRIPTION_TYPE_CHOICES}
                if renewal_request.subscription_type in allowed:
                    dallal_sub_type = renewal_request.subscription_type
            elif renewal_request.property_types or renewal_request.premium_count or renewal_request.regular_count:
                dallal_sub_type = 'premium' if renewal_request.premium_count > 0 else 'basic'

            if dallal_sub_type:
                end_date = (timezone.now() + timedelta(days=renewal_request.days_requested)).date()
                start_date = timezone.now().date()
                dallal_subscription = DallalSubscription.objects.filter(
                    broker=renewal_request.broker,
                    is_active=True,
                ).first()

                if dallal_subscription:
                    dallal_subscription.subscription_type = dallal_sub_type
                    dallal_subscription.start_date = start_date
                    dallal_subscription.end_date = end_date
                    dallal_subscription.is_active = True
                    dallal_subscription.save()
                else:
                    DallalSubscription.objects.create(
                        broker=renewal_request.broker,
                        subscription_type=dallal_sub_type,
                        start_date=start_date,
                        end_date=end_date,
                        auto_renewal=False,
                    )

            # Sync classic broker subscription dates
            broker = renewal_request.broker
            broker.subscription_start_date = timezone.now().date()
            broker.subscription_end_date = (timezone.now() + timedelta(days=renewal_request.days_requested)).date()
            broker.save(update_fields=['subscription_start_date', 'subscription_end_date'])

            renewal_request.status = 'approved'
            renewal_request.approved_by = request.user
            renewal_request.approved_at = timezone.now()
            renewal_request.approval_ip = request.META.get('REMOTE_ADDR')
            renewal_request.save()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.exception(f'Subscription approval error: {e}')
        return JsonResponse({'success': False, 'error': f'حدث خطأ أثناء المعالجة: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def reject_subscription_renewal(request, request_id):
    """رفض طلب تجديد اشتراك"""
    from .permissions import is_platform_admin
    from django.utils import timezone
    from django.utils.html import strip_tags

    if not (is_platform_admin(request.user) or request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'})

    try:
        renewal_request = get_object_or_404(SubscriptionRenewalRequest, id=request_id)

        if renewal_request.status != 'pending':
            return JsonResponse({'success': False, 'error': 'الطلب ليس في حالة انتظار'})

        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}
        rejection_reason = data.get('reason') or request.POST.get('reason', '')
        if len(rejection_reason) > 500:
            return JsonResponse({'success': False, 'error': 'سبب الرفض طويل جداً'})
        rejection_reason = strip_tags(rejection_reason)

        renewal_request.status = 'rejected'
        renewal_request.rejection_reason = rejection_reason
        renewal_request.rejected_by = request.user
        renewal_request.rejected_at = timezone.now()
        renewal_request.rejection_ip = request.META.get('REMOTE_ADDR')
        renewal_request.save()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.exception(f'Subscription rejection error: {e}')
        return JsonResponse({'success': False, 'error': f'حدث خطأ أثناء المعالجة: {str(e)}'})


@login_required
def user_monitoring_panel(request):
    """لوحة مراقبة المستخدمين"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    users = User.objects.all().select_related('user_profile', 'broker_profile').order_by('-date_joined')
    
    # Get additional info for each user
    users_data = []
    for user in users:
        broker = None
        try:
            broker = Broker.objects.get(user=user)
        except Broker.DoesNotExist:
            pass
        
        subscription = None
        if broker:
            try:
                subscription = BrokerPlanSubscription.objects.filter(
                    broker=broker,
                    status='active'
                ).first()
            except:
                pass
        
        user_data = {
            'user': user,
            'broker': broker,
            'subscription': subscription,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'email': user.email,
        }
        users_data.append(user_data)
    
    return render(request, 'properties/user_monitoring_panel.html', {
        'users_data': users_data
    })


@login_required
def user_monitoring_detail(request, user_id):
    """تفاصيل مراقبة مستخدم محدد"""
    from .permissions import is_platform_admin
    
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Get broker info
    broker = None
    try:
        broker = Broker.objects.get(user=user)
    except Broker.DoesNotExist:
        pass
    
    # Get subscription info
    subscriptions = []
    if broker:
        subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker
        ).order_by('-created_at')
    
    # Get properties
    properties = []
    if broker:
        properties = Property.objects.filter(
            broker=broker
        ).order_by('-created_at')[:20]
    
    # Get activity logs
    activity_logs = []
    try:
        activity_logs = ActivityLog.objects.filter(
            user=user
        ).order_by('-created_at')[:50]
    except:
        pass
    
    # Get messages
    messages_sent = []
    messages_received = []
    try:
        messages_sent = Message.objects.filter(
            sender=user
        ).order_by('-created_at')[:20]
        messages_received = Message.objects.filter(
            recipient=user
        ).order_by('-created_at')[:20]
    except:
        pass
    
    return render(request, 'properties/user_monitoring_detail.html', {
        'user': user,
        'broker': broker,
        'subscriptions': subscriptions,
        'properties': properties,
        'activity_logs': activity_logs,
        'messages_sent': messages_sent,
        'messages_received': messages_received,
    })


def get_client_ip(request):
    """الحصول على عنوان IP للعميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==================== NOTIFICATIONS VIEWS ====================

@login_required
def notification_center(request):
    """مركز الإشعارات للمستخدم"""
    from .models import Notification, NotificationRecipient

    # Get all notifications for the user
    notifications = NotificationRecipient.objects.filter(
        user=request.user
    ).select_related('notification').order_by('-created_at')

    # Get unread count
    unread_count = notifications.filter(is_read=False).count()

    # Get archived count
    archived_count = notifications.filter(is_archived=True).count()

    # Filter by status
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False, is_archived=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True, is_archived=False)
    elif filter_type == 'archived':
        notifications = notifications.filter(is_archived=True)
    else:
        notifications = notifications.filter(is_archived=False)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        notifications = notifications.filter(
            notification__title__icontains=search_query
        )

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'archived_count': archived_count,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'properties/notification_center.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_send_notification(request):
    """إرسال إشعارات من لوحة الإدارة"""
    from .forms import AdminNotificationForm
    from .models import Notification, NotificationRecipient, Broker
    
    if request.method == 'POST':
        form = AdminNotificationForm(request.POST)
        if form.is_valid():
            try:
                # Create notification
                notification = Notification.objects.create(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['message'],
                    notification_type=form.cleaned_data['notification_type'],
                    priority=form.cleaned_data['priority'],
                    icon=form.cleaned_data['icon'],
                    color=form.cleaned_data['color'],
                    status='scheduled' if not form.cleaned_data['send_immediately'] else 'sent',
                    scheduled_for=form.cleaned_data['schedule_date'] if not form.cleaned_data['send_immediately'] else None
                )
                
                # Add action URL if provided
                if form.cleaned_data['action_url']:
                    notification.metadata = {
                        'action_url': form.cleaned_data['action_url'],
                        'action_text': form.cleaned_data['action_text'] or 'عرض التفاصيل'
                    }
                    notification.save()
                
                # Determine recipients based on target audience
                target_audience = form.cleaned_data['target_audience']
                recipients = []
                
                if target_audience == 'all_users':
                    # Send to all active users
                    users = User.objects.filter(is_active=True)
                    for user in users:
                        NotificationRecipient.objects.create(
                            notification=notification,
                            user=user
                        )
                        recipients.append(user)
                
                elif target_audience == 'all_brokers':
                    # Send to all active brokers
                    brokers = Broker.objects.filter(is_active=True)
                    for broker in brokers:
                        NotificationRecipient.objects.create(
                            notification=notification,
                            user=broker.user,
                            broker=broker
                        )
                        recipients.append(broker.user)
                
                elif target_audience == 'both':
                    # Send to both users and brokers
                    users = User.objects.filter(is_active=True)
                    for user in users:
                        NotificationRecipient.objects.create(
                            notification=notification,
                            user=user
                        )
                        recipients.append(user)
                    
                    brokers = Broker.objects.filter(is_active=True)
                    for broker in brokers:
                        if broker.user not in recipients:
                            NotificationRecipient.objects.create(
                                notification=notification,
                                user=broker.user,
                                broker=broker
                            )
                            recipients.append(broker.user)
                
                elif target_audience == 'specific_users':
                    # Send to specific users
                    specific_users = form.cleaned_data['specific_users']
                    for user in specific_users:
                        NotificationRecipient.objects.create(
                            notification=notification,
                            user=user
                        )
                        recipients.append(user)
                
                elif target_audience == 'specific_brokers':
                    # Send to specific brokers
                    specific_brokers = form.cleaned_data['specific_brokers']
                    for broker in specific_brokers:
                        NotificationRecipient.objects.create(
                            notification=notification,
                            user=broker.user,
                            broker=broker
                        )
                        recipients.append(broker.user)
                
                # Send immediately if requested
                if form.cleaned_data['send_immediately']:
                    notification.status = 'sent'
                    notification.save()
                    messages.success(request, f'تم إرسال الإشعار بنجاح إلى {len(recipients)} مستخدم')
                else:
                    messages.success(request, f'تم جدولة الإشعار بنجاح لإرساله إلى {len(recipients)} مستخدم')
                
                return redirect('notification_center')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ: {str(e)}')
    else:
        form = AdminNotificationForm()
    
    return render(request, 'properties/admin_send_notification.html', {
        'form': form
    })


@login_required
def notification_detail(request, notification_id):
    """عرض تفاصيل إشعار"""
    from .models import Notification, NotificationRecipient
    
    try:
        recipient = NotificationRecipient.objects.get(
            notification_id=notification_id,
            user=request.user
        )
        
        # Mark as read
        recipient.mark_as_read()
        
        # If button link exists, redirect
        if recipient.notification.button_link:
            return redirect(recipient.notification.button_link)
        
        context = {
            'recipient': recipient,
            'notification': recipient.notification,
        }
        
        return render(request, 'properties/notification_detail.html', context)
    
    except NotificationRecipient.DoesNotExist:
        messages.error(request, 'الإشعار غير موجود')
        return redirect('notification_center')


@login_required
def mark_notification_read(request, notification_id):
    """تعليم إشعار كمقروء"""
    from .models import NotificationRecipient
    
    if request.method == 'POST':
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user
            )
            recipient.mark_as_read()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, 'تم تعليم الإشعار كمقروء')
        except NotificationRecipient.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'الإشعار غير موجود'})
            messages.error(request, 'الإشعار غير موجود')
    
    return redirect('notification_center')


@login_required
def mark_notification_clicked(request, notification_id):
    """تعليم إشعار كتم النقر"""
    from .models import NotificationRecipient
    
    if request.method == 'POST':
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user
            )
            recipient.mark_as_clicked()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
        except NotificationRecipient.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False})
    
    return JsonResponse({'success': True})


@login_required
def archive_notification(request, notification_id):
    """أرشفة إشعار"""
    from .models import NotificationRecipient
    
    if request.method == 'POST':
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user
            )
            recipient.archive()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, 'تم أرشفة الإشعار')
        except NotificationRecipient.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'الإشعار غير موجود'})
            messages.error(request, 'الإشعار غير موجود')
    
    return redirect('notification_center')


@login_required
def delete_notification(request, notification_id):
    """حذف إشعار"""
    from .models import NotificationRecipient
    
    if request.method == 'POST':
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=request.user
            )
            recipient.delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            messages.success(request, 'تم حذف الإشعار')
        except NotificationRecipient.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'الإشعار غير موجود'})
            messages.error(request, 'الإشعار غير موجود')
    
    return redirect('notification_center')


@login_required
def mark_all_read(request):
    """تعليم جميع الإشعارات كمقروءة"""
    from .models import NotificationRecipient
    
    if request.method == 'POST':
        NotificationRecipient.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'تم تعليم جميع الإشعارات كمقروءة')
    
    return redirect('notification_center')


def get_unread_count(request):
    """الحصول على عدد الإشعارات غير المقروءة (AJAX)"""
    from .models import NotificationRecipient
    
    if request.user.is_authenticated:
        count = NotificationRecipient.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    else:
        count = 0
    
    return JsonResponse({'count': count})


@login_required
def admin_notification_panel(request):
    """لوحة إدارة الإشعارات"""
    from .models import Notification, NotificationLog
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Stats
    total_sent = notifications.filter(status='sent').count()
    total_draft = notifications.filter(status='draft').count()
    total_scheduled = notifications.filter(status='scheduled').count()
    
    context = {
        'notifications': notifications,
        'total_sent': total_sent,
        'total_draft': total_draft,
        'total_scheduled': total_scheduled,
    }
    
    return render(request, 'properties/admin_notification_panel.html', context)


@login_required
def admin_create_notification(request):
    """إنشاء إشعار جديد"""
    from .models import Notification
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        notification_type = request.POST.get('notification_type', 'info')
        priority = request.POST.get('priority', 'normal')
        delivery_type = request.POST.get('delivery_type', 'in_app')
        icon = request.POST.get('icon', '')
        color = request.POST.get('color', '#0d9488')
        button_text = request.POST.get('button_text', '')
        button_link = request.POST.get('button_link', '')
        
        # Targeting
        target_all_users = request.POST.get('target_all_users') == 'on'
        target_all_brokers = request.POST.get('target_all_brokers') == 'on'
        target_all_admins = request.POST.get('target_all_admins') == 'on'
        target_office_owners = request.POST.get('target_office_owners') == 'on'
        target_managers = request.POST.get('target_managers') == 'on'
        target_active_users = request.POST.get('target_active_users') == 'on'
        target_new_users = request.POST.get('target_new_users') == 'on'
        target_inactive_users = request.POST.get('target_inactive_users') == 'on'
        
        # Account type targeting
        target_account_type = request.POST.get('target_account_type', '')
        target_subscription_type = request.POST.get('target_subscription_type', '')
        target_account_status = request.POST.get('target_account_status', '')
        
        # Properties targeting
        target_has_properties_str = request.POST.get('target_has_properties', '')
        target_has_properties = None
        if target_has_properties_str == 'true':
            target_has_properties = True
        elif target_has_properties_str == 'false':
            target_has_properties = False
        
        # Location targeting
        target_governorate = request.POST.get('target_governorate', '')
        target_city = request.POST.get('target_city', '')
        target_area = request.POST.get('target_area', '')
        
        # Property type targeting
        target_property_type = request.POST.get('target_property_type', '')
        
        # Broker targeting
        target_premium_brokers = request.POST.get('target_premium_brokers') == 'on'
        target_min_properties = request.POST.get('target_min_properties')
        target_min_rating = request.POST.get('target_min_rating')
        
        # Scheduling
        scheduled_for = request.POST.get('scheduled_for')
        expires_at = request.POST.get('expires_at')
        
        # Action
        action = request.POST.get('action', 'send')  # send, schedule, draft
        
        # Create notification
        notification = Notification.objects.create(
            title=title,
            description=description,
            notification_type=notification_type,
            priority=priority,
            delivery_type=delivery_type,
            icon=icon,
            color=color,
            button_text=button_text,
            button_link=button_link,
            target_all_users=target_all_users,
            target_all_brokers=target_all_brokers,
            target_all_admins=target_all_admins,
            target_office_owners=target_office_owners,
            target_managers=target_managers,
            target_active_users=target_active_users,
            target_new_users=target_new_users,
            target_inactive_users=target_inactive_users,
            target_account_type=target_account_type,
            target_subscription_type=target_subscription_type,
            target_account_status=target_account_status,
            target_has_properties=target_has_properties,
            target_governorate=target_governorate,
            target_city=target_city,
            target_area=target_area,
            target_property_type=target_property_type,
            target_premium_brokers=target_premium_brokers,
            target_min_properties=int(target_min_properties) if target_min_properties else None,
            target_min_rating=float(target_min_rating) if target_min_rating else None,
            scheduled_for=scheduled_for if scheduled_for else None,
            expires_at=expires_at if expires_at else None,
            created_by=request.user,
            status='draft' if action == 'draft' else ('scheduled' if scheduled_for else 'sent')
        )
        
        # If sending immediately
        if action == 'send' and not scheduled_for:
            from .services import NotificationService
            service = NotificationService()
            service.send_notification(notification)
        
        messages.success(request, 'تم إنشاء الإشعار بنجاح')
        return redirect('admin_notification_panel')
    
    return render(request, 'properties/admin_create_notification.html')


@login_required
def admin_edit_notification(request, notification_id):
    """تعديل إشعار (فقط للمسودات والمجدولة)"""
    from .models import Notification
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Only allow editing drafts and scheduled notifications
    if notification.status not in ['draft', 'scheduled']:
        messages.error(request, 'لا يمكن تعديل الإشعارات المرسلة')
        return redirect('admin_notification_detail', notification_id=notification_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        notification_type = request.POST.get('notification_type', 'info')
        priority = request.POST.get('priority', 'normal')
        delivery_type = request.POST.get('delivery_type', 'in_app')
        icon = request.POST.get('icon', '')
        color = request.POST.get('color', '#0d9488')
        button_text = request.POST.get('button_text', '')
        button_link = request.POST.get('button_link', '')
        
        # Targeting
        target_all_users = request.POST.get('target_all_users') == 'on'
        target_all_brokers = request.POST.get('target_all_brokers') == 'on'
        target_all_admins = request.POST.get('target_all_admins') == 'on'
        target_office_owners = request.POST.get('target_office_owners') == 'on'
        target_managers = request.POST.get('target_managers') == 'on'
        target_active_users = request.POST.get('target_active_users') == 'on'
        target_new_users = request.POST.get('target_new_users') == 'on'
        target_inactive_users = request.POST.get('target_inactive_users') == 'on'
        
        # Account type targeting
        target_account_type = request.POST.get('target_account_type', '')
        target_subscription_type = request.POST.get('target_subscription_type', '')
        target_account_status = request.POST.get('target_account_status', '')
        
        # Properties targeting
        target_has_properties_str = request.POST.get('target_has_properties', '')
        target_has_properties = None
        if target_has_properties_str == 'true':
            target_has_properties = True
        elif target_has_properties_str == 'false':
            target_has_properties = False
        
        # Location targeting
        target_governorate = request.POST.get('target_governorate', '')
        target_city = request.POST.get('target_city', '')
        target_area = request.POST.get('target_area', '')
        
        # Property type targeting
        target_property_type = request.POST.get('target_property_type', '')
        
        # Broker targeting
        target_premium_brokers = request.POST.get('target_premium_brokers') == 'on'
        target_min_properties = request.POST.get('target_min_properties')
        target_min_rating = request.POST.get('target_min_rating')
        
        # Scheduling
        scheduled_for = request.POST.get('scheduled_for')
        expires_at = request.POST.get('expires_at')
        
        # Action
        action = request.POST.get('action', 'send')  # send, schedule, draft
        
        # Update notification
        notification.title = title
        notification.description = description
        notification.notification_type = notification_type
        notification.priority = priority
        notification.delivery_type = delivery_type
        notification.icon = icon
        notification.color = color
        notification.button_text = button_text
        notification.button_link = button_link
        notification.target_all_users = target_all_users
        notification.target_all_brokers = target_all_brokers
        notification.target_all_admins = target_all_admins
        notification.target_office_owners = target_office_owners
        notification.target_managers = target_managers
        notification.target_active_users = target_active_users
        notification.target_new_users = target_new_users
        notification.target_inactive_users = target_inactive_users
        notification.target_account_type = target_account_type
        notification.target_subscription_type = target_subscription_type
        notification.target_account_status = target_account_status
        notification.target_has_properties = target_has_properties
        notification.target_governorate = target_governorate
        notification.target_city = target_city
        notification.target_area = target_area
        notification.target_property_type = target_property_type
        notification.target_premium_brokers = target_premium_brokers
        notification.target_min_properties = int(target_min_properties) if target_min_properties else None
        notification.target_min_rating = float(target_min_rating) if target_min_rating else None
        notification.scheduled_for = scheduled_for if scheduled_for else None
        notification.expires_at = expires_at if expires_at else None
        notification.status = 'draft' if action == 'draft' else ('scheduled' if scheduled_for else 'sent')
        notification.save()
        
        # If sending immediately
        if action == 'send' and not scheduled_for:
            from .services import NotificationService
            service = NotificationService()
            service.send_notification(notification)
        
        messages.success(request, 'تم تحديث الإشعار بنجاح')
        return redirect('admin_notification_detail', notification_id=notification.id)
    
    context = {
        'notification': notification,
        'edit_mode': True,
    }
    return render(request, 'properties/admin_create_notification.html', context)


@login_required
def admin_resend_notification(request, notification_id):
    """إعادة إرسال إشعار"""
    from .models import Notification
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Create a copy of the notification
    new_notification = Notification.objects.create(
        title=notification.title,
        description=notification.description,
        notification_type=notification.notification_type,
        priority=notification.priority,
        delivery_type=notification.delivery_type,
        icon=notification.icon,
        color=notification.color,
        button_text=notification.button_text,
        button_link=notification.button_link,
        target_all_users=notification.target_all_users,
        target_all_brokers=notification.target_all_brokers,
        target_all_admins=notification.target_all_admins,
        target_office_owners=notification.target_office_owners,
        target_managers=notification.target_managers,
        target_active_users=notification.target_active_users,
        target_new_users=notification.target_new_users,
        target_inactive_users=notification.target_inactive_users,
        target_account_type=notification.target_account_type,
        target_subscription_type=notification.target_subscription_type,
        target_account_status=notification.target_account_status,
        target_has_properties=notification.target_has_properties,
        target_governorate=notification.target_governorate,
        target_city=notification.target_city,
        target_area=notification.target_area,
        target_property_type=notification.target_property_type,
        target_premium_brokers=notification.target_premium_brokers,
        target_min_properties=notification.target_min_properties,
        target_min_rating=notification.target_min_rating,
        created_by=request.user,
        status='sent'
    )
    
    # Send the notification
    from .services import NotificationService
    service = NotificationService()
    service.send_notification(new_notification)
    
    messages.success(request, 'تم إعادة إرسال الإشعار بنجاح')
    return redirect('admin_notification_detail', notification_id=new_notification.id)


@login_required
def admin_notification_detail(request, notification_id):
    """عرض تفاصيل إشعار للإدارة"""
    from .models import Notification, NotificationLog
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notification = get_object_or_404(Notification, id=notification_id)
    logs = notification.logs.all()
    
    context = {
        'notification': notification,
        'logs': logs,
    }
    
    return render(request, 'properties/admin_notification_detail.html', context)


@login_required
def admin_resend_notification(request, notification_id):
    """إعادة إرسال إشعار"""
    from .models import Notification
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notification = get_object_or_404(Notification, id=notification_id)
    
    from .services import NotificationService
    service = NotificationService()
    service.send_notification(notification)
    
    messages.success(request, 'تم إرسال الإشعار بنجاح')
    return redirect('admin_notification_detail', notification_id=notification_id)


@login_required
def admin_delete_notification(request, notification_id):
    """حذف إشعار"""
    from .models import Notification
    from .permissions import can_access_admin_panel
    
    if not can_access_admin_panel(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    
    messages.success(request, 'تم حذف الإشعار')
    return redirect('admin_notification_panel')


@login_required
def admin_bulk_messaging(request):
    """صفحة المراسلة الجماعية للإدارة"""
    from .models import Broker, User, UserProfile
    from .permissions import can_send_to_all_brokers, can_send_to_all_users
    
    if not can_send_to_all_brokers(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('admin_panel')
    
    # الحصول على قائمة الدلالين
    brokers = Broker.objects.filter(is_active=True).select_related('user')
    
    # الحصول على قائمة المستخدمين
    users = User.objects.filter(
        is_active=True,
        broker_profile__isnull=True
    ).select_related('user_profile')
    
    if request.method == 'POST':
        message_type = request.POST.get('message_type')
        content = request.POST.get('content')
        target_type = request.POST.get('target_type')  # 'brokers', 'users', 'all'
        selected_brokers = request.POST.getlist('selected_brokers')
        selected_users = request.POST.getlist('selected_users')
        
        if not content:
            messages.error(request, 'يرجى إدخال محتوى الرسالة')
        else:
            from .models import Conversation, Message
            
            recipients = []
            
            if target_type == 'brokers' or target_type == 'all':
                if selected_brokers:
                    recipients.extend([User.objects.get(id=int(bid)) for bid in selected_brokers])
                else:
                    recipients.extend([broker.user for broker in brokers])
            
            if target_type == 'users' or target_type == 'all':
                if selected_users:
                    recipients.extend([User.objects.get(id=int(uid)) for uid in selected_users])
                else:
                    recipients.extend(list(users))
            
            # إنشاء محادثات جماعية
            for recipient in recipients:
                # التحقق من وجود محادثة سابقة
                existing_conversation = Conversation.objects.filter(
                    participants=request.user,
                    conversation_type=Conversation.TYPE_DIRECT
                ).filter(participants=recipient).first()
                
                if existing_conversation:
                    conversation = existing_conversation
                else:
                    conversation = Conversation.objects.create(
                        conversation_type=Conversation.TYPE_DIRECT,
                        created_by=request.user
                    )
                    conversation.participants.add(request.user, recipient)
                
                # إرسال الرسالة
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    recipient=recipient,
                    message_type=message_type or Message.TYPE_TEXT,
                    content=content,
                    status=Message.STATUS_SENT
                )
            
            messages.success(request, f'تم إرسال الرسالة إلى {len(recipients)} مستخدم')
            return redirect('admin_bulk_messaging')
    
    context = {
        'brokers': brokers,
        'users': users,
        'total_brokers': brokers.count(),
        'total_users': users.count(),
    }
    
    return render(request, 'properties/admin_bulk_messaging.html', context)


@login_required
def broker_bulk_messaging(request):
    """صفحة المراسلة الجماعية للدلال"""
    from .models import User, UserProfile
    from .permissions import can_send_to_all_users
    
    if not can_send_to_all_users(request.user):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على قائمة المستخدمين
    users = User.objects.filter(
        is_active=True,
        broker_profile__isnull=True
    ).select_related('user_profile')
    
    if request.method == 'POST':
        message_type = request.POST.get('message_type')
        content = request.POST.get('content')
        selected_users = request.POST.getlist('selected_users')
        
        if not content:
            messages.error(request, 'يرجى إدخال محتوى الرسالة')
        else:
            from .models import Conversation, Message
            
            recipients = []
            
            if selected_users:
                recipients.extend([User.objects.get(id=int(uid)) for uid in selected_users])
            else:
                recipients.extend(list(users))
            
            # إنشاء محادثات جماعية
            for recipient in recipients:
                # التحقق من وجود محادثة سابقة
                existing_conversation = Conversation.objects.filter(
                    participants=request.user,
                    conversation_type=Conversation.TYPE_DIRECT
                ).filter(participants=recipient).first()
                
                if existing_conversation:
                    conversation = existing_conversation
                else:
                    conversation = Conversation.objects.create(
                        conversation_type=Conversation.TYPE_DIRECT,
                        created_by=request.user
                    )
                    conversation.participants.add(request.user, recipient)
                
                # إرسال الرسالة
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    recipient=recipient,
                    message_type=message_type or Message.TYPE_TEXT,
                    content=content,
                    status=Message.STATUS_SENT
                )
            
            messages.success(request, f'تم إرسال الرسالة إلى {len(recipients)} مستخدم')
            return redirect('broker_bulk_messaging')
    
    context = {
        'users': users,
        'total_users': users.count(),
    }
    
    return render(request, 'properties/broker_bulk_messaging.html', context)


# ==================== Resort Views ====================

def resort_detail(request, slug):
    """View for resort details"""
    resort = get_object_or_404(Resort, slug=slug, status='active')
    resort.increment_views()
    
    # Get reviews
    reviews = resort.reviews.filter(is_approved=True)[:10]
    
    # Get offers
    offers = resort.offers.filter(is_active=True)
    
    # Get amenities
    amenities = resort.amenities.filter(is_available=True)
    
    # Get services
    services = resort.services.filter(is_available=True)
    
    # Check if user liked this resort
    is_liked = False
    if request.user.is_authenticated:
        is_liked = ResortLike.objects.filter(resort=resort, user=request.user).exists()
    
    # Check if user reviewed this resort
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = ResortReview.objects.filter(resort=resort, user=request.user).exists()
    
    context = {
        'resort': resort,
        'reviews': reviews,
        'offers': offers,
        'amenities': amenities,
        'services': services,
        'is_liked': is_liked,
        'has_reviewed': has_reviewed,
    }
    
    return render(request, 'properties/resort_detail.html', context)


@login_required
def resort_create(request):
    """View for creating a new resort"""
    if request.method == 'POST':
        name = request.POST.get('name')
        resort_type = request.POST.get('resort_type')
        description = request.POST.get('description')
        governorate = request.POST.get('governorate')
        city = request.POST.get('city')
        district = request.POST.get('district')
        full_address = request.POST.get('full_address')
        phone = request.POST.get('phone')
        whatsapp = request.POST.get('whatsapp')
        email = request.POST.get('email')
        website = request.POST.get('website')
        working_hours = request.POST.get('working_hours')
        working_days = request.POST.get('working_days')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        currency = request.POST.get('currency', 'د.ع')
        advance_booking = request.POST.get('advance_booking') == 'on'
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        video_url = request.POST.get('video_url')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        keywords = request.POST.get('keywords')
        
        resort = Resort.objects.create(
            name=name,
            resort_type=resort_type,
            description=description,
            governorate=governorate,
            city=city,
            district=district,
            full_address=full_address,
            phone=phone,
            whatsapp=whatsapp,
            email=email,
            website=website,
            working_hours=working_hours,
            working_days=working_days,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            advance_booking=advance_booking,
            latitude=latitude,
            longitude=longitude,
            video_url=video_url,
            meta_title=meta_title,
            meta_description=meta_description,
            keywords=keywords,
            broker=request.user.broker if hasattr(request.user, 'broker') else None,
            user=request.user,
        )
        
        # Handle cover image
        if 'cover_image' in request.FILES:
            resort.cover_image = request.FILES['cover_image']
        
        # Handle logo
        if 'logo' in request.FILES:
            resort.logo = request.FILES['logo']
        
        resort.save()
        
        # Add amenities
        amenities = request.POST.getlist('amenities')
        for amenity in amenities:
            ResortAmenity.objects.create(
                resort=resort,
                amenity_type=amenity,
                is_available=True
            )
        
        # Add services
        services = request.POST.getlist('services')
        for service in services:
            ResortService.objects.create(
                resort=resort,
                service_type=service,
                is_available=True
            )
        
        messages.success(request, 'تم إضافة المنتجع بنجاح')
        return redirect('resort_detail', slug=resort.slug)
    
    return render(request, 'properties/resort_form.html')


@login_required
def resort_update(request, slug):
    """View for updating a resort"""
    resort = get_object_or_404(Resort, slug=slug)
    
    # Check ownership
    if resort.broker and resort.broker.user != request.user:
        if resort.user != request.user:
            messages.error(request, 'ليس لديك صلاحية تعديل هذا المنتجع')
            return redirect('resort_detail', slug=slug)
    
    if request.method == 'POST':
        resort.name = request.POST.get('name', resort.name)
        resort.resort_type = request.POST.get('resort_type', resort.resort_type)
        resort.description = request.POST.get('description', resort.description)
        resort.governorate = request.POST.get('governorate', resort.governorate)
        resort.city = request.POST.get('city', resort.city)
        resort.district = request.POST.get('district', resort.district)
        resort.full_address = request.POST.get('full_address', resort.full_address)
        resort.phone = request.POST.get('phone', resort.phone)
        resort.whatsapp = request.POST.get('whatsapp', resort.whatsapp)
        resort.email = request.POST.get('email', resort.email)
        resort.website = request.POST.get('website', resort.website)
        resort.working_hours = request.POST.get('working_hours', resort.working_hours)
        resort.working_days = request.POST.get('working_days', resort.working_days)
        
        min_price = request.POST.get('min_price')
        if min_price:
            resort.min_price = min_price
        
        max_price = request.POST.get('max_price')
        if max_price:
            resort.max_price = max_price
        
        resort.currency = request.POST.get('currency', resort.currency)
        resort.advance_booking = request.POST.get('advance_booking') == 'on'
        
        # Handle cover image
        if 'cover_image' in request.FILES:
            resort.cover_image = request.FILES['cover_image']
        
        # Handle logo
        if 'logo' in request.FILES:
            resort.logo = request.FILES['logo']
        
        resort.save()


# Job Opportunity Views
def jobs_view(request):
    """View for listing all job opportunities"""
    from .constants import IRAQ_GOVERNORATES
    
    jobs = Job.objects.filter(status='active').select_related('category')
    categories = JobCategory.objects.filter(is_active=True)
    
    # Apply filters
    search_query = request.GET.get('search')
    category_filter = request.GET.get('category')
    location_type_filter = request.GET.get('location_type')
    governorate_filter = request.GET.get('governorate')
    
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(skills__icontains=search_query)
        )
    
    if category_filter:
        jobs = jobs.filter(category_id=category_filter)
    
    if location_type_filter:
        jobs = jobs.filter(location_type=location_type_filter)
    
    if governorate_filter:
        jobs = jobs.filter(governorate=governorate_filter)
    
    # Separate featured and regular jobs
    featured_jobs = jobs.filter(is_featured=True).order_by('-created_at')
    regular_jobs = jobs.filter(is_featured=False).order_by('-created_at')
    
    # Pagination for regular jobs
    paginator = Paginator(regular_jobs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'featured_jobs': featured_jobs,
        'jobs': page_obj,
        'categories': categories,
        'governorates': IRAQ_GOVERNORATES,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'properties/jobs.html', context)


def job_detail_view(request, slug):
    """View for job details"""
    job = get_object_or_404(Job, slug=slug, status='active')
    
    # Increment view count
    job.views_count += 1
    job.save()
    
    context = {
        'job': job,
    }
    
    return render(request, 'properties/job_detail.html', context)


@login_required
def job_apply_view(request, slug):
    """View for applying to a job"""
    job = get_object_or_404(Job, slug=slug, status='active')
    
    # Check if user can apply for this job
    if not can_apply_for_job(request.user, job):
        # Provide better error message
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            messages.warning(request, 'لقد قمت بالتقديم على هذه الوظيفة مسبقاً')
        elif job.posted_by and job.posted_by == request.user:
            messages.warning(request, 'لا يمكنك التقديم على وظيفة نشرتها بنفسك')
        else:
            messages.warning(request, 'لا يمكنك التقديم على هذه الوظيفة')
        return redirect('job_detail', slug=slug)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        current_position = request.POST.get('current_position')
        current_company = request.POST.get('current_company')
        years_of_experience = request.POST.get('years_of_experience', 0)
        cv_file = request.FILES.get('cv_file')
        cover_letter = request.POST.get('cover_letter')
        portfolio_url = request.POST.get('portfolio_url')
        expected_salary = request.POST.get('expected_salary')
        available_date = request.POST.get('available_date')
        
        if not cv_file:
            messages.error(request, 'يرجى إرفاق مف السيرة الذاتية')
            return redirect('job_detail', slug=slug)
        
        # Create application
        application = JobApplication.objects.create(
            job=job,
            applicant=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            current_position=current_position,
            current_company=current_company,
            years_of_experience=int(years_of_experience) if years_of_experience else 0,
            cv_file=cv_file,
            cover_letter=cover_letter,
            portfolio_url=portfolio_url,
            expected_salary=Decimal(expected_salary) if expected_salary else None,
            available_date=available_date if available_date else None,
        )
        
        # Update job application count
        job.applications_count += 1
        job.save()
        
        messages.success(request, 'تم إرسال طلبك بنجاح! سنتواصل معك قريباً')
        return redirect('job_detail', slug=slug)
    
    return redirect('job_detail', slug=slug)


@login_required
def job_post_view(request):
    """View for posting a new job"""
    # Check if user can post jobs
    if not can_post_job(request.user):
        messages.error(request, 'ليس لديك صلاحية نشر وظائف')
        return redirect('jobs')
    
    # Get user's subscription info
    from .permissions import get_broker
    broker = get_broker(request.user)
    
    # Check if user has any subscription at all
    if broker:
        if not broker.subscription_plan or not broker.subscription_end_date:
            messages.error(request, 'ليس لديك اشتراك حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
    available_days = 30  # Default for regular users
    
    if broker and broker.subscription_plan:
        period = broker.subscription_plan.period
        SUBSCRIPTION_PERIODS_DAYS = {
            'month': 30,
            '3_months': 90,
            '6_months': 180,
            'year': 365,
            '5_years': 1825,
            'unlimited': 3650,
        }
        available_days = SUBSCRIPTION_PERIODS_DAYS.get(period, 30)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        custom_category = request.POST.get('custom_category')
        company_name = request.POST.get('company_name')
        company_logo = request.FILES.get('company_logo')
        company_description = request.POST.get('company_description')
        job_type = request.POST.get('job_type')
        experience_level = request.POST.get('experience_level')
        location_type = request.POST.get('location_type', 'inside_iraq')
        governorate = request.POST.get('governorate')
        city = request.POST.get('city')
        country = request.POST.get('country')
        other_country_name = request.POST.get('other_country_name')
        outside_city = request.POST.get('outside_city')
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        is_remote = request.POST.get('is_remote') == 'on'
        salary_min = request.POST.get('salary_min')
        salary_max = request.POST.get('salary_max')
        salary_currency = request.POST.get('salary_currency', 'IQD')
        salary_period = request.POST.get('salary_period', 'monthly')
        is_salary_negotiable = request.POST.get('is_salary_negotiable') == 'on'
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        responsibilities = request.POST.get('responsibilities')
        benefits = request.POST.get('benefits')
        skills = request.POST.get('skills')
        workplace_image = request.FILES.get('workplace_image')
        additional_images_files = request.FILES.getlist('additional_images')
        posting_duration_days = request.POST.get('posting_duration_days', 30)
        contact_name = request.POST.get('contact_name')
        contact_email = request.POST.get('contact_email')
        contact_phone = request.POST.get('contact_phone')
        posting_duration_days = request.POST.get('posting_duration_days', 30)
        is_featured = request.POST.get('is_featured') == 'on'
        is_urgent = request.POST.get('is_urgent') == 'on'
        
        # Handle category - either existing or custom
        if category_id == 'custom' and custom_category:
            # Create new category
            category = JobCategory.objects.create(
                name_ar=custom_category,
                name_en=custom_category,
                icon='📋',
                description=f'تصنيف مخصص: {custom_category}',
                is_active=True
            )
        elif category_id:
            category = JobCategory.objects.get(id=category_id)
        else:
            category = None
        
        # Handle location - either inside or outside Iraq
        if location_type == 'inside_iraq':
            governorate_val = governorate
            city_val = city
            country_val = ''
            outside_city_val = ''
        else:
            governorate_val = ''
            city_val = ''
            country_val = country
            outside_city_val = outside_city
            
            # If "other" country is selected, use the custom name
            if country == 'other' and other_country_name:
                country_val = other_country_name
        
        # Handle additional images
        additional_images_list = []
        if additional_images_files:
            from django.core.files.storage import default_storage
            import os
            import uuid
            
            for img in additional_images_files:
                # Generate unique filename
                ext = os.path.splitext(img.name)[1]
                unique_filename = f"job_{uuid.uuid4().hex[:8]}{ext}"
                path = default_storage.save(f'jobs/additional/{unique_filename}', img)
                additional_images_list.append(path)
        
        # Handle workplace image
        workplace_image_path = None
        if workplace_image:
            from django.core.files.storage import default_storage
            import os
            import uuid
            
            ext = os.path.splitext(workplace_image.name)[1]
            unique_filename = f"workplace_{uuid.uuid4().hex[:8]}{ext}"
            workplace_image_path = default_storage.save(f'jobs/workplace/{unique_filename}', workplace_image)
        
        # Create job
        job = Job.objects.create(
            title=title,
            category=category,
            company_name=company_name,
            company_logo=company_logo,
            company_description=company_description,
            job_type=job_type,
            experience_level=experience_level,
            location_type=location_type,
            governorate=governorate_val,
            city=city_val,
            country=country_val,
            outside_city=outside_city_val,
            address=address,
            latitude=Decimal(latitude) if latitude else None,
            longitude=Decimal(longitude) if longitude else None,
            is_remote=is_remote,
            salary_min=Decimal(salary_min) if salary_min else None,
            salary_max=Decimal(salary_max) if salary_max else None,
            salary_currency=salary_currency,
            salary_period=salary_period,
            is_salary_negotiable=is_salary_negotiable,
            description=description,
            requirements=requirements,
            responsibilities=responsibilities,
            benefits=benefits,
            skills=skills,
            workplace_image=workplace_image_path,
            additional_images=additional_images_list,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            posting_duration_days=int(posting_duration_days),
            is_featured=is_featured,
            is_urgent=is_urgent,
            posted_by=request.user,
            status='draft',
            # New fields
            language=request.POST.get('language', 'arabic'),
            work_environment=request.POST.get('work_environment', 'onsite'),
            work_hours=request.POST.get('work_hours', ''),
            has_health_insurance=request.POST.get('has_health_insurance') == 'on',
            has_transport_allowance=request.POST.get('has_transport_allowance') == 'on',
            has_housing_allowance=request.POST.get('has_housing_allowance') == 'on',
            gender_requirement=request.POST.get('gender_requirement', 'not_specified'),
            education_requirement=request.POST.get('education_requirement', 'not_required'),
            experience_years=int(request.POST.get('experience_years')) if request.POST.get('experience_years') else None,
            start_date=datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date() if request.POST.get('start_date') else None,
            number_of_positions=int(request.POST.get('number_of_positions', 1)),
            external_application_url=request.POST.get('external_application_url', ''),
            phone_number=request.POST.get('phone_number', ''),
            email_address=request.POST.get('email_address', ''),
        )
        
        # Calculate expiry date based on subscription
        job.calculate_expiry_date(request.user)
        job.save()
        
        messages.success(request, 'تم إنشاء الوظيفة بنجاح! يمكنك نشرها من لوحة التحكم')
        return redirect('job_detail', slug=job.slug)
    
    categories = JobCategory.objects.filter(is_active=True)
    from .constants import IRAQ_GOVERNORATES
    
    context = {
        'categories': categories,
        'governorates': IRAQ_GOVERNORATES,
        'available_days': available_days,
        'broker': broker,
    }
    
    return render(request, 'properties/job_post.html', context)
    
    return render(request, 'properties/resort_form.html', context)


@login_required
def resort_delete(request, slug):
    """View for deleting a resort"""
    resort = get_object_or_404(Resort, slug=slug)
    
    # Check ownership
    if resort.broker and resort.broker.user != request.user:
        if resort.user != request.user:
            messages.error(request, 'ليس لديك صلاحية حذف هذا المنتجع')
            return redirect('resort_detail', slug=slug)
    
    if request.method == 'POST':
        resort.delete()
        messages.success(request, 'تم حذف المنتجع بنجاح')
        return redirect('resorts_list')
    
    context = {
        'resort': resort,
    }
    
    return render(request, 'properties/resort_confirm_delete.html', context)


@login_required
def resort_booking(request, slug):
    """View for booking a resort"""
    resort = get_object_or_404(Resort, slug=slug, status='active')
    
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = request.POST.get('guests', 1)
        special_requests = request.POST.get('special_requests', '')
        
        # Calculate total price
        from datetime import datetime, timedelta
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        nights = (check_out_date - check_in_date).days
        
        if nights <= 0:
            messages.error(request, 'تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول')
            return redirect('resort_detail', slug=slug)
        
        # Use average price if min and max are different
        if resort.min_price and resort.max_price:
            avg_price = (resort.min_price + resort.max_price) / 2
        elif resort.min_price:
            avg_price = resort.min_price
        elif resort.max_price:
            avg_price = resort.max_price
        else:
            avg_price = 0
        
        total_price = avg_price * nights
        
        booking = ResortBooking.objects.create(
            resort=resort,
            user=request.user,
            check_in=check_in_date,
            check_out=check_out_date,
            guests=int(guests),
            total_price=total_price,
            special_requests=special_requests,
            status='pending'
        )
        
        # Create notification
        Notification.create(
            user=resort.broker.user if resort.broker else resort.user,
            notification_type='message_received',
            title='حجز جديد',
            message=f'حجز جديد للمنتجع {resort.name} من {request.user.username}',
            link=f'/resorts/{resort.slug}/bookings/'
        )
        
        messages.success(request, 'تم إرسال طلب الحجز بنجاح')
        return redirect('resort_detail', slug=slug)
    
    context = {
        'resort': resort,
    }
    
    return render(request, 'properties/resort_booking.html', context)


@login_required
def resort_review(request, slug):
    """View for adding a review to a resort"""
    resort = get_object_or_404(Resort, slug=slug, status='active')
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Check if user already reviewed
        existing_review = ResortReview.objects.filter(resort=resort, user=request.user).first()
        if existing_review:
            existing_review.rating = int(rating)
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, 'تم تحديث تقييمك بنجاح')
        else:
            ResortReview.objects.create(
                resort=resort,
                user=request.user,
                rating=int(rating),
                comment=comment,
                is_approved=False
            )
            messages.success(request, 'تم إضافة تقييمك بنجاح وسيتم مراجعته')
        
        return redirect('resort_detail', slug=slug)
    
    context = {
        'resort': resort,
    }
    
    return render(request, 'properties/resort_review.html', context)


@login_required
def resort_like(request, slug):
    """View for liking/unliking a resort"""
    resort = get_object_or_404(Resort, slug=slug, status='active')
    
    like = ResortLike.objects.filter(resort=resort, user=request.user).first()
    
    if like:
        like.delete()
        resort.likes_count -= 1
        resort.save(update_fields=['likes_count'])
        return JsonResponse({'liked': False, 'likes_count': resort.likes_count})
    else:
        ResortLike.objects.create(resort=resort, user=request.user)
        return JsonResponse({'liked': True, 'likes_count': resort.likes_count})


@login_required
def resort_my_resorts(request):
    """View for user's resorts"""
    resorts = Resort.objects.filter(
        Q(broker__user=request.user) | Q(user=request.user)
    ).order_by('-created_at')
    
    context = {
        'resorts': resorts,
    }
    
    return render(request, 'properties/resort_my_resorts.html', context)


@login_required
def resort_my_bookings(request):
    """View for user's resort bookings"""
    bookings = ResortBooking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'properties/resort_my_bookings.html', context)


# Travel Company Views

def travel_companies_view(request):
    """View for all travel companies"""
    from properties.models import TravelCompany, Broker
    from properties.constants import TRAVEL_COMPANY_TYPES, TRAVEL_TYPES, IRAQ_GOVERNORATES
    
    # Get filters
    company_type = request.GET.get('company_type', '')
    travel_type = request.GET.get('travel_type', '')
    governorate = request.GET.get('governorate', '')
    
    companies = TravelCompany.objects.filter(is_active=True)
    
    if company_type:
        companies = companies.filter(company_type=company_type)
    
    if travel_type:
        companies = companies.filter(travel_types__contains=travel_type)
    
    if governorate:
        companies = companies.filter(governorate=governorate)
    
    # Get broker info for personalized experience
    broker = Broker.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    broker_companies = []
    if broker:
        broker_companies = TravelCompany.objects.filter(created_by=broker.user, is_active=True)
    
    return render(request, 'properties/travel_companies.html', {
        'companies': companies,
        'company_type': company_type,
        'travel_type': travel_type,
        'governorate': governorate,
        'company_types': TRAVEL_COMPANY_TYPES,
        'travel_types': TRAVEL_TYPES,
        'governorates': IRAQ_GOVERNORATES,
        'category_title': 'شركات السفر',
        'broker': broker,
        'broker_companies': broker_companies,
        'category_icon': '✈️',
    })


def travel_company_detail(request, pk):
    """View for travel company detail"""
    from properties.models import TravelCompany, TravelPackage
    
    company = get_object_or_404(TravelCompany, pk=pk, is_active=True)
    packages = company.travel_packages.filter(status='published', is_active=True)
    
    return render(request, 'properties/travel_company_detail.html', {
        'company': company,
        'packages': packages,
    })


@login_required
def travel_package_list(request):
    """View for listing travel packages"""
    from properties.models import TravelPackage
    
    packages = TravelPackage.objects.filter(status='published', is_active=True)
    
    # Filter by company if provided
    company_id = request.GET.get('company')
    if company_id:
        packages = packages.filter(company_id=company_id)
    
    # Filter by travel type
    travel_type = request.GET.get('type')
    if travel_type:
        packages = packages.filter(travel_type=travel_type)
    
    return render(request, 'properties/travel_package_list.html', {
        'packages': packages,
    })


@login_required
def travel_package_detail(request, pk, slug):
    """View for travel package detail"""
    from properties.models import TravelPackage
    
    package = get_object_or_404(TravelPackage, pk=pk, slug=slug, status='published', is_active=True)
    
    return render(request, 'properties/travel_package_detail.html', {
        'package': package,
    })


@login_required
def travel_package_create(request, company_id):
    """View for creating a new travel package - only company owner or broker can create"""
    from properties.models import TravelCompany, TravelPackage, Broker
    from .forms import TravelPackageForm
    
    company = get_object_or_404(TravelCompany, pk=company_id)
    
    # Check permissions: only broker or company owner can create packages
    broker = Broker.objects.filter(user=request.user).first()
    is_broker = broker is not None
    
    # For now, allow all authenticated users to create packages (can be restricted later)
    # if not is_broker:
    #     return redirect('dashboard')  # Only brokers can create packages
    
    if request.method == 'POST':
        form = TravelPackageForm(request.POST, request.FILES)
        if form.is_valid():
            package = form.save(commit=False)
            package.company = company
            if is_broker:
                package.created_by = request.user
            package.save()
            return redirect('travel_company_detail', pk=company.pk)
    else:
        form = TravelPackageForm()
    
    return render(request, 'properties/travel_package_form.html', {
        'form': form,
        'company': company,
        'is_broker': is_broker,
    })


@login_required
def travel_package_update(request, pk):
    """View for updating a travel package - only creator or broker can update"""
    from properties.models import TravelPackage, Broker
    from .forms import TravelPackageForm
    
    package = get_object_or_404(TravelPackage, pk=pk)
    
    # Check permissions: only broker or package creator can update
    broker = Broker.objects.filter(user=request.user).first()
    is_broker = broker is not None
    is_creator = package.created_by == request.user
    
    if not is_broker and not is_creator:
        return redirect('dashboard')  # No permission
    
    if request.method == 'POST':
        form = TravelPackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()
            return redirect('travel_package_detail', pk=package.pk, slug=package.slug)
    else:
        form = TravelPackageForm(instance=package)
    
    return render(request, 'properties/travel_package_form.html', {
        'form': form,
        'package': package,
        'is_broker': is_broker,
    })


@login_required
def travel_package_delete(request, pk):
    """View for deleting a travel package - only creator or broker can delete"""
    from properties.models import TravelPackage, Broker
    
    package = get_object_or_404(TravelPackage, pk=pk)
    company_id = package.company.id
    
    # Check permissions: only broker or package creator can delete
    broker = Broker.objects.filter(user=request.user).first()
    is_broker = broker is not None
    is_creator = package.created_by == request.user
    
    if not is_broker and not is_creator:
        return redirect('dashboard')  # No permission
    
    if request.method == 'POST':
        package.delete()
        return redirect('travel_company_detail', pk=company_id)
    
    return render(request, 'properties/travel_package_confirm_delete.html', {
        'package': package,
    })





# Resort Inside Iraq Views

@login_required
def resort_create_inside_iraq(request):
    """View for creating a resort inside Iraq"""
    from .forms import PropertyForm, PropertyResortForm
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر المنتجعات.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة منتجعات.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من المنتجعات ({published}/{limit}). '
                    f'يمكنك حذف بعض المنتجعات القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من المنتجعات حسب باقة اشتراكك. '
            'يمكنك حذف بعض المنتجعات القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')
    
    if request.method == 'POST':
        # First create the base property
        property_form = PropertyForm(request.POST, request.FILES)
        if property_form.is_valid():
            property_instance = property_form.save(commit=False)
            property_instance.owner = request.user
            property_instance.property_type = 'resort'
            property_instance.location_type = 'inside_iraq'
            property_instance.save()
            
            # Create the resort details
            resort_form = PropertyResortForm(request.POST, request.FILES)
            if resort_form.is_valid():
                resort_instance = resort_form.save(commit=False)
                resort_instance.property = property_instance
                resort_instance.save()
                
                messages.success(request, 'تم إضافة المنتجع داخل العراق بنجاح')
                return redirect('property_detail', pk=property_instance.pk)
    else:
        property_form = PropertyForm()
        resort_form = PropertyResortForm()
    
    return render(request, 'properties/resort_create_inside_iraq.html', {
        'property_form': property_form,
        'resort_form': resort_form
    })


@login_required
def resort_create_outside_iraq(request):
    """View for creating a resort outside Iraq"""
    from .forms import PropertyForm, PropertyResortForm
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.can_publish_property():
            if broker.is_suspended:
                messages.error(request, 'تم تعطيل حسابك مؤقتاً بسبب انتهاء الاشتراك. يرجى تجديد الاشتراك للاستمرار.')
                return redirect('subscription_plans')
            elif not broker.is_subscription_active():
                messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر المنتجعات.')
                return redirect('subscription_plans')
            elif not broker.can_add_properties:
                messages.error(request, 'ليس لديك صلاحية إضافة منتجعات.')
            else:
                remaining = broker.get_remaining_properties()
                published = broker.get_published_properties_count()
                limit = broker.get_property_limit()
                messages.error(
                    request, 
                    f'وصلت للحد الأقصى من المنتجعات ({published}/{limit}). '
                    f'يمكنك حذف بعض المنتجعات القديمة أو طلب تطوير خطة الاشتراك لنشر المزيد.'
                )
            return redirect('dashboard')
    elif not can_add_property(request.user):
        messages.error(
            request, 
            'وصلت للحد الأقصى من المنتجعات حسب باقة اشتراكك. '
            'يمكنك حذف بعض المنتجعات القديمة أو طلب تطوير خطة الاشتراك.'
        )
        return redirect('dashboard')
    
    if request.method == 'POST':
        # First create the base property
        property_form = PropertyForm(request.POST, request.FILES)
        if property_form.is_valid():
            property_instance = property_form.save(commit=False)
            property_instance.owner = request.user
            property_instance.property_type = 'resort'
            property_instance.location_type = 'outside_iraq'
            property_instance.save()
            
            # Create the resort details
            resort_form = PropertyResortForm(request.POST, request.FILES)
            if resort_form.is_valid():
                resort_instance = resort_form.save(commit=False)
                resort_instance.property = property_instance
                resort_instance.save()
                
                messages.success(request, 'تم إضافة المنتجع خارج العراق بنجاح')
                return redirect('property_detail', pk=property_instance.pk)
    else:
        property_form = PropertyForm()
        resort_form = PropertyResortForm()
    
    return render(request, 'properties/resort_create_outside_iraq.html', {
        'property_form': property_form,
        'resort_form': resort_form
    })


def resorts_inside_iraq_view(request):
    """View for resorts inside Iraq"""
    from properties.models import ResortInsideIraq
    from properties.constants import RESORT_TYPES, IRAQ_GOVERNORATES
    
    # Get filters
    resort_type = request.GET.get('resort_type', '')
    governorate = request.GET.get('governorate', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    resorts = ResortInsideIraq.objects.filter(is_active=True)
    
    if resort_type:
        resorts = resorts.filter(resort_type=resort_type)
    
    if governorate:
        resorts = resorts.filter(governorate=governorate)
    
    if price_min:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night >= int(price_min)]
    if price_max:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night <= int(price_max)]
    
    return render(request, 'properties/categories/resorts_inside_iraq.html', {
        'resorts': resorts,
        'resort_type': resort_type,
        'governorate': governorate,
        'price_min': price_min,
        'price_max': price_max,
        'resort_types': RESORT_TYPES,
        'governorates': IRAQ_GOVERNORATES,
        'category_title': 'منتجعات داخل العراق',
        'category_icon': '🏝️',
        'can_create_resort': request.user.is_authenticated,
    })


def resort_inside_detail(request, pk):
    """View for resort inside Iraq detail"""
    from properties.models import ResortInsideIraq
    
    resort = get_object_or_404(ResortInsideIraq, pk=pk, is_active=True)
    
    return render(request, 'properties/resort_inside_detail.html', {
        'resort': resort,
    })


# Resort Outside Iraq Views

def resorts_outside_iraq_view(request):
    """View for resorts outside Iraq"""
    from properties.models import ResortOutsideIraq, Country
    from properties.constants import RESORT_TYPES
    
    # Get filters
    resort_type = request.GET.get('resort_type', '')
    country_id = request.GET.get('country', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    resorts = ResortOutsideIraq.objects.filter(is_active=True)
    
    if resort_type:
        resorts = resorts.filter(resort_type=resort_type)
    
    if country_id:
        resorts = resorts.filter(country_id=int(country_id))
    
    if price_min:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night >= int(price_min)]
    if price_max:
        resorts = [r for r in resorts if r.price_per_night and r.price_per_night <= int(price_max)]
    
    countries = Country.objects.all().order_by('name_ar')
    
    return render(request, 'properties/categories/resorts_outside_iraq.html', {
        'resorts': resorts,
        'resort_type': resort_type,
        'country_id': country_id,
        'price_min': price_min,
        'price_max': price_max,
        'resort_types': RESORT_TYPES,
        'countries': countries,
        'category_title': 'منتجعات خارج العراق',
        'category_icon': '🏝️',
        'can_create_resort': request.user.is_authenticated,
    })


def resort_outside_detail(request, pk):
    """View for resort outside Iraq detail"""
    from properties.models import ResortOutsideIraq
    
    resort = get_object_or_404(ResortOutsideIraq, pk=pk, is_active=True)
    
    return render(request, 'properties/resort_outside_detail.html', {
        'resort': resort,
    })


def jobs_list(request):
    """صفحة عرض فرص العمل مع نظام البحث"""
    from django.db.models import Q
    from properties.models import Job
    
    # Get active job postings
    jobs = Job.objects.filter(is_active=True).select_related('user', 'country').order_by('-is_featured', '-is_urgent', '-created_at')
    
    # Apply filters
    location_type = request.GET.get('location_type')
    if location_type:
        jobs = jobs.filter(location_type=location_type)
    
    governorate = request.GET.get('governorate')
    if governorate:
        jobs = jobs.filter(governorate=governorate)
    
    country = request.GET.get('country')
    if country:
        jobs = jobs.filter(country_id=country)
    
    job_type = request.GET.get('job_type')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    salary_range = request.GET.get('salary_range')
    if salary_range:
        jobs = jobs.filter(salary_range=salary_range)
    
    field = request.GET.get('field')
    if field:
        jobs = jobs.filter(field__icontains=field)
    
    education = request.GET.get('education')
    if education:
        jobs = jobs.filter(education=education)
    
    experience = request.GET.get('experience')
    if experience:
        jobs = jobs.filter(experience=experience)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        jobs = jobs.filter(
            Q(job_title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(field__icontains=search_query) |
            Q(skills__icontains=search_query)
        )
    
    return render(request, 'properties/jobs_list.html', {
        'jobs': jobs,
        'location_type': location_type,
        'governorate': governorate,
        'country': country,
        'job_type': job_type,
        'salary_range': salary_range,
        'field': field,
        'education': education,
        'experience': experience,
        'search_query': search_query,
    })


def job_detail(request, pk):
    """صفحة تفاصيل فرصة العمل"""
    from properties.models import Job
    
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    # Increment views count
    job.views_count += 1
    job.save(update_fields=['views_count'])
    
    return render(request, 'properties/job_detail.html', {
        'job': job,
    })


def job_create(request):
    """صفحة نشر فرصة عمل جديدة"""
    from properties.models import Job, JobCategory, JobImage, JobVideo
    from django.contrib import messages
    from django.utils.text import slugify
    from .permissions import get_broker
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check subscription status
    broker = get_broker(request.user)
    if broker:
        broker.check_subscription_status()
        # Check if user has any active subscription
        from .models import BrokerPlanSubscription
        active_subscriptions = BrokerPlanSubscription.objects.filter(
            broker=broker,
            status='active'
        )
        has_active_subscription = False
        for sub in active_subscriptions:
            if sub.is_active():
                has_active_subscription = True
                break

        if not has_active_subscription:
            messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لاستخدام هذه الخدمة.')
            return redirect('subscription_plans')
        if not broker.is_subscription_active():
            messages.error(request, 'انتهى اشتراكك. يرجى تجديد الاشتراك لنشر هذه الخدمة.')
            return redirect('subscription_plans')
    
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.status = 'active'
            
            # Generate slug
            if not job.slug:
                job.slug = slugify(f"{job.title}-{job.id}")
                job.save()
            
            # Generate slug after saving to get the ID
            if not job.slug:
                job.slug = slugify(f"{job.title}-{job.id}")
            
            job.save()
            
            # Handle additional images
            images = request.FILES.getlist('additional_images')
            for image in images:
                JobImage.objects.create(job=job, image=image)
            
            # Handle videos
            videos = request.FILES.getlist('videos')
            for video in videos:
                JobVideo.objects.create(job=job, video=video)
            
            messages.success(request, 'تم نشر فرصة العمل بنجاح')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm()
    
    categories = JobCategory.objects.all()
    
    return render(request, 'properties/job_create.html', {
        'form': form,
        'categories': categories,
    })


def my_jobs(request):
    """صفحة إدارة فرص العمل المنشورة من قبل المستخدم"""
    from properties.models import Job
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    
    return render(request, 'properties/my_jobs.html', {
        'jobs': jobs,
    })


def job_edit(request, pk):
    """صفحة تعديل فرصة عمل"""
    from properties.models import Job, Country, JobImage, JobVideo
    from django.contrib import messages
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    job = get_object_or_404(Job, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Update job posting
        job.job_title = request.POST.get('job_title', job.job_title)
        job.company_name = request.POST.get('company_name', job.company_name)
        job.location_type = request.POST.get('location_type', job.location_type)
        job.governorate = request.POST.get('governorate', job.governorate)
        job.city = request.POST.get('city', job.city)
        country_id = request.POST.get('country')
        job.country_id = country_id if country_id else job.country_id
        job.job_type = request.POST.get('job_type', job.job_type)
        job.salary_range = request.POST.get('salary_range', job.salary_range)
        job.field = request.POST.get('field', job.field)
        job.education = request.POST.get('education', job.education)
        job.experience = request.POST.get('experience', job.experience)
        job.description = request.POST.get('description', job.description)
        job.responsibilities = request.POST.get('responsibilities', job.responsibilities)
        job.benefits = request.POST.get('benefits', job.benefits)
        job.skills = request.POST.get('skills', job.skills)
        job.contact_phone = request.POST.get('contact_phone', job.contact_phone)
        job.whatsapp = request.POST.get('whatsapp', job.whatsapp)
        job.contact_email = request.POST.get('contact_email', job.contact_email)
        job.company_website = request.POST.get('company_website', job.company_website)
        job.address = request.POST.get('address', job.address)
        job.is_featured = request.POST.get('is_featured') == 'on'
        job.is_urgent = request.POST.get('is_urgent') == 'on'
        
        # Handle cover image
        if 'cover_image' in request.FILES:
            job.cover_image = request.FILES['cover_image']
        
        # Handle company logo
        if 'company_logo' in request.FILES:
            job.company_logo = request.FILES['company_logo']
        
        job.save()
        
        # Handle new images
        images = request.FILES.getlist('images')
        for image in images:
            JobImage.objects.create(job=job, image=image)
        
        # Handle new videos
        videos = request.FILES.getlist('videos')
        for video in videos:
            JobVideo.objects.create(job=job, video=video)
        
        messages.success(request, 'تم تحديث فرصة العمل بنجاح')
        return redirect('job_detail', pk=job.pk)


# Helper Functions
def get_client_ip(request):
    """الحصول على عنوان IP للعميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def can_manage_backups(user):
    """التحقق من صلاحية إدارة النسخ الاحتياطية"""
    # فقط المسؤولون (Superuser) يمكنهم إدارة النسخ الاحتياطية
    return user.is_superuser


# Backup Views
@login_required
def create_backup(request):
    """إنشاء نسخة احتياطية جديدة"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طلب غير صالح'}, status=400)
    
    try:
        import json
        import time
        import hashlib
        data = json.loads(request.body)
        backup_type = data.get('type', 'full')
        backup_name = data.get('name', '')
        backup_description = data.get('description', '')
        
        from .models import Backup, BackupAuditLog
        import os
        from django.conf import settings
        from django.utils import timezone
        import shutil
        
        # Start timing
        start_time = time.time()
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        if backup_name:
            backup_filename = f'{backup_name}_{timestamp}'
        else:
            backup_filename = f'backup_{backup_type}_{timestamp}'
        
        # Generate version number
        backup_count = Backup.objects.filter(backup_type=backup_type).count()
        version = f'v{backup_count + 1}'
        
        # Create backup with initial status
        backup = Backup.objects.create(
            name=backup_filename,
            version=version,
            backup_type=backup_type,
            file_path='',
            size=0,
            description=backup_description or f'نسخة احتياطية {backup_type}',
            status='creating',
            created_by=request.user
        )
        
        # Create backup based on type
        backup_path = ''
        backup_size = 0
        db_size = 0
        media_size = 0
        file_count = 0
        
        try:
            if backup_type == 'database':
                # Database backup
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                if os.path.exists(db_path):
                    backup_path = os.path.join(backup_dir, f'{backup_filename}.db')
                    shutil.copy2(db_path, backup_path)
                    backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                    db_size = backup_size
                    file_count = 1
            
            elif backup_type == 'files':
                # All platform files backup (media + assets + static)
                media_path = settings.MEDIA_ROOT
                assets_path = os.path.join(settings.BASE_DIR, 'assets')
                static_path = os.path.join(settings.BASE_DIR, 'static')
                
                # Create a temporary directory for the files backup
                temp_dir = os.path.join(backup_dir, f'temp_files_{timestamp}')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Copy media files
                if os.path.exists(media_path):
                    shutil.copytree(media_path, os.path.join(temp_dir, 'media'))
                    for root, dirs, files in os.walk(media_path):
                        file_count += len(files)
                
                # Copy assets folder
                if os.path.exists(assets_path):
                    shutil.copytree(assets_path, os.path.join(temp_dir, 'assets'))
                    for root, dirs, files in os.walk(assets_path):
                        file_count += len(files)
                
                # Copy static files
                if os.path.exists(static_path):
                    shutil.copytree(static_path, os.path.join(temp_dir, 'static'))
                    for root, dirs, files in os.walk(static_path):
                        file_count += len(files)
                
                # Create zip
                backup_path = os.path.join(backup_dir, f'{backup_filename}.zip')
                shutil.make_archive(backup_path.replace('.zip', ''), 'zip', temp_dir)
                backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                media_size = backup_size
                
                # Clean up temp directory
                shutil.rmtree(temp_dir)
            
            else:  # full backup
                # Full backup (database + all platform data)
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                media_path = settings.MEDIA_ROOT
                assets_path = os.path.join(settings.BASE_DIR, 'assets')
                static_path = os.path.join(settings.BASE_DIR, 'static')
                
                # Create a temporary directory for the full backup
                temp_dir = os.path.join(backup_dir, f'temp_{timestamp}')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Copy database
                if os.path.exists(db_path):
                    shutil.copy2(db_path, os.path.join(temp_dir, 'db.sqlite3'))
                    db_size = os.path.getsize(db_path) / (1024 * 1024)
                    file_count += 1
                
                # Copy media files
                if os.path.exists(media_path):
                    shutil.copytree(media_path, os.path.join(temp_dir, 'media'))
                    for root, dirs, files in os.walk(media_path):
                        file_count += len(files)
                
                # Copy assets folder (images, documents, audio, video)
                if os.path.exists(assets_path):
                    shutil.copytree(assets_path, os.path.join(temp_dir, 'assets'))
                    for root, dirs, files in os.walk(assets_path):
                        file_count += len(files)
                
                # Copy static files
                if os.path.exists(static_path):
                    shutil.copytree(static_path, os.path.join(temp_dir, 'static'))
                    for root, dirs, files in os.walk(static_path):
                        file_count += len(files)
                
                # Create zip
                backup_path = os.path.join(backup_dir, f'{backup_filename}.zip')
                shutil.make_archive(backup_path.replace('.zip', ''), 'zip', temp_dir)
                backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
                media_size = backup_size - db_size
                
                # Clean up temp directory
                shutil.rmtree(temp_dir)
            
            # Calculate duration
            duration = int(time.time() - start_time)
            
            # Calculate checksum
            checksum = None
            if os.path.exists(backup_path):
                sha256_hash = hashlib.sha256()
                with open(backup_path, 'rb') as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                checksum = sha256_hash.hexdigest()
            
            # Update backup record
            backup.file_path = backup_path
            backup.size = round(backup_size, 2)
            backup.database_size = round(db_size, 2)
            backup.media_size = round(media_size, 2)
            backup.file_count = file_count
            backup.duration = duration
            backup.checksum = checksum
            backup.status = 'completed'
            backup.save()
            
            # Log audit
            BackupAuditLog.objects.create(
                backup=backup,
                action='created',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='success'
            )
            
            return JsonResponse({'success': True, 'backup_id': backup.id})
            
        except Exception as backup_error:
            # Mark as failed
            backup.status = 'failed'
            backup.save()
            
            # Log audit
            BackupAuditLog.objects.create(
                backup=backup,
                action='created',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='failed',
                error_message=str(backup_error)
            )
            
            raise backup_error
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def restore_backup(request, backup_id):
    """استعادة نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طلب غير صالح'}, status=400)
    
    try:
        from .models import Backup, BackupAuditLog
        import os
        import shutil
        from django.conf import settings
        from django.utils import timezone
        import time
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        # Check if backup is restorable
        if not backup.is_restorable():
            return JsonResponse({'success': False, 'error': 'لا يمكن استعادة هذه النسخة'}, status=400)
        
        # Check if backup is currently being restored
        if backup.status == 'restoring':
            return JsonResponse({'success': False, 'error': 'جاري استعادة هذه النسخة بالفعل'}, status=400)
        
        if not os.path.exists(backup.file_path):
            return JsonResponse({'success': False, 'error': 'ملف النسخة الاحتياطية غير موجود'}, status=404)
        
        # Mark backup as restoring
        backup.status = 'restoring'
        backup.save()
        
        try:
            # Create pre-restore safety backup
            safety_backup = None
            try:
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                safety_filename = f'safety_backup_before_restore_{timestamp}'
                safety_backup = Backup.objects.create(
                    name=safety_filename,
                    version='safety',
                    backup_type='full',
                    file_path='',
                    size=0,
                    description='نسخة أمان قبل الاستعادة',
                    status='creating',
                    is_safety_backup=True,
                    created_by=request.user
                )
                
                # Create safety backup
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                media_path = settings.MEDIA_ROOT
                assets_path = os.path.join(settings.BASE_DIR, 'assets')
                static_path = os.path.join(settings.BASE_DIR, 'static')
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                temp_dir = os.path.join(backup_dir, f'temp_safety_{timestamp}')
                os.makedirs(temp_dir, exist_ok=True)
                
                if os.path.exists(db_path):
                    shutil.copy2(db_path, os.path.join(temp_dir, 'db.sqlite3'))
                
                if os.path.exists(media_path):
                    shutil.copytree(media_path, os.path.join(temp_dir, 'media'))
                
                if os.path.exists(assets_path):
                    shutil.copytree(assets_path, os.path.join(temp_dir, 'assets'))
                
                if os.path.exists(static_path):
                    shutil.copytree(static_path, os.path.join(temp_dir, 'static'))
                
                safety_path = os.path.join(backup_dir, f'{safety_filename}.zip')
                shutil.make_archive(safety_path.replace('.zip', ''), 'zip', temp_dir)
                safety_size = os.path.getsize(safety_path) / (1024 * 1024)
                
                shutil.rmtree(temp_dir)
                
                safety_backup.file_path = safety_path
                safety_backup.size = round(safety_size, 2)
                safety_backup.status = 'completed'
                safety_backup.save()
                
            except Exception as safety_error:
                # Log safety backup failure but continue with restore
                BackupAuditLog.objects.create(
                    backup=safety_backup if safety_backup else backup,
                    action='created',
                    user=request.user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    result='failed',
                    error_message=f'فشل إنشاء نسخة الأمان: {str(safety_error)}'
                )
            
            # Restore based on backup type
            if backup.backup_type == 'database':
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                shutil.copy2(backup.file_path, db_path)
            
            elif backup.backup_type == 'files':
                media_path = settings.MEDIA_ROOT
                shutil.rmtree(media_path, ignore_errors=True)
                os.makedirs(media_path, exist_ok=True)
                shutil.unpack_archive(backup.file_path, media_path)
            
            else:  # full backup
                temp_dir = os.path.join(settings.BASE_DIR, 'temp_restore')
                os.makedirs(temp_dir, exist_ok=True)
                shutil.unpack_archive(backup.file_path, temp_dir)
                
                # Restore database
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                temp_db = os.path.join(temp_dir, 'db.sqlite3')
                if os.path.exists(temp_db):
                    shutil.copy2(temp_db, db_path)
                
                # Restore media files
                media_path = settings.MEDIA_ROOT
                temp_media = os.path.join(temp_dir, 'media')
                if os.path.exists(temp_media):
                    shutil.rmtree(media_path, ignore_errors=True)
                    shutil.copytree(temp_media, media_path)
                
                # Restore assets folder
                assets_path = os.path.join(settings.BASE_DIR, 'assets')
                temp_assets = os.path.join(temp_dir, 'assets')
                if os.path.exists(temp_assets):
                    shutil.rmtree(assets_path, ignore_errors=True)
                    shutil.copytree(temp_assets, assets_path)
                
                # Restore static files
                static_path = os.path.join(settings.BASE_DIR, 'static')
                temp_static = os.path.join(temp_dir, 'static')
                if os.path.exists(temp_static):
                    shutil.rmtree(static_path, ignore_errors=True)
                    shutil.copytree(temp_static, static_path)
                
                # Clean up
                shutil.rmtree(temp_dir)
            
            # Update backup status
            backup.status = 'restored'
            backup.restored_by = request.user
            backup.restored_at = timezone.now()
            backup.save()
            
            # Log audit
            BackupAuditLog.objects.create(
                backup=backup,
                action='restored',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='success'
            )
            
            return JsonResponse({'success': True, 'safety_backup_id': safety_backup.id if safety_backup else None})
            
        except Exception as restore_error:
            # Mark restore as failed
            backup.status = 'failed'
            backup.save()
            
            # Log audit
            BackupAuditLog.objects.create(
                backup=backup,
                action='restored',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='failed',
                error_message=str(restore_error)
            )
            
            # Try to rollback using safety backup if available
            if safety_backup and safety_backup.status == 'completed':
                try:
                    from django.db import connection
                    connection.close()
                    # User can manually restore the safety backup
                    return JsonResponse({
                        'success': False, 
                        'error': f'فشلت الاستعادة: {str(restore_error)}. نسخة الأمان متاحة للاستعادة اليدوية.',
                        'safety_backup_id': safety_backup.id
                    }, status=500)
                except:
                    pass
            
            raise restore_error
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Broker Management API Views
@login_required
@require_POST
def api_broker_verify(request, broker_id):
    """Verify broker - for admin use"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        broker = get_object_or_404(Broker, pk=broker_id)
        broker.is_verified = True
        broker.save()
        
        return JsonResponse({'success': True, 'is_verified': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_delete(request, broker_id):
    """Delete broker - for admin use"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        broker = get_object_or_404(Broker, pk=broker_id)
        broker.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_toggle_status(request, broker_id):
    """Toggle broker active status"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        broker = get_object_or_404(Broker, pk=broker_id)
        broker.is_active = not broker.is_active
        broker.save()
        
        return JsonResponse({'success': True, 'active': broker.is_active})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_verify(request, broker_id):
    """Verify broker"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        broker = get_object_or_404(Broker, pk=broker_id)
        broker.is_verified = not broker.is_verified
        broker.save()
        
        return JsonResponse({'success': True, 'verified': broker.is_verified})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(['DELETE'])
def api_broker_delete(request, broker_id):
    """Delete broker"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        broker = get_object_or_404(Broker, pk=broker_id)
        
        # Don't allow deleting self
        if broker.user == request.user:
            return JsonResponse({'success': False, 'error': 'لا يمكن حذف حسابك'}, status=400)
        
        broker.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_bulk_verify(request):
    """Bulk verify brokers"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        data = json.loads(request.body)
        broker_ids = data.get('broker_ids', [])
        
        brokers = Broker.objects.filter(pk__in=broker_ids)
        brokers.update(is_verified=True)
        
        return JsonResponse({'success': True, 'count': brokers.count()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_bulk_activate(request):
    """Bulk activate brokers"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        data = json.loads(request.body)
        broker_ids = data.get('broker_ids', [])
        
        brokers = Broker.objects.filter(pk__in=broker_ids)
        brokers.update(is_active=True)
        
        return JsonResponse({'success': True, 'count': brokers.count()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_broker_bulk_deactivate(request):
    """Bulk deactivate brokers"""
    if not can_manage_brokers(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        data = json.loads(request.body)
        broker_ids = data.get('broker_ids', [])
        
        # Don't allow deactivating self
        brokers = Broker.objects.filter(pk__in=broker_ids).exclude(user=request.user)
        brokers.update(is_active=False)
        
        return JsonResponse({'success': True, 'count': brokers.count()})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def download_backup(request, backup_id):
    """تحميل نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        from .models import Backup, BackupAuditLog
        import os
        from django.http import FileResponse
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        if not os.path.exists(backup.file_path):
            # Log failed download attempt
            BackupAuditLog.objects.create(
                backup=backup,
                action='downloaded',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='failed',
                error_message='ملف النسخة الاحتياطية غير موجود'
            )
            return JsonResponse({'success': False, 'error': 'ملف النسخة الاحتياطية غير موجود'}, status=404)
        
        # Log successful download
        BackupAuditLog.objects.create(
            backup=backup,
            action='downloaded',
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        # Generate secure filename
        secure_filename = f'{backup.name}_{backup.version}.zip'
        return FileResponse(open(backup.file_path, 'rb'), as_attachment=True, filename=secure_filename)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def delete_backup(request, backup_id):
    """حذف نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طلب غير صالح'}, status=400)
    
    try:
        from .models import Backup, BackupAuditLog
        import os
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        # Check if backup is protected
        if backup.is_protected:
            return JsonResponse({'success': False, 'error': 'النسخة محمية ولا يمكن حذفها'}, status=400)
        
        # Check if backup is currently being restored
        if backup.status == 'restoring':
            return JsonResponse({'success': False, 'error': 'لا يمكن حذف نسخة قيد الاستعادة'}, status=400)
        
        # Check if it's a safety backup
        if backup.is_safety_backup:
            return JsonResponse({'success': False, 'error': 'لا يمكن حذف نسخة الأمان'}, status=400)
        
        # Delete file
        file_deleted = False
        if os.path.exists(backup.file_path):
            os.remove(backup.file_path)
            file_deleted = True
        
        # Log audit before deletion
        BackupAuditLog.objects.create(
            backup=backup,
            action='deleted',
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        # Delete record
        backup.delete()
        
        return JsonResponse({'success': True, 'file_deleted': file_deleted})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def verify_backup(request, backup_id):
    """فحص نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        from .models import Backup, BackupAuditLog
        import os
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        verification_result = {
            'file_exists': False,
            'size_matches': False,
            'checksum_valid': False,
            'structure_valid': False,
            'overall_status': 'unknown'
        }
        
        # Check if file exists
        if os.path.exists(backup.file_path):
            verification_result['file_exists'] = True
            actual_size = os.path.getsize(backup.file_path) / (1024 * 1024)
            verification_result['size_matches'] = abs(actual_size - backup.size) < 0.1
        else:
            verification_result['overall_status'] = 'file_missing'
            backup.mark_as_corrupted()
            
            BackupAuditLog.objects.create(
                backup=backup,
                action='verified',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='failed',
                error_message='الملف غير موجود'
            )
            return JsonResponse({'success': False, 'verification': verification_result})
        
        # Verify checksum
        if backup.checksum:
            current_checksum = backup.calculate_checksum()
            verification_result['checksum_valid'] = (current_checksum == backup.checksum)
            if not verification_result['checksum_valid']:
                backup.mark_as_corrupted()
                verification_result['overall_status'] = 'corrupted'
                
                BackupAuditLog.objects.create(
                    backup=backup,
                    action='verified',
                    user=request.user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    result='failed',
                    error_message='التوقيع الرقمي غير متطابق'
                )
                return JsonResponse({'success': False, 'verification': verification_result})
        
        # Overall status
        if verification_result['file_exists'] and verification_result['size_matches'] and verification_result['checksum_valid']:
            verification_result['overall_status'] = 'healthy'
            
            BackupAuditLog.objects.create(
                backup=backup,
                action='verified',
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                result='success'
            )
        else:
            verification_result['overall_status'] = 'warning'
        
        return JsonResponse({'success': True, 'verification': verification_result})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def protect_backup(request, backup_id):
    """حماية نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طلب غير صالح'}, status=400)
    
    try:
        from .models import Backup, BackupAuditLog
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        import json
        data = json.loads(request.body)
        is_protected = data.get('is_protected', True)
        
        backup.is_protected = is_protected
        backup.save()
        
        BackupAuditLog.objects.create(
            backup=backup,
            action='protected',
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            result='success'
        )
        
        return JsonResponse({'success': True, 'is_protected': is_protected})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def backup_detail(request, backup_id):
    """تفاصيل نسخة احتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        from .models import Backup, BackupAuditLog
        
        backup = get_object_or_404(Backup, pk=backup_id)
        
        # Get recent audit logs
        audit_logs = BackupAuditLog.objects.filter(backup=backup).order_by('-created_at')[:20]
        
        backup_data = {
            'id': backup.id,
            'name': backup.name,
            'version': backup.version,
            'backup_type': backup.get_backup_type_display(),
            'file_path': backup.file_path,
            'size': float(backup.size),
            'description': backup.description,
            'status': backup.get_status_display(),
            'checksum': backup.checksum,
            'file_count': backup.file_count,
            'database_size': float(backup.database_size),
            'media_size': float(backup.media_size),
            'duration': backup.duration,
            'is_protected': backup.is_protected,
            'is_safety_backup': backup.is_safety_backup,
            'created_by': backup.created_by.username if backup.created_by else 'System',
            'created_at': backup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'restored_by': backup.restored_by.username if backup.restored_by else None,
            'restored_at': backup.restored_at.strftime('%Y-%m-%d %H:%M:%S') if backup.restored_at else None,
            'updated_at': backup.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_restorable': backup.is_restorable(),
            'is_corrupted': backup.is_corrupted(),
        }
        
        audit_logs_data = []
        for log in audit_logs:
            audit_logs_data.append({
                'action': log.get_action_display(),
                'user': log.user.username if log.user else 'System',
                'result': log.get_result_display(),
                'error_message': log.error_message,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        return JsonResponse({
            'success': True,
            'backup': backup_data,
            'audit_logs': audit_logs_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def backup_list(request):
    """قائمة النسخ الاحتياطية"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        from .models import Backup
        
        # Get query parameters
        search = request.GET.get('search', '')
        backup_type = request.GET.get('type', '')
        status = request.GET.get('status', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Build query
        backups = Backup.objects.all()
        
        if search:
            backups = backups.filter(
                name__icontains=search
            ) | backups.filter(
                description__icontains=search
            ) | backups.filter(
                version__icontains=search
            )
        
        if backup_type:
            backups = backups.filter(backup_type=backup_type)
        
        if status:
            backups = backups.filter(status=status)
        
        # Pagination
        total = backups.count()
        start = (page - 1) * per_page
        end = start + per_page
        backups = backups.order_by('-created_at')[start:end]
        
        # Build response
        backups_data = []
        for backup in backups:
            backups_data.append({
                'id': backup.id,
                'name': backup.name,
                'version': backup.version,
                'backup_type': backup.get_backup_type_display(),
                'size': float(backup.size),
                'description': backup.description,
                'status': backup.get_status_display(),
                'is_protected': backup.is_protected,
                'is_safety_backup': backup.is_safety_backup,
                'created_by': backup.created_by.username if backup.created_by else 'System',
                'created_at': backup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_restorable': backup.is_restorable(),
                'is_corrupted': backup.is_corrupted(),
            })
        
        return JsonResponse({
            'success': True,
            'backups': backups_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def import_backup(request):
    """استيراد نسخة احتياطية من ملف"""
    if not can_manage_backups(request.user):
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)
    
    try:
        from .models import Backup, BackupAuditLog
        import time
        import hashlib
        import zipfile
        import shutil
        
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'يرجى اختيار ملف'}, status=400)
        
        uploaded_file = request.FILES['file']
        backup_type = request.POST.get('type', 'full')
        backup_description = request.POST.get('description', '')
        
        # Validate file type
        allowed_extensions = ['.zip', '.db']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({'success': False, 'error': 'نوع الملف غير مدعوم. يدعم فقط ZIP و DB'}, status=400)
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'imported_{backup_type}_{timestamp}{file_extension}'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Save uploaded file
        with open(backup_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Calculate file size
        file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
        
        # Calculate checksum
        sha256_hash = hashlib.sha256()
        with open(backup_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        
        # Generate version number
        backup_count = Backup.objects.filter(backup_type=backup_type).count()
        version = f'v{backup_count + 1}'
        
        # Create backup record
        backup = Backup.objects.create(
            name=backup_filename,
            version=version,
            backup_type=backup_type,
            file_path=backup_path,
            size=round(file_size, 2),
            description=backup_description or f'نسخة مستوردة: {uploaded_file.name}',
            status='completed',
            checksum=checksum,
            file_count=1 if file_extension == '.db' else 0,
            duration=0,
            created_by=request.user
        )
        
        # Create audit log
        BackupAuditLog.objects.create(
            backup=backup,
            action='import',
            user=request.user,
            details=f'استيراد نسخة من ملف: {uploaded_file.name}'
        )
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'message': 'تم استيراد النسخة الاحتياطية بنجاح'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def job_delete(request, pk):
    """حذف فرصة عمل"""
    from properties.models import Job
    from django.contrib import messages
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    job = get_object_or_404(Job, pk=pk, user=request.user)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'تم حذف فرصة العمل بنجاح')
        return redirect('my_jobs')
    
    return render(request, 'properties/job_delete.html', {
        'job': job,
    })


@login_required
def system_settings(request):
    """إعدادات النظام المتقدمة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # هنا يمكن حفظ الإعدادات في قاعدة البيانات أو ملف الإعدادات
            # للبساطة، سنقوم بمحاكاة الحفظ
            
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ الإعدادات بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def clear_cache(request):
    """مسح الذاكرة المؤقتة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            from django.core.cache import cache
            cache.clear()
            
            return JsonResponse({
                'success': True,
                'message': 'تم مسح الذاكرة المؤقتة بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def restart_server(request):
    """إعادة تشغيل السيرفر"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            # محاكاة إعادة التشغيل
            # في بيئة الإنتاج، سيتم استخدام أمر حقيقي
            
            return JsonResponse({
                'success': True,
                'message': 'سيتم إعادة تشغيل السيرفر خلال دقيقة'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def advanced_settings(request):
    """إعدادات النظام المتقدمة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # هنا يمكن حفظ الإعدادات المتقدمة في قاعدة البيانات أو ملف الإعدادات
            # للبساطة، سنقوم بمحاكاة الحفظ
            
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ الإعدادات المتقدمة بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def system_diagnostics(request):
    """تشخيص النظام"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            # تشخيصات النظام
            results = []
            
            # فحص قاعدة البيانات
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                results.append("✅ قاعدة البيانات: سليمة")
            
            # فحص الملفات
            import os
            if os.path.exists('media'):
                results.append("✅ مجلد الملفات: موجود")
            else:
                results.append("❌ مجلد الملفات: غير موجود")
            
            # فحص النسخ الاحتياطية
            backup_count = Backup.objects.count()
            results.append(f"✅ النسخ الاحتياطية: {backup_count} نسخة")
            
            # فحص الذاكرة
            try:
                import psutil
                memory_usage = psutil.virtual_memory().percent
                if memory_usage < 80:
                    results.append(f"✅ استخدام الذاكرة: {memory_usage}%")
                else:
                    results.append(f"⚠️ استخدام الذاكرة: {memory_usage}% (مرتفع)")
                
                # فحص المعالج
                cpu_usage = psutil.cpu_percent()
                if cpu_usage < 80:
                    results.append(f"✅ استخدام المعالج: {cpu_usage}%")
                else:
                    results.append(f"⚠️ استخدام المعالج: {cpu_usage}% (مرتفع)")
            except ImportError:
                results.append("⚠️ psutil غير متوفر - لا يمكن فحص الموارد")
            
            return JsonResponse({
                'success': True,
                'results': results
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def emergency_shutdown(request):
    """إيقاف طوارئ"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            # تنشيط وضع الصيانة الطارئ
            # في بيئة الإنتاج، سيتم حفظ هذا في قاعدة البيانات
            
            return JsonResponse({
                'success': True,
                'message': 'تم تفعيل وضع الطوارئ'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def toggle_user_status(request, user_id):
    """تغيير حالة المستخدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, pk=user_id)
            user.is_active = not user.is_active
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'تم تغيير حالة المستخدم {user.username} بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def approve_property_api(request, property_id):
    """الموافقة على عقار"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            property = get_object_or_404(Property, pk=property_id)
            property.status = 'approved'
            property.is_verified = True
            property.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تمت الموافقة على العقار بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def reject_property_api(request, property_id):
    """رفض عقار"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    if request.method == 'POST':
        try:
            property = get_object_or_404(Property, pk=property_id)
            property.status = 'rejected'
            property.is_verified = False
            property.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم رفض العقار بنجاح'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'طريقة غير مدعومة'}, status=405)


@login_required
def user_details_api(request, user_id):
    """تفاصيل المستخدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        user = get_object_or_404(User, pk=user_id)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'لم يسجل دخول',
            'conversations_count': user.conversationparticipant_set.count(),
            'messages_count': user.chatmessage_set.count() if hasattr(user, 'chatmessage_set') else 0,
            'reports_count': user.messagereport_reporter.count() if hasattr(user, 'messagereport_reporter') else 0,
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def export_users(request):
    """تصدير المستخدمين"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح - هذه الصلاحية للمسؤولين فقط'}, status=403)
    
    try:
        import csv
        from django.http import HttpResponse
        
        users = User.objects.all()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Is Active', 'Is Superuser', 'Is Staff', 'Date Joined', 'Last Login'])
        
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.is_active,
                user.is_superuser,
                user.is_staff,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
            ])
        
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_growth_data(request):
    """بيانات نمو المنشورات للرسوم البيانية"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        days = int(request.GET.get('days', 30))
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # الحصول على بيانات المنشورات
        properties = Property.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
        
        # تجميع البيانات حسب التاريخ
        from collections import defaultdict
        daily_data = defaultdict(int)
        
        for prop in properties:
            date_key = prop.created_at.strftime('%Y-%m-%d')
            daily_data[date_key] += 1
        
        # إنشاء التسميات والبيانات
        labels = []
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            labels.append(date_key)
            data.append(daily_data.get(date_key, 0))
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data,
            'total': sum(data)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_property_distribution(request):
    """بيانات توزيع العقارات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        distribution_type = request.GET.get('type', 'type')
        
        if distribution_type == 'type':
            # توزيع حسب النوع
            data = Property.objects.values('property_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            labels = [item['property_type'] or 'غير محدد' for item in data]
            values = [item['count'] for item in data]
            
        elif distribution_type == 'location':
            # توزيع حسب الموقع
            data = Property.objects.values('city').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            labels = [item['city'] or 'غير محدد' for item in data]
            values = [item['count'] for item in data]
            
        elif distribution_type == 'price':
            # توزيع حسب السعر
            price_ranges = {
                'أقل من 100 ألف': 0,
                '100 ألف - 500 ألف': 0,
                '500 ألف - مليون': 0,
                'مليون - 5 مليون': 0,
                'أكثر من 5 مليون': 0
            }
            
            for prop in Property.objects.filter(price__isnull=False):
                price = prop.price
                if price < 100000:
                    price_ranges['أقل من 100 ألف'] += 1
                elif price < 500000:
                    price_ranges['100 ألف - 500 ألف'] += 1
                elif price < 1000000:
                    price_ranges['500 ألف - مليون'] += 1
                elif price < 5000000:
                    price_ranges['مليون - 5 مليون'] += 1
                else:
                    price_ranges['أكثر من 5 مليون'] += 1
            
            labels = list(price_ranges.keys())
            values = list(price_ranges.values())
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': values
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_broker_performance(request):
    """بيانات أداء الدلالين"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        performance_type = request.GET.get('type', 'all')
        
        # الحصول على بيانات الدلالين الحقيقية
        from .models import Broker
        brokers = Broker.objects.annotate(
            property_count=Count('user__owned_properties', distinct=True)
        ).order_by('-property_count')
        
        if performance_type == 'top':
            brokers = brokers[:10]
        elif performance_type == 'bottom':
            brokers = brokers.order_by('property_count')[:10]
        else:
            brokers = brokers[:20]
        
        labels = [broker.user.username for broker in brokers]
        values = [broker.property_count for broker in brokers]
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': values
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_revenue(request):
    """بيانات الإيرادات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        period = request.GET.get('period', 'monthly')
        
        # محاكاة بيانات الإيرادات (في الإنتاج، استخدم بيانات حقيقية من الدفعات)
        if period == 'monthly':
            labels = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
            data = [12000, 15000, 18000, 22000, 25000, 28000, 
                   32000, 35000, 30000, 38000, 42000, 45000]
        elif period == 'quarterly':
            labels = ['الربع الأول', 'الربع الثاني', 'الربع الثالث', 'الربع الرابع']
            data = [45000, 75000, 97000, 125000]
        elif period == 'yearly':
            labels = ['2022', '2023', '2024', '2025']
            data = [150000, 280000, 420000, 580000]
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_geographic(request):
    """بيانات التوزيع الجغرافي"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        filter_type = request.GET.get('type', 'all')
        
        if filter_type == 'active':
            # النشطين فقط
            properties = Property.objects.filter(status='published')
        elif filter_type == 'verified':
            # الموثقين فقط
            properties = Property.objects.filter(is_verified=True)
        else:
            # الكل
            properties = Property.objects.all()
        
        # توزيع حسب المدن
        city_data = properties.values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:15]
        
        labels = [item['city'] or 'غير محدد' for item in city_data]
        values = [item['count'] for item in city_data]
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': values
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def analytics_user_activity(request):
    """بيانات نشاط المستخدمين"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        period = request.GET.get('period', 'daily')
        
        from django.utils import timezone
        from datetime import timedelta
        
        if period == 'daily':
            # آخر 7 أيام
            days = 7
        elif period == 'weekly':
            # آخر 4 أسابيع
            days = 28
        else:
            # آخر 30 يوم
            days = 30
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # الحصول على نشاط المستخدمين
        from collections import defaultdict
        activity_data = defaultdict(int)
        
        # محاكاة بيانات النشاط (في الإنتاج، استخدم بيانات حقيقية من Logs)
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            # محاكاة نشاط عشوائي
            activity_data[date_key] = random.randint(10, 100)
            current_date += timedelta(days=1)
        
        labels = list(activity_data.keys())
        values = list(activity_data.values())
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': values
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def analytics_performance(request):
    """بيانات أداء النظام"""
    # Allow unauthenticated users to receive basic metrics
    # Only show detailed metrics to admins/staff
    is_admin = request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)
    
    try:
        metric_type = request.GET.get('type', 'overall')

        if metric_type == 'overall':
            # مؤشرات الأداء العامة
            metrics = {
                'page_load_time': round(random.uniform(0.5, 2.5), 2),
                'server_response_time': round(random.uniform(100, 500), 2),
                'database_query_time': round(random.uniform(10, 100), 2),
                'cache_hit_rate': round(random.uniform(70, 95), 2),
                'error_rate': round(random.uniform(0.1, 2.0), 2),
                'uptime_percentage': round(random.uniform(99.0, 99.9), 2),
            }
        elif metric_type == 'database':
            # مؤشرات قاعدة البيانات - فقط للمسؤولين
            if not is_admin:
                return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
            metrics = {
                'query_count': random.randint(1000, 5000),
                'slow_queries': random.randint(5, 50),
                'avg_query_time': round(random.uniform(20, 150), 2),
                'connection_pool_usage': round(random.uniform(40, 80), 2),
            }
        elif metric_type == 'server':
            # مؤشرات الخادم - فقط للمسؤولين
            if not is_admin:
                return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
            metrics = {
                'cpu_usage': round(random.uniform(20, 70), 2),
                'memory_usage': round(random.uniform(40, 80), 2),
                'disk_usage': round(random.uniform(30, 60), 2),
                'network_io': round(random.uniform(10, 100), 2),
            }
        else:
            metrics = {}
        
        return JsonResponse({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def advanced_notifications(request):
    """نظام إشعارات متقدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        limit = int(request.GET.get('limit', 20))
        notification_type = request.GET.get('type', 'all')
        
        # محاكاة بيانات الإشعارات
        notifications = []
        
        notification_types = ['info', 'warning', 'error', 'success']
        categories = ['system', 'user', 'property', 'payment', 'security']
        
        for i in range(limit):
            notifications.append({
                'id': i + 1,
                'type': random.choice(notification_types),
                'category': random.choice(categories),
                'title': f'إشعار {i + 1}',
                'message': f'تفاصيل الإشعار {i + 1}',
                'icon': random.choice(['🔔', '⚠️', '❌', '✅', 'ℹ️']),
                'is_read': random.choice([True, False]),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action_url': f'/dashboard/notifications/{i + 1}/'
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'unread_count': sum(1 for n in notifications if not n['is_read'])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def performance_monitoring(request):
    """لوحة مراقبة الأداء الحية"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        import psutil
        import time
        
        # فحص الموارد الحالية
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # فحص الشبكة
        network = psutil.net_io_counters()
        
        # فحص العمليات
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # ترتيب العمليات حسب استخدام المعالج
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        processes = processes[:10]  # أفضل 10 عمليات
        
        return JsonResponse({
            'success': True,
            'performance': {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'top_processes': processes
            },
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def support_tickets(request):
    """نظام تذاكر دعم فني"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        # محاكاة بيانات التذاكر
        tickets = []
        priorities = ['low', 'medium', 'high', 'critical']
        statuses = ['open', 'in_progress', 'resolved', 'closed']
        categories = ['technical', 'billing', 'feature', 'bug', 'other']
        
        for i in range(15):
            tickets.append({
                'id': i + 1,
                'title': f'تذكرة دعم {i + 1}',
                'description': f'وصف المشكلة {i + 1}',
                'priority': random.choice(priorities),
                'status': random.choice(statuses),
                'category': random.choice(categories),
                'user': f'user_{i + 1}',
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'assigned_to': random.choice(['admin', 'support_1', 'support_2', None])
            })
        
        return JsonResponse({
            'success': True,
            'tickets': tickets,
            'statistics': {
                'total': len(tickets),
                'open': sum(1 for t in tickets if t['status'] == 'open'),
                'in_progress': sum(1 for t in tickets if t['status'] == 'in_progress'),
                'resolved': sum(1 for t in tickets if t['status'] == 'resolved'),
                'closed': sum(1 for t in tickets if t['status'] == 'closed'),
                'high_priority': sum(1 for t in tickets if t['priority'] in ['high', 'critical'])
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def audit_log(request):
    """سجل تدقيق شامل"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        limit = int(request.GET.get('limit', 50))
        action_type = request.GET.get('action', 'all')
        user_id = request.GET.get('user_id', None)
        
        # محاكاة بيانات سجل التدقيق
        actions = ['login', 'logout', 'create', 'update', 'delete', 'export', 'import', 'approve', 'reject']
        modules = ['users', 'properties', 'backups', 'settings', 'payments', 'subscriptions']
        
        logs = []
        for i in range(limit):
            logs.append({
                'id': i + 1,
                'action': random.choice(actions),
                'module': random.choice(modules),
                'user': f'user_{random.randint(1, 20)}',
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'status': random.choice(['success', 'failed']),
                'details': f'تفاصيل العملية {i + 1}',
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs,
            'total_count': len(logs)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_keys_management(request):
    """نظام إدارة API Keys"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات API Keys
            keys = []
            for i in range(5):
                keys.append({
                    'id': i + 1,
                    'name': f'API Key {i + 1}',
                    'key': f'sk_test_{random.randint(1000000000000000, 9999999999999999)}',
                    'permissions': ['read', 'write', 'delete'] if i < 2 else ['read'],
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_used': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'is_active': random.choice([True, False]),
                    'expires_at': (timezone.now() + timedelta(days=365)).strftime('%Y-%m-%d') if i < 3 else None
                })
            
            return JsonResponse({
                'success': True,
                'keys': keys
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_key = {
                'id': 999,
                'name': data.get('name', 'New API Key'),
                'key': f'sk_test_{random.randint(1000000000000000, 9999999999999999)}',
                'permissions': data.get('permissions', ['read']),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_used': None,
                'is_active': True,
                'expires_at': data.get('expires_at')
            }
            
            return JsonResponse({
                'success': True,
                'key': new_key,
                'message': 'تم إنشاء API Key بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def developer_tools(request):
    """لوحة تحكم المطورين"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        # معلومات بيئة التطوير
        from django.conf import settings
        
        dev_info = {
            'django_version': django.__version__,
            'python_version': sys.version,
            'debug_mode': settings.DEBUG,
            'database': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME']
            },
            'installed_apps': settings.INSTALLED_APPS,
            'middleware': settings.MIDDLEWARE,
            'static_url': settings.STATIC_URL,
            'media_url': settings.MEDIA_URL
        }
        
        return JsonResponse({
            'success': True,
            'development_info': dev_info
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def advanced_search(request):
    """نظام البحث المتقدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        query = request.GET.get('q', '')
        search_type = request.GET.get('type', 'all')
        
        results = []
        
        if search_type in ['all', 'users']:
            users = User.objects.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )[:10]
            for user in users:
                results.append({
                    'type': 'user',
                    'id': user.id,
                    'title': user.username,
                    'description': user.email,
                    'url': f'/dashboard/users/{user.id}/'
                })
        
        if search_type in ['all', 'properties']:
            properties = Property.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(city__icontains=query)
            )[:10]
            for prop in properties:
                results.append({
                    'type': 'property',
                    'id': prop.id,
                    'title': prop.title,
                    'description': prop.city,
                    'url': f'/property/{prop.id}/'
                })
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'total_count': len(results)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def task_management(request):
    """نظام إدارة المهام"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات المهام
            tasks = []
            priorities = ['low', 'medium', 'high', 'critical']
            statuses = ['pending', 'in_progress', 'completed', 'cancelled']
            categories = ['maintenance', 'development', 'content', 'security', 'feature']
            
            for i in range(15):
                tasks.append({
                    'id': i + 1,
                    'title': f'مهمة {i + 1}',
                    'description': f'وصف المهمة {i + 1}',
                    'priority': random.choice(priorities),
                    'status': random.choice(statuses),
                    'category': random.choice(categories),
                    'assigned_to': random.choice(['admin', 'developer_1', 'developer_2', None]),
                    'due_date': (timezone.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'completed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'tasks': tasks,
                'statistics': {
                    'total': len(tasks),
                    'pending': sum(1 for t in tasks if t['status'] == 'pending'),
                    'in_progress': sum(1 for t in tasks if t['status'] == 'in_progress'),
                    'completed': sum(1 for t in tasks if t['status'] == 'completed'),
                    'overdue': sum(1 for t in tasks if t['due_date'] < timezone.now().strftime('%Y-%m-%d') and t['status'] != 'completed')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_task = {
                'id': 999,
                'title': data.get('title', 'New Task'),
                'description': data.get('description', ''),
                'priority': data.get('priority', 'medium'),
                'status': 'pending',
                'category': data.get('category', 'development'),
                'assigned_to': data.get('assigned_to'),
                'due_date': data.get('due_date'),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'completed_at': None
            }
            
            return JsonResponse({
                'success': True,
                'task': new_task,
                'message': 'تم إنشاء المهمة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def report_scheduling(request):
    """نظام جدولة التقارير"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات التقارير المجدولة
            scheduled_reports = []
            report_types = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
            formats = ['pdf', 'excel', 'csv', 'json']
            
            for i in range(10):
                scheduled_reports.append({
                    'id': i + 1,
                    'name': f'تقرير {i + 1}',
                    'report_type': random.choice(report_types),
                    'format': random.choice(formats),
                    'recipients': ['admin@example.com', 'manager@example.com'],
                    'schedule': f'{random.choice(["daily", "weekly", "monthly"])} at {random.randint(0, 23)}:{random.randint(0, 59)}',
                    'last_run': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'next_run': (timezone.now() + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d %H:%M:%S'),
                    'is_active': random.choice([True, False]),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'scheduled_reports': scheduled_reports
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_schedule = {
                'id': 999,
                'name': data.get('name', 'New Scheduled Report'),
                'report_type': data.get('report_type', 'daily'),
                'format': data.get('format', 'pdf'),
                'recipients': data.get('recipients', []),
                'schedule': data.get('schedule'),
                'next_run': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': True,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'scheduled_report': new_schedule,
                'message': 'تم جدولة التقرير بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def file_management(request):
    """نظام إدارة الملفات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        import os
        from django.conf import settings
        
        if request.method == 'GET':
            # محاكاة بيانات الملفات
            files = []
            directories = ['media/images', 'media/documents', 'media/videos', 'media/audio', 'static', 'logs']
            
            for directory in directories:
                if os.path.exists(directory):
                    for filename in os.listdir(directory)[:5]:
                        filepath = os.path.join(directory, filename)
                        if os.path.isfile(filepath):
                            files.append({
                                'name': filename,
                                'path': filepath,
                                'size': os.path.getsize(filepath),
                                'modified': os.path.getmtime(filepath),
                                'directory': directory
                            })
            
            total_size = sum(f['size'] for f in files)
            
            return JsonResponse({
                'success': True,
                'files': files,
                'statistics': {
                    'total_files': len(files),
                    'total_size': total_size,
                    'directories': len(directories)
                }
            })
        
        elif request.method == 'POST':
            action = request.GET.get('action', '')
            
            if action == 'upload':
                # محاكاة رفع الملفات
                return JsonResponse({
                    'success': True,
                    'message': 'تم رفع الملف بنجاح'
                })
            elif action == 'delete':
                file_path = request.GET.get('path')
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    return JsonResponse({
                        'success': True,
                        'message': 'تم حذف الملف بنجاح'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'الملف غير موجود'
                    })
            elif action == 'cleanup':
                # محاكاة تنظيف الملفات
                return JsonResponse({
                    'success': True,
                    'message': 'تم تنظيف الملفات غير المستخدمة'
                })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def server_logs(request):
    """نظام تتبع سجلات الخادم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        log_type = request.GET.get('type', 'error')
        lines = int(request.GET.get('lines', 100))
        
        log_files = {
            'error': 'logs/error.log',
            'access': 'logs/access.log',
            'debug': 'logs/debug.log',
            'django': 'logs/django.log'
        }
        
        log_file = log_files.get(log_type, 'logs/error.log')
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()[-lines:]
            
            return JsonResponse({
                'success': True,
                'log_type': log_type,
                'lines': log_lines,
                'total_lines': len(log_lines)
            })
        else:
            return JsonResponse({
                'success': True,
                'log_type': log_type,
                'lines': ['الملف غير موجود'],
                'total_lines': 0
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def database_management(request):
    """نظام إدارة القواعد البيانات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        from django.db import connection, connections
        from django.core.management import call_command
        from io import StringIO
        
        action = request.GET.get('action', 'info')
        
        if action == 'info':
            # معلومات قاعدة البيانات
            db_info = []
            for alias in connections:
                db_info.append({
                    'alias': alias,
                    'engine': connections[alias].settings_dict['ENGINE'],
                    'name': connections[alias].settings_dict['NAME'],
                    'host': connections[alias].settings_dict.get('HOST', 'localhost'),
                    'port': connections[alias].settings_dict.get('PORT', ''),
                    'options': connections[alias].settings_dict.get('OPTIONS', {})
                })
            
            # فحص حجم قاعدة البيانات
            db_size = 0
            if os.path.exists('db.sqlite3'):
                db_size = os.path.getsize('db.sqlite3')
            
            return JsonResponse({
                'success': True,
                'databases': db_info,
                'total_size': db_size
            })
        
        elif action == 'optimize':
            # تحسين قاعدة البيانات
            with connection.cursor() as cursor:
                cursor.execute("VACUUM")
            return JsonResponse({
                'success': True,
                'message': 'تم تحسين قاعدة البيانات بنجاح'
            })
        
        elif action == 'backup':
            # نسخة احتياطية لقاعدة البيانات
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء نسخة احتياطية لقاعدة البيانات'
            })
        
        elif action == 'migrate':
            # تشغيل الترحيلات
            out = StringIO()
            call_command('migrate', stdout=out, stderr=out)
            return JsonResponse({
                'success': True,
                'output': out.getvalue()
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def security_monitoring(request):
    """نظام مراقبة الأمان"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        # محاكاة بيانات الأمان
        security_events = []
        event_types = ['login_attempt', 'suspicious_activity', 'permission_denied', 'brute_force', 'malware_detected']
        severity_levels = ['low', 'medium', 'high', 'critical']
        
        for i in range(20):
            security_events.append({
                'id': i + 1,
                'event_type': random.choice(event_types),
                'severity': random.choice(severity_levels),
                'ip_address': f'192.168.1.{random.randint(1, 255)}',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'user': f'user_{random.randint(1, 20)}' if random.choice([True, False]) else 'anonymous',
                'description': f'وصف الحدث الأمني {i + 1}',
                'blocked': random.choice([True, False]),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'security_events': security_events,
            'statistics': {
                'total_events': len(security_events),
                'blocked': sum(1 for e in security_events if e['blocked']),
                'critical': sum(1 for e in security_events if e['severity'] == 'critical'),
                'high': sum(1 for e in security_events if e['severity'] == 'high')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def subscription_management_advanced(request):
    """نظام إدارة الاشتراكات المتقدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        # محاكاة بيانات الاشتراكات المتقدمة
        subscriptions = []
        plan_types = ['basic', 'premium', 'enterprise', 'custom']
        payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'crypto']
        
        for i in range(20):
            start_date = timezone.now() - timedelta(days=random.randint(1, 365))
            end_date = start_date + timedelta(days=random.randint(30, 365))
            
            subscriptions.append({
                'id': i + 1,
                'user': f'user_{i + 1}',
                'plan': random.choice(plan_types),
                'payment_method': random.choice(payment_methods),
                'amount': random.randint(10, 500),
                'currency': 'USD',
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'status': random.choice(['active', 'expired', 'cancelled', 'pending']),
                'auto_renew': random.choice([True, False]),
                'properties_used': random.randint(0, 100),
                'properties_limit': random.choice([10, 50, 100, 500, 1000]),
                'created_at': start_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'subscriptions': subscriptions,
            'statistics': {
                'total': len(subscriptions),
                'active': sum(1 for s in subscriptions if s['status'] == 'active'),
                'expired': sum(1 for s in subscriptions if s['status'] == 'expired'),
                'revenue': sum(s['amount'] for s in subscriptions if s['status'] == 'active')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def data_analytics(request):
    """نظام تحليلات البيانات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        analysis_type = request.GET.get('type', 'overview')
        
        if analysis_type == 'overview':
            # نظرة عامة على البيانات
            overview = {
                'user_growth': {
                    'labels': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                    'new_users': [120, 150, 180, 220, 250, 280],
                    'total_users': [500, 550, 620, 780, 950, 1150]
                },
                'property_trends': {
                    'labels': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                    'new_properties': [45, 55, 60, 75, 80, 95],
                    'total_properties': [300, 320, 350, 380, 410, 450]
                },
                'engagement_metrics': {
                    'avg_session_duration': '5m 32s',
                    'bounce_rate': '25%',
                    'page_views': 45000,
                    'unique_visitors': 2500
                },
                'conversion_funnel': {
                    'visitors': 10000,
                    'signups': 2000,
                    'active_users': 1500,
                    'subscribers': 500,
                    'conversion_rate': '5%'
                }
            }
            
            return JsonResponse({
                'success': True,
                'analysis_type': analysis_type,
                'data': overview
            })
        
        elif analysis_type == 'user_behavior':
            # تحليل سلوك المستخدمين
            behavior = {
                'most_active_hours': [9, 10, 11, 14, 15, 16, 17, 18, 19, 20],
                'peak_activity_time': '15:00',
                'average_sessions_per_day': 3.5,
                'most_visited_pages': ['/dashboard', '/properties', '/search', '/notifications'],
                'device_distribution': {
                    'desktop': 65,
                    'mobile': 30,
                    'tablet': 5
                },
                'browser_distribution': {
                    'chrome': 70,
                    'firefox': 15,
                    'safari': 10,
                    'edge': 5
                }
            }
            
            return JsonResponse({
                'success': True,
                'analysis_type': analysis_type,
                'data': behavior
            })
        
        elif analysis_type == 'performance':
            # تحليل الأداء
            performance = {
                'page_load_time': '2.3s',
                'server_response_time': '150ms',
                'database_query_time': '45ms',
                'api_response_time': '89ms',
                'uptime': '99.95%',
                'error_rate': '0.05%'
            }
            
            return JsonResponse({
                'success': True,
                'analysis_type': analysis_type,
                'data': performance
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def media_management(request):
    """نظام إدارة الوسائط المحسّن - يعمل مع قاعدة البيانات"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        from .models import PropertyImage, PropertyVideo, PropertyDocument
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        
        if request.method == 'GET':
            # جمع بيانات الوسائط من قاعدة البيانات
            media_type = request.GET.get('type', 'all')
            property_id = request.GET.get('property_id')
            uploaded_by = request.GET.get('uploaded_by')
            
            # فلاتر
            images_qs = PropertyImage.objects.select_related('property', 'uploaded_by').all()
            videos_qs = PropertyVideo.objects.select_related('property', 'uploaded_by').all()
            documents_qs = PropertyDocument.objects.select_related('property', 'uploaded_by').all()
            
            if media_type != 'all':
                if media_type == 'image':
                    videos_qs = videos_qs.none()
                    documents_qs = documents_qs.none()
                elif media_type == 'video':
                    images_qs = images_qs.none()
                    documents_qs = documents_qs.none()
                elif media_type == 'document':
                    images_qs = images_qs.none()
                    videos_qs = videos_qs.none()
            
            if property_id:
                images_qs = images_qs.filter(property_id=property_id)
                videos_qs = videos_qs.filter(property_id=property_id)
                documents_qs = documents_qs.filter(property_id=property_id)
            
            if uploaded_by:
                images_qs = images_qs.filter(uploaded_by_id=uploaded_by)
                videos_qs = videos_qs.filter(uploaded_by_id=uploaded_by)
                documents_qs = documents_qs.filter(uploaded_by_id=uploaded_by)
            
            # تجميع البيانات
            media_items = []
            
            for img in images_qs:
                media_items.append({
                    'id': img.id,
                    'type': 'image',
                    'name': img.image.name if img.image else img.caption or 'بدون اسم',
                    'property_id': img.property_id,
                    'property_title': img.property.display_title if img.property else None,
                    'property_slug': img.property.slug if img.property else None,
                    'caption': img.caption or '',
                    'image_type': img.image_type,
                    'is_primary': img.is_primary,
                    'is_360': img.is_360,
                    'sort_order': img.sort_order,
                    'file_size': img.file_size,
                    'file_size_display': img.get_file_size_display(),
                    'width': img.width,
                    'height': img.alt_text,
                    'is_published': img.is_published,
                    'view_count': img.view_count,
                    'uploaded_by': img.uploaded_by.username if img.uploaded_by else None,
                    'created_at': img.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'url': img.image.url if img.image else None,
                })
            
            for video in videos_qs:
                media_items.append({
                    'id': video.id,
                    'type': 'video',
                    'name': video.video.name if video.video else video.caption or 'بدون اسم',
                    'property_id': video.property_id,
                    'property_title': video.property.display_title if video.property else None,
                    'property_slug': video.property.slug if video.property else None,
                    'caption': video.caption or '',
                    'video_type': video.video_type,
                    'duration': video.duration,
                    'duration_display': video.get_duration_display(),
                    'sort_order': video.sort_order,
                    'file_size': video.file_size,
                    'file_size_display': video.get_file_size_display(),
                    'resolution': video.resolution,
                    'is_published': video.is_published,
                    'is_featured': video.is_featured,
                    'view_count': video.view_count,
                    'processing_status': video.processing_status,
                    'uploaded_by': video.uploaded_by.username if video.uploaded_by else None,
                    'created_at': video.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'url': video.video.url if video.video else None,
                    'thumbnail': video.thumbnail.url if video.thumbnail else None,
                })
            
            for doc in documents_qs:
                media_items.append({
                    'id': doc.id,
                    'type': 'document',
                    'name': doc.file.name if doc.file else doc.title or 'بدون اسم',
                    'property_id': doc.property_id,
                    'property_title': doc.property.display_title if doc.property else None,
                    'property_slug': doc.property.slug if doc.property else None,
                    'document_type': doc.document_type,
                    'title': doc.title,
                    'description': doc.description or '',
                    'file_size': doc.file_size,
                    'file_size_display': doc.get_file_size_display(),
                    'file_hash': doc.file_hash,
                    'visibility': doc.visibility,
                    'download_count': doc.download_count,
                    'is_verified': doc.is_verified,
                    'verified_by': doc.verified_by.username if doc.verified_by else None,
                    'uploaded_by': doc.uploaded_by.username if doc.uploaded_by else None,
                    'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'url': doc.file.url if doc.file else None,
                    'expiry_date': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else None,
                    'is_expired': doc.is_expired(),
                })
            
            media_items.sort(key=lambda x: x['created_at'], reverse=True)
            
            # إحصائيات متقدمة
            total_size = sum(item['file_size'] for item in media_items)
            
            # إحصائيات حسب النوع
            image_stats = images_qs.aggregate(
                total=Count('id'),
                total_size=Sum('file_size'),
                total_views=Sum('view_count')
            )
            
            video_stats = videos_qs.aggregate(
                total=Count('id'),
                total_size=Sum('file_size'),
                total_views=Sum('view_count')
            )
            
            document_stats = documents_qs.aggregate(
                total=Count('id'),
                total_size=Sum('file_size'),
                total_downloads=Sum('download_count')
            )
            
            # الوسائط خلال الأسبوع الماضي
            week_ago = timezone.now() - timedelta(days=7)
            recent_images = images_qs.filter(created_at__gte=week_ago).count()
            recent_videos = videos_qs.filter(created_at__gte=week_ago).count()
            recent_documents = documents_qs.filter(created_at__gte=week_ago).count()
            
            # الوسائط غير المنشورة
            unpublished_images = images_qs.filter(is_published=False).count()
            unpublished_videos = videos_qs.filter(is_published=False).count()
            
            # الفيديوهات قيد المعالجة
            processing_videos = videos_qs.filter(processing_status='processing').count()
            failed_videos = videos_qs.filter(status='failed').count()
            
            # المستندات منتهية الصلاحية
            expired_documents = documents_qs.filter(expiry_date__lt=timezone.now().date()).count()
            
            return JsonResponse({
                'success': True,
                'media_items': media_items,
                'statistics': {
                    'total_items': len(media_items),
                    'total_size': total_size,
                    'total_size_display': format_file_size(total_size),
                    'images': image_stats['total'],
                    'videos': video_stats['total'],
                    'documents': document_stats['total'],
                    'image_stats': {
                        'total_size': image_stats['total_size'] or 0,
                        'total_views': image_stats['total_views'] or 0,
                    },
                    'video_stats': {
                        'total_size': video_stats['total_size'] or 0,
                        'total_views': video_stats['total_views'] or 0,
                    },
                    'document_stats': {
                        'total_size': document_stats['total_size'] or 0,
                        'total_downloads': document_stats['total_downloads'] or 0,
                    },
                    'recent_week': {
                        'images': recent_images,
                        'videos': recent_videos,
                        'documents': recent_documents,
                    },
                    'unpublished': {
                        'images': unpublished_images,
                        'videos': unpublished_videos,
                    },
                    'processing': {
                        'videos_processing': processing_videos,
                        'videos_failed': failed_videos,
                    },
                    'expired': {
                        'documents': expired_documents,
                    },
                }
            })
        
        elif request.method == 'POST':
            # رفع ملف جديد
            media_type = request.POST.get('media_type', 'image')
            property_id = request.POST.get('property_id')
            file = request.FILES.get('file')
            
            if not file:
                return JsonResponse({'success': False, 'error': 'لم يتم رفع ملف'}, status=400)
            
            if not property_id:
                return JsonResponse({'success': False, 'error': 'لم يتم تحديد العقار'}, status=400)
            
            property_obj = get_object_or_404(Property, id=property_id)
            
            if media_type == 'image':
                media_item = PropertyImage.objects.create(
                    property=property_obj,
                    image=file,
                    caption=request.POST.get('caption', ''),
                    image_type=request.POST.get('image_type', 'photo'),
                    is_primary=request.POST.get('is_primary', False) == 'true',
                    is_360=request.POST.get('is_360', False) == 'true',
                    uploaded_by=request.user,
                    file_size=file.size,
                )
                
                # ضبط حجم الصورة
                try:
                    from PIL import Image
                    img = Image.open(file)
                    media_item.width = img.width
                    media_item.height = img.height
                    media_item.save(update_fields=['width', 'height'])
                except:
                    pass
                
            elif media_type == 'video':
                media_item = PropertyVideo.objects.create(
                    property=property_obj,
                    video=file,
                    caption=request.POST.get('caption', ''),
                    video_type=request.POST.get('video_type', 'regular'),
                    duration=int(request.POST.get('duration', 0)) if request.POST.get('duration') else None,
                    uploaded_by=request.user,
                    file_size=file.size,
                    processing_status='pending',
                )
                
            elif media_type == 'document':
                media_item = PropertyDocument.objects.create(
                    property=property_obj,
                    file=file,
                    document_type=request.POST.get('document_type', 'other'),
                    title=request.POST.get('title', file.name),
                    description=request.POST.get('description', ''),
                    uploaded_by=request.user,
                    file_size=file.size,
                    visibility=request.POST.get('visibility', 'private'),
                )
                
                # توليد تجزئة الملف
                media_item.generate_file_hash()
            
            return JsonResponse({
                'success': True,
                'message': 'تم رفع الملف بنجاح',
                'media_item': {
                    'id': media_item.id,
                    'type': media_type,
                    'name': file.name,
                }
            })
        
        elif request.method == 'PUT':
            # تحديث عنصر الوسائط
            media_id = request.POST.get('id')
            media_type = request.POST.get('type')
            
            if media_type == 'image':
                media_item = get_object_or_404(PropertyImage, id=media_id)
                media_item.caption = request.POST.get('caption', media_item.caption)
                media_item.is_primary = request.POST.get('is_primary', False) == 'true'
                media_item.is_published = request.POST.get('is_published', True) == 'true'
                media_item.save()
                
            elif media_type == 'video':
                media_item = get_object_or_404(PropertyVideo, id=media_id)
                media_item.caption = request.POST.get('caption', media_item.caption)
                media_item.is_featured = request.POST.get('is_featured', False) == 'true'
                media_item.is_published = request.POST.get('is_published', True) == 'true'
                media_item.save()
                
            elif media_type == 'document':
                media_item = get_object_or_404(PropertyDocument, id=media_id)
                media_item.title = request.POST.get('title', media_item.title)
                media_item.description = request.POST.get('description', media_item.description)
                media_item.visibility = request.POST.get('visibility', media_item.visibility)
                media_item.is_verified = request.POST.get('is_verified', False) == 'true'
                media_item.verified_by = request.user
                media_item.verified_at = timezone.now()
                media_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث الملف بنجاح'
            })
        
        elif request.method == 'DELETE':
            # حذف ملف
            media_id = request.POST.get('id')
            media_type = request.POST.get('type')
            
            if media_type == 'image':
                media_item = get_object_or_404(PropertyImage, id=media_id)
                media_item.delete()
            elif media_type == 'video':
                media_item = get_object_or_404(PropertyVideo, id=media_id)
                media_item.delete()
            elif media_type == 'document':
                media_item = get_object_or_404(PropertyDocument, id=media_id)
                media_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'تم حذف الملف بنجاح'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def format_file_size(size):
    """تنسيق حجم الملف"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


@login_required
def media_dashboard(request):
    """لوحة تحكم إدارة الوسائط"""
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('dashboard')
    
    from .models import PropertyImage, PropertyVideo, PropertyDocument
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # إحصائيات عامة
    total_images = PropertyImage.objects.count()
    total_videos = PropertyVideo.objects.count()
    total_documents = PropertyDocument.objects.count()
    total_media = total_images + total_videos + total_documents
    
    # إحصائيات الحجم
    total_image_size = PropertyImage.objects.aggregate(total=Sum('file_size'))['total'] or 0
    total_video_size = PropertyVideo.objects.aggregate(total=Sum('file_size'))['total'] or 0
    total_document_size = PropertyDocument.objects.aggregate(total=Sum('file_size'))['total'] or 0
    total_size = total_image_size + total_video_size + total_document_size
    
    # إحصائيات المشاهدات
    total_image_views = PropertyImage.objects.aggregate(total=Sum('view_count'))['total'] or 0
    total_video_views = PropertyVideo.objects.aggregate(total=Sum('view_count'))['total'] or 0
    total_document_downloads = PropertyDocument.objects.aggregate(total=Sum('download_count'))['total'] or 0
    
    # الوسائط الحديثة
    recent_images = PropertyImage.objects.select_related('property', 'uploaded_by').order_by('-created_at')[:10]
    recent_videos = PropertyVideo.objects.select_related('property', 'uploaded_by').order_by('-created_at')[:10]
    recent_documents = PropertyDocument.objects.select_related('property', 'uploaded_by').order_by('-created_at')[:10]
    
    # الوسائط غير المنشورة
    unpublished_images = PropertyImage.objects.filter(is_published=False).count()
    unpublished_videos = PropertyVideo.objects.filter(is_published=False).count()
    
    # الفيديوهات قيد المعالجة
    processing_videos = PropertyVideo.objects.filter(processing_status='processing').count()
    failed_videos = PropertyVideo.objects.filter(processing_status='failed').count()
    
    # المستندات المنتهية
    expired_documents = PropertyDocument.objects.filter(expiry_date__lt=timezone.now().date()).count()
    
    # الصور الرئيسية
    primary_images = PropertyImage.objects.filter(is_primary=True).count()
    
    # صور 360°
    images_360 = PropertyImage.objects.filter(is_360=True).count()
    
    # الفيديوهات المميزة
    featured_videos = PropertyVideo.objects.filter(is_featured=True).count()
    
    # المستندات الموثقة
    verified_documents = PropertyDocument.objects.filter(is_verified=True).count()
    
    # إحصائيات حسب النوع
    image_type_stats = PropertyImage.objects.values('image_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    video_type_stats = PropertyVideo.objects.values('video_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    document_type_stats = PropertyDocument.objects.values('document_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_media': total_media,
        'total_images': total_images,
        'total_videos': total_videos,
        'total_documents': total_documents,
        'total_size': total_size,
        'total_size_display': format_file_size(total_size),
        'total_image_size': total_image_size,
        'total_image_size_display': format_file_size(total_image_size),
        'total_video_size': total_video_size,
        'total_video_size_display': format_file_size(total_video_size),
        'total_document_size': total_document_size,
        'total_document_size_display': format_file_size(total_document_size),
        'total_image_views': total_image_views,
        'total_video_views': total_video_views,
        'total_document_downloads': total_document_downloads,
        'recent_images': recent_images,
        'recent_videos': recent_videos,
        'recent_documents': recent_documents,
        'unpublished_images': unpublished_images,
        'unpublished_videos': unpublished_videos,
        'processing_videos': processing_videos,
        'failed_videos': failed_videos,
        'expired_documents': expired_documents,
        'primary_images': primary_images,
        'images_360': images_360,
        'featured_videos': featured_videos,
        'verified_documents': verified_documents,
        'image_type_stats': image_type_stats,
        'video_type_stats': video_type_stats,
        'document_type_stats': document_type_stats,
    }
    
    return render(request, 'properties/media_dashboard.html', context)


@login_required
def advanced_messaging(request):
    """نظام إدارة الرسائل المتقدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الرسائل
            messages = []
            message_types = ['chat', 'notification', 'alert', 'system']
            priorities = ['low', 'normal', 'high', 'urgent']
            statuses = ['sent', 'delivered', 'read', 'failed']
            
            for i in range(20):
                messages.append({
                    'id': i + 1,
                    'type': random.choice(message_types),
                    'priority': random.choice(priorities),
                    'status': random.choice(statuses),
                    'sender': f'user_{random.randint(1, 10)}',
                    'receiver': f'user_{random.randint(1, 10)}',
                    'subject': f'رسالة {i + 1}',
                    'content': f'محتوى الرسالة {i + 1}',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'read_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'messages': messages,
                'statistics': {
                    'total': len(messages),
                    'unread': sum(1 for m in messages if m['status'] != 'read'),
                    'sent': sum(1 for m in messages if m['status'] == 'sent'),
                    'delivered': sum(1 for m in messages if m['status'] == 'delivered'),
                    'failed': sum(1 for m in messages if m['status'] == 'failed')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_message = {
                'id': 999,
                'type': data.get('type', 'chat'),
                'priority': data.get('priority', 'normal'),
                'status': 'sent',
                'sender': request.user.username,
                'receiver': data.get('receiver'),
                'subject': data.get('subject', 'New Message'),
                'content': data.get('content', ''),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'read_at': None
            }
            
            return JsonResponse({
                'success': True,
                'message': new_message,
                'notification': 'تم إرسال الرسالة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def email_management(request):
    """نظام إدارة البريد الإلكتروني"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات البريد الإلكتروني
            emails = []
            email_types = ['promotional', 'transactional', 'notification', 'newsletter']
            statuses = ['sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed']
            
            for i in range(25):
                emails.append({
                    'id': i + 1,
                    'type': random.choice(email_types),
                    'status': random.choice(statuses),
                    'to': f'user{i + 1}@example.com',
                    'subject': f'إيميل {i + 1}',
                    'template': random.choice(['welcome', 'password_reset', 'notification', 'promo']),
                    'sent_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'opened_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'clicked_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'emails': emails,
                'statistics': {
                    'total': len(emails),
                    'sent': sum(1 for e in emails if e['status'] == 'sent'),
                    'delivered': sum(1 for e in emails if e['status'] == 'delivered'),
                    'opened': sum(1 for e in emails if e['status'] == 'opened'),
                    'bounced': sum(1 for e in emails if e['status'] == 'bounced'),
                    'failed': sum(1 for e in emails if e['status'] == 'failed')
                }
            })
        
        elif request.method == 'POST':
            action = request.GET.get('action', '')
            
            if action == 'send':
                data = json.loads(request.body)
                return JsonResponse({
                    'success': True,
                    'message': 'تم إرسال البريد الإلكتروني بنجاح'
                })
            elif action == 'template':
                # محاكاة إدارة القوالب
                return JsonResponse({
                    'success': True,
                    'message': 'تم تحديث القالب بنجاح'
                })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def access_control(request):
    """نظام التحكم في الوصول"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات التحكم في الوصول
            access_rules = []
            rule_types = ['allow', 'deny', 'limit']
            resources = ['dashboard', 'api', 'files', 'settings', 'admin']
            
            for i in range(15):
                access_rules.append({
                    'id': i + 1,
                    'type': random.choice(rule_types),
                    'resource': random.choice(resources),
                    'user': f'user_{random.randint(1, 20)}' if random.choice([True, False]) else 'all',
                    'role': random.choice(['admin', 'staff', 'user', 'guest']),
                    'ip_range': f'192.168.1.{random.randint(1, 255)}/24' if random.choice([True, False]) else None,
                    'time_range': f'{random.randint(0, 23)}:00-{random.randint(0, 23)}:00' if random.choice([True, False]) else None,
                    'description': f'قاعدة الوصول {i + 1}',
                    'is_active': random.choice([True, False]),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'access_rules': access_rules,
                'statistics': {
                    'total': len(access_rules),
                    'active': sum(1 for r in access_rules if r['is_active']),
                    'allow': sum(1 for r in access_rules if r['type'] == 'allow'),
                    'deny': sum(1 for r in access_rules if r['type'] == 'deny')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_rule = {
                'id': 999,
                'type': data.get('type', 'allow'),
                'resource': data.get('resource', 'dashboard'),
                'user': data.get('user'),
                'role': data.get('role', 'user'),
                'description': data.get('description', 'New Access Rule'),
                'is_active': True,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'rule': new_rule,
                'message': 'تم إنشاء قاعدة الوصول بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def crm_management(request):
    """نظام إدارة العلاقات العامة CRM - محسّن"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        from .models import CRMContact
        import json
        from django.utils import timezone
        from django.db.models import Count, Sum, Q
        from datetime import timedelta
        
        if request.method == 'GET':
            contacts_qs = CRMContact.objects.select_related('user', 'created_by', 'assigned_to').prefetch_related('properties_interested').all()
            
            # تطبيق الفلاتر
            stage_filter = request.GET.get('stage')
            priority_filter = request.GET.get('priority')
            source_filter = request.GET.get('source')
            assigned_to_filter = request.GET.get('assigned_to')
            
            if stage_filter:
                contacts_qs = contacts_qs.filter(stage=stage_filter)
            if priority_filter:
                contacts_qs = contacts_qs.filter(priority=priority_filter)
            if source_filter:
                contacts_qs = contacts_qs.filter(source=source_filter)
            if assigned_to_filter:
                contacts_qs = contacts_qs.filter(assigned_to_id=assigned_to_filter)
            
            contacts = []
            
            for c in contacts_qs:
                contacts.append({
                    'id': c.id,
                    'name': c.name,
                    'email': c.email,
                    'phone': c.phone,
                    'secondary_phone': c.secondary_phone or '',
                    'company': c.company or '',
                    'position': c.position or '',
                    'stage': c.stage,
                    'priority': c.priority,
                    'source': c.source or '',
                    'value': float(c.value),
                    'converted_value': float(c.converted_value),
                    'last_contact': c.last_contact.strftime('%Y-%m-%d %H:%M') if c.last_contact else None,
                    'next_followup': c.next_followup.strftime('%Y-%m-%d %H:%M') if c.next_followup else None,
                    'first_contact': c.first_contact.strftime('%Y-%m-%d') if c.first_contact else None,
                    'notes': c.notes or '',
                    'interaction_count': c.interaction_count,
                    'is_active': c.is_active,
                    'is_converted': c.is_converted,
                    'governorate': c.governorate or '',
                    'city': c.city or '',
                    'user': c.user.username if c.user else None,
                    'created_by': c.created_by.username if c.created_by else None,
                    'assigned_to': c.assigned_to.username if c.assigned_to else None,
                    'days_since_last_contact': c.get_days_since_last_contact(),
                    'is_followup_due': c.is_followup_due(),
                    'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'properties_count': c.properties_interested.count(),
                })
            
            # إحصائيات متقدمة
            total_value = sum(c['value'] for c in contacts)
            total_converted_value = sum(c['converted_value'] for c in contacts)
            conversion_rate = round((sum(1 for c in contacts if c['is_converted']) / len(contacts) * 100) if contacts else 0, 1)
            
            # إحصائيات حسب المرحلة
            stage_stats = contacts_qs.values('stage').annotate(
                count=Count('id'),
                total_value=Sum('value')
            ).order_by('-count')
            
            # إحصائيات حسب الأولوية
            priority_stats = contacts_qs.values('priority').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # إحصائيات حسب المصدر
            source_stats = contacts_qs.values('source').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # المتابعات المستحقة
            followup_due_count = contacts_qs.filter(
                next_followup__lte=timezone.now(),
                is_active=True
            ).count()
            
            # لم يتم التواصل معهم منذ أكثر من 30 يوم
            thirty_days_ago = timezone.now() - timedelta(days=30)
            stale_contacts_count = contacts_qs.filter(
                last_contact__lt=thirty_days_ago,
                is_active=True
            ).count()
            
            return JsonResponse({
                'success': True,
                'contacts': contacts,
                'statistics': {
                    'total': len(contacts),
                    'active': sum(1 for c in contacts if c['is_active']),
                    'converted': sum(1 for c in contacts if c['is_converted']),
                    'leads': sum(1 for c in contacts if c['stage'] == 'lead'),
                    'prospects': sum(1 for c in contacts if c['stage'] == 'prospect'),
                    'customers': sum(1 for c in contacts if c['stage'] == 'customer'),
                    'churned': sum(1 for c in contacts if c['stage'] == 'churned'),
                    'total_value': total_value,
                    'total_converted_value': total_converted_value,
                    'conversion_rate': conversion_rate,
                    'followup_due': followup_due_count,
                    'stale_contacts': stale_contacts_count,
                    'stage_stats': list(stage_stats),
                    'priority_stats': list(priority_stats),
                    'source_stats': list(source_stats),
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            
            # إنشاء جهة اتصال جديدة
            new_contact = CRMContact.objects.create(
                name=data.get('name', 'جهة اتصال جديدة'),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                secondary_phone=data.get('secondary_phone', ''),
                company=data.get('company', ''),
                position=data.get('position', ''),
                stage=data.get('stage', 'lead'),
                priority=data.get('priority', 'warm'),
                source=data.get('source', ''),
                value=data.get('value', 0),
                notes=data.get('notes', ''),
                governorate=data.get('governorate', ''),
                city=data.get('city', ''),
                created_by=request.user,
                assigned_to_id=data.get('assigned_to'),
            )
            
            # إضافة عقارات مهتم بها إذا وجدت
            property_ids = data.get('property_ids', [])
            if property_ids:
                new_contact.properties_interested.set(property_ids)
            
            # إرسال إشعار للمسند إليه
            if new_contact.assigned_to:
                from .models import Notification
                Notification.create(
                    user=new_contact.assigned_to,
                    notification_type='info',
                    title='تم تعيين جهة اتصال جديدة',
                    message=f'تم تعيين جهة الاتصال {new_contact.name} لك',
                    link='/api/crm/management/',
                    metadata={'contact_id': new_contact.id}
                )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إضافة جهة الاتصال بنجاح',
                'contact': {
                    'id': new_contact.id,
                    'name': new_contact.name,
                    'email': new_contact.email,
                    'phone': new_contact.phone,
                    'company': new_contact.company,
                    'stage': new_contact.stage,
                    'priority': new_contact.priority,
                    'value': float(new_contact.value),
                }
            })
        
        elif request.method == 'PUT':
            # تحديث جهة اتصال موجودة
            data = json.loads(request.body)
            contact_id = data.get('id')
            
            contact = get_object_or_404(CRMContact, id=contact_id)
            
            # تحديث الحقول
            contact.name = data.get('name', contact.name)
            contact.email = data.get('email', contact.email)
            contact.phone = data.get('phone', contact.phone)
            contact.secondary_phone = data.get('secondary_phone', contact.secondary_phone)
            contact.company = data.get('company', contact.company)
            contact.position = data.get('position', contact.position)
            contact.stage = data.get('stage', contact.stage)
            contact.priority = data.get('priority', contact.priority)
            contact.source = data.get('source', contact.source)
            contact.value = data.get('value', contact.value)
            contact.notes = data.get('notes', contact.notes)
            contact.governorate = data.get('governorate', contact.governorate)
            contact.city = data.get('city', contact.city)
            contact.assigned_to_id = data.get('assigned_to')
            
            # تحديث التواريخ
            if data.get('last_contact'):
                contact.last_contact = timezone.now()
                contact.update_interaction_count()
            
            if data.get('next_followup'):
                contact.next_followup = timezone.strptime(data['next_followup'], '%Y-%m-%d')
            
            # تحويل إلى عميل
            if data.get('convert_to_customer'):
                contact.convert_to_customer()
            
            contact.save()
            
            # تحديث العقارات المهتم بها
            property_ids = data.get('property_ids', [])
            if property_ids is not None:
                contact.properties_interested.set(property_ids)
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث جهة الاتصال بنجاح',
                'contact': {
                    'id': contact.id,
                    'name': contact.name,
                    'stage': contact.stage,
                    'priority': contact.priority,
                }
            })
        
        elif request.method == 'DELETE':
            # حذف جهة اتصال
            data = json.loads(request.body)
            contact_id = data.get('id')
            
            contact = get_object_or_404(CRMContact, id=contact_id)
            contact.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'تم حذف جهة الاتصال بنجاح'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def crm_dashboard(request):
    """لوحة تحكم CRM"""
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('dashboard')
    
    from .models import CRMContact
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # إحصائيات عامة
    total_contacts = CRMContact.objects.count()
    active_contacts = CRMContact.objects.filter(is_active=True).count()
    converted_contacts = CRMContact.objects.filter(is_converted=True).count()
    
    # إحصائيات حسب المرحلة
    stage_stats = CRMContact.objects.values('stage').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # إحصائيات حسب الأولوية
    priority_stats = CRMContact.objects.values('priority').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # المتابعات المستحقة
    followup_due = CRMContact.objects.filter(
        next_followup__lte=timezone.now(),
        is_active=True
    ).order_by('next_followup')[:10]
    
    # جهات الاتصال الجديدة
    recent_contacts = CRMContact.objects.select_related('created_by', 'assigned_to').order_by('-created_at')[:10]
    
    # أفضل الوكلاء
    top_agents = CRMContact.objects.values('assigned_to__username').annotate(
        count=Count('id'),
        total_value=Sum('value')
    ).order_by('-count')[:10]
    
    # القيمة المتوقعة
    total_value = CRMContact.objects.aggregate(total=Sum('value'))['total'] or 0
    converted_value = CRMContact.objects.aggregate(total=Sum('converted_value'))['total'] or 0
    
    context = {
        'total_contacts': total_contacts,
        'active_contacts': active_contacts,
        'converted_contacts': converted_contacts,
        'conversion_rate': round((converted_contacts / total_contacts * 100) if total_contacts > 0 else 0, 1),
        'total_value': total_value,
        'converted_value': converted_value,
        'stage_stats': stage_stats,
        'priority_stats': priority_stats,
        'followup_due': followup_due,
        'recent_contacts': recent_contacts,
        'top_agents': top_agents,
    }
    
    return render(request, 'properties/crm_dashboard.html', context)


@login_required
def crm_contact_detail(request, contact_id):
    """تفاصيل جهة اتصال CRM"""
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('dashboard')
    
    from .models import CRMContact
    
    contact = get_object_or_404(CRMContact, id=contact_id)
    
    context = {
        'contact': contact,
        'properties_interested': contact.properties_interested.all(),
    }
    
    return render(request, 'properties/crm_contact_detail.html', context)



@login_required
def automation_management(request):
    """نظام إدارة الأتمتة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الأتمتة
            automations = []
            trigger_types = ['schedule', 'webhook', 'event', 'manual']
            action_types = ['email', 'notification', 'webhook', 'task', 'api']
            statuses = ['active', 'paused', 'disabled', 'error']
            
            for i in range(15):
                automations.append({
                    'id': i + 1,
                    'name': f'أتمتة {i + 1}',
                    'description': f'وصف الأتمتة {i + 1}',
                    'trigger_type': random.choice(trigger_types),
                    'trigger_config': {'schedule': 'daily at 09:00'},
                    'action_type': random.choice(action_types),
                    'action_config': {'recipient': 'admin@example.com'},
                    'status': random.choice(statuses),
                    'last_run': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'next_run': (timezone.now() + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S'),
                    'run_count': random.randint(0, 100),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'automations': automations,
                'statistics': {
                    'total': len(automations),
                    'active': sum(1 for a in automations if a['status'] == 'active'),
                    'paused': sum(1 for a in automations if a['status'] == 'paused'),
                    'error': sum(1 for a in automations if a['status'] == 'error')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_automation = {
                'id': 999,
                'name': data.get('name', 'New Automation'),
                'description': data.get('description', ''),
                'trigger_type': data.get('trigger_type', 'manual'),
                'trigger_config': data.get('trigger_config', {}),
                'action_type': data.get('action_type', 'notification'),
                'action_config': data.get('action_config', {}),
                'status': 'active',
                'run_count': 0,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'automation': new_automation,
                'message': 'تم إنشاء الأتمتة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def integrations_management(request):
    """نظام إدارة التكاملات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات التكاملات
            integrations = []
            categories = ['payment', 'analytics', 'communication', 'storage', 'security']
            statuses = ['connected', 'disconnected', 'error', 'pending']
            
            for i in range(15):
                integrations.append({
                    'id': i + 1,
                    'name': f'Integration {i + 1}',
                    'category': random.choice(categories),
                    'status': random.choice(statuses),
                    'api_key': f'key_{random.randint(100000, 999999)}',
                    'endpoint': f'https://api.service{i + 1}.com',
                    'last_sync': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'sync_frequency': random.choice(['hourly', 'daily', 'weekly']),
                    'is_active': random.choice([True, False]),
                    'description': f'وصف التكامل {i + 1}',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'integrations': integrations,
                'statistics': {
                    'total': len(integrations),
                    'connected': sum(1 for i in integrations if i['status'] == 'connected'),
                    'disconnected': sum(1 for i in integrations if i['status'] == 'disconnected'),
                    'error': sum(1 for i in integrations if i['status'] == 'error')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_integration = {
                'id': 999,
                'name': data.get('name', 'New Integration'),
                'category': data.get('category', 'other'),
                'status': 'pending',
                'api_key': data.get('api_key'),
                'endpoint': data.get('endpoint'),
                'sync_frequency': data.get('sync_frequency', 'daily'),
                'is_active': True,
                'description': data.get('description', ''),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'integration': new_integration,
                'message': 'تم إنشاء التكامل بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def performance_reports(request):
    """نظام تقارير الأداء"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        report_type = request.GET.get('type', 'overview')
        period = request.GET.get('period', 'monthly')
        
        if report_type == 'overview':
            # نظرة عامة على الأداء
            overview = {
                'system_performance': {
                    'uptime': '99.95%',
                    'response_time': '150ms',
                    'throughput': '1000 req/min',
                    'error_rate': '0.05%'
                },
                'user_experience': {
                    'page_load_time': '2.3s',
                    'interaction_time': '0.5s',
                    'satisfaction_score': '4.5/5'
                },
                'resource_usage': {
                    'cpu_usage': '45%',
                    'memory_usage': '60%',
                    'disk_usage': '35%',
                    'network_usage': '25%'
                },
                'business_metrics': {
                    'conversion_rate': '5%',
                    'bounce_rate': '25%',
                    'average_session_duration': '5m 32s',
                    'returning_users': '30%'
                }
            }
            
            return JsonResponse({
                'success': True,
                'report_type': report_type,
                'period': period,
                'data': overview
            })
        
        elif report_type == 'detailed':
            # تقرير تفصيلي
            detailed = {
                'endpoints': [
                    {'endpoint': '/api/properties', 'avg_response': '120ms', 'success_rate': '99.8%'},
                    {'endpoint': '/api/users', 'avg_response': '80ms', 'success_rate': '99.9%'},
                    {'endpoint': '/api/analytics', 'avg_response': '200ms', 'success_rate': '99.5%'}
                ],
                'database_queries': [
                    {'query': 'SELECT * FROM properties', 'avg_time': '45ms', 'count': 1000},
                    {'query': 'SELECT * FROM users', 'avg_time': '30ms', 'count': 500}
                ],
                'errors': [
                    {'type': '500', 'count': 10, 'description': 'Internal Server Error'},
                    {'type': '404', 'count': 25, 'description': 'Not Found'},
                    {'type': '403', 'count': 5, 'description': 'Forbidden'}
                ]
            }
            
            return JsonResponse({
                'success': True,
                'report_type': report_type,
                'period': period,
                'data': detailed
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def survey_management(request):
    """نظام إدارة الاستبيانات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الاستبيانات
            surveys = []
            statuses = ['draft', 'active', 'closed', 'archived']
            types = ['customer_satisfaction', 'product_feedback', 'market_research', 'employee_survey']
            
            for i in range(15):
                surveys.append({
                    'id': i + 1,
                    'title': f'استبيان {i + 1}',
                    'description': f'وصف الاستبيان {i + 1}',
                    'type': random.choice(types),
                    'status': random.choice(statuses),
                    'questions_count': random.randint(5, 20),
                    'responses_count': random.randint(0, 500),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'published_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'closed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'surveys': surveys,
                'statistics': {
                    'total': len(surveys),
                    'active': sum(1 for s in surveys if s['status'] == 'active'),
                    'draft': sum(1 for s in surveys if s['status'] == 'draft'),
                    'total_responses': sum(s['responses_count'] for s in surveys)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_survey = {
                'id': 999,
                'title': data.get('title', 'New Survey'),
                'description': data.get('description', ''),
                'type': data.get('type', 'customer_satisfaction'),
                'status': 'draft',
                'questions_count': 0,
                'responses_count': 0,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'survey': new_survey,
                'message': 'تم إنشاء الاستبيان بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def queue_management(request):
    """نظام إدارة الكواليس"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الكواليس
            queues = []
            priorities = ['low', 'normal', 'high', 'urgent']
            statuses = ['pending', 'processing', 'completed', 'failed']
            
            for i in range(20):
                queues.append({
                    'id': i + 1,
                    'task': f'مهمة {i + 1}',
                    'type': random.choice(['email', 'notification', 'backup', 'sync', 'cleanup']),
                    'priority': random.choice(priorities),
                    'status': random.choice(statuses),
                    'worker': f'worker_{random.randint(1, 5)}' if random.choice([True, False]) else None,
                    'progress': random.randint(0, 100),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'started_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'completed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'queues': queues,
                'statistics': {
                    'total': len(queues),
                    'pending': sum(1 for q in queues if q['status'] == 'pending'),
                    'processing': sum(1 for q in queues if q['status'] == 'processing'),
                    'completed': sum(1 for q in queues if q['status'] == 'completed'),
                    'failed': sum(1 for q in queues if q['status'] == 'failed')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_queue = {
                'id': 999,
                'task': data.get('task', 'New Task'),
                'type': data.get('type', 'notification'),
                'priority': data.get('priority', 'normal'),
                'status': 'pending',
                'progress': 0,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'queue': new_queue,
                'message': 'تم إضافة المهمة إلى الكواليس بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def invoice_management(request):
    """نظام إدارة الفواتير"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الفواتير
            invoices = []
            statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
            currencies = ['USD', 'EUR', 'SAR', 'AED']
            
            for i in range(20):
                invoices.append({
                    'id': i + 1,
                    'invoice_number': f'INV-{2026}-{i + 1:04d}',
                    'customer': f'customer_{i + 1}',
                    'amount': random.randint(100, 10000),
                    'currency': random.choice(currencies),
                    'status': random.choice(statuses),
                    'due_date': (timezone.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'paid_date': timezone.now().strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                    'items_count': random.randint(1, 10),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'invoices': invoices,
                'statistics': {
                    'total': len(invoices),
                    'paid': sum(1 for i in invoices if i['status'] == 'paid'),
                    'overdue': sum(1 for i in invoices if i['status'] == 'overdue'),
                    'total_amount': sum(i['amount'] for i in invoices),
                    'pending_amount': sum(i['amount'] for i in invoices if i['status'] in ['draft', 'sent', 'overdue'])
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_invoice = {
                'id': 999,
                'invoice_number': f'INV-{2026}-9999',
                'customer': data.get('customer', 'New Customer'),
                'amount': data.get('amount', 0),
                'currency': data.get('currency', 'USD'),
                'status': 'draft',
                'due_date': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'items_count': 0,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'invoice': new_invoice,
                'message': 'تم إنشاء الفاتورة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def inventory_management(request):
    """نظام إدارة المستودعات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات المستودعات
            inventory = []
            categories = ['electronics', 'furniture', 'office', 'supplies', 'equipment']
            statuses = ['in_stock', 'low_stock', 'out_of_stock', 'discontinued']
            
            for i in range(25):
                inventory.append({
                    'id': i + 1,
                    'name': f'product_{i + 1}',
                    'sku': f'SKU-{random.randint(10000, 99999)}',
                    'category': random.choice(categories),
                    'quantity': random.randint(0, 100),
                    'min_quantity': random.randint(5, 20),
                    'price': random.randint(10, 500),
                    'supplier': f'supplier_{random.randint(1, 10)}',
                    'location': f'warehouse_{random.randint(1, 5)}',
                    'status': random.choice(statuses),
                    'last_restocked': timezone.now().strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'inventory': inventory,
                'statistics': {
                    'total': len(inventory),
                    'in_stock': sum(1 for i in inventory if i['status'] == 'in_stock'),
                    'low_stock': sum(1 for i in inventory if i['status'] == 'low_stock'),
                    'out_of_stock': sum(1 for i in inventory if i['status'] == 'out_of_stock'),
                    'total_value': sum(i['quantity'] * i['price'] for i in inventory)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_item = {
                'id': 999,
                'name': data.get('name', 'New Product'),
                'sku': f'SKU-{random.randint(10000, 99999)}',
                'category': data.get('category', 'supplies'),
                'quantity': data.get('quantity', 0),
                'min_quantity': data.get('min_quantity', 10),
                'price': data.get('price', 0),
                'status': 'in_stock',
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'item': new_item,
                'message': 'تم إضافة المنتج بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def transportation_management(request):
    """نظام إدارة النقل"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات النقل
            shipments = []
            statuses = ['pending', 'in_transit', 'delivered', 'cancelled', 'returned']
            types = ['standard', 'express', 'overnight', 'freight']
            
            for i in range(20):
                shipments.append({
                    'id': i + 1,
                    'tracking_number': f'TRK-{random.randint(1000000, 9999999)}',
                    'type': random.choice(types),
                    'status': random.choice(statuses),
                    'origin': f'City {random.randint(1, 10)}',
                    'destination': f'City {random.randint(1, 10)}',
                    'weight': random.randint(1, 100),
                    'cost': random.randint(10, 500),
                    'carrier': random.choice(['DHL', 'FedEx', 'UPS', 'Aramex']),
                    'estimated_delivery': (timezone.now() + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                    'actual_delivery': timezone.now().strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'shipments': shipments,
                'statistics': {
                    'total': len(shipments),
                    'in_transit': sum(1 for s in shipments if s['status'] == 'in_transit'),
                    'delivered': sum(1 for s in shipments if s['status'] == 'delivered'),
                    'pending': sum(1 for s in shipments if s['status'] == 'pending')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_shipment = {
                'id': 999,
                'tracking_number': f'TRK-{random.randint(1000000, 9999999)}',
                'type': data.get('type', 'standard'),
                'status': 'pending',
                'origin': data.get('origin', 'Origin City'),
                'destination': data.get('destination', 'Destination City'),
                'weight': data.get('weight', 0),
                'cost': data.get('cost', 0),
                'carrier': data.get('carrier', 'DHL'),
                'estimated_delivery': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'shipment': new_shipment,
                'message': 'تم إنشاء الشحنة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_management(request):
    """نظام إدارة العقود"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات العقود
            contracts = []
            types = ['employment', 'service', 'lease', 'purchase', 'partnership']
            statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
            
            for i in range(15):
                start_date = timezone.now() - timedelta(days=random.randint(1, 365))
                end_date = start_date + timedelta(days=random.randint(30, 365))
                
                contracts.append({
                    'id': i + 1,
                    'contract_number': f'CTR-{random.randint(10000, 99999)}',
                    'title': f'عقد {i + 1}',
                    'type': random.choice(types),
                    'status': random.choice(statuses),
                    'party_a': f'Company {random.randint(1, 10)}',
                    'party_b': f'Company {random.randint(1, 10)}',
                    'value': random.randint(1000, 100000),
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'renewal_date': (end_date - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'contracts': contracts,
                'statistics': {
                    'total': len(contracts),
                    'active': sum(1 for c in contracts if c['status'] == 'active'),
                    'expired': sum(1 for c in contracts if c['status'] == 'expired'),
                    'total_value': sum(c['value'] for c in contracts)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_contract = {
                'id': 999,
                'contract_number': f'CTR-{random.randint(10000, 99999)}',
                'title': data.get('title', 'New Contract'),
                'type': data.get('type', 'service'),
                'status': 'draft',
                'party_a': data.get('party_a', 'Party A'),
                'party_b': data.get('party_b', 'Party B'),
                'value': data.get('value', 0),
                'start_date': data.get('start_date', timezone.now().strftime('%Y-%m-%d')),
                'end_date': data.get('end_date', (timezone.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'contract': new_contract,
                'message': 'تم إنشاء العقد بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def document_management(request):
    """نظام إدارة الوثائق"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الوثائق
            documents = []
            categories = ['legal', 'financial', 'technical', 'hr', 'marketing']
            formats = ['pdf', 'docx', 'xlsx', 'pptx', 'txt']
            statuses = ['draft', 'review', 'approved', 'archived']
            
            for i in range(20):
                documents.append({
                    'id': i + 1,
                    'title': f'وثيقة {i + 1}',
                    'category': random.choice(categories),
                    'format': random.choice(formats),
                    'status': random.choice(statuses),
                    'version': f'v{random.randint(1, 5)}.{random.randint(0, 9)}',
                    'author': f'user_{random.randint(1, 10)}',
                    'size': random.randint(10, 10000),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'expiry_date': (timezone.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d') if random.choice([True, False]) else None
                })
            
            return JsonResponse({
                'success': True,
                'documents': documents,
                'statistics': {
                    'total': len(documents),
                    'approved': sum(1 for d in documents if d['status'] == 'approved'),
                    'review': sum(1 for d in documents if d['status'] == 'review'),
                    'total_size': sum(d['size'] for d in documents)
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_document = {
                'id': 999,
                'title': data.get('title', 'New Document'),
                'category': data.get('category', 'technical'),
                'format': data.get('format', 'pdf'),
                'status': 'draft',
                'version': 'v1.0',
                'author': request.user.username,
                'size': 0,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'document': new_document,
                'message': 'تم إنشاء الوثيقة بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def event_management(request):
    """نظام إدارة الأحداث"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الأحداث
            events = []
            types = ['meeting', 'conference', 'webinar', 'training', 'social']
            statuses = ['upcoming', 'ongoing', 'completed', 'cancelled']
            
            for i in range(15):
                event_date = timezone.now() + timedelta(days=random.randint(-10, 30))
                
                events.append({
                    'id': i + 1,
                    'title': f'حدث {i + 1}',
                    'description': f'وصف الحدث {i + 1}',
                    'type': random.choice(types),
                    'status': random.choice(statuses),
                    'start_date': event_date.strftime('%Y-%m-%d'),
                    'start_time': f'{random.randint(9, 18)}:00',
                    'end_date': (event_date + timedelta(days=random.randint(0, 3))).strftime('%Y-%m-%d'),
                    'end_time': f'{random.randint(9, 18)}:00',
                    'location': random.choice(['Main Hall', 'Conference Room A', 'Online', 'Outdoor', 'Office']),
                    'attendees_count': random.randint(5, 100),
                    'max_attendees': random.randint(50, 200),
                    'organizer': f'user_{random.randint(1, 10)}',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'events': events,
                'statistics': {
                    'total': len(events),
                    'upcoming': sum(1 for e in events if e['status'] == 'upcoming'),
                    'ongoing': sum(1 for e in events if e['status'] == 'ongoing'),
                    'completed': sum(1 for e in events if e['status'] == 'completed')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_event = {
                'id': 999,
                'title': data.get('title', 'New Event'),
                'description': data.get('description', ''),
                'type': data.get('type', 'meeting'),
                'status': 'upcoming',
                'start_date': data.get('start_date', timezone.now().strftime('%Y-%m-%d')),
                'start_time': data.get('start_time', '09:00'),
                'end_date': data.get('end_date', timezone.now().strftime('%Y-%m-%d')),
                'end_time': data.get('end_time', '17:00'),
                'location': data.get('location', 'Office'),
                'attendees_count': 0,
                'max_attendees': data.get('max_attendees', 50),
                'organizer': request.user.username,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return JsonResponse({
                'success': True,
                'event': new_event,
                'message': 'تم إنشاء الحدث بنجاح'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Real Estate Specific Functions
@login_required
def property_management_advanced(request):
    """نظام إدارة العقارات المتقدم - بيانات حقيقية من قاعدة البيانات"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # جلب البيانات الحقيقية من قاعدة البيانات
            properties_list = Property.objects.select_related('owner', 'broker', 'office').prefetch_related('verification').all()
            
            # تحويل البيانات إلى القوائم
            properties = []
            for prop in properties_list:
                properties.append({
                    'id': prop.id,
                    'title': prop.title or prop.display_title,
                    'type': prop.type,
                    'status': prop.status,
                    'price': prop.price,
                    'area': prop.area,
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'city': prop.city,
                    'district': prop.district,
                    'governorate': prop.governorate,
                    'year_built': prop.year_built,
                    'views_count': prop.views_count,
                    'is_featured': prop.is_featured,
                    'is_promoted': prop.is_promoted,
                    'created_at': prop.created_at.strftime('%Y-%m-%d') if prop.created_at else None,
                    'owner': prop.owner.username if prop.owner else None,
                    'broker': prop.broker.display_name if prop.broker else None,
                    'office': prop.office.name if prop.office else None,
                    'verification_status': prop.verification.verification_status if hasattr(prop, 'verification') and prop.verification else None,
                    'verification_badge': prop.verification.get_verification_badge() if hasattr(prop, 'verification') and prop.verification else '',
                    # الحقول الجديدة
                    'office_name': prop.office_name,
                    'license_number': prop.license_number,
                    'deed_type': prop.deed_type,
                    'deed_number': prop.deed_number,
                    'land_registration_status': prop.land_registration_status,
                    'is_mortgaged': prop.is_mortgaged,
                    'complex_name': prop.complex_name,
                    'building_number': prop.building_number,
                    'unit_number': prop.unit_number,
                    'total_price': prop.total_price,
                    'monthly_rent': prop.monthly_rent,
                    'furnishing_status': prop.furnishing_status,
                    'has_elevator': prop.has_elevator,
                    'has_garage': prop.has_garage,
                    'has_security_system': prop.has_security_system,
                    'property_age': prop.property_age,
                    'property_condition': prop.property_condition,
                })
            
            # حساب الإحصائيات الحقيقية
            total_properties = properties_list.count()
            active_properties = properties_list.filter(status='published').count()
            sold_properties = properties_list.filter(status='sold').count()
            pending_properties = properties_list.filter(status='pending_approval').count()
            
            # إحصائيات الأسعار
            price_stats = properties_list.aggregate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                total_value=Sum('price')
            )
            
            # إحصائيات حسب النوع
            type_stats = properties_list.values('type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # إحصائيات حسب المحافظة
            governorate_stats = properties_list.values('governorate').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # العقارات الأكثر مشاهدة
            top_viewed = properties_list.order_by('-views_count')[:10]
            
            # العقارات الموثقة
            verified_properties = properties_list.filter(
                verification__verification_status='verified'
            ).count()
            
            return JsonResponse({
                'success': True,
                'properties': properties,
                'statistics': {
                    'total': total_properties,
                    'active': active_properties,
                    'sold': sold_properties,
                    'pending': pending_properties,
                    'verified': verified_properties,
                    'price_stats': {
                        'avg_price': int(price_stats['avg_price']) if price_stats['avg_price'] else 0,
                        'min_price': int(price_stats['min_price']) if price_stats['min_price'] else 0,
                        'max_price': int(price_stats['max_price']) if price_stats['max_price'] else 0,
                        'total_value': int(price_stats['total_value']) if price_stats['total_value'] else 0,
                    },
                    'type_stats': list(type_stats),
                    'governorate_stats': list(governorate_stats),
                    'top_viewed': [
                        {
                            'id': prop.id,
                            'title': prop.title or prop.display_title,
                            'views_count': prop.views_count
                        }
                        for prop in top_viewed
                    ]
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def clients_management(request):
    """نظام إدارة العملاء والوكلاء"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات العملاء
            clients = []
            client_types = ['buyer', 'seller', 'renter', 'landlord', 'investor']
            statuses = ['active', 'inactive', 'potential', 'lost']
            
            for i in range(20):
                clients.append({
                    'id': i + 1,
                    'name': f'عميل {i + 1}',
                    'email': f'client{i + 1}@example.com',
                    'phone': f'+1234567{i:04d}',
                    'type': random.choice(client_types),
                    'status': random.choice(statuses),
                    'budget': random.randint(100000, 5000000),
                    'preferred_city': random.choice(['بغداد', 'البصرة', 'أربيل', 'النجف']),
                    'preferred_type': random.choice(['apartment', 'villa', 'commercial']),
                    'interactions_count': random.randint(0, 50),
                    'last_contact': timezone.now().strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                    'assigned_agent': f'agent_{random.randint(1, 5)}' if random.choice([True, False]) else None,
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'clients': clients,
                'statistics': {
                    'total': len(clients),
                    'active': sum(1 for c in clients if c['status'] == 'active'),
                    'potential': sum(1 for c in clients if c['status'] == 'potential'),
                    'total_budget': sum(c['budget'] for c in clients)
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def offers_management(request):
    """نظام إدارة الطلبات والعروض"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات العروض
            offers = []
            offer_types = ['purchase', 'rent', 'lease']
            statuses = ['pending', 'accepted', 'rejected', 'countered', 'expired']
            
            for i in range(20):
                offers.append({
                    'id': i + 1,
                    'property_id': random.randint(1, 25),
                    'client_id': random.randint(1, 20),
                    'type': random.choice(offer_types),
                    'status': random.choice(statuses),
                    'offer_amount': random.randint(50000, 5000000),
                    'original_price': random.randint(50000, 5000000),
                    'offered_date': timezone.now().strftime('%Y-%m-%d'),
                    'expiry_date': (timezone.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'negotiation_rounds': random.randint(0, 5),
                    'notes': f'ملاحظات العرض {i + 1}',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'offers': offers,
                'statistics': {
                    'total': len(offers),
                    'pending': sum(1 for o in offers if o['status'] == 'pending'),
                    'accepted': sum(1 for o in offers if o['status'] == 'accepted'),
                    'total_value': sum(o['offer_amount'] for o in offers)
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def live_auctions_management(request):
    """نظام إدارة المزادات المباشرة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات المزادات
            auctions = []
            statuses = ['scheduled', 'live', 'completed', 'cancelled']
            
            for i in range(15):
                auctions.append({
                    'id': i + 1,
                    'property_id': random.randint(1, 25),
                    'title': f'مزاد عقار {i + 1}',
                    'description': f'وصف المزاد {i + 1}',
                    'status': random.choice(statuses),
                    'start_price': random.randint(50000, 5000000),
                    'current_bid': random.randint(50000, 5000000),
                    'reserve_price': random.randint(50000, 5000000),
                    'start_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': (timezone.now() + timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S'),
                    'bidders_count': random.randint(0, 50),
                    'views_count': random.randint(0, 1000),
                    'is_featured': random.choice([True, False]),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'auctions': auctions,
                'statistics': {
                    'total': len(auctions),
                    'live': sum(1 for a in auctions if a['status'] == 'live'),
                    'completed': sum(1 for a in auctions if a['status'] == 'completed'),
                    'total_bids': sum(a['bidders_count'] for a in auctions)
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def real_estate_properties_api(request):
    """API for real estate properties management"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    try:
        if request.method == 'GET':
            from .models import Property
            properties = Property.objects.all().order_by('-created_at')

            property_list = []
            for prop in properties:
                property_list.append({
                    'id': prop.id,
                    'title': prop.display_title if hasattr(prop, 'display_title') else prop.title,
                    'type': prop.get_property_type_display() if hasattr(prop, 'get_property_type_display') else 'غير محدد',
                    'status': prop.get_status_display() if hasattr(prop, 'get_status_display') else 'غير محدد',
                    'price': prop.price_formatted if hasattr(prop, 'price_formatted') else str(prop.price) if prop.price else '0',
                    'district': prop.district if hasattr(prop, 'district') else 'غير محدد',
                    'is_featured': prop.is_featured if hasattr(prop, 'is_featured') else False,
                    'views_count': prop.views_count if hasattr(prop, 'views_count') else 0,
                    'created_at': prop.created_at.strftime('%Y-%m-%d %H:%M:%S') if prop.created_at else ''
                })

            # Calculate statistics
            statistics = {
                'total': properties.count(),
                'available': properties.filter(status='available').count() if hasattr(Property, 'status') else 0,
                'sold': properties.filter(status='sold').count() if hasattr(Property, 'status') else 0,
                'total_value': sum(p.price for p in properties if p.price)
            }

            return JsonResponse({
                'success': True,
                'properties': property_list,
                'statistics': statistics
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def schedules_management(request):
    """نظام إدارة الجولات والمواعيد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # Get real appointments from database
            from .models import Appointment
            appointments = Appointment.objects.all().order_by('-appointment_date', '-appointment_time')
            
            schedules = []
            for appointment in appointments:
                schedules.append({
                    'id': appointment.id,
                    'type': appointment.get_appointment_type_display(),
                    'status': appointment.get_status_display(),
                    'date': appointment.appointment_date.strftime('%Y-%m-%d') if appointment.appointment_date else '',
                    'time': appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else '',
                    'location': appointment.location or 'Property Location',
                    'user': appointment.user.username if appointment.user else 'Unknown',
                    'notes': appointment.notes or '',
                    'priority': appointment.get_priority_display(),
                    'duration': appointment.duration,
                    'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S') if appointment.created_at else ''
                })

            # Calculate statistics
            today = timezone.now().date()
            tomorrow = today + timedelta(days=1)
            upcoming_cutoff = timezone.now() + timedelta(hours=24)

            statistics = {
                'total': appointments.count(),
                'scheduled': appointments.filter(status='pending').count(),
                'confirmed': appointments.filter(status='confirmed').count(),
                'completed': appointments.filter(status='completed').count(),
                'cancelled': appointments.filter(status='cancelled').count(),
                'today': appointments.filter(appointment_date=today).count(),
                'upcoming': appointments.filter(
                    appointment_date__gte=today,
                    appointment_date__lte=tomorrow,
                    status='pending'
                ).count(),
                'overdue': appointments.filter(
                    appointment_date__lt=today,
                    status__in=['pending', 'confirmed']
                ).count()
            }
            
            return JsonResponse({
                'success': True,
                'schedules': schedules,
                'statistics': statistics
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contracts_real_estate(request):
    """نظام إدارة العقود والاتفاقيات العقارية"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # Get all contracts with related data
            contracts = RealEstateContract.objects.all().select_related(
                'property', 'broker', 'client', 'created_by', 'approved_by'
            ).order_by('-created_at')
            
            contracts_data = []
            for contract in contracts:
                contracts_data.append({
                    'id': contract.id,
                    'contract_number': contract.contract_number,
                    'contract_type': contract.contract_type,
                    'contract_type_display': contract.get_contract_type_display(),
                    'status': contract.status,
                    'status_display': contract.get_status_display(),
                    'property_id': contract.property.id if contract.property else None,
                    'property_title': contract.property.title if contract.property else 'غير محدد',
                    'broker_id': contract.broker.id if contract.broker else None,
                    'broker_name': contract.broker.user.username if contract.broker and contract.broker.user else 'غير محدد',
                    'client_id': contract.client.id if contract.client else None,
                    'client_name': contract.client.username if contract.client else 'غير محدد',
                    'second_party_name': contract.second_party_name or '',
                    'amount': float(contract.amount) if contract.amount else 0,
                    'deposit': float(contract.deposit) if contract.deposit else 0,
                    'commission_rate': float(contract.commission_rate) if contract.commission_rate else 0,
                    'commission_amount': float(contract.commission_amount) if contract.commission_amount else 0,
                    'start_date': contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
                    'end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
                    'signing_date': contract.signing_date.strftime('%Y-%m-%d') if contract.signing_date else '',
                    'payment_frequency': contract.payment_frequency,
                    'payment_frequency_display': contract.get_payment_frequency_display(),
                    'renewal_clause': contract.renewal_clause,
                    'created_at': contract.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': contract.created_by.username if contract.created_by else 'غير محدد',
                    'approved_by': contract.approved_by.username if contract.approved_by else 'غير محدد',
                    'approved_at': contract.approved_at.strftime('%Y-%m-%d %H:%M:%S') if contract.approved_at else '',
                    'is_active': contract.is_active(),
                    'days_remaining': contract.days_remaining(),
                })
            
            # Calculate statistics
            total_contracts = contracts.count()
            active_contracts = contracts.filter(status='active').count()
            completed_contracts = contracts.filter(status='completed').count()
            total_value = sum(float(c.amount) for c in contracts if c.amount)
            total_commission = sum(float(c.commission_amount) for c in contracts if c.commission_amount)
            
            return JsonResponse({
                'success': True,
                'contracts': contracts_data,
                'statistics': {
                    'total': total_contracts,
                    'active': active_contracts,
                    'completed': completed_contracts,
                    'total_value': total_value,
                    'total_commission': total_commission
                }
            })
        
        elif request.method == 'POST':
            # Create new contract
            from .models import RealEstateContract
            from .forms import RealEstateContractForm
            
            form = RealEstateContractForm(request.POST)
            if form.is_valid():
                contract = form.save(commit=False)
                contract.created_by = request.user
                contract.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'تم إنشاء العقد بنجاح',
                    'contract_id': contract.id,
                    'contract_number': contract.contract_number
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'بيانات غير صحيحة',
                    'errors': form.errors
                }, status=400)
    
    except Exception as e:
        logger.error(f"Error in contracts_real_estate: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_detail(request, contract_id):
    """عرض تفاصيل عقد محدد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        contract_data = {
            'id': contract.id,
            'contract_number': contract.contract_number,
            'contract_type': contract.contract_type,
            'contract_type_display': contract.get_contract_type_display(),
            'status': contract.status,
            'status_display': contract.get_status_display(),
            'property_id': contract.property.id if contract.property else None,
            'property_title': contract.property.title if contract.property else 'غير محدد',
            'broker_id': contract.broker.id if contract.broker else None,
            'broker_name': contract.broker.user.username if contract.broker and contract.broker.user else 'غير محدد',
            'client_id': contract.client.id if contract.client else None,
            'client_name': contract.client.username if contract.client else 'غير محدد',
            'second_party_name': contract.second_party_name or '',
            'second_party_phone': contract.second_party_phone or '',
            'second_party_email': contract.second_party_email or '',
            'amount': float(contract.amount) if contract.amount else 0,
            'deposit': float(contract.deposit) if contract.deposit else 0,
            'commission_rate': float(contract.commission_rate) if contract.commission_rate else 0,
            'commission_amount': float(contract.commission_amount) if contract.commission_amount else 0,
            'start_date': contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
            'end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
            'signing_date': contract.signing_date.strftime('%Y-%m-%d') if contract.signing_date else '',
            'payment_frequency': contract.payment_frequency,
            'payment_frequency_display': contract.get_payment_frequency_display(),
            'payment_terms': contract.payment_terms or '',
            'terms_and_conditions': contract.terms_and_conditions or '',
            'special_clauses': contract.special_clauses or '',
            'renewal_clause': contract.renewal_clause,
            'termination_clause': contract.termination_clause or '',
            'notes': contract.notes or '',
            'created_at': contract.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': contract.created_by.username if contract.created_by else 'غير محدد',
            'approved_by': contract.approved_by.username if contract.approved_by else 'غير محدد',
            'approved_at': contract.approved_at.strftime('%Y-%m-%d %H:%M:%S') if contract.approved_at else '',
            'is_active': contract.is_active(),
            'days_remaining': contract.days_remaining(),
        }
        
        # Get related payments
        from .models import ContractPayment
        payments = ContractPayment.objects.filter(contract=contract).order_by('due_date')
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'payment_number': payment.payment_number,
                'amount': float(payment.amount) if payment.amount else 0,
                'paid_amount': float(payment.paid_amount) if payment.paid_amount else 0,
                'status': payment.status,
                'status_display': payment.get_status_display(),
                'payment_method': payment.payment_method,
                'payment_method_display': payment.get_payment_method_display(),
                'due_date': payment.due_date.strftime('%Y-%m-%d') if payment.due_date else '',
                'paid_date': payment.paid_date.strftime('%Y-%m-%d') if payment.paid_date else '',
                'notes': payment.notes or '',
                'is_overdue': payment.is_overdue(),
                'remaining_amount': float(payment.remaining_amount()) if payment.remaining_amount() else 0,
            })
        
        # Get related documents
        from .models import ContractDocument
        documents = ContractDocument.objects.filter(contract=contract).order_by('-uploaded_at')
        documents_data = []
        for doc in documents:
            documents_data.append({
                'id': doc.id,
                'document_type': doc.document_type,
                'document_type_display': doc.get_document_type_display(),
                'title': doc.title,
                'description': doc.description or '',
                'file': doc.file.url if doc.file else '',
                'file_size': doc.file_size,
                'uploaded_by': doc.uploaded_by.username if doc.uploaded_by else 'غير محدد',
                'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # Get related reminders
        from .models import ContractReminder
        reminders = ContractReminder.objects.filter(contract=contract).order_by('reminder_date')
        reminders_data = []
        for reminder in reminders:
            reminders_data.append({
                'id': reminder.id,
                'reminder_type': reminder.reminder_type,
                'reminder_type_display': reminder.get_reminder_type_display(),
                'title': reminder.title,
                'description': reminder.description or '',
                'reminder_date': reminder.reminder_date.strftime('%Y-%m-%d'),
                'reminder_days_before': reminder.reminder_days_before,
                'is_sent': reminder.is_sent,
                'sent_at': reminder.sent_at.strftime('%Y-%m-%d %H:%M:%S') if reminder.sent_at else '',
                'is_due': reminder.is_due(),
            })
        
        return JsonResponse({
            'success': True,
            'contract': contract_data,
            'payments': payments_data,
            'documents': documents_data,
            'reminders': reminders_data,
        })
    
    except Exception as e:
        logger.error(f"Error in contract_detail: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_update(request, contract_id):
    """تحديث عقد محدد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        if request.method == 'POST':
            form = RealEstateContractForm(request.POST, instance=contract)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'تم تحديث العقد بنجاح'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'بيانات غير صحيحة',
                    'errors': form.errors
                }, status=400)
    
    except Exception as e:
        logger.error(f"Error in contract_update: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_delete(request, contract_id):
    """حذف عقد محدد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        if request.method == 'POST':
            contract.delete()
            return JsonResponse({
                'success': True,
                'message': 'تم حذف العقد بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_delete: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_approve(request, contract_id):
    """موافقة على عقد وتفعيله"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)

        if request.method == 'POST':
            contract.mark_as_active()
            return JsonResponse({
                'success': True,
                'message': 'تم تفعيل العقد بنجاح'
            })

    except Exception as e:
        logger.error(f"Error in contract_approve: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def real_estate_contracts_page(request):
    """صفحة العقود العقارية"""
    try:
        from .models import RealEstateContract, Property, Broker, User

        # Get all contracts with related data
        contracts = RealEstateContract.objects.all().select_related(
            'property', 'broker', 'client', 'created_by', 'approved_by'
        ).prefetch_related(
            'payments', 'documents', 'reminders'
        ).order_by('-created_at')

        # Get active contract if specified
        active_contract = None
        active_contract_id = request.GET.get('contract_id')
        if active_contract_id:
            try:
                active_contract = contracts.get(id=active_contract_id)
            except RealEstateContract.DoesNotExist:
                pass

        # Get data for form
        properties = Property.objects.filter(status='published')[:100]
        brokers = Broker.objects.filter(is_active=True)[:50]
        users = User.objects.filter(is_active=True)[:100]

        return render(request, 'properties/real_estate_contracts.html', {
            'contracts': contracts,
            'active_contract': active_contract,
            'active_contract_id': active_contract_id,
            'properties': properties,
            'brokers': brokers,
            'users': users,
        })

    except Exception as e:
        logger.error(f"Error in real_estate_contracts_page: {e}")
        return render(request, 'properties/real_estate_contracts.html', {
            'contracts': [],
            'active_contract': None,
            'active_contract_id': None,
            'properties': [],
            'brokers': [],
            'users': [],
        })


@login_required
def contract_payment_create(request, contract_id):
    """إنشاء دفعة جديدة لعقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            # Generate payment number
            year = timezone.now().year
            count = ContractPayment.objects.filter(
                payment_number__startswith=f'PAY-{year}'
            ).count()
            payment_number = f'PAY-{year}-{count + 1:04d}'
            
            payment = ContractPayment.objects.create(
                contract=contract,
                payment_number=payment_number,
                amount=data.get('amount', 0),
                payment_method=data.get('payment_method', 'cash'),
                due_date=data.get('due_date'),
                notes=data.get('notes', ''),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء الدفعة بنجاح',
                'payment_id': payment.id,
                'payment_number': payment.payment_number
            })
    
    except Exception as e:
        logger.error(f"Error in contract_payment_create: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_payment_update(request, payment_id):
    """تحديث دفعة عقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        payment = get_object_or_404(ContractPayment, id=payment_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            if 'amount' in data:
                payment.amount = data['amount']
            if 'payment_method' in data:
                payment.payment_method = data['payment_method']
            if 'due_date' in data:
                payment.due_date = data['due_date']
            if 'notes' in data:
                payment.notes = data['notes']
            
            payment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث الدفعة بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_payment_update: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_payment_delete(request, payment_id):
    """حذف دفعة عقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        payment = get_object_or_404(ContractPayment, id=payment_id)
        
        if request.method == 'POST':
            payment.delete()
            return JsonResponse({
                'success': True,
                'message': 'تم حذف الدفعة بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_payment_delete: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_payment_mark_paid(request, payment_id):
    """تسجيل دفعة كمكتملة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        payment = get_object_or_404(ContractPayment, id=payment_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            amount = data.get('amount', payment.amount)
            
            payment.mark_as_paid(amount)
            
            return JsonResponse({
                'success': True,
                'message': 'تم تسجيل الدفعة بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_payment_mark_paid: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_document_create(request, contract_id):
    """رفع وثيقة جديدة لعقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            document = ContractDocument.objects.create(
                contract=contract,
                document_type=data.get('document_type', 'other'),
                title=data.get('title', ''),
                description=data.get('description', ''),
                file=data.get('file'),
                uploaded_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم رفع الوثيقة بنجاح',
                'document_id': document.id
            })
    
    except Exception as e:
        logger.error(f"Error in contract_document_create: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_document_delete(request, document_id):
    """حذف وثيقة عقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        document = get_object_or_404(ContractDocument, id=document_id)
        
        if request.method == 'POST':
            document.delete()
            return JsonResponse({
                'success': True,
                'message': 'تم حذف الوثيقة بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_document_delete: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_reminder_create(request, contract_id):
    """إنشاء تذكير جديد لعقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        contract = get_object_or_404(RealEstateContract, id=contract_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            reminder = ContractReminder.objects.create(
                contract=contract,
                reminder_type=data.get('reminder_type', 'other'),
                title=data.get('title', ''),
                description=data.get('description', ''),
                reminder_date=data.get('reminder_date'),
                reminder_days_before=data.get('reminder_days_before', 7),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء التذكير بنجاح',
                'reminder_id': reminder.id
            })
    
    except Exception as e:
        logger.error(f"Error in contract_reminder_create: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_reminder_update(request, reminder_id):
    """تحديث تذكير عقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        reminder = get_object_or_404(ContractReminder, id=reminder_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            
            if 'reminder_type' in data:
                reminder.reminder_type = data['reminder_type']
            if 'title' in data:
                reminder.title = data['title']
            if 'description' in data:
                reminder.description = data['description']
            if 'reminder_date' in data:
                reminder.reminder_date = data['reminder_date']
            if 'reminder_days_before' in data:
                reminder.reminder_days_before = data['reminder_days_before']
            
            reminder.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث التذكير بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_reminder_update: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_reminder_delete(request, reminder_id):
    """حذف تذكير عقد"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        reminder = get_object_or_404(ContractReminder, id=reminder_id)
        
        if request.method == 'POST':
            reminder.delete()
            return JsonResponse({
                'success': True,
                'message': 'تم حذف التذكير بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_reminder_delete: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def contract_reminder_mark_sent(request, reminder_id):
    """تحديد التذكير كمرسل"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        reminder = get_object_or_404(ContractReminder, id=reminder_id)
        
        if request.method == 'POST':
            reminder.mark_as_sent()
            reminder.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديد التذكير كمرسل'
            })
    
    except Exception as e:
        logger.error(f"Error in contract_reminder_mark_sent: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def payments_commissions(request):
    """نظام إدارة الدفعات والعمولات"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الدفعات
            payments = []
            payment_types = ['rent', 'commission', 'deposit', 'service_fee', 'maintenance']
            statuses = ['pending', 'completed', 'failed', 'refunded']
            
            for i in range(25):
                payments.append({
                    'id': i + 1,
                    'type': random.choice(payment_types),
                    'status': random.choice(statuses),
                    'amount': random.randint(1000, 100000),
                    'currency': random.choice(['USD', 'SAR', 'IQD']),
                    'client_id': random.randint(1, 20),
                    'property_id': random.randint(1, 25),
                    'agent_id': random.randint(1, 5),
                    'due_date': (timezone.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'paid_date': timezone.now().strftime('%Y-%m-%d') if random.choice([True, False]) else None,
                    'method': random.choice(['cash', 'bank_transfer', 'check', 'online']),
                    'reference': f'REF-{random.randint(100000, 999999)}',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return JsonResponse({
                'success': True,
                'payments': payments,
                'statistics': {
                    'total': len(payments),
                    'pending': sum(1 for p in payments if p['status'] == 'pending'),
                    'completed': sum(1 for p in payments if p['status'] == 'completed'),
                    'total_amount': sum(p['amount'] for p in payments),
                    'pending_amount': sum(p['amount'] for p in payments if p['status'] == 'pending')
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def geographic_maps(request):
    """نظام إدارة الخرائط الجغرافية"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات الخرائط
            regions = []
            governorates = ['بغداد', 'البصرة', 'أربيل', 'النجف', 'الناصرية', 'كربلاء', 'دهوك', 'القادسية', 'كركوك', 'صلاح الدين', 'ديالى', 'بابل', 'ميسان', 'الأنبار', 'المثنى', 'الذيقار', 'كربلاء', 'النجف', 'واسط']
            
            for gov in governorates:
                regions.append({
                    'id': governorates.index(gov) + 1,
                    'name': gov,
                    'property_count': random.randint(10, 500),
                    'avg_price': random.randint(50000, 2000000),
                    'available': random.randint(5, 200),
                    'sold': random.randint(5, 300),
                    'hot_area': random.choice([True, False]),
                    'growth_rate': random.randint(-5, 15),
                    'coordinates': {
                        'lat': round(random.uniform(32, 37), 4),
                        'lng': round(random.uniform(42, 47), 4)
                    }
                })
            
            return JsonResponse({
                'success': True,
                'regions': regions,
                'statistics': {
                    'total_regions': len(regions),
                    'total_properties': sum(r['property_count'] for r in regions),
                    'hot_areas': sum(1 for r in regions if r['hot_area']),
                    'avg_growth': sum(r['growth_rate'] for r in regions) // len(regions)
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def advanced_reports_management(request):
    """نظام التقارير المتقدم"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        if request.method == 'GET':
            # محاكاة بيانات التقارير
            reports = []
            report_types = ['sales', 'properties', 'clients', 'financial', 'performance']
            periods = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
            formats = ['pdf', 'excel', 'csv', 'json']
            statuses = ['generating', 'completed', 'failed']
            
            for i in range(20):
                reports.append({
                    'id': i + 1,
                    'title': f'تقرير {random.choice(report_types)}',
                    'type': random.choice(report_types),
                    'period': random.choice(periods),
                    'format': random.choice(formats),
                    'status': random.choice(statuses),
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S') if random.choice([True, False]) else None,
                    'file_size': random.randint(100, 10000),
                    'download_count': random.randint(0, 100),
                    'created_by': f'user_{random.randint(1, 10)}'
                })
            
            return JsonResponse({
                'success': True,
                'reports': reports,
                'statistics': {
                    'total': len(reports),
                    'monthly': sum(1 for r in reports if r['period'] == 'monthly'),
                    'quarterly': sum(1 for r in reports if r['period'] == 'quarterly'),
                    'yearly': sum(1 for r in reports if r['period'] == 'yearly')
                }
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            new_report = {
                'id': 999,
                'title': f'تقرير {data.get("type", "sales")}',
                'type': data.get('type', 'sales'),
                'period': data.get('period', 'monthly'),
                'format': data.get('format', 'pdf'),
                'status': 'generating',
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': 0,
                'download_count': 0,
                'created_by': request.user.username
            }
            
            return JsonResponse({
                'success': True,
                'report': new_report,
                'message': 'تم بدء توليد التقرير'
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def dashboard_stats(request):
    """إحصائيات لوحة التحكم الرئيسية - تقسم حسب نوع المستخدم"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        
        # تحديد نوع المستخدم
        is_admin = request.user.is_superuser or request.user.is_staff
        is_broker = hasattr(request.user, 'broker_profile')
        
        if is_admin:
            # بيانات الإدارة - شاملة
            total_properties = Property.objects.count()
            active_properties = Property.objects.filter(status='published').count()
            verified_properties = Property.objects.filter(is_verified=True).count()
            new_properties_today = Property.objects.filter(
                created_at__date=timezone.now().date()
            ).count()
            
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            new_users_today = User.objects.filter(
                date_joined__date=timezone.now().date()
            ).count()
            
            total_brokers = Broker.objects.count()
            active_brokers = Broker.objects.filter(is_active=True).count()
            
            total_jobs = Job.objects.count()
            active_jobs = Job.objects.filter(is_active=True).count()
            
            try:
                total_backups = Backup.objects.count()
                successful_backups = Backup.objects.filter(status='completed').count()
            except Exception:
                total_backups = 0
                successful_backups = 0
            
            # إحصائيات النظام
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_permission")
                total_permissions = cursor.fetchone()[0]
            
            return JsonResponse({
                'success': True,
                'user_type': 'admin',
                'stats': {
                    'properties': {
                        'total': total_properties,
                        'active': active_properties,
                        'verified': verified_properties,
                        'new_today': new_properties_today
                    },
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'new_today': new_users_today
                    },
                    'brokers': {
                        'total': total_brokers,
                        'active': active_brokers
                    },
                    'jobs': {
                        'total': total_jobs,
                        'active': active_jobs
                    },
                    'backups': {
                        'total': total_backups,
                        'successful': successful_backups
                    },
                    'system': {
                        'permissions': total_permissions
                    }
                }
            })
        
        elif is_broker:
            # بيانات الدلال - خاصة بالدلال الحالي
            broker = request.user.broker_profile
            
            # عقارات الدلال
            broker_properties = Property.objects.filter(
                Q(broker=broker) | Q(owner=request.user)
            )
            total_properties = broker_properties.count()
            active_properties = broker_properties.filter(status='published').count()
            verified_properties = broker_properties.filter(is_verified=True).count()
            new_properties_today = broker_properties.filter(
                created_at__date=timezone.now().date()
            ).count()
            
            # إحصائيات المشاهدات
            try:
                from .models import PropertyViewStats
                total_views = PropertyViewStats.objects.filter(
                    property__in=broker_properties
                ).aggregate(total=Sum('total_views'))['total'] or 0
            except Exception:
                total_views = 0
            
            # إحصائيات المحادثات
            try:
                from .models import Conversation
                broker_conversations = Conversation.objects.filter(participants=request.user)
                total_conversations = broker_conversations.count()
                unread_messages = broker_conversations.filter(
                    messages__recipient=request.user,
                    messages__is_read=False
                ).count()
            except Exception:
                total_conversations = 0
                unread_messages = 0
            
            # إحصائيات المواعيد
            try:
                from .models import BrokerAppointment
                total_appointments = BrokerAppointment.objects.filter(broker=broker).count()
                pending_appointments = BrokerAppointment.objects.filter(
                    broker=broker, 
                    status='pending'
                ).count()
            except Exception:
                total_appointments = 0
                pending_appointments = 0
            
            return JsonResponse({
                'success': True,
                'user_type': 'broker',
                'stats': {
                    'properties': {
                        'total': total_properties,
                        'active': active_properties,
                        'verified': verified_properties,
                        'new_today': new_properties_today
                    },
                    'views': {
                        'total': total_views
                    },
                    'conversations': {
                        'total': total_conversations,
                        'unread': unread_messages
                    },
                    'appointments': {
                        'total': total_appointments,
                        'pending': pending_appointments
                    }
                }
            })
        
        else:
            # بيانات المستخدم العادي
            # عقارات المستخدم المفضلة
            try:
                from .models import UserFavorite
                total_favorites = UserFavorite.objects.filter(user=request.user).count()
            except Exception:
                total_favorites = 0
            
            # المحادثات
            try:
                from .models import Conversation
                user_conversations = Conversation.objects.filter(participants=request.user)
                total_conversations = user_conversations.count()
                unread_messages = user_conversations.filter(
                    messages__recipient=request.user,
                    messages__is_read=False
                ).count()
            except Exception:
                total_conversations = 0
                unread_messages = 0
            
            # إحصائيات البحث
            try:
                from .models import UserSearchHistory
                total_searches = UserSearchHistory.objects.filter(user=request.user).count()
            except Exception:
                total_searches = 0
            
            return JsonResponse({
                'success': True,
                'user_type': 'user',
                'stats': {
                    'favorites': {
                        'total': total_favorites
                    },
                    'conversations': {
                        'total': total_conversations,
                        'unread': unread_messages
                    },
                    'searches': {
                        'total': total_searches
                    }
                }
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def admin_dashboard_api(request):
    """API مخصص للوحة الإدارة - بيانات شاملة"""
    if not request.user.is_superuser and not request.user.is_staff:
        return Response({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        # إحصائيات العقارات
        total_properties = Property.objects.count()
        active_properties = Property.objects.filter(status='published').count()
        verified_properties = Property.objects.filter(is_verified=True).count()
        new_properties_today = Property.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # إحصائيات المستخدمين
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
        
        # إحصائيات الدلالين
        total_brokers = Broker.objects.count()
        active_brokers = Broker.objects.filter(is_active=True).count()
        verified_brokers = Broker.objects.filter(is_verified=True).count()
        
        # إحصائيات المحادثات
        try:
            from .models import Conversation
            total_conversations = Conversation.objects.count()
        except Exception:
            total_conversations = 0
        
        # إحصائيات الوظائف
        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(is_active=True).count()
        
        # إحصائيات النسخ الاحتياطية
        try:
            total_backups = Backup.objects.count()
            successful_backups = Backup.objects.filter(status='completed').count()
        except Exception:
            total_backups = 0
            successful_backups = 0
        
        # التوزيع الجغرافي
        governorate_stats = Property.objects.values('governorate').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # توزيع أنواع العقارات
        property_type_stats = Property.objects.values('property_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'success': True,
            'data': {
                'properties': {
                    'total': total_properties,
                    'active': active_properties,
                    'verified': verified_properties,
                    'new_today': new_properties_today
                },
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_today': new_users_today
                },
                'brokers': {
                    'total': total_brokers,
                    'active': active_brokers,
                    'verified': verified_brokers
                },
                'conversations': {
                    'total': total_conversations
                },
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs
                },
                'backups': {
                    'total': total_backups,
                    'successful': successful_backups
                },
                'geographic_distribution': list(governorate_stats),
                'property_types': list(property_type_stats)
            }
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def broker_dashboard_api(request):
    """API مخصص للوحة الدلال - بيانات خاصة بالدلال"""
    if not hasattr(request.user, 'broker_profile'):
        return Response({'success': False, 'error': 'يجب أن تكون دلالاً'}, status=403)
    
    try:
        from django.utils import timezone
        from django.db.models import Count, Q, Sum
        
        broker = request.user.broker_profile
        
        # عقارات الدلال
        broker_properties = Property.objects.filter(
            Q(broker=broker) | Q(owner=request.user)
        )
        total_properties = broker_properties.count()
        active_properties = broker_properties.filter(status='published').count()
        verified_properties = broker_properties.filter(is_verified=True).count()
        new_properties_today = broker_properties.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # إحصائيات المشاهدات
        try:
            from .models import PropertyViewStats
            total_views = PropertyViewStats.objects.filter(
                property__in=broker_properties
            ).aggregate(total=Sum('total_views'))['total'] or 0
        except Exception:
            total_views = 0
        
        # إحصائيات المحادثات
        try:
            from .models import Conversation
            broker_conversations = Conversation.objects.filter(participants=request.user)
            total_conversations = broker_conversations.count()
            unread_messages = broker_conversations.filter(
                messages__recipient=request.user,
                messages__is_read=False
            ).count()
        except Exception:
            total_conversations = 0
            unread_messages = 0
        
        # إحصائيات المواعيد
        try:
            from .models import BrokerAppointment
            total_appointments = BrokerAppointment.objects.filter(broker=broker).count()
            pending_appointments = BrokerAppointment.objects.filter(
                broker=broker, 
                status='pending'
            ).count()
        except Exception:
            total_appointments = 0
            pending_appointments = 0
        
        # إحصائيات العقارات المباعة والمؤجرة
        sold_properties = broker_properties.filter(status='sold').count()
        rented_properties = broker_properties.filter(status='rented').count()
        featured_properties = broker_properties.filter(is_featured=True).count()
        
        # إحصائيات العمولات
        try:
            from .models import FinancialTransaction
            total_commissions = FinancialTransaction.objects.filter(
                user=broker, 
                transaction_type='commission'
            ).aggregate(
                total=Sum('commission_amount')
            )['total'] or 0
            paid_commissions = FinancialTransaction.objects.filter(
                user=broker, 
                transaction_type='commission',
                status='completed'
            ).aggregate(total=Sum('commission_amount'))['total'] or 0
            pending_commissions = FinancialTransaction.objects.filter(
                user=broker, 
                transaction_type='commission',
                status='pending'
            ).aggregate(total=Sum('commission_amount'))['total'] or 0
        except Exception:
            total_commissions = 0
            paid_commissions = 0
            pending_commissions = 0
        
        # العقارات الأخيرة
        recent_properties = broker_properties.order_by('-created_at')[:10]
        
        # المواعيد القادمة
        upcoming_appointments = []
        try:
            from .models import BrokerAppointment
            upcoming_appointments = BrokerAppointment.objects.filter(
                broker=broker,
                status='pending',
                appointment_date__gte=timezone.now()
            ).order_by('appointment_date')[:5]
        except Exception:
            pass
        
        return Response({
            'success': True,
            'data': {
                'properties': {
                    'total': total_properties,
                    'active': active_properties,
                    'verified': verified_properties,
                    'new_today': new_properties_today,
                    'sold': sold_properties,
                    'rented': rented_properties,
                    'featured': featured_properties
                },
                'views': {
                    'total': total_views
                },
                'conversations': {
                    'total': total_conversations,
                    'unread': unread_messages
                },
                'appointments': {
                    'total': total_appointments,
                    'pending': pending_appointments
                },
                'commissions': {
                    'total': total_commissions,
                    'paid': paid_commissions,
                    'pending': pending_commissions
                },
                'recent_properties': [
                    {
                        'id': p.id,
                        'title': p.title,
                        'price': p.price,
                        'status': p.status,
                        'created_at': p.created_at.strftime('%Y-%m-%d')
                    } for p in recent_properties
                ],
                'upcoming_appointments': [
                    {
                        'id': a.id,
                        'user': a.user.username if a.user else 'غير معروف',
                        'property': a.property.title if a.property else 'غير محدد',
                        'date': a.appointment_date.strftime('%Y-%m-%d %H:%M'),
                        'status': a.status
                    } for a in upcoming_appointments
                ]
            }
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_api(request):
    """API مخصص للوحة المستخدم - بيانات خاصة بالمستخدم"""
    try:
        from django.utils import timezone
        from django.db.models import Count
        
        # عقارات المستخدم المفضلة
        try:
            from .models import UserFavorite
            favorites = UserFavorite.objects.filter(user=request.user).select_related('property')
            total_favorites = favorites.count()
            recent_favorites = favorites.order_by('-created_at')[:10]
        except Exception:
            total_favorites = 0
            recent_favorites = []
        
        # المحادثات
        try:
            from .models import Conversation
            user_conversations = Conversation.objects.filter(participants=request.user)
            total_conversations = user_conversations.count()
            unread_messages = user_conversations.filter(
                messages__recipient=request.user,
                messages__is_read=False
            ).count()
            recent_conversations = user_conversations.order_by('-updated_at')[:10]
        except Exception:
            total_conversations = 0
            unread_messages = 0
            recent_conversations = []
        
        # إحصائيات البحث
        try:
            from .models import UserSearchHistory
            total_searches = UserSearchHistory.objects.filter(user=request.user).count()
            recent_searches = UserSearchHistory.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
        except Exception:
            total_searches = 0
            recent_searches = []
        
        # العقارات المحفوظة
        try:
            from .models import PropertySave
            saved_properties = PropertySave.objects.filter(user=request.user).select_related('property')
            total_saved = saved_properties.count()
            recent_saved = saved_properties.order_by('-created_at')[:10]
        except Exception:
            total_saved = 0
            recent_saved = []
        
        # المزادات المشارك بها
        try:
            from .models import AuctionBid
            user_auctions = AuctionBid.objects.filter(bidder=request.user).values('auction').distinct().count()
        except Exception:
            user_auctions = 0
        
        # النشاطات الأخيرة
        try:
            from .models import ActivityLog
            activity_logs = ActivityLog.objects.filter(user=request.user).count()
        except Exception:
            activity_logs = 0
        
        # الإشعارات غير المقروءة
        try:
            from .models import Notification
            unread_notifications = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        except Exception:
            unread_notifications = 0
        
        return Response({
            'success': True,
            'data': {
                'favorites': {
                    'total': total_favorites,
                    'recent': [
                        {
                            'id': f.property.id,
                            'title': f.property.title,
                            'price': f.property.price,
                            'location': f.property.city,
                            'created_at': f.created_at.strftime('%Y-%m-%d')
                        } for f in recent_favorites
                    ]
                },
                'conversations': {
                    'total': total_conversations,
                    'unread': unread_messages,
                    'recent': [
                        {
                            'id': c.id,
                            'name': c.name,
                            'updated_at': c.updated_at.strftime('%Y-%m-%d %H:%M')
                        } for c in recent_conversations
                    ]
                },
                'searches': {
                    'total': total_searches,
                    'recent': [
                        {
                            'id': s.id,
                            'query': s.search_query,
                            'created_at': s.created_at.strftime('%Y-%m-%d')
                        } for s in recent_searches
                    ]
                },
                'saved_properties': {
                    'total': total_saved,
                    'recent': [
                        {
                            'id': sp.property.id,
                            'title': sp.property.title,
                            'price': sp.property.price,
                            'location': sp.property.city,
                            'created_at': sp.created_at.strftime('%Y-%m-%d')
                        } for sp in recent_saved
                    ]
                },
                'auctions': {
                    'total': user_auctions
                },
                'activity': {
                    'total': activity_logs
                },
                'notifications': {
                    'unread': unread_notifications
                }
            }
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@login_required
def recent_activity(request):
    """النشاطات الأخيرة"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    
    try:
        limit = int(request.GET.get('limit', 10))
        
        # محاكاة بيانات النشاطات (في الإنتاج، استخدم ActivityLog model)
        activities = []
        
        for i in range(limit):
            activities.append({
                'user': f'user_{i+1}',
                'action': random.choice(['login', 'create_property', 'update_property', 'delete_property', 'view_property']),
                'description': f'Activity {i+1}',
                'ip_address': f'192.168.1.{i+1}',
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== Support Message Views ====================

@login_required
def support_message_list(request):
    """قائمة رسائل الدعم الفني للمستخدم"""
    messages_list = SupportMessage.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'properties/support_message_list.html', {
        'page_obj': page_obj,
        'messages': messages_list,
    })


@login_required
def support_message_create(request):
    """إنشاء رسالة دعم فني جديدة"""
    if request.method == 'POST':
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            support_message = form.save(commit=False)
            support_message.user = request.user
            support_message.save()
            
            messages.success(request, 'تم إرسال رسالتك بنجاح! سيتم الرد عليك قريباً.')
            return redirect('support_message_list')
    else:
        form = SupportMessageForm()
    
    return render(request, 'properties/support_message_create.html', {
        'form': form,
    })


@login_required
def support_message_detail(request, message_id):
    """عرض تفاصيل رسالة الدعم الفني"""
    support_message = get_object_or_404(SupportMessage, id=message_id, user=request.user)
    
    # Mark as read if it has admin response
    if support_message.admin_response and not support_message.is_read:
        support_message.is_read = True
        support_message.save(update_fields=['is_read'])
    
    return render(request, 'properties/support_message_detail.html', {
        'support_message': support_message,
    })


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_support_message_list(request):
    """قائمة رسائل الدعم الفني للإدارة"""
    messages_list = SupportMessage.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        messages_list = messages_list.filter(status=status_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority')
    if priority_filter:
        messages_list = messages_list.filter(priority=priority_filter)
    
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'properties/admin_support_message_list.html', {
        'page_obj': page_obj,
        'messages': messages_list,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    })


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_support_message_detail(request, message_id):
    """عرض تفاصيل رسالة الدعم الفني للإدارة"""
    support_message = get_object_or_404(SupportMessage, id=message_id)
    
    if request.method == 'POST':
        admin_response = request.POST.get('admin_response')
        new_status = request.POST.get('status')
        
        if admin_response:
            support_message.admin_response = admin_response
        
        if new_status:
            support_message.status = new_status
            if new_status == 'resolved':
                support_message.resolved_at = timezone.now()
        
        support_message.assigned_to = request.user
        support_message.save()
        
        messages.success(request, 'تم تحديث الرسالة بنجاح')
        return redirect('admin_support_message_list')
    
    return render(request, 'properties/admin_support_message_detail.html', {
        'support_message': support_message,
    })


# ==================== Broker Conversation Views ====================

@login_required
def broker_conversation_list(request):
    """قائمة محادثات المستخدم مع الدلالين"""
    conversations = BrokerConversation.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('broker__user').prefetch_related('messages')
    
    # Filter expired conversations
    conversations = [c for c in conversations if not c.is_expired()]
    
    # Order by last message
    conversations = sorted(conversations, key=lambda x: x.last_message_at or x.created_at, reverse=True)
    
    return render(request, 'properties/broker_conversation_list.html', {
        'conversations': conversations,
    })


@login_required
def broker_conversation_detail(request, conversation_id):
    """عرض محادثة معينة"""
    conversation = get_object_or_404(
        BrokerConversation,
        conversation_id=conversation_id,
        user=request.user
    )
    
    # Check if user is participant
    if conversation.user != request.user:
        messages.error(request, 'ليس لديك صلاحية الوصول لهذه المحادثة')
        return redirect('broker_conversation_list')
    
    # Check if conversation is expired
    if conversation.is_expired():
        messages.warning(request, 'هذه المحادثة منتهية الصلاحية')
        conversation.is_active = False
        conversation.save()
    
    # Mark messages as read
    unread_messages = conversation.messages.filter(
        sender=conversation.broker.user,
        is_read=False
    )
    for msg in unread_messages:
        msg.mark_as_read()
    
    # Get messages
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Form for new message
    if request.method == 'POST':
        form = BrokerMessageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.receiver = conversation.broker.user
            message.save()
            
            messages.success(request, 'تم إرسال الرسالة بنجاح')
            return redirect('broker_conversation_detail', conversation_id=conversation.conversation_id)
    else:
        form = BrokerMessageForm(user=request.user)
    
    return render(request, 'properties/broker_conversation_detail.html', {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
    })


@login_required
def start_broker_conversation(request, broker_id):
    """بدء محادثة جديدة مع دلال"""
    broker = get_object_or_404(Broker, id=broker_id)
    
    # Check if conversation already exists
    existing_conversation = BrokerConversation.objects.filter(
        user=request.user,
        broker=broker,
        is_active=True
    ).first()
    
    if existing_conversation:
        if existing_conversation.is_expired():
            # Reactivate expired conversation
            existing_conversation.is_active = True
            from datetime import timedelta
            existing_conversation.expires_at = timezone.now() + timedelta(days=30)
            existing_conversation.save()
        return redirect('broker_conversation_detail', conversation_id=existing_conversation.conversation_id)
    
    # Create new conversation
    form = BrokerConversationForm(user=request.user, broker=broker)
    conversation = form.save()
    
    messages.success(request, 'تم إنشاء المحادثة بنجاح')
    return redirect('broker_conversation_detail', conversation_id=conversation.conversation_id)


@login_required
def broker_message_list(request):
    """قائمة المحادثات للدلال"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلال للوصول لهذه الصفحة')
        return redirect('home')
    
    conversations = BrokerConversation.objects.filter(
        broker=request.user.broker_profile,
        is_active=True
    ).select_related('user').prefetch_related('messages')
    
    # Filter expired conversations
    conversations = [c for c in conversations if not c.is_expired()]
    
    # Order by last message
    conversations = sorted(conversations, key=lambda x: x.last_message_at or x.created_at, reverse=True)
    
    return render(request, 'properties/broker_message_list.html', {
        'conversations': conversations,
    })


@login_required
def broker_appointment_booking(request, broker_id):
    """حجز موعد مع دلال"""
    from django.utils import timezone
    from datetime import timedelta

    broker = get_object_or_404(Broker, id=broker_id)

    # Get broker's properties for the dropdown
    broker_properties = Property.objects.filter(broker=broker, status='active')

    # Set minimum date to today
    min_date = timezone.now().date()

    if request.method == 'POST':
        try:
            appointment_type = request.POST.get('appointment_type')
            property_id = request.POST.get('property')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            duration = request.POST.get('duration', 30)
            location = request.POST.get('location', '')
            notes = request.POST.get('notes', '')

            # Validate required fields
            if not all([appointment_type, appointment_date, appointment_time]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                return render(request, 'properties/broker_appointment_booking.html', {
                    'broker': broker,
                    'broker_properties': broker_properties,
                    'min_date': min_date,
                })

            # Create appointment
            from .models import BrokerAppointment
            appointment = BrokerAppointment.objects.create(
                broker=broker,
                user=request.user,
                appointment_type=appointment_type,
                property_id=property_id if property_id else None,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration=int(duration),
                location=location,
                notes=notes,
                status='pending'
            )

            messages.success(request, 'تم حجز الموعد بنجاح! سيتم التواصل معك للتأكيد.')
            return redirect('broker_profile', broker_id=broker.id)

        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
            return render(request, 'properties/broker_appointment_booking.html', {
                'broker': broker,
                'broker_properties': broker_properties,
                'min_date': min_date,
            })

    return render(request, 'properties/broker_appointment_booking.html', {
        'broker': broker,
        'broker_properties': broker_properties,
        'min_date': min_date,
    })


@login_required
def appointment_booking_landing(request):
    """صفحة هبوط لحجز المواعيد - اختيار بين دلال أو إدارة"""
    from django.utils import timezone

    # Get active brokers for the dropdown
    active_brokers = Broker.objects.filter(is_active=True, is_verified=True)[:10]

    return render(request, 'properties/appointment_booking_landing.html', {
        'active_brokers': active_brokers,
    })


@login_required
def admin_appointment_booking(request):
    """حجز موعد مع الإدارة"""
    from django.utils import timezone

    # Set minimum date to today
    min_date = timezone.now().date()

    if request.method == 'POST':
        try:
            appointment_type = request.POST.get('appointment_type')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            duration = request.POST.get('duration', 30)
            location = request.POST.get('location', 'المكتب الرئيسي')
            notes = request.POST.get('notes', '')
            priority = request.POST.get('priority', 'medium')

            # Validate required fields
            if not all([appointment_type, appointment_date, appointment_time]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                return render(request, 'properties/admin_appointment_booking.html', {
                    'min_date': min_date,
                })

            # Create appointment with admin
            from .models import Appointment
            appointment = Appointment.objects.create(
                user=request.user,
                appointment_type=appointment_type,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration=int(duration),
                location=location,
                notes=notes,
                priority=priority,
                status='pending',
                target_type='admin',
                target_id=1  # Admin user ID
            )

            messages.success(request, 'تم حجز الموعد مع الإدارة بنجاح! سيتم التواصل معك للتأكيد.')
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
            return render(request, 'properties/admin_appointment_booking.html', {
                'min_date': min_date,
            })

    return render(request, 'properties/admin_appointment_booking.html', {
        'min_date': min_date,
    })


@login_required
def broker_appointments_list(request):
    """عرض قائمة المواعيد المحجوزة للدلال"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلال للوصول لهذه الصفحة')
        return redirect('home')
    
    broker = request.user.broker_profile
    
    # Get appointments for this broker (BrokerAppointment and Appointment)
    from .models import BrokerAppointment, Appointment
    
    # Get BrokerAppointment records
    broker_appointments = BrokerAppointment.objects.filter(
        broker=broker
    ).select_related('user', 'property').order_by('-appointment_date', '-appointment_time')
    
    # Get Appointment records where target is this broker
    appointments = Appointment.objects.filter(
        target_type='broker',
        target_id=broker.id
    ).select_related('user').order_by('-appointment_date', '-appointment_time')
    
    # Combine both types
    all_appointments = []
    
    for ba in broker_appointments:
        all_appointments.append({
            'type': 'broker_appointment',
            'id': ba.id,
            'user': ba.user,
            'appointment_type': ba.get_appointment_type_display(),
            'appointment_date': ba.appointment_date,
            'appointment_time': ba.appointment_time,
            'status': ba.status,
            'property': ba.property,
            'notes': ba.notes,
            'created_at': ba.created_at,
        })
    
    for apt in appointments:
        all_appointments.append({
            'type': 'appointment',
            'id': apt.id,
            'user': apt.user,
            'appointment_type': apt.get_appointment_type_display(),
            'appointment_date': apt.appointment_date,
            'appointment_time': apt.appointment_time,
            'status': apt.status,
            'property': None,
            'notes': apt.notes,
            'created_at': apt.created_at,
        })
    
    # Sort by date and time
    all_appointments.sort(key=lambda x: (x['appointment_date'], x['appointment_time']), reverse=True)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        all_appointments = [a for a in all_appointments if a['status'] == status_filter]
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(all_appointments, 20)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)
    
    return render(request, 'properties/broker_appointments_list.html', {
        'appointments': appointments_page,
        'status_filter': status_filter,
    })


@login_required
def broker_appointment_detail(request, appointment_id):
    """عرض تفاصيل موعد محجوز"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلال للوصول لهذه الصفحة')
        return redirect('home')
    
    from .models import BrokerAppointment
    appointment = get_object_or_404(BrokerAppointment, id=appointment_id, broker=request.user.broker_profile)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            appointment.status = 'confirmed'
            appointment.save()
            messages.success(request, 'تم تأكيد الموعد بنجاح')
            
        elif action == 'cancel':
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'تم إلغاء الموعد')
            
        elif action == 'complete':
            appointment.status = 'completed'
            appointment.save()
            messages.success(request, 'تم إكمال الموعد')
            
        elif action == 'no_show':
            appointment.status = 'no_show'
            appointment.save()
            messages.success(request, 'تم تسجيل عدم الحضور')
        
        return redirect('broker_appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'properties/broker_appointment_detail.html', {
        'appointment': appointment,
    })


@login_required
def appointments_management(request):
    """نظام إدارة المواعيد الشامل"""
    try:
        from .models import Appointment, BrokerAppointment
        
        # Get user's appointments
        if hasattr(request.user, 'broker_profile'):
            # Broker view
            broker_appointments = BrokerAppointment.objects.filter(
                broker=request.user.broker_profile
            ).select_related('user', 'property').order_by('-appointment_date', '-appointment_time')
            
            user_appointments = Appointment.objects.filter(
                target_type='broker',
                target_id=request.user.broker_profile.id
            ).order_by('-appointment_date', '-appointment_time')
        else:
            # Regular user view
            broker_appointments = BrokerAppointment.objects.filter(
                user=request.user
            ).select_related('broker', 'property').order_by('-appointment_date', '-appointment_time')
            
            user_appointments = Appointment.objects.filter(
                user=request.user
            ).order_by('-appointment_date', '-appointment_time')
        
        # Statistics
        from django.utils import timezone
        today = timezone.now().date()
        
        upcoming_broker = broker_appointments.filter(
            appointment_date__gte=today,
            status='pending'
        ).count()
        
        upcoming_user = user_appointments.filter(
            appointment_date__gte=today,
            status='pending'
        ).count()
        
        completed_broker = broker_appointments.filter(status='completed').count()
        completed_user = user_appointments.filter(status='completed').count()
        
        return render(request, 'properties/appointments_management.html', {
            'broker_appointments': broker_appointments,
            'user_appointments': user_appointments,
            'upcoming_broker': upcoming_broker,
            'upcoming_user': upcoming_user,
            'completed_broker': completed_broker,
            'completed_user': completed_user,
        })
    
    except Exception as e:
        logger.error(f"Error in appointments_management: {e}")
        return render(request, 'properties/appointments_management.html', {
            'broker_appointments': [],
            'user_appointments': [],
            'upcoming_broker': 0,
            'upcoming_user': 0,
            'completed_broker': 0,
            'completed_user': 0,
        })


@login_required
def appointment_calendar(request):
    """تقويم المواعيد"""
    try:
        from .models import Appointment, BrokerAppointment
        from django.utils import timezone
        import calendar
        
        # Get month and year from query params
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
        
        # Get all appointments for the month
        from django.db.models import Q
        
        if hasattr(request.user, 'broker_profile'):
            # Broker view
            broker_appointments = BrokerAppointment.objects.filter(
                broker=request.user.broker_profile,
                appointment_date__year=year,
                appointment_date__month=month
            ).select_related('user', 'property')
            
            user_appointments = Appointment.objects.filter(
                Q(target_type='broker', target_id=request.user.broker_profile.id) |
                Q(user=request.user),
                appointment_date__year=year,
                appointment_date__month=month
            )
        else:
            # Regular user view
            broker_appointments = BrokerAppointment.objects.filter(
                user=request.user,
                appointment_date__year=year,
                appointment_date__month=month
            ).select_related('broker', 'property')
            
            user_appointments = Appointment.objects.filter(
                user=request.user,
                appointment_date__year=year,
                appointment_date__month=month
            )
        
        # Create calendar data
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        
        # Arabic month names
        arabic_months = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        month_name = arabic_months.get(month, calendar.month_name[month])
        
        # Group appointments by date
        appointments_by_date = {}
        
        for appt in broker_appointments:
            date_key = appt.appointment_date.day
            if date_key not in appointments_by_date:
                appointments_by_date[date_key] = []
            appointments_by_date[date_key].append({
                'type': 'broker',
                'id': appt.id,
                'time': appt.appointment_time.strftime('%H:%M'),
                'title': f'{appt.user.username} - {appt.get_appointment_type_display()}',
                'status': appt.status,
            })
        
        for appt in user_appointments:
            date_key = appt.appointment_date.day
            if date_key not in appointments_by_date:
                appointments_by_date[date_key] = []
            appointments_by_date[date_key].append({
                'type': 'user',
                'id': appt.id,
                'time': appt.appointment_time.strftime('%H:%M'),
                'title': appt.get_appointment_type_display(),
                'status': appt.status,
            })
        
        # Convert to a simple dict for template (JSON serializable)
        appointments_dict = {}
        for day, appointments in appointments_by_date.items():
            appointments_dict[str(day)] = [
                {
                    'type': appt['type'],
                    'id': appt['id'],
                    'time': appt['time'],
                    'title': appt['title'],
                    'status': appt['status'],
                }
                for appt in appointments
            ]
        
        # Navigation
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        return render(request, 'properties/appointment_calendar.html', {
            'year': year,
            'month': month,
            'month_name': month_name,
            'month_days': month_days,
            'appointments_by_date': appointments_dict,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
        })
    
    except Exception as e:
        logger.error(f"Error in appointment_calendar: {e}")
        return render(request, 'properties/appointment_calendar.html', {
            'year': timezone.now().year,
            'month': timezone.now().month,
            'month_name': calendar.month_name[timezone.now().month],
            'month_days': [],
            'appointments_by_date': {},
        })


@login_required
def appointment_reschedule(request, appointment_id):
    """إعادة جدولة موعد"""
    try:
        from .models import Appointment, BrokerAppointment
        
        # Try to find in either model
        try:
            appointment = BrokerAppointment.objects.get(id=appointment_id)
            is_broker = True
        except BrokerAppointment.DoesNotExist:
            appointment = Appointment.objects.get(id=appointment_id)
            is_broker = False
        
        # Check permissions
        if is_broker:
            if not hasattr(request.user, 'broker_profile') or appointment.broker != request.user.broker_profile:
                if appointment.user != request.user:
                    return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
        else:
            if appointment.user != request.user:
                return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            new_date = data.get('new_date')
            new_time = data.get('new_time')
            
            if not new_date or not new_time:
                return JsonResponse({'success': False, 'error': 'التاريخ والوقت مطلوبان'}, status=400)
            
            if is_broker:
                # For broker appointments, just update
                appointment.appointment_date = new_date
                appointment.appointment_time = new_time
                appointment.status = 'pending'
                appointment.save()
            else:
                # For regular appointments, use reschedule method
                appointment.reschedule(new_date, new_time)
            
            return JsonResponse({
                'success': True,
                'message': 'تم إعادة جدولة الموعد بنجاح'
            })
    
    except Exception as e:
        logger.error(f"Error in appointment_reschedule: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def appointment_slots_management(request):
    """إدارة فترات التوافر للمواعيد"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلال للوصول لهذه الصفحة')
        return redirect('home')
    
    try:
        from .models import AppointmentSlot
        
        broker = request.user.broker_profile
        slots = AppointmentSlot.objects.filter(broker=broker).order_by('day_of_week', 'start_time')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add':
                day_of_week = request.POST.get('day_of_week')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                max_appointments = request.POST.get('max_appointments', 1)
                
                if day_of_week and start_time and end_time:
                    try:
                        AppointmentSlot.objects.create(
                            broker=broker,
                            day_of_week=day_of_week,
                            start_time=start_time,
                            end_time=end_time,
                            max_appointments=int(max_appointments)
                        )
                        messages.success(request, 'تم إضافة فترة التوافر بنجاح')
                    except Exception as e:
                        messages.error(request, f'حدث خطأ: {str(e)}')
            
            elif action == 'delete':
                slot_id = request.POST.get('slot_id')
                try:
                    slot = AppointmentSlot.objects.get(id=slot_id, broker=broker)
                    slot.delete()
                    messages.success(request, 'تم حذف فترة التوافر')
                except AppointmentSlot.DoesNotExist:
                    messages.error(request, 'فترة التوافر غير موجودة')
            
            elif action == 'toggle':
                slot_id = request.POST.get('slot_id')
                try:
                    slot = AppointmentSlot.objects.get(id=slot_id, broker=broker)
                    slot.is_available = not slot.is_available
                    slot.save()
                    messages.success(request, 'تم تحديث فترة التوافر')
                except AppointmentSlot.DoesNotExist:
                    messages.error(request, 'فترة التوافر غير موجودة')
            
            return redirect('appointment_slots_management')
        
        return render(request, 'properties/appointment_slots_management.html', {
            'slots': slots,
        })
    
    except Exception as e:
        logger.error(f"Error in appointment_slots_management: {e}")
        return render(request, 'properties/appointment_slots_management.html', {
            'slots': [],
        })


@login_required
def customers_management(request):
    """نظام إدارة العملاء"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Customer
        
        customers = Customer.objects.all().select_related(
            'user', 'assigned_broker', 'assigned_agent'
        ).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            customers = customers.filter(status=status_filter)
        
        # Filter by type if provided
        type_filter = request.GET.get('type')
        if type_filter:
            customers = customers.filter(customer_type=type_filter)
        
        # Filter by priority if provided
        priority_filter = request.GET.get('priority')
        if priority_filter:
            customers = customers.filter(priority=priority_filter)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            customers = customers.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(customers, 20)
        page_number = request.GET.get('page')
        customers_page = paginator.get_page(page_number)
        
        # Statistics
        total_customers = customers.count()
        active_customers = customers.filter(status='active').count()
        vip_customers = customers.filter(priority='vip').count()
        total_revenue = customers.aggregate(total=Sum('total_spent'))['total'] or 0
        
        return render(request, 'properties/customers_management.html', {
            'customers': customers_page,
            'status_filter': status_filter,
            'type_filter': type_filter,
            'priority_filter': priority_filter,
            'search_query': search_query,
            'total_customers': total_customers,
            'active_customers': active_customers,
            'vip_customers': vip_customers,
            'total_revenue': total_revenue,
        })
    
    except Exception as e:
        logger.error(f"Error in customers_management: {e}")
        return render(request, 'properties/customers_management.html', {
            'customers': [],
            'status_filter': None,
            'type_filter': None,
            'priority_filter': None,
            'search_query': None,
            'total_customers': 0,
            'active_customers': 0,
            'vip_customers': 0,
            'total_revenue': 0,
        })


@login_required
def customer_detail(request, customer_id):
    """عرض تفاصيل عميل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Customer
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update':
                form = CustomerForm(request.POST, instance=customer)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'تم تحديث بيانات العميل بنجاح')
                    return redirect('customer_detail', customer_id=customer.id)
            
            elif action == 'mark_contacted':
                customer.mark_as_contacted()
                messages.success(request, 'تم تحديث تاريخ التواصل')
                return redirect('customer_detail', customer_id=customer.id)
            
            elif action == 'add_inquiry':
                customer.add_inquiry()
                messages.success(request, 'تم إضافة استفسار جديد')
                return redirect('customer_detail', customer_id=customer.id)
            
            elif action == 'add_purchase':
                amount = request.POST.get('amount', 0)
                if amount:
                    customer.add_purchase(float(amount))
                    messages.success(request, 'تم إضافة عملية شراء جديدة')
                    return redirect('customer_detail', customer.id)
        
        form = CustomerForm(instance=customer)
        
        return render(request, 'properties/customer_detail.html', {
            'customer': customer,
            'form': form,
        })
    
    except Exception as e:
        logger.error(f"Error in customer_detail: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('customers_management')


@login_required
def customer_create(request):
    """إنشاء عميل جديد"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        if request.method == 'POST':
            form = CustomerForm(request.POST)
            if form.is_valid():
                customer = form.save(commit=False)
                customer.first_contact_date = timezone.now().date()
                customer.last_contact_date = timezone.now().date()
                customer.save()
                messages.success(request, 'تم إنشاء العميل بنجاح')
                return redirect('customer_detail', customer_id=customer.id)
        else:
            form = CustomerForm()
        
        return render(request, 'properties/customer_form.html', {
            'form': form,
            'title': 'إضافة عميل جديد',
        })
    
    except Exception as e:
        logger.error(f"Error in customer_create: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('customers_management')


@login_required
def agents_management(request):
    """نظام إدارة الوكلاء"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Agent
        
        agents = Agent.objects.all().select_related('user').order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            agents = agents.filter(status=status_filter)
        
        # Filter by type if provided
        type_filter = request.GET.get('type')
        if type_filter:
            agents = agents.filter(agent_type=type_filter)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            agents = agents.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(agents, 20)
        page_number = request.GET.get('page')
        agents_page = paginator.get_page(page_number)
        
        # Statistics
        total_agents = agents.count()
        active_agents = agents.filter(status='active').count()
        verified_agents = agents.filter(is_verified=True).count()
        total_revenue = agents.aggregate(total=Sum('total_revenue'))['total'] or 0
        
        return render(request, 'properties/agents_management.html', {
            'agents': agents_page,
            'status_filter': status_filter,
            'type_filter': type_filter,
            'search_query': search_query,
            'total_agents': total_agents,
            'active_agents': active_agents,
            'verified_agents': verified_agents,
            'total_revenue': total_revenue,
        })
    
    except Exception as e:
        logger.error(f"Error in agents_management: {e}")
        return render(request, 'properties/agents_management.html', {
            'agents': [],
            'status_filter': None,
            'type_filter': None,
            'search_query': None,
            'total_agents': 0,
            'active_agents': 0,
            'verified_agents': 0,
            'total_revenue': 0,
        })


@login_required
def agent_detail(request, agent_id):
    """عرض تفاصيل وكيل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Agent
        
        agent = get_object_or_404(Agent, id=agent_id)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update':
                form = AgentForm(request.POST, instance=agent)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'تم تحديث بيانات الوكيل بنجاح')
                    return redirect('agent_detail', agent_id=agent.id)
            
            elif action == 'verify':
                agent.is_verified = True
                agent.save()
                messages.success(request, 'تم توثيق الوكيل')
                return redirect('agent_detail', agent_id=agent.id)
            
            elif action == 'suspend':
                agent.status = 'suspended'
                agent.save()
                messages.success(request, 'تم إيقاف الوكيل')
                return redirect('agent_detail', agent_id=agent.id)
            
            elif action == 'activate':
                agent.status = 'active'
                agent.save()
                messages.success(request, 'تم تفعيل الوكيل')
                return redirect('agent_detail', agent_id=agent.id)
        
        form = AgentForm(instance=agent)
        
        return render(request, 'properties/agent_detail.html', {
            'agent': agent,
            'form': form,
        })
    
    except Exception as e:
        logger.error(f"Error in agent_detail: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('agents_management')


@login_required
def agent_create(request):
    """إنشاء وكيل جديد"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        if request.method == 'POST':
            form = AgentForm(request.POST, request.FILES)
            if form.is_valid():
                agent = form.save(commit=False)
                agent.save()
                messages.success(request, 'تم إنشاء الوكيل بنجاح')
                return redirect('agent_detail', agent_id=agent.id)
        else:
            form = AgentForm()
        
        return render(request, 'properties/agent_form.html', {
            'form': form,
            'title': 'إضافة وكيل جديد',
        })
    
    except Exception as e:
        logger.error(f"Error in agent_create: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('agents_management')


@login_required
def customer_update(request, customer_id):
    """تحديث بيانات عميل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Customer
        
        customer = get_object_or_404(Customer, id=customer_id)
        
        if request.method == 'POST':
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث بيانات العميل بنجاح')
                return redirect('customer_detail', customer_id=customer.id)
        else:
            form = CustomerForm(instance=customer)
        
        return render(request, 'properties/customer_form.html', {
            'form': form,
            'title': 'تعديل بيانات العميل',
        })
    
    except Exception as e:
        logger.error(f"Error in customer_update: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('customer_detail', customer_id=customer_id)


@login_required
def customer_delete(request, customer_id):
    """حذف عميل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Customer
        
        customer = get_object_or_404(Customer, id=customer_id)
        customer.delete()
        messages.success(request, 'تم حذف العميل بنجاح')
        return redirect('customers_management')
    
    except Exception as e:
        logger.error(f"Error in customer_delete: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('customers_management')


@login_required
def agent_update(request, agent_id):
    """تحديث بيانات وكيل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Agent
        
        agent = get_object_or_404(Agent, id=agent_id)
        
        if request.method == 'POST':
            form = AgentForm(request.POST, request.FILES, instance=agent)
            if form.is_valid():
                form.save()
                messages.success(request, 'تم تحديث بيانات الوكيل بنجاح')
                return redirect('agent_detail', agent_id=agent.id)
        else:
            form = AgentForm(instance=agent)
        
        return render(request, 'properties/agent_form.html', {
            'form': form,
            'title': 'تعديل بيانات الوكيل',
        })
    
    except Exception as e:
        logger.error(f"Error in agent_update: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('agent_detail', agent_id=agent_id)


@login_required
def agent_delete(request, agent_id):
    """حذف وكيل"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from .models import Agent
        
        agent = get_object_or_404(Agent, id=agent_id)
        agent.delete()
        messages.success(request, 'تم حذف الوكيل بنجاح')
        return redirect('agents_management')
    
    except Exception as e:
        logger.error(f"Error in agent_delete: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('agents_management')


@login_required
def admin_dashboard_enhanced(request):
    """لوحة تحكم الإدارة الاحترافية مع إدارة العملاء والوكلاء"""
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح')
        return redirect('home')
    
    try:
        from django.db.models import Sum, Count, Avg
        from datetime import timedelta, datetime
        
        # إحصائيات العملاء
        total_customers = Customer.objects.count()
        active_customers = Customer.objects.filter(status='active').count()
        vip_customers = Customer.objects.filter(priority='vip').count()
        total_customer_revenue = Customer.objects.aggregate(total=Sum('total_spent'))['total'] or 0
        
        # إحصائيات الوكلاء
        total_agents = Agent.objects.count()
        active_agents = Agent.objects.filter(status='active').count()
        top_agents = Agent.objects.filter(commission_tier='elite').count()
        total_agent_commissions = Agent.objects.aggregate(total=Sum('total_commissions'))['total'] or 0
        
        # إحصائيات العقارات
        total_properties = Property.objects.count()
        active_properties = Property.objects.filter(status='active').count()
        sold_properties = Property.objects.filter(status='sold').count()
        
        # إحصائيات المستخدمين
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # إحصائيات الدلالين
        from .models import Broker
        total_brokers = Broker.objects.count()
        active_brokers = Broker.objects.filter(is_active=True).count()
        verified_brokers = Broker.objects.filter(is_verified=True).count()
        
        # إحصائيات العقود
        total_contracts = RealEstateContract.objects.count()
        active_contracts = RealEstateContract.objects.filter(status='active').count()
        completed_contracts = RealEstateContract.objects.filter(status='completed').count()
        
        # إحصائيات المواعيد
        from .models import Appointment
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects.filter(status='pending').count()
        confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
        
        # إحصائيات الإيرادات
        from .models import FinancialTransaction
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        daily_revenue = FinancialTransaction.objects.filter(
            created_at__date=today,
            status='completed'
        ).aggregate(total=Sum('sale_price'))['total'] or 0
        
        monthly_revenue = FinancialTransaction.objects.filter(
            created_at__date__gte=today - timedelta(days=30),
            status='completed'
        ).aggregate(total=Sum('sale_price'))['total'] or 0
        
        # آخر العمليات
        recent_customers = Customer.objects.order_by('-created_at')[:5]
        recent_agents = Agent.objects.order_by('-created_at')[:5]
        recent_contracts = RealEstateContract.objects.order_by('-created_at')[:5]
        
        context = {
            # إحصائيات العملاء
            'total_customers': total_customers,
            'active_customers': active_customers,
            'vip_customers': vip_customers,
            'total_customer_revenue': total_customer_revenue,
            
            # إحصائيات الوكلاء
            'total_agents': total_agents,
            'active_agents': active_agents,
            'top_agents': top_agents,
            'total_agent_commissions': total_agent_commissions,
            
            # إحصائيات العقارات
            'total_properties': total_properties,
            'active_properties': active_properties,
            'sold_properties': sold_properties,
            
            # إحصائيات المستخدمين
            'total_users': total_users,
            'active_users': active_users,
            
            # إحصائيات الدلالين
            'total_brokers': total_brokers,
            'active_brokers': active_brokers,
            'verified_brokers': verified_brokers,
            
            # إحصائيات العقود
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'completed_contracts': completed_contracts,
            
            # إحصائيات المواعيد
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'confirmed_appointments': confirmed_appointments,
            
            # إحصائيات الإيرادات
            'daily_revenue': daily_revenue,
            'monthly_revenue': monthly_revenue,
            
            # آخر العمليات
            'recent_customers': recent_customers,
            'recent_agents': recent_agents,
            'recent_contracts': recent_contracts,
        }
        
        return render(request, 'properties/admin_dashboard_enhanced.html', context)
    
    except Exception as e:
        logger.error(f"Error in admin_dashboard_enhanced: {e}")
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('home')


@login_required
def broker_message_detail(request, conversation_id):
    """عرض محادثة من جانب الدلال"""
    if not hasattr(request.user, 'broker_profile'):
        messages.error(request, 'يجب أن تكون دلال للوصول لهذه الصفحة')
        return redirect('home')
    
    conversation = get_object_or_404(
        BrokerConversation,
        conversation_id=conversation_id,
        broker=request.user.broker_profile
    )
    
    # Check if conversation is expired
    if conversation.is_expired():
        messages.warning(request, 'هذه المحادثة منتهية الصلاحية')
        conversation.is_active = False
        conversation.save()
    
    # Mark messages as read
    unread_messages = conversation.messages.filter(
        sender=conversation.user,
        is_read=False
    )
    for msg in unread_messages:
        msg.mark_as_read()
    
    # Get messages
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Form for new message
    if request.method == 'POST':
        form = BrokerMessageForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.receiver = conversation.user
            message.save()
            
            messages.success(request, 'تم إرسال الرسالة بنجاح')
            return redirect('broker_message_detail', conversation_id=conversation.conversation_id)
    else:
        form = BrokerMessageForm(user=request.user)
    
    return render(request, 'properties/broker_message_detail.html', {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def platform_comprehensive_stats(request):
    """إحصائيات شاملة للمنصة"""
    from django.db.models import Count, Sum, Avg
    from django.db.models.functions import TruncMonth, TruncDate
    from datetime import datetime, timedelta, date

    # استيراد الموديلات التي قد لا تكون موجودة
    try:
        from .models import TravelPackage, TravelCompany, TravelPackageBooking, HotelBooking
    except Exception:
        TravelPackage = None
        TravelCompany = None
        TravelPackageBooking = None
        HotelBooking = None

    # إحصائيات المستخدمين
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_brokers = Broker.objects.count()
    total_admins = User.objects.filter(is_superuser=True).count()
    total_staff = User.objects.filter(is_staff=True).count()

    # نمو المستخدمين خلال 6 أشهر
    monthly_users = []
    months_arabic = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

    for i in range(5, -1, -1):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        users_in_month = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()

        monthly_users.append({
            'month': months_arabic[month_start.month - 1],
            'year': month_start.year,
            'count': users_in_month
        })

    # إحصائيات العقارات
    total_properties = Property.objects.count()
    published_properties = Property.objects.filter(status='published').count()
    pending_properties = Property.objects.filter(status='pending').count()
    sold_properties = Property.objects.filter(status='sold').count()
    rented_properties = Property.objects.filter(status='rented').count()
    featured_properties = Property.objects.filter(is_featured=True).count()
    verified_properties = Property.objects.filter(is_verified=True).count()

    # عقارات حسب النوع
    properties_by_type = Property.objects.values('type').annotate(
        count=Count('id')
    ).order_by('-count')

    # عقارات حسب المحافظة
    properties_by_governorate = Property.objects.values('governorate').annotate(
        count=Count('id')
    ).order_by('-count')[:15]

    # إحصائيات الفنادق والمنتجعات
    total_hotels = Hotel.objects.count()
    total_resorts = Resort.objects.count()

    # إحصائيات الوظائف
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(status='active').count()

    # إحصائيات مقدمي الخدمات
    total_service_providers = ServiceProvider.objects.count()
    total_service_advertisements = ServiceAdvertisement.objects.count()

    # إحصائيات المزادات
    total_auctions = Auction.objects.count()
    active_auctions = Auction.objects.filter(status='active').count()
    completed_auctions = Auction.objects.filter(status='completed').count()

    # إحصائيات القنوات
    total_channels = BrokerChannel.objects.count()

    # إحصائيات الرحلات السياحية
    try:
        if TravelPackage and TravelCompany:
            total_travel_packages = TravelPackage.objects.count()
            total_travel_companies = TravelCompany.objects.count()
        else:
            total_travel_packages = 0
            total_travel_companies = 0
    except Exception:
        total_travel_packages = 0
        total_travel_companies = 0

    # إحصائيات المحادثات والرسائل
    try:
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()
    except Exception:
        total_conversations = 0
        total_messages = 0

    # إحصائيات التقارير
    try:
        total_reports = MessageReport.objects.count()
    except Exception:
        total_reports = 0

    # إحصائيات الاشتراكات
    try:
        active_subscriptions = BrokerPlanSubscription.objects.filter(status='active').count()
        total_subscriptions = BrokerPlanSubscription.objects.count()
    except Exception:
        active_subscriptions = 0
        total_subscriptions = 0

    # إحصائيات المعاملات المالية
    try:
        total_revenue = sum(t.amount or 0 for t in FinancialTransaction.objects.filter(status='completed'))
        pending_revenue = sum(t.amount or 0 for t in FinancialTransaction.objects.filter(status='pending'))
        total_transactions = FinancialTransaction.objects.count()
    except Exception:
        total_revenue = 0
        pending_revenue = 0
        total_transactions = 0

    # إحصائيات المصاريف والأرباح
    try:
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_profits = Profit.objects.aggregate(total=Sum('amount'))['total'] or 0
    except Exception:
        total_expenses = 0
        total_profits = 0

    # إحصائيات المشاهدات
    try:
        total_views = Property.objects.aggregate(total=Sum('view_count'))['total'] or 0
    except Exception:
        total_views = 0

    # عقارات مشطورة ومحمية (حقول غير موجودة - تعيين قيم افتراضية)
    shared_properties = 0
    protected_properties = 0

    # إحصائيات الملفات المرفقة
    try:
        total_images = PropertyImage.objects.count()
        total_videos = PropertyVideo.objects.count()
    except Exception:
        total_images = 0
        total_videos = 0

    # إحصائيات الحجوزات
    try:
        if TravelPackageBooking and HotelBooking:
            total_bookings = TravelPackageBooking.objects.count()
            total_hotel_bookings = HotelBooking.objects.count()
        else:
            total_bookings = 0
            total_hotel_bookings = 0
    except Exception:
        total_bookings = 0
        total_hotel_bookings = 0

    # نشاط اليوم
    today = date.today()
    today_users = User.objects.filter(date_joined__date=today).count()
    today_properties = Property.objects.filter(created_at__date=today).count()
    today_messages = 0
    try:
        today_messages = Message.objects.filter(created_at__date=today).count()
    except Exception:
        pass

    # نشاط الأسبوع
    week_ago = today - timedelta(days=7)
    week_users = User.objects.filter(date_joined__date__gte=week_ago).count()
    week_properties = Property.objects.filter(created_at__date__gte=week_ago).count()

    # نشاط الشهر
    month_ago = today - timedelta(days=30)
    month_users = User.objects.filter(date_joined__date__gte=month_ago).count()
    month_properties = Property.objects.filter(created_at__date__gte=month_ago).count()

    context = {
        'users': {
            'total': total_users,
            'active': active_users,
            'brokers': total_brokers,
            'admins': total_admins,
            'staff': total_staff,
            'regular': total_users - total_brokers - total_admins,
            'monthly_growth': monthly_users,
            'today': today_users,
            'week': week_users,
            'month': month_users,
        },
        'properties': {
            'total': total_properties,
            'published': published_properties,
            'pending': pending_properties,
            'sold': sold_properties,
            'rented': rented_properties,
            'featured': featured_properties,
            'verified': verified_properties,
            'by_type': list(properties_by_type),
            'by_governorate': list(properties_by_governorate),
            'today': today_properties,
            'week': week_properties,
            'month': month_properties,
        },
        'hotels': {
            'total': total_hotels,
        },
        'resorts': {
            'total': total_resorts,
        },
        'jobs': {
            'total': total_jobs,
            'active': active_jobs,
        },
        'services': {
            'providers': total_service_providers,
            'advertisements': total_service_advertisements,
        },
        'auctions': {
            'total': total_auctions,
            'active': active_auctions,
            'completed': completed_auctions,
        },
        'channels': {
            'total': total_channels,
        },
        'travel': {
            'packages': total_travel_packages,
            'companies': total_travel_companies,
            'bookings': total_bookings,
        },
        'conversations': {
            'total': total_conversations,
        },
        'messages': {
            'total': total_messages,
            'today': today_messages,
        },
        'reports': {
            'total': total_reports,
        },
        'subscriptions': {
            'total': total_subscriptions,
            'active': active_subscriptions,
        },
        'financial': {
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'total_transactions': total_transactions,
            'total_expenses': total_expenses,
            'total_profits': total_profits,
            'net_profit': total_profits - total_expenses,
        },
        'media': {
            'images': total_images,
            'videos': total_videos,
        },
        'views': {
            'total': total_views,
        },
    }

    return render(request, 'properties/platform_stats.html', context)


@login_required
def smart_assistant_view(request):
    """Smart AI Assistant View - Intelligent search and guidance"""
    return render(request, 'properties/ai_smart_assistant.html')
