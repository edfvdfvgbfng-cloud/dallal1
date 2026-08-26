"""
Comprehensive Testing Suite for Production-Grade AI Platform
Unit tests, integration tests, and end-to-end tests
"""

import json
import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from .models import Property, Broker, JobPosting
from .ai_intent_detection import intent_detector
from .ai_entity_extraction import entity_extractor
from .ai_conversation_manager import conversation_manager
from .ai_agent_loop import ai_agent
from .ai_agent_tools import tool_registry
from .feature_flags import feature_flags
from .monitoring import health_checker, performance_monitor, ai_service_monitor
from .middleware import RateLimitMiddleware, AICostControlMiddleware


class AIIntentDetectionTests(TestCase):
    """Unit tests for AI intent detection"""
    
    def setUp(self):
        self.test_cases = [
            ("أريد بيت بالبصرة", "buy_property"),
            ("عندي دار وأريد أبيعه", "sell_property"),
            ("أريد شغل ببغداد", "find_job"),
            ("كيف أسجل دلال؟", "join_agent"),
            ("فندق في النجف", "find_hotel"),
            ("أريد خدمة البناء", "find_service"),
        ]
    
    def test_intent_detection_accuracy(self):
        """Test intent detection accuracy"""
        correct = 0
        total = len(self.test_cases)
        
        for text, expected_intent in self.test_cases:
            result = intent_detector.detect_intent(text)
            if result.get('intent') == expected_intent:
                correct += 1
        
        accuracy = correct / total
        self.assertGreater(accuracy, 0.8, f"Intent detection accuracy {accuracy} is below threshold")
    
    def test_confidence_scores(self):
        """Test confidence scores are valid"""
        for text, _ in self.test_cases:
            result = intent_detector.detect_intent(text)
            confidence = result.get('confidence', 0)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
    
    def test_unknown_queries(self):
        """Test handling of unknown queries"""
        unknown_query = "xyz random text 123"
        result = intent_detector.detect_intent(unknown_query)
        self.assertEqual(result.get('intent'), 'unknown')


class AIEntityExtractionTests(TestCase):
    """Unit tests for AI entity extraction"""
    
    def test_price_extraction(self):
        """Test price entity extraction"""
        test_cases = [
            ("150 مليون", 150000000),
            ("مئة وخمسين مليون", 150000000),
            ("200,000,000", 200000000),
        ]
        
        for text, expected_price in test_cases:
            entities = entity_extractor.extract_entities(text)
            self.assertEqual(entities.get('price'), expected_price)
    
    def test_location_extraction(self):
        """Test location entity extraction"""
        test_cases = [
            ("بيت بالبصرة", "البصرة"),
            ("عقار في بغداد", "بغداد"),
            ("شقة في النجف", "النجف"),
        ]
        
        for text, expected_location in test_cases:
            entities = entity_extractor.extract_entities(text)
            self.assertEqual(entities.get('governorate'), expected_location)
    
    def test_property_type_extraction(self):
        """Test property type extraction"""
        test_cases = [
            ("أريد بيت", "house"),
            ("أريد شقة", "apartment"),
            ("أرض للبناء", "land"),
        ]
        
        for text, expected_type in test_cases:
            entities = entity_extractor.extract_entities(text)
            self.assertEqual(entities.get('property_type'), expected_type)


class ConversationManagerTests(TestCase):
    """Unit tests for conversation manager"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.conversation_id = "test_conversation_123"
    
    def test_conversation_state_persistence(self):
        """Test conversation state is persisted correctly"""
        state = {
            'intent': 'buy_property',
            'entities': {'price': 150000000, 'governorate': 'البصرة'},
            'context': {'step': 'budget'}
        }
        
        conversation_manager.save_conversation_state(self.conversation_id, state)
        retrieved_state = conversation_manager.get_conversation_state(self.conversation_id)
        
        self.assertEqual(retrieved_state['intent'], state['intent'])
        self.assertEqual(retrieved_state['entities']['price'], state['entities']['price'])
    
    def test_conversation_context_management(self):
        """Test conversation context is managed correctly"""
        message = "أريد بيت بالبصرة"
        response = conversation_manager.process_message(
            message=message,
            conversation_id=self.conversation_id,
            user=self.user
        )
        
        self.assertIn('response', response)
        self.assertIn('intent', response)
        self.assertIsNotNone(response.get('conversation_id'))


class AgentToolTests(TestCase):
    """Unit tests for AI agent tools"""
    
    def test_tool_registry_initialization(self):
        """Test tool registry is properly initialized"""
        tools = tool_registry.get_all_tools()
        self.assertIsInstance(tools, dict)
        self.assertGreater(len(tools), 0)
    
    def test_tool_execution(self):
        """Test tool execution with valid parameters"""
        test_tool = tool_registry.get_tool('search_properties')
        if test_tool:
            result = test_tool({'governorate': 'البصرة', 'price': 150000000})
            self.assertIn('results', result)
    
    def test_tool_error_handling(self):
        """Test tool error handling"""
        test_tool = tool_registry.get_tool('search_properties')
        if test_tool:
            result = test_tool({'invalid_param': 'value'})
            self.assertIn('error', result)


class FeatureFlagsTests(TestCase):
    """Unit tests for feature flags system"""
    
    def test_default_flags(self):
        """Test default feature flags are loaded"""
        flags = feature_flags.get_all_flags()
        self.assertIsInstance(flags, dict)
        self.assertIn('voice_ai', flags)
        self.assertIn('property_ai', flags)
    
    def test_flag_enable_disable(self):
        """Test enabling and disabling flags"""
        feature_flags.enable_feature('test_flag', ttl=60)
        self.assertTrue(feature_flags.is_enabled('test_flag'))
        
        feature_flags.disable_feature('test_flag', ttl=60)
        self.assertFalse(feature_flags.is_enabled('test_flag'))
    
    def test_user_specific_flags(self):
        """Test user-specific flag overrides"""
        user = User.objects.create_user(username='flaguser', password='testpass')
        
        feature_flags.set_user_specific_flag(user, 'test_feature', True)
        self.assertTrue(feature_flags.is_enabled('test_feature', user))
        
        feature_flags.set_user_specific_flag(user, 'test_feature', False)
        self.assertFalse(feature_flags.is_enabled('test_feature', user))


class MonitoringTests(TestCase):
    """Unit tests for monitoring system"""
    
    def test_health_checker_all_systems(self):
        """Test health checker examines all systems"""
        health_report = health_checker.check_all_systems()
        
        self.assertIn('status', health_report)
        self.assertIn('components', health_report)
        self.assertIn('database', health_report['components'])
        self.assertIn('cache', health_report['components'])
    
    def test_performance_monitoring(self):
        """Test performance metrics recording"""
        performance_monitor.record_metric('test_metric', 123.45, {'tag': 'test'})
        
        metrics = performance_monitor.get_metrics()
        self.assertIn('test_metric', metrics)
        
        metric_data = metrics['test_metric']
        self.assertEqual(metric_data['count'], 1)
        self.assertEqual(metric_data['sum'], 123.45)
    
    def test_ai_service_monitoring(self):
        """Test AI service usage monitoring"""
        user = User.objects.create_user(username='aimonuser', password='testpass')
        
        ai_service_monitor.record_ai_request(
            request_type='chat',
            tokens_used=100,
            duration_ms=500,
            user_id=user.id,
            model='test_model'
        )
        
        usage_stats = ai_service_monitor.get_user_usage(user.id)
        self.assertEqual(usage_stats['total_requests'], 1)
        self.assertEqual(usage_stats['total_tokens'], 100)


class MiddlewareTests(TestCase):
    """Unit tests for middleware components"""
    
    def test_rate_limiting(self):
        """Test rate limiting middleware"""
        client = Client()
        
        # Make multiple requests to test rate limiting
        for i in range(110):  # Above default limit of 100
            response = client.get('/api/chatbot/')
            if i >= 100:
                self.assertEqual(response.status_code, 429)
    
    def test_security_headers(self):
        """Test security headers middleware"""
        client = Client()
        response = client.get('/')
        
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)


class APIIntegrationTests(APITestCase):
    """Integration tests for API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_ai_chat_api(self):
        """Test AI chat API endpoint"""
        url = reverse('ai_chat_production_api')
        data = {
            'message': 'أريد بيت بالبصرة',
            'conversation_id': 'test_conv_123',
            'is_voice': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('success', response_data)
        self.assertIn('data', response_data)
    
    def test_conversation_persistence_api(self):
        """Test conversation persistence API"""
        url = reverse('ai_conversation_persistence_api')
        data = {
            'conversation_id': 'test_conv_456',
            'state': {'intent': 'buy_property', 'step': 'budget'}
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_saved_search_api(self):
        """Test saved search API"""
        url = reverse('ai_saved_search_api')
        data = {
            'criteria': {'governorate': 'البصرة', 'price': 150000000},
            'name': 'بحث البصرة'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_property_comparison_api(self):
        """Test property comparison API"""
        # Create test properties
        prop1 = Property.objects.create(
            title='Property 1',
            price=150000000,
            area=250,
            governorate='البصرة',
            district='العشار',
            property_type='house',
            user=self.user
        )
        prop2 = Property.objects.create(
            title='Property 2',
            price=200000000,
            area=300,
            governorate='البصرة',
            district='المعقل',
            property_type='house',
            user=self.user
        )
        
        url = reverse('ai_property_comparison_api')
        data = {'property_ids': [prop1.id, prop2.id]}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('comparison', response_data['data'])
        self.assertEqual(len(response_data['data']['comparison']), 2)


class EndToEndTests(TestCase):
    """End-to-end tests for complete user flows"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='e2euser', password='testpass')
        self.client = Client()
        self.client.login(username='e2euser', password='testpass')
    
    def test_complete_property_search_flow(self):
        """Test complete property search flow"""
        # Step 1: User initiates search
        response = self.client.post('/api/chatbot/', {
            'message': 'أريد بيت بالبصرة',
            'conversation_id': 'e2e_test_1'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 2: User provides budget
        response = self.client.post('/api/chatbot/', {
            'message': '150 مليون',
            'conversation_id': 'e2e_test_1'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 3: User provides district
        response = self.client.post('/api/chatbot/', {
            'message': 'العشار',
            'conversation_id': 'e2e_test_1'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Save search
        response = self.client.post('/api/ai/saved-search/', {
            'criteria': {'governorate': 'البصرة', 'price': 150000000, 'district': 'العشار'},
            'name': 'بحث اختبار'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_voice_interaction_flow(self):
        """Test voice interaction flow"""
        if feature_flags.is_enabled('voice_ai'):
            response = self.client.post('/api/chatbot/', {
                'message': 'أريد بيت بالبصرة',
                'conversation_id': 'voice_test_1',
                'is_voice': True
            })
            self.assertEqual(response.status_code, 200)
            
            response_data = response.json()
            self.assertIn('data', response_data)
            self.assertIn('metadata', response_data['data'])
    
    def test_error_recovery_flow(self):
        """Test error recovery in user flows"""
        # Send invalid request
        response = self.client.post('/api/chatbot/', {
            'message': '',
            'conversation_id': 'error_test_1'
        })
        
        # Should still get valid response with error handling
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('success', response_data)


class PerformanceTests(TestCase):
    """Performance tests for critical operations"""
    
    def test_intent_detection_performance(self):
        """Test intent detection meets performance requirements"""
        start_time = time.time()
        
        for i in range(100):
            intent_detector.detect_intent("أريد بيت بالبصرة")
        
        duration = time.time() - start_time
        avg_time = duration / 100
        
        self.assertLess(avg_time, 0.1, "Intent detection too slow")
    
    def test_entity_extraction_performance(self):
        """Test entity extraction meets performance requirements"""
        start_time = time.time()
        
        for i in range(100):
            entity_extractor.extract_entities("أريد بيت بالبصرة بـ150 مليون")
        
        duration = time.time() - start_time
        avg_time = duration / 100
        
        self.assertLess(avg_time, 0.1, "Entity extraction too slow")
    
    def test_api_response_time(self):
        """Test API response time meets requirements"""
        user = User.objects.create_user(username='perfuser', password='testpass')
        client = Client()
        client.login(username='perfuser', password='testpass')
        
        start_time = time.time()
        response = client.post('/api/chatbot/', {
            'message': 'أريد بيت بالبصرة',
            'conversation_id': 'perf_test_1'
        })
        duration = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 2.0, "API response time too slow")


class SecurityTests(TestCase):
    """Security tests for the platform"""
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        malicious_input = "أريد بيت'; DROP TABLE properties; --"
        response = self.client.post('/api/chatbot/', {
            'message': malicious_input,
            'conversation_id': 'security_test_1'
        })
        
        # Should handle gracefully without SQL errors
        self.assertEqual(response.status_code, 200)
    
    def test_xss_protection(self):
        """Test XSS protection"""
        xss_input = "<script>alert('xss')</script>أريد بيت"
        response = self.client.post('/api/chatbot/', {
            'message': xss_input,
            'conversation_id': 'security_test_2'
        })
        
        response_data = response.json()
        # Should not contain raw script tags in response
        self.assertNotIn('<script>', str(response_data))
    
    def test_authentication_required(self):
        """Test authentication is required for protected endpoints"""
        client = Client()  # Not authenticated
        
        response = client.post('/api/ai/saved-search/', {
            'criteria': {'governorate': 'البصرة'},
            'name': 'test'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to login


class DatabaseTests(TestCase):
    """Database optimization and query tests"""
    
    def test_query_optimization(self):
        """Test database queries are optimized"""
        from django.db import connection
        from django.test.utils import override_settings
        
        # Enable query logging
        with override_settings(DEBUG=True):
            # Clear query log
            connection.queries_log.clear()
            
            # Perform search
            properties = Property.objects.filter(
                governororate='البصرة',
                price__lte=200000000
            ).select_related('user').prefetch_related('images')
            
            # Check query count
            query_count = len(connection.queries)
            self.assertLess(query_count, 5, "Too many database queries")
    
    def test_index_usage(self):
        """Test database indexes are being used"""
        # This would require database analysis tools
        # Placeholder for index usage verification
        pass


class ArabicProcessingTests(TestCase):
    """Arabic language processing tests"""
    
    def test_arabic_text_normalization(self):
        """Test Arabic text normalization"""
        from .ai_arabic_normalizer import normalize_arabic_text
        
        test_cases = [
            ("بغداذ", "بغداد"),
            ("البصره", "البصرة"),
            ("الناصره", "الناصرية"),
        ]
        
        for input_text, expected_output in test_cases:
            result = normalize_arabic_text(input_text)
            self.assertEqual(result, expected_output)
    
    def test_arabic_number_conversion(self):
        """Test Arabic number conversion"""
        from .ai_arabic_normalizer import convert_arabic_numbers
        
        test_cases = [
            ("٠١٢٣", "0123"),
            ("مئة", "100"),
            ("مليون", "1000000"),
        ]
        
        for input_text, expected_output in test_cases:
            result = convert_arabic_numbers(input_text)
            self.assertEqual(result, expected_output)


if __name__ == '__main__':
    import django
    django.setup()
    
    # Run all tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
    
    if failures:
        print(f"Tests failed: {failures}")
    else:
        print("All tests passed!")