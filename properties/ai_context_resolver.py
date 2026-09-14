"""
Context Resolver for References
Resolves references like "this", "that", "first", "second", "previous" in conversation
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class ReferenceType(Enum):
    """Types of references in conversation"""
    DEMONSTRATIVE = "demonstrative"  # this, that
    ORDINAL = "ordinal"  # first, second, third
    QUANTITATIVE = "quantitative"  # one, two, three
    RELATIVE = "relative"  # previous, next, same
    COMPARATIVE = "comparative"  # better, worse, best
    INDEFINITE = "indefinite"  # something, anything


class Reference:
    """Represents a reference in conversation"""
    
    def __init__(self,
                 reference_type: ReferenceType,
                 reference_text: str,
                 resolved_value: Any = None,
                 confidence: float = 0.0,
                 context_source: str = None):
        self.reference_type = reference_type
        self.reference_text = reference_text
        self.resolved_value = resolved_value
        self.confidence = confidence
        self.context_source = context_source
        self.resolution_timestamp = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'reference_type': self.reference_type.value,
            'reference_text': self.reference_text,
            'resolved_value': self.resolved_value,
            'confidence': self.confidence,
            'context_source': self.context_source,
            'resolution_timestamp': self.resolution_timestamp
        }


class ContextResolver:
    """
    Advanced context resolver for understanding references in conversation
    """
    
    def __init__(self):
        self.reference_patterns = self._initialize_reference_patterns()
        self.conversation_history: List[Dict] = []
        self.entity_history: Dict[str, List[Any]] = defaultdict(list)
        self.reference_cache: Dict[str, Reference] = {}
    
    def resolve_reference(self, 
                        reference_text: str, 
                        conversation_context: Dict) -> Optional[Reference]:
        """
        Resolve a reference to its actual value
        
        Args:
            reference_text: The reference text (e.g., "this", "first", "previous")
            conversation_context: Current conversation context
            
        Returns:
            Resolved Reference object
        """
        try:
            # Check cache first
            cache_key = f"{reference_text}_{conversation_context.get('conversation_id', 'default')}"
            if cache_key in self.reference_cache:
                return self.reference_cache[cache_key]
            
            # Determine reference type
            reference_type = self._classify_reference(reference_text)
            
            # Resolve based on type
            if reference_type == ReferenceType.DEMONSTRATIVE:
                resolved = self._resolve_demonstrative(reference_text, conversation_context)
            elif reference_type == ReferenceType.ORDINAL:
                resolved = self._resolve_ordinal(reference_text, conversation_context)
            elif reference_type == ReferenceType.QUANTITATIVE:
                resolved = self._resolve_quantitative(reference_text, conversation_context)
            elif reference_type == ReferenceType.RELATIVE:
                resolved = self._resolve_relative(reference_text, conversation_context)
            elif reference_type == ReferenceType.COMPARATIVE:
                resolved = self._resolve_comparative(reference_text, conversation_context)
            else:
                resolved = self._resolve_indefinite(reference_text, conversation_context)
            
            if resolved:
                # Cache the resolution
                self.reference_cache[cache_key] = resolved
                resolved.resolution_timestamp = self._get_timestamp()
                
                logger.info(f"Resolved reference '{reference_text}' to {resolved.resolved_value}")
            
            return resolved
            
        except Exception as e:
            logger.error(f"Error resolving reference '{reference_text}': {str(e)}")
            return None
    
    def _classify_reference(self, reference_text: str) -> ReferenceType:
        """Classify the type of reference"""
        reference_text = reference_text.strip().lower()
        
        # Demonstrative references
        demonstrative_patterns = [
            r'هذا|هاذا|هذه|هاذه|ذاك|تلك',
            r'this|that|these|those'
        ]
        for pattern in demonstrative_patterns:
            if re.search(pattern, reference_text, re.IGNORECASE):
                return ReferenceType.DEMONSTRATIVE
        
        # Ordinal references
        ordinal_patterns = [
            r'الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر',
            r'first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth'
        ]
        for pattern in ordinal_patterns:
            if re.search(pattern, reference_text, re.IGNORECASE):
                return ReferenceType.ORDINAL
        
        # Quantitative references
        quantitative_patterns = [
            r'واحد|اثنين|ثلاثة|أربعة|خمسة|واحدة|اثنتان|ثلاث|أربع|خمس',
            r'one|two|three|four|five'
        ]
        for pattern in quantitative_patterns:
            if re.search(pattern, reference_text, re.IGNORECASE):
                return ReferenceType.QUANTITATIVE
        
        # Relative references
        relative_patterns = [
            r'السابق|التالي|السابق|القادم|الماضي|الحالي',
            r'previous|next|past|current|last'
        ]
        for pattern in relative_patterns:
            if re.search(pattern, reference_text, re.IGNORECASE):
                return ReferenceType.RELATIVE
        
        # Comparative references
        comparative_patterns = [
            r'الأفضل|الأرخص|الأغلى|الأكبر|الأصغر|الأجمل',
            r'best|better|worst|cheapest|most expensive'
        ]
        for pattern in comparative_patterns:
            if re.search(pattern, reference_text, re.IGNORECASE):
                return ReferenceType.COMPARATIVE
        
        return ReferenceType.INDEFINITE
    
    def _resolve_demonstrative(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve demonstrative references (this, that)"""
        # "this" usually refers to the most recently mentioned item
        recent_items = context.get('recent_items', [])
        if recent_items:
            last_item = recent_items[-1]
            return Reference(
                reference_type=ReferenceType.DEMONSTRATIVE,
                reference_text=reference_text,
                resolved_value=last_item,
                confidence=0.9,
                context_source="recent_items"
            )
        
        # Try to get from active conversation context
        active_entity = context.get('active_entity')
        if active_entity:
            return Reference(
                reference_type=ReferenceType.DEMONSTRATIVE,
                reference_text=reference_text,
                resolved_value=active_entity,
                confidence=0.8,
                context_source="active_entity"
            )
        
        return None
    
    def _resolve_ordinal(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve ordinal references (first, second, third)"""
        # Map Arabic ordinal numbers to indices
        ordinal_map = {
            'الأول': 0,
            'الثاني': 1,
            'الثالث': 2,
            'الرابع': 3,
            'الخامس': 4,
            'السادس': 5,
            'السابع': 6,
            'الثامن': 7,
            'التاسع': 8,
            'العاشر': 9,
            'first': 0,
            'second': 1,
            'third': 2,
            'fourth': 3,
            'fifth': 4,
            'sixth': 5,
            'seventh': 6,
            'eighth': 7,
            'ninth': 8,
            'tenth': 9
        }
        
        # Normalize and find the ordinal
        normalized_text = reference_text.strip().lower()
        for ordinal, index in ordinal_map.items():
            if ordinal in normalized_text:
                # Get the item at the specified index
                items = context.get('search_results', [])
                if 0 <= index < len(items):
                    return Reference(
                        reference_type=ReferenceType.ORDINAL,
                        reference_text=reference_text,
                        resolved_value=items[index],
                        confidence=0.95,
                        context_source="search_results"
                    )
        
        return None
    
    def _resolve_quantitative(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve quantitative references (one, two, three)"""
        # Map numbers to indices
        number_map = {
            'واحد': 0,
            'اثنين': 1,
            'ثلاثة': 2,
            'أربعة': 3,
            'خمسة': 4,
            'one': 0,
            'two': 1,
            'three': 2,
            'four': 3,
            'five': 4
        }
        
        normalized_text = reference_text.strip().lower()
        for number, index in number_map.items():
            if number in normalized_text:
                items = context.get('search_results', [])
                if 0 <= index < len(items):
                    return Reference(
                        reference_type=ReferenceType.QUANTITATIVE,
                        reference_text=reference_text,
                        resolved_value=items[index],
                        confidence=0.9,
                        context_source="search_results"
                    )
        
        return None
    
    def _resolve_relative(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve relative references (previous, next, same)"""
        normalized_text = reference_text.strip().lower()
        
        # "previous" - get previous item in context
        if any(word in normalized_text for word in ['السابق', 'previous', 'last']):
            recent_items = context.get('recent_items', [])
            if len(recent_items) > 1:
                return Reference(
                    reference_type=ReferenceType.RELATIVE,
                    reference_text=reference_text,
                    resolved_value=recent_items[-2],
                    confidence=0.85,
                    context_source="recent_items"
                )
        
        # "next" - get next item (if available)
        if any(word in normalized_text for word in ['التالي', 'next']):
            current_index = context.get('current_item_index', -1)
            items = context.get('search_results', [])
            if current_index + 1 < len(items):
                return Reference(
                    reference_type=ReferenceType.RELATIVE,
                    reference_text=reference_text,
                    resolved_value=items[current_index + 1],
                    confidence=0.85,
                    context_source="search_results"
                )
        
        # "same" - get current item
        if any(word in normalized_text for word in ['نفس', 'same', 'مثله']):
            current_item = context.get('active_entity')
            if current_item:
                return Reference(
                    reference_type=ReferenceType.RELATIVE,
                    reference_text=reference_text,
                    resolved_value=current_item,
                    confidence=0.9,
                    context_source="active_entity"
                )
        
        return None
    
    def _resolve_comparative(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve comparative references (best, cheapest, etc.)"""
        normalized_text = reference_text.strip().lower()
        
        # "best" or "better" - get best ranked item
        if any(word in normalized_text for word in ['الأفضل', 'best', 'better']):
            ranked_items = context.get('ranked_results', [])
            if ranked_items:
                # Assuming ranked_results is sorted by score
                best_item = ranked_items[0]
                return Reference(
                    reference_type=ReferenceType.COMPARATIVE,
                    reference_text=reference_text,
                    resolved_value=best_item,
                    confidence=0.8,
                    context_source="ranked_results"
                )
        
        # "cheapest" - get cheapest item
        if any(word in normalized_text for word in ['الأرخص', 'cheapest']):
            items = context.get('search_results', [])
            if items:
                # Sort by price
                sorted_items = sorted(items, key=lambda x: x.get('price', float('inf')))
                return Reference(
                    reference_type=ReferenceType.COMPARATIVE,
                    reference_text=reference_text,
                    resolved_value=sorted_items[0],
                    confidence=0.9,
                    context_source="price_sorted"
                )
        
        # "most expensive" - get most expensive item
        if any(word in normalized_text for word in ['الأغلى', 'most expensive']):
            items = context.get('search_results', [])
            if items:
                sorted_items = sorted(items, key=lambda x: x.get('price', 0), reverse=True)
                return Reference(
                    reference_type=ReferenceType.COMPARATIVE,
                    reference_text=reference_text,
                    resolved_value=sorted_items[0],
                    confidence=0.9,
                    context_source="price_sorted"
                )
        
        return None
    
    def _resolve_indefinite(self, reference_text: str, context: Dict) -> Optional[Reference]:
        """Resolve indefinite references (something, anything)"""
        # Indefinite references usually require clarification
        normalized_text = reference_text.strip().lower()
        
        if any(word in normalized_text for word in ['شيء', 'something', 'anything']):
            # Try to get the most relevant item from context
            recent_items = context.get('recent_items', [])
            if recent_items:
                return Reference(
                    reference_type=ReferenceType.INDEFINITE,
                    reference_text=reference_text,
                    resolved_value=recent_items[-1],
                    confidence=0.5,  # Lower confidence for indefinite
                    context_source="recent_items"
                )
        
        return None
    
    def update_context(self, context: Dict):
        """Update conversation context with new information"""
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': self._get_timestamp(),
            'context': context
        })
        
        # Update entity history
        for entity_type, value in context.get('entities', {}).items():
            self.entity_history[entity_type].append({
                'value': value,
                'timestamp': self._get_timestamp()
            })
        
        # Limit history size
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]
        
        for entity_type in self.entity_history:
            if len(self.entity_history[entity_type]) > 50:
                self.entity_history[entity_type] = self.entity_history[entity_type][-25:]
    
    def get_entity_history(self, entity_type: str, limit: int = 5) -> List[Any]:
        """Get recent history for a specific entity type"""
        return self.entity_history.get(entity_type, [])[-limit:]
    
    def clear_cache(self):
        """Clear reference cache"""
        self.reference_cache.clear()
        logger.info("Reference cache cleared")
    
    def _initialize_reference_patterns(self) -> Dict:
        """Initialize reference detection patterns"""
        return {
            ReferenceType.DEMONSTRATIVE: [
                r'هذا|هاذا|هذه|ذاك|تلك',
                r'this|that|these|those'
            ],
            ReferenceType.ORDINAL: [
                r'الأول|الثاني|الثالث|الرابع|الخامس',
                r'first|second|third|fourth|fifth'
            ],
            ReferenceType.QUANTITATIVE: [
                r'واحد|اثنين|ثلاثة|أربعة|خمسة',
                r'one|two|three|four|five'
            ],
            ReferenceType.RELATIVE: [
                r'السابق|التالي|القادم|الماضي',
                r'previous|next|past|current'
            ],
            ReferenceType.COMPARATIVE: [
                r'الأفضل|الأرخص|الأغلى|الأكبر',
                r'best|better|worst|cheapest'
            ]
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def resolve_ambiguous_reference(self, 
                                   reference_text: str, 
                                   context: Dict) -> List[Reference]:
        """
        When reference is ambiguous, return multiple possible resolutions
        """
        possible_resolutions = []
        
        # Try different resolution strategies
        strategies = [
            self._resolve_demonstrative,
            self._resolve_ordinal,
            self._resolve_quantitative,
            self._resolve_relative,
            self._resolve_comparative
        ]
        
        for strategy in strategies:
            try:
                resolved = strategy(reference_text, context)
                if resolved:
                    possible_resolutions.append(resolved)
            except:
                continue
        
        return possible_resolutions
    
    def needs_clarification(self, reference_text: str, context: Dict) -> bool:
        """Check if reference needs clarification from user"""
        resolved = self.resolve_reference(reference_text, context)
        
        if not resolved:
            return True
        
        # Low confidence resolution needs clarification
        if resolved.confidence < 0.7:
            return True
        
        return False
    
    def generate_clarification_question(self, reference_text: str, context: Dict) -> str:
        """Generate clarification question for ambiguous reference"""
        possible_resolutions = self.resolve_ambiguous_reference(reference_text, context)
        
        if not possible_resolutions:
            return f"ماذا تقصد بـ'{reference_text}'؟"
        
        if len(possible_resolutions) == 1:
            resolution = possible_resolutions[0]
            return f"هل تقصد {resolution.resolved_value}؟"
        
        # Multiple possible resolutions
        options = [str(r.resolved_value) for r in possible_resolutions[:3]]
        return f"هل تقصد {', '.join(options)}؟"
    
    def add_reference_mapping(self, reference_text: str, resolved_value: Any, confidence: float = 1.0):
        """Manually add a reference mapping for learning"""
        reference = Reference(
            reference_type=ReferenceType.INDEFINITE,
            reference_text=reference_text,
            resolved_value=resolved_value,
            confidence=confidence,
            context_source="manual_mapping"
        )
        
        cache_key = f"{reference_text}_manual"
        self.reference_cache[cache_key] = reference
        logger.info(f"Added manual reference mapping: '{reference_text}' -> {resolved_value}")


# Global instance
context_resolver = ContextResolver()