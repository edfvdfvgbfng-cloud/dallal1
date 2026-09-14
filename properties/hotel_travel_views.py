"""
Hotel and Travel Booking Views
Comprehensive booking system for hotels, car rentals, and travel packages
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q, Avg, Count
from decimal import Decimal
import json
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


# ==================== HOTEL BOOKING VIEWS ====================

@login_required
def hotel_booking_page(request, hotel_id):
    """صفحة حجز الفندق"""
    try:
        from .models import Hotel
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        context = {
            'hotel': hotel,
            'check_in': request.GET.get('check_in'),
            'check_out': request.GET.get('check_out'),
            'guests': request.GET.get('guests', 1),
            'rooms': request.GET.get('rooms', 1),
        }
        
        return render(request, 'properties/hotel_booking.html', context)
    except Exception as e:
        logger.error(f"Error in hotel_booking_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل صفحة الحجز')
        return redirect('home')


@login_required
@require_POST
def create_hotel_booking(request):
    """إنشاء حجز فندق جديد"""
    try:
        from .models import Hotel, HotelBooking
        
        hotel_id = request.POST.get('hotel_id')
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        # Create booking
        booking = HotelBooking.objects.create(
            user=request.user,
            hotel=hotel,
            check_in=request.POST.get('check_in'),
            check_out=request.POST.get('check_out'),
            room_type=request.POST.get('room_type'),
            rooms_count=int(request.POST.get('rooms_count', 1)),
            guests=int(request.POST.get('guests', 1)),
            base_price=Decimal(request.POST.get('base_price', 0)),
            taxes=Decimal(request.POST.get('taxes', 0)),
            fees=Decimal(request.POST.get('fees', 0)),
            total_price=Decimal(request.POST.get('total_price', 0)),
            guest_name=request.POST.get('guest_name'),
            guest_email=request.POST.get('guest_email'),
            guest_phone=request.POST.get('guest_phone'),
            special_requests=request.POST.get('special_requests', ''),
            status='pending'
        )
        
        messages.success(request, f'تم إنشاء حجزك بنجاح! رقم الحجز: {booking.booking_reference}')
        return redirect('hotel_booking_detail', booking_id=booking.id)
        
    except Exception as e:
        logger.error(f"Error in create_hotel_booking: {e}")
        messages.error(request, 'حدث خطأ أثناء إنشاء الحجز')
        return redirect('hotel_booking_page', hotel_id=hotel_id)


@login_required
def hotel_booking_detail(request, booking_id):
    """تفاصيل حجز الفندق"""
    try:
        from .models import HotelBooking
        booking = get_object_or_404(HotelBooking, id=booking_id, user=request.user)
        
        context = {
            'booking': booking,
        }
        
        return render(request, 'properties/hotel_booking_detail.html', context)
    except Exception as e:
        logger.error(f"Error in hotel_booking_detail: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل تفاصيل الحجز')
        return redirect('user_dashboard_enhanced')


@login_required
@require_POST
def process_hotel_payment(request, booking_id):
    """معالجة دفع حجز الفندق"""
    try:
        from .models import HotelBooking
        booking = get_object_or_404(HotelBooking, id=booking_id, user=request.user)
        
        # In production, integrate with payment gateway (Stripe, PayPal, etc.)
        # For now, we'll simulate payment processing
        
        payment_method = request.POST.get('payment_method')
        payment_id = f"PAY_{booking.booking_reference}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        booking.payment_status = 'completed'
        booking.payment_method = payment_method
        booking.payment_id = payment_id
        booking.status = 'confirmed'
        booking.confirmed_at = timezone.now()
        booking.save()
        
        messages.success(request, 'تم الدفع بنجاح! حجزك مؤكد الآن.')
        return redirect('hotel_booking_detail', booking_id=booking.id)
        
    except Exception as e:
        logger.error(f"Error in process_hotel_payment: {e}")
        messages.error(request, 'حدث خطأ أثناء معالجة الدفع')
        return redirect('hotel_booking_detail', booking_id=booking_id)


# ==================== CAR RENTAL VIEWS ====================

@login_required
def car_rental_page(request):
    """صفحة تأجير السيارات"""
    try:
        from .models import ServiceProvider
        rental_companies = ServiceProvider.objects.filter(
            service_type='car_rental',
            is_active=True
        )
        
        context = {
            'rental_companies': rental_companies,
            'pickup_date': request.GET.get('pickup_date'),
            'dropoff_date': request.GET.get('dropoff_date'),
            'pickup_location': request.GET.get('pickup_location'),
        }
        
        return render(request, 'properties/car_rental.html', context)
    except Exception as e:
        logger.error(f"Error in car_rental_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل صفحة تأجير السيارات')
        return redirect('home')


@login_required
@require_POST
def create_car_rental(request):
    """إنشاء حجز تأجير سيارة"""
    try:
        from .models import CarRental, ServiceProvider
        
        rental_company_id = request.POST.get('rental_company_id')
        rental_company = get_object_or_404(ServiceProvider, id=rental_company_id)
        
        rental = CarRental.objects.create(
            user=request.user,
            rental_company=rental_company,
            car_type=request.POST.get('car_type'),
            car_model=request.POST.get('car_model'),
            pickup_location=request.POST.get('pickup_location'),
            dropoff_location=request.POST.get('dropoff_location'),
            pickup_date=request.POST.get('pickup_date'),
            dropoff_date=request.POST.get('dropoff_date'),
            daily_rate=Decimal(request.POST.get('daily_rate', 0)),
            insurance=Decimal(request.POST.get('insurance', 0)),
            fuel_charge=Decimal(request.POST.get('fuel_charge', 0)),
            total_price=Decimal(request.POST.get('total_price', 0)),
            driver_name=request.POST.get('driver_name'),
            driver_license=request.POST.get('driver_license'),
            driver_age=int(request.POST.get('driver_age', 25)),
            special_requests=request.POST.get('special_requests', ''),
            status='pending'
        )
        
        messages.success(request, f'تم حجز السيارة بنجاح! رقم الحجز: {rental.booking_reference}')
        return redirect('car_rental_detail', rental_id=rental.id)
        
    except Exception as e:
        logger.error(f"Error in create_car_rental: {e}")
        messages.error(request, 'حدث خطأ أثناء حجز السيارة')
        return redirect('car_rental_page')


@login_required
def car_rental_detail(request, rental_id):
    """تفاصيل حجز السيارة"""
    try:
        from .models import CarRental
        rental = get_object_or_404(CarRental, id=rental_id, user=request.user)
        
        context = {
            'rental': rental,
        }
        
        return render(request, 'properties/car_rental_detail.html', context)
    except Exception as e:
        logger.error(f"Error in car_rental_detail: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل تفاصيل الحجز')
        return redirect('user_dashboard_enhanced')


# ==================== TRAVEL PACKAGE VIEWS ====================

@login_required
def travel_packages_page(request):
    """صفحة الرحلات السياحية"""
    try:
        from .models import TravelPackage
        
        packages = TravelPackage.objects.filter(
            status='published'
        ).order_by('-is_featured', '-created_at')
        
        context = {
            'packages': packages,
            'travel_type': request.GET.get('travel_type'),
            'destination': request.GET.get('destination'),
        }
        
        return render(request, 'properties/travel_packages.html', context)
    except Exception as e:
        logger.error(f"Error in travel_packages_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل الرحلات السياحية')
        return redirect('home')


@login_required
def travel_package_detail(request, package_id):
    """تفاصيل الرحلة السياحية"""
    try:
        from .models import TravelPackage
        package = get_object_or_404(TravelPackage, id=package_id)
        
        context = {
            'package': package,
        }
        
        return render(request, 'properties/travel_package_detail.html', context)
    except Exception as e:
        logger.error(f"Error in travel_package_detail: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل تفاصيل الرحلة')
        return redirect('travel_packages_page')


@login_required
def create_custom_travel_package(request):
    """إنشاء رحلة مخصصة"""
    try:
        from .models import TravelPackage, TravelItinerary
        
        if request.method == 'POST':
            package = TravelPackage.objects.create(
                user=request.user,
                package_type='custom',
                travel_type=request.POST.get('travel_type'),
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                destination=request.POST.get('destination'),
                country_id=request.POST.get('country'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                base_price=Decimal(request.POST.get('base_price', 0)),
                max_participants=int(request.POST.get('max_participants', 1)),
                status='draft'
            )
            
            messages.success(request, 'تم إنشاء الرحلة المخصصة بنجاح!')
            return redirect('travel_package_detail', package_id=package.id)
        
        return render(request, 'properties/create_custom_travel_package.html')
        
    except Exception as e:
        logger.error(f"Error in create_custom_travel_package: {e}")
        messages.error(request, 'حدث خطأ أثناء إنشاء الرحلة المخصصة')
        return redirect('travel_packages_page')


@login_required
@require_POST
def book_travel_package(request, package_id):
    """حجز رحلة سياحية"""
    try:
        from .models import TravelPackage, TravelBooking
        
        package = get_object_or_404(TravelPackage, id=package_id)
        
        booking = TravelBooking.objects.create(
            user=request.user,
            package=package,
            adults_count=int(request.POST.get('adults_count', 1)),
            children_count=int(request.POST.get('children_count', 0)),
            infants_count=int(request.POST.get('infants_count', 0)),
            departure_date=request.POST.get('departure_date'),
            return_date=request.POST.get('return_date'),
            base_price=package.base_price,
            total_price=Decimal(request.POST.get('total_price', package.total_price)),
            lead_guest_name=request.POST.get('lead_guest_name'),
            lead_guest_email=request.POST.get('lead_guest_email'),
            lead_guest_phone=request.POST.get('lead_guest_phone'),
            special_requests=request.POST.get('special_requests', ''),
            status='pending'
        )
        
        messages.success(request, f'تم حجز الرحلة بنجاح! رقم الحجز: {booking.booking_reference}')
        return redirect('travel_booking_detail', booking_id=booking.id)
        
    except Exception as e:
        logger.error(f"Error in book_travel_package: {e}")
        messages.error(request, 'حدث خطأ أثناء حجز الرحلة')
        return redirect('travel_package_detail', package_id=package_id)


# ==================== AI ITINERARY GENERATION ====================

@login_required
def generate_ai_itinerary(request):
    """توليد جدول زمني بالذكاء الاصطناعي"""
    try:
        from .ai_travel_itinerary_placeholder import generate_itinerary
        
        if request.method == 'POST':
            destination = request.POST.get('destination')
            duration = int(request.POST.get('duration', 3))
            interests = request.POST.getlist('interests')
            budget = Decimal(request.POST.get('budget', 0))
            
            # Generate itinerary using AI
            itinerary = generate_itinerary(
                destination=destination,
                duration=duration,
                interests=interests,
                budget=budget
            )
            
            messages.success(request, 'تم توليد الجدول الزمني بنجاح!')
            return render(request, 'properties/ai_itinerary_result.html', {
                'itinerary': itinerary,
                'destination': destination,
                'duration': duration
            })
        
        return render(request, 'properties/generate_ai_itinerary.html')
        
    except Exception as e:
        logger.error(f"Error in generate_ai_itinerary: {e}")
        messages.error(request, 'حدث خطأ أثناء توليد الجدول الزمني')
        return redirect('travel_packages_page')


# ==================== TOUR GUIDE VIEWS ====================

@login_required
def tour_guides_page(request):
    """صفحة المرشدين السياحيين"""
    try:
        from .models import TourGuide
        
        guides = TourGuide.objects.filter(
            is_active=True,
            is_verified=True
        ).order_by('-rating')
        
        context = {
            'guides': guides,
            'destination': request.GET.get('destination'),
            'language': request.GET.get('language'),
        }
        
        return render(request, 'properties/tour_guides.html', context)
    except Exception as e:
        logger.error(f"Error in tour_guides_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل المرشدين السياحيين')
        return redirect('home')


@login_required
def tour_guide_detail(request, guide_id):
    """تفاصيل المرشد السياحي"""
    try:
        from .models import TourGuide
        guide = get_object_or_404(TourGuide, id=guide_id)
        
        context = {
            'guide': guide,
        }
        
        return render(request, 'properties/tour_guide_detail.html', context)
    except Exception as e:
        logger.error(f"Error in tour_guide_detail: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل تفاصيل المرشد')
        return redirect('tour_guides_page')


@login_required
@require_POST
def book_tour_guide(request, guide_id):
    """حجز مرشد سياحي"""
    try:
        from .models import TourGuide
        
        guide = get_object_or_404(TourGuide, id=guide_id)
        
        # Create booking logic here
        # This would integrate with the travel booking system
        
        messages.success(request, 'تم إرسال طلب حجز المرشد بنجاح!')
        return redirect('tour_guide_detail', guide_id=guide_id)
        
    except Exception as e:
        logger.error(f"Error in book_tour_guide: {e}")
        messages.error(request, 'حدث خطأ أثناء حجز المرشد')
        return redirect('tour_guide_detail', guide_id=guide_id)


# ==================== HOTEL COMPARISON VIEW ====================

@login_required
def hotel_comparison_page(request):
    """صفحة مقارنة الفنادق"""
    try:
        from .models import Hotel
        
        hotel_ids = request.GET.getlist('hotels')
        hotels = Hotel.objects.filter(id__in=hotel_ids)
        
        context = {
            'hotels': hotels,
        }
        
        return render(request, 'properties/hotel_comparison.html', context)
    except Exception as e:
        logger.error(f"Error in hotel_comparison_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل صفحة المقارنة')
        return redirect('home')


# ==================== HOTEL RATING VIEW ====================

@login_required
def hotel_rating_page(request, booking_id):
    """صفحة تقييم الفندق"""
    try:
        from .models import HotelBooking
        
        booking = get_object_or_404(HotelBooking, id=booking_id, user=request.user)
        
        if request.method == 'POST':
            from .models import HotelRating
            
            rating = HotelRating.objects.create(
                user=request.user,
                hotel=booking.hotel,
                booking=booking,
                cleanliness=int(request.POST.get('cleanliness', 5)),
                location=int(request.POST.get('location', 5)),
                service=int(request.POST.get('service', 5)),
                value=int(request.POST.get('value', 5)),
                facilities=int(request.POST.get('facilities', 5)),
                title=request.POST.get('title'),
                review=request.POST.get('review'),
                is_verified_booking=True,
                verified_stay_date=booking.check_in
            )
            
            messages.success(request, 'تم إرسال تقييمك بنجاح!')
            return redirect('hotel_booking_detail', booking_id=booking_id)
        
        context = {
            'booking': booking,
        }
        
        return render(request, 'properties/hotel_rating.html', context)
    except Exception as e:
        logger.error(f"Error in hotel_rating_page: {e}")
        messages.error(request, 'حدث خطأ أثناء تحميل صفحة التقييم')
        return redirect('user_dashboard_enhanced')


# ==================== HOTEL PRICE ALERT VIEW ====================

@login_required
def create_hotel_price_alert(request):
    """إنشاء تنبيه انخفاض سعر الفندق"""
    try:
        from .models import Hotel, HotelPriceAlert
        
        if request.method == 'POST':
            hotel_id = request.POST.get('hotel_id')
            hotel = get_object_or_404(Hotel, id=hotel_id)
            
            alert = HotelPriceAlert.objects.create(
                user=request.user,
                hotel=hotel,
                target_price=Decimal(request.POST.get('target_price')),
                current_price=hotel.price_per_night,
                check_in_date=request.POST.get('check_in_date'),
                check_out_date=request.POST.get('check_out_date'),
                is_active=True
            )
            
            messages.success(request, 'تم إنشاء تنبيه السعر بنجاح!')
            return redirect('hotel_detail', hotel_id=hotel_id)
        
        return render(request, 'properties/create_hotel_price_alert.html')
    except Exception as e:
        logger.error(f"Error in create_hotel_price_alert: {e}")
        messages.error(request, 'حدث خطأ أثناء إنشاء تنبيه السعر')
        return redirect('home')


# ==================== API ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hotel_comparison_api(request):
    """API لمقارنة الفنادق"""
    try:
        hotel_ids = request.GET.getlist('hotels')
        from .models import Hotel
        
        hotels = Hotel.objects.filter(id__in=hotel_ids)
        
        comparison_data = []
        for hotel in hotels:
            try:
                avg_rating = hotel.ratings.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0
                comparison_data.append({
                    'id': hotel.id,
                    'name': hotel.name,
                    'price_per_night': str(hotel.price_per_night) if hotel.price_per_night else 'غير محدد',
                    'rating': round(avg_rating, 1),
                    'rating_count': hotel.ratings.count(),
                    'location': hotel.city,
                    'amenities': hotel.amenities if hasattr(hotel, 'amenities') else [],
                    'image': hotel.main_image.url if hotel.main_image else '/static/img/placeholder-hotel.svg'
                })
            except Exception as e:
                logger.error(f"Error processing hotel {hotel.id}: {e}")
                continue
        
        return Response({'hotels': comparison_data})
    except Exception as e:
        logger.error(f"Error in hotel_comparison_api: {e}")
        return Response({'hotels': []}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hotel_booking_api(request):
    """API لحجز الفندق"""
    try:
        from .models import Hotel, HotelBooking
        
        hotel_id = request.data.get('hotel_id')
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        booking = HotelBooking.objects.create(
            user=request.user,
            hotel=hotel,
            check_in=request.data.get('check_in'),
            check_out=request.data.get('check_out'),
            room_type=request.data.get('room_type'),
            rooms_count=int(request.data.get('rooms_count', 1)),
            guests=int(request.data.get('guests', 1)),
            base_price=Decimal(request.data.get('base_price', 0)),
            taxes=Decimal(request.data.get('taxes', 0)),
            fees=Decimal(request.data.get('fees', 0)),
            total_price=Decimal(request.data.get('total_price', 0)),
            guest_name=request.data.get('guest_name'),
            guest_email=request.data.get('guest_email'),
            guest_phone=request.data.get('guest_phone'),
            special_requests=request.data.get('special_requests', ''),
            status='pending'
        )
        
        return Response({
            'success': True,
            'booking_id': booking.id,
            'booking_reference': booking.booking_reference,
            'message': 'تم إنشاء الحجز بنجاح'
        })
    except Exception as e:
        logger.error(f"Error in hotel_booking_api: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_itinerary_api(request):
    """API لتوليد جدول زمني بالذكاء الاصطناعي"""
    try:
        from .ai_travel_itinerary_placeholder import generate_itinerary
        
        destination = request.data.get('destination')
        duration = int(request.data.get('duration', 3))
        interests = request.data.get('interests', [])
        budget = Decimal(request.data.get('budget', 0))
        
        itinerary = generate_itinerary(
            destination=destination,
            duration=duration,
            interests=interests,
            budget=budget
        )
        
        return Response({
            'success': True,
            'itinerary': itinerary
        })
    except Exception as e:
        logger.error(f"Error in ai_itinerary_api: {e}")
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hotel_points_api(request, hotel_id):
    """API للحصول على نقاط الفندق"""
    try:
        from .models import Hotel, HotelPointsSystem
        
        hotel = get_object_or_404(Hotel, id=hotel_id)
        points_system, created = HotelPointsSystem.objects.get_or_create(hotel=hotel)
        
        return Response({
            'hotel_id': hotel.id,
            'total_points': points_system.total_points,
            'available_points': points_system.available_points,
            'level': points_system.level,
            'level_name': points_system.level_name,
            'benefits': points_system.benefits
        })
    except Exception as e:
        logger.error(f"Error in hotel_points_api: {e}")
        return Response({'error': str(e)}, status=500)