"""
AI Voice Provider - Speech-to-Text and Text-to-Speech
Independent voice layer that can be swapped with different providers
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('properties')


class VoiceProviderType(Enum):
    """Voice provider types"""
    WEB_SPEECH_API = "web_speech_api"
    AZURE_SPEECH = "azure_speech"
    GOOGLE_SPEECH = "google_speech"
    AMAZON_POLLY = "amazon_polly"
    CUSTOM = "custom"


@dataclass
class SpeechRecognitionResult:
    """Result from speech recognition"""
    success: bool
    text: str
    confidence: float
    language: str
    duration_ms: float
    error: Optional[str] = None


@dataclass
class SpeechSynthesisResult:
    """Result from speech synthesis"""
    success: bool
    audio_data: Optional[bytes]
    duration_ms: float
    error: Optional[str] = None


class VoiceProvider:
    """Base voice provider interface"""
    
    def __init__(self, provider_type: VoiceProviderType):
        self.provider_type = provider_type
        self.supported_languages = ['ar-SA', 'ar-IQ', 'en-US']
        self.is_available = False
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.is_available
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return self.supported_languages
    
    def speech_to_text(self, audio_data: bytes, language: str = 'ar-SA') -> SpeechRecognitionResult:
        """Convert speech to text"""
        raise NotImplementedError("Speech-to-text must be implemented by subclass")
    
    def text_to_speech(self, text: str, language: str = 'ar-SA') -> SpeechSynthesisResult:
        """Convert text to speech"""
        raise NotImplementedError("Text-to-speech must be implemented by subclass")
    
    def stop_speech(self):
        """Stop current speech synthesis"""
        raise NotImplementedError("Stop speech must be implemented by subclass")


class WebSpeechAPIProvider(VoiceProvider):
    """
    Web Speech API Provider (Browser-based)
    Uses browser's built-in speech recognition and synthesis
    """
    
    def __init__(self):
        super().__init__(VoiceProviderType.WEB_SPEECH_API)
        self.is_available = self._check_availability()
        self.recognition = None
        self.synthesis = None
    
    def _check_availability(self) -> bool:
        """Check if Web Speech API is available (server-side check)"""
        # Web Speech API is client-side only
        # This check is for server-side fallback providers
        return False
    
    def speech_to_text(self, audio_data: bytes, language: str = 'ar-SA') -> SpeechRecognitionResult:
        """
        For Web Speech API, this is handled client-side
        This method is for server-side processing only
        """
        return SpeechRecognitionResult(
            success=False,
            text="",
            confidence=0.0,
            language=language,
            duration_ms=0.0,
            error="Web Speech API is client-side only"
        )
    
    def text_to_speech(self, text: str, language: str = 'ar-SA') -> SpeechSynthesisResult:
        """
        For Web Speech API, this is handled client-side
        This method is for server-side processing only
        """
        return SpeechSynthesisResult(
            success=False,
            audio_data=None,
            duration_ms=0.0,
            error="Web Speech API is client-side only"
        )
    
    def stop_speech(self):
        """Stop current speech synthesis (client-side)"""
        pass


class VoiceAnalytics:
    """Voice conversation analytics"""
    
    def __init__(self):
        self.voice_conversations = 0
        self.total_recording_duration = 0
        self.stt_success_count = 0
        self.stt_failure_count = 0
        self.tts_usage_count = 0
        self.interrupted_responses = 0
        self.voice_commands = []
        self.unknown_voice_queries = []
    
    def record_voice_conversation(self, duration_ms: float, success: bool):
        """Record a voice conversation"""
        self.voice_conversations += 1
        self.total_recording_duration += duration_ms
        
        if success:
            self.stt_success_count += 1
        else:
            self.stt_failure_count += 1
    
    def record_tts_usage(self):
        """Record TTS usage"""
        self.tts_usage_count += 1
    
    def record_interruption(self):
        """Record interruption"""
        self.interrupted_responses += 1
    
    def record_voice_command(self, command: str):
        """Record voice command"""
        self.voice_commands.append(command)
    
    def record_unknown_query(self, text: str):
        """Record unknown voice query"""
        self.unknown_voice_queries.append(text)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get voice analytics statistics"""
        stt_total = self.stt_success_count + self.stt_failure_count
        stt_success_rate = (self.stt_success_count / stt_total * 100) if stt_total > 0 else 0
        
        return {
            'voice_conversations': self.voice_conversations,
            'total_recording_duration_ms': self.total_recording_duration,
            'average_recording_duration_ms': self.total_recording_duration / self.voice_conversations if self.voice_conversations > 0 else 0,
            'stt_success_rate': stt_success_rate,
            'stt_success_count': self.stt_success_count,
            'stt_failure_count': self.stt_failure_count,
            'tts_usage_count': self.tts_usage_count,
            'interrupted_responses': self.interrupted_responses,
            'voice_commands_count': len(self.voice_commands),
            'unknown_queries_count': len(self.unknown_voice_queries),
            'most_common_commands': self._get_most_common_commands()
        }
    
    def _get_most_common_commands(self) -> List[str]:
        """Get most common voice commands"""
        from collections import Counter
        if not self.voice_commands:
            return []
        
        counter = Counter(self.voice_commands)
        return [cmd for cmd, count in counter.most_common(5)]


class VoiceCommandHandler:
    """Handles voice commands and contextual references"""
    
    def __init__(self):
        self.commands = {
            'افتح الأول': 'open_first',
            'شوف الثاني': 'view_second',
            'أريد الأرخص': 'show_cheapest',
            'أريد أشوف هذا': 'view_this',
            'رجعني': 'go_back',
            'رجع للنتائج': 'back_to_results',
            'غير البحث': 'change_search',
            'اتصل بالدلال': 'contact_agent',
            'احفظ هذا': 'save_this',
            'قدم على الوظيفة': 'apply_job',
            'ابدأ من جديد': 'start_over',
            'وقف': 'stop',
            'اسكت': 'stop',
            'كافي': 'stop',
            'خلاص': 'stop'
        }
    
    def recognize_command(self, text: str) -> Optional[str]:
        """Recognize voice command from text"""
        text_normalized = text.strip().lower()
        
        for command_arabic, command_key in self.commands.items():
            if command_arabic.lower() in text_normalized:
                return command_key
        
        return None
    
    def execute_command(self, command: str, context: Dict) -> Dict[str, Any]:
        """Execute voice command with context"""
        command_mapping = {
            'open_first': self._open_first,
            'view_second': self._view_second,
            'show_cheapest': self._show_cheapest,
            'view_this': self._view_this,
            'go_back': self._go_back,
            'back_to_results': self._back_to_results,
            'change_search': self._change_search,
            'contact_agent': self._contact_agent,
            'save_this': self._save_this,
            'apply_job': self._apply_job,
            'start_over': self._start_over,
            'stop': self._stop
        }
        
        if command in command_mapping:
            return command_mapping[command](context)
        
        return {'success': False, 'error': 'Unknown command'}
    
    def _open_first(self, context: Dict) -> Dict[str, Any]:
        """Open first result"""
        results = context.get('results', [])
        if results:
            return {
                'success': True,
                'action': 'open_result',
                'result': results[0]
            }
        return {'success': False, 'error': 'No results available'}
    
    def _view_second(self, context: Dict) -> Dict[str, Any]:
        """View second result"""
        results = context.get('results', [])
        if len(results) >= 2:
            return {
                'success': True,
                'action': 'view_result',
                'result': results[1]
            }
        return {'success': False, 'error': 'No second result available'}
    
    def _show_cheapest(self, context: Dict) -> Dict[str, Any]:
        """Show cheapest result"""
        results = context.get('results', [])
        if results:
            # Sort by price if available
            sorted_results = sorted(results, key=lambda x: x.get('price', float('inf')))
            return {
                'success': True,
                'action': 'show_cheapest',
                'result': sorted_results[0]
            }
        return {'success': False, 'error': 'No results available'}
    
    def _view_this(self, context: Dict) -> Dict[str, Any]:
        """View current/focused result"""
        current_result = context.get('current_result')
        if current_result:
            return {
                'success': True,
                'action': 'view_result',
                'result': current_result
            }
        return {'success': False, 'error': 'No current result'}
    
    def _go_back(self, context: Dict) -> Dict[str, Any]:
        """Go back to previous state"""
        return {
            'success': True,
            'action': 'go_back'
        }
    
    def _back_to_results(self, context: Dict) -> Dict[str, Any]:
        """Go back to search results"""
        return {
            'success': True,
            'action': 'back_to_results'
        }
    
    def _change_search(self, context: Dict) -> Dict[str, Any]:
        """Change search parameters"""
        return {
            'success': True,
            'action': 'change_search'
        }
    
    def _contact_agent(self, context: Dict) -> Dict[str, Any]:
        """Contact agent for current result"""
        current_result = context.get('current_result')
        if current_result:
            return {
                'success': True,
                'action': 'contact_agent',
                'agent': current_result.get('agent')
            }
        return {'success': False, 'error': 'No current result'}
    
    def _save_this(self, context: Dict) -> Dict[str, Any]:
        """Save current result"""
        current_result = context.get('current_result')
        if current_result:
            return {
                'success': True,
                'action': 'save_result',
                'result': current_result
            }
        return {'success': False, 'error': 'No current result'}
    
    def _apply_job(self, context: Dict) -> Dict[str, Any]:
        """Apply to current job"""
        current_result = context.get('current_result')
        if current_result:
            return {
                'success': True,
                'action': 'apply_job',
                'job': current_result
            }
        return {'success': False, 'error': 'No current job'}
    
    def _start_over(self, context: Dict) -> Dict[str, Any]:
        """Start new conversation"""
        return {
            'success': True,
            'action': 'start_over'
        }
    
    def _stop(self, context: Dict) -> Dict[str, Any]:
        """Stop current operation"""
        return {
            'success': True,
            'action': 'stop'
        }


# Global instances
voice_analytics = VoiceAnalytics()
voice_command_handler = VoiceCommandHandler()