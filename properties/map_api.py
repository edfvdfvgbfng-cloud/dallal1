"""
Map API Endpoints for Interactive Maps
Provides APIs for heatmaps, area statistics, nearby amenities, and location-based search
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Min, Max, Count, Q, F
from django.core.cache import cache
import logging
import math

from .models import Property, AreaStats, Amenity, HeatmapData
from .permissions_centralized import rate_limit, get_client_ip

logger = logging.getLogger(__name__)


def get_cache_key(*args):
    """Generate a cache key from arguments"""
    return "map_" + "_".join(str(arg) for arg in args)


@rate_limit(max_requests=50, period=60)
@require_GET
@login_required
def price_heatmap_api(request):
    """
    API: Get price heatmap data for a specific area
    Returns heatmap grid cells with price density values
    """
    governorate = request.GET.get('governorate')
    city = request.GET.get('city')
    property_type = request.GET.get('property_type', '')
    grid_size = float(request.GET.get('grid_size', 0.01))
    
    if not governorate or not city:
        logger.warning(f'Missing parameters in heatmap API by user {request.user.username}')
        return JsonResponse({
            'error': 'Missing required parameters: governorate and city'
        }, status=400)
    
    # Check cache
    cache_key = get_cache_key('heatmap', governorate, city, property_type, grid_size)
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    
    try:
        # Generate heatmap data
        heatmap_data = HeatmapData.generate_heatmap(
            governorate=governorate,
            city=city,
            property_type=property_type if property_type else None,
            grid_size=grid_size
        )
        
        # Format response
        response_data = {
            'governorate': governorate,
            'city': city,
            'property_type': property_type,
            'grid_size': grid_size,
            'data': [
                {
                    'lat_min': float(cell.lat_min),
                    'lat_max': float(cell.lat_max),
                    'lng_min': float(cell.lng_min),
                    'lng_max': float(cell.lng_max),
                    'value': float(cell.value),
                    'property_count': cell.property_count
                }
                for cell in heatmap_data
            ],
            'total_cells': len(heatmap_data)
        }
        
        # Cache for 1 hour
        cache.set(cache_key, response_data, 3600)
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error generating heatmap: {str(e)}")
        return JsonResponse({
            'error': 'Failed to generate heatmap data'
        }, status=500)


@rate_limit(max_requests=50, period=60)
@require_GET
def area_stats_api(request):
    """
    API: Get area statistics (average prices, property counts, trends)
    Returns statistical data for different areas
    """
    governorate = request.GET.get('governorate')
    city = request.GET.get('city')
    district = request.GET.get('district', '')
    area = request.GET.get('area', '')
    
    # Build query
    stats_query = AreaStats.objects.all()
    if governorate:
        stats_query = stats_query.filter(governorate=governorate)
    if city:
        stats_query = stats_query.filter(city=city)
    if district:
        stats_query = stats_query.filter(district=district)
    if area:
        stats_query = stats_query.filter(area=area)
    
    try:
        stats = stats_query.select_related().order_by('-updated_at')
        
        response_data = {
            'areas': [
                {
                    'governorate': stat.governorate,
                    'city': stat.city,
                    'district': stat.district,
                    'area': stat.area,
                    'avg_price': float(stat.avg_price) if stat.avg_price else None,
                    'avg_price_per_sqm': float(stat.avg_price_per_sqm) if stat.avg_price_per_sqm else None,
                    'min_price': float(stat.min_price) if stat.min_price else None,
                    'max_price': float(stat.max_price) if stat.max_price else None,
                    'total_properties': stat.total_properties,
                    'sale_properties': stat.sale_properties,
                    'rent_properties': stat.rent_properties,
                    'price_trend': stat.price_trend,
                    'price_change_percent': float(stat.price_change_percent) if stat.price_change_percent else None,
                    'view_count': stat.view_count,
                    'favorite_count': stat.favorite_count,
                    'bounds': {
                        'south': float(stat.bounds_south) if stat.bounds_south else None,
                        'north': float(stat.bounds_north) if stat.bounds_north else None,
                        'west': float(stat.bounds_west) if stat.bounds_west else None,
                        'east': float(stat.bounds_east) if stat.bounds_east else None,
                    } if stat.bounds_south else None
                }
                for stat in stats
            ],
            'total': stats.count()
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error fetching area stats: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch area statistics'
        }, status=500)


@rate_limit(max_requests=50, period=60)
@require_GET
def average_price_by_area_api(request):
    """
    API: Get average property prices by area
    Returns average prices grouped by city/district/area
    """
    governorate = request.GET.get('governorate')
    property_type = request.GET.get('property_type', '')
    transaction_type = request.GET.get('transaction_type', '')
    
    # Build property query
    property_query = Property.objects.filter(
        status='available',
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    if governorate:
        property_query = property_query.filter(governorate=governorate)
    if property_type:
        property_query = property_query.filter(type=property_type)
    if transaction_type:
        property_query = property_query.filter(transaction_type=transaction_type)
    
    try:
        # Group by city and calculate averages
        city_stats = property_query.values('city').annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            property_count=Count('id')
        ).order_by('-avg_price')
        
        # Group by district for more detail
        district_stats = property_query.values('city', 'district').annotate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            property_count=Count('id')
        ).order_by('-avg_price')
        
        response_data = {
            'by_city': [
                {
                    'city': stat['city'],
                    'avg_price': float(stat['avg_price']) if stat['avg_price'] else None,
                    'min_price': float(stat['min_price']) if stat['min_price'] else None,
                    'max_price': float(stat['max_price']) if stat['max_price'] else None,
                    'property_count': stat['property_count']
                }
                for stat in city_stats
            ],
            'by_district': [
                {
                    'city': stat['city'],
                    'district': stat['district'],
                    'avg_price': float(stat['avg_price']) if stat['avg_price'] else None,
                    'min_price': float(stat['min_price']) if stat['min_price'] else None,
                    'max_price': float(stat['max_price']) if stat['max_price'] else None,
                    'property_count': stat['property_count']
                }
                for stat in district_stats
            ]
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error calculating average prices: {str(e)}")
        return JsonResponse({
            'error': 'Failed to calculate average prices'
        }, status=500)


@rate_limit(max_requests=50, period=60)
@require_GET
def nearby_amenities_api(request):
    """
    API: Get nearby amenities (schools, hospitals, markets, etc.)
    Returns amenities within a specified radius of a location
    """
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    radius_km = float(request.GET.get('radius', 2.0))  # Default 2km radius
    amenity_types = request.GET.get('types', '').split(',') if request.GET.get('types') else []
    
    if not latitude or not longitude:
        return JsonResponse({
            'error': 'Missing required parameters: latitude and longitude'
        }, status=400)
    
    try:
        lat = float(latitude)
        lng = float(longitude)
        
        # Build amenity query
        amenities_query = Amenity.objects.all()
        
        if amenity_types:
            amenities_query = amenities_query.filter(amenity_type__in=amenity_types)
        
        # Filter by distance using Haversine formula
        nearby_amenities = []
        for amenity in amenities_query:
            distance = amenity.calculate_distance_to_property(lat, lng)
            if distance <= radius_km:
                nearby_amenities.append({
                    'id': amenity.id,
                    'name': amenity.name,
                    'type': amenity.amenity_type,
                    'type_display': amenity.get_amenity_type_display(),
                    'latitude': float(amenity.latitude),
                    'longitude': float(amenity.longitude),
                    'distance_km': round(distance, 2),
                    'address': amenity.address,
                    'phone': amenity.phone,
                    'website': amenity.website,
                    'rating': float(amenity.rating) if amenity.rating else None,
                    'opening_hours': amenity.opening_hours,
                    # Additional fields based on type
                    'education_level': amenity.education_level if amenity.amenity_type in ['school', 'university'] else None,
                    'student_count': amenity.student_count if amenity.amenity_type in ['school', 'university'] else None,
                    'bed_count': amenity.bed_count if amenity.amenity_type == 'hospital' else None,
                    'emergency_services': amenity.emergency_services if amenity.amenity_type == 'hospital' else None,
                })
        
        # Sort by distance
        nearby_amenities.sort(key=lambda x: x['distance_km'])
        
        # Group by type
        grouped_amenities = {}
        for amenity in nearby_amenities:
            amenity_type = amenity['type_display']
            if amenity_type not in grouped_amenities:
                grouped_amenities[amenity_type] = []
            grouped_amenities[amenity_type].append(amenity)
        
        response_data = {
            'latitude': lat,
            'longitude': lng,
            'radius_km': radius_km,
            'total_count': len(nearby_amenities),
            'amenities': nearby_amenities,
            'grouped_by_type': grouped_amenities
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error fetching nearby amenities: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch nearby amenities'
        }, status=500)


@rate_limit(max_requests=50, period=60)
@require_GET
def distance_calculation_api(request):
    """
    API: Calculate distance and estimated travel time between two locations
    Returns distance in km and estimated travel time by car
    """
    from_lat = request.GET.get('from_latitude')
    from_lng = request.GET.get('from_longitude')
    to_lat = request.GET.get('to_latitude')
    to_lng = request.GET.get('to_longitude')
    transport_mode = request.GET.get('transport_mode', 'car')  # car, walking, cycling
    
    if not all([from_lat, from_lng, to_lat, to_lng]):
        return JsonResponse({
            'error': 'Missing required coordinates'
        }, status=400)
    
    try:
        # Calculate distance using Haversine formula
        lat1, lng1 = math.radians(float(from_lat)), math.radians(float(from_lng))
        lat2, lng2 = math.radians(float(to_lat)), math.radians(float(to_lng))
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in km
        distance_km = 6371 * c
        
        # Estimate travel time (simple estimation)
        transport_speeds = {
            'car': 40,      # Average speed in km/h for urban areas
            'walking': 5,   # Average walking speed in km/h
            'cycling': 15   # Average cycling speed in km/h
        }
        
        speed = transport_speeds.get(transport_mode, 40)
        travel_time_hours = distance_km / speed
        travel_time_minutes = int(travel_time_hours * 60)
        
        response_data = {
            'from': {
                'latitude': float(from_lat),
                'longitude': float(from_lng)
            },
            'to': {
                'latitude': float(to_lat),
                'longitude': float(to_lng)
            },
            'distance_km': round(distance_km, 2),
            'transport_mode': transport_mode,
            'travel_time_minutes': travel_time_minutes,
            'travel_time_formatted': f"{travel_time_minutes // 60}h {travel_time_minutes % 60}m" if travel_time_minutes >= 60 else f"{travel_time_minutes}m"
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        return JsonResponse({
            'error': 'Failed to calculate distance'
        }, status=500)


@rate_limit(max_requests=50, period=60)
@require_GET
def location_based_search_api(request):
    """
    API: Search properties near a specific location (workplace, university, etc.)
    Returns properties within a specified radius
    """
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    radius_km = float(request.GET.get('radius', 5.0))  # Default 5km radius
    property_type = request.GET.get('property_type', '')
    transaction_type = request.GET.get('transaction_type', '')
    max_price = request.GET.get('max_price', '')
    min_area = request.GET.get('min_area', '')
    
    if not latitude or not longitude:
        return JsonResponse({
            'error': 'Missing required parameters: latitude and longitude'
        }, status=400)
    
    try:
        lat = float(latitude)
        lng = float(longitude)
        
        # Build property query
        property_query = Property.objects.filter(
            status='available',
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if property_type:
            property_query = property_query.filter(type=property_type)
        if transaction_type:
            property_query = property_query.filter(transaction_type=transaction_type)
        if max_price:
            property_query = property_query.filter(price__lte=float(max_price))
        if min_area:
            property_query = property_query.filter(total_area__gte=float(min_area))
        
        # Filter by distance
        nearby_properties = []
        for property_obj in property_query:
            distance = calculate_haversine_distance(
                lat, lng,
                float(property_obj.latitude),
                float(property_obj.longitude)
            )
            if distance <= radius_km:
                nearby_properties.append({
                    'id': property_obj.id,
                    'slug': property_obj.slug,
                    'title': property_obj.display_title,
                    'type': property_obj.type,
                    'transaction_type': property_obj.transaction_type,
                    'price': property_obj.price,
                    'currency': property_obj.currency,
                    'total_area': property_obj.total_area,
                    'bedrooms': property_obj.bedrooms,
                    'bathrooms': property_obj.bathrooms,
                    'latitude': float(property_obj.latitude),
                    'longitude': float(property_obj.longitude),
                    'distance_km': round(distance, 2),
                    'governorate': property_obj.governorate,
                    'city': property_obj.city,
                    'district': property_obj.district,
                    'image': property_obj.get_main_image() if hasattr(property_obj, 'get_main_image') else None,
                })
        
        # Sort by distance
        nearby_properties.sort(key=lambda x: x['distance_km'])
        
        response_data = {
            'search_location': {
                'latitude': lat,
                'longitude': lng
            },
            'radius_km': radius_km,
            'filters': {
                'property_type': property_type,
                'transaction_type': transaction_type,
                'max_price': max_price,
                'min_area': min_area
            },
            'total_count': len(nearby_properties),
            'properties': nearby_properties
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error in location-based search: {str(e)}")
        return JsonResponse({
            'error': 'Failed to perform location-based search'
        }, status=500)


@require_GET
def area_comparison_api(request):
    """
    API: Compare multiple areas by prices and services
    Returns comparison data for selected areas
    """
    areas = request.GET.get('areas', '').split(',')  # Format: "governorate,city,district;governorate,city,district"
    
    if not areas or not areas[0]:
        return JsonResponse({
            'error': 'Missing required parameter: areas'
        }, status=400)
    
    try:
        comparison_data = []
        
        for area_str in areas:
            parts = area_str.split(',')
            if len(parts) >= 2:
                governorate = parts[0].strip()
                city = parts[1].strip()
                district = parts[2].strip() if len(parts) > 2 else ''
                
                # Get area stats
                area_stats = AreaStats.objects.filter(
                    governorate=governorate,
                    city=city,
                    district=district if district else None
                ).first()
                
                # Get nearby amenities count
                if area_stats and area_stats.bounds_south:
                    amenity_count = Amenity.objects.filter(
                        governorate=governorate,
                        city=city
                    ).count()
                else:
                    amenity_count = 0
                
                comparison_data.append({
                    'governorate': governorate,
                    'city': city,
                    'district': district,
                    'avg_price': float(area_stats.avg_price) if area_stats and area_stats.avg_price else None,
                    'avg_price_per_sqm': float(area_stats.avg_price_per_sqm) if area_stats and area_stats.avg_price_per_sqm else None,
                    'total_properties': area_stats.total_properties if area_stats else 0,
                    'price_trend': area_stats.price_trend if area_stats else 'unknown',
                    'amenity_count': amenity_count,
                    'score': calculate_area_score(area_stats, amenity_count) if area_stats else 0
                })
        
        # Sort by score
        comparison_data.sort(key=lambda x: x['score'], reverse=True)
        
        response_data = {
            'areas': comparison_data,
            'total_areas': len(comparison_data)
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error comparing areas: {str(e)}")
        return JsonResponse({
            'error': 'Failed to compare areas'
        }, status=500)


@require_GET
def properties_on_map_api(request):
    """
    API: Get properties for map display with real-time updates
    Returns properties with coordinates for map rendering
    """
    governorate = request.GET.get('governorate')
    city = request.GET.get('city')
    property_type = request.GET.get('property_type', '')
    transaction_type = request.GET.get('transaction_type', '')
    limit = int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    
    # Build query
    property_query = Property.objects.filter(
        status='available',
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    if governorate:
        property_query = property_query.filter(governorate=governorate)
    if city:
        property_query = property_query.filter(city=city)
    if property_type:
        property_query = property_query.filter(type=property_type)
    if transaction_type:
        property_query = property_query.filter(transaction_type=transaction_type)
    
    try:
        # Get properties with pagination
        properties = property_query[offset:offset+limit]
        
        # Format for map display
        map_properties = []
        for property_obj in properties:
            map_properties.append({
                'id': property_obj.id,
                'slug': property_obj.slug,
                'title': property_obj.display_title,
                'type': property_obj.type,
                'transaction_type': property_obj.transaction_type,
                'price': property_obj.price,
                'currency': property_obj.currency,
                'total_area': property_obj.total_area,
                'bedrooms': property_obj.bedrooms,
                'bathrooms': property_obj.bathrooms,
                'latitude': float(property_obj.latitude),
                'longitude': float(property_obj.longitude),
                'governorate': property_obj.governorate,
                'city': property_obj.city,
                'district': property_obj.district,
                'is_featured': property_obj.is_featured,
                'created_at': property_obj.created_at.isoformat() if property_obj.created_at else None,
                'image': property_obj.get_main_image() if hasattr(property_obj, 'get_main_image') else None,
            })
        
        response_data = {
            'properties': map_properties,
            'total_count': property_query.count(),
            'limit': limit,
            'offset': offset,
            'has_more': property_query.count() > offset + limit
        }
        
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error fetching properties for map: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch properties for map'
        }, status=500)


# Helper functions

def calculate_haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula"""
    lat1, lng1 = math.radians(lat1), math.radians(lng1)
    lat2, lng2 = math.radians(lat2), math.radians(lng2)
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return 6371 * c  # Earth's radius in km


def calculate_area_score(area_stats, amenity_count):
    """Calculate a score for an area based on various factors"""
    if not area_stats:
        return 0
    
    score = 0
    
    # Price factor (lower is better, but normalized)
    if area_stats.avg_price:
        score += max(0, 100 - (area_stats.avg_price / 1000000))  # Normalize
    
    # Property availability
    score += min(area_stats.total_properties, 50)  # Cap at 50 points
    
    # Amenities
    score += min(amenity_count * 2, 30)  # Cap at 30 points
    
    # Price trend (rising areas get bonus)
    if area_stats.price_trend == 'rising':
        score += 10
    elif area_stats.price_trend == 'stable':
        score += 5
    
    return min(score, 100)  # Cap at 100