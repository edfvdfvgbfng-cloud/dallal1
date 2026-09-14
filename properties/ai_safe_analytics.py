"""
Safe Analytics Query Layer
Safe query execution for market analytics
Prevents arbitrary SQL injection and ensures data safety
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of allowed analytics queries"""
    COUNT = "count"
    AVG = "avg"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    DISTRIBUTION = "distribution"
    COMPARE = "compare"
    GROUP_BY = "group_by"


class MetricType(Enum):
    """Types of metrics that can be queried"""
    PRICE = "price"
    AREA = "area"
    ROOMS = "rooms"
    PRICE_PER_M2 = "price_per_m2"
    LISTING_AGE = "listing_age"
    VIEWS = "views"
    SAVES = "saves"
    CONTACTS = "contacts"


@dataclass
class AnalyticsQuery:
    """Safe analytics query request"""
    query_id: str = None
    entity: str = None  # property, agent, etc.
    filters: Dict[str, Any] = None
    metric: MetricType = None
    query_type: QueryType = None
    group_by: List[str] = None
    time_range: Dict = None
    limit: int = None
    user_id: int = None
    request_timestamp: str = None
    
    def __post_init__(self):
        if self.query_id is None:
            import uuid
            self.query_id = str(uuid.uuid4())[:8]
        if self.request_timestamp is None:
            self.request_timestamp = datetime.now().isoformat()
        if self.filters is None:
            self.filters = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'query_id': self.query_id,
            'entity': self.entity,
            'filters': self.filters,
            'metric': self.metric.value,
            'query_type': self.query_type.value,
            'group_by': self.group_by,
            'time_range': self.time_range,
            'limit': self.limit,
            'user_id': self.user_id,
            'request_timestamp': self.request_timestamp
        }


@dataclass
class AnalyticsResult:
    """Result of analytics query"""
    query_id: str
    success: bool
    result: Any
    row_count: int
    execution_time_ms: float
    error: str = None
    data_source: str = "database"
    confidence: str = "high"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'query_id': self.query_id,
            'success': self.success,
            'result': self.result,
            'row_count': self.row_count,
            'execution_time_ms': self.execution_time_ms,
            'error': self.error,
            'data_source': self.data_source,
            'confidence': self.confidence
        }


class SafeAnalyticsQueryLayer:
    """
    Safe layer for executing analytics queries
    Prevents arbitrary SQL and ensures only safe queries are executed
    """
    
    def __init__(self):
        self.allowed_entities = ['property', 'agent', 'user', 'conversation']
        self.allowed_metrics = [m.value for m in MetricType]
        self.allowed_query_types = [q.value for q in QueryType]
        self.query_history: List[Dict] = []
        self.database_query_func: Callable = None
    
    def register_database_query_function(self, func: Callable):
        """Register the actual database query function"""
        self.database_query_func = func
        logger.info("Registered database query function")
    
    def create_query(self,
                    entity: str,
                    metric: MetricType,
                    query_type: QueryType,
                    filters: Dict = None,
                    group_by: List[str] = None,
                    time_range: Dict = None,
                    limit: int = None,
                    user_id: int = None) -> AnalyticsQuery:
        """
        Create a safe analytics query
        
        Args:
            entity: Entity to query (property, agent, etc.)
            metric: Metric to calculate
            query_type: Type of query (count, avg, median, etc.)
            filters: Filters to apply
            group_by: Fields to group by
            time_range: Time range for query
            limit: Result limit
            user_id: User ID (for authorization)
            
        Returns:
            AnalyticsQuery object
        """
        # Validate inputs
        if entity not in self.allowed_entities:
            raise ValueError(f"Entity '{entity}' not allowed")
        
        if metric.value not in self.allowed_metrics:
            raise ValueError(f"Metric '{metric.value}' not allowed")
        
        if query_type.value not in self.allowed_query_types:
            raise ValueError(f"Query type '{query_type.value}' not allowed")
        
        # Validate filters (SQL injection prevention)
        if filters:
            self._validate_filters(filters)
        
        # Validate group_by
        if group_by:
            self._validate_group_by(group_by, entity)
        
        # Validate limit
        if limit is not None:
            if limit > 10000:
                raise ValueError(f"Limit {limit} exceeds maximum of 10000")
        
        return AnalyticsQuery(
            entity=entity,
            metric=metric,
            query_type=query_type,
            filters=filters or {},
            group_by=group_by,
            time_range=time_range,
            limit=limit,
            user_id=user_id
        )
    
    def execute_query(self, query: AnalyticsQuery) -> AnalyticsResult:
        """
        Execute analytics query safely
        
        Args:
            query: AnalyticsQuery to execute
            
        Returns:
            AnalyticsResult with data
        """
        start_time = datetime.now()
        
        try:
            # Convert query to database query
            db_query = self._convert_to_database_query(query)
            
            # Execute database query
            if self.database_query_func:
                db_result = self.database_query_func(db_query)
            else:
                # Placeholder - return empty result
                db_result = {'data': [], 'count': 0}
            
            # Process result
            result = self._process_result(db_result, query)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log query
            self.query_history.append({
                'timestamp': datetime.now().isoformat(),
                'query_id': query.query_id,
                'entity': query.entity,
                'metric': query.metric.value,
                'query_type': query.query_type.value,
                'success': True,
                'execution_time_ms': execution_time
            })
            
            return AnalyticsResult(
                query_id=query.query_id,
                success=True,
                result=result,
                row_count=db_result.get('count', 0),
                execution_time_ms=execution_time,
                data_source="database"
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.error(f"Error executing query {query.query_id}: {str(e)}")
            
            self.query_history.append({
                'timestamp': datetime.now().isoformat(),
                'query_id': query.query_id,
                'entity': query.entity,
                'metric': query.metric.value,
                'query_type': query.query_type.value,
                'success': False,
                'error': str(e)
            })
            
            return AnalyticsResult(
                query_id=query.query_id,
                success=False,
                result=None,
                row_count=0,
                execution_time_ms=execution_time,
                error=str(e),
                confidence="low"
            )
    
    def _validate_filters(self, filters: Dict):
        """Validate filters to prevent SQL injection"""
        # Only allow specific filter keys
        allowed_filter_keys = {
            'property': ['governorate', 'district', 'property_type', 'price_min', 'price_max', 
                         'area_min', 'area_max', 'rooms_min', 'rooms_max', 'status'],
            'agent': ['governorate', 'district', 'verification_status', 'specialization'],
            'user': ['user_id', 'role', 'created_after']
        }
        
        for key in filters.keys():
            if key not in allowed_filter_keys.get('property', []):
                # Try to find in other entities
                found = False
                for entity, keys in allowed_filter_keys.items():
                    if key in keys:
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"Filter key '{key}' not allowed")
    
    def _validate_group_by(self, group_by: List[str], entity: str):
        """Validate group_by fields"""
        allowed_group_by = {
            'property': ['governorate', 'district', 'property_type', 'rooms'],
            'agent': ['governorate', 'district', 'specialization']
        }
        
        for field in group_by:
            if field not in allowed_group_by.get(entity, []):
                raise ValueError(f"Group by field '{field}' not allowed for entity '{entity}'")
    
    def _convert_to_database_query(self, query: AnalyticsQuery) -> Dict:
        """Convert analytics query to database query parameters"""
        db_query = {
            'entity': query.entity,
            'metric': query.metric.value,
            'query_type': query.query_type.value,
            'filters': query.filters,
            'group_by': query.group_by,
            'time_range': query.time_range,
            'limit': query.limit
        }
        
        return db_query
    
    def _process_result(self, db_result: Dict, query: AnalyticsQuery) -> Any:
        """Process database result based on query type"""
        data = db_result.get('data', [])
        
        if query.query_type == QueryType.COUNT:
            return {'count': len(data)}
        
        elif query.query_type == QueryType.AVG:
            values = [item.get(query.metric.value) for item in data if item.get(query.metric.value)]
            if values:
                return {'average': sum(values) / len(values)}
            return {'average': None}
        
        elif query.query_type == QueryType.MEDIAN:
            values = [item.get(query.metric.value) for item in data if item.get(query.metric.value)]
            if values:
                values.sort()
                return {'median': values[len(values) // 2]}
            return {'median': None}
        
        elif query.query_type == QueryType.MIN:
            values = [item.get(query.metric.value) for item in data if item.get(query.metric.value)]
            return {'min': min(values) if values else None}
        
        elif query.query_type == QueryType.MAX:
            values = [item.get(query.metric.value) for item in data if item.get(query.metric.value)]
            return {'max': max(values) if values else None}
        
        elif query.query_type == QueryType.DISTRIBUTION:
            values = [item.get(query.metric.value) for item in data if item.get(query.metric.value)]
            if values:
                values.sort()
                return {
                    'q1': values[len(values) // 4],
                    'q2': values[len(values) // 2],
                    'q3': values[len(values) * 3 // 4]
                }
            return {'q1': None, 'q2': None, 'q3': None}
        
        else:
            return {'data': data}
    
    def explain_query(self, query: AnalyticsQuery) -> str:
        """Generate human-readable explanation of query"""
        entity_name = "العقارات" if query.entity == "property" else query.entity
        
        metric_names = {
            MetricType.PRICE: "السعر",
            MetricType.AREA: "المساحة",
            MetricType.ROOMS: "الغرف",
            MetricType.PRICE_PER_M2: "السعر لكل متر مربع"
        }
        
        metric_name = metric_names.get(query.metric, query.metric.value)
        
        query_type_names = {
            QueryType.COUNT: "عدد",
            QueryType.AVG: "المتوسط",
            QueryType.MEDIAN: "الوسيط",
            QueryType.MIN: "الحد الأدنى",
            QueryType.MAX: "الحد الأقصى"
        }
        
        query_type_name = query_type_names.get(query.query_type, query.query_type.value)
        
        explanation = f"حساب {query_type_name} {metric_name} لـ{entity_name}"
        
        if query.filters:
            filter_desc = " مع الفلات: " + ", ".join([f"{k}={v}" for k, v in query.filters.items()])
            explanation += filter_desc
        
        return explanation
    
    def get_query_statistics(self) -> Dict:
        """Get statistics about executed queries"""
        total_queries = len(self.query_history)
        successful_queries = sum(1 for q in self.query_history if q.get('success'))
        
        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': total_queries - successful_queries,
            'average_execution_time_ms': sum(q.get('execution_time_ms', 0) for q in self.query_history) / total_queries if total_queries > 0 else 0
        }


# Global instance
safe_analytics_layer = SafeAnalyticsQueryLayer()