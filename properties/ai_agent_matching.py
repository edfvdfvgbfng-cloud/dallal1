"""
Agent Matching System
Matches sellers with appropriate real estate agents
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .ai_market_intelligence import AgentVerificationStatus

logger = logging.getLogger(__name__)


class AgentSpecialization(Enum):
    """Types of agent specializations"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LUXURY = "luxury"
    INVESTMENT = "investment"
    LAND = "land"
    GENERAL = "general"


@dataclass
class AgentProfile:
    """Agent profile for matching"""
    agent_id: int
    name: str
    verification_status: AgentVerificationStatus
    specializations: List[AgentSpecialization]
    governorate: str
    districts: List[str]
    active_listings_count: int
    total_sales: int
    average_sale_time_days: float
    response_rate: float
    rating: float
    phone: str = None
    email: str = None
    is_available: bool = True
    last_active: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'verification_status': self.verification_status.value,
            'specializations': [s.value for s in self.specializations],
            'governorate': self.governorate,
            'districts': self.districts,
            'active_listings_count': self.active_listings_count,
            'total_sales': self.total_sales,
            'average_sale_time_days': self.average_sale_time_days,
            'response_rate': self.response_rate,
            'rating': self.rating,
            'phone': self.phone,
            'email': self.email,
            'is_available': self.is_available,
            'last_active': self.last_active
        }


@dataclass
class AgentMatchScore:
    """Agent match score with breakdown"""
    overall_score: float
    agent: AgentProfile
    reasons: List[str]
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'overall_score': self.overall_score,
            'agent': self.agent.to_dict(),
            'reasons': self.reasons,
            'warnings': self.warnings
        }


class AgentMatchingSystem:
    """
    Matches sellers with appropriate real estate agents
    Based on location, specialization, activity, and verification
    """
    
    def __init__(self):
        self.agent_profiles: Dict[int, AgentProfile] = {}
        self.matching_history: List[Dict] = []
    
    def register_agent(self, agent_profile: AgentProfile):
        """Register an agent profile"""
        self.agent_profiles[agent_profile.agent_id] = agent_profile
        logger.info(f"Registered agent {agent_profile.agent_id}: {agent_profile.name}")
    
    def match_agent_for_seller(self,
                              seller_requirements: Dict) -> List[AgentMatchScore]:
        """
        Match appropriate agents for seller
        
        Args:
            seller_requirements: Seller's requirements (location, property type, intent)
            
        Returns:
            List of matched agents with scores
        """
        try:
            # Extract requirements
            governorate = seller_requirements.get('governorate')
            property_type = seller_requirements.get('property_type')
            seller_intent = seller_requirements.get('intent', 'best_price')
            
            matched_agents = []
            
            for agent_id, agent in self.agent_profiles.items():
                if not agent.is_available:
                    continue
                
                score = 0.0
                reasons = []
                warnings = []
                
                # Location match
                if agent.governorate == governorate:
                    score += 0.4
                    reasons.append("متخصص في المحافظة")
                elif governorate in agent.districts:
                    score += 0.2
                    reasons.append("يعمل في المحافظة")
                
                # Specialization match
                property_type_specialization = self._map_property_type_to_specialization(property_type)
                if property_type_specialization in agent.specializations:
                    score += 0.3
                    reasons.append(f"متخصص في {property_type_specialization.value}")
                elif AgentSpecialization.GENERAL in agent.specializations:
                    score += 0.1
                
                # Activity match
                if agent.active_listings_count > 0:
                    score += 0.1
                    reasons.append(f"نشط حاليًا ({agent.active_listings_count} إعلان)")
                
                # Intent-specific factors
                if seller_intent == 'quick_sale':
                    if agent.average_sale_time_days and agent.average_sale_time_days < 60:
                        score += 0.2
                        reasons.append("متوسط وقت بيع سريع")
                
                if seller_intent == 'best_price':
                    if agent.rating and agent.rating > 4.0:
                        score += 0.2
                        reasons.append("تقييم عالي")
                
                # Verification status
                if agent.verification_status == AgentVerificationStatus.VERIFIED:
                    score += 0.2
                elif agent.verification_status == AgentVerificationStatus.UNVERIFIED:
                    warnings.append("غير موثق")
                elif agent.verification_status == AgentVerificationStatus.PENDING_REVIEW:
                    warnings.append("قيد المراجعة")
                
                # Response rate
                if agent.response_rate and agent.response_rate > 0.8:
                    score += 0.1
                
                # Limit score
                score = min(score, 1.0)
                
                # Only include if score is reasonable
                if score > 0.3:
                    matched_agents.append(AgentMatchScore(
                        overall_score=score,
                        agent=agent,
                        reasons=reasons,
                        warnings=warnings
                    ))
            
            # Sort by score
            matched_agents.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Log match
            self.matching_history.append({
                'timestamp': datetime.now().isoformat(),
                'requirements': seller_requirements,
                'matched_count': len(matched_agents)
            })
            
            logger.info(f"Matched {len(matched_agents)} agents for seller")
            return matched_agents
            
        except Exception as e:
            logger.error(f"Error matching agents: {str(e)}")
            return []
    
    def _map_property_type_to_specialization(self, property_type: str) -> AgentSpecialization:
        """Map property type to agent specialization"""
        type_map = {
            'house': AgentSpecialization.RESIDENTIAL,
            'apartment': AgentSpecialization.RESIDENTIAL,
            'villa': AgentSpecialization.LUXURY,
            'land': AgentSpecialization.LAND,
            'office': AgentSpecialization.COMMERCIAL,
            'shop': AgentSpecialization.COMMERCIAL
        }
        
        return type_map.get(property_type, AgentSpecialization.GENERAL)
    
    def get_agent_by_id(self, agent_id: int) -> Optional[AgentProfile]:
        """Get agent profile by ID"""
        return self.agent_profiles.get(agent_id)
    
    def get_agents_by_location(self, governorate: str, district: str = None) -> List[AgentProfile]:
        """Get agents by location"""
        agents = []
        
        for agent in self.agent_profiles.values():
            if agent.governorate == governorate:
                if district is None or district in agent.districts:
                    agents.append(agent)
        
        return agents
    
    def get_matching_summary(self, matches: List[AgentMatchScore]) -> Dict:
        """Get summary of agent matching"""
        if not matches:
            return {'total': 0, 'verified_count': 0, 'high_score_count': 0}
        
        verified_count = sum(1 for m in matches if m.agent.verification_status == AgentVerificationStatus.VERIFIED)
        high_score_count = sum(1 for m in matches if m.overall_score > 0.7)
        
        return {
            'total': len(matches),
            'verified_count': verified_count,
            'high_score_count': high_score_count,
            'average_score': sum(m.overall_score for m in matches) / len(matches)
        }


# Global instance
agent_matching_system = AgentMatchingSystem()