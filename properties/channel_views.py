"""
واجهات القنوات المتقدمة
Advanced Channel Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View

from .models import BrokerChannel, ChannelFollow, ChannelSubscription, ChannelContent, ChannelBroadcast, ChannelCollaboration, ChannelAdvertisement, ChannelAnalyticsAdvanced
from .channel_forms import ChannelSubscriptionForm, ChannelContentForm, ChannelBroadcastForm, ChannelCollaborationForm, ChannelAdvertisementForm, ChannelSearchForm


class ChannelListView(View):
    """قائمة القنوات المتقدمة"""
    
    def get(self, request):
        search_form = ChannelSearchForm(request.GET)
        # Annotate channels with real followers count
        channels = BrokerChannel.objects.filter(status='active').annotate(
            real_followers_count=Count('followers')
        )
        
        # Apply filters
        if search_form.is_valid():
            q = search_form.cleaned_data.get('q')
            governorate = search_form.cleaned_data.get('governorate')
            channel_type = search_form.cleaned_data.get('channel_type')
            category = search_form.cleaned_data.get('category')
            is_verified = search_form.cleaned_data.get('is_verified')
            sort = search_form.cleaned_data.get('sort', 'followers')
            
            if q:
                channels = channels.filter(
                    Q(name__icontains=q) | 
                    Q(description__icontains=q) |
                    Q(broker__full_name__icontains=q)
                )
            
            if governorate:
                channels = channels.filter(governorate=governorate)
            
            if channel_type:
                type_mapping = {
                    'basic': BrokerChannel.CHANNEL_TYPE_BASIC,
                    'premium': BrokerChannel.CHANNEL_TYPE_PREMIUM,
                    'elite': BrokerChannel.CHANNEL_TYPE_ELITE,
                }
                channels = channels.filter(channel_type=type_mapping.get(channel_type))
            
            if category:
                channels = channels.filter(category=category)
            
            if is_verified:
                channels = channels.filter(is_verified=True)
            
            # Apply sorting
            if sort == 'followers':
                channels = channels.order_by('-real_followers_count')
            elif sort == 'rating':
                channels = channels.order_by('-rating')
            elif sort == 'properties':
                channels = channels.order_by('-properties_count')
            elif sort == 'newest':
                channels = channels.order_by('-created_at')
        
        # Only show featured channels first
        channels = channels.order_by('-is_featured', '-real_followers_count')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(channels, 12)
        page_obj = paginator.get_page(page)
        
        context = {
            'channels': page_obj,
            'search_form': search_form,
            'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        }
        
        if context['is_ajax']:
            return JsonResponse({
                'channels': [
                    {
                        'id': channel.id,
                        'name': channel.name,
                        'logo': channel.logo.url if channel.logo else None,
                        'cover_image': channel.cover_image.url if channel.cover_image else None,
                        'description': channel.description[:200],
                        'followers_count': getattr(channel, 'real_followers_count', channel.followers_count),
                        'views_count': channel.views_count,
                        'rating': float(channel.rating),
                        'is_verified': channel.is_verified,
                        'is_featured': channel.is_featured,
                        'broker_name': channel.broker.display_name,
                        'url': channel.get_absolute_url()
                    }
                    for channel in page_obj
                ],
                'pagination': {
                    'page': page,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            })
        
        return render(request, 'properties/channel_list.html', context)


class ChannelDetailView(View):
    """تفاصيل القناة المتقدمة"""
    
    def get(self, request, channel_id):
        channel = get_object_or_404(BrokerChannel, id=channel_id)
        
        # Increment view counter
        channel.increment_views()
        
        # Get channel content
        content = channel.contents.filter(status='published')[:10]
        
        # Get analytics if available
        analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
        
        # Check if user is following
        is_following = False
        if request.user.is_authenticated:
            is_following = channel.followers.filter(user=request.user).exists()
        
        context = {
            'channel': channel,
            'content': content,
            'analytics': analytics,
            'is_following': is_following,
            'is_owner': request.user.is_authenticated and request.user == channel.broker.user,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'id': channel.id,
                'name': channel.name,
                'description': channel.description,
                'followers_count': channel.followers_count,
                'views_count': channel.views_count,
                'rating': float(channel.rating),
                'is_verified': channel.is_verified,
                'is_featured': channel.is_featured,
                'is_following': is_following,
                'analytics': {
                    'total_visitors': analytics.total_visitors,
                    'unique_visitors': analytics.unique_visitors,
                    'average_session_duration': analytics.average_session_duration,
                    'engagement_rate': analytics.calculate_engagement_rate(),
                }
            })
        
        return render(request, 'properties/channel_detail.html', context)


@login_required
def channel_dashboard(request, channel_id):
    """لوحة تحكم القناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, broker__user=request.user)
    
    # Get subscription
    subscription, created = ChannelSubscription.objects.get_or_create(channel=channel)
    
    # Get analytics
    analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
    
    # Get recent content
    recent_content = channel.contents.all()[:5]
    
    # Get live streams
    live_streams = channel.broadcasts.all()[:5]
    
    # Get collaborations
    collaborations = channel.sent_collaborations.all()[:5]
    
    context = {
        'channel': channel,
        'subscription': subscription,
        'analytics': analytics,
        'recent_content': recent_content,
        'live_streams': live_streams,
        'collaborations': collaborations,
    }
    
    return render(request, 'properties/channel_dashboard.html', context)


@login_required
def create_channel_content(request, channel_id):
    """إنشاء محتوى للقناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, broker__user=request.user)
    
    if request.method == 'POST':
        form = ChannelContentForm(request.POST, request.FILES, initial={'channel': channel})
        if form.is_valid():
            content = form.save(commit=False)
            content.channel = channel
            content.save()
            
            messages.success(request, 'تم إنشاء المحتوى بنجاح!')
            return redirect('channel_content_detail', content_id=content.id)
    else:
        form = ChannelContentForm(initial={'channel': channel})
    
    return render(request, 'properties/channel_content_create.html', {
        'form': form,
        'channel': channel
    })


@login_required
def create_channel_broadcast(request, channel_id):
    """إنشاء بث مباشر للقناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, broker__user=request.user)
    
    if request.method == 'POST':
        form = ChannelBroadcastForm(request.POST, request.FILES, initial={'channel': channel})
        if form.is_valid():
            broadcast = form.save(commit=False)
            broadcast.channel = channel
            broadcast.save()
            
            messages.success(request, 'تم إنشاء البث المباشر بنجاح!')
            return redirect('channel_broadcast_detail', broadcast_id=broadcast.id)
    else:
        form = ChannelBroadcastForm(initial={'channel': channel})
    
    return render(request, 'properties/channel_broadcast_create.html', {
        'form': form,
        'channel': channel
    })


@login_required
def manage_channel_subscription(request, channel_id):
    """إدارة اشتراك القناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id, broker__user=request.user)
    subscription, created = ChannelSubscription.objects.get_or_create(channel=channel)
    
    if request.method == 'POST':
        form = ChannelSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الاشتراك بنجاح!')
            return redirect('channel_dashboard', channel_id=channel.id)
    else:
        form = ChannelSubscriptionForm(instance=subscription)
    
    return render(request, 'properties/channel_subscription.html', {
        'form': form,
        'channel': channel,
        'subscription': subscription
    })


@login_required
def create_channel_collaboration(request):
    """إنشاء تعاون قناة"""
    if request.method == 'POST':
        form = ChannelCollaborationForm(request.POST)
        if form.is_valid():
            collaboration = form.save(commit=False)
            collaboration.requesting_channel = request.user.broker.channel
            collaboration.save()
            
            messages.success(request, 'تم إرسال طلب التعاون بنجاح!')
            return redirect('channel_collaborations')
    else:
        form = ChannelCollaborationForm()
    
    return render(request, 'properties/channel_collaboration_create.html', {'form': form})


@login_required
def create_channel_advertisement(request, channel_id):
    """إنشاء إعلان للقناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    
    if request.method == 'POST':
        form = ChannelAdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.channel = channel
            advertisement.advertiser = request.user
            advertisement.save()
            
            messages.success(request, 'تم إنشاء الإعلان بنجاح!')
            return redirect('channel_advertisements')
    else:
        form = ChannelAdvertisementForm()
    
    return render(request, 'properties/channel_advertisement_create.html', {
        'form': form,
        'channel': channel
    })


@require_POST
def follow_channel(request, channel_id):
    """متابعة قناة"""
    channel = get_object_or_404(BrokerChannel, id=channel_id)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Check if already following
    if channel.followers.filter(user=request.user).exists():
        channel.decrement_followers()
        channel.followers.remove(request.user)
        return JsonResponse({'success': True, 'following': False})
    else:
        channel.increment_followers()
        channel.followers.add(request.user)
        return JsonResponse({'success': True, 'following': True})


@require_POST
def like_channel_content(request, content_id):
    """إعجاب محتوى القناة"""
    content = get_object_or_404(ChannelContent, id=content_id)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Check if already liked
    if content.likes.filter(user=request.user).exists():
        content.likes.remove(request.user)
        content.likes_count -= 1
        content.save(update_fields=['likes_count'])
        return JsonResponse({'success': True, 'liked': False})
    else:
        content.likes.add(request.user)
        content.likes_count += 1
        content.save(update_fields=['likes_count'])
        return JsonResponse({'success': True, 'liked': True})