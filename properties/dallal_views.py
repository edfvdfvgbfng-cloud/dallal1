"""views لإدارة نظام الدلال"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
import re
import random
import string

def generate_slug(name):
    """Generate URL-friendly slug from name"""
    if not name:
        # Generate random slug if name is empty
        return 'hotel-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    slug = name.lower()
    # Remove special characters
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Remove Arabic characters
    slug = re.sub(r'[\u0600-\u06FF]', '', slug)
    slug = slug.strip()
    # Convert spaces to hyphens
    slug = re.sub(r'[-\s]+', '-', slug)

    # If slug is empty after cleaning, use random
    if not slug:
        slug = 'hotel-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    return slug
from django.views.decorators.http import require_http_methods

from .decorators import broker_required, manage_brokers_required
from .models import (
    DallalGlobalSettings, BasicDallalSettings, PremiumDallalSettings,
    DallalSubscription, PropertyDallalAssignment, TravelCompany,
    TravelCompanyRatingBreakdown, TravelCompanyReview, HotelPage, HotelPost
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

    # Get broker (no subscription check for company creation)
    broker = get_broker(request.user)

    if request.method == 'POST':
        form = TravelCompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.broker = broker
            company.is_active = True  # Ensure company is active by default
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
    broker = get_broker(request.user)
    company = TravelCompany.objects.filter(pk=company_id, broker=broker).first()
    if not company:
        messages.error(request, 'شركة السفر غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_travel_companies')

    # No subscription check for editing companies
    from .dallal_forms import TravelCompanyForm

    if request.method == 'POST':
        form = TravelCompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث شركة السفر بنجاح')
            return redirect('travel_company_detail', company.id)
    else:
        form = TravelCompanyForm(instance=company)

    return render(request, 'properties/dallal_travel_company_form.html', {
        'form': form,
        'title': 'تعديل شركة السفر',
        'company': company,
    })


@login_required
@broker_required
def dallal_travel_company_delete(request, company_id):
    """حذف شركة سفر"""
    broker = get_broker(request.user)
    company = TravelCompany.objects.filter(pk=company_id, broker=broker).first()
    
    if not company:
        messages.error(request, 'شركة السفر غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_travel_companies')
    
    if request.method == 'POST':
        company_name = company.name
        company.delete()
        messages.success(request, f'تم حذف شركة {company_name} بنجاح')
        return redirect('broker_travel_companies')
    
    return render(request, 'properties/travel_company_delete_confirm.html', {
        'company': company,
    })


@login_required
@broker_required
def broker_travel_companies(request):
    """صفحة اختيار شركة السفر لإنشاء منشور"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على شركات السفر الخاصة بالدلال
    companies = TravelCompany.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'properties/broker_travel_companies.html', {
        'broker': broker,
        'companies': companies,
    })


@login_required
@broker_required
def travel_company_post_create(request, company_id):
    """إنشاء منشور جديد داخل صفحة شركة السفر"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    company = TravelCompany.objects.filter(id=company_id, broker=broker).first()
    if not company:
        messages.error(request, 'شركة السفر غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_travel_companies')

    # Check subscription status for creating posts
    broker.check_subscription_status()
    from .models import BrokerPlanSubscription
    active_subscriptions = BrokerPlanSubscription.objects.filter(
        broker=broker,
        status='active'
    )
    has_active_subscription = active_subscriptions.exists()

    if not has_active_subscription:
        messages.error(request, 'ليس لديك اشتراك نشط حالياً. يرجى الاشتراك لنشر المنشورات داخل شركات السفر.')
        return redirect('subscription_plans')

    if request.method == 'POST':
        # معالجة إنشاء المنشور
        from .models import TravelCompanyPost
        post_type = request.POST.get('post_type', 'general')
        
        # Helper function to convert empty strings to None for numeric fields
        def get_numeric_value(value):
            if value == '' or value is None:
                return None
            try:
                return int(value) if '.' not in str(value) else float(value)
            except (ValueError, TypeError):
                return None
        
        post = TravelCompanyPost.objects.create(
            company=company,
            title=request.POST.get('title'),
            post_type=post_type,
            description=request.POST.get('description') or '',  # Default to empty string if not provided
            main_image=request.FILES.get('main_image') if 'main_image' in request.FILES else None,
            price=get_numeric_value(request.POST.get('price')),
            original_price=get_numeric_value(request.POST.get('original_price')),
            currency=request.POST.get('currency', 'IQD'),
            price_per=request.POST.get('price_per', 'person'),
            is_negotiable=request.POST.get('is_negotiable') == 'on',
            is_limited_offer=request.POST.get('is_limited_offer') == 'on',
            offer_expires_at=request.POST.get('offer_expires_at'),
            booking_method=request.POST.get('booking_method', 'call'),
            booking_phone=request.POST.get('booking_phone'),
            booking_whatsapp=request.POST.get('booking_whatsapp'),
            booking_link=request.POST.get('booking_link'),
            booking_deadline=request.POST.get('booking_deadline'),
            seats_available=get_numeric_value(request.POST.get('seats_available')),
            # حقول الرحلة - تعيين الحقول المتاحة
            departure_country=request.POST.get('trip_country') if post_type == 'trip' else None,
            departure_city=request.POST.get('trip_city') if post_type == 'trip' else None,
            destination_country=request.POST.get('trip_country') if post_type == 'trip' else None,
            destination_city=request.POST.get('trip_city') if post_type == 'trip' else None,
            departure_date=request.POST.get('departure_date') if post_type == 'trip' else None,
            return_date=request.POST.get('return_date') if post_type == 'trip' else None,
            duration_days=get_numeric_value(request.POST.get('duration_days')) if post_type == 'trip' else None,
            duration_nights=get_numeric_value(request.POST.get('duration_nights')) if post_type == 'trip' else None,
            persons_count=get_numeric_value(request.POST.get('persons_count')) if post_type == 'trip' else None,
            hotel_name=request.POST.get('hotel_name') if post_type == 'trip' else None,
            hotel_stars=get_numeric_value(request.POST.get('hotel_stars')) if post_type == 'trip' else None,
            hotel_room_type=request.POST.get('hotel_room_type') if post_type == 'trip' else None,
            hotel_nights=get_numeric_value(request.POST.get('hotel_nights')) if post_type == 'trip' else None,
            includes_breakfast=request.POST.get('includes_breakfast') == 'on' if post_type == 'trip' else False,
            includes_accommodation=request.POST.get('includes_accommodation') == 'on' if post_type == 'trip' else False,
            airline=request.POST.get('airline') if post_type == 'trip' else None,
            flight_number=request.POST.get('flight_number') if post_type == 'trip' else None,
            flight_class=request.POST.get('flight_class') if post_type == 'trip' else None,
        )
        messages.success(request, f'تم إنشاء المنشور بنجاح داخل {company.name}')
        return redirect('travel_company_detail', company.id)
    
    return render(request, 'properties/travel_company_post_form.html', {
        'broker': broker,
        'company': company,
    })


@login_required
@broker_required
def travel_company_post_edit(request, company_id, post_id):
    """تعديل منشور داخل صفحة شركة السفر"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    company = TravelCompany.objects.filter(id=company_id, broker=broker).first()
    if not company:
        messages.error(request, 'شركة السفر غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_travel_companies')
    
    from .models import TravelCompanyPost
    post = TravelCompanyPost.objects.filter(id=post_id, company=company).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('travel_company_detail', company.id)

    if request.method == 'POST':
        post_type = request.POST.get('post_type', 'general')
        
        # Helper function to convert empty strings to None for numeric fields
        def get_numeric_value(value):
            if value == '' or value is None:
                return None
            try:
                return int(value) if '.' not in str(value) else float(value)
            except (ValueError, TypeError):
                return None
        
        post.title = request.POST.get('title')
        post.post_type = post_type
        post.description = request.POST.get('description')
        if 'main_image' in request.FILES:
            post.main_image = request.FILES.get('main_image')
        post.price = get_numeric_value(request.POST.get('price'))
        post.original_price = get_numeric_value(request.POST.get('original_price'))
        post.currency = request.POST.get('currency', 'IQD')
        post.price_per = request.POST.get('price_per', 'person')
        post.is_negotiable = request.POST.get('is_negotiable') == 'on'
        post.is_limited_offer = request.POST.get('is_limited_offer') == 'on'
        post.offer_expires_at = request.POST.get('offer_expires_at')
        post.booking_method = request.POST.get('booking_method', 'call')
        post.booking_phone = request.POST.get('booking_phone')
        post.booking_whatsapp = request.POST.get('booking_whatsapp')
        post.booking_link = request.POST.get('booking_link')
        post.booking_deadline = request.POST.get('booking_deadline')
        post.seats_available = get_numeric_value(request.POST.get('seats_available'))
        
        # حقول الرحلة
        if post_type == 'trip':
            post.departure_country = request.POST.get('trip_country')
            post.departure_city = request.POST.get('trip_city')
            post.destination_country = request.POST.get('trip_country')
            post.destination_city = request.POST.get('trip_city')
            post.departure_date = request.POST.get('departure_date')
            post.return_date = request.POST.get('return_date')
            post.duration_days = get_numeric_value(request.POST.get('duration_days'))
            post.duration_nights = get_numeric_value(request.POST.get('duration_nights'))
            post.persons_count = get_numeric_value(request.POST.get('persons_count'))
            post.hotel_name = request.POST.get('hotel_name')
            post.hotel_stars = get_numeric_value(request.POST.get('hotel_stars'))
            post.hotel_room_type = request.POST.get('hotel_room_type')
            post.hotel_nights = get_numeric_value(request.POST.get('hotel_nights'))
            post.includes_breakfast = request.POST.get('includes_breakfast') == 'on'
            post.includes_accommodation = request.POST.get('includes_accommodation') == 'on'
            post.airline = request.POST.get('airline')
            post.flight_number = request.POST.get('flight_number')
            post.flight_class = request.POST.get('flight_class')
        
        post.save()
        messages.success(request, f'تم تحديث المنشور بنجاح')
        return redirect('travel_company_detail', company.id)
    
    return render(request, 'properties/travel_company_post_form.html', {
        'broker': broker,
        'company': company,
        'post': post,
    })


@login_required
@broker_required
def travel_company_post_delete(request, company_id, post_id):
    """حذف منشور داخل صفحة شركة السفر"""
    broker = get_broker(request.user)
    company = TravelCompany.objects.filter(id=company_id, broker=broker).first()
    
    if not company:
        messages.error(request, 'شركة السفر غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_travel_companies')
    
    from .models import TravelCompanyPost
    post = TravelCompanyPost.objects.filter(id=post_id, company=company).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('travel_company_detail', company.id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'تم حذف المنشور بنجاح')
        return redirect('travel_company_detail', company.id)
    
    return render(request, 'properties/travel_company_post_delete_confirm.html', {
        'company': company,
        'post': post,
    })


# ============ Hotel Functions ============

@login_required
def dallal_hotel_create(request):
    """إنشاء صفحة فندق جديدة للدلال"""
    # Always allow access - create broker in background if needed
    broker = get_broker(request.user)

    # Create broker account if not exists (silently, no redirect)
    if not broker:
        try:
            from .models import Broker
            broker = Broker.objects.create(
                user=request.user,
                phone='',
                is_active=True
            )
            messages.info(request, 'تم إنشاء حساب دلال تلقائياً')
        except Exception as e:
            # Log error but don't redirect - let user proceed
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Could not create broker for user {request.user.id}: {str(e)}')
            # Set broker to None but continue
            broker = None

    if request.method == 'POST':
        # إنشاء slug من اسم الفندق
        name = request.POST.get('name')
        slug = generate_slug(name)
        # تأكد من تفرد الـ slug
        base_slug = slug
        counter = 1
        while HotelPage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # إنشاء صفحة الفندق وربطها بالدلال
        hotel = HotelPage.objects.create(
            user=request.user,
            broker=broker,  # Will be None if broker creation failed
            page_type=request.POST.get('page_type', 'hotel'),
            is_outside_iraq=False,  # Inside Iraq hotels
            status='active',  # Set status to active
            name=name or '',  # Default to empty string if not provided
            slug=slug,
            description=request.POST.get('description') or '',  # Default to empty string if not provided
            governorate=request.POST.get('governorate') or '',  # Default to empty string if not provided
            city=request.POST.get('city') or '',  # Default to empty string if not provided
            district=request.POST.get('district') or '',  # Default to empty string if not provided
            subdistrict=request.POST.get('subdistrict') or '',  # Default to empty string if not provided
            area=request.POST.get('area') or '',  # Default to empty string if not provided
            neighborhood=request.POST.get('neighborhood') or '',  # Default to empty string if not provided
            address=request.POST.get('address') or '',  # Default to empty string if not provided
            phone=request.POST.get('phone') or '',  # Default to empty string if not provided
            email=request.POST.get('email') or '',  # Default to empty string if not provided
            whatsapp=request.POST.get('whatsapp') or '',  # Default to empty string if not provided
            website=request.POST.get('website') or '',  # Default to empty string if not provided
            facebook=request.POST.get('facebook'),
            instagram=request.POST.get('instagram'),
            telegram=request.POST.get('telegram'),
            tiktok=request.POST.get('tiktok'),
            # معلومات إضافية
            total_rooms=request.POST.get('total_rooms') or None,
            suites=request.POST.get('suites') or None,
            family_rooms=request.POST.get('family_rooms') or None,
            single_rooms=request.POST.get('single_rooms') or None,
            double_rooms=request.POST.get('double_rooms') or None,
            triple_rooms=request.POST.get('triple_rooms') or None,
            floors=request.POST.get('floors') or None,
            elevators=request.POST.get('elevators') or None,
            max_capacity=request.POST.get('max_capacity') or None,
            # الأسعار
            price_start=request.POST.get('price_start') or None,
            price_end=request.POST.get('price_end') or None,
            currency=request.POST.get('currency', 'IQD'),
            average_price_per_night=request.POST.get('average_price_per_night') or None,
            single_room_price=request.POST.get('single_room_price') or None,
            double_room_price=request.POST.get('double_room_price') or None,
            family_room_price=request.POST.get('family_room_price') or None,
            suite_price=request.POST.get('suite_price') or None,
            # معلومات إضافية في JSON
            additional_data={
                'page_name': request.POST.get('page_name'),
                'star_rating': request.POST.get('star_rating'),
                'establishment_year': request.POST.get('establishment_year'),
                'owner_name': request.POST.get('owner_name'),
                'manager_name': request.POST.get('manager_name'),
                'license_number': request.POST.get('license_number'),
                'licensing_authority': request.POST.get('licensing_authority'),
                'phone_secondary': request.POST.get('phone_secondary'),
                'booking_url': request.POST.get('booking_url'),
                'tourist_area': request.POST.get('tourist_area'),
                'nearest_airport': request.POST.get('nearest_airport'),
                'distance_to_airport': request.POST.get('distance_to_airport'),
                'distance_to_city_center': request.POST.get('distance_to_city_center'),
                'includes_tax': request.POST.get('includes_tax'),
                'includes_breakfast': request.POST.get('includes_breakfast'),
                'price_variable': request.POST.get('price_variable'),
                # Note: virtual_tour_url removed - now using file upload instead
            }
        )

        # معالجة الصور والفيديوهات
        if request.FILES.get('logo'):
            hotel.logo = request.FILES['logo']
        if request.FILES.get('cover_image'):
            hotel.cover_image = request.FILES['cover_image']
        if request.FILES.get('virtual_tour_video'):
            hotel.virtual_tour_video = request.FILES['virtual_tour_video']

        hotel.save()
        messages.success(request, f'تم إنشاء صفحة الفندق {hotel.name} بنجاح')
        return redirect('hotel_page_detail', hotel.slug)
    
    return render(request, 'properties/dallal_hotel_form.html', {
        'broker': broker,
    })


@login_required
@broker_required
def broker_hotels(request):
    """صفحة اختيار فندق لإنشاء منشور"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات الفنادق الخاصة بالدلال
    hotels = HotelPage.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'properties/broker_hotels.html', {
        'broker': broker,
        'hotels': hotels,
    })


@login_required
@broker_required
def broker_manage_hotels(request):
    """صفحة إدارة صفحات الفنادق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات الفنادق الخاصة بالدلال
    hotels = HotelPage.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'properties/broker_manage_hotels.html', {
        'broker': broker,
        'hotels': hotels,
    })


@login_required
@broker_required
def hotel_post_create(request, hotel_id):
    """إنشاء منشور جديد داخل صفحة الفندق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    hotel = HotelPage.objects.filter(id=hotel_id, user=request.user).first()
    if not hotel:
        messages.error(request, 'صفحة الفندق غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_hotels')
    
    if request.method == 'POST':
        # معالجة إنشاء المنشور
        post = HotelPost.objects.create(
            page=hotel,
            post_type=request.POST.get('post_type', 'listing'),
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            price=request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price'),
            currency=request.POST.get('currency', 'IQD'),
            valid_from=request.POST.get('valid_from'),
            valid_until=request.POST.get('valid_until'),
            # إضافة الحقول الإضافية في JSON
            additional_data={
                'room_type': request.POST.get('room_type'),
                'guests': request.POST.get('guests'),
                'nights': request.POST.get('nights'),
                'price_per_night': request.POST.get('price_per_night'),
                'original_price': request.POST.get('original_price'),
                'discount_percentage': request.POST.get('discount_percentage'),
                'breakfast': request.POST.get('breakfast'),
                'lunch': request.POST.get('lunch'),
                'dinner': request.POST.get('dinner'),
                'hall_name': request.POST.get('hall_name'),
                'event_type': request.POST.get('event_type'),
                'capacity': request.POST.get('capacity'),
                'price_per_hour': request.POST.get('price_per_hour'),
                'price_per_day': request.POST.get('price_per_day'),
                'facilities': request.POST.get('facilities'),
                'av_equipment': request.POST.get('av_equipment'),
                'audio_equipment': request.POST.get('audio_equipment'),
                'lighting': request.POST.get('lighting'),
                'catering': request.POST.get('catering'),
                'parking': request.POST.get('parking'),
                'available_date': request.POST.get('available_date'),
                'available_rooms': request.POST.get('available_rooms'),
                'available_bookings': request.POST.get('available_bookings'),
                'terms': request.POST.get('terms'),
                'booking_url': request.POST.get('booking_url'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')
        
        post.save()
        messages.success(request, f'تم إنشاء المنشور بنجاح داخل {hotel.name}')
        return redirect('hotel_page_detail', hotel.slug)
    
    return render(request, 'properties/hotel_post_form.html', {
        'broker': broker,
        'hotel': hotel,
    })


@login_required
@broker_required
def dallal_hotel_edit(request, hotel_id):
    """تعديل صفحة الفندق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    hotel = HotelPage.objects.filter(id=hotel_id, user=request.user).first()
    if not hotel:
        messages.error(request, 'صفحة الفندق غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_hotels')
    
    if request.method == 'POST':
        # معالجة تعديل الفندق
        hotel.name = request.POST.get('name', hotel.name)
        hotel.description = request.POST.get('description', hotel.description)
        # إضافة الحقول الأخرى
        hotel.save()
        messages.success(request, f'تم تعديل صفحة الفندق {hotel.name} بنجاح')
        return redirect('broker_manage_hotels')
    
    return render(request, 'properties/dallal_hotel_form.html', {
        'broker': broker,
        'hotel': hotel,
        'title': 'تعديل صفحة الفندق',
    })


# ============ Hotel Outside Iraq Functions ============

@login_required
@broker_required
def dallal_hotel_outside_create(request):
    """إنشاء صفحة فندق خارج العراق جديدة للدلال"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # إنشاء slug من اسم الفندق
        name = request.POST.get('name')
        slug = generate_slug(name)
        # تأكد من تفرد الـ slug
        base_slug = slug
        counter = 1
        while HotelPage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # إنشاء صفحة الفندق وربطها بالدلال
        hotel = HotelPage.objects.create(
            user=request.user,
            broker=broker,
            page_type=request.POST.get('page_type', 'hotel'),
            is_outside_iraq=True,
            status='active',  # Set status to active
            name=name or '',  # Default to empty string if not provided
            slug=slug,
            description=request.POST.get('description') or '',  # Default to empty string if not provided
            country=request.POST.get('country'),
            city=request.POST.get('city') or '',  # Default to empty string if not provided
            area=request.POST.get('area') or '',  # Default to empty string if not provided
            neighborhood=request.POST.get('neighborhood') or '',  # Default to empty string if not provided
            mahalla=request.POST.get('mahalla') or '',  # Default to empty string if not provided
            block=request.POST.get('block') or '',  # Default to empty string if not provided
            street=request.POST.get('street') or '',  # Default to empty string if not provided
            alley=request.POST.get('alley') or '',  # Default to empty string if not provided
            house_number=request.POST.get('house_number') or '',  # Default to empty string if not provided
            property_number=request.POST.get('property_number') or '',  # Default to empty string if not provided
            landmark=request.POST.get('landmark') or '',  # Default to empty string if not provided
            address=request.POST.get('address') or '',  # Default to empty string if not provided
            phone=request.POST.get('phone') or '',  # Default to empty string if not provided
            email=request.POST.get('email') or '',  # Default to empty string if not provided
            whatsapp=request.POST.get('whatsapp') or '',  # Default to empty string if not provided
            website=request.POST.get('website') or '',  # Default to empty string if not provided
            facebook=request.POST.get('facebook'),
            instagram=request.POST.get('instagram'),
            telegram=request.POST.get('telegram'),
            tiktok=request.POST.get('tiktok'),
            # معلومات إضافية
            total_rooms=request.POST.get('total_rooms') or None,
            suites=request.POST.get('suites') or None,
            family_rooms=request.POST.get('family_rooms') or None,
            single_rooms=request.POST.get('single_rooms') or None,
            double_rooms=request.POST.get('double_rooms') or None,
            triple_rooms=request.POST.get('triple_rooms') or None,
            floors=request.POST.get('floors') or None,
            elevators=request.POST.get('elevators') or None,
            max_capacity=request.POST.get('max_capacity') or None,
            # الأسعار
            price_start=request.POST.get('price_start') or None,
            price_end=request.POST.get('price_end') or None,
            currency=request.POST.get('currency', 'USD'),
            average_price_per_night=request.POST.get('average_price_per_night') or None,
            single_room_price=request.POST.get('single_room_price') or None,
            double_room_price=request.POST.get('double_room_price') or None,
            family_room_price=request.POST.get('family_room_price') or None,
            suite_price=request.POST.get('suite_price') or None,
            # معلومات إضافية في JSON
            additional_data={
                'page_name': request.POST.get('page_name'),
                'star_rating': request.POST.get('star_rating'),
                'establishment_year': request.POST.get('establishment_year'),
                'owner_name': request.POST.get('owner_name'),
                'manager_name': request.POST.get('manager_name'),
                'license_number': request.POST.get('license_number'),
                'licensing_authority': request.POST.get('licensing_authority'),
                'phone_secondary': request.POST.get('phone_secondary'),
                'booking_url': request.POST.get('booking_url'),
                'tourist_area': request.POST.get('tourist_area'),
                'nearest_airport': request.POST.get('nearest_airport'),
                'distance_to_airport': request.POST.get('distance_to_airport'),
                'distance_to_city_center': request.POST.get('distance_to_city_center'),
                'nearest_train_station': request.POST.get('nearest_train_station'),
                'nearest_metro_station': request.POST.get('nearest_metro_station'),
                'includes_tax': request.POST.get('includes_tax'),
                'includes_breakfast': request.POST.get('includes_breakfast'),
                'price_variable': request.POST.get('price_variable'),
                'latitude': request.POST.get('latitude'),
                'longitude': request.POST.get('longitude'),
                'enable_gps': request.POST.get('enable_gps'),
            }
        )
        
        # معالجة الصور - these might be required in the model
        if request.FILES.get('logo'):
            hotel.logo = request.FILES['logo']
        if request.FILES.get('cover_image'):
            hotel.cover_image = request.FILES['cover_image']
        
        # If no logo provided, use a default or handle the error
        if not hotel.logo:
            # For now, try to save without logo - if model requires it, we'll need to provide a default
            pass
        
        hotel.save()
        messages.success(request, f'تم إنشاء صفحة الفندق {hotel.name} بنجاح')
        return redirect('hotel_page_detail', hotel.slug)
    
    return render(request, 'properties/dallal_hotel_outside_form.html', {
        'broker': broker,
    })


@login_required
@broker_required
def broker_hotels_outside(request):
    """صفحة اختيار فندق خارج العراق لإنشاء منشور"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات الفنادق الخارجية الخاصة بالدلال
    hotels = HotelPage.objects.filter(user=request.user, is_outside_iraq=True).order_by('-created_at')
    
    return render(request, 'properties/broker_hotels_outside.html', {
        'broker': broker,
        'hotels': hotels,
    })


@login_required
@broker_required
def broker_manage_hotels_outside(request):
    """صفحة إدارة صفحات الفنادق الخارجية"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات الفنادق الخارجية الخاصة بالدلال
    hotels = HotelPage.objects.filter(user=request.user, is_outside_iraq=True).order_by('-created_at')
    
    return render(request, 'properties/broker_manage_hotels_outside.html', {
        'broker': broker,
        'hotels': hotels,
    })


@login_required
@broker_required
def hotel_outside_post_create(request, hotel_id):
    """إنشاء منشور جديد داخل صفحة فندق خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    hotel = HotelPage.objects.filter(id=hotel_id, user=request.user, is_outside_iraq=True).first()
    if not hotel:
        messages.error(request, 'صفحة الفندق غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_hotels_outside')
    
    if request.method == 'POST':
        # معالجة إنشاء المنشور
        post = HotelPost.objects.create(
            page=hotel,
            post_type=request.POST.get('post_type', 'listing'),
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            price=request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price'),
            currency=request.POST.get('currency', 'USD'),
            valid_from=request.POST.get('valid_from'),
            valid_until=request.POST.get('valid_until'),
            # إضافة الحقول الإضافية في JSON
            additional_data={
                'room_type': request.POST.get('room_type'),
                'guests': request.POST.get('guests'),
                'nights': request.POST.get('nights'),
                'price_per_night': request.POST.get('price_per_night'),
                'original_price': request.POST.get('original_price'),
                'discount_percentage': request.POST.get('discount_percentage'),
                'breakfast': request.POST.get('breakfast'),
                'lunch': request.POST.get('lunch'),
                'dinner': request.POST.get('dinner'),
                'hall_name': request.POST.get('hall_name'),
                'event_type': request.POST.get('event_type'),
                'capacity': request.POST.get('capacity'),
                'price_per_hour': request.POST.get('price_per_hour'),
                'price_per_day': request.POST.get('price_per_day'),
                'facilities': request.POST.get('facilities'),
                'av_equipment': request.POST.get('av_equipment'),
                'audio_equipment': request.POST.get('audio_equipment'),
                'lighting': request.POST.get('lighting'),
                'catering': request.POST.get('catering'),
                'parking': request.POST.get('parking'),
                'available_date': request.POST.get('available_date'),
                'available_rooms': request.POST.get('available_rooms'),
                'available_bookings': request.POST.get('available_bookings'),
                'terms': request.POST.get('terms'),
                'booking_url': request.POST.get('booking_url'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')
        
        post.save()
        messages.success(request, f'تم إنشاء المنشور بنجاح داخل {hotel.name}')
        return redirect('hotel_page_detail', hotel.slug)
    
    return render(request, 'properties/hotel_post_form.html', {
        'broker': broker,
        'hotel': hotel,
    })


@login_required
@broker_required
def dallal_hotel_outside_edit(request, hotel_id):
    """تعديل صفحة فندق خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    hotel = HotelPage.objects.filter(id=hotel_id, user=request.user, is_outside_iraq=True).first()
    if not hotel:
        messages.error(request, 'صفحة الفندق غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_hotels_outside')
    
    if request.method == 'POST':
        # معالجة تعديل الفندق
        hotel.name = request.POST.get('name', hotel.name)
        hotel.description = request.POST.get('description', hotel.description)
        # إضافة الحقول الأخرى
        hotel.save()
        messages.success(request, f'تم تعديل صفحة الفندق {hotel.name} بنجاح')
        return redirect('broker_manage_hotels_outside')
    
    return render(request, 'properties/dallal_hotel_outside_form.html', {
        'broker': broker,
        'hotel': hotel,
        'title': 'تعديل صفحة الفندق',
    })


# ============ Resort Inside Iraq Functions ============

@login_required
@broker_required
def dallal_resort_create(request):
    """إنشاء صفحة منتجع داخل العراق جديدة للدلال"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # إنشاء slug من اسم المنتجع
        name = request.POST.get('name')
        slug = generate_slug(name)
        # تأكد من تفرد الـ slug
        base_slug = slug
        counter = 1
        while HotelPage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # إنشاء صفحة المنتجع وربطها بالدلال
        resort = HotelPage.objects.create(
            user=request.user,
            broker=broker,
            page_type=request.POST.get('page_type', 'resort'),
            is_outside_iraq=False,
            status='active',  # Set status to active
            name=name or '',  # Default to empty string if not provided
            slug=slug,
            description=request.POST.get('description') or '',  # Default to empty string if not provided
            governorate=request.POST.get('governorate') or '',  # Default to empty string if not provided
            city=request.POST.get('city') or '',  # Default to empty string if not provided
            district=request.POST.get('district') or '',  # Default to empty string if not provided
            subdistrict=request.POST.get('subdistrict') or '',  # Default to empty string if not provided
            area=request.POST.get('area') or '',  # Default to empty string if not provided
            neighborhood=request.POST.get('neighborhood') or '',  # Default to empty string if not provided
            mahalla=request.POST.get('mahalla') or '',  # Default to empty string if not provided
            block=request.POST.get('block') or '',  # Default to empty string if not provided
            street=request.POST.get('street') or '',  # Default to empty string if not provided
            alley=request.POST.get('alley') or '',  # Default to empty string if not provided
            house_number=request.POST.get('house_number') or '',  # Default to empty string if not provided
            property_number=request.POST.get('property_number') or '',  # Default to empty string if not provided
            landmark=request.POST.get('landmark') or '',  # Default to empty string if not provided
            address=request.POST.get('address') or '',  # Default to empty string if not provided
            phone=request.POST.get('phone') or '',  # Default to empty string if not provided
            email=request.POST.get('email') or '',  # Default to empty string if not provided
            whatsapp=request.POST.get('whatsapp') or '',  # Default to empty string if not provided
            website=request.POST.get('website') or '',  # Default to empty string if not provided
            facebook=request.POST.get('facebook'),
            instagram=request.POST.get('instagram'),
            telegram=request.POST.get('telegram'),
            tiktok=request.POST.get('tiktok'),
            # معلومات السعة
            min_capacity=request.POST.get('min_capacity') or None,
            max_capacity=request.POST.get('max_capacity') or None,
            total_units=request.POST.get('total_units') or None,
            chalets_count=request.POST.get('chalets_count') or None,
            cabins_count=request.POST.get('cabins_count') or None,
            beds_count=request.POST.get('beds_count') or None,
            extra_beds_count=request.POST.get('extra_beds_count') or None,
            parking_spaces=request.POST.get('parking_spaces') or None,
            # الأسعار
            price_start=request.POST.get('price_start') or None,
            price_end=request.POST.get('price_end') or None,
            currency=request.POST.get('currency', 'IQD'),
            unit_price=request.POST.get('unit_price') or None,
            person_price=request.POST.get('person_price') or None,
            weekend_price=request.POST.get('weekend_price') or None,
            holiday_price=request.POST.get('holiday_price') or None,
            # معلومات إضافية في JSON
            additional_data={
                'page_name': request.POST.get('page_name'),
                'establishment_year': request.POST.get('establishment_year'),
                'owner_name': request.POST.get('owner_name'),
                'manager_name': request.POST.get('manager_name'),
                'license_number': request.POST.get('license_number'),
                'licensing_authority': request.POST.get('licensing_authority'),
                'phone_secondary': request.POST.get('phone_secondary'),
                'booking_url': request.POST.get('booking_url'),
                'tourist_area': request.POST.get('tourist_area'),
                'nearest_city': request.POST.get('nearest_city'),
                'distance_from_city_center': request.POST.get('distance_from_city_center'),
                'distance_from_main_road': request.POST.get('distance_from_main_road'),
                'latitude': request.POST.get('latitude'),
                'longitude': request.POST.get('longitude'),
                'enable_gps': request.POST.get('enable_gps'),
                'services': request.POST.getlist('services'),
                'family_friendly': request.POST.get('family_friendly'),
                'children_friendly': request.POST.get('children_friendly'),
                'pets_allowed': request.POST.get('pets_allowed'),
                'parties_allowed': request.POST.get('parties_allowed'),
                'music_allowed': request.POST.get('music_allowed'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('logo'):
            resort.logo = request.FILES['logo']
        if request.FILES.get('cover_image'):
            resort.cover_image = request.FILES['cover_image']
        
        resort.save()
        messages.success(request, f'تم إنشاء صفحة المنتجع {resort.name} بنجاح')
        return redirect('hotel_page_detail', resort.slug)
    
    return render(request, 'properties/dallal_resort_form.html', {
        'broker': broker,
    })


@login_required
@broker_required
def broker_resorts(request):
    """صفحة اختيار منتجع داخل العراق لإنشاء منشور"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات المنتجعات الداخلية الخاصة بالدلال
    resorts = HotelPage.objects.filter(user=request.user, is_outside_iraq=False, page_type__in=['resort', 'chalet', 'cabin', 'tourism_farm', 'rest_house', 'camp', 'beach', 'tourism_city', 'tourism_village']).order_by('-created_at')
    
    return render(request, 'properties/broker_resorts.html', {
        'broker': broker,
        'resorts': resorts,
    })


@login_required
@broker_required
def broker_manage_resorts(request):
    """صفحة إدارة صفحات المنتجعات الداخلية"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات المنتجعات الداخلية الخاصة بالدلال
    resorts = HotelPage.objects.filter(user=request.user, is_outside_iraq=False, page_type__in=['resort', 'chalet', 'cabin', 'tourism_farm', 'rest_house', 'camp', 'beach', 'tourism_city', 'tourism_village']).order_by('-created_at')
    
    return render(request, 'properties/broker_manage_resorts.html', {
        'broker': broker,
        'resorts': resorts,
    })


@login_required
@broker_required
def resort_post_create(request, resort_id):
    """إنشاء منشور جديد داخل صفحة منتجع داخل العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    resort = HotelPage.objects.filter(id=resort_id, user=request.user).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_resorts')
    
    if request.method == 'POST':
        # معالجة إنشاء المنشور
        post = HotelPost.objects.create(
            page=resort,
            post_type=request.POST.get('post_type', 'listing'),
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            price=request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price'),
            currency=request.POST.get('currency', 'IQD'),
            valid_from=request.POST.get('valid_from'),
            valid_until=request.POST.get('valid_until'),
            # إضافة الحقول الإضافية في JSON
            additional_data={
                'unit_type': request.POST.get('unit_type'),
                'unit_name': request.POST.get('unit_name'),
                'capacity': request.POST.get('capacity'),
                'rooms': request.POST.get('rooms'),
                'bathrooms': request.POST.get('bathrooms'),
                'facilities': request.POST.get('facilities'),
                'price_per_night': request.POST.get('price_per_night'),
                'price_per_week': request.POST.get('price_per_week'),
                'original_price': request.POST.get('original_price'),
                'discount_percentage': request.POST.get('discount_percentage'),
                'available_days': request.POST.get('available_days'),
                'available_units': request.POST.get('available_units'),
                'terms': request.POST.get('terms'),
                'booking_url': request.POST.get('booking_url'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')
        
        post.save()
        messages.success(request, f'تم إنشاء المنشور بنجاح داخل {resort.name}')
        return redirect('hotel_page_detail', resort.slug)

    return render(request, 'properties/resort_post_form.html', {
        'broker': broker,
        'resort': resort,
    })


@login_required
@broker_required
def resort_post_edit(request, post_id):
    """تعديل منشور داخل صفحة منتجع"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    post = HotelPost.objects.filter(id=post_id, page__user=request.user).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('hotel_page_detail', post.page.slug)

    if request.method == 'POST':
        post.title = request.POST.get('title', post.title)
        post.content = request.POST.get('content', post.content)
        post.price = request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price')
        post.currency = request.POST.get('currency', post.currency)
        post.valid_from = request.POST.get('valid_from', post.valid_from)
        post.valid_until = request.POST.get('valid_until', post.valid_until)
        post.additional_data = {
            'unit_type': request.POST.get('unit_type'),
            'unit_name': request.POST.get('unit_name'),
            'capacity': request.POST.get('capacity'),
            'rooms': request.POST.get('rooms'),
            'bathrooms': request.POST.get('bathrooms'),
            'facilities': request.POST.get('facilities'),
            'price_per_night': request.POST.get('price_per_night'),
            'price_per_week': request.POST.get('price_per_week'),
            'original_price': request.POST.get('original_price'),
            'discount_percentage': request.POST.get('discount_percentage'),
            'available_days': request.POST.get('available_days'),
            'available_units': request.POST.get('available_units'),
            'terms': request.POST.get('terms'),
            'booking_url': request.POST.get('booking_url'),
        }

        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')

        post.save()
        messages.success(request, f'تم تعديل المنشور بنجاح')
        return redirect('hotel_page_detail', post.page.slug)

    return render(request, 'properties/resort_post_form.html', {
        'broker': broker,
        'resort': post.page,
        'post': post,
    })


@login_required
@broker_required
def resort_post_delete(request, post_id):
    """حذف منشور داخل صفحة منتجع"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    post = HotelPost.objects.filter(id=post_id, page__user=request.user).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('hotel_page_detail', post.page.slug)

    if request.method == 'POST':
        post_title = post.title
        resort_slug = post.page.slug
        post.delete()
        messages.success(request, f'تم حذف المنشور {post_title} بنجاح')
        return redirect('hotel_page_detail', resort_slug)

    return render(request, 'properties/post_delete_confirm.html', {
        'post': post,
    })


@login_required
@broker_required
def dallal_resort_edit(request, resort_id):
    """تعديل صفحة منتجع داخل العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    resort = HotelPage.objects.filter(id=resort_id, user=request.user).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_resorts')

    if request.method == 'POST':
        # معالجة تعديل المنتجع
        resort.name = request.POST.get('name', resort.name)
        resort.description = request.POST.get('description', resort.description)
        # إضافة الحقول الأخرى
        resort.save()
        messages.success(request, f'تم تعديل صفحة المنتجع {resort.name} بنجاح')
        return redirect('broker_manage_resorts')

    return render(request, 'properties/dallal_resort_form.html', {
        'broker': broker,
        'resort': resort,
        'title': 'تعديل صفحة المنتجع',
    })


@login_required
@broker_required
def dallal_resort_delete(request, resort_id):
    """حذف صفحة منتجع داخل العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    resort = HotelPage.objects.filter(id=resort_id, user=request.user).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_resorts')

    if request.method == 'POST':
        resort_name = resort.name
        resort.delete()
        messages.success(request, f'تم حذف صفحة المنتجع {resort_name} بنجاح')
        return redirect('broker_manage_resorts')

    return render(request, 'properties/resort_delete_confirm.html', {
        'resort': resort,
    })


# ============ Resort Outside Iraq Functions ============

@login_required
@broker_required
def dallal_resort_outside_create(request):
    """إنشاء صفحة منتجع خارج العراق جديدة للدلال"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # إنشاء slug من اسم المنتجع
        name = request.POST.get('name')
        slug = generate_slug(name)
        # تأكد من تفرد الـ slug
        base_slug = slug
        counter = 1
        while HotelPage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # إنشاء صفحة المنتجع وربطها بالدلال
        resort = HotelPage.objects.create(
            user=request.user,
            broker=broker,
            page_type=request.POST.get('page_type', 'resort'),
            is_outside_iraq=True,
            status='active',  # Set status to active
            name=name or '',  # Default to empty string if not provided
            slug=slug,
            description=request.POST.get('description') or '',  # Default to empty string if not provided
            country=request.POST.get('country'),
            city=request.POST.get('city') or '',  # Default to empty string if not provided
            area=request.POST.get('area') or '',  # Default to empty string if not provided
            neighborhood=request.POST.get('neighborhood') or '',  # Default to empty string if not provided
            mahalla=request.POST.get('mahalla') or '',  # Default to empty string if not provided
            block=request.POST.get('block') or '',  # Default to empty string if not provided
            street=request.POST.get('street') or '',  # Default to empty string if not provided
            alley=request.POST.get('alley') or '',  # Default to empty string if not provided
            house_number=request.POST.get('house_number') or '',  # Default to empty string if not provided
            property_number=request.POST.get('property_number') or '',  # Default to empty string if not provided
            landmark=request.POST.get('landmark') or '',  # Default to empty string if not provided
            address=request.POST.get('address') or '',  # Default to empty string if not provided
            phone=request.POST.get('phone') or '',  # Default to empty string if not provided
            email=request.POST.get('email') or '',  # Default to empty string if not provided
            whatsapp=request.POST.get('whatsapp') or '',  # Default to empty string if not provided
            website=request.POST.get('website') or '',  # Default to empty string if not provided
            facebook=request.POST.get('facebook'),
            instagram=request.POST.get('instagram'),
            telegram=request.POST.get('telegram'),
            tiktok=request.POST.get('tiktok'),
            # معلومات السعة
            min_capacity=request.POST.get('min_capacity') or None,
            max_capacity=request.POST.get('max_capacity') or None,
            total_units=request.POST.get('total_units') or None,
            chalets_count=request.POST.get('chalets_count') or None,
            cabins_count=request.POST.get('cabins_count') or None,
            beds_count=request.POST.get('beds_count') or None,
            extra_beds_count=request.POST.get('extra_beds_count') or None,
            parking_spaces=request.POST.get('parking_spaces') or None,
            # الأسعار
            price_start=request.POST.get('price_start') or None,
            price_end=request.POST.get('price_end') or None,
            currency=request.POST.get('currency', 'USD'),
            unit_price=request.POST.get('unit_price') or None,
            person_price=request.POST.get('person_price') or None,
            weekend_price=request.POST.get('weekend_price') or None,
            holiday_price=request.POST.get('holiday_price') or None,
            # معلومات إضافية في JSON
            additional_data={
                'page_name': request.POST.get('page_name'),
                'establishment_year': request.POST.get('establishment_year'),
                'owner_name': request.POST.get('owner_name'),
                'manager_name': request.POST.get('manager_name'),
                'license_number': request.POST.get('license_number'),
                'licensing_authority': request.POST.get('licensing_authority'),
                'phone_secondary': request.POST.get('phone_secondary'),
                'booking_url': request.POST.get('booking_url'),
                'tourist_area': request.POST.get('tourist_area'),
                'nearest_city': request.POST.get('nearest_city'),
                'nearest_airport': request.POST.get('nearest_airport'),
                'distance_to_airport': request.POST.get('distance_to_airport'),
                'distance_to_city_center': request.POST.get('distance_to_city_center'),
                'nearest_train_station': request.POST.get('nearest_train_station'),
                'nearest_metro_station': request.POST.get('nearest_metro_station'),
                'nearest_beach': request.POST.get('nearest_beach'),
                'nearest_tourist_area': request.POST.get('nearest_tourist_area'),
                'nearest_mall': request.POST.get('nearest_mall'),
                'nearest_hospital': request.POST.get('nearest_hospital'),
                'latitude': request.POST.get('latitude'),
                'longitude': request.POST.get('longitude'),
                'enable_gps': request.POST.get('enable_gps'),
                'services': request.POST.getlist('services'),
                'family_friendly': request.POST.get('family_friendly'),
                'children_friendly': request.POST.get('children_friendly'),
                'pets_allowed': request.POST.get('pets_allowed'),
                'parties_allowed': request.POST.get('parties_allowed'),
                'music_allowed': request.POST.get('music_allowed'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('logo'):
            resort.logo = request.FILES['logo']
        if request.FILES.get('cover_image'):
            resort.cover_image = request.FILES['cover_image']
        
        resort.save()
        messages.success(request, f'تم إنشاء صفحة المنتجع {resort.name} بنجاح')
        return redirect('hotel_page_detail', resort.slug)
    
    return render(request, 'properties/dallal_resort_outside_form.html', {
        'broker': broker,
    })


@login_required
@broker_required
def broker_resorts_outside(request):
    """صفحة اختيار منتجع خارج العراق لإنشاء منشور"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات المنتجعات الخارجية الخاصة بالدلال
    resorts = HotelPage.objects.filter(user=request.user, is_outside_iraq=True, page_type__in=['resort', 'chalet', 'cabin', 'tourism_farm', 'rest_house', 'camp', 'beach', 'tourism_city', 'tourism_village']).order_by('-created_at')
    
    return render(request, 'properties/broker_resorts_outside.html', {
        'broker': broker,
        'resorts': resorts,
    })


@login_required
@broker_required
def broker_manage_resorts_outside(request):
    """صفحة إدارة صفحات المنتجعات الخارجية"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    # الحصول على صفحات المنتجعات الخارجية الخاصة بالدلال
    resorts = HotelPage.objects.filter(user=request.user, is_outside_iraq=True, page_type__in=['resort', 'chalet', 'cabin', 'tourism_farm', 'rest_house', 'camp', 'beach', 'tourism_city', 'tourism_village']).order_by('-created_at')
    
    return render(request, 'properties/broker_manage_resorts_outside.html', {
        'broker': broker,
        'resorts': resorts,
    })


@login_required
@broker_required
def resort_outside_post_create(request, resort_id):
    """إنشاء منشور جديد داخل صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')
    
    resort = HotelPage.objects.filter(id=resort_id, user=request.user, is_outside_iraq=True).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_resorts_outside')
    
    if request.method == 'POST':
        # معالجة إنشاء المنشور
        post = HotelPost.objects.create(
            page=resort,
            post_type=request.POST.get('post_type', 'listing'),
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            price=request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price'),
            currency=request.POST.get('currency', 'USD'),
            valid_from=request.POST.get('valid_from'),
            valid_until=request.POST.get('valid_until'),
            # إضافة الحقول الإضافية في JSON
            additional_data={
                'unit_type': request.POST.get('unit_type'),
                'unit_name': request.POST.get('unit_name'),
                'capacity': request.POST.get('capacity'),
                'rooms': request.POST.get('rooms'),
                'bathrooms': request.POST.get('bathrooms'),
                'facilities': request.POST.get('facilities'),
                'price_per_night': request.POST.get('price_per_night'),
                'price_per_week': request.POST.get('price_per_week'),
                'original_price': request.POST.get('original_price'),
                'discount_percentage': request.POST.get('discount_percentage'),
                'available_days': request.POST.get('available_days'),
                'available_units': request.POST.get('available_units'),
                'terms': request.POST.get('terms'),
                'booking_url': request.POST.get('booking_url'),
            }
        )
        
        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')
        
        post.save()
        messages.success(request, f'تم إنشاء المنشور بنجاح داخل {resort.name}')
        return redirect('hotel_page_detail', resort.slug)

    return render(request, 'properties/resort_post_form.html', {
        'broker': broker,
        'resort': resort,
    })


@login_required
@broker_required
def resort_outside_post_delete(request, post_id):
    """حذف منشور داخل صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    post = HotelPost.objects.filter(id=post_id, page__user=request.user, page__is_outside_iraq=True).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('hotel_page_detail', post.page.slug)

    if request.method == 'POST':
        post_title = post.title
        resort_slug = post.page.slug
        post.delete()
        messages.success(request, f'تم حذف المنشور {post_title} بنجاح')
        return redirect('hotel_page_detail', resort_slug)

    return render(request, 'properties/post_delete_confirm.html', {
        'post': post,
    })


@login_required
@broker_required
def resort_outside_post_edit(request, post_id):
    """تعديل منشور داخل صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    post = HotelPost.objects.filter(id=post_id, page__user=request.user, page__is_outside_iraq=True).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('hotel_page_detail', post.page.slug)

    if request.method == 'POST':
        post.title = request.POST.get('title', post.title)
        post.content = request.POST.get('content', post.content)
        post.price = request.POST.get('price') or request.POST.get('total_price') or request.POST.get('discounted_price')
        post.currency = request.POST.get('currency', post.currency)
        post.valid_from = request.POST.get('valid_from', post.valid_from)
        post.valid_until = request.POST.get('valid_until', post.valid_until)
        post.additional_data = {
            'unit_type': request.POST.get('unit_type'),
            'unit_name': request.POST.get('unit_name'),
            'capacity': request.POST.get('capacity'),
            'rooms': request.POST.get('rooms'),
            'bathrooms': request.POST.get('bathrooms'),
            'facilities': request.POST.get('facilities'),
            'price_per_night': request.POST.get('price_per_night'),
            'price_per_week': request.POST.get('price_per_week'),
            'original_price': request.POST.get('original_price'),
            'discount_percentage': request.POST.get('discount_percentage'),
            'available_days': request.POST.get('available_days'),
            'available_units': request.POST.get('available_units'),
            'terms': request.POST.get('terms'),
            'booking_url': request.POST.get('booking_url'),
        }

        # معالجة الصور
        if request.FILES.get('images'):
            post.images = request.FILES.getlist('images')

        post.save()
        messages.success(request, f'تم تعديل المنشور بنجاح')
        return redirect('hotel_page_detail', post.page.slug)

    return render(request, 'properties/resort_post_form.html', {
        'broker': broker,
        'resort': post.page,
        'post': post,
    })


@login_required
@broker_required
def resort_outside_post_delete(request, post_id):
    """حذف منشور داخل صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    post = HotelPost.objects.filter(id=post_id, page__user=request.user, page__is_outside_iraq=True).first()
    if not post:
        messages.error(request, 'المنشور غير موجود أو لا تملك صلاحية الوصول إليه')
        return redirect('hotel_page_detail', post.page.slug)

    if request.method == 'POST':
        post_title = post.title
        resort_slug = post.page.slug
        post.delete()
        messages.success(request, f'تم حذف المنشور {post_title} بنجاح')
        return redirect('hotel_page_detail', resort_slug)

    return render(request, 'properties/post_delete_confirm.html', {
        'post': post,
    })


@login_required
@broker_required
def dallal_resort_outside_edit(request, resort_id):
    """تعديل صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    resort = HotelPage.objects.filter(id=resort_id, user=request.user, is_outside_iraq=True).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_resorts_outside')

    if request.method == 'POST':
        # معالجة تعديل المنتجع
        resort.name = request.POST.get('name', resort.name)
        resort.description = request.POST.get('description', resort.description)
        # إضافة الحقول الأخرى
        resort.save()
        messages.success(request, f'تم تعديل صفحة المنتجع {resort.name} بنجاح')
        return redirect('broker_manage_resorts_outside')

    return render(request, 'properties/dallal_resort_outside_form.html', {
        'broker': broker,
        'resort': resort,
        'title': 'تعديل صفحة المنتجع خارج العراق',
    })


@login_required
@broker_required
def dallal_resort_outside_delete(request, resort_id):
    """حذف صفحة منتجع خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    resort = HotelPage.objects.filter(id=resort_id, user=request.user, is_outside_iraq=True).first()
    if not resort:
        messages.error(request, 'صفحة المنتجع غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_resorts_outside')

    if request.method == 'POST':
        resort_name = resort.name
        resort.delete()
        messages.success(request, f'تم حذف صفحة المنتجع {resort_name} بنجاح')
        return redirect('broker_manage_resorts_outside')

    return render(request, 'properties/resort_delete_confirm.html', {
        'resort': resort,
    })


@login_required
@broker_required
def dallal_hotel_outside_delete(request, hotel_id):
    """حذف صفحة فندق خارج العراق"""
    broker = get_broker(request.user)
    if not broker:
        messages.error(request, 'يجب أن تكون دلال للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    hotel = HotelPage.objects.filter(id=hotel_id, user=request.user, is_outside_iraq=True).first()
    if not hotel:
        messages.error(request, 'صفحة الفندق غير موجودة أو لا تملك صلاحية الوصول إليها')
        return redirect('broker_manage_hotels_outside')

    if request.method == 'POST':
        hotel_name = hotel.name
        hotel.delete()
        messages.success(request, f'تم حذف صفحة الفندق {hotel_name} بنجاح')
        return redirect('broker_manage_hotels_outside')

    return render(request, 'properties/hotel_delete_confirm.html', {
        'hotel': hotel,
    })
    
    return render(request, 'properties/dallal_resort_outside_form.html', {
        'broker': broker,
        'resort': resort,
        'title': 'تعديل صفحة المنتجع',
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
