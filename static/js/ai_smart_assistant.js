// AI Smart Assistant JavaScript

class SmartAssistant {
    constructor() {
        this.conversationId = this.generateConversationId();
        this.apiBaseUrl = '/api/ai/smart/';
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        this.initializeEventListeners();
    }
    
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeEventListeners() {
        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', () => {
                const message = button.dataset.message;
                this.sendMessage(message);
            });
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
        });
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    async sendMessage(overrideMessage = null) {
        const message = overrideMessage || this.messageInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Call API
            const response = await fetch(this.apiBaseUrl + 'chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId,
                    render_results: true
                })
            });
            
            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add assistant response
            this.addAssistantResponse(data);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.', 'assistant');
        }
    }
    
    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'assistant' ? '🤖' : '👤';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Parse content for basic formatting
        const formattedContent = this.formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addAssistantResponse(data) {
        const response = data.response || '';
        const action = data.action;
        const results = data.rendered_results || [];
        const metadata = data.metadata || {};
        
        // Add main response message
        this.addMessage(response, 'assistant');
        
        // Add result cards if available
        if (results && results.length > 0) {
            this.addResultCards(results);
        }
        
        // Handle special actions
        if (action === 'confirm_create_listing') {
            this.addConfirmationButtons('create_listing', metadata.listing_data);
        } else if (action === 'suggest_alternatives') {
            this.addSuggestAlternativesButton();
        }
    }
    
    formatMessage(content) {
        // Convert basic formatting
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert emojis
        formatted = this.convertEmojis(formatted);
        
        return formatted;
    }
    
    convertEmojis(text) {
        const emojiMap = {
            '🏠': 'house',
            '🏨': 'hotel',
            '💼': 'briefcase',
            '🔧': 'wrench',
            '🔨': 'hammer',
            '🤝': 'handshake',
            '📍': 'location',
            '💰': 'money',
            '📐': 'straight_ruler',
            '🛏️': 'bed',
            '⭐': 'star',
            '👤': 'person',
            '💬': 'speech_balloon',
            '👁️': 'eye',
            '🎯': 'target',
            '👥': 'people',
            '👨‍👩‍👧‍👦': 'family',
            '🏢': 'office',
            '📋': 'clipboard',
            '⏰': 'alarm_clock',
            '🔄': 'arrows_counterclockwise',
            '🎉': 'party_popper',
            '👋': 'waving_hand',
        };
        
        return text;
    }
    
    addResultCards(results) {
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'results-container';
        
        results.forEach(result => {
            const card = this.createResultCard(result);
            resultsContainer.appendChild(card);
        });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content"></div>
        `;
        
        messageDiv.querySelector('.message-content').appendChild(resultsContainer);
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Header
        const header = document.createElement('div');
        header.className = 'card-header';
        header.innerHTML = `
            <span class="card-emoji">${result.emoji}</span>
            <span class="card-title">${result.title}</span>
            <span class="card-score">${Math.round(result.score * 100)}%</span>
        `;
        card.appendChild(header);
        
        // Fields
        const fields = document.createElement('div');
        fields.className = 'card-fields';
        result.fields.forEach(field => {
            const fieldDiv = document.createElement('div');
            fieldDiv.className = 'card-field';
            fieldDiv.innerHTML = `
                <span class="card-field-label">${field.label}</span>
                <span>${field.value}</span>
            `;
            fields.appendChild(fieldDiv);
        });
        card.appendChild(fields);
        
        // Actions
        const actions = document.createElement('div');
        actions.className = 'card-actions';
        result.actions.forEach(action => {
            const button = document.createElement('button');
            button.className = 'action-button';
            if (action.action === 'contact_broker') {
                button.classList.add('secondary');
            }
            button.textContent = action.label;
            button.onclick = () => this.handleCardAction(action);
            actions.appendChild(button);
        });
        card.appendChild(actions);
        
        return card;
    }
    
    handleCardAction(action) {
        if (action.action === 'view' && action.url) {
            window.location.href = action.url;
        } else if (action.action === 'contact_broker' && action.broker_id) {
            this.contactBroker(action.broker_id);
        } else if (action.action === 'contact' && action.url) {
            window.location.href = action.url;
        }
    }
    
    contactBroker(brokerId) {
        // Implement broker contact logic
        // This would integrate with the messaging system
        console.log('Contacting broker:', brokerId);
        // For now, redirect to messages
        window.location.href = `/messages/?broker=${brokerId}`;
    }
    
    addConfirmationButtons(actionType, data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="confirmation-buttons">
                    <button class="action-button" onclick="confirmAction('${actionType}')">✅ نعم، متابعة</button>
                    <button class="action-button secondary" onclick="cancelAction()">✏️ تعديل</button>
                    <button class="action-button secondary" onclick="cancelAction()">❌ إلغاء</button>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addSuggestAlternativesButton() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <button class="action-button" onclick="suggestAlternatives()">🔍 توسيع البحث</button>
            </div>
        `;
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.chatMessages.appendChild(this.typingIndicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return '';
    }
    
    async resetConversation() {
        try {
            await fetch(this.apiBaseUrl + 'reset/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    conversation_id: this.conversationId
                })
            });
            
            // Clear chat messages
            this.chatMessages.innerHTML = '';
            
            // Add welcome message
            this.addMessage('تم بدء محادثة جديدة. كيف يمكنني مساعدتك؟', 'assistant');
            
            // Generate new conversation ID
            this.conversationId = this.generateConversationId();
            
        } catch (error) {
            console.error('Error resetting conversation:', error);
        }
    }
}

// Global functions for button handlers
let assistant;

async function sendMessage() {
    await assistant.sendMessage();
}

function handleKeyDown(event) {
    assistant.handleKeyDown(event);
}

async function resetConversation() {
    await assistant.resetConversation();
}

async function confirmAction(actionType) {
    try {
        const response = await fetch('/api/ai/smart/confirm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': assistant.getCsrfToken()
            },
            body: JSON.stringify({
                conversation_id: assistant.conversationId,
                confirmed: true
            })
        });
        
        const data = await response.json();
        assistant.addAssistantResponse(data);
        
    } catch (error) {
        console.error('Error confirming action:', error);
    }
}

async function cancelAction() {
    try {
        const response = await fetch('/api/ai/smart/confirm/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': assistant.getCsrfToken()
            },
            body: JSON.stringify({
                conversation_id: assistant.conversationId,
                confirmed: false
            })
        });
        
        const data = await response.json();
        assistant.addAssistantResponse(data);
        
    } catch (error) {
        console.error('Error canceling action:', error);
    }
}

async function suggestAlternatives() {
    try {
        const response = await fetch('/api/ai/suggest-alternatives/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': assistant.getCsrfToken()
            },
            body: JSON.stringify({
                conversation_id: assistant.conversationId
            })
        });
        
        const data = await response.json();
        assistant.addAssistantResponse(data);
        
    } catch (error) {
        console.error('Error suggesting alternatives:', error);
    }
}

// Initialize assistant when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    assistant = new SmartAssistant();
});
