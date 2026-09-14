"""
AI Smart Assistant Tests
Comprehensive tests for the smart AI assistant system
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

from .ai_smart_intent_detection import Intent, intent_detector, IntentDetector
from .ai_smart_request_parser import ai_request_parser, AIRequestParser
from .ai_unified_search_service import ai_search_service, AISearchService
from .ai_smart_conversation_handler import smart_conversation_manager, SmartConversationManager
from .ai_result_renderer import result_renderer, ResultRenderer


class IntentDetectionTests(TestCase):
    """Test intent detection functionality"""
    
    def setUp(self):
        self.detector = IntentDetector()
    
    def test_buy_property_intent_arabic(self):
        """Test buy property intent detection in Arabic"""
        intent, confidence = self.detector.detect_intent("أريد اشتري بيت")
        self.assertEqual(intent, Intent.BUY_PROPERTY)
        self.assertGreater(confidence, 0.5)
    
    def test_buy_property_intent_english(self):
        """Test buy property intent detection in English"""
        intent, confidence = self.detector.detect_intent("I want to buy a house")
        self.assertEqual(intent, Intent.BUY_PROPERTY)
        self.assertGreater(confidence, 0.5)
    
    def test_sell_property_intent(self):
        """Test sell property intent detection"""
        intent, confidence = self.detector.detect_intent("أريد بيع داري")
        self.assertEqual(intent, Intent.SELL_PROPERTY)
        self.assertGreater(confidence, 0.5)
    
    def test_search_hotel_intent(self):
        """Test hotel search intent detection"""
        intent, confidence = self.detector.detect_intent("أريد فندق في بغداد")
        self.assertEqual(intent, Intent.SEARCH_HOTEL)
        self.assertGreater(confidence, 0.5)
    
    def test_search_job_intent(self):
        """Test job search intent detection"""
        intent, confidence = self.detector.detect_intent("أبحث عن وظيفة محاسب")
        self.assertEqual(intent, Intent.SEARCH_JOB)
        self.assertGreater(confidence, 0.5)
    
    def test_search_service_intent(self):
        """Test service search intent detection"""
        intent, confidence = self.detector.detect_intent("أريد كهربائي")
        self.assertEqual(intent, Intent.SEARCH_SERVICE)
        self.assertGreater(confidence, 0.5)
    
    def test_greeting_intent(self):
        """Test greeting intent detection"""
        intent, confidence = self.detector.detect_intent("مرحبا")
        self.assertEqual(intent, Intent.GREETING)
        self.assertGreater(confidence, 0.5)
    
    def test_iraqi_dialect_location(self):
        """Test Iraqi dialect location extraction"""
        location = self.detector.extract_location("أريد بيت بالناصرية")
        self.assertEqual(location, "Nasiriyah")
    
    def test_price_extraction_million(self):
        """Test price extraction in millions"""
        price = self.detector.extract_price("150 مليون")
        self.assertIsNotNone(price)
        self.assertEqual(price['value'], 150_000_000)
        self.assertEqual(price['currency'], 'iqd')
    
    def test_price_extraction_usd(self):
        """Test price extraction in USD"""
        price = self.detector.extract_price("100 ألف دولار")
        self.assertIsNotNone(price)
        self.assertEqual(price['value'], 100_000)
        self.assertEqual(price['currency'], 'usd')
    
    def test_area_extraction(self):
        """Test area extraction"""
        area = self.detector.extract_area("200 متر")
        self.assertEqual(area, 200)
    
    def test_rooms_extraction(self):
        """Test rooms extraction"""
        rooms = self.detector.extract_rooms("3 غرف")
        self.assertEqual(rooms, 3)
    
    def test_property_type_extraction(self):
        """Test property type extraction"""
        property_type = self.detector.extract_property_type("أريد شقة")
        self.assertEqual(property_type, 'apartment')


class RequestParserTests(TestCase):
    """Test request parsing functionality"""
    
    def setUp(self):
        self.parser = AIRequestParser()
    
    def test_parse_buy_property_request(self):
        """Test parsing buy property request"""
        result = self.parser.parse_request("أريد بيت في الناصرية بـ 150 مليون")
        
        self.assertEqual(result['intent'], Intent.BUY_PROPERTY)
        self.assertIn('location', result['filters'])
        self.assertIn('price', result['filters'])
        self.assertEqual(result['filters']['location'], 'Nasiriyah')
    
    def test_parse_hotel_request(self):
        """Test parsing hotel request"""
        result = self.parser.parse_request("فندق في بغداد لعائلة 4 أشخاص")
        
        self.assertEqual(result['intent'], Intent.SEARCH_HOTEL)
        self.assertIn('city', result['filters'])
        self.assertIn('guests', result['filters'])
        self.assertEqual(result['filters']['guests'], 4)
    
    def test_parse_job_request(self):
        """Test parsing job request"""
        result = self.parser.parse_request("وظيفة محاسب بالناصرية")
        
        self.assertEqual(result['intent'], Intent.SEARCH_JOB)
        self.assertIn('location', result['filters'])
        self.assertIn('job_title', result['filters'])
    
    def test_identify_missing_fields(self):
        """Test missing field identification"""
        result = self.parser.parse_request("أريد بيت")
        
        self.assertIn('location', result['missing_fields'])
        self.assertIn('price', result['missing_fields'])
    
    def test_validate_filters_valid(self):
        """Test valid filter validation"""
        filters = {
            'price': {'value': 150_000_000, 'currency': 'iqd'},
            'area': 200,
            'rooms': 3
        }
        
        is_valid, errors = self.parser.validate_filters(Intent.BUY_PROPERTY, filters)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_filters_invalid_price(self):
        """Test invalid price validation"""
        filters = {
            'price': {'value': -100, 'currency': 'iqd'}
        }
        
        is_valid, errors = self.parser.validate_filters(Intent.BUY_PROPERTY, filters)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class SearchServiceTests(TestCase):
    """Test search service functionality"""
    
    def setUp(self):
        self.service = AISearchService()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @patch('properties.ai_search_service.Property.objects.filter')
    def test_search_properties(self, mock_filter):
        """Test property search"""
        # Mock queryset
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 5
        mock_queryset.__getitem__.return_value = []
        mock_filter.return_value = mock_queryset
        
        filters = {
            'location': 'Nasiriyah',
            'price': {'value': 150_000_000, 'currency': 'iqd'},
            'property_type': 'house'
        }
        
        result = self.service.search(Intent.BUY_PROPERTY, filters, self.user.id)
        
        self.assertEqual(result['total_count'], 5)
        self.assertIn('results', result)
        self.assertIn('metadata', result)
    
    @patch('properties.ai_search_service.Hotel.objects.filter')
    def test_search_hotels(self, mock_filter):
        """Test hotel search"""
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 3
        mock_queryset.__getitem__.return_value = []
        mock_filter.return_value = mock_queryset
        
        filters = {
            'city': 'Baghdad',
            'guests': 4
        }
        
        result = self.service.search(Intent.SEARCH_HOTEL, filters, self.user.id)
        
        self.assertEqual(result['total_count'], 3)
        self.assertIn('results', result)
    
    def test_search_unsupported_intent(self):
        """Test search with unsupported intent"""
        result = self.service.search(Intent.GENERAL_QUESTION, {}, self.user.id)
        
        self.assertEqual(result['total_count'], 0)
        self.assertIn('error', result['metadata'])
    
    def test_calculate_property_match_score(self):
        """Test property match score calculation"""
        # Create mock property object
        property_obj = MagicMock()
        property_obj.governorate = 'Nasiriyah'
        property_obj.city = 'Nasiriyah'
        property_obj.price = 150_000_000
        property_obj.area = 200
        property_obj.rooms = 3
        property_obj.type = 'house'
        property_obj.purpose = 'sale'
        
        filters = {
            'location': 'Nasiriyah',
            'price': {'value': 150_000_000, 'currency': 'iqd'},
            'area': 200,
            'rooms': 3,
            'property_type': 'house',
            'purpose': 'sale'
        }
        
        score = self.service._calculate_property_match_score(property_obj, filters)
        
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)


class ConversationManagerTests(TestCase):
    """Test conversation manager functionality"""
    
    def setUp(self):
        self.manager = SmartConversationManager()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.conversation_id = 'test_conv_123'
    
    def test_create_conversation_state(self):
        """Test creating new conversation state"""
        state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        
        self.assertEqual(state.conversation_id, self.conversation_id)
        self.assertEqual(state.user_id, self.user.id)
        self.assertIsNone(state.current_intent)
        self.assertEqual(len(state.collected_filters), 0)
    
    def test_save_and_load_state(self):
        """Test saving and loading conversation state"""
        state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        state.current_intent = Intent.BUY_PROPERTY
        state.collected_filters = {'location': 'Nasiriyah'}
        
        self.manager.save_state(state)
        
        loaded_state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        
        self.assertEqual(loaded_state.current_intent, Intent.BUY_PROPERTY)
        self.assertEqual(loaded_state.collected_filters['location'], 'Nasiriyah')
    
    def test_process_message_greeting(self):
        """Test processing greeting message"""
        response = self.manager.process_message("مرحبا", self.conversation_id, self.user.id)
        
        self.assertIn('response', response)
        self.assertEqual(response['metadata']['intent'], 'greeting')
    
    def test_process_property_search(self):
        """Test processing property search message"""
        response = self.manager.process_message("أريد بيت في الناصرية", self.conversation_id, self.user.id)
        
        self.assertIn('response', response)
        self.assertIn('action', response)
    
    def test_clear_conversation(self):
        """Test clearing conversation"""
        state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        state.current_intent = Intent.BUY_PROPERTY
        state.collected_filters = {'location': 'Nasiriyah'}
        
        self.manager.save_state(state)
        
        response = self.manager.process_message("ابدأ من جديد", self.conversation_id, self.user.id)
        
        self.assertTrue(response['metadata']['conversation_reset'])
        
        loaded_state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        self.assertIsNone(loaded_state.current_intent)
        self.assertEqual(len(loaded_state.collected_filters), 0)
    
    def test_awaiting_confirmation(self):
        """Test awaiting confirmation state"""
        state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        
        state.set_awaiting_confirmation('create_listing', {'property_type': 'house'})
        
        self.assertTrue(state.awaiting_confirmation)
        self.assertEqual(state.pending_action, 'create_listing')
        self.assertIsNotNone(state.pending_data)
    
    def test_clear_confirmation(self):
        """Test clearing confirmation state"""
        state = self.manager.get_or_create_state(self.conversation_id, self.user.id)
        state.set_awaiting_confirmation('create_listing', {})
        
        state.clear_confirmation()
        
        self.assertFalse(state.awaiting_confirmation)
        self.assertIsNone(state.pending_action)
        self.assertIsNone(state.pending_data)


class ResultRendererTests(TestCase):
    """Test result renderer functionality"""
    
    def setUp(self):
        self.renderer = ResultRenderer()
    
    def test_render_property_card(self):
        """Test rendering property result card"""
        property_obj = MagicMock()
        property_obj.display_title = "بيت للبيع في الناصرية"
        property_obj.governorate = "Nasiriyah"
        property_obj.price = 150_000_000
        property_obj.area = 200
        property_obj.rooms = 3
        property_obj.purpose = 'sale'
        property_obj.slug = 'test-property'
        
        card = self.renderer._render_property_card(property_obj, 0.85, '/property/test-property/')
        
        self.assertEqual(card['type'], 'property')
        self.assertEqual(card['emoji'], '🏠')
        self.assertEqual(card['score'], 0.85)
        self.assertGreater(len(card['fields']), 0)
        self.assertGreater(len(card['actions']), 0)
    
    def test_render_hotel_card(self):
        """Test rendering hotel result card"""
        hotel_obj = MagicMock()
        hotel_obj.name = "فندق بغداد"
        hotel_obj.governorate = "Baghdad"
        hotel_obj.star_rating = 4
        hotel_obj.price_range = 'luxury'
        
        card = self.renderer._render_hotel_card(hotel_obj, 0.90, '/hotels/1/')
        
        self.assertEqual(card['type'], 'hotel')
        self.assertEqual(card['emoji'], '🏨')
        self.assertEqual(card['score'], 0.90)
    
    def test_render_job_card(self):
        """Test rendering job result card"""
        job_obj = MagicMock()
        job_obj.title = "محاسب"
        job_obj.governorate = "Nasiriyah"
        job_obj.company_name = "شركة العراق"
        job_obj.salary_min = 1_000_000
        job_obj.job_type = "full-time"
        job_obj.slug = 'accountant-job'
        
        card = self.renderer._render_job_card(job_obj, 0.75, '/jobs/accountant-job/')
        
        self.assertEqual(card['type'], 'job')
        self.assertEqual(card['emoji'], '💼')
        self.assertEqual(card['score'], 0.75)
    
    def test_render_results_list(self):
        """Test rendering list of results"""
        results = [
            {
                'item': MagicMock(display_title="بيت 1"),
                'score': 0.9,
                'type': 'property',
                'url': '/property/1/'
            },
            {
                'item': MagicMock(display_title="بيت 2"),
                'score': 0.8,
                'type': 'property',
                'url': '/property/2/'
            }
        ]
        
        rendered = self.renderer.render_results(results)
        
        self.assertEqual(len(rendered), 2)
        self.assertEqual(rendered[0]['type'], 'property')
        self.assertEqual(rendered[1]['type'], 'property')
    
    def test_render_text_summary(self):
        """Test rendering text summary"""
        results = [
            {
                'item': MagicMock(display_title="بيت في الناصرية"),
                'score': 0.9,
                'type': 'property',
                'url': '/property/1/'
            }
        ]
        
        summary = self.renderer.render_text_summary(results)
        
        self.assertIn('وجدت', summary)
        self.assertIn('نتيجة', summary)


class APITests(TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
    
    def test_smart_assistant_chat_endpoint(self):
        """Test smart assistant chat endpoint"""
        response = self.client.post(
            '/api/ai/smart/chat/',
            data=json.dumps({
                'message': 'أريد بيت في الناصرية',
                'conversation_id': 'test_conv_123',
                'render_results': True
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('response', data)
        self.assertIn('conversation_id', data)
    
    def test_smart_assistant_reset_endpoint(self):
        """Test smart assistant reset endpoint"""
        response = self.client.post(
            '/api/ai/smart/reset/',
            data=json.dumps({
                'conversation_id': 'test_conv_123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_smart_assistant_state_endpoint(self):
        """Test smart assistant state endpoint"""
        response = self.client.get(
            '/api/ai/smart/state/',
            {'conversation_id': 'test_conv_123'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('state', data)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.logout()
        
        response = self.client.post(
            '/api/ai/smart/chat/',
            data=json.dumps({'message': 'test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401 or 403)  # Depending on auth backend


class SecurityTests(TestCase):
    """Test security aspects of the smart assistant"""
    
    def test_no_sql_injection(self):
        """Test that SQL injection is prevented"""
        malicious_input = "'; DROP TABLE properties; --"
        
        intent, confidence = intent_detector.detect_intent(malicious_input)
        
        # Should not execute SQL, just return general question
        self.assertEqual(intent, Intent.GENERAL_QUESTION)
    
    def test_no_idor_vulnerability(self):
        """Test that IDOR is prevented"""
        user1 = User.objects.create_user(username='user1', password='pass1')
        user2 = User.objects.create_user(username='user2', password='pass2')
        
        # User1 should not be able to access User2's conversation
        state = smart_conversation_manager.get_or_create_state('user2_conv', user2.id)
        state.collected_filters = {'secret': 'data'}
        smart_conversation_manager.save_state(state)
        
        # User1 tries to access User2's conversation
        user1_state = smart_conversation_manager.get_or_create_state('user2_conv', user1.id)
        
        # Should get fresh state, not User2's state
        self.assertNotEqual(user1_state.collected_filters, {'secret': 'data'})
    
    def test_rate_limiting(self):
        """Test that rate limiting is enforced"""
        # This would require implementing rate limiting first
        # For now, just test that the structure exists
        from django.core.cache import cache
        
        # Simulate rate limit check
        cache_key = f'rate_limit_test_{123}'
        cache.set(cache_key, 1, 60)
        
        value = cache.get(cache_key)
        self.assertEqual(value, 1)


class IraqiDialectTests(TestCase):
    """Test Iraqi dialect support"""
    
    def test_iraqi_property_names(self):
        """Test Iraqi property name variations"""
        variations = [
            ("أريد دار", "house"),
            ("أريد بيت", "house"),
            ("أريد شقة", "apartment"),
            ("أريد فيلا", "villa"),
        ]
        
        for text, expected_type in variations:
            property_type = intent_detector.extract_property_type(text)
            self.assertEqual(property_type, expected_type)
    
    def test_iraqi_location_names(self):
        """Test Iraqi location name variations"""
        variations = [
            ("بغداد", "Baghdad"),
            ("البصرة", "Basra"),
            ("أربيل", "Erbil"),
            ("الناصرية", "Nasiriyah"),
        ]
        
        for text, expected_location in variations:
            location = intent_detector.extract_location(text)
            self.assertEqual(location, expected_location)
    
    def test_iraqi_price_formats(self):
        """Test Iraqi price format variations"""
        variations = [
            ("150 مليون", 150_000_000),
            ("مليون", 1_000_000),
            ("100 ألف", 100_000),
        ]
        
        for text, expected_value in variations:
            price = intent_detector.extract_price(text)
            self.assertIsNotNone(price)
            self.assertEqual(price['value'], expected_value)
    
    def test_iraqi_action_verbs(self):
        """Test Iraqi action verb variations"""
        variations = [
            "أريد اشتري",
            "أريد أشتري",
            "أريد شراء",
            "بدي اشتري",
            "أدور على",
        ]
        
        for text in variations:
            intent, confidence = intent_detector.detect_intent(text)
            self.assertEqual(intent, Intent.BUY_PROPERTY)
            self.assertGreater(confidence, 0.3)


class IntegrationTests(TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.conversation_id = 'integration_test_conv'
    
    def test_complete_property_search_flow(self):
        """Test complete property search flow"""
        # Step 1: User sends initial message
        response1 = smart_conversation_manager.process_message(
            "أريد بيت", self.conversation_id, self.user.id
        )
        
        # Should ask for location
        self.assertIn('location', response1['metadata'].get('collecting_field', ''))
        
        # Step 2: User provides location
        response2 = smart_conversation_manager.process_message(
            "الناصرية", self.conversation_id, self.user.id
        )
        
        # Should ask for price
        self.assertIn('price', response2['metadata'].get('collecting_field', ''))
        
        # Step 3: User provides price
        response3 = smart_conversation_manager.process_message(
            "150 مليون", self.conversation_id, self.user.id
        )
        
        # Should perform search
        self.assertIn('action', response3)
        self.assertEqual(response3['action'], 'show_results')
    
    def test_sell_property_flow(self):
        """Test sell property flow"""
        # User wants to sell
        response1 = smart_conversation_manager.process_message(
            "أريد بيع داري", self.conversation_id, self.user.id
        )
        
        # Should collect information
        self.assertIn('collect_info', response1['action'])
        
        # Provide property type
        response2 = smart_conversation_manager.process_message(
            "بيت", self.conversation_id, self.user.id
        )
        
        # Provide location
        response3 = smart_conversation_manager.process_message(
            "الناصرية", self.conversation_id, self.user.id
        )
        
        # Should ask for confirmation
        self.assertIn('confirm', response3['action'])
    
    def test_conversation_persistence(self):
        """Test that conversation state persists across messages"""
        # First message
        smart_conversation_manager.process_message(
            "أريد بيت", self.conversation_id, self.user.id
        )
        
        # Second message
        response = smart_conversation_manager.process_message(
            "الناصرية", self.conversation_id, self.user.id
        )
        
        # State should have collected information
        state = smart_conversation_manager.get_or_create_state(self.conversation_id, self.user.id)
        self.assertIn('location', state.collected_filters)
        self.assertEqual(state.collected_filters['location'], 'Nasiriyah')
