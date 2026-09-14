"""
AI Training Models - Database Models for Training and Evaluation
Separate training data from production data
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class TrainingExample(models.Model):
    """Training examples for intent classification and entity extraction"""
    
    DATASET_TYPES = [
        ('initial', 'Initial Dataset'),
        ('user_generated', 'User Generated'),
        ('augmented', 'Data Augmented'),
        ('expert_curated', 'Expert Curated')
    ]
    
    INTENT_CHOICES = [
        ('buy_property', 'Buy Property'),
        ('sell_property', 'Sell Property'),
        ('join_agent', 'Join Agent'),
        ('find_job', 'Find Job'),
        ('travel', 'Travel'),
        ('find_hotel', 'Find Hotel'),
        ('find_service', 'Find Service'),
        ('construction', 'Construction'),
        ('auction', 'Auction'),
        ('find_resort', 'Find Resort'),
        ('find_product', 'Find Product'),
        ('general_question', 'General Question'),
        ('support', 'Support'),
        ('unknown', 'Unknown')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review')
    ]
    
    text = models.TextField()
    normalized_text = models.TextField(blank=True, null=True)
    intent = models.CharField(max_length=50, choices=INTENT_CHOICES)
    confidence = models.FloatField(default=0.0)
    entities = models.JSONField(default=dict, blank=True)
    
    # Metadata
    dataset_type = models.CharField(max_length=50, choices=DATASET_TYPES, default='user_generated')
    source = models.CharField(max_length=100, blank=True)  # e.g., 'user_correction', 'conversation'
    conversation_id = models.CharField(max_length=100, blank=True)
    original_message = models.TextField(blank=True)
    
    # Review
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_examples')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    
    # Quality metrics
    is_test = models.BooleanField(default=False)  # Is this in test set
    quality_score = models.FloatField(null=True, blank=True)  # 0-1
    
    # Augmentation
    is_augmented = models.BooleanField(default=False)
    parent_example = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='augmented_examples')
    augmentation_method = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_training_examples'
        indexes = [
            models.Index(fields=['intent']),
            models.Index(fields=['status']),
            models.Index(fields=['dataset_type']),
            models.Index(fields=['is_test']),
        ]
    
    def __str__(self):
        return f"{self.text[:50]}... ({self.intent})"


class UserFeedback(models.Model):
    """User feedback on AI responses for learning"""
    
    FEEDBACK_TYPES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral')
    ]
    
    FEEDBACK_CONTEXT = [
        ('search_results', 'Search Results'),
        ('response_quality', 'Response Quality'),
        ('clarification', 'Clarification'),
        ('suggestion', 'Suggestion'),
        ('general', 'General')
    ]
    
    conversation_id = models.CharField(max_length=100)
    user_message = models.TextField()
    ai_response = models.TextField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    feedback_context = models.CharField(max_length=50, choices=FEEDBACK_CONTEXT, default='general')
    
    # Additional context
    detected_intent = models.CharField(max_length=50, blank=True)
    detected_entities = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    
    # User provided clarification
    user_clarification = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    
    # Results if applicable
    results_shown = models.JSONField(default=list, blank=True)
    selected_result = models.JSONField(null=True, blank=True)
    
    # Session info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_user_feedback'
        indexes = [
            models.Index(fields=['feedback_type']),
            models.Index(fields=['feedback_context']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.feedback_type} - {self.user_message[:30]}..."


class UnknownQuery(models.Model):
    """Queries that the AI system couldn't understand"""
    
    text = models.TextField()
    conversation_id = models.CharField(max_length=100)
    
    # Analysis
    attempted_intent = models.CharField(max_length=50, blank=True)
    attempted_entities = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    
    # Resolution
    resolved = models.BooleanField(default=False)
    resolved_intent = models.CharField(max_length=50, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Priority for review
    priority = models.IntegerField(default=1)  # 1=low, 5=high
    occurrence_count = models.IntegerField(default=1)
    
    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_unknown_queries'
        indexes = [
            models.Index(fields=['resolved']),
            models.Index(fields=['priority']),
            models.Index(fields=['occurrence_count']),
        ]
    
    def __str__(self):
        return f"{self.text[:50]}... ({'Resolved' if self.resolved else 'Unresolved'})"


class ModelVersion(models.Model):
    """Model versioning and tracking"""
    
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('testing', 'Testing'),
        ('staging', 'Staging'),
        ('production', 'Production'),
        ('archived', 'Archived')
    ]
    
    version = models.CharField(max_length=50, unique=True)
    model_type = models.CharField(max_length=50)  # e.g., 'intent_classifier', 'entity_extractor'
    description = models.TextField(blank=True)
    
    # Training info
    training_dataset_version = models.CharField(max_length=50)
    training_date = models.DateTimeField()
    training_duration = models.DurationField(null=True, blank=True)
    training_config = models.JSONField(default=dict, blank=True)
    
    # Model file info
    model_file_path = models.CharField(max_length=255, blank=True)
    model_size_mb = models.FloatField(null=True, blank=True)
    model_checksum = models.CharField(max_length=64, blank=True)
    
    # Evaluation metrics
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    evaluation_dataset_version = models.CharField(max_length=50, blank=True)
    evaluation_date = models.DateTimeField(null=True, blank=True)
    
    # Deployment info
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    deployed_at = models.DateTimeField(null=True, blank=True)
    deployed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Performance metrics
    avg_response_time_ms = models.FloatField(null=True, blank=True)
    success_rate = models.FloatField(null=True, blank=True)
    user_satisfaction = models.FloatField(null=True, blank=True)
    
    # Rollback info
    can_rollback = models.BooleanField(default=True)
    rollback_deadline = models.DateTimeField(null=True, blank=True)
    
    # Notes
    release_notes = models.TextField(blank=True)
    known_issues = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_model_versions'
        indexes = [
            models.Index(fields=['model_type']),
            models.Index(fields=['status']),
            models.Index(fields=['version']),
        ]
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.version} ({self.model_type}) - {self.status}"


class ModelEvaluation(models.Model):
    """Detailed evaluation results for model versions"""
    
    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='evaluations')
    evaluation_dataset = models.CharField(max_length=50)
    evaluation_date = models.DateTimeField(auto_now_add=True)
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Test results
    test_type = models.CharField(max_length=50)  # e.g., 'intent_accuracy', 'entity_accuracy', 'end_to_end'
    total_tests = models.IntegerField()
    passed_tests = models.IntegerField()
    failed_tests = models.IntegerField()
    
    # Metrics
    accuracy = models.FloatField()
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    
    # Detailed results
    detailed_results = models.JSONField(default=dict, blank=True)
    confusion_matrix = models.JSONField(default=dict, blank=True)
    
    # Comparison with previous version
    compared_to_version = models.CharField(max_length=50, blank=True)
    accuracy_delta = models.FloatField(null=True, blank=True)
    improvement = models.BooleanField(default=False)
    
    # Status
    passed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'ai_model_evaluations'
        indexes = [
            models.Index(fields=['model_version']),
            models.Index(fields=['test_type']),
            models.Index(fields=['evaluation_date']),
        ]
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"Evaluation of {self.model_version.version} - {self.test_type}"


class SearchAnalytics(models.Model):
    """Search analytics for learning user preferences"""
    
    conversation_id = models.CharField(max_length=100)
    query = models.TextField()
    normalized_query = models.TextField(blank=True, null=True)
    
    # Intent and entities
    detected_intent = models.CharField(max_length=50)
    detected_entities = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField()
    
    # Search parameters
    search_params = models.JSONField(default=dict, blank=True)
    
    # Results
    results_count = models.IntegerField()
    results_shown = models.JSONField(default=list, blank=True)
    
    # User interaction
    selected_result = models.JSONField(null=True, blank=True)
    user_feedback = models.CharField(max_length=20, blank=True)  # positive, negative, neutral
    clicked_results = models.JSONField(default=list, blank=True)
    
    # Session info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Performance
    search_duration_ms = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_search_analytics'
        indexes = [
            models.Index(fields=['detected_intent']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search: {self.query[:30]}... ({self.detected_intent})"


class ConversationLog(models.Model):
    """Complete conversation logs for analysis"""
    
    conversation_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Conversation metadata
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.DurationField(null=True, blank=True)
    
    # Messages
    messages = models.JSONField(default=list)  # List of message objects
    
    # Summary
    final_intent = models.CharField(max_length=50, blank=True)
    resolved = models.BooleanField(default=False)
    resolution = models.TextField(blank=True)
    
    # Quality metrics
    user_satisfaction = models.IntegerField(null=True, blank=True)  # 1-5
    agent_performance_score = models.FloatField(null=True, blank=True)  # 0-1
    
    # Session info
    session_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_conversation_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['started_at']),
            models.Index(fields=['resolved']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Conversation {self.conversation_id}"


class KnowledgeBaseEntry(models.Model):
    """Knowledge base entries for RAG - site-specific information"""
    
    CATEGORY_CHOICES = [
        ('faq', 'FAQ'),
        ('policy', 'Policy'),
        ('guide', 'Guide'),
        ('service', 'Service'),
        ('general', 'General')
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    content = models.TextField()
    
    # Metadata
    keywords = models.JSONField(default=list, blank=True)  # List of keywords for search
    language = models.CharField(max_length=10, default='ar')
    priority = models.IntegerField(default=1)  # Higher priority shown first
    
    # References
    related_urls = models.JSONField(default=list, blank=True)
    related_sections = models.JSONField(default=list, blank=True)
    
    # Versioning
    version = models.IntegerField(default=1)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Embedding (for future vector search)
    embedding_vector = models.JSONField(null=True, blank=True)  # Store as list of floats
    embedding_model = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_knowledge_base'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['language']),
            models.Index(fields=['priority']),
        ]
        ordering = ['-priority', '-last_updated']
    
    def __str__(self):
        return f"{self.title} ({self.category})"


class ToolUsageLog(models.Model):
    """Tool usage analytics for AI Agent"""
    
    tool_name = models.CharField(max_length=100)
    conversation_id = models.CharField(max_length=100)
    
    # Input
    input_data = models.JSONField(default=dict, blank=True)
    
    # Output
    success = models.BooleanField()
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Performance
    execution_time_ms = models.FloatField()
    
    # Context
    intent = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_tool_usage_log'
        indexes = [
            models.Index(fields=['tool_name']),
            models.Index(fields=['success']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tool_name} - {'Success' if self.success else 'Failed'}"


class VoiceInteractionLog(models.Model):
    """Track voice interactions with the AI Assistant"""
    
    # Recording details
    duration_ms = models.FloatField()
    audio_quality_score = models.FloatField(null=True, blank=True)
    
    # Speech-to-Text results
    recognized_text = models.TextField()
    stt_confidence = models.FloatField(null=True, blank=True)
    stt_language = models.CharField(max_length=10, default='ar-SA')
    stt_success = models.BooleanField()
    
    # Processing results
    intent_detected = models.CharField(max_length=50, blank=True)
    entities_extracted = models.JSONField(default=dict, blank=True)
    command_recognized = models.CharField(max_length=50, blank=True)
    
    # Text-to-Speech
    response_text = models.TextField(blank=True)
    tts_used = models.BooleanField(default=False)
    tts_duration_ms = models.FloatField(null=True, blank=True)
    
    # User interaction
    interrupted = models.BooleanField(default=False)
    user_corrected = models.BooleanField(default=False)
    corrected_text = models.TextField(blank=True)
    
    # Session info
    conversation_id = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_voice_interaction_log'
        indexes = [
            models.Index(fields=['stt_success']),
            models.Index(fields=['tts_used']),
            models.Index(fields=['created_at']),
            models.Index(fields=['conversation_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Voice Interaction - {self.recognized_text[:50]}..."