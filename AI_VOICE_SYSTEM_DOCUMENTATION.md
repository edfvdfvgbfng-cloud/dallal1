# AI Voice System Documentation

## Overview

The AI Voice System integrates comprehensive voice capabilities into the Dalal real-estate platform's AI Assistant, enabling natural language voice interaction while maintaining the same intelligent core.

## Architecture

```
صوت المستخدم
      ↓
Speech-to-Text (Web Speech API)
      ↓
Arabic Normalization (Preprocessing)
      ↓
Intent Detection
      ↓
Entity Extraction
      ↓
Conversation Context
      ↓
AI Agent (Same Core)
      ↓
Search / Tools / Database
      ↓
AI Response
      ↓
Text-to-Speech (Web Speech API)
      ↓
صوت المساعد
```

## Components

### 1. Voice Provider Module (`ai_voice_provider.py`)

**VoiceProvider Base Class:**
- Abstract interface for different voice providers
- Supports multiple provider types: Web Speech API, Azure Speech, Google Speech, Amazon Polly
- Extensible for future provider additions

**WebSpeechAPIProvider:**
- Client-side implementation using browser's Web Speech API
- Handles Speech Recognition (STT)
- Handles Speech Synthesis (TTS)
- Supports Arabic (ar-SA) and Iraqi Arabic (ar-IQ)

**VoiceAnalytics:**
- Tracks voice conversation statistics
- Records STT success/failure rates
- Monitors TTS usage
- Tracks voice commands
- Analytics for continuous improvement

**VoiceCommandHandler:**
- Recognizes voice commands in Arabic
- Context-aware command execution
- Supports navigation, search, and action commands

### 2. Frontend Integration (`base.html`)

**Voice Button:**
- Microphone button in chatbot interface
- Visual feedback for recording state
- Animation for active recording

**Speech Recognition:**
- Web Speech API integration
- Arabic language support (ar-SA)
- Real-time transcription display
- Interim results for better UX

**Text-to-Speech:**
- Arabic voice synthesis
- Response text cleanup for speech
- Rate and pitch optimization for Arabic
- Voice selection for Arabic voices

**Voice Mode Toggle:**
- Push-to-Talk mode (manual recording)
- Continuous conversation mode (auto-recording)
- Voice mode indicator

**Voice Commands:**
- Stop commands: "وقف", "اسكت", "كافي", "خلاص"
- Navigation: "افتح الأول", "شوف الثاني", "رجعني"
- Actions: "أريد الأرخص", "اتصل بالدلال", "احفظ هذا"
- Search: "غير البحث", "ابدأ من جديد"

**Arabic Preprocessing:**
- Arabic number word conversion ("مئة" → "100")
- Arabic numeral conversion ("٠" → "0")
- Speech error correction ("بل ب" → "بال")
- Common mispronunciation handling

### 3. Backend Integration

**AI Conversation Manager:**
- Voice input processing with `is_voice` flag
- Voice interaction logging
- Voice command detection
- Integration with existing AI Agent

**Voice Interaction Log Model:**
- Recording duration and quality
- STT results and confidence
- Intent and entity extraction
- TTS usage and duration
- User interaction tracking
- Interruption detection

**API Updates:**
- `/api/chatbot/` endpoint accepts `is_voice` parameter
- Voice analytics included in response
- Voice interaction logging

### 4. CSS Styling (`ai_chatbot_styles.css`)

**Voice Button Styles:**
- Gradient background
- Recording animation (pulse effect)
- Processing state styling
- Hover effects

**Voice Status Indicator:**
- Status messages display
- Fade-in animation
- Context-aware positioning

**Voice Mode Button:**
- Toggle button styling
- Active state indication
- Dark mode support

**Voice Command Suggestions:**
- Command button styling
- Hover effects
- Responsive layout

**Audio Wave Animation:**
- Visual feedback for recording
- Waveform animation
- Professional appearance

## Features

### 1. Speech-to-Text (STT)

**Capabilities:**
- Arabic Fusha (Standard Arabic)
- Iraqi Arabic dialect support
- Fast speech recognition
- Long sentence handling
- Number recognition
- Location name recognition
- Real-time transcription

**Language Support:**
- Arabic (ar-SA) - Primary
- Iraqi Arabic (ar-IQ) - Enhanced
- English (en-US) - Fallback

### 2. Text-to-Speech (TTS)

**Capabilities:**
- Natural Arabic voice synthesis
- Response text optimization
- Emoji removal for speech
- Long text summarization
- Rate and pitch control
- Voice selection

**Smart Features:**
- Doesn't read long lists (20+ items)
- Summarizes results: "لكيتلك 20 عقار. راح أعرضهم أمامك"
- Appropriate speaking rate for Arabic

### 3. Voice Conversation Flow

**Push-to-Talk Mode:**
- User presses microphone button
- Speaks while holding button
- Releases to stop recording
- System processes and responds

**Continuous Mode:**
- System auto-starts recording
- Alternates between listening and speaking
- Timeout for silence detection
- User can stop anytime

**Barge-In Detection:**
- User typing stops TTS
- Voice button press stops TTS
- Stop commands stop TTS
- Seamless interruption handling

### 4. Voice Commands

**Navigation Commands:**
- "افتح الأول" - Open first result
- "شوف الثاني" - View second result
- "أريد أشوف هذا" - View current item
- "رجعني" - Go back
- "رجع للنتائج" - Back to results

**Action Commands:**
- "أريد الأرخص" - Show cheapest
- "أريد الأغلى" - Show most expensive
- "اتصل بالدلال" - Contact agent
- "احفظ هذا" - Save current item
- "قدم على الوظيفة" - Apply to job

**Control Commands:**
- "غير البحث" - Change search
- "ابدأ من جديد" - Start over
- "وقف/اسكت/كافي/خلاص" - Stop speaking

### 5. Context-Aware Voice

**Pronoun Resolution:**
- "الأول" → Refers to first result
- "شكد سعره؟" → Refers to current item
- "أريد أتواصل وياه" → Refers to agent

**State Awareness:**
- Knows current search results
- Tracks selected items
- Maintains conversation context
- Understands implicit references

### 6. Error Handling

**STT Errors:**
- Microphone permission denied
- Browser not supported
- Network issues
- Timeout handling

**TTS Errors:**
- Voice not available
- Synthesis failure
- Interruption handling

**Fallback:**
- Graceful degradation to text
- Clear error messages
- User guidance

### 7. Privacy & Security

**Privacy Features:**
- No permanent audio storage
- Temporary audio processing
- Audio deleted after STT
- Optional recording with consent

**Security:**
- CSRF protection
- User authentication
- Voice log anonymization
- Secure API endpoints

### 8. Analytics

**Voice Metrics:**
- Voice conversation count
- Average recording duration
- STT success rate
- STT failure rate
- TTS usage count
- Interrupted responses
- Voice command frequency
- Unknown voice queries

**Continuous Improvement:**
- Pattern recognition
- User preference learning
- Error analysis
- Performance optimization

## Integration Points

### 1. AI Agent Integration

**Shared Core:**
- Same Intent Detection engine
- Same Entity Extraction
- Same Conversation Memory
- Same Tool Calling system
- Same Search capabilities

**Voice-specific Processing:**
- Arabic normalization
- Voice command handling
- Voice interaction logging
- TTS response formatting

### 2. Database Integration

**VoiceInteractionLog Model:**
- Records all voice interactions
- Stores STT/TTS data
- Tracks user corrections
- Links to conversation context

**Analytics Integration:**
- Voice statistics in admin dashboard
- Performance monitoring
- User behavior analysis

### 3. API Integration

**Chatbot API Enhancement:**
- `is_voice` parameter
- Voice-specific responses
- Voice command handling
- Analytics data

## Usage Examples

### Example 1: Property Search with Voice

```
User: 🎤 "أريد بيت بالبصرة"
System: 🎤 "أكيد، شكد ميزانيتك تقريبًا؟"
User: 🎤 "حدود مية وخمسين مليون"
System: 🎤 "تمام، تفضل منطقة معينة؟"
User: 🎤 "العشار"
System: 🎤 "حلو، خلي أبحث لك..."
[Results displayed]
```

### Example 2: Voice Commands

```
System: [Shows 5 properties]
User: 🎤 "أريد الأرخص"
System: [Properties sorted by price]
User: 🎤 "افتح الأول"
System: [Opens first property details]
User: 🎤 "أريد أتواصل وياه"
System: [Opens contact form for agent]
```

### Example 3: Mixed Mode

```
User: 🎤 "أريد بيت بالبصرة"
System: 🎤 "أكيد، شكد ميزانيتك تقريبًا؟"
User: [Types: "150 مليون"]
System: [Processes text input]
User: 🎤 "العشار"
System: 🎤 "حلو، خلي أبحث لك..."
```

## Testing

### Browser Compatibility

**Desktop:**
- Chrome 25+ (Full support)
- Edge 79+ (Full support)
- Firefox (Partial support)
- Safari (Partial support)

**Mobile:**
- Android Chrome (Full support)
- iOS Safari (Partial support)
- Samsung Internet (Full support)

### Test Scenarios

**1. Microphone Permission:**
- Allow microphone access
- Deny microphone access
- Re-request permission

**2. Speech Recognition:**
- Arabic Fusha
- Iraqi Arabic
- Numbers
- Locations
- Fast speech
- Long sentences

**3. Text-to-Speech:**
- Short responses
- Long responses
- Lists of results
- Emoji handling
- Arabic pronunciation

**4. Voice Commands:**
- Navigation commands
- Action commands
- Control commands
- Context references

**5. Error Handling:**
- No microphone
- Browser not supported
- Network issues
- Timeout

**6. User Interaction:**
- Barge-in (typing while speaking)
- Voice button press while speaking
- Stop commands
- Mode switching

## Configuration

### Frontend Configuration

```javascript
// Voice settings
const voiceSettings = {
  language: 'ar-SA',
  continuous: false,
  interimResults: true,
  maxAlternatives: 1,
  speechRate: 0.9,
  speechPitch: 1.0
};
```

### Backend Configuration

```python
# Voice analytics
voice_analytics = VoiceAnalytics()

# Voice command handler
voice_command_handler = VoiceCommandHandler()

# Conversation manager
conversation_manager = ConversationManager(
    voice_enabled=True,
    voice_analytics=voice_analytics,
    voice_command_handler=voice_command_handler
)
```

## Performance Optimization

### Frontend

**Speech Recognition:**
- Lazy initialization
- Reuse recognition instance
- Clean up resources
- Debounce commands

**Text-to-Speech:**
- Voice caching
- Queue management
- Cancellation handling
- Rate limiting

### Backend

**Voice Logging:**
- Async logging
- Batch processing
- Index optimization
- Query optimization

**Analytics:**
- Real-time tracking
- Periodic aggregation
- Data cleanup
- Performance monitoring

## Future Enhancements

### Planned Features

1. **Advanced STT:**
   - Server-side STT providers
   - Custom language models
   - Real-time transcription
   - Noise cancellation

2. **Enhanced TTS:**
   - Multiple voice options
   - Emotion detection
   - Custom voice training
   - SSML support

3. **Voice Activity Detection:**
   - Automatic silence detection
   - Speech start/end detection
   - Noise filtering
   - Adaptive thresholding

4. **Advanced Commands:**
   - Natural language commands
   - Multi-step commands
   - Conditional commands
   - Custom command creation

5. **Analytics:**
   - Sentiment analysis
   - User profiling
   - A/B testing
   - Performance metrics

## Troubleshooting

### Common Issues

**1. Microphone Not Working:**
- Check browser permissions
- Verify device settings
- Test with other apps
- Check console errors

**2. Poor Recognition:**
- Check audio quality
- Verify language settings
- Try quieter environment
- Check microphone position

**3. TTS Not Speaking:**
- Check browser support
- Verify voice availability
- Check volume settings
- Review console errors

**4. Commands Not Recognized:**
- Check command patterns
- Verify Arabic normalization
- Test with known commands
- Check voice logs

## Maintenance

### Regular Tasks

1. **Monitor Analytics:**
   - Review voice conversation stats
   - Check STT success rates
   - Monitor TTS usage
   - Analyze command patterns

2. **Update Commands:**
   - Add new commands
   - Update patterns
   - Improve recognition
   - Test effectiveness

3. **Optimize Performance:**
   - Review response times
   - Check resource usage
   - Optimize queries
   - Clean up logs

4. **User Feedback:**
   - Collect feedback
   - Analyze issues
   - Implement improvements
   - Test changes

## Conclusion

The AI Voice System provides comprehensive voice capabilities while maintaining the intelligent core of the AI Assistant. It supports natural Arabic conversation, powerful voice commands, and seamless integration with the existing platform features.

The system is designed for:
- **Natural Interaction:** Voice-first design with text fallback
- **Accessibility:** Voice input for all users
- **Performance:** Fast, responsive voice processing
- **Privacy:** Secure, temporary audio processing
- **Extensibility:** Easy to add new features and providers

The voice integration enhances the user experience while maintaining the platform's core functionality and intelligence.