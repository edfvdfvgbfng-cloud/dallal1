"""
Property Image Analysis System
Analyzes property images with safety and grounding in actual data
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict

from .ai_multimodal_input import ImageData, ImageCategory

logger = logging.getLogger(__name__)


class ImageElement(Enum):
    """Elements that can be detected in property images"""
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    ROOM = "room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    GARDEN = "garden"
    PARKING = "parking"
    POOL = "pool"
    BALCONY = "balcony"
    WINDOW = "window"
    DOOR = "door"
    FLOOR = "floor"
    CEILING = "ceiling"
    WALL = "wall"
    FURNITURE = "furniture"
    APPLIANCE = "appliance"
    LIGHTING = "lighting"
    UNKNOWN = "unknown"


class VisibilityLevel(Enum):
    """Confidence in what is visible in image"""
    VISIBLE = "visible"  # Clearly visible
    LIKELY = "likely"  # Probably visible
    INFERRED = "inferred"  # Inferred from context
    UNKNOWN = "unknown"  # Cannot determine


@dataclass
class ImageObservation:
    """Represents an observation from image analysis"""
    element: ImageElement
    visibility: VisibilityLevel
    confidence: float
    description: str
    region: Dict = None  # Bounding box or region in image
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'element': self.element.value,
            'visibility': self.visibility.value,
            'confidence': self.confidence,
            'description': self.description,
            'region': self.region,
            'metadata': self.metadata
        }


@dataclass
class ImageQuality:
    """Quality assessment of an image"""
    clarity_score: float  # 0-1
    lighting_score: float  # 0-1
    composition_score: float  # 0-1
    overall_quality: float  # 0-1
    issues: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'clarity_score': self.clarity_score,
            'lighting_score': self.lighting_score,
            'composition_score': self.composition_score,
            'overall_quality': self.overall_quality,
            'issues': self.issues
        }


class PropertyImageAnalyzer:
    """
    Analyzes property images with strict grounding in visible data
    Only reports what is actually visible or can be safely inferred
    """
    
    def __init__(self):
        self.analysis_history: List[Dict] = []
    
    def analyze_property_image(self, 
                              image: ImageData,
                              property_data: Dict = None) -> Tuple[List[ImageObservation], ImageQuality]:
        """
        Analyze a property image
        
        Args:
            image: Image data to analyze
            property_data: Optional property data from database for grounding
            
        Returns:
            Tuple of (observations, quality)
        """
        try:
            # Analyze image quality
            quality = self._assess_image_quality(image)
            
            # Extract observations (what is visible)
            observations = self._extract_observations(image)
            
            # Ground observations in property data if available
            if property_data:
                observations = self._ground_observations(observations, property_data)
            
            # Log analysis
            self.analysis_history.append({
                'timestamp': self._get_timestamp(),
                'image_id': image.image_id,
                'observation_count': len(observations),
                'quality_score': quality.overall_quality
            })
            
            logger.info(f"Analyzed image {image.image_id}: {len(observations)} observations")
            return observations, quality
            
        except Exception as e:
            logger.error(f"Error analyzing image {image.image_id}: {str(e)}")
            return [], ImageQuality(0.5, 0.5, 0.5, 0.5, [str(e)])
    
    def _assess_image_quality(self, image: ImageData) -> ImageQuality:
        """Assess quality of an image"""
        issues = []
        
        # Placeholder quality assessment
        # In production, this would use actual image analysis
        clarity_score = 0.7
        lighting_score = 0.6
        composition_score = 0.7
        
        # Check for common issues
        if image.width and image.width < 800:
            issues.append("Low resolution")
            clarity_score -= 0.2
        
        if not issues:
            issues.append("No issues detected")
        
        overall_quality = (clarity_score + lighting_score + composition_score) / 3
        
        return ImageQuality(
            clarity_score=clarity_score,
            lighting_score=lighting_score,
            composition_score=composition_score,
            overall_quality=overall_quality,
            issues=issues
        )
    
    def _extract_observations(self, image: ImageData) -> List[ImageObservation]:
        """
        Extract observations from image
        Only report what is actually visible with confidence
        """
        observations = []
        
        # Placeholder observation extraction
        # In production, this would use computer vision models
        
        # For now, create minimal observations based on metadata
        if image.related_property_id:
            observations.append(ImageObservation(
                element=ImageElement.EXTERIOR,
                visibility=VisibilityLevel.LIKELY,
                confidence=0.6,
                description="Property exterior visible",
                metadata={'source': 'property_relation'}
            ))
        
        return observations
    
    def _ground_observations(self, 
                            observations: List[ImageObservation],
                            property_data: Dict) -> List[ImageObservation]:
        """
        Ground image observations in actual property data
        Only keep observations that are consistent with database
        """
        grounded_observations = []
        
        # Check each observation against property data
        for obs in observations:
            if self._is_observation_supported(obs, property_data):
                # Mark as visible with higher confidence
                obs.visibility = VisibilityLevel.VISIBLE
                obs.confidence = min(obs.confidence + 0.2, 1.0)
                obs.metadata['grounded'] = True
                obs.metadata['database_source'] = True
                grounded_observations.append(obs)
            else:
                # If not supported, downgrade confidence
                obs.visibility = VisibilityLevel.INFERRED
                obs.confidence = max(obs.confidence - 0.3, 0.1)
                obs.metadata['grounded'] = False
                grounded_observations.append(obs)
        
        return grounded_observations
    
    def _is_observation_supported(self, observation: ImageObservation, property_data: Dict) -> bool:
        """Check if observation is supported by property data"""
        # Map observations to property data fields
        element_to_field = {
            ImageElement.GARDEN: 'has_garden',
            ImageElement.PARKING: 'has_parking',
            ImageElement.POOL: 'has_pool',
            ImageElement.BALCONY: 'has_balcony'
        }
        
        field = element_to_field.get(observation.element)
        if field and field in property_data:
            return property_data[field] == True
        
        # For other elements, if not in database, don't assume
        return False
    
    def categorize_image(self, image: ImageData) -> ImageCategory:
        """
        Categorize image type
        Only assign category with high confidence
        """
        # Placeholder categorization
        # In production, this would use classification model
        
        # Use existing category if set
        if image.category != ImageCategory.UNCLASSIFIED:
            return image.category
        
        # Default to unclassified if uncertain
        return ImageCategory.UNCLASSIFIED
    
    def suggest_main_image(self, images: List[ImageData]) -> Optional[ImageData]:
        """
        Suggest the best main image from a set
        Based on quality, clarity, and content
        """
        if not images:
            return None
        
        # Analyze all images
        analyzed_images = []
        for image in images:
            observations, quality = self.analyze_property_image(image)
            analyzed_images.append({
                'image': image,
                'quality': quality,
                'observations': observations
            })
        
        # Sort by overall quality
        analyzed_images.sort(key=lambda x: x['quality'].overall_quality, reverse=True)
        
        # Return best image
        return analyzed_images[0]['image']
    
    def detect_duplicates(self, images: List[ImageData]) -> List[Tuple[ImageData, ImageData, float]]:
        """
        Detect duplicate or very similar images
        Returns list of (image1, image2, similarity_score)
        """
        duplicates = []
        
        # Placeholder duplicate detection
        # In production, this would use perceptual hashing or similarity detection
        
        # Simple check: same filename or size
        for i, img1 in enumerate(images):
            for j, img2 in enumerate(images[i+1:], i+1):
                similarity = 0.0
                
                # Check filename similarity
                if img1.filename and img2.filename:
                    if img1.filename == img2.filename:
                        similarity = 1.0
                
                # Check size similarity
                if len(img1.data) == len(img2.data):
                    similarity = max(similarity, 0.9)
                
                if similarity > 0.8:
                    duplicates.append((img1, img2, similarity))
        
        return duplicates
    
    def compare_images(self, 
                      query_image: ImageData,
                      database_images: List[ImageData]) -> List[Tuple[ImageData, float]]:
        """
        Compare query image against database images
        Returns list of (image, similarity_score) sorted by similarity
        """
        similarities = []
        
        # Placeholder similarity comparison
        # In production, this would use embedding-based similarity
        
        for db_image in database_images:
            # Simple similarity based on metadata
            similarity = 0.0
            
            # Same category
            if query_image.category == db_image.category:
                similarity += 0.3
            
            # Same property
            if query_image.related_property_id == db_image.related_property_id:
                similarity += 0.5
            
            similarities.append((db_image, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    def explain_observations(self, observations: List[ImageObservation]) -> str:
        """Generate human-readable explanation of observations"""
        if not observations:
            return "لم أتمكن من تحديد عناصر واضحة في الصورة."
        
        visible = [obs for obs in observations if obs.visibility == VisibilityLevel.VISIBLE]
        likely = [obs for obs in observations if obs.visibility == VisibilityLevel.LIKELY]
        
        explanation_parts = []
        
        if visible:
            visible_descriptions = [obs.description for obs in visible]
            explanation_parts.append(f"تظهر بوضوح: {', '.join(visible_descriptions)}")
        
        if likely:
            likely_descriptions = [obs.description for obs in likely]
            explanation_parts.append(f"يبدو أنها تظهر: {', '.join(likely_descriptions)}")
        
        if not explanation_parts:
            return "الصورة غير واضحة بما يكفي لتحديد العناصر."
        
        return " ".join(explanation_parts)
    
    def get_image_summary(self, image: ImageData, observations: List[ImageObservation]) -> Dict:
        """Get summary of image analysis"""
        visible_count = sum(1 for obs in observations if obs.visibility == VisibilityLevel.VISIBLE)
        likely_count = sum(1 for obs in observations if obs.visibility == VisibilityLevel.LIKELY)
        
        return {
            'image_id': image.image_id,
            'category': image.category.value,
            'total_observations': len(observations),
            'visible_count': visible_count,
            'likely_count': likely_count,
            'confidence_range': (
                min(obs.confidence for obs in observations) if observations else 0,
                max(obs.confidence for obs in observations) if observations else 0
            )
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global instance
property_image_analyzer = PropertyImageAnalyzer()