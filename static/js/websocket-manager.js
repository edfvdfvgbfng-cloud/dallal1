/**
 * WebSocket Manager - Advanced WebSocket Client
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection state management
 * - Heartbeat/ping
 * - Message queue for offline
 * - Online/offline presence
 * - Last seen tracking
 * - Delivery status events
 * - Typing indicators
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.url = null;
        this.conversationId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.isManualClose = false;
        this.heartbeatInterval = null;
        this.heartbeatIntervalTime = 30000; // 30 seconds
        this.messageQueue = [];
        this.isQueueProcessing = false;
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, reconnecting
        this.lastMessageTime = null;
        this.eventHandlers = {};

        // Offline message queue in localStorage
        this.offlineQueueKey = 'chat_offline_queue';
        this.loadOfflineQueue();
    }

    /**
     * Connect to WebSocket
     * @param {string} conversationId - Conversation ID
     */
    connect(conversationId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        this.conversationId = conversationId;
        this.isManualClose = false;
        this.connectionState = 'connecting';

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.url = `${protocol}//${window.location.host}/ws/chat/${conversationId}/`;

        console.log(`Connecting to WebSocket: ${this.url}`);

        try {
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleConnectionError(error);
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.ws.onopen = (event) => this.handleOpen(event);
        this.ws.onclose = (event) => this.handleClose(event);
        this.ws.onerror = (event) => this.handleError(event);
        this.ws.onmessage = (event) => this.handleMessage(event);
    }

    /**
     * Handle WebSocket open
     */
    handleOpen(event) {
        console.log('WebSocket connected');
        this.connectionState = 'connected';
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        // Start heartbeat
        this.startHeartbeat();

        // Process queued messages
        this.processMessageQueue();

        // Emit connected event
        this.emit('connected', { conversationId: this.conversationId });

        // Send online status
        this.sendOnlineStatus();
    }

    /**
     * Handle WebSocket close
     */
    handleClose(event) {
        console.log('WebSocket closed:', event.code, event.reason);

        this.connectionState = 'disconnected';
        this.stopHeartbeat();

        if (!this.isManualClose) {
            this.emit('disconnected', { code: event.code, reason: event.reason });
            this.scheduleReconnect();
        }
    }

    /**
     * Handle WebSocket error
     */
    handleError(event) {
        console.error('WebSocket error:', event);
        this.emit('error', { event });
    }

    /**
     * Handle WebSocket message
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.lastMessageTime = Date.now();

            console.log('WebSocket message received:', data.type);

            // Handle different message types
            switch (data.type) {
                case 'chat_message':
                    this.emit('message', data);
                    break;
                case 'typing_indicator':
                    this.emit('typing', data);
                    break;
                case 'message_read':
                    this.emit('messageRead', data);
                    break;
                case 'message_delivered':
                    this.emit('messageDelivered', data);
                    break;
                case 'message_edited':
                    this.emit('messageEdited', data);
                    break;
                case 'message_deleted':
                    this.emit('messageDeleted', data);
                    break;
                case 'user_joined':
                    this.emit('userJoined', data);
                    break;
                case 'user_left':
                    this.emit('userLeft', data);
                    break;
                case 'user_online':
                    this.emit('userOnline', data);
                    break;
                case 'user_offline':
                    this.emit('userOffline', data);
                    break;
                case 'reaction':
                    this.emit('reaction', data);
                    break;
                case 'error':
                    this.emit('wsError', data);
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    /**
     * Handle connection error
     */
    handleConnectionError(error) {
        console.error('Connection error:', error);
        this.connectionState = 'disconnected';
        this.emit('connectionError', { error });
        this.scheduleReconnect();
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            this.connectionState = 'failed';
            this.emit('reconnectFailed', { attempts: this.reconnectAttempts });
            return;
        }

        this.reconnectAttempts++;
        this.connectionState = 'reconnecting';

        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });

        setTimeout(() => {
            if (this.connectionState === 'reconnecting') {
                this.connect(this.conversationId);
            }
        }, delay);
    }

    /**
     * Start heartbeat/ping
     */
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, this.heartbeatIntervalTime);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Send message through WebSocket
     * @param {object} data - Message data
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('Error sending message:', error);
                this.queueMessage(data);
                return false;
            }
        } else {
            console.log('WebSocket not connected, queuing message');
            this.queueMessage(data);
            return false;
        }
    }

    /**
     * Queue message for later sending
     * @param {object} data - Message data
     */
    queueMessage(data) {
        const queuedMessage = {
            data: data,
            timestamp: Date.now(),
            conversationId: this.conversationId
        };

        this.messageQueue.push(queuedMessage);
        this.saveOfflineQueue();

        console.log('Message queued:', data.type);
        this.emit('messageQueued', { message: data });
    }

    /**
     * Process queued messages
     */
    async processMessageQueue() {
        if (this.isQueueProcessing || this.messageQueue.length === 0) {
            return;
        }

        this.isQueueProcessing = true;
        console.log(`Processing ${this.messageQueue.length} queued messages`);

        while (this.messageQueue.length > 0) {
            const queued = this.messageQueue.shift();

            // Skip messages older than 5 minutes
            if (Date.now() - queued.timestamp > 300000) {
                console.log('Skipping old queued message');
                continue;
            }

            // Send message
            const sent = this.send(queued.data);
            if (!sent) {
                // Put back in queue if failed
                this.messageQueue.unshift(queued);
                break;
            }

            // Small delay between messages
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        this.saveOfflineQueue();
        this.isQueueProcessing = false;

        console.log('Message queue processed');
        this.emit('queueProcessed', { remaining: this.messageQueue.length });
    }

    /**
     * Save offline queue to localStorage
     */
    saveOfflineQueue() {
        try {
            localStorage.setItem(this.offlineQueueKey, JSON.stringify(this.messageQueue));
        } catch (error) {
            console.error('Error saving offline queue:', error);
        }
    }

    /**
     * Load offline queue from localStorage
     */
    loadOfflineQueue() {
        try {
            const saved = localStorage.getItem(this.offlineQueueKey);
            if (saved) {
                this.messageQueue = JSON.parse(saved);
                console.log(`Loaded ${this.messageQueue.length} queued messages`);
            }
        } catch (error) {
            console.error('Error loading offline queue:', error);
        }
    }

    /**
     * Clear offline queue
     */
    clearOfflineQueue() {
        this.messageQueue = [];
        localStorage.removeItem(this.offlineQueueKey);
    }

    /**
     * Send online status
     */
    sendOnlineStatus() {
        this.send({
            type: 'online_status',
            status: 'online'
        });
    }

    /**
     * Send typing indicator
     * @param {boolean} isTyping - Whether user is typing
     */
    sendTyping(isTyping) {
        this.send({
            type: 'typing',
            is_typing: isTyping
        });
    }

    /**
     * Send message read status
     * @param {string} messageId - Message ID
     */
    sendMarkAsRead(messageId) {
        this.send({
            type: 'mark_read',
            message_id: messageId
        });
    }

    /**
     * Send message edit
     * @param {string} messageId - Message ID
     * @param {string} content - New content
     */
    sendEditMessage(messageId, content) {
        this.send({
            type: 'edit_message',
            message_id: messageId,
            content: content
        });
    }

    /**
     * Send message delete
     * @param {string} messageId - Message ID
     */
    sendDeleteMessage(messageId) {
        this.send({
            type: 'delete_message',
            message_id: messageId
        });
    }

    /**
     * Send reaction
     * @param {string} messageId - Message ID
     * @param {string} reactionType - Reaction type
     */
    sendReaction(messageId, reactionType) {
        this.send({
            type: 'add_reaction',
            message_id: messageId,
            reaction_type: reactionType
        });
    }

    /**
     * Close WebSocket connection
     */
    close() {
        this.isManualClose = true;
        this.connectionState = 'disconnected';
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
        }

        this.emit('manualClose');
    }

    /**
     * Get connection state
     * @returns {string} Connection state
     */
    getState() {
        return this.connectionState;
    }

    /**
     * Check if connected
     * @returns {boolean} Connection status
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Register event handler
     * @param {string} event - Event name
     * @param {function} handler - Event handler
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    /**
     * Unregister event handler
     * @param {string} event - Event name
     * @param {function} handler - Event handler
     */
    off(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        }
    }

    /**
     * Emit event
     * @param {string} event - Event name
     * @param {object} data - Event data
     */
    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Get statistics
     * @returns {object} Statistics
     */
    getStats() {
        return {
            state: this.connectionState,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length,
            lastMessageTime: this.lastMessageTime,
            isConnected: this.isConnected()
        };
    }
}

// Global WebSocket manager instance
const wsManager = new WebSocketManager();

// Auto-connect when page loads if conversation is open
document.addEventListener('DOMContentLoaded', () => {
    // Check if there's a current conversation
    const currentConversation = window.currentConversationId;
    if (currentConversation) {
        wsManager.connect(currentConversation);
    }

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // Page hidden, stop heartbeat
            wsManager.stopHeartbeat();
        } else {
            // Page visible, reconnect if needed
            if (wsManager.getState() === 'disconnected' && window.currentConversationId) {
                wsManager.connect(window.currentConversationId);
            }
        }
    });

    // Handle before unload
    window.addEventListener('beforeunload', () => {
        wsManager.close();
    });
});
