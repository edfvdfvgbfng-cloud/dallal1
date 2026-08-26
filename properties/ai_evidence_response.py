"""
Evidence-Based Response System
Ensures all AI responses are based on actual data with proper verification
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .ai_agent_tools import tool_registry
from .ai_conversation_planner import ConversationPlan
from .ai_context_resolver import ContextResolver

logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """Types of evidence for responses"""
    DATABASE = "database"
    TOOL_RESULT = "tool_result"
    USER_PROVIDED = "user_provided"
    CALCULATED = "calculated"
    INFERRED = "inferred"
    EXTERNAL_API = "external_api"


class ConfidenceLevel(Enum):
    """Confidence levels for responses"""
    HIGH = "high"  # 0.9+
    MEDIUM = "medium"  # 0.7-0.9
    LOW = "low"  # 0.5-0.7
    VERY_LOW = "very_low"  # <0.5


@dataclass
class Evidence:
    """Evidence for a piece of information"""
    evidence_id: str
    evidence_type: EvidenceType
    source: str
    data: Dict[str, Any]
    confidence: float
    timestamp: str
    verified: bool = False
    verification_method: str = None
    
    def __post_init__(self):
        if not self.evidence_id:
            self.evidence_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'source': self.source,
            'data': self.data,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'verified': self.verified,
            'verification_method': self.verification_method
        }


@dataclass
class ResponseClaim:
    """Individual claim in a response with supporting evidence"""
    claim_id: str
    claim_text: str
    evidence: List[Evidence]
    confidence: float
    requires_verification: bool = False
    verification_status: str = "pending"
    
    def __post_init__(self):
        if not self.claim_id:
            self.claim_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'claim_id': self.claim_id,
            'claim_text': self.claim_text,
            'evidence': [e.to_dict() for e in self.evidence],
            'confidence': self.confidence,
            'requires_verification': self.requires_verification,
            'verification_status': self.verification_status
        }


@dataclass
class VerifiedResponse:
    """Verified response with evidence and confidence"""
    response_id: str
    original_response: str
    verified_response: str
    claims: List[ResponseClaim]
    overall_confidence: float
    confidence_level: ConfidenceLevel
    evidence_summary: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.response_id:
            self.response_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'response_id': self.response_id,
            'original_response': self.original_response,
            'verified_response': self.verified_response,
            'claims': [claim.to_dict() for claim in self.claims],
            'overall_confidence': self.overall_confidence,
            'confidence_level': self.confidence_level.value,
            'evidence_summary': self.evidence_summary,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class EvidenceBasedResponseSystem:
    """
    Evidence-based response system that ensures all AI responses
    are based on actual data with proper verification
    """
    
    def __init__(self):
        self.context_resolver = ContextResolver()
        self.evidence_cache: Dict[str, Evidence] = {}
        self.response_history: List[Dict] = []
        self.verification_rules = self._initialize_verification_rules()
    
    def verify_response(self, 
                      ai_response: str,
                      tool_results: Dict[str, Any],
                      conversation_context: Dict) -> VerifiedResponse:
        """
        Verify an AI response against available evidence
        
        Args:
            ai_response: The AI's response text
            tool_results: Results from tool calls
            conversation_context: Conversation context
            
        Returns:
            Verified response with evidence and confidence
        """
        try:
            # Parse response into claims
            claims = self._parse_response_into_claims(ai_response, conversation_context)
            
            # Verify each claim
            verified_claims = []
            for claim in claims:
                verified_claim = self._verify_claim(claim, tool_results, conversation_context)
                verified_claims.append(verified_claim)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(verified_claims)
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            # Generate verified response
            verified_response = self._generate_verified_response(
                ai_response, verified_claims, confidence_level
            )
            
            # Generate evidence summary
            evidence_summary = self._generate_evidence_summary(verified_claims)
            
            # Generate warnings if needed
            warnings = self._generate_warnings(verified_claims, tool_results)
            
            # Create verified response object
            verified_response_obj = VerifiedResponse(
                original_response=ai_response,
                verified_response=verified_response,
                claims=verified_claims,
                overall_confidence=overall_confidence,
                confidence_level=confidence_level,
                evidence_summary=evidence_summary,
                warnings=warnings,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'claim_count': len(verified_claims),
                    'verified_count': sum(1 for c in verified_claims if c.verification_status == "verified")
                }
            )
            
            # Add to history
            self.response_history.append({
                'timestamp': datetime.now().isoformat(),
                'response_id': verified_response_obj.response_id,
                'confidence': overall_confidence,
                'warnings': warnings
            })
            
            logger.info(f"Verified response with confidence {overall_confidence:.2f}")
            return verified_response_obj
            
        except Exception as e:
            logger.error(f"Error verifying response: {str(e)}")
            return self._create_error_response(ai_response, str(e))
    
    def _parse_response_into_claims(self, 
                                  response: str,
                                  context: Dict) -> List[ResponseClaim]:
        """Parse AI response into individual claims"""
        claims = []
        
        # Simple claim extraction based on patterns
        # In a real system, this would use NLP to extract claims
        
        # Split response into sentences
        sentences = self._split_into_sentences(response)
        
        for i, sentence in enumerate(sentences):
            if self._is_fact_claim(sentence):
                claim = ResponseClaim(
                    claim_text=sentence.strip(),
                    evidence=[],
                    confidence=0.7,  # Initial confidence
                    requires_verification=True
                )
                claims.append(claim)
        
        return claims
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_fact_claim(self, sentence: str) -> bool:
        """Determine if a sentence makes a factual claim"""
        factual_indicators = [
            r'\d+',  # Numbers
            r'سعر|السعر|المساحة|الموقع|المحافظة',  # Property terms
            r'يوجد|يتوفر|موجود',  # Existence claims
            r'في|عند|من',  # Location claims
        ]
        
        for pattern in factual_indicators:
            if re.search(pattern, sentence):
                return True
        
        return False
    
    def _verify_claim(self, 
                     claim: ResponseClaim,
                     tool_results: Dict[str, Any],
                     context: Dict) -> ResponseClaim:
        """Verify a single claim against available evidence"""
        claim_text = claim.claim_text.lower()
        
        # Try to find supporting evidence in tool results
        evidence = self._find_evidence_for_claim(claim_text, tool_results, context)
        
        if evidence:
            claim.evidence = evidence
            claim.confidence = min(0.9, sum(e.confidence for e in evidence) / len(evidence))
            claim.verification_status = "verified"
        else:
            # No evidence found
            claim.confidence = 0.3
            claim.verification_status = "unverified"
        
        return claim
    
    def _find_evidence_for_claim(self, 
                                claim_text: str,
                                tool_results: Dict[str, Any],
                                context: Dict) -> List[Evidence]:
        """Find evidence supporting a claim"""
        evidence = []
        
        # Check tool results for matching evidence
        for tool_name, result in tool_results.items():
            if isinstance(result, dict):
                evidence_item = self._extract_evidence_from_result(result, claim_text, tool_name)
                if evidence_item:
                    evidence.append(evidence_item)
        
        # Check context for supporting information
        context_evidence = self._extract_evidence_from_context(claim_text, context)
        if context_evidence:
            evidence.append(context_evidence)
        
        return evidence
    
    def _extract_evidence_from_result(self, 
                                    result: Dict,
                                    claim_text: str,
                                    tool_name: str) -> Optional[Evidence]:
        """Extract evidence from a tool result"""
        # Check if claim text matches any values in the result
        for key, value in result.items():
            if str(value).lower() in claim_text or claim_text in str(value).lower():
                return Evidence(
                    evidence_type=EvidenceType.TOOL_RESULT,
                    source=tool_name,
                    data={key: value},
                    confidence=0.8,
                    verified=True,
                    verification_method="direct_match"
                )
        
        return None
    
    def _extract_evidence_from_context(self, 
                                       claim_text: str,
                                       context: Dict) -> Optional[Evidence]:
        """Extract evidence from conversation context"""
        # Check recent entities in context
        recent_entities = context.get('entities', {})
        
        for key, value in recent_entities.items():
            if str(value).lower() in claim_text:
                return Evidence(
                    evidence_type=EvidenceType.USER_PROVIDED,
                    source="conversation_context",
                    data={key: value},
                    confidence=0.7,
                    verified=True,
                    verification_method="context_match"
                )
        
        return None
    
    def _calculate_overall_confidence(self, claims: List[ResponseClaim]) -> float:
        """Calculate overall confidence from all claims"""
        if not claims:
            return 0.5
        
        # Weight claims by their confidence
        total_weight = 0
        weighted_confidence = 0
        
        for claim in claims:
            weight = 1.0 if claim.verification_status == "verified" else 0.5
            total_weight += weight
            weighted_confidence += claim.confidence * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from confidence score"""
        if confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_verified_response(self, 
                                    original_response: str,
                                    claims: List[ResponseClaim],
                                    confidence_level: ConfidenceLevel) -> str:
        """Generate final verified response"""
        # For now, return original response
        # In a real system, this might modify uncertain claims
        return original_response
    
    def _generate_evidence_summary(self, claims: List[ResponseClaim]) -> Dict:
        """Generate summary of evidence for the response"""
        verified_count = sum(1 for c in claims if c.verification_status == "verified")
        unverified_count = len(claims) - verified_count
        
        evidence_types = defaultdict(int)
        for claim in claims:
            for evidence in claim.evidence:
                evidence_types[evidence.evidence_type.value] += 1
        
        return {
            'total_claims': len(claims),
            'verified_claims': verified_count,
            'unverified_claims': unverified_count,
            'evidence_types': dict(evidence_types)
        }
    
    def _generate_warnings(self, 
                          claims: List[ResponseClaim],
                          tool_results: Dict[str, Any]) -> List[str]:
        """Generate warnings for the response"""
        warnings = []
        
        # Warning for unverified claims
        unverified_claims = [c for c in claims if c.verification_status == "unverified"]
        if unverified_claims:
            warnings.append(f"توجد {len(unverified_claims)} معلومات غير مؤكدة في الرد")
        
        # Warning for low confidence
        low_confidence_claims = [c for c in claims if c.confidence < 0.5]
        if low_confidence_claims:
            warnings.append(f"توجد {len(low_confidence_claims)} معلومات منخفضة الثقة")
        
        # Warning for no tool results
        if not tool_results:
            warnings.append("الرد مبني على معلومات عامة وليس بيانات محددة")
        
        return warnings
    
    def _create_error_response(self, original_response: str, error: str) -> VerifiedResponse:
        """Create error response when verification fails"""
        return VerifiedResponse(
            original_response=original_response,
            verified_response=original_response,
            claims=[],
            overall_confidence=0.3,
            confidence_level=ConfidenceLevel.VERY_LOW,
            evidence_summary={'error': error},
            warnings=["فشل التحقق من صحة المعلومات"],
            metadata={'error': error, 'timestamp': datetime.now().isoformat()}
        )
    
    def check_for_hallucinations(self, 
                                response: str,
                                available_data: Dict[str, Any]) -> List[str]:
        """
        Check for potential hallucinations in the response
        
        Args:
            response: AI response text
            available_data: Available data sources
            
        Returns:
            List of potential hallucinations
        """
        potential_hallucinations = []
        
        # Extract specific claims from response
        claims = self._extract_specific_claims(response)
        
        for claim in claims:
            if not self._is_claim_supported(claim, available_data):
                potential_hallucinations.append(claim)
        
        return potential_hallucinations
    
    def _extract_specific_claims(self, response: str) -> List[str]:
        """Extract specific factual claims from response"""
        claims = []
        
        # Extract numbers and specific values
        import re
        
        # Extract prices
        price_claims = re.findall(r'(\d+,?\d*)\s*(مليون|ألف|دينار)', response)
        claims.extend(price_claims)
        
        # Extract specific locations
        location_claims = re.findall(r'(في|بالبصرة|في بغداد|في النجف|في الموصل)', response)
        claims.extend(location_claims)
        
        # Extract property types
        type_claims = re.findall(r'(بيت|شقة|أرض|فيلا|دور)', response)
        claims.extend(type_claims)
        
        return claims
    
    def _is_claim_supported(self, claim: str, available_data: Dict[str, Any]) -> bool:
        """Check if a claim is supported by available data"""
        claim_lower = claim.lower()
        
        # Check against available data
        for key, value in available_data.items():
            if isinstance(value, (list, dict)):
                continue  # Skip complex structures for now
            
            if str(value).lower() in claim_lower or claim_lower in str(value).lower():
                return True
        
        return False
    
    def add_evidence(self, evidence: Evidence):
        """Add evidence to cache"""
        self.evidence_cache[evidence.evidence_id] = evidence
        logger.info(f"Added evidence {evidence.evidence_id} of type {evidence.evidence_type.value}")
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence from cache"""
        return self.evidence_cache.get(evidence_id)
    
    def _initialize_verification_rules(self) -> Dict:
        """Initialize verification rules for different types of claims"""
        return {
            'price_claims': {
                'required_evidence': [EvidenceType.DATABASE, EvidenceType.TOOL_RESULT],
                'min_confidence': 0.8,
                'verification_method': 'direct_comparison'
            },
            'location_claims': {
                'required_evidence': [EvidenceType.DATABASE, EvidenceType.USER_PROVIDED],
                'min_confidence': 0.7,
                'verification_method': 'location_match'
            },
            'existence_claims': {
                'required_evidence': [EvidenceType.DATABASE, EvidenceType.TOOL_RESULT],
                'min_confidence': 0.9,
                'verification_method': 'existence_check'
            },
            'preference_claims': {
                'required_evidence': [EvidenceType.INFERRED, EvidenceType.USER_PROVIDED],
                'min_confidence': 0.5,
                'verification_method': 'preference_matching'
            }
        }
    
    def explain_confidence(self, response: VerifiedResponse) -> str:
        """Generate explanation for confidence level"""
        confidence_explanations = {
            ConfidenceLevel.HIGH: "هذا الرد مبني على بيانات مؤكدة من قاعدة البيانات",
            ConfidenceLevel.MEDIUM: "هذا الرد مبني على بيانات متوفرة لكن قد يحتاج تأكيد",
            ConfidenceLevel.LOW: "هذا الرد مبني على معلومات محدودة ويفضل التأكيد",
            ConfidenceLevel.VERY_LOW: "هذا الرد مبني على معلومات عامة وقد يكون غير دقيق"
        }
        
        return confidence_explanations.get(response.confidence_level, "مستوى الثقة غير محدد")
    
    def generate_uncertainty_response(self, 
                                      query: str,
                                      context: Dict) -> str:
        """Generate response when confidence is low"""
        return f"أعتقد أنك تقصد {self._most_likely_interpretation(query, context)}، صحيح؟"
    
    def _most_likely_interpretation(self, query: str, context: Dict) -> str:
        """Get most likely interpretation of ambiguous query"""
        # Use context resolver to resolve references
        reference = self.context_resolver.resolve_reference(query, context)
        
        if reference and reference.resolved_value:
            return str(reference.resolved_value)
        
        # Return original query if no resolution
        return query


# Global instance
evidence_based_response_system = EvidenceBasedResponseSystem()