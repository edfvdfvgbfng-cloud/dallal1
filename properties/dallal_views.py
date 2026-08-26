"""views لإدارة نظام الدلال"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .decorators import broker_required, manage_brokers_required
from .models import (
    DallalGlobalSettings, BasicDallalSettings, PremiumDallalSettings,
    DallalSubscription, PropertyDallalAssignment, TravelCompany,
    TravelCompanyRatingBreakdown, TravelCompanyReview
)
from .permissions import is_platform_admin, get_broker


@login_required
@manage_brokers_required
def dallal_settings(request):
    """صفحة إعدادات نظام الدلال"""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    global_settings = DallalGlobalSettings.get_settings()
    basic_settings = BasicDallalSettings.get_settings()
    premium_settings = PremiumDallalSettings.get_settings()
    
    if request.method == 'POST':
        # تحديث الإعدادات العامة
        if 'update_global' in request.POST:
            global_settings.is_dallal_system_enabled = request.POST.get('is_dallal_system_enabled') == 'on'
            global_settings.max_brokers_per_user = int(request.POST.get('max_brokers_per_user', 1))
            global_settings.max_properties_per_dallal = int(request.POST.get('max_properties_per_dallal', 100))
            global_settings.show_dallal_on_homepage = request.POST.get('show_dallal_on_homepage') == 'on'
            global_settings.dallal_display_order = request.POST.get('dallal_display_order', 'premium_first')
            global_settings.show_expired_dallal = request.POST.get('show_expired_dallal') == 'on'
            global_settings.save()
            messages.success(request, 'تم تحديث الإعدادات العامة')
        
        # تحديث إعدادات الدلال العادي
        elif 'update_basic' in request.POST:
            basic_settings.max_properties = int(request.POST.get('max_properties', 20))
            basic_settings.duration_days = int(request.POST.get('duration_days', 30))
            basic_settings.auto_renewal = request.POST.get('auto_renewal') == 'on'
            basic_settings.impressions_limit = int(request.POST.get('impressions_limit', 1000))
            basic_settings.cost = float(request.POST.get('cost', 0))
            basic_settings.is_enabled = request.POST.get('is_enabled') == 'on'
            basic_settings.save()
            messages.success(request, 'تم تحديث إعدادات الدلال العادي')
        
        # تحديث إعدادات الدلال المميز
        elif 'update_premium' in request.POST:
            premium_settings.max_properties = int(request.POST.get('max_properties', 100))
            premium_settings.duration_days = int(request.POST.get('duration_days', 90))
            premium_settings.priority_display = request.POST.get('priority_display') == 'on'
            premium_settings.impressions_limit = int(request.POST.get('impressions_limit', 5000))
            premium_settings.cost = float(request.POST.get('cost', 0))
            premium_settings.is_enabled = request.POST.get('is_enabled') == 'on'
            premium_settings.visual_badge = request.POST.get('visual_badge') == 'on'
            premium_settings.highlight_effect = request.POST.get('highlight_effect') == 'on'
            premium_settings.save()
            messages.success(request, 'تم تحديث إعدادات الدلال المميز')
        
        return redirect('dallal_settings')
    
    # الحصول على إحصائيات الاشتراكات
    basic_subscriptions = DallalSubscription.objects.filter(subscription_type='basic')
    premium_subscriptions = DallalSubscription.objects.filter(subscription_type='premium')
    
    stats = {
        'basic_active': basic_subscriptions.filter(is_active=True).count(),
        'basic_expired': basic_subscriptions.filter(is_active=False).count(),
        'premium_active': premium_subscriptions.filter(is_active=True).count(),
        'premium_expired': premium_subscriptions.filter(is_active=False).count(),
    }
    
    return render(request, 'properties/dallal_settings.html', {
        'global_settings': global_settings,
        'basic_settings': basic_settings,
        'premium_settings': premium_settings,
        'stats': stats,
    })


@login_required
@manage_brokers_required
def dallal_subscriptions_list(request):
    """قائمة اشتراكات الدلال"""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    subscriptions = DallalSubscription.objects.select_related('broker').all()
    
    return render(request, 'properties/dallal_subscriptions_list.html', {
        'subscriptions': subscriptions,
    })


@login_required
@manage_brokers_required
@require_http_methods(['GET', 'POST'])
def dallal_subscription_create(request):
    """إنشاء اشتراك دلال جديد"""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    from .dallal_forms import DallalSubscriptionForm
    
    if request.method == 'POST':
        form = DallalSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, f'تم إنشاء اشتراك {subscription.get_subscription_type_display()}')
            return redirect('dallal_subscriptions_list')
    else:
        form = DallalSubscriptionForm()
    
    return render(request, 'properties/dallal_subscription_form.html', {
        'form': form,
        'title': 'إنشاء اشتراك دلال',
    })


@login_required
@manage_brokers_required
@require_http_methods(['GET', 'POST'])
def dallal_subscription_edit(request, subscription_id):
    """تعديل اشتراك دلال"""
    if not is_platform_admin(request.user):
        messages.error(request, 'ليس لديك صلاحية')
        return redirect('dashboard')
    
    subscription = DallalSubscription.objects.get(pk=subscription_id)
    
    from .dallal_forms import DallalSubscriptionForm
    
    if request.method == 'POST':
        form = DallalSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الاشتراك')
            return redirect('dallal_subscriptions_list')
    else:
        form = DallalSubscriptionForm(instance=subscription)
    
    return render(request, 'properties/dallal_subscription_form.html', {
        'form': form,
        'title': 'تعديل اشتراك دلال',
        'subscription': subscription,
    })


@login_required
@broker_required
@require_http_methods(['GET', 'POST'])
def dallal_travel_company_create(request):
    """إنشاء شركة سفر جديدة للدلال"""
    from .dallal_forms import TravelCompanyForm
    
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
        form = TravelCompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            
            # Create rating breakdown for the new company
            TravelCompanyRatingBreakdown.objects.create(company=company)
            
            messages.success(request, f'تم إنشاء شركة {company.name} بنجاح')
            return redirect('travel_companies')
    else:
        form = TravelCompanyForm()
    
    return render(request, 'properties/dallal_travel_company_form.html', {
        'form': form,
        'title': 'إضافة شركة سفر جديدة',
    })


@login_required
@broker_required
@require_http_methods(['GET', 'POST'])
def dallal_travel_company_edit(request, company_id):
    """تعديل شركة سفر"""
    company = TravelCompany.objects.get(pk=company_id, user=request.user)
    
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
    
    from .dallal_forms import TravelCompanyForm
    
    if request.method == 'POST':
        form = TravelCompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث شركة السفر بنجاح')
            return redirect('travel_companies')
    else:
        form = TravelCompanyForm(instance=company)
    
    return render(request, 'properties/dallal_travel_company_form.html', {
        'form': form,
        'title': 'تعديل شركة السفر',
        'company': company,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def travel_company_review_create(request, company_id):
    """إضافة تقييم لشركة سفر"""
    company = TravelCompany.objects.get(pk=company_id)
    
    if request.method == 'POST':
        try:
            # Create review with detailed ratings
            review = TravelCompanyReview.objects.create(
                company=company,
                user=request.user,
                overall_rating=int(request.POST.get('overall_rating', 3)),
                service_quality=int(request.POST.get('service_quality', 3)),
                price_value=int(request.POST.get('price_value', 3)),
                reliability=int(request.POST.get('reliability', 3)),
                customer_service=int(request.POST.get('customer_service', 3)),
                comfort=int(request.POST.get('comfort', 3)),
                title=request.POST.get('title', ''),
                comment=request.POST.get('comment', ''),
                comment_en=request.POST.get('comment_en', ''),
                trip_date=request.POST.get('trip_date') if request.POST.get('trip_date') else None,
                destination=request.POST.get('destination', ''),
                travel_type=request.POST.get('travel_type', ''),
            )
            
            # Update rating breakdown
            try:
                breakdown = company.rating_breakdown
                breakdown.update_from_reviews()
            except TravelCompanyRatingBreakdown.DoesNotExist:
                # Create breakdown if it doesn't exist
                breakdown = TravelCompanyRatingBreakdown.objects.create(company=company)
                breakdown.update_from_reviews()
            
            messages.success(request, 'تم إضافة تقييمك بنجاح')
            return redirect('travel_company_detail', pk=company_id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
    
    return render(request, 'properties/travel_company_review_form.html', {
        'company': company,
        'title': 'إضافة تقييم لشركة السفر',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def travel_company_review_edit(request, review_id):
    """تعديل تقييم شركة سفر"""
    review = TravelCompanyReview.objects.get(pk=review_id, user=request.user)
    
    if request.method == 'POST':
        try:
            review.overall_rating = int(request.POST.get('overall_rating', 3))
            review.service_quality = int(request.POST.get('service_quality', 3))
            review.price_value = int(request.POST.get('price_value', 3))
            review.reliability = int(request.POST.get('reliability', 3))
            review.customer_service = int(request.POST.get('customer_service', 3))
            review.comfort = int(request.POST.get('comfort', 3))
            review.title = request.POST.get('title', '')
            review.comment = request.POST.get('comment', '')
            review.comment_en = request.POST.get('comment_en', '')
            review.trip_date = request.POST.get('trip_date') if request.POST.get('trip_date') else None
            review.destination = request.POST.get('destination', '')
            review.travel_type = request.POST.get('travel_type', '')
            review.save()
            
            # Update rating breakdown
            if hasattr(review.company, 'rating_breakdown'):
                review.company.rating_breakdown.update_from_reviews()
            
            messages.success(request, 'تم تحديث تقييمك بنجاح')
            return redirect('travel_company_detail', pk=review.company.id)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
    
    return render(request, 'properties/travel_company_review_form.html', {
        'review': review,
        'company': review.company,
        'title': 'تعديل التقييم',
    })
