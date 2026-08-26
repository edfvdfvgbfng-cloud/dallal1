"""
أدوات القنوات المتقدمة
Advanced Channel Utilities
"""

from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.models import User

from .models import BrokerChannel, ChannelSubscription, ChannelContent, ChannelAnalyticsAdvanced, ChannelCollaboration, ChannelAdvertisement


def update_channel_analytics(channel):
    """تحديث إحصائيات القناة المتقدمة"""
    analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
    
    # Update basic channel stats
    channel.views_count = channel.views_count + 1
    channel.save(update_fields=['views_count'])
    
    # Calculate engagement rate
    total_interactions = (
        channel.contents.aggregate(
            total_likes=Sum('likes_count'),
            total_comments=Sum('comments_count'),
            total_shares=Sum('shares_count')
        )
    )
    
    total_engagement = (
        (total_interactions['total_likes'] or 0) +
        (total_interactions['total_comments'] or 0) +
        (total_interactions['total_shares'] or 0)
    )
    
    if channel.views_count > 0:
        analytics.engagement_rate = round((total_engagement / channel.views_count) * 100, 2)
    
    # Update followers tracking
    analytics.daily_followers[str(timezone.now().date())] = channel.followers_count
    analytics.weekly_followers[str(timezone.now().date())] = channel.followers_count
    analytics.monthly_followers[str(timezone.now().date())] = channel.followers_count
    
    # Update views tracking
    analytics.daily_views[str(timezone.now().date())] = channel.views_count
    analytics.weekly_views[str(timezone.now().date())] = channel.views_count
    analytics.monthly_views[str(timezone.now().date())] = channel.views_count
    
    # Calculate conversion rate
    if channel.properties_count > 0:
        analytics.conversion_rate = round(
            (analytics.properties_contacted / channel.properties_count) * 100, 2
        )
    
    analytics.last_updated = timezone.now()
    analytics.save()
    
    return analytics


def recommend_channels(user, limit=10):
    """توصية القنوات للمستخدم"""
    if not user.is_authenticated:
        return []
    
    # Get user's preferences based on activity
    user_properties = user.properties.all() if hasattr(user, 'properties') else []
    user_governorates = [prop.governorate for prop in user_properties if prop.governorate]
    
    # Get channels matching user preferences
    recommended = BrokerChannel.objects.filter(
        status='active',
        is_verified=True
    ).exclude(followers=user)
    
    if user_governorates:
        recommended = recommended.filter(governorate__in=user_governorates)
    
    # Sort by rating and followers
    recommended = recommended.order_by('-rating', '-followers_count')
    
    return recommended[:limit]


def find_channel_collaborations(channel):
    """البحث عن فرص تعاون للقناة"""
    # Find channels in same governorate
    similar_channels = BrokerChannel.objects.filter(
        status='active',
        governorate=channel.governorate,
        channel_type=channel.channel_type
    ).exclude(id=channel.id)
    
    # Find channels with complementary specializations
    if channel.specialization:
        complementary_channels = BrokerChannel.objects.filter(
            status='active',
            specialization__icontains=channel.specialization.split()[0] if channel.specialization else ''
        ).exclude(id=channel.id)
    
    return {
        'similar_channels': similar_channels[:5],
        'complementary_channels': complementary_channels[:5] if 'complementary_channels' in locals() else []
    }


def calculate_channel_revenue(channel, start_date=None, end_date=None):
    """حساب إيرادات القناة"""
    if not start_date:
        start_date = timezone.now().replace(day=1)
    if not end_date:
        end_date = timezone.now()
    
    # Revenue from advertisements
    ad_revenue = ChannelAdvertisement.objects.filter(
        channel=channel,
        status='active',
        start_date__gte=start_date,
        end_date__lte=end_date
    ).aggregate(total=Sum('budget'))['total'] or 0
    
    # Revenue from collaborations
    collab_revenue = ChannelCollaboration.objects.filter(
        Q(requesting_channel=channel) | Q(target_channel=channel),
        status='active',
        started_at__gte=start_date,
        ended_at__lte=end_date
    ).aggregate(total=Sum('total_revenue'))['total'] or 0
    
    return {
        'advertisement_revenue': ad_revenue,
        'collaboration_revenue': collab_revenue,
        'total_revenue': ad_revenue + collab_revenue
    }


def track_channel_performance(channel):
    """تتبع أداء القناة"""
    analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
    
    # Get recent content performance
    recent_content = channel.contents.filter(
        status='published',
        published_at__gte=timezone.now() - timezone.timedelta(days=30)
    )
    
    performance_data = {
        'total_content': recent_content.count(),
        'total_views': recent_content.aggregate(Sum('views_count'))['views_count__sum'] or 0,
        'total_likes': recent_content.aggregate(Sum('likes_count'))['likes_count__sum'] or 0,
        'total_comments': recent_content.aggregate(Sum('comments_count'))['comments_count__sum'] or 0,
        'average_engagement': 0
    }
    
    if performance_data['total_content'] > 0:
        performance_data['average_engagement'] = round(
            (performance_data['total_likes'] + performance_data['total_comments']) / 
            performance_data['total_content'], 2
        )
    
    return performance_data


def get_channel_insights(channel):
    """الحصول على رؤى شاملة للقناة"""
    analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
    
    insights = {
        'channel': channel,
        'analytics': analytics,
        'performance': track_channel_performance(channel),
        'revenue': calculate_channel_revenue(channel),
        'collaborations': find_channel_collaborations(channel),
        'growth_rate': calculate_growth_rate(channel),
    }
    
    return insights


def calculate_growth_rate(channel):
    """حساب معدل نمو القناة"""
    analytics, created = ChannelAnalyticsAdvanced.objects.get_or_create(channel=channel)
    
    # Calculate monthly growth rate
    monthly_followers = analytics.monthly_followers
    if len(monthly_followers) >= 2:
        months = sorted(monthly_followers.keys())
        current_month = monthly_followers[months[-1]]
        previous_month = monthly_followers[months[-2]]
        
        if previous_month > 0:
            growth_rate = round(((current_month - previous_month) / previous_month) * 100, 2)
        else:
            growth_rate = 0
    else:
        growth_rate = 0
    
    return {
        'monthly_growth_rate': growth_rate,
        'current_followers': channel.followers_count,
        'trend': 'increasing' if growth_rate > 0 else 'decreasing' if growth_rate < 0 else 'stable'
    }


def validate_channel_content(channel, content_type, title, content):
    """التحقق من صحة محتوى القناة"""
    errors = []
    
    # Check subscription limits
    subscription, created = ChannelSubscription.objects.get_or_create(channel=channel)
    
    if not subscription.is_active():
        errors.append('الاشتراك غير نشط. يرجى تجديد الاشتراك.')
    elif not subscription.can_post():
        errors.append('وصلت إلى الحد الأقصى للمنشورات الشهرية.')
    
    # Check content requirements
    if not title or len(title) < 5:
        errors.append('العنوان يجب أن يكون 5 أحرف على الأقل.')
    
    if not content or len(content) < 20:
        errors.append('المحتوى يجب أن يكون 20 حرف على الأقل.')
    
    # Check content type requirements
    if content_type == 'video' and not content:
        errors.append('محتوى الفيديو مطلوب.')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def optimize_channel_for_seo(channel):
    """تحسين القناة لمحركات البحث"""
    recommendations = []
    
    # Check if channel has proper SEO fields
    if not channel.meta_title or len(channel.meta_title) < 10:
        recommendations.append('إضافة عنوان SEO جذاب')
    
    if not channel.meta_description or len(channel.meta_description) < 20:
        recommendations.append('إضافة وصف SEO شامل')
    
    if not channel.keywords:
        recommendations.append('إضافة كلمات مفتاحية')
    
    # Check if channel has proper content
    if channel.contents.filter(status='published').count() < 5:
        recommendations.append('نشر المزيد من المحتوى لتحسين الترتيب')
    
    # Check if channel has verified status
    if not channel.is_verified:
        recommendations.append('طلب التحقق من القناة لزيادة الثقة')
    
    return {
        'seo_score': 100 - (len(recommendations) * 15),
        'recommendations': recommendations
    }


def get_channel_statistics_summary(channel):
    """الحصول على ملخص إحصائيات القناة"""
    return {
        'basic_stats': {
            'followers': channel.followers_count,
            'views': channel.views_count,
            'properties': channel.properties_count,
            'rating': float(channel.rating),
        },
        'engagement_stats': {
            'likes': channel.contents.aggregate(Sum('likes_count'))['likes_count__sum'] or 0,
            'comments': channel.contents.aggregate(Sum('comments_count'))['comments_count__sum'] or 0,
            'shares': channel.contents.aggregate(Sum('shares_count'))['shares_count__sum'] or 0,
        },
        'content_stats': {
            'total_posts': channel.contents.count(),
            'published_posts': channel.contents.filter(status='published').count(),
            'scheduled_posts': channel.contents.filter(status='scheduled').count(),
        },
        'growth': calculate_growth_rate(channel),
    }