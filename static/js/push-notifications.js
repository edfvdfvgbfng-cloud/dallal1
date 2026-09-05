/**
 * Web Push Notifications System
 * Handles push notification subscription and display
 */

class PushNotificationManager {
    constructor() {
        this.subscription = null;
        this.vapidPublicKey = null;
        this.isSupported = this.checkSupport();
    }

    checkSupport() {
        return 'serviceWorker' in navigator && 'PushManager' in window;
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Push notifications not supported');
            return false;
        }

        try {
            // Register service worker
            const registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('Service Worker registered:', registration);

            // Get VAPID public key
            await this.getVapidPublicKey();

            // Check existing subscription
            this.subscription = await registration.pushManager.getSubscription();
            console.log('Existing subscription:', this.subscription);

            // Subscribe if not subscribed
            if (!this.subscription) {
                await this.subscribe();
            }

            return true;
        } catch (error) {
            console.error('Push notification init error:', error);
            return false;
        }
    }

    async getVapidPublicKey() {
        try {
            const response = await fetch('/api/push/vapid-key/');
            const data = await response.json();
            this.vapidPublicKey = data.publicKey;
            return this.vapidPublicKey;
        } catch (error) {
            console.error('Error getting VAPID key:', error);
            return null;
        }
    }

    async subscribe() {
        if (!this.vapidPublicKey) {
            await this.getVapidPublicKey();
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            this.subscription = subscription;

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);

            console.log('Push subscription successful:', subscription);
            return subscription;
        } catch (error) {
            console.error('Push subscription error:', error);
            throw error;
        }
    }

    async unsubscribe() {
        if (!this.subscription) {
            return;
        }

        try {
            await this.subscription.unsubscribe();
            await this.sendUnsubscriptionToServer(this.subscription);
            this.subscription = null;
            console.log('Push unsubscription successful');
        } catch (error) {
            console.error('Push unsubscription error:', error);
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(subscription.toJSON())
            });

            const data = await response.json();
            console.log('Subscription sent to server:', data);
            return data;
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }

    async sendUnsubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/push/unsubscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ endpoint: subscription.endpoint })
            });

            const data = await response.json();
            console.log('Unsubscription sent to server:', data);
            return data;
        } catch (error) {
            console.error('Error sending unsubscription to server:', error);
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
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

    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('This browser does not support desktop notification');
            return false;
        }

        if (Notification.permission === 'granted') {
            return true;
        }

        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }

        return false;
    }

    showLocalNotification(title, options = {}) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(title, {
                icon: '/static/images/favicon.svg',
                badge: '/static/images/favicon.svg',
                ...options
            });

            notification.onclick = (event) => {
                event.preventDefault();
                if (options.data && options.data.link) {
                    window.location.href = options.data.link;
                }
                notification.close();
            };

            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000);

            return notification;
        }
    }
}

// Toast Notification Display
class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(title, message, type = 'info', duration = 5000, link = null) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
        `;

        const icon = this.getIcon(type);
        const content = `
            <div style="font-size: 24px;">${icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: bold; margin-bottom: 4px;">${title}</div>
                <div style="font-size: 14px; opacity: 0.9;">${message}</div>
            </div>
            <button style="background: none; border: none; color: white; font-size: 20px; cursor: pointer;">&times;</button>
        `;

        toast.innerHTML = content;

        // Add click handler
        toast.addEventListener('click', () => {
            if (link) {
                window.location.href = link;
            }
            this.dismiss(toast);
        });

        // Add close button handler
        const closeBtn = toast.querySelector('button');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.dismiss(toast);
        });

        this.container.appendChild(toast);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    getIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌',
            message: '💬',
            property: '🏠',
            rating: '⭐',
            subscription: '💳',
            auction: '🔨',
            system: '⚙️'
        };
        return icons[type] || 'ℹ️';
    }

    dismiss(toast) {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .toast {
        backdrop-filter: blur(10px);
    }

    .toast-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    }

    .toast-error {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%) !important;
    }

    .toast-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    }

    .toast-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
    }
`;
document.head.appendChild(style);

// Initialize
const pushManager = new PushNotificationManager();
const toastManager = new ToastManager();

// Auto-init on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Handle manual permission button
    const permissionBtn = document.getElementById('push-permission-btn');
    if (permissionBtn) {
        // Hide button if permission already granted
        if (Notification.permission === 'granted') {
            permissionBtn.style.display = 'none';
            await pushManager.init();
        } else {
            permissionBtn.addEventListener('click', async () => {
                const granted = await pushManager.requestPermission();
                if (granted) {
                    await pushManager.init();
                    permissionBtn.style.display = 'none';
                    toastManager.show('تم التفعيل', 'تم تفعيل الإشعارات بنجاح!', 'success');
                }
            });
        }
    } else if (Notification.permission === 'granted') {
        await pushManager.init();
    }
});

// Export for use in other scripts
window.pushManager = pushManager;
window.toastManager = toastManager;
