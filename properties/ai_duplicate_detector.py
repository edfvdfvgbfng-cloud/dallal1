"""
Advanced Duplicate Detection System
Detects duplicate images and suspicious listings
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict
import hashlib
from PIL import Image
import io

logger = logging.getLogger(__name__)


class DuplicateType(Enum):
    """Types of duplicates"""
    EXACT_MATCH = "exact_match"  # Identical images
    NEAR_DUPLICATE = "near_duplicate"  # Very similar images
    VISUALLY_SIMILAR = "visually_similar"  # Similar content
    SUSPICIOUS_PATTERN = "suspicious_pattern"  # Suspicious posting pattern


class SuspicionLevel(Enum):
    """Level of suspicion for a listing"""
    CLEAN = "clean"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DuplicateFinding:
    """Represents a duplicate finding"""
    property_id: int
    duplicate_property_id: int
    duplicate_type: DuplicateType
    similarity_score: float
    evidence: List[str]
    metadata: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'property_id': self.property_id,
            'duplicate_property_id': self.duplicate_property_id,
            'duplicate_type': self.duplicate_type.value,
            'similarity_score': self.similarity_score,
            'evidence': self.evidence,
            'metadata': self.metadata
        }


@dataclass
class SuspiciousListing:
    """Represents a suspicious listing"""
    property_id: int
    suspicion_level: SuspicionLevel
    reasons: List[str]
    confidence: float
    metadata: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'property_id': self.property_id,
            'suspicion_level': self.suspicion_level.value,
            'reasons': self.reasons,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


class DuplicateDetector:
    """
    Advanced duplicate detection system
    Detects duplicate images and suspicious patterns
    """

    def __init__(self):
        self.image_hashes = {}  # Store image hashes
        self.property_patterns = defaultdict(list)  # Track posting patterns
        self.detection_history = []

    def calculate_image_hash(self, image_data: bytes) -> str:
        """
        Calculate perceptual hash of image

        Args:
            image_data: Image bytes

        Returns:
            Hash string
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Resize to standard size for hash calculation
            image = image.resize((8, 8), Image.LANCZOS)

            # Convert to grayscale
            image = image.convert('L')

            # Calculate average hash
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)

            # Generate hash
            hash_string = ""
            for pixel in pixels:
                hash_string += "1" if pixel > avg else "0"

            return hash_string

        except Exception as e:
            logger.error(f"Error calculating image hash: {e}")
            return ""

    def detect_duplicate_images(self, property_images: List[Tuple[int, bytes]]) -> List[DuplicateFinding]:
        """
        Detect duplicate images across properties

        Args:
            property_images: List of (property_id, image_data) tuples

        Returns:
            List of duplicate findings
        """
        findings = []

        # Calculate hashes for all images
        hashes = {}
        for property_id, image_data in property_images:
            hash_value = self.calculate_image_hash(image_data)
            if hash_value:
                if hash_value not in hashes:
                    hashes[hash_value] = []
                hashes[hash_value].append(property_id)

        # Find duplicates
        for hash_value, property_ids in hashes.items():
            if len(property_ids) > 1:
                # These properties have identical images
                for i in range(len(property_ids)):
                    for j in range(i + 1, len(property_ids)):
                        finding = DuplicateFinding(
                            property_id=property_ids[i],
                            duplicate_property_id=property_ids[j],
                            duplicate_type=DuplicateType.EXACT_MATCH,
                            similarity_score=1.0,
                            evidence=["صور متطابقة تماماً"],
                            metadata={'hash': hash_value}
                        )
                        findings.append(finding)

        return findings

    def detect_near_duplicates(self, property_images: List[Tuple[int, bytes]], threshold: float = 0.9) -> List[DuplicateFinding]:
        """
        Detect near-duplicate images

        Args:
            property_images: List of (property_id, image_data) tuples
            threshold: Similarity threshold

        Returns:
            List of near-duplicate findings
        """
        findings = []

        # This is a simplified version - in production, use specialized libraries like:
        # - imagehash library for perceptual hashing
        # - OpenCV for feature matching
        # - specialized duplicate detection services

        # For now, we'll use exact hash detection as a proxy
        exact_duplicates = self.detect_duplicate_images(property_images)

        # Mark as near-duplicates with slightly lower score
        for duplicate in exact_duplicates:
            near_duplicate = DuplicateFinding(
                property_id=duplicate.property_id,
                duplicate_property_id=duplicate.duplicate_property_id,
                duplicate_type=DuplicateType.NEAR_DUPLICATE,
                similarity_score=0.95,
                evidence=["صور متشابهة جداً"],
                metadata=duplicate.metadata
            )
            findings.append(near_duplicate)

        return findings

    def detect_suspicious_patterns(self, property_data: List[Dict]) -> List[SuspiciousListing]:
        """
        Detect suspicious posting patterns

        Args:
            property_data: List of property data dictionaries

        Returns:
            List of suspicious listings
        """
        suspicious_listings = []

        for prop in property_data:
            reasons = []
            suspicion_level = SuspicionLevel.CLEAN
            confidence = 0.0

            # Check for suspicious price patterns
            if self._is_suspicious_price(prop):
                reasons.append("سعر مشبوه")
                suspicion_level = SuspicionLevel.MEDIUM
                confidence += 0.3

            # Check for suspicious description patterns
            if self._is_suspicious_description(prop):
                reasons.append("وصف مشبوه")
                suspicion_level = SuspicionLevel.MEDIUM
                confidence += 0.2

            # Check for suspicious posting frequency
            if self._is_suspicious_frequency(prop):
                reasons.append("تكرار نشر مشبوه")
                suspicion_level = SuspicionLevel.HIGH
                confidence += 0.4

            # Check for missing required information
            if self._is_missing_required_info(prop):
                reasons.append("معلومات ناقصة")
                suspicion_level = SuspicionLevel.LOW
                confidence += 0.1

            # Check for suspicious contact information
            if self._is_suspicious_contact(prop):
                reasons.append("معلومات اتصال مشبوهة")
                suspicion_level = SuspicionLevel.HIGH
                confidence += 0.5

            # Update suspicion level based on confidence
            if confidence >= 0.8:
                suspicion_level = SuspicionLevel.CRITICAL
            elif confidence >= 0.6:
                suspicion_level = SuspicionLevel.HIGH
            elif confidence >= 0.4:
                suspicion_level = SuspicionLevel.MEDIUM
            elif confidence >= 0.2:
                suspicion_level = SuspicionLevel.LOW

            if reasons:
                suspicious_listing = SuspiciousListing(
                    property_id=prop.get('id'),
                    suspicion_level=suspicion_level,
                    reasons=reasons,
                    confidence=min(confidence, 1.0),
                    metadata={'property_data': prop}
                )
                suspicious_listings.append(suspicious_listing)

        return suspicious_listings

    def _is_suspicious_price(self, property_data: Dict) -> bool:
        """Check if price is suspicious"""
        price = property_data.get('price')
        if not price:
            return False

        # Check for unrealistically low prices
        if price < 1000000:  # Less than 1 million IQD
            return True

        # Check for round numbers (often fake)
        if price in [100000000, 200000000, 500000000, 1000000000]:
            return True

        return False

    def _is_suspicious_description(self, property_data: Dict) -> bool:
        """Check if description is suspicious"""
        description = property_data.get('description', '')
        if not description:
            return True  # No description is suspicious

        # Check for very short descriptions
        if len(description) < 50:
            return True

        # Check for generic/repetitive text
        generic_phrases = ['عقار ممتاز', 'فرصة ذهبية', 'استثمار ممتاز']
        for phrase in generic_phrases:
            if phrase in description:
                return True

        return False

    def _is_suspicious_frequency(self, property_data: Dict) -> bool:
        """Check if posting frequency is suspicious"""
        # This would require tracking posting history
        # For now, return False
        return False

    def _is_missing_required_info(self, property_data: Dict) -> bool:
        """Check if required information is missing"""
        required_fields = ['title', 'price', 'location', 'contact']
        for field in required_fields:
            if not property_data.get(field):
                return True
        return False

    def _is_suspicious_contact(self, property_data: Dict) -> bool:
        """Check if contact information is suspicious"""
        contact = property_data.get('contact', '')
        if not contact:
            return True

        # Check for international numbers for local properties
        if contact.startswith('+') and len(contact) > 15:
            return True

        return False

    def analyze_property_images(self, property_id: int, images: List[bytes]) -> Dict[str, Any]:
        """
        Analyze property images for quality and authenticity

        Args:
            property_id: Property ID
            images: List of image bytes

        Returns:
            Analysis results
        """
        analysis = {
            'property_id': property_id,
            'total_images': len(images),
            'image_quality': [],
            'duplicate_detected': False,
            'suspicious_patterns': [],
            'overall_score': 0.0
        }

        if not images:
            analysis['suspicious_patterns'].append('لا توجد صور')
            return analysis

        # Analyze each image
        for i, image_data in enumerate(images):
            try:
                image = Image.open(io.BytesIO(image_data))

                # Check image quality
                quality_score = self._assess_image_quality(image)
                analysis['image_quality'].append({
                    'image_index': i,
                    'quality_score': quality_score,
                    'dimensions': image.size,
                    'format': image.format
                })

            except Exception as e:
                logger.error(f"Error analyzing image {i}: {e}")
                analysis['suspicious_patterns'].append(f'خطأ في تحليل الصورة {i}')

        # Check for duplicates within the same property
        if len(images) > 1:
            hashes = [self.calculate_image_hash(img) for img in images]
            if len(set(hashes)) < len(hashes):
                analysis['duplicate_detected'] = True
                analysis['suspicious_patterns'].append('صور مكررة في نفس الإعلان')

        # Calculate overall score
        if analysis['image_quality']:
            avg_quality = sum(img['quality_score'] for img in analysis['image_quality']) / len(analysis['image_quality'])
            analysis['overall_score'] = avg_quality

            if analysis['duplicate_detected']:
                analysis['overall_score'] -= 0.3

            if analysis['suspicious_patterns']:
                analysis['overall_score'] -= 0.2 * len(analysis['suspicious_patterns'])

        return analysis

    def _assess_image_quality(self, image: Image.Image) -> float:
        """
        Assess image quality

        Args:
            image: PIL Image object

        Returns:
            Quality score (0-1)
        """
        score = 1.0

        # Check resolution
        width, height = image.size
        if width < 300 or height < 300:
            score -= 0.3

        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            score -= 0.2

        # Check if image is too small
        if width * height < 100000:  # Less than 100k pixels
            score -= 0.4

        return max(0.0, score)

    def generate_duplicate_report(self, findings: List[DuplicateFinding]) -> Dict[str, Any]:
        """
        Generate comprehensive duplicate report

        Args:
            findings: List of duplicate findings

        Returns:
            Report dictionary
        """
        report = {
            'total_findings': len(findings),
            'by_type': defaultdict(int),
            'severity_distribution': defaultdict(int),
            'affected_properties': set(),
            'recommendations': []
        }

        for finding in findings:
            report['by_type'][finding.duplicate_type.value] += 1
            report['affected_properties'].add(finding.property_id)
            report['affected_properties'].add(finding.duplicate_property_id)

            if finding.similarity_score >= 0.95:
                report['severity_distribution']['critical'] += 1
            elif finding.similarity_score >= 0.8:
                report['severity_distribution']['high'] += 1
            elif finding.similarity_score >= 0.6:
                report['severity_distribution']['medium'] += 1
            else:
                report['severity_distribution']['low'] += 1

        # Generate recommendations
        if report['total_findings'] > 0:
            report['recommendations'].append('مراجعة الإعلانات المشبوهة')
            report['recommendations'].append('تحقق من ملكية الصور')
            report['recommendations'].append('طلب تأكيد إضافي من المعلن')

        return {
            'summary': {
                'total_findings': report['total_findings'],
                'affected_properties': len(report['affected_properties']),
                'severity_distribution': dict(report['severity_distribution'])
            },
            'detailed_findings': [f.to_dict() for f in findings],
            'recommendations': report['recommendations']
        }


# Global instance
duplicate_detector = DuplicateDetector()
