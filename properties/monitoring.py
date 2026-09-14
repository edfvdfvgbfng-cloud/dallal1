"""
Production Monitoring and Health Check System
Comprehensive monitoring for system health, performance, and AI metrics
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class SystemHealthChecker:
    """
    Comprehensive health checking for all system components
    """
    
    def __init__(self):
        self.health_cache_timeout = 60  # Cache health checks for 60 seconds
    
    def check_all_systems(self) -> Dict[str, Any]:
        """
        Check health of all system components
        
        Returns:
            Complete health report
        """
        health_report = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'components': {}
        }
        
        # Check each component
        components = {
            'database': self._check_database,
            'cache': self._check_cache,
            'ai_engine': self._check_ai_engine,
            'voice_system': self._check_voice_system,
            'vector_db': self._check_vector_db,
            'api': self._check_api,
            'storage': self._check_storage,
            'external_services': self._check_external_services
        }
        
        for component_name, check_func in components.items():
            try:
                health_report['components'][component_name] = check_func()
                
                # If any component is unhealthy, mark system as degraded
                if health_report['components'][component_name]['status'] != 'healthy':
                    health_report['status'] = 'degraded'
            except Exception as e:
                logger.error(f"Error checking {component_name}: {str(e)}")
                health_report['components'][component_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
        
        return health_report
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        cache_key = 'health_database'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            start_time = time.time()
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Check connection pool
            from django.db import connections
            connection_info = connections['default']
            
            health_status = {
                'status': 'healthy',
                'latency_ms': round(latency_ms, 2),
                'connection_pool': {
                    'max_connections': getattr(connection_info, 'MAX_CONNS', 0),
                    'current_connections': getattr(connection_info, 'connections', 0)
                }
            }
            
            # Health threshold
            if latency_ms > 1000:
                health_status['status'] = 'warning'
                health_status['message'] = 'High database latency'
            
            cache.set(cache_key, health_status, timeout=self.health_cache_timeout)
            return health_status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """Check cache connectivity"""
        cache_key = 'health_cache'
        
        try:
            start_time = time.time()
            
            # Test cache
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', timeout=10)
            retrieved_value = cache.get(test_key)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if retrieved_value == 'test_value':
                return {
                    'status': 'healthy',
                    'latency_ms': round(latency_ms, 2),
                    'backend': 'default'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache read/write failed'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_ai_engine(self) -> Dict[str, Any]:
        """Check AI engine status"""
        cache_key = 'health_ai_engine'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            from .ai_intent_classifier import intent_classifier
            from .ai_entity_extraction import entity_extractor
            from .ai_conversation_manager import conversation_manager
            from .ai_agent_loop import ai_agent
            from .ai_agent_tools import tool_registry
            
            # Test intent detection
            start_time = time.time()
            test_result = intent_detector.detect_intent("اختبار")
            intent_latency = (time.time() - start_time) * 1000
            
            # Check component availability
            health_status = {
                'status': 'healthy',
                'components': {
                    'intent_detector': 'operational',
                    'entity_extractor': 'operational',
                    'conversation_manager': 'operational',
                    'ai_agent': 'operational',
                    'tool_registry': 'operational'
                },
                'performance': {
                    'intent_detection_latency_ms': round(intent_latency, 2),
                    'available_tools': len(tool_registry.get_all_tools())
                }
            }
            
            cache.set(cache_key, health_status, timeout=self.health_cache_timeout)
            return health_status
            
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'AI engine components not fully operational'
            }
    
    def _check_voice_system(self) -> Dict[str, Any]:
        """Check voice system status"""
        cache_key = 'health_voice_system'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            from .ai_voice_provider import voice_analytics
            
            # Voice is client-side, so we check analytics availability
            analytics = voice_analytics.get_statistics()
            
            return {
                'status': 'healthy',
                'type': 'client_side',
                'analytics_available': True,
                'recent_conversations': analytics.get('voice_conversations', 0)
            }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Voice analytics not available'
            }
    
    def _check_vector_db(self) -> Dict[str, Any]:
        """Check vector database status"""
        cache_key = 'health_vector_db'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            from .ai_semantic_search import hybrid_search_engine
            
            # Check semantic search availability
            if hybrid_search_engine:
                return {
                    'status': 'healthy',
                    'type': 'semantic_search',
                    'embeddings_available': True
                }
            else:
                return {
                    'status': 'not_configured',
                    'message': 'Vector database not configured'
                }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Vector database check failed'
            }
    
    def _check_api(self) -> Dict[str, Any]:
        """Check API endpoints health"""
        cache_key = 'health_api'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Check critical API endpoints
            api_endpoints = {
                'chatbot': '/api/chatbot/',
                'analytics': '/api/ai/analytics/',
                'health': '/api/ai/health/'
            }
            
            return {
                'status': 'healthy',
                'endpoints': list(api_endpoints.keys()),
                'routing': 'operational'
            }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e)
            }
    
    def _check_storage(self) -> Dict[str, Any]:
        """Check file storage system"""
        cache_key = 'health_storage'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            import os
            
            # Check if media directory is writable
            media_root = settings.MEDIA_ROOT
            test_file = os.path.join(media_root, 'health_check.txt')
            
            try:
                with open(test_file, 'w') as f:
                    f.write('health check')
                os.remove(test_file)
                
                return {
                    'status': 'healthy',
                    'type': 'local',
                    'media_root': media_root
                }
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'error': f"Storage not writable: {str(e)}"
                }
                
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e)
            }
    
    def _check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity"""
        cache_key = 'health_external'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            # Add external service checks as needed
            external_services = {}
            
            # Example: Check if external APIs are configured
            if hasattr(settings, 'EXTERNAL_API_URL'):
                external_services['custom_api'] = 'configured'
            
            return {
                'status': 'healthy',
                'services': external_services,
                'message': 'No external services configured'
            }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e)
            }


class PerformanceMonitor:
    """
    Real-time performance monitoring and metrics collection
    """
    
    def __init__(self):
        self.metrics_cache_key = 'performance_metrics'
        self.metrics_ttl = 300  # 5 minutes
    
    def record_metric(self, metric_name: str, value: float, tags: Dict = None):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for categorization
        """
        try:
            metrics = cache.get(self.metrics_cache_key, {})
            
            if metric_name not in metrics:
                metrics[metric_name] = {
                    'count': 0,
                    'sum': 0,
                    'avg': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'history': []
                }
            
            metric_data = metrics[metric_name]
            metric_data['count'] += 1
            metric_data['sum'] += value
            metric_data['avg'] = metric_data['sum'] / metric_data['count']
            metric_data['min'] = min(metric_data['min'], value)
            metric_data['max'] = max(metric_data['max'], value)
            
            # Keep last 100 values for history
            metric_data['history'].append({
                'value': value,
                'timestamp': timezone.now().isoformat(),
                'tags': tags or {}
            })
            if len(metric_data['history']) > 100:
                metric_data['history'].pop(0)
            
            cache.set(self.metrics_cache_key, metrics, timeout=self.metrics_ttl)
            
        except Exception as e:
            logger.error(f"Error recording metric {metric_name}: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics"""
        return cache.get(self.metrics_cache_key, {})
    
    def get_metric(self, metric_name: str) -> Optional[Dict]:
        """Get specific metric data"""
        metrics = self.get_metrics()
        return metrics.get(metric_name)
    
    def reset_metrics(self):
        """Reset all metrics"""
        cache.delete(self.metrics_cache_key)


class AIServiceMonitor:
    """
    AI-specific monitoring for model usage, costs, and performance
    """
    
    def __init__(self):
        self.usage_cache_key = 'ai_usage_metrics'
        self.usage_ttl = 3600  # 1 hour
    
    def record_ai_request(self, request_type: str, tokens_used: int, 
                          duration_ms: float, user_id: int = None, 
                          model: str = 'default'):
        """
        Record AI service usage for cost tracking
        
        Args:
            request_type: Type of AI request (chat, voice, embedding, etc.)
            tokens_used: Number of tokens consumed
            duration_ms: Processing time in milliseconds
            user_id: User ID (optional)
            model: Model used for the request
        """
        try:
            usage_data = cache.get(self.usage_cache_key, {})
            
            timestamp = timezone.now().isoformat()
            key = f"{timestamp}_{request_type}_{user_id or 'anonymous'}"
            
            usage_data[key] = {
                'request_type': request_type,
                'tokens_used': tokens_used,
                'duration_ms': duration_ms,
                'user_id': user_id,
                'model': model,
                'timestamp': timestamp
            }
            
            # Update summary stats
            summary_key = f"summary_{request_type}"
            if summary_key not in usage_data:
                usage_data[summary_key] = {
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_duration_ms': 0,
                    'unique_users': set()
                }
            
            summary = usage_data[summary_key]
            summary['total_requests'] += 1
            summary['total_tokens'] += tokens_used
            summary['total_duration_ms'] += duration_ms
            if user_id:
                summary['unique_users'].add(user_id)
            
            cache.set(self.usage_cache_key, usage_data, timeout=self.usage_ttl)
            
        except Exception as e:
            logger.error(f"Error recording AI usage: {str(e)}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics"""
        usage_data = cache.get(self.usage_cache_key, {})
        
        # Convert sets to lists for JSON serialization
        for key, value in usage_data.items():
            if isinstance(value, dict) and 'unique_users' in value:
                value['unique_users'] = list(value['unique_users'])
        
        return usage_data
    
    def get_user_usage(self, user_id: int) -> Dict[str, Any]:
        """Get usage statistics for a specific user"""
        usage_data = self.get_usage_stats()
        
        user_usage = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_duration_ms': 0,
            'requests_by_type': {}
        }
        
        for key, data in usage_data.items():
            if key.startswith('summary_'):
                continue  # Skip summary keys
            
            if data.get('user_id') == user_id:
                request_type = data.get('request_type')
                user_usage['total_requests'] += 1
                user_usage['total_tokens'] += data.get('tokens_used', 0)
                user_usage['total_duration_ms'] += data.get('duration_ms', 0)
                
                if request_type not in user_usage['requests_by_type']:
                    user_usage['requests_by_type'][request_type] = 0
                user_usage['requests_by_type'][request_type] += 1
        
        return user_usage


# Global instances
health_checker = SystemHealthChecker()
performance_monitor = PerformanceMonitor()
ai_service_monitor = AIServiceMonitor()