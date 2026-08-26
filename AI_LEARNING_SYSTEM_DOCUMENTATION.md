# AI Learning System Documentation

## Overview

The AI Learning System provides a comprehensive framework for continuous improvement of the Dalal platform's AI Assistant through data collection, analysis, model training, and evaluation.

## Architecture

```
Real User Conversations
        ↓
Data Collection Pipeline
        ↓
Data Preprocessing
        ↓
Entity Normalization
        ↓
Data Anonymization
        ↓
Training Dataset
        ↓
Data Augmentation
        ↓
Model Training
        ↓
Model Evaluation
        ↓
A/B Testing
        ↓
Production Deployment
        ↓
User Feedback
        ↓
Continuous Improvement
```

## Core Components

### 1. Data Collection Pipeline

**DataCollector Class:**
- Collects conversation data from user interactions
- Separates sensitive data from training data
- Records user corrections and feedback
- Tracks unknown queries for learning
- Monitors search analytics

**Key Methods:**
- `collect_conversation_data()` - Complete conversation logging
- `collect_training_example()` - Individual training examples
- `collect_user_feedback()` - User satisfaction tracking
- `collect_unknown_query()` - Failed intent detection
- `collect_search_analytics()` - Search behavior analysis
- `collect_user_correction()` - User correction tracking

### 2. Data Preprocessing

**MoneyParser Class:**
- Parses Arabic money expressions
- Handles Iraqi dialect variations
- Supports range indicators ("أقل من", "حدود")
- Currency detection and normalization

**Supported Expressions:**
- "150 مليون" → 150,000,000 IQD
- "مئة وخمسين مليون" → 150,000,000 IQD
- "حدود 150 مليون" → Range: 135M-165M IQD
- "أقل من 150 مليون" → Max: 150,000,000 IQD

**TimeDateParser Class:**
- Parses Arabic time expressions
- Handles relative time references
- Date format conversion
- Timezone awareness

**Supported Expressions:**
- "باچر" → Tomorrow
- "بعد أسبوع" → +7 days
- "الشهر الجاي" → +30 days
- "15/8/2026" → Specific date

**EntityNormalizer Class:**
- Normalizes entity values to standard format
- Governorate name standardization
- Property type unification
- Job type normalization

**Normalization Examples:**
- "بغداد", "بغداذ", "بغدادَ" → "Baghdad"
- "بيت", "دار", "منزل" → "house"
- "وظيفة", "عمل", "شغل" → "job"

### 3. Data Augmentation

**DataAugmenter Class:**
- Generates training data variations
- Iraqi dialect support
- Phrase variation generation
- Quality validation

**Augmentation Methods:**
- Phrase variations: "أريد" → ["أبغى", "أبي", "أكدر"]
- Dialect variations: Standard → Iraqi dialect
- Synonym replacement: Context-aware substitutions
- Word reordering: Arabic sentence structure variations

**Quality Control:**
- Confidence scoring for augmented data
- Parent text tracking
- Validation before training use

### 4. Dataset Management

**DatasetManager Class:**
- Training/test dataset creation
- Data export functionality
- Quality control
- Statistical analysis

**Dataset Types:**
- `initial` - Initial training data
- `user_generated` - Real user conversations
- `augmented` - Synthetic variations
- `expert_curated` - Human-reviewed examples

**Quality Metrics:**
- Intent distribution analysis
- Entity extraction accuracy
- Dataset balance monitoring
- Outlier detection

### 5. Model Training

**ModelTrainer Class:**
- Intent classifier training
- Entity extraction model training
- Model versioning
- Training pipeline orchestration

**Training Pipeline:**
1. Dataset preparation
2. Feature extraction
3. Model training
4. Validation
5. Version creation
6. Performance evaluation

**Model Types:**
- Intent Classification
- Entity Recognition
- Ranking Models
- Response Generation

### 6. Model Evaluation

**Evaluator Class:**
- Model performance testing
- Comparison between versions
- Regression testing
- A/B testing support

**Evaluation Metrics:**
- Intent Accuracy
- Entity F1 Score
- Retrieval Accuracy
- Ranking Quality
- Response Quality
- User Satisfaction

**Testing Methods:**
- Hold-out test set
- Cross-validation
- A/B testing
- Regression testing

### 7. Data Privacy

**DataAnonymizer Class:**
- Sensitive data detection
- PII removal
- Phone number masking
- Email obfuscation
- Address anonymization

**Privacy Patterns:**
- Phone numbers: Iraqi and international formats
- Email addresses: Standard email patterns
- Personal identifiers: Custom patterns
- Financial data: Account numbers, etc.

### 8. Debug & Monitoring

**DebugMode Class:**
- Developer debugging tools
- Internal processing visibility
- Performance tracking
- Error analysis

**Debug Information:**
- Raw user message
- Normalized message
- Intent detection results
- Entity extraction
- Conversation state
- Tool calls
- API responses
- Latency metrics

**AIHealthChecker Class:**
- System health monitoring
- Component status checking
- Performance metrics
- Automated alerts

**Health Checks:**
- Database connectivity
- Intent detector status
- Entity extractor status
- Context manager health
- Tool registry status
- Learning pipeline status
- Voice system status

## API Endpoints

### Data Collection

**POST /api/ai/user-correction/**
- Submit user corrections
- Records intent/entity corrections
- High-priority training data

**Request:**
```json
{
  "conversation_id": "conv_123",
  "original_intent": "buy_property",
  "corrected_intent": "sell_property",
  "original_entities": {},
  "corrected_entities": {},
  "user_message": "لا أريد أبيع"
}
```

### Model Management

**POST /api/ai/train-model/**
- Trigger model training
- Configurable training parameters
- Async training support

**Request:**
```json
{
  "model_type": "intent_classifier",
  "config": {
    "epochs": 10,
    "batch_size": 32
  }
}
```

**POST /api/ai/model-evaluation/**
- Run model evaluation
- Compare model versions
- Performance metrics

**Request:**
```json
{
  "model_version": "v2.0",
  "test_dataset": "all"
}
```

### System Monitoring

**GET /api/ai/health/**
- System health check
- Component status
- Performance metrics

**Response:**
```json
{
  "success": true,
  "health": {
    "status": "healthy",
    "components": {
      "database": {"status": "connected"},
      "intent_detector": {"status": "operational"},
      "entity_extractor": {"status": "operational"}
    }
  },
  "performance": {
    "resolution_rate": 85.5,
    "tool_success_rate": 92.3
  }
}
```

### Debug & Development

**POST /api/ai/debug-mode/**
- Toggle debug mode
- Developer-only access
- Security controlled

**GET /api/ai/debug-data/**
- Get debug information
- Processing details
- Performance data

**POST /api/ai/data-augmentation/**
- Generate data variations
- Training data expansion
- Quality validation

### Advanced Features

**POST /api/ai/ab-testing/**
- Configure A/B testing
- Model comparison
- Traffic splitting

## Database Models

### Training Example
- User message and normalized text
- Intent and entities
- Confidence score
- Source and dataset type
- Quality metrics
- Review status

### User Feedback
- Conversation feedback
- Positive/negative ratings
- Detected intent accuracy
- User satisfaction tracking

### Unknown Query
- Failed intent detection
- Occurrence counting
- Priority classification
- Resolution tracking

### Model Version
- Version management
- Training metadata
- Performance metrics
- Deployment status

### Model Evaluation
- Test results
- Metric tracking
- Comparison data
- Regression testing

### Search Analytics
- Query patterns
- User behavior
- Result selection
- Search optimization

### Conversation Log
- Complete conversation history
- Intent resolution
- Session data
- Performance metrics

### Knowledge Base Entry
- Static knowledge
- FAQ entries
- Policy information
- RAG support

### Tool Usage Log
- Tool execution tracking
- Success/failure rates
- Performance metrics
- Usage patterns

### Voice Interaction Log
- Voice conversation tracking
- STT/TTS metrics
- Command recognition
- User interaction patterns

## Integration Points

### Conversation Manager Integration

**Preprocessing Pipeline:**
```python
def process_message(message, conversation_id, user, is_voice):
    # 1. Preprocess with learning pipeline
    preprocessed = self._preprocess_message(message)
    
    # 2. Process with AI Agent
    response = self.ai_agent.process_message(
        preprocessed['normalized_text'], 
        conversation_id, 
        user
    )
    
    # 3. Normalize entities
    response['state']['entities'] = self._normalize_entities(
        response['state']['entities']
    )
    
    # 4. Collect training data
    if self.collect_training_data:
        self._collect_training_data_from_response(
            preprocessed['normalized_text'], 
            response, 
            conversation_id, 
            user
        )
    
    return response
```

### Voice System Integration

**Voice Analytics:**
- Voice conversation tracking
- STT success monitoring
- TTS usage statistics
- Command recognition

**Entity Processing:**
- Voice text normalization
- Arabic number conversion
- Dialect handling
- Error correction

## Workflow Examples

### 1. Continuous Learning Pipeline

```
User: "أريد بيت بالبصرة بـ150 مليون"
↓
Intent Detection: buy_property
↓
Entity Extraction: {governorate: "البصرة", budget: 150000000}
↓
Search Execution
↓
Results Displayed
↓
User Selects Result C
↓
Data Collection:
  - Training example created
  - Search analytics recorded
  - User preference logged
↓
Dataset Updated
↓
Model Retraining (periodic)
↓
Improved Recommendations
```

### 2. User Correction Workflow

```
AI: "أنت تبحث عن شراء بيت."
User: "لا أريد أبيع."
↓
Correction API Called
↓
Data Collection:
  - Original intent: buy_property
  - Corrected intent: sell_property
  - High priority training example
↓
Expert Review
↓
Dataset Update
↓
Model Improvement
```

### 3. Unknown Query Handling

```
User: "شو أسعار الدلالين؟"
↓
Intent Detection: unknown
↓
Unknown Query Logged
↓
Admin Dashboard Alert
↓
Expert Classification:
  - Intent: general_question
  - Entities: {topic: "broker_prices"}
↓
Added to Training Dataset
↓
Future Recognition Improved
```

## Admin Dashboard Features

### 1. Training Examples Management
- View all training examples
- Filter by intent, status, dataset type
- Approve/reject examples
- Edit entities and intents
- Quality scoring

### 2. Unknown Queries Review
- View failed detections
- Priority sorting
- Batch classification
- Pattern analysis
- Resolution tracking

### 3. Model Version Control
- View all model versions
- Performance comparison
- Deployment management
- Rollback capabilities
- A/B testing configuration

### 4. Analytics Dashboard
- Intent accuracy trends
- Entity extraction metrics
- User satisfaction rates
- System performance
- Voice analytics
- Tool usage statistics

### 5. Knowledge Base Management
- FAQ entries
- Policy information
- Static knowledge
- RAG content management

## Performance Optimization

### Caching Strategy
- Intent detection caching
- Entity extraction caching
- Model version caching
- Analytics aggregation

### Data Processing
- Batch processing for large datasets
- Async training operations
- Incremental updates
- Smart sampling

### Resource Management
- Memory-efficient data loading
- Lazy loading for large datasets
- Connection pooling
- Query optimization

## Security Considerations

### Data Privacy
- Automatic PII detection
- Data anonymization
- Access control
- Audit logging

### API Security
- Authentication required
- Admin-only endpoints
- Rate limiting
- Input validation

### Model Security
- Version control
- Deployment validation
- Rollback capabilities
- A/B testing safeguards

## Best Practices

### 1. Data Quality
- Always validate augmented data
- Regular dataset cleaning
- Outlier detection
- Balance monitoring

### 2. Model Training
- Use separate test sets
- Regular evaluation
- Regression testing
- A/B testing before deployment

### 3. User Privacy
- Always anonymize training data
- Obtain user consent
- Secure data storage
- Regular privacy audits

### 4. System Monitoring
- Health checks automation
- Performance metrics tracking
- Alert configuration
- Regular system reviews

## Troubleshooting

### Common Issues

**1. Low Intent Accuracy:**
- Check training data quality
- Review intent distribution
- Analyze failure patterns
- Consider data augmentation

**2. Poor Entity Extraction:**
- Review normalization rules
- Check entity patterns
- Analyze extraction failures
- Update entity mappings

**3. Model Performance Degradation:**
- Check for data drift
- Review recent changes
- Run regression tests
- Consider rollback

**4. System Health Issues:**
- Check component status
- Review error logs
- Monitor resource usage
- Check database connectivity

## Future Enhancements

### Planned Features

1. **Advanced NLP Models:**
   - Transformer-based models
   - Multilingual support
   - Context-aware understanding

2. **Reinforcement Learning:**
   - User feedback integration
   - Adaptive learning
   - Personalization

3. **Advanced Analytics:**
   - Predictive analytics
   - User behavior modeling
   - Trend analysis

4. **Automation:**
   - Automatic dataset curation
   - Automated model deployment
   - Self-healing systems

## Conclusion

The AI Learning System provides a comprehensive framework for continuous improvement of the AI Assistant. It combines data collection, preprocessing, model training, and evaluation into a unified pipeline that enables the system to learn from user interactions and improve over time while maintaining privacy, security, and performance standards.

The system is designed to be:
- **Scalable:** Handles growing data volumes
- **Secure:** Protects user privacy
- **Maintainable:** Clear architecture and documentation
- **Extensible:** Easy to add new features
- **Reliable:** Robust error handling and monitoring

This learning system transforms the AI Assistant from a static chatbot into an intelligent, adaptive system that continuously improves based on real user interactions.