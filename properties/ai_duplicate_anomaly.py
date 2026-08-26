"""
Duplicate and Anomaly Detection System
Detects duplicate listings and suspicious patterns
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies"""
    UNUSUAL_PRICE = "unusual_price"
    DATA_INCONSISTENCY = "data_inconsistency"
    REPEATED_IMAGES = "repeated_images"
    RAPID_PRICE_CHANGE = "rapid_price_change"
    MULTIPLE_SIMILAR_LISTINGS = "multiple_similar_listings"
    SUSPICIOUS_AGENT = "suspicious_agent"


@dataclass
class DuplicateDetection:
    """Result of duplicate detection"""
    listing_id: str
    duplicate_with: List[str]
    similarity_score: float
    detected_at: str
    status: str  # potential_confirmed, potential_suspected
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'listing_id': listing_id,
            'duplicate_with': self.duplicate_with,
            'similarity_score': self.similarity_score,
            'detected_at': self.detected_at,
            'status': self.status
        }


@dataclass
class AnomalyDetection:
    """Result of anomaly detection"""
    listing_id: str
    anomaly_type: AnomalyType
    confidence: float
    description: str
    severity: str  # low, medium, high
    detected_at: str
    requires_review: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'listing_id': self.listing_id,
            'anomaly_type': self.anomaly_type.value,
            'confidence': self.confidence,
            'description': self.description,
            'severity': self.severity,
            'detected_at': self.detected_at,
            'requires_review': self.requires_review
        }


class DuplicateAnomalyDetector:
    """
    Detects duplicate listings and suspicious patterns
    Flags potential issues for admin review without automatic action
    """
    
    def __init__(self):
        self.listing_hashes: Dict[str, str] = {}  # hash -> listing_id
        self.detection_history: List[Dict] = []
        self.price_history: Dict[str, List[float]] = {}  # listing_id -> price history
    
    def calculate_listing_hash(self, listing_data: Dict) -> str:
        """
        Calculate hash for listing to detect duplicates
        Based on title, price, area, location, images
        """
        # Create a normalized string representation
        hash_components = [
            str(listing_data.get('title', '')).lower().strip(),
            str(listing_data.get('price', 0)),
            str(listing_data.get('area', 0)),
            str(listing_data.get('governorate', '')).lower().strip(),
            str(listing_data.get('district', '')).lower().strip(),
            str(listing_data.get('property_type', '')).lower().strip(),
            str(listing_data.get('rooms', 0))
        ]
        
        hash_string = "|".join(hash_components)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def detect_duplicate_listing(self, listing_data: Dict) -> Optional[DuplicateDetection]:
        """
        Detect if listing is duplicate of existing listing
        
        Args:
            listing_data: Listing data to check
            
        Returns:
            DuplicateDetection result if duplicate found
        """
        try:
            listing_id = listing_data.get('id')
            if not listing_id:
                return None
            
            # Calculate hash
            listing_hash = self.calculate_listing_hash(listing_data)
            
            # Check for hash match
            existing_listing_id = self.listing_hashes.get(listing_hash)
            
            if existing_listing_id and existing_listing_id != listing_id:
                return DuplicateDetection(
                    listing_id=listing_id,
                    duplicate_with=[existing_listing_id],
                    similarity_score=1.0,
                    detected_at=datetime.now().isoformat(),
                    status="potential_confirmed"
                )
            
            # Store hash
            self.listing_hashes[listing_hash] = listing_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting duplicate listing: {str(e)}")
            return None
    
    def detect_image_duplicates(self, listing_id: str, image_hashes: List[str]) -> List[str]:
        """
        Detect if listing uses duplicate images
        
        Args:
            listing_id: Listing ID
            image_hashes: List of image hashes
            
        Returns:
            List of duplicate image hashes
        """
        duplicates = []
        seen_hashes = set()
        
        for image_hash in image_hashes:
            if image_hash in seen_hashes:
                duplicates.append(image_hash)
            seen_hashes.add(image_hash)
        
        if duplicates:
            logger.warning(f"Detected {len(duplicates)} duplicate images in listing {listing_id}")
        
        return duplicates
    
    def detect_price_anomaly(self, listing_data: Dict, comparable_listings: List[Dict]) -> Optional[AnomalyDetection]:
        """
        Detect if listing price is anomalous compared to similar listings
        
        Args:
            listing_data: Listing to check
            comparable_listings: Similar listings for comparison
            
        Returns:
            AnomalyDetection if anomaly found
        """
        try:
            listing_id = listing_data.get('id')
            price = listing_data.get('price', 0)
            
            if price == 0:
                return None
            
            if not comparable_listings:
                return None
            
            # Calculate statistics from comparable listings
            prices = [l.get('price', 0) for l in comparable_listings if l.get('price', 0) > 0]
            
            if not prices:
                return None
            
            import statistics
            median_price = statistics.median(prices)
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Check if price is significantly different
            if std_dev > 0:
                z_score = (price - median_price) / std_dev
                
                if abs(z_score) > 3:  # More than 3 standard deviations
                    return AnomalyDetection(
                        listing_id=listing_id,
                        anomaly_type=AnomalyType.UNUSUAL_PRICE,
                        confidence=min(abs(z_score) / 5, 1.0),
                        description=f"السعر يختلف {abs(z_score):.1f} انحراف معياري عن المتوسط للعقارات المشابهة",
                        severity="high" if abs(z_score) > 5 else "medium",
                        detected_at=datetime.now().isoformat(),
                        requires_review=True
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting price anomaly: {str(e)}")
            return None
    
    def detect_rapid_price_change(self, listing_id: str, old_price: float, new_price: float) -> Optional[AnomalyDetection]:
        """
        Detect if price change is unusually rapid
        
        Args:
            listing_id: Listing ID
            old_price: Previous price
            new_price: New price
            
        Returns:
            AnomalyDetection if change is anomalous
        """
        try:
            if old_price == 0 or new_price ==  DetectionResult:
                return None
            
            change_percentage = abs(new_price - old_price) / old_price
            
            # More than 50% change is unusual
            if change_percentage > 0.5:
                return AnomalyDetection(
                    listing_id=listing_id,
                    anomaly_type=AnomalyType.RAPID_PRICE_CHANGE,
                    confidence=min(change_percentage, 1.0),
                    description=f"تغيير سعر غير معتاد: {change_percentage:.0%}",
                    severity="high" if change_percentage > 0.8 else "medium",
                    detected_at=datetime.now().isoformat(),
                    requires_review=True
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting rapid price change: {str(e)}")
            return None
    
    def detect_data_inconsistency(self, listing_data: Dict) -> Optional[AnomalyDetection]:
        """
        Detect data inconsistencies in listing
        
        Args:
            listing_data: Listing data to check
            
        Returns:
            AnomalyDetection if inconsistency found
        """
        try:
            listing_id = listing_data.get('id')
            inconsistencies = []
            
            # Check if price is unrealistically low
            price = listing_data.get('price', 0)
            area = listing_data.get('area', 0)
            
            if price > 0 and area > 0:
                price_per_m2 = price / area
                # Less than 100,000 IQD per m2 is suspicious for residential
                if price_per_m2 < 100000:
                    inconsistencies.append("السعر لكل متر مربع منخفض بشكل غير معتاد")
            
            # Check if rooms/area ratio is unusual
            rooms = listing_data.get('rooms', 0)
            if area > 0 and rooms > 0:
                area_per_room = area / rooms
                # Less than 10 m2 per room is suspicious
                if area_per_room < 10:
                    inconsistencies.append("نسبة الغرف إلى المساحة غير معتادة")
            
            if inconsistencies:
                return AnomalyDetection(
                    listing_id=listing_id,
                    anomaly_type=AnomalyType.DATA_INCONSISTENCY,
                    confidence=0.7,
                    description="؛ ".join(inconsistencies),
                    severity="medium",
                    detected_at=datetime.now().isoformat(),
                    requires_review=True
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting data inconsistency: {str(e)}")
            return None
    
    def get_detection_summary(self) -> Dict:
        """Get summary of detections"""
        duplicate_count = sum(1 for d in self.detection_history if d.get('type') == 'duplicate')
        anomaly_count = sum(1 for d in self.detection_history if d.get('type') == 'anomaly')
        
        return {
            'total_detections': len(self.detection_history),
            'duplicate_detections': duplicate_count,
            'anomaly_detections': anomaly_count,
            'unique_listings_hashed': len(self.listing_hashes)
        }


# Global instance
duplicate_anomaly_detector = DuplicateAnomalyDetector()