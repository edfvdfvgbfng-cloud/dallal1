// AI Chatbot Functionality
document.addEventListener('DOMContentLoaded', function() {
  console.log('[AI Chatbot] DOM Content Loaded - Initializing chatbot...');

  // Generate unique conversation ID
  const conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

  const chatbot = document.getElementById('ai-chatbot');
  const chatbotBtn = document.getElementById('ai-chatbot-btn');
  const chatbotClose = document.getElementById('chatbot-close');
  const chatbotInput = document.getElementById('chatbot-input');
  const chatbotSend = document.getElementById('chatbot-send');
  const chatbotMessages = document.getElementById('chatbot-messages');
  const chatbotNewChat = document.getElementById('chatbot-new-chat');
  const chatbotHistory = document.getElementById('chatbot-history');
  const chatbotSettings = document.getElementById('chatbot-settings');
  const chatbotVoiceMode = document.getElementById('voice-mode-btn');
  const chatbotAttach = document.getElementById('chatbot-attach');
  const chatbotVoice = document.getElementById('chatbot-voice');
  const chatbotFileInput = document.getElementById('chatbot-file-input');
  const quickOptions = document.querySelectorAll('.quick-option');

  console.log('[AI Chatbot] Elements query completed');
  console.log('[AI Chatbot] chatbot:', chatbot);
  console.log('[AI Chatbot] chatbotBtn:', chatbotBtn);
  console.log('[AI Chatbot] chatbotClose:', chatbotClose);

  // Check if chatbot elements exist
  if (!chatbot) {
    console.error('[AI Chatbot] Chatbot container not found');
    return;
  }

  if (!chatbotBtn) {
    console.error('[AI Chatbot] Chatbot button not found');
    return;
  }

  if (!chatbotClose) {
    console.error('[AI Chatbot] Chatbot close button not found');
    return;
  }

  console.log('[AI Chatbot] All elements found, initializing...');

  // Check optional elements
  if (!chatbotInput) console.warn('[AI Chatbot] Chatbot input not found');
  if (!chatbotSend) console.warn('[AI Chatbot] Chatbot send button not found');
  if (!chatbotMessages) console.warn('[AI Chatbot] Chatbot messages container not found');

  // Voice Assistant Integration
  let speechRecognition = null;
  let speechSynthesis = window.speechSynthesis;
  let isRecording = false;
  let isSpeaking = false;
  let currentUtterance = null;
  let voiceConversationEnabled = false;
  let voiceMode = 'push-to-talk';

  // Initialize Speech Recognition
  function initSpeechRecognition() {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      speechRecognition = new SpeechRecognition();
      speechRecognition.continuous = false;
      speechRecognition.interimResults = true;
      speechRecognition.lang = 'ar-SA';
      speechRecognition.maxAlternatives = 1;

      speechRecognition.onstart = function() {
        isRecording = true;
        chatbotVoice.classList.add('recording');
        showVoiceStatus('🎤 أستمع...');
      };

      speechRecognition.onresult = function(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        if (interimTranscript) {
          showVoiceStatus(`" ${interimTranscript}`);
        }

        if (finalTranscript) {
          showVoiceStatus('🧠 جاري فهم كلامك...');
          chatbotInput.value = finalTranscript;
          setTimeout(() => {
            sendMessage();
          }, 500);
        }
      };

      speechRecognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        chatbotVoice.classList.remove('recording');

        if (event.error === 'not-allowed') {
          showVoiceStatus('❌ ممنوع استخدام الميكروفون');
        } else if (event.error === 'no-speech') {
          showVoiceStatus('🔇 ماكو كلام');
        } else {
          showVoiceStatus('❌ خطأ في الصوت');
        }
      };

      speechRecognition.onend = function() {
        isRecording = false;
        chatbotVoice.classList.remove('recording');
      };

      console.log('[AI Chatbot] Speech recognition initialized');
    } else {
      console.warn('[AI Chatbot] Speech recognition not supported');
      if (chatbotVoice) chatbotVoice.style.display = 'none';
    }
  }

  // Voice status display
  function showVoiceStatus(status) {
    const existingStatus = document.querySelector('.voice-status');
    if (existingStatus) {
      existingStatus.remove();
    }

    const statusDiv = document.createElement('div');
    statusDiv.className = 'voice-status';
    statusDiv.textContent = status;
    if (chatbotInput && chatbotInput.parentElement) {
      chatbotInput.parentElement.insertBefore(statusDiv, chatbotInput);
    }

    setTimeout(() => {
      if (statusDiv.parentNode) {
        statusDiv.remove();
      }
    }, 3000);
  }

  // Start voice recording
  function startVoiceRecording() {
    if (!speechRecognition) {
      showVoiceStatus('❌ الصوت غير مدعوم');
      return;
    }

    if (isRecording) {
      stopVoiceRecording();
      return;
    }

    try {
      speechRecognition.start();
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      showVoiceStatus('❌ خطأ في التسجيل');
    }
  }

  // Stop voice recording
  function stopVoiceRecording() {
    if (speechRecognition && isRecording) {
      speechRecognition.stop();
    }
  }

  // Process voice command
  function processVoiceCommand(text) {
    const normalized = text.toLowerCase().trim();

    if (normalized.includes('توقف') || normalized.includes('اكتفى') || normalized.includes('خلاص')) {
      return 'stop';
    }

    if (normalized.includes('امسح') || normalized.includes('مسح') || normalized.includes('نظف')) {
      return 'clear';
    }

    if (normalized.includes('جديد') || normalized.includes('محادثة جديدة')) {
      return 'new';
    }

    return null;
  }

  // Preprocess Arabic text for voice input
  function preprocessArabicText(text) {
    let normalized = text;
    normalized = normalized.replace(/أ/g, 'ا');
    normalized = normalized.replace(/إ/g, 'ا');
    normalized = normalized.replace(/آ/g, 'ا');
    normalized = normalized.replace(/ة/g, 'ه');
    normalized = normalized.replace(/[\u064B-\u065F]/g, '');
    normalized = normalized.replace(/\s+/g, ' ').trim();
    return normalized;
  }

  let conversationState = {
    intent: null,
    data: {},
    step: 0
  };

  // Toggle chatbot
  chatbotBtn.addEventListener('click', function() {
    console.log('[AI Chatbot] Button clicked');
    chatbot.classList.toggle('active');
    console.log('[AI Chatbot] Chatbot classes:', chatbot.classList.toString());
    console.log('[AI Chatbot] Is active:', chatbot.classList.contains('active'));
  });

  chatbotClose.addEventListener('click', function() {
    console.log('[AI Chatbot] Close button clicked');
    chatbot.classList.remove('active');
    console.log('[AI Chatbot] Chatbot closed');
  });

  // Quick options
  quickOptions.forEach(option => {
    option.addEventListener('click', function() {
      const intent = this.getAttribute('data-intent');
      addUserMessage(this.textContent);
      handleIntent(intent);
    });
  });

  // Send message
  chatbotSend.addEventListener('click', sendMessage);
  if (chatbotInput) {
    chatbotInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }

  // New chat
  if (chatbotNewChat) {
    chatbotNewChat.addEventListener('click', function() {
      chatbotMessages.innerHTML = '<div class="message bot-message"><div class="message-content"><p>السلام عليكم 👋</p><p>أهلاً بك، شلون أگدر أساعدك اليوم؟</p></div></div>';
      conversationState = { intent: null, data: {}, step: 0 };
    });
  }

  // Voice mode toggle
  if (chatbotVoiceMode) {
    chatbotVoiceMode.addEventListener('click', function() {
      voiceConversationEnabled = !voiceConversationEnabled;
      this.textContent = voiceConversationEnabled ? '🔊 صوت مفعل' : '🔇 صوت معطل';
      this.classList.toggle('active', voiceConversationEnabled);

      if (voiceConversationEnabled) {
        initSpeechRecognition();
      }
    });
  }

  // Attach file
  if (chatbotAttach && chatbotFileInput) {
    chatbotAttach.addEventListener('click', function() {
      chatbotFileInput.click();
    });

    chatbotFileInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        addUserMessage(`📎 ملف مرفق: ${file.name}`);
        addBotMessage('تم استلام الملف. جاري معالجته...');
        setTimeout(() => {
          addBotMessage('تمت معالجة الملف بنجاح. شلون أگدر أساعدك بعد؟');
        }, 1500);
      }
    });
  }

  // Voice recording
  if (chatbotVoice) {
    chatbotVoice.addEventListener('click', function() {
      if (!speechRecognition) {
        initSpeechRecognition();
      }

      if (voiceMode === 'push-to-talk') {
        if (isRecording) {
          stopVoiceRecording();
        } else {
          startVoiceRecording();
        }
      }
    });
  }

  // Intent handling
  function handleIntent(intent) {
    conversationState.intent = intent;
    conversationState.step = 1;

    switch(intent) {
      case 'buy_property':
        addBotMessage('حسناً، تريد شراء عقار. في أي محافظة تبحث؟');
        break;
      case 'sell_property':
        addBotMessage('حسناً، تريد بيع عقار. هل عندك تفاصيل عن العقار؟');
        break;
      case 'broker':
        addBotMessage('حسناً، أنت دلال. شلون أگدر أساعدك؟');
        break;
      case 'job':
        addBotMessage('حسناً، تبحث عن وظيفة. في أي مجال؟');
        break;
      default:
        addBotMessage('فهمت طلبك. جاري البحث...');
        setTimeout(() => {
          addBotMessage('سأقوم بمساعدتك في هذا الطلب.');
        }, 1000);
    }
  }

  async function sendMessage() {
    const message = chatbotInput ? chatbotInput.value.trim() : '';
    if (!message) return;

    let processedMessage = message;
    let isVoiceInput = chatbotVoice ? chatbotVoice.classList.contains('recording') : false;

    if (isVoiceInput) {
      processedMessage = preprocessArabicText(message);
      if (chatbotInput) chatbotInput.value = processedMessage;
    }

    const command = processVoiceCommand(processedMessage);
    if (command === 'stop') {
      showVoiceStatus('توقفت عن التحدث 🛑');
      if (chatbotInput) chatbotInput.value = '';
      return;
    }

    addUserMessage(processedMessage);
    if (chatbotInput) chatbotInput.value = '';
    showVoiceStatus('توقفت عن التحدث 🛑');

    await processMessage(processedMessage, isVoiceInput);
  }

  async function processMessage(message, isVoiceInput) {
    showTypingIndicator();

    if (isVoiceInput) {
      showVoiceStatus('🔎 جاري البحث...');
    }

    try {
      const response = await fetch('/api/chatbot/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
          message: message,
          conversation_id: conversationId,
          state: conversationState,
          is_voice: isVoiceInput
        })
      });

      const data = await response.json();
      hideTypingIndicator();

      if (isVoiceInput) {
        showVoiceStatus('💬 أجيب...');
      }

      if (data.success) {
        addBotMessage(data.response);

        if (data.state) {
          conversationState = data.state;
        }

        if (data.property_results && data.property_results.length > 0) {
          displayPropertyResults(data.property_results);
        }
      } else {
        addBotMessage(data.response || 'حدث خطأ. يرجى المحاولة مرة أخرى.');
      }
    } catch (error) {
      console.error('Chatbot API error:', error);
      hideTypingIndicator();
      addBotMessage('حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.');
    }
  }

  function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatbotMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatbotMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatbotMessages.appendChild(typingDiv);
    scrollToBottom();
  }

  function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  function scrollToBottom() {
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
  }

  function displayPropertyResults(properties) {
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'property-results';

    properties.forEach((property, index) => {
      const propertyCard = document.createElement('div');
      propertyCard.className = 'property-card';
      propertyCard.innerHTML = `
        <div class="property-image">
          <img src="${property.image || '/static/images/placeholder.jpg'}" alt="${property.title}">
        </div>
        <div class="property-info">
          <h4>${property.title}</h4>
          <p>${property.location}</p>
          <p class="price">${property.price}</p>
          <button class="btn btn-sm btn-primary" onclick="viewProperty(${property.id})">عرض</button>
        </div>
      `;
      resultsDiv.appendChild(propertyCard);
    });

    chatbotMessages.appendChild(resultsDiv);
    scrollToBottom();
  }

  function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
  }

  // Initialize voice features
  if (chatbotVoice) {
    initSpeechRecognition();
  }

  console.log('[AI Chatbot] Initialization complete');
});