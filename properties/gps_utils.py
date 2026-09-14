"""
GPS and Location Utilities
Handles GPS coordinates, distance calculations, and nearby property search
"""

import math
from typing import List, Tuple, Dict, Any
from django.db.models import Q
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GPSCalculator:
    """GPS coordinate calculations using Haversine formula"""
    
    EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers
    EARTH_RADIUS_MILES = 3959.0  # Earth's radius in miles
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = 'km') -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            unit: Distance unit ('km' or 'miles')
            
        Returns:
            Distance in specified unit
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Choose radius based on unit
        radius = GPSCalculator.EARTH_RADIUS_KM if unit == 'km' else GPSCalculator.EARTH_RADIUS_MILES
        
        return c * radius
    
    @staticmethod
    def bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box around a point
        
        Args:
            lat, lon: Center coordinates
            radius_km: Radius in kilometers
            
        Returns:
            Tuple of (min_lat, max_lat, min_lon, max_lon)
        """
        # Earth's radius in km
        earth_radius = GPSCalculator.EARTH_RADIUS_KM
        
        # Calculate bounding box
        lat_delta = (radius_km / earth_radius) * (180 / math.pi)
        lon_delta = (radius_km / earth_radius) * (180 / math.pi) / math.cos(math.radians(lat))
        
        min_lat = lat - lat_delta
        max_lat = lat + lat_delta
        min_lon = lon - lon_delta
        max_lon = lon + lon_delta
        
        return (min_lat, max_lat, min_lon, max_lon)
    
    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate bearing between two points
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Bearing in degrees (0-360)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
        """
        Calculate midpoint between two coordinates
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Tuple of (mid_lat, mid_lon)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        bx = math.cos(lat2) * math.cos(dlon)
        by = math.cos(lat2) * math.sin(dlon)
        
        lat3 = math.atan2(
            math.sin(lat1) + math.sin(lat2),
            math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2)
        )
        lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)
        
        return (math.degrees(lat3), math.degrees(lon3))


class NearbyPropertyFinder:
    """Find properties near a given location"""
    
    @staticmethod
    def find_nearby_properties(
        lat: float,
        lon: float,
        radius_km: float = 5.0,
        property_model=None,
        filters: Dict[str, Any] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find properties within a radius of a location
        
        Args:
            lat, lon: Center coordinates
            radius_km: Search radius in kilometers
            property_model: Property model class
            filters: Additional query filters
            limit: Maximum number of results
            
        Returns:
            List of property dictionaries with distance information
        """
        if property_model is None:
            from .models import Property
            property_model = Property
        
        filters = filters or {}
        
        # Calculate bounding box for initial filtering
        min_lat, max_lat, min_lon, max_lon = GPSCalculator.bounding_box(lat, lon, radius_km)
        
        # Build query
        query = Q(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lon,
            longitude__lte=max_lon,
            status='available'
        )
        
        # Add additional filters
        for key, value in filters.items():
            if value:
                query &= Q(**{key: value})
        
        # Execute query
        properties = property_model.objects.filter(query)[:limit * 2]  # Get more for distance filtering
        
        # Calculate exact distances and filter
        nearby_properties = []
        for prop in properties:
            if prop.latitude and prop.longitude:
                distance = GPSCalculator.haversine_distance(
                    lat, lon, prop.latitude, prop.longitude
                )
                
                if distance <= radius_km:
                    bearing = GPSCalculator.calculate_bearing(
                        lat, lon, prop.latitude, prop.longitude
                    )
                    
                    nearby_properties.append({
                        'property': prop,
                        'distance_km': round(distance, 2),
                        'distance_miles': round(distance * 0.621371, 2),
                        'bearing': round(bearing, 2),
                        'bearing_direction': GPSCalculator._get_bearing_direction(bearing)
                    })
        
        # Sort by distance and limit results
        nearby_properties.sort(key=lambda x: x['distance_km'])
        return nearby_properties[:limit]
    
    @staticmethod
    def _get_bearing_direction(bearing: float) -> str:
        """Get compass direction from bearing"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = round(bearing / 45) % 8
        return directions[index]
    
    @staticmethod
    def find_properties_in_area(
        bounds: Tuple[float, float, float, float],
        property_model=None,
        filters: Dict[str, Any] = None,
        limit: int = 100
    ) -> List:
        """
        Find properties within a rectangular area
        
        Args:
            bounds: Tuple of (min_lat, max_lat, min_lon, max_lon)
            property_model: Property model class
            filters: Additional query filters
            limit: Maximum number of results
            
        Returns:
            List of properties within the area
        """
        if property_model is None:
            from .models import Property
            property_model = Property
        
        filters = filters or {}
        min_lat, max_lat, min_lon, max_lon = bounds
        
        query = Q(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lon,
            longitude__lte=max_lon,
            status='available'
        )
        
        for key, value in filters.items():
            if value:
                query &= Q(**{key: value})
        
        return list(property_model.objects.filter(query)[:limit])
    
    @staticmethod
    def cluster_properties(
        properties: List,
        cluster_radius_km: float = 0.5,
        min_cluster_size: int = 3
    ) -> List[List]:
        """
        Cluster nearby properties together
        
        Args:
            properties: List of properties with coordinates
            cluster_radius_km: Maximum distance between properties in same cluster
            min_cluster_size: Minimum properties to form a cluster
            
        Returns:
            List of property clusters
        """
        if not properties:
            return []
        
        clusters = []
        used_indices = set()
        
        for i, prop1 in enumerate(properties):
            if i in used_indices:
                continue
            
            cluster = [prop1]
            used_indices.add(i)
            
            for j, prop2 in enumerate(properties):
                if j in used_indices:
                    continue
                
                if hasattr(prop1, 'latitude') and hasattr(prop1, 'longitude') and \
                   hasattr(prop2, 'latitude') and hasattr(prop2, 'longitude'):
                    distance = GPSCalculator.haversine_distance(
                        prop1.latitude, prop1.longitude,
                        prop2.latitude, prop2.longitude
                    )
                    
                    if distance <= cluster_radius_km:
                        cluster.append(prop2)
                        used_indices.add(j)
            
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
        
        return clusters


class LocationValidator:
    """Validate and normalize location data"""
    
    IRAQ_BOUNDS = {
        'min_lat': 29.0,
        'max_lat': 37.5,
        'min_lon': 38.5,
        'max_lon': 48.5
    }
    
    @staticmethod
    def validate_iraq_coordinates(lat: float, lon: float) -> bool:
        """
        Validate if coordinates are within Iraq bounds
        
        Args:
            lat, lon: Coordinates to validate
            
        Returns:
            True if coordinates are valid for Iraq
        """
        bounds = LocationValidator.IRAQ_BOUNDS
        return (
            bounds['min_lat'] <= lat <= bounds['max_lat'] and
            bounds['min_lon'] <= lon <= bounds['max_lon']
        )
    
    @staticmethod
    def normalize_coordinates(lat: float, lon: float) -> Tuple[float, float]:
        """
        Normalize coordinates to valid ranges
        
        Args:
            lat, lon: Coordinates to normalize
            
        Returns:
            Normalized (lat, lon) tuple
        """
        # Clamp latitude to [-90, 90]
        lat = max(-90, min(90, lat))
        
        # Normalize longitude to [-180, 180]
        lon = ((lon + 180) % 360) - 180
        
        return (lat, lon)
    
    @staticmethod
    def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
        """
        Format coordinates as a string
        
        Args:
            lat, lon: Coordinates to format
            precision: Decimal precision
            
        Returns:
            Formatted coordinate string
        """
        return f"{lat:.{precision}f}, {lon:.{precision}f}"


class GeocodingService:
    """Service for geocoding operations (placeholder for future integration)"""
    
    ENABLED = False
    API_KEY = None
    PROVIDER = None  # 'google', 'mapbox', 'here', etc.
    
    @classmethod
    def initialize(cls):
        """Initialize geocoding service"""
        cls.ENABLED = getattr(settings, 'GEOCODING_ENABLED', False)
        cls.API_KEY = getattr(settings, 'GEOCODING_API_KEY', None)
        cls.PROVIDER = getattr(settings, 'GEOCODING_PROVIDER', None)
        
        if cls.ENABLED and cls.API_KEY:
            logger.info(f"Geocoding service initialized: {cls.PROVIDER}")
    
    @classmethod
    def geocode_address(cls, address: str) -> Tuple[float, float] or None:
        """
        Convert address to coordinates
        
        Args:
            address: Address string
            
        Returns:
            Tuple of (lat, lon) or None if geocoding fails
        """
        if not cls.ENABLED or not cls.API_KEY:
            logger.warning("Geocoding service not enabled")
            return None
        
        try:
            if cls.PROVIDER == 'google':
                return cls._geocode_google(address)
            elif cls.PROVIDER == 'mapbox':
                return cls._geocode_mapbox(address)
            else:
                logger.warning(f"Unsupported geocoding provider: {cls.PROVIDER}")
                return None
        except Exception as e:
            logger.error(f"Geocoding failed: {str(e)}")
            return None
    
    @classmethod
    def reverse_geocode(cls, lat: float, lon: float) -> str or None:
        """
        Convert coordinates to address
        
        Args:
            lat, lon: Coordinates
            
        Returns:
            Address string or None if reverse geocoding fails
        """
        if not cls.ENABLED or not cls.API_KEY:
            logger.warning("Geocoding service not enabled")
            return None
        
        try:
            if cls.PROVIDER == 'google':
                return cls._reverse_geocode_google(lat, lon)
            elif cls.PROVIDER == 'mapbox':
                return cls._reverse_geocode_mapbox(lat, lon)
            else:
                logger.warning(f"Unsupported geocoding provider: {cls.PROVIDER}")
                return None
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {str(e)}")
            return None
    
    @classmethod
    def _geocode_google(cls, address: str) -> Tuple[float, float] or None:
        """Google Maps Geocoding API"""
        try:
            import requests
            
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': cls.API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
            
            return None
        except ImportError:
            logger.error("requests library not installed")
            return None
        except Exception as e:
            logger.error(f"Google geocoding failed: {str(e)}")
            return None
    
    @classmethod
    def _reverse_geocode_google(cls, lat: float, lon: float) -> str or None:
        """Google Maps Reverse Geocoding API"""
        try:
            import requests
            
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'latlng': f"{lat},{lon}",
                'key': cls.API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                return data['results'][0]['formatted_address']
            
            return None
        except ImportError:
            logger.error("requests library not installed")
            return None
        except Exception as e:
            logger.error(f"Google reverse geocoding failed: {str(e)}")
            return None
    
    @classmethod
    def _geocode_mapbox(cls, address: str) -> Tuple[float, float] or None:
        """Mapbox Geocoding API"""
        try:
            import requests
            
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
            params = {
                'access_token': cls.API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['features']:
                coordinates = data['features'][0]['center']
                return (coordinates[1], coordinates[0])  # Mapbox returns [lon, lat]
            
            return None
        except ImportError:
            logger.error("requests library not installed")
            return None
        except Exception as e:
            logger.error(f"Mapbox geocoding failed: {str(e)}")
            return None
    
    @classmethod
    def _reverse_geocode_mapbox(cls, lat: float, lon: float) -> str or None:
        """Mapbox Reverse Geocoding API"""
        try:
            import requests
            
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json"
            params = {
                'access_token': cls.API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['features']:
                return data['features'][0]['place_name']
            
            return None
        except ImportError:
            logger.error("requests library not installed")
            return None
        except Exception as e:
            logger.error(f"Mapbox reverse geocoding failed: {str(e)}")
            return None


# Initialize geocoding service on module load
GeocodingService.initialize()