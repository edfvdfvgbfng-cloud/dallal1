"""
Location Intelligence System
Handles geospatial queries and location-based search
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import math

from .ai_multimodal_input import LocationData

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Types of nearby services"""
    SCHOOL = "school"
    HOSPITAL = "hospital"
    MARKET = "market"
    UNIVERSITY = "university"
    MOSQUE = "mosque"
    BANK = "bank"
    PARK = "park"
    RESTAURANT = "restaurant"


@dataclass
class NearbyService:
    """Represents a nearby service"""
    service_id: str
    service_type: ServiceType
    name: str
    latitude: float
    longitude: float
    distance_km: float
    address: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'service_id': self.service_id,
            'service_type': self.service_type.value,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'distance_km': self.distance_km,
            'address': self.address
        }


@dataclass
class LocationConstraint:
    """Represents a location-based constraint"""
    constraint_type: str  # 'near', 'within_radius', 'in_area'
    service_type: ServiceType = None
    latitude: float = None
    longitude: float = None
    radius_km: float = None
    governorate: str = None
    district: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'constraint_type': self.constraint_type,
            'service_type': self.service_type.value if self.service_type else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'radius_km': self.radius_km,
            'governorate': self.governorate,
            'district': self.district
        }


class LocationIntelligenceSystem:
    """
    Handles location-based queries and geospatial search
    Only uses actual location data when available
    """
    
    def __init__(self):
        self.service_database: Dict[ServiceType, List[NearbyService]] = {}
        self.query_history: List[Dict] = []
    
    def process_location_input(self, location: LocationData) -> LocationData:
        """
        Process location input and enrich with geospatial data
        
        Args:
            location: Location data to process
            
        Returns:
            Enriched location data
        """
        try:
            # Reverse geocode if address not provided
            if not location.address:
                address_info = self._reverse_geocode(location.latitude, location.longitude)
                location.address = address_info.get('address')
                location.governorate = address_info.get('governorate')
                location.district = address_info.get('district')
            
            # Find nearby services
            if location.radius_km:
                location.nearby_services = self._find_nearby_services(
                    location.latitude, location.longitude, location.radius_km
                )
            
            logger.info(f"Processed location {location.location_id}")
            return location
            
        except Exception as e:
            logger.error(f"Error processing location: {str(e)}")
            return location
    
    def parse_natural_location_request(self, query: str) -> Optional[LocationConstraint]:
        """
        Parse natural language location request
        
        Args:
            query: Natural language query (e.g., "قريب من المدرسة")
            
        Returns:
            LocationConstraint if understood
        """
        query_lower = query.lower()
        
        # Parse "near [service]" patterns
        service_patterns = {
            'قريب من المدرسة': ServiceType.SCHOOL,
            'قريب من المستشفى': ServiceType.HOSPITAL,
            'قريب من السوق': ServiceType.MARKET,
            'قريب من الجامعة': ServiceType.UNIVERSITY,
            'قريب من المسجد': ServiceType.MOSQUE,
            'قريب من البنك': ServiceType.BANK,
            'قريب من الحديقة': ServiceType.PARK
        }
        
        for pattern, service_type in service_patterns.items():
            if pattern in query_lower:
                return LocationConstraint(
                    constraint_type='near',
                    service_type=service_type
                )
        
        # Parse "within X km of [location]" patterns
        import re
        radius_match = re.search(r'(\d+(?:\.\d+)?)\s*(km|كيلومتر|كيلومترات)', query_lower)
        if radius_match:
            radius = float(radius_match.group(1))
            return LocationConstraint(
                constraint_type='within_radius',
                radius_km=radius
            )
        
        return None
    
    def calculate_distance(self, 
                         lat1: float, 
                         lon1: float, 
                         lat2: float, 
                         lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def find_properties_within_radius(self,
                                     center_lat: float,
                                     center_lon: float,
                                     radius_km: float,
                                     properties: List[Dict]) -> List[Dict]:
        """
        Find properties within a radius of a point
        
        Args:
            center_lat, center_lon: Center coordinates
            radius_km: Search radius
            properties: List of properties to search
            
        Returns:
            Properties within radius with distance
        """
        matching_properties = []
        
        for prop in properties:
            prop_lat = prop.get('latitude')
            prop_lon = prop.get('longitude')
            
            if prop_lat and prop_lon:
                distance = self.calculate_distance(
                    center_lat, center_lon, prop_lat, prop_lon
                )
                
                if distance <= radius_km:
                    prop_copy = prop.copy()
                    prop_copy['distance_km'] = distance
                    matching_properties.append(prop_copy)
        
        # Sort by distance
        matching_properties.sort(key=lambda x: x['distance_km'])
        
        return matching_properties
    
    def find_properties_near_service(self,
                                   service_type: ServiceType,
                                   max_distance_km: float,
                                   properties: List[Dict]) -> List[Dict]:
        """
        Find properties near a specific service type
        
        Args:
            service_type: Type of service
            max_distance_km: Maximum distance
            properties: List of properties to search
            
        Returns:
            Properties near service with distance
        """
        # Get service locations
        services = self.service_database.get(service_type, [])
        
        if not services:
            logger.warning(f"No services found for type {service_type.value}")
            return []
        
        matching_properties = []
        
        for prop in properties:
            prop_lat = prop.get('latitude')
            prop_lon = prop.get('longitude')
            
            if prop_lat and prop_lon:
                # Find nearest service of this type
                min_distance = float('inf')
                
                for service in services:
                    distance = self.calculate_distance(
                        prop_lat, prop_lon, service.latitude, service.longitude
                    )
                    min_distance = min(min_distance, distance)
                
                if min_distance <= max_distance_km:
                    prop_copy = prop.copy()
                    prop_copy['distance_to_service'] = min_distance
                    prop_copy['service_type'] = service_type.value
                    matching_properties.append(prop_copy)
        
        # Sort by distance to service
        matching_properties.sort(key=lambda x: x['distance_to_service'])
        
        return matching_properties
    
    def _reverse_geocode(self, lat: float, lon: float) -> Dict:
        """Reverse geocode coordinates to address (placeholder)"""
        # This would integrate with geocoding service (Google Maps, OpenStreetMap, etc.)
        logger.info(f"Reverse geocoding ({lat}, {lon})")
        return {
            'address': None,
            'governorate': None,
            'district': None
        }
    
    def _find_nearby_services(self, 
                             lat: float, 
                             lon: float, 
                             radius_km: float) -> List[str]:
        """Find nearby services within radius (placeholder)"""
        # This would query a database of service locations
        nearby = []
        
        for service_type, services in self.service_database.items():
            for service in services:
                distance = self.calculate_distance(lat, lon, service.latitude, service.longitude)
                if distance <= radius_km:
                    nearby.append(service_type.value)
        
        return list(set(nearby))
    
    def add_service_location(self, service: NearbyService):
        """Add a service location to the database"""
        if service.service_type not in self.service_database:
            self.service_database[service.service_type] = []
        
        self.service_database[service.service_type].append(service)
        logger.info(f"Added service {service.service_id} of type {service.service_type.value}")
    
    def get_location_summary(self, location: LocationData) -> Dict:
        """Get summary of location data"""
        return {
            'location_id': location.location_id,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'address': location.address,
            'governorate': location.governorate,
            'district': location.district,
            'radius': location.radius,
            'nearby_services_count': len(location.nearby_services)
        }
    
    def apply_location_constraint_to_query(self,
                                          constraint: LocationConstraint,
                                          query_params: Dict) -> Dict:
        """
        Apply location constraint to search query parameters
        
        Args:
            constraint: Location constraint to apply
            query_params: Current query parameters
            
        Returns:
            Updated query parameters
        """
        updated_params = query_params.copy()
        
        if constraint.governorate:
            updated_params['governorate'] = constraint.governorate
        
        if constraint.district:
            updated_params['district'] = constraint.district
        
        if constraint.radius_km and constraint.latitude and constraint.longitude:
            updated_params['geo_search'] = {
                'latitude': constraint.latitude,
                'longitude': constraint.longitude,
                'radius_km': constraint.radius_km
            }
        
        return updated_params


# Global instance
location_intelligence_system = LocationIntelligenceSystem()