"""
Agent Profiles and Handoff System
Manages specialized agent types and context transfer between agents
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents"""
    GENERAL = "general"
    PROPERTY = "property"
    SELLER = "seller"
    BUYER = "buyer"
    JOBS = "jobs"
    MARKET = "market"
    DOCUMENT = "document"
    ANALYTICS = "analytics"


@dataclass
class AgentProfile:
    """Profile for an agent type"""
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    tools: List[str]
    permissions: List[str]
    can_handoff_to: List[AgentType]
    max_retries: int = 3
    timeout_seconds: int = 60
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'agent_type': self.agent_type.value,
            'name': self.name,
            'description': self.description,
            'capabilities': self.capabilities,
            'tools': self.tools,
            'permissions': self.permissions,
            'can_handoff_to': [a.value for a in self.can_handoff_to],
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds
        }


@dataclass
class AgentContext:
    """Context transferred between agents"""
    context_id: str = None
    user_id: int = None
    conversation_id: str = None
    intent: str = None
    entities: Dict[str, Any] = None
    goal: str = None
    task_id: str = None
    property_id: int = None
    document_id: str = None
    agent_history: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: str = None
    
    def __post_init__(self):
        if not self.context_id:
            self.context_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'context_id': self.context_id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'intent': self.intent,
            'entities': self.entities,
            'goal': self.goal,
            'task_id': self.task_id,
            'property_id': self.property_id,
            'document_id': self.document_id,
            'agent_history': self.agent_history,
            'metadata': self.metadata,
            'created_at': self.created_at
        }


class AgentHandoffSystem:
    """
    Manages agent profiles and context transfer between agents
    Enables smooth handoff with context preservation
    """
    
    def __init__(self):
        self.agent_profiles: Dict[AgentType, AgentProfile] = {}
        self.active_contexts: Dict[str, AgentContext] = {}
        self.handoff_history: List[Dict] = []
        self._initialize_profiles()
    
    def _initialize_profiles(self):
        """Initialize agent profiles"""
        # General Assistant
        self.agent_profiles[AgentType.GENERAL] = AgentProfile(
            agent_type=AgentType.GENERAL,
            name="General Assistant",
            description="General purpose AI assistant",
            capabilities=["chat", "information", "basic_search"],
            tools=["search", "retrieve", "analyze"],
            permissions=["read:*"],
            can_handoff_to=[AgentType.PROPERTY, AgentType.SELLER, AgentType.BUYER, AgentType.JOBS, AgentType.MARKET]
        )
        
        # Property Assistant
        self.agent_profiles[AgentType.PROPERTY] = AgentProfile(
            agent_type=AgentType.PROPERTY,
            name="Property Assistant",
            description="Specialized in property search and analysis",
            capabilities=["property_search", "property_comparison", "recommendation"],
            tools=["search_properties", "compare_properties", "rank_properties"],
            permissions=["read:property", "read:agent"],
            can_handoff_to=[AgentType.SELLER, AgentType.BUYER, AgentType.GENERAL]
        )
        
        # Seller Assistant
        self.agent_profiles[AgentType.SELLER] = AgentProfile(
            agent_type=AgentType.SELLER,
            name="Seller Assistant",
            description="Specialized in selling properties",
            capabilities=["create_listing", "agent_matching", "listing_optimization"],
            tools=["create_listing", "match_agent", "optimize_listing", "upload_images"],
            permissions=["read:property", "write:listing", "write:image"],
            can_handoff_to=[AgentType.PROPERTY, AgentType.GENERAL]
        )
        
        # Buyer Assistant
        self.agent_profiles[AgentType.BUYER] = AgentProfile(
            agent_type=AgentType.BUYER,
            name="Buyer Assistant",
            description="Specialized in helping buyers find properties",
            capabilities=["property_search", "agent_contact", "application"],
            tools=["search_properties", "contact_agent", "submit_application"],
            permissions=["read:property", "read:agent", "write:application"],
            can_handoff_to=[AgentType.PROPERTY, AgentType.GENERAL]
        )
        
        # Jobs Assistant
        self.agent_profiles[AgentType.JOBS] = AgentProfile(
            agent_type=AgentType.JOBS,
            name="Jobs Assistant",
            description="Specialized in job search and CV matching",
            capabilities=["job_search", "cv_analysis", "job_application"],
            tools=["search_jobs", "analyze_cv", "match_jobs", "submit_application"],
            permissions=["read:job", "read:cv", "write:application"],
            can_handoff_to=[AgentType.GENERAL]
        )
        
        # Market Assistant
        self.agent_profiles[AgentType.MARKET] = AgentProfile(
            agent_type=AgentType.MARKET,
            name="Market Assistant",
            description="Specialized in market analytics and intelligence",
            capabilities=["market_analysis", "price_analysis", "trends"],
            tools=["market_analytics", "price_comparison", "area_analysis"],
            permissions=["read:property", "read:market"],
            can_handoff_to=[AgentType.PROPERTY, AgentType.GENERAL]
        )
        
        # Document Assistant
        self.agent_profiles[AgentType.DOCUMENT] = AgentProfile(
            agent_type=AgentType.DOCUMENT,
            name="Document Assistant",
            description="Specialized in document processing and analysis",
            capabilities=["document_extraction", "document_qa", "ocr"],
            tools=["extract_document", "qa_document", "ocr"],
            permissions=["read:document", "write:document"],
            can_handoff_to=[AgentType.JOBS, AgentType.GENERAL]
        )
        
        # Analytics Assistant
        self.agent_profiles[AgentType.ANALYTICS] = AgentProfile(
            agent_type=AgentType.ANALYTICS,
            name="Analytics Assistant",
            description="Specialized in data analytics and reporting",
            capabilities=["analytics", "reporting", "visualization"],
            tools=["run_analytics", "generate_report"],
            permissions=["read:*", "write:report"],
            can_handoff_to=[AgentType.MARKET, AgentType.GENERAL]
        )
    
    def get_agent_profile(self, agent_type: AgentType) -> Optional[AgentProfile]:
        """Get profile for an agent type"""
        return self.agent_profiles.get(agent_type)
    
    def determine_best_agent(self, user_input: str, context: Dict = None) -> AgentType:
        """
        Determine the best agent type for a given input
        
        Args:
            user_input: User's input
            context: Conversation context
            
        Returns:
            Recommended agent type
        """
        user_input_lower = user_input.lower()
        
        # Check for buy intent
        if any(kw in user_input_lower for kw in ['أريد شراء', 'أريد بيت', 'أبحث عن', 'شراء']):
            return AgentType.BUYER
        
        # Check for sell intent
        if any(kw in user_input_lower for kw in ['أريد بيع', 'أبيع', 'نشر إعلان', 'بيتي للبيع']):
            return AgentType.SELLER
        
        # Check for job intent
        if any(kw in user_input_lower for kw in ['وظيفة', 'شغل', 'cv', 'سيرة ذاتية', 'توظيف']):
            return AgentType.JOBS
        
        # Check for market intent
        if any(kw in user_input_lower for kw in ['سعر', 'متوسط', 'أسعار', 'سوق', 'إحصاء']):
            return AgentType.MARKET
        
        # Check for document intent
        if any(kw in user_input_lower for kw in ['ملف', 'pdf', 'مستند', 'استخرج']):
            return AgentType.DOCUMENT
        
        # Default to general
        return AgentType.GENERAL
    
    def create_context(self,
                     user_id: int,
                     conversation_id: str,
                     intent: str,
                     entities: Dict,
                     goal: str) -> AgentContext:
        """Create a new agent context"""
        context = AgentContext(
            user_id=user_id,
            conversation_id=conversation_id,
            intent=intent,
            entities=entities,
            goal=goal
        )
        
        self.active_contexts[context.context_id] = context
        return context
    
    def handoff(self,
               from_agent: AgentType,
               to_agent: AgentType,
               context: AgentContext) -> AgentContext:
        """
        Handoff context from one agent to another
        
        Args:
            from_agent: Source agent type
            to_agent: Destination agent type
            context: Current context
            
        Returns:
            Updated context for destination agent
        """
        # Validate handoff is allowed
        from_profile = self.agent_profiles.get(from_agent)
        if not from_profile or to_agent not in from_profile.can_handoff_to:
            logger.warning(f"Handoff from {from_agent.value} to {to_agent.value} not allowed")
            return context
        
        # Update context
        context.agent_history.append(from_agent.value)
        context.metadata['last_handoff_from'] = from_agent.value
        context.metadata['last_handoff_at'] = datetime.now().isoformat()
        
        # Log handoff
        self.handoff_history.append({
            'timestamp': datetime.now().isoformat(),
            'from_agent': from_agent.value,
            'to_agent': to_agent.value,
            'context_id': context.context_id,
            'user_id': context.user_id
        })
        
        logger.info(f"Handoff from {from_agent.value} to {to_agent.value} for context {context.context_id}")
        return context
    
    def get_context(self, context_id: str) -> Optional[AgentContext]:
        """Get context by ID"""
        return self.active_contexts.get(context_id)
    
    def update_context(self, context_id: str, updates: Dict):
        """Update context with new information"""
        if context_id in self.active_contexts:
            for key, value in updates.items():
                setattr(self.active_contexts[context_id], key, value)
    
    def cleanup_context(self, context_id: str):
        """Remove context when no longer needed"""
        if context_id in self.active_contexts:
            del self.active_contexts[context_id]
            logger.info(f"Cleaned up context {context_id}")
    
    def get_handoff_statistics(self) -> Dict:
        """Get handoff statistics"""
        handoff_counts = {}
        
        for handoff in self.handoff_history:
            key = f"{handoff['from_agent']} -> {handoff['to_agent']}"
            handoff_counts[key] = handoff_counts.get(key, 0) + 1
        
        return {
            'total_handoffs': len(self.handoff_history),
            'handoff_distribution': handoff_counts,
            'active_contexts': len(self.active_contexts),
            'available_agents': len(self.agent_profiles)
        }


# Global instance
agent_handoff_system = AgentHandoffSystem()