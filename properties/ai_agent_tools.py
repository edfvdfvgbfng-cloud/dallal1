"""
AI Agent Tools System
Provides structured tool calling capabilities with permissions and validation
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Property, Broker, HotelPage, ServiceProviderPage, BuildingAdvertisement
from .ai_arabic_normalizer import arabic_normalizer

logger = logging.getLogger('properties')


class ToolPermission(Enum):
    """Tool permission levels"""
    READ = "read"  # Can read data
    WRITE = "write"  # Can modify data
    ADMIN = "admin"  # Administrative operations


@dataclass
class ToolResult:
    """Standardized tool result"""
    success: bool
    data: Any
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_data: Optional[Dict] = None
    metadata: Optional[Dict] = None


class Tool:
    """Base tool class with validation and permissions"""
    
    def __init__(self, name: str, description: str, permission: ToolPermission, 
                 input_schema: Dict, response_schema: Dict):
        self.name = name
        self.description = description
        self.permission = permission
        self.input_schema = input_schema
        self.response_schema = response_schema
        self.usage_count = 0
        self.error_count = 0
    
    def validate_input(self, input_data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate input against schema"""
        try:
            for field, schema in self.input_schema.items():
                if schema.get('required', False) and field not in input_data:
                    return False, f"Missing required field: {field}"
                
                if field in input_data:
                    value = input_data[field]
                    field_type = schema.get('type')
                    
                    if field_type == 'string' and not isinstance(value, str):
                        return False, f"Field {field} must be string"
                    elif field_type == 'number' and not isinstance(value, (int, float)):
                        return False, f"Field {field} must be number"
                    elif field_type == 'boolean' and not isinstance(value, bool):
                        return False, f"Field {field} must be boolean"
                    
                    # Additional validation
                    if 'min' in schema and isinstance(value, (int, float)):
                        if value < schema['min']:
                            return False, f"Field {field} must be >= {schema['min']}"
                    if 'max' in schema and isinstance(value, (int, float)):
                        if value > schema['max']:
                            return False, f"Field {field} must be <= {schema['max']}"
            
            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute the tool - to be implemented by subclasses"""
        raise NotImplementedError("Tool execution must be implemented by subclass")
    
    def record_usage(self, success: bool):
        """Record tool usage statistics"""
        self.usage_count += 1
        if not success:
            self.error_count += 1


class SearchPropertiesTool(Tool):
    """Tool for searching properties"""
    
    def __init__(self):
        super().__init__(
            name="search_properties",
            description="Search for properties based on criteria",
            permission=ToolPermission.READ,
            input_schema={
                "property_type": {"type": "string", "required": False},
                "governorate": {"type": "string", "required": False},
                "district": {"type": "string", "required": False},
                "min_price": {"type": "number", "required": False, "min": 0},
                "max_price": {"type": "number", "required": False, "min": 0},
                "min_area": {"type": "number", "required": False, "min": 0},
                "max_area": {"type": "number", "required": False, "min": 0},
                "min_rooms": {"type": "number", "required": False, "min": 0},
                "max_rooms": {"type": "number", "required": False, "min": 0},
                "limit": {"type": "number", "required": False, "min": 1, "max": 50}
            },
            response_schema={
                "results": "array of property objects",
                "total_count": "number",
                "search_params": "object"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute property search"""
        try:
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            query = Property.objects.filter(status='published')
            
            # Apply filters
            if 'property_type' in input_data and input_data['property_type']:
                query = query.filter(type=input_data['property_type'])
            
            if 'governorate' in input_data and input_data['governorate']:
                query = query.filter(governorate=input_data['governorate'])
            
            if 'district' in input_data and input_data['district']:
                query = query.filter(district__icontains=input_data['district'])
            
            if 'min_price' in input_data:
                query = query.filter(price__gte=input_data['min_price'])
            
            if 'max_price' in input_data:
                query = query.filter(price__lte=input_data['max_price'])
            
            if 'min_area' in input_data:
                query = query.filter(area__gte=input_data['min_area'])
            
            if 'max_area' in input_data:
                query = query.filter(area__lte=input_data['max_area'])
            
            if 'min_rooms' in input_data:
                query = query.filter(rooms__gte=input_data['min_rooms'])
            
            if 'max_rooms' in input_data:
                query = query.filter(rooms__lte=input_data['max_rooms'])
            
            # Limit results
            limit = input_data.get('limit', 10)
            properties = query[:limit]
            
            # Convert to dict format
            results = []
            for prop in properties:
                results.append({
                    'id': prop.id,
                    'title': prop.title,
                    'price': prop.price,
                    'governorate': prop.governorate,
                    'district': prop.district,
                    'area': prop.area,
                    'type': prop.type,
                    'rooms': prop.rooms,
                    'image': prop.image.url if prop.image else None,
                    'url': f'/property/{prop.id}/'
                })
            
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'results': results,
                    'total_count': len(results),
                    'search_params': input_data
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"SearchPropertiesTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class GetPropertyTool(Tool):
    """Tool for getting specific property details"""
    
    def __init__(self):
        super().__init__(
            name="get_property",
            description="Get detailed information about a specific property",
            permission=ToolPermission.READ,
            input_schema={
                "property_id": {"type": "number", "required": True, "min": 1}
            },
            response_schema={
                "property": "property object with full details"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute property fetch"""
        try:
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            property_id = input_data['property_id']
            try:
                prop = Property.objects.get(id=property_id, status='published')
            except Property.DoesNotExist:
                return ToolResult(success=False, data=None, error="Property not found")
            
            property_data = {
                'id': prop.id,
                'title': prop.title,
                'description': prop.description,
                'price': prop.price,
                'governorate': prop.governorate,
                'district': prop.district,
                'area': prop.area,
                'type': prop.type,
                'rooms': prop.rooms,
                'bathrooms': prop.bathrooms,
                'floors': prop.floors,
                'image': prop.image.url if prop.image else None,
                'url': f'/property/{prop.id}/'
            }
            
            self.record_usage(True)
            
            return ToolResult(success=True, data={'property': property_data})
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"GetPropertyTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class SearchAgentsTool(Tool):
    """Tool for searching brokers/agents"""
    
    def __init__(self):
        super().__init__(
            name="search_agents",
            description="Search for real estate agents/brokers",
            permission=ToolPermission.READ,
            input_schema={
                "governorate": {"type": "string", "required": False},
                "specialization": {"type": "string", "required": False},
                "limit": {"type": "number", "required": False, "min": 1, "max": 50}
            },
            response_schema={
                "results": "array of agent objects",
                "total_count": "number"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute agent search"""
        try:
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            query = Broker.objects.filter(is_active=True)
            
            if 'governorate' in input_data and input_data['governorate']:
                query = query.filter(governorate=input_data['governorate'])
            
            if 'specialization' in input_data and input_data['specialization']:
                query = query.filter(specialization__icontains=input_data['specialization'])
            
            limit = input_data.get('limit', 10)
            agents = query[:limit]
            
            results = []
            for agent in agents:
                results.append({
                    'id': agent.id,
                    'name': agent.display_name,
                    'governorate': agent.governorate,
                    'specialization': agent.specialization,
                    'rating': agent.rating if hasattr(agent, 'rating') else None,
                    'url': f'/broker/{agent.id}/'
                })
            
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'results': results,
                    'total_count': len(results)
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"SearchAgentsTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class SearchJobsTool(Tool):
    """Tool for searching jobs"""
    
    def __init__(self):
        super().__init__(
            name="search_jobs",
            description="Search for job opportunities",
            permission=ToolPermission.READ,
            input_schema={
                "job_type": {"type": "string", "required": False},
                "location": {"type": "string", "required": False},
                "min_salary": {"type": "number", "required": False, "min": 0},
                "limit": {"type": "number", "required": False, "min": 1, "max": 50}
            },
            response_schema={
                "results": "array of job objects",
                "total_count": "number"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute job search"""
        try:
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            # Placeholder for job search - implement based on your job model
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'results': [],
                    'total_count': 0,
                    'message': 'Job search feature coming soon'
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"SearchJobsTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class SavePropertyTool(Tool):
    """Tool for saving a property to user's favorites"""
    
    def __init__(self):
        super().__init__(
            name="save_property",
            description="Save a property to user's favorites",
            permission=ToolPermission.WRITE,
            input_schema={
                "property_id": {"type": "number", "required": True, "min": 1}
            },
            response_schema={
                "success": "boolean",
                "message": "string"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute property save"""
        try:
            if not user or not user.is_authenticated:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Authentication required to save properties"
                )
            
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            property_id = input_data['property_id']
            
            try:
                prop = Property.objects.get(id=property_id, status='published')
            except Property.DoesNotExist:
                return ToolResult(success=False, data=None, error="Property not found")
            
            # Check if already saved - implement based on your user model
            # This is a placeholder - implement based on your SavedProperty model
            
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'success': True,
                    'message': 'Property saved to favorites'
                },
                requires_confirmation=True,
                confirmation_data={
                    'action': 'save_property',
                    'property_id': property_id,
                    'property_title': prop.title
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"SavePropertyTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class ContactAgentTool(Tool):
    """Tool for contacting an agent"""
    
    def __init__(self):
        super().__init__(
            name="contact_agent",
            description="Send a message to a real estate agent",
            permission=ToolPermission.WRITE,
            input_schema={
                "agent_id": {"type": "number", "required": True, "min": 1},
                "message": {"type": "string", "required": True, "min_length": 10},
                "property_id": {"type": "number", "required": False, "min": 1}
            },
            response_schema={
                "success": "boolean",
                "message": "string"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute agent contact"""
        try:
            if not user or not user.is_authenticated:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Authentication required to contact agents"
                )
            
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            agent_id = input_data['agent_id']
            message = input_data['message']
            
            try:
                agent = Broker.objects.get(id=agent_id, is_active=True)
            except Broker.DoesNotExist:
                return ToolResult(success=False, data=None, error="Agent not found")
            
            # Implement message sending based on your messaging system
            # This is a placeholder
            
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'success': True,
                    'message': 'Message sent to agent'
                },
                requires_confirmation=True,
                confirmation_data={
                    'action': 'contact_agent',
                    'agent_id': agent_id,
                    'agent_name': agent.display_name,
                    'message_preview': message[:50] + '...' if len(message) > 50 else message
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"ContactAgentTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class CreatePropertyListingTool(Tool):
    """Tool for creating a new property listing"""
    
    def __init__(self):
        super().__init__(
            name="create_property_listing",
            description="Create a new property listing",
            permission=ToolPermission.WRITE,
            input_schema={
                "title": {"type": "string", "required": True, "min_length": 5},
                "description": {"type": "string", "required": True, "min_length": 20},
                "property_type": {"type": "string", "required": True},
                "governorate": {"type": "string", "required": True},
                "district": {"type": "string", "required": True},
                "area": {"type": "number", "required": True, "min": 10},
                "price": {"type": "number", "required": True, "min": 0},
                "rooms": {"type": "number", "required": False, "min": 0}
            },
            response_schema={
                "success": "boolean",
                "property_id": "number",
                "message": "string"
            }
        )
    
    def execute(self, input_data: Dict, user: Optional[User] = None) -> ToolResult:
        """Execute property listing creation"""
        try:
            if not user or not user.is_authenticated:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Authentication required to create property listings"
                )
            
            validation, error = self.validate_input(input_data)
            if not validation:
                return ToolResult(success=False, data=None, error=error)
            
            # Create property based on input data
            # This is a placeholder - implement based on your property creation logic
            
            self.record_usage(True)
            
            return ToolResult(
                success=True,
                data={
                    'success': True,
                    'message': 'Property listing created successfully'
                },
                requires_confirmation=True,
                confirmation_data={
                    'action': 'create_property',
                    'title': input_data['title'],
                    'property_type': input_data['property_type'],
                    'governorate': input_data['governorate'],
                    'district': input_data['district'],
                    'area': input_data['area'],
                    'price': input_data['price']
                }
            )
            
        except Exception as e:
            self.record_usage(False)
            logger.error(f"CreatePropertyListingTool error: {str(e)}")
            return ToolResult(success=False, data=None, error=str(e))


class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        self.register_tool(SearchPropertiesTool())
        self.register_tool(GetPropertyTool())
        self.register_tool(SearchAgentsTool())
        self.register_tool(SearchJobsTool())
        self.register_tool(SavePropertyTool())
        self.register_tool(ContactAgentTool())
        self.register_tool(CreatePropertyListingTool())
    
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools"""
        return self.tools.copy()
    
    def get_tools_by_permission(self, permission: ToolPermission) -> List[Tool]:
        """Get tools by permission level"""
        return [tool for tool in self.tools.values() if tool.permission == permission]
    
    def check_permission(self, tool_name: str, user: Optional[User] = None) -> bool:
        """Check if user has permission to use tool"""
        tool = self.get_tool(tool_name)
        if not tool:
            return False
        
        if tool.permission == ToolPermission.READ:
            return True  # Read tools are generally available
        
        if tool.permission == ToolPermission.WRITE:
            return user and user.is_authenticated
        
        if tool.permission == ToolPermission.ADMIN:
            return user and user.is_authenticated and user.is_staff
        
        return False


# Global tool registry instance
tool_registry = ToolRegistry()