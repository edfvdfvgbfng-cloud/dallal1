"""
Contradiction Detector
Detects conflicting information from different sources
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts"""
    PRICE_CONFLICT = "price_conflict"
    LOCATION_CONFLICT = "location_conflict"
    AREA_CONFLICT = "area_conflict"
    STATUS_CONFLICT = "status_conflict"
    DATE_CONFLICT = "date_conflict"
    IDENTITY_CONFLICT = "identity_conflict"
    VALUE_CONFLICT = "value_conflict"


class SourceType(Enum):
    """Types of information sources"""
    VERIFIED_DATABASE = "verified_database"
    OFFICIAL_API = "official_api"
    USER_INPUT = "user_input"
    UPLOADED_DOCUMENT = "uploaded_document"
    AI_INFERENCE = "ai_inference"
    AGENT_OUTPUT = "agent_output"


@dataclass
class ConflictDetection:
    """Result of conflict detection"""
    conflict_type: ConflictType = None
    source1: SourceType = None
    source2: SourceType = None
    value1: Any = None
    value2: Any = None
    confidence: float = 0.0
    severity: str = "medium"  # low, medium, high
    detected_at: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'conflict_type': self.conflict_type.value,
            'source1': self.source1.value,
            'source2': self.source2.value,
            'value1': self.value1,
            'value2': self.value2,
            'confidence': self.confidence,
            'severity': self.severity,
            'detected_at': self.detected_at
        }


class ContradictionDetector:
    """
    Detects conflicting information from different sources
    Prevents AI from making decisions based on contradictory data
    """
    
    def __init__(self):
        self.source_priority = self._initialize_source_priority()
        self.conflict_history: List[Dict] = []
    
    def _initialize_source_priority(self) -> Dict[SourceType, int]:
        """Initialize source priority (lower = higher priority)"""
        return {
            SourceType.VERIFIED_DATABASE: 1,
            SourceType.OFFICIAL_API: 2,
            SourceType.USER_INPUT: 3,
            SourceType.UPLOADED_DOCUMENT: 4,
            SourceType.AGENT_OUTPUT: 5,
            SourceType.AI_INFERENCE: 6
        }
    
    def detect_conflicts(self, data_sources: Dict[SourceType, Dict]) -> List[ConflictDetection]:
        """
        Detect conflicts between data sources
        
        Args:
            data_sources: Dictionary of source type to data
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check each pair of sources
        source_list = list(data_sources.items())
        
        for i in range(len(source_list)):
            for j in range(i + 1, len(source_list)):
                source1_type, source1_data = source_list[i]
                source2_type, source2_data = source_list[j]
                
                # Check for conflicts
                pair_conflicts = self._compare_sources(
                    source1_type, source1_data,
                    source2_type, source2_data
                )
                
                conflicts.extend(pair_conflicts)
        
        # Log conflicts
        for conflict in conflicts:
            self.conflict_history.append({
                'timestamp': datetime.now().isoformat(),
                'conflict_type': conflict.conflict_type.value,
                'source1': conflict.source1.value,
                'source2': conflict.source2.value
            })
        
        return conflicts
    
    def _compare_sources(self,
                       source1_type: SourceType,
                       source1_data: Dict,
                       source2_type: SourceType,
                       source2_data: Dict) -> List[ConflictDetection]:
        """Compare two data sources for conflicts"""
        conflicts = []
        
        # Check price conflict
        if 'price' in source1_data and 'price' in source2_data:
            if source1_data['price'] != source2_data['price']:
                # Calculate difference percentage
                price1 = source1_data['price']
                price2 = source2_data['price']
                diff = abs(price1 - price2)
                diff_percentage = diff / max(price1, price2) if max(price1, price2) > 0 else 0
                
                if diff_percentage > 0.1:  # More than 10% difference
                    severity = "high" if diff_percentage > 0.5 else "medium"
                    conflicts.append(ConflictDetection(
                        conflict_type=ConflictType.PRICE_CONFLICT,
                        source1=source1_type,
                        source2=source2_type,
                        value1=price1,
                        value2=price2,
                        confidence=diff_percentage,
                        severity=severity,
                        detected_at=datetime.now().isoformat()
                    ))
        
        # Check location conflict
        if 'governorate' in source1_data and 'governorate' in source2_data:
            if source1_data['governorate'] != source2_data['governorate']:
                conflicts.append(ConflictDetection(
                    conflict_type=ConflictType.LOCATION_CONFLICT,
                    source1=source1_type,
                    source2=source2_type,
                    value1=source1_data['governorate'],
                    value2=source2_data['governorate'],
                    confidence=1.0,
                    severity="high",
                    detected_at=datetime.now().isoformat()
                ))
        
        # Check area conflict
        if 'area' in source1_data and 'area' in source2_data:
            if source1_data['area'] != source2_data['area']:
                area1 = source1_data['area']
                area2 = source2_data['area']
                diff = abs(area1 - area2)
                diff_percentage = diff / max(area1, area2) if max(area1, area2) > 0 else 0
                
                if diff_percentage > 0.2:  # More than 20% difference
                    conflicts.append(ConflictDetection(
                        conflict_type=ConflictType.AREA_CONFLICT,
                        source1=source1_type,
                        source2=source2_type,
                        value1=area1,
                        value2=area2,
                        confidence=diff_percentage,
                        severity="medium",
                        detected_at=datetime.now().isoformat()
                    ))
        
        # Check status conflict
        if 'status' in source1_data and 'status' in source2_data:
            if source1_data['status'] != source2_data['status']:
                conflicts.append(ConflictDetection(
                    conflict_type=ConflictType.STATUS_CONFLICT,
                    source1=source1_type,
                    source2=source2_type,
                    value1=source1_data['status'],
                    value2=source2_data['status'],
                    confidence=1.0,
                    severity="high",
                    detected_at=datetime.now().isoformat()
                ))
        
        return conflicts
    
    def resolve_conflict(self, conflicts: List[ConflictDetection]) -> Dict:
        """
        Resolve conflicts based on source priority
        
        Args:
            conflicts: List of detected conflicts
            
        Returns:
            Resolution with preferred values
        """
        resolution = {}
        
        for conflict in conflicts:
            # Get source priorities
            priority1 = self.source_priority.get(conflict.source1, 999)
            priority2 = self.source_priority.get(conflict.source2, 999)
            
            # Choose value from higher priority source (lower number)
            if priority1 < priority2:
                preferred_source = conflict.source1
                preferred_value = conflict.value1
            else:
                preferred_source = conflict.source2
                preferred_value = conflict.value2
            
            resolution[conflict.conflict_type.value] = {
                'preferred_value': preferred_value,
                'preferred_source': preferred_source.value,
                'confidence': conflict.confidence
            }
        
        return resolution
    
    def check_single_field_conflict(self,
                                  field_name: str,
                                  value1: Any,
                                  source1: SourceType,
                                  value2: Any,
                                  source2: SourceType) -> Optional[ConflictDetection]:
        """
        Check if a single field has conflicting values
        
        Args:
            field_name: Name of the field
            value1: First value
            source1: First source
            value2: Second value
            source2: Second source
            
        Returns:
            ConflictDetection if conflict found, None otherwise
        """
        if value1 == value2:
            return None
        
        # Determine conflict type based on field
        conflict_type_map = {
            'price': ConflictType.PRICE_CONFLICT,
            'governorate': ConflictType.LOCATION_CONFLICT,
            'district': ConflictType.LOCATION_CONFLICT,
            'area': ConflictType.AREA_CONFLICT,
            'status': ConflictType.STATUS_CONFLICT
        }
        
        conflict_type = conflict_type_map.get(field_name, ConflictType.VALUE_CONFLICT)
        
        # Calculate severity
        priority1 = self.source_priority.get(source1, 999)
        priority2 = self.source_priority.get(source2, 999)
        
        severity = "medium"
        if conflict_type in [ConflictType.PRICE_CONFLICT, ConflictType.STATUS_CONFLICT]:
            severity = "high"
        
        return ConflictDetection(
            conflict_type=conflict_type,
            source1=source1,
            source2=source2,
            value1=value1,
            value2=value2,
            confidence=1.0,
            severity=severity,
            detected_at=datetime.now().isoformat()
        )
    
    def has_critical_conflicts(self, conflicts: List[ConflictDetection]) -> bool:
        """Check if there are any critical (high severity) conflicts"""
        return any(c.severity == "high" for c in conflicts)
    
    def get_conflict_statistics(self) -> Dict:
        """Get conflict detection statistics"""
        type_counts = {}
        severity_counts = {}
        
        for conflict in self.conflict_history:
            c_type = conflict['conflict_type']
            type_counts[c_type] = type_counts.get(c_type, 0) + 1
        
        # Would need severity in history for severity counts
        return {
            'total_conflicts': len(self.conflict_history),
            'type_distribution': type_counts,
            'source_priority': {k.value: v for k, v in self.source_priority.items()}
        }


# Global instance
contradiction_detector = ContradictionDetector()