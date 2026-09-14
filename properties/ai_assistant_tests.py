"""
AI Assistant Test Suite
Comprehensive testing for the intelligent AI assistant with Iraqi dialect support
"""

import unittest
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .ai_arabic_normalizer import arabic_normalizer, number_parser
from .ai_intent_classifier import intent_detector, feature_extractor
from .ai_entity_extraction import entity_extractor, entity_normalizer
from .ai_context_engine import context_manager, question_generator
from .ai_conversation_manager import conversation_manager
from .ai_semantic_search import hybrid_search_engine, conversation_learner
from .models import Property, Broker


class ArabicNormalizerTests(TestCase):
    """Test Arabic text normalization with Iraqi dialect support"""
    
    def setUp(self):
        self.normalizer = arabic_normalizer
    
    def test_dialect_normalization(self):
        """Test Iraqi dialect normalization"""
        # Test dialect words
        text = "شكد المال عندك؟"
        normalized = self.normalizer.normalize_text(text)
        self.assertIn('كم', normalized)
        
        text = "أدور على دار بلبصرة"
        normalized = self.normalizer.normalize_text(text)
        self.assertIn('أبحث', normalized)
        self.assertIn('بالبصرة', normalized)
    
    def test_spelling_correction(self):
        """Test spelling correction"""
        text = "اريد بيت بل بصره"
        normalized = self.normalizer.normalize_text(text)
        self.assertIn('البصرة', normalized)
    
    def test_number_extraction(self):
        """Test number extraction from Iraqi dialect"""
        text = "عندي 150 مليون"
        numbers = self.normalizer.extract_numbers(text)
        self.assertEqual(len(numbers), 1)
        self.assertEqual(numbers[0]['converted'], 150000000)
    
    def test_fractional_numbers(self):
        """Test fractional number parsing"""
        text = "نصف مليون"
        numbers = self.normalizer.extract_numbers(text)
        self.assertEqual(len(numbers), 1)
        self.assertEqual(numbers[0]['converted'], 500000)
    
    def test_governorate_normalization(self):
        """Test governorate name normalization"""
        variations = ['البصرة', 'بلبصرة', 'بالبصره', 'بصرة']
        for variation in variations:
            normalized = self.normalizer.normalize_governorate(variation)
            self.assertEqual(normalized, 'البصرة')
    
    def test_property_type_normalization(self):
        """Test property type normalization"""
        variations = ['بيت', 'دار', 'منزل']
        for variation in variations:
            normalized = self.normalizer.normalize_property_type(variation)
            self.assertEqual(normalized, 'house')
    
    def test_compound_request_parsing(self):
        """Test compound request parsing"""
        text = "أريد بيت بالبصرة بحدود 150 مليون"
        result = self.normalizer.parse_compound_request(text)
        
        self.assertEqual(result['entities']['property_type'], 'house')
        self.assertEqual(result['entities']['governorate'], 'البصرة')
        self.assertEqual(result['entities']['budget'], 150000000)
        self.assertGreater(result['confidence'], 0.7)


class IntentDetectionTests(TestCase):
    """Test intent detection with confidence scoring"""
    
    def setUp(self):
        self.detector = intent_detector
    
    def test_buy_property_intent(self):
        """Test buy property intent detection"""
        messages = [
            "أريد بيت بالبصرة",
            "أدور على دار",
            "أبحث عن منزل",
            "أريد أشتري عقار"
        ]
        
        for message in messages:
            result = self.detector.detect_intent(message)
            self.assertEqual(result['intent'], 'buy_property')
            self.assertGreater(result['confidence'], 0.7)
    
    def test_sell_property_intent(self):
        """Test sell property intent detection"""
        messages = [
            "أريد أبيع بيتي",
            "عندي دار وأريد أبيعها",
            "أملك عقار وأريد بيعه"
        ]
        
        for message in messages:
            result = self.detector.detect_intent(message)
            self.assertEqual(result['intent'], 'sell_property')
            self.assertGreater(result['confidence'], 0.7)
    
    def test_find_job_intent(self):
        """Test find job intent detection"""
        messages = [
            "أبحث عن وظيفة",
            "أريد شغل",
            "أدور على عمل"
        ]
        
        for message in messages:
            result = self.detector.detect_intent(message)
            self.assertEqual(result['intent'], 'find_job')
            self.assertGreater(result['confidence'], 0.7)
    
    def test_low_confidence_handling(self):
        """Test low confidence intent handling"""
        ambiguous_message = "شيء"
        result = self.detector.detect_intent(ambiguous_message)
        
        self.assertLess(result['confidence'], 0.7)
        self.assertTrue(result['requires_clarification'])
    
    def test_confidence_threshold(self):
        """Test confidence threshold functionality"""
        self.detector.set_confidence_threshold(0.80)
        
        message = "أريد شيء"
        result = self.detector.detect_intent(message)
        
        # Should require clarification with higher threshold
        self.assertTrue(result['requires_clarification'])


class EntityExtractionTests(TestCase):
    """Test entity extraction with context awareness"""
    
    def setUp(self):
        self.extractor = entity_extractor
        self.normalizer = entity_normalizer
    
    def test_property_entity_extraction(self):
        """Test property entity extraction"""
        text = "أريد بيت بالبصرة مساحته 200 متر وبحدود 180 مليون"
        entities = self.extractor.extract_entities(text, 'buy_property')
        
        self.assertEqual(entities['property_type'], 'house')
        self.assertEqual(entities['governorate'], 'البصرة')
        self.assertEqual(entities['area'], 200)
        self.assertEqual(entities['budget'], 180000000)
    
    def test_location_entity_extraction(self):
        """Test location entity extraction"""
        text = "أريد وظيفة في بغداد"
        entities = self.extractor.extract_entities(text, 'find_job')
        
        self.assertEqual(entities['location'], 'بغداد')
    
    def test_budget_interpretation(self):
        """Test budget interpretation from text"""
        text = "ميزانيتي 150 مليون"
        budget = arabic_normalizer.interpret_budget(text)
        
        self.assertEqual(budget, 150000000)
    
    def test_area_interpretation(self):
        """Test area interpretation from text"""
        text = "مساحته 200 متر"
        area = arabic_normalizer.interpret_area(text)
        
        self.assertEqual(area, 200)
    
    def test_entity_normalization(self):
        """Test entity normalization"""
        entities = {
            'governorate': 'بلبصرة',
            'property_type': 'دار',
            'budget': 150000000
        }
        
        normalized = self.normalizer.normalize(entities)
        
        self.assertEqual(normalized['governorate'], 'البصرة')
        self.assertEqual(normalized['property_type'], 'house')
        self.assertEqual(normalized['budget'], 150000000)


class ContextEngineTests(TestCase):
    """Test conversation context management"""
    
    def setUp(self):
        self.context_manager = context_manager
        self.question_generator = question_generator
    
    def test_context_creation(self):
        """Test conversation context creation"""
        context = self.context_manager.get_context('test_conversation')
        
        self.assertIsNotNone(context)
        self.assertEqual(context.context['conversation_id'], 'test_conversation')
    
    def test_intent_update(self):
        """Test intent update in context"""
        context = self.context_manager.get_context('test_conversation')
        context.update_intent('buy_property', 0.95)
        
        self.assertEqual(context.context['intent'], 'buy_property')
        self.assertEqual(context.context['intent_confidence'], 0.95)
    
    def test_entity_update(self):
        """Test entity update in context"""
        context = self.context_manager.get_context('test_conversation')
        entities = {'governorate': 'البصرة', 'budget': 150000000}
        context.update_entities(entities)
        
        self.assertEqual(context.context['entities']['governorate'], 'البصرة')
        self.assertEqual(context.context['entities']['budget'], 150000000)
    
    def test_turn_tracking(self):
        """Test conversation turn tracking"""
        context = self.context_manager.get_context('test_conversation')
        initial_turn = context.context['turn_count']
        
        context.increment_turn()
        
        self.assertEqual(context.context['turn_count'], initial_turn + 1)
    
    def test_missing_fields_detection(self):
        """Test missing fields detection"""
        context = self.context_manager.get_context('test_conversation')
        context.update_entities({'governorate': 'البصرة'})
        
        required_fields = ['governorate', 'property_type', 'budget']
        missing = context.get_missing_fields(required_fields)
        
        self.assertIn('property_type', missing)
        self.assertIn('budget', missing)
        self.assertNotIn('governorate', missing)
    
    def test_smart_question_generation(self):
        """Test smart question generation"""
        context = self.context_manager.get_context('test_conversation')
        context.update_entities({'governorate': 'البصرة'})
        
        question = self.question_generator.generate_next_question(context, 'buy_property')
        
        self.assertIsNotNone(question)
        self.assertIn('المحافظة', question.lower())


class ConversationManagerTests(TestCase):
    """Test main conversation manager integration"""
    
    def setUp(self):
        self.manager = conversation_manager
        self.client = Client()
    
    def test_message_processing(self):
        """Test complete message processing"""
        message = "أريد بيت بالبصرة"
        conversation_id = 'test_conversation'
        
        response = self.manager.process_message(message, conversation_id)
        
        self.assertTrue(response['success'])
        self.assertIn('response', response)
        self.assertIn('intent', response)
    
    def test_modification_handling(self):
        """Test request modification handling"""
        # First establish context
        conversation_id = 'test_modification'
        self.manager.process_message("أريد بيت بالبصرة", conversation_id)
        
        # Then modify the request
        response = self.manager.process_message("لا خلّي الميزانية 200 مليون", conversation_id)
        
        self.assertTrue(response['success'])
    
    def test_low_confidence_clarification(self):
        """Test low confidence handling with clarification"""
        ambiguous_message = "شيء"
        conversation_id = 'test_ambiguous'
        
        response = self.manager.process_message(ambiguous_message, conversation_id)
        
        self.assertTrue(response['success'])
        self.assertTrue(response.get('requires_clarification', False))
    
    def test_feedback_recording(self):
        """Test user feedback recording"""
        conversation_id = 'test_feedback'
        feedback = 'positive'
        message = 'آخر رسالة'
        
        response = self.manager.record_feedback(conversation_id, feedback, message)
        
        self.assertTrue(response['success'])


class ConversationLearnerTests(TestCase):
    """Test learning from conversations"""
    
    def setUp(self):
        self.learner = conversation_learner
    
    def test_correction_recording(self):
        """Test correction recording"""
        self.learner.record_correction(
            'buy_property',
            'sell_property',
            {'property_type': 'house'},
            {'property_type': 'house'},
            'أريد أبيع بيتي'
        )
        
        stats = self.learner.get_learning_statistics()
        self.assertEqual(stats['total_corrections'], 1)
    
    def test_feedback_recording(self):
        """Test feedback recording"""
        self.learner.record_feedback('test_conv', 'positive', 'test message', 'test response')
        
        stats = self.learner.get_learning_statistics()
        self.assertEqual(stats['total_feedback'], 1)
    
    def test_conversation_recording(self):
        """Test conversation recording"""
        messages = [
            {'text': 'أريد بيت', 'intent': 'buy_property'},
            {'text': 'البصرة', 'intent': 'buy_property'}
        ]
        
        self.learner.record_conversation('test_conv', messages)
        
        stats = self.learner.get_learning_statistics()
        self.assertEqual(stats['total_conversations'], 1)
    
    def test_training_data_export(self):
        """Test training data export"""
        self.learner.record_correction(
            'buy_property',
            'sell_property',
            {'property_type': 'house'},
            {'property_type': 'house'},
            'أريد أبيع بيتي'
        )
        
        training_data = self.learner.export_training_data()
        
        self.assertGreater(len(training_data), 0)
        self.assertIn('text', training_data[0])
        self.assertIn('intent', training_data[0])


class EndToEndTests(TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        self.manager = conversation_manager
        self.client = Client()
    
    def test_full_conversation_flow(self):
        """Test complete conversation flow"""
        conversation_id = 'test_full_flow'
        
        # Step 1: Initial request
        response1 = self.manager.process_message("أريد بيت", conversation_id)
        self.assertTrue(response1['success'])
        self.assertEqual(response1['intent'], 'buy_property')
        
        # Step 2: Provide governorate
        response2 = self.manager.process_message("البصرة", conversation_id)
        self.assertTrue(response2['success'])
        
        # Step 3: Provide budget
        response3 = self.manager.process_message("150 مليون", conversation_id)
        self.assertTrue(response3['success'])
        
        # Step 4: Provide property type
        response4 = self.manager.process_message("بيت", conversation_id)
        self.assertTrue(response4['success'])
        
        # Step 5: Should proceed to search
        self.assertIn(response4['action'], ['search', 'show_results'])
    
    def test_iraqi_dialect_conversation(self):
        """Test conversation with Iraqi dialect"""
        conversation_id = 'test_dialect'
        
        messages = [
            "أدور على دار بلبصرة",
            "عندي حدود 150 مليون",
            "تفضل بيت مو شقة"
        ]
        
        for message in messages:
            response = self.manager.process_message(message, conversation_id)
            self.assertTrue(response['success'])
    
    def test_error_correction_flow(self):
        """Test error correction flow"""
        conversation_id = 'test_correction'
        
        # Initial request
        response1 = self.manager.process_message("أريد بيت", conversation_id)
        
        # User correction
        response2 = self.manager.process_message("لا، أريد أبيع", conversation_id)
        self.assertTrue(response2['success'])
    
    def test_multi_step_preferences(self):
        """Test multi-step preference handling"""
        conversation_id = 'test_preferences'
        
        messages = [
            "أريد بيت بالبصرة",
            "150 مليون",
            "خليه قريب من مدرسة",
            "وأيضاً منطقة هادئة"
        ]
        
        for message in messages:
            response = self.manager.process_message(message, conversation_id)
            self.assertTrue(response['success'])


class IraqiDialectSpecificTests(TestCase):
    """Tests specific to Iraqi dialect processing"""
    
    def test_iraqi_number_expressions(self):
        """Test Iraqi number expressions"""
        expressions = [
            ("مئة مليون", 100000000),
            ("مائة مليون", 100000000),
            ("نصف مليون", 500000),
            ("مليون ونص", 1500000),
            ("ربع مليون", 250000)
        ]
        
        for expression, expected in expressions:
            result = arabic_normalizer.interpret_budget(expression)
            self.assertEqual(result, expected)
    
    def test_iraqi_location_variations(self):
        """Test Iraqi location name variations"""
        variations = {
            'هولير': 'أربيل',
            'العمارة': 'ميسان',
            'السماوة': 'المثنى',
            'الرمادي': 'الانبار',
            'الناصرية': 'ذي قار'
        }
        
        for variation, expected in variations.items():
            result = arabic_normalizer.normalize_governorate(variation)
            self.assertEqual(result, expected)
    
    def test_iraqi_property_terminology(self):
        """Test Iraqi property terminology"""
        terms = {
            'قسيمة': 'plot',
            'بناية': 'building',
            'محل': 'commercial',
            'فيلا': 'villa'
        }
        
        for term, expected in terms.items():
            result = arabic_normalizer.normalize_property_type(term)
            self.assertEqual(result, expected)


class PerformanceTests(TestCase):
    """Performance and scalability tests"""
    
    def test_bulk_message_processing(self):
        """Test bulk message processing"""
        messages = [
            "أريد بيت بالبصرة",
            "أبحث عن شقة في بغداد",
            "أريد وظيفة في كربلاء",
            "أبحث عن فندق في أربيل"
        ]
        
        for i, message in enumerate(messages):
            conversation_id = f'bulk_test_{i}'
            response = conversation_manager.process_message(message, conversation_id)
            self.assertTrue(response['success'])
    
    def test_context_memory_efficiency(self):
        """Test context memory management"""
        conversation_ids = [f'memory_test_{i}' for i in range(100)]
        
        for conv_id in conversation_ids:
            context = context_manager.get_context(conv_id)
            context.update_intent('buy_property', 0.9)
        
        # Cleanup should work efficiently
        context_manager.cleanup_expired_contexts()
        
        active_count = context_manager.get_active_contexts_count()
        self.assertLessEqual(active_count, 100)


if __name__ == '__main__':
    unittest.main()