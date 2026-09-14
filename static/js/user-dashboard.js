/**
 * Enhanced User Dashboard JavaScript
 * Handles all dashboard functionality
 */

class UserDashboard {
    constructor() {
        this.currentTab = 'overview';
        this.userData = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupModals();
        this.setupForms();
        this.loadDashboardData();
        this.setupEventListeners();
    }

    setupNavigation() {
        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabName) {
                tab.classList.add('active');
            }
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            if (content.id === tabName) {
                content.classList.add('active');
            }
        });

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    loadTabData(tabName) {
        switch(tabName) {
            case 'saved':
                this.loadSavedItems();
                break;
            case 'searches':
                this.loadSavedSearches();
                break;
            case 'comparisons':
                this.loadComparisons();
                break;
            case 'viewed':
                this.loadViewedItems();
                break;
            case 'viewings':
                this.loadViewings();
                break;
            case 'bookings':
                this.loadBookings();
                break;
            case 'messages':
                this.loadMessages();
                break;
            case 'notifications':
                this.loadNotifications();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
        }
    }

    setupModals() {
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });

        // Click outside to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeAllModals();
                }
            });
        });

        // New search button
        document.getElementById('newSearch')?.addEventListener('click', () => {
            this.openModal('searchModal');
        });

        // New viewing button
        document.getElementById('newViewing')?.addEventListener('click', () => {
            this.openModal('viewingModal');
        });

        // New alert button
        document.getElementById('newAlert')?.addEventListener('click', () => {
            this.openModal('alertModal');
        });

        // New comparison button
        document.getElementById('newComparison')?.addEventListener('click', () => {
            this.openComparisonModal();
        });

        // New message button
        document.getElementById('newMessage')?.addEventListener('click', () => {
            this.openMessageModal();
        });
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    setupForms() {
        // Profile form
        document.getElementById('profileForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfile();
        });

        // Security form
        document.getElementById('securityForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePassword();
        });

        // Search form
        document.getElementById('searchForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSearch();
        });

        // Viewing form
        document.getElementById('viewingForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.bookViewing();
        });

        // Alert form
        document.getElementById('alertForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAlert();
        });
    }

    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.currentTarget.dataset.filter;
                this.applyFilter(filter, e.currentTarget);
            });
        });

        // Alerts tabs
        document.querySelectorAll('.alerts-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.switchAlertsTab(type, e.currentTarget);
            });
        });

        // Clear history button
        document.getElementById('clearHistory')?.addEventListener('click', () => {
            this.clearViewHistory();
        });

        // Mark all read button
        document.getElementById('markAllRead')?.addEventListener('click', () => {
            this.markAllNotificationsRead();
        });

        // Edit interests button
        document.getElementById('editInterests')?.addEventListener('click', () => {
            this.editInterests();
        });

        // Add area button
        document.getElementById('addArea')?.addEventListener('click', () => {
            this.addFavoriteArea();
        });

        // Price range sliders
        const minPrice = document.getElementById('minPrice');
        const maxPrice = document.getElementById('maxPrice');
        if (minPrice && maxPrice) {
            minPrice.addEventListener('input', () => this.updatePriceLabels());
            maxPrice.addEventListener('input', () => this.updatePriceLabels());
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/user-dashboard/');
            const data = await response.json();
            this.userData = data;
            this.updateStats(data.stats);
            this.updateRecentActivity(data.recent_activity);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    updateStats(stats) {
        if (!stats) return;

        const statElements = {
            'saved_properties': '.stat-primary .stat-value',
            'saved_searches': '.stat-secondary .stat-value',
            'viewed_properties': '.stat-success .stat-value',
            'unread_notifications': '.stat-warning .stat-value',
            'unread_messages': '.stat-info .stat-value',
            'upcoming_viewings': '.stat-danger .stat-value'
        };

        for (const [key, selector] of Object.entries(statElements)) {
            const element = document.querySelector(selector);
            if (element && stats[key] !== undefined) {
                element.textContent = stats[key];
            }
        }
    }

    updateRecentActivity(activities) {
        const container = document.querySelector('.activity-timeline');
        if (!container || !activities) return;

        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${activity.icon}</div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    async loadSavedItems() {
        const container = document.getElementById('savedGrid');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/saved-items/');
            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                container.innerHTML = data.items.map(item => this.renderSavedItem(item)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد عناصر محفوظة', 'ابدأ بحفظ العناصر التي تعجبك');
            }
        } catch (error) {
            console.error('Error loading saved items:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل العناصر المحفوظة');
        }
    }

    renderSavedItem(item) {
        return `
            <div class="saved-item">
                <img src="${item.image || '/static/img/placeholder.svg'}" alt="${item.title}" class="saved-item-image">
                <div class="saved-item-content">
                    <h3 class="saved-item-title">${item.title}</h3>
                    <p class="saved-item-price">${item.price}</p>
                    <p class="saved-item-location">${item.location}</p>
                    <div class="saved-item-actions">
                        <a href="${item.url}" class="btn btn-sm btn-primary">عرض</a>
                        <button class="btn btn-sm btn-outline" onclick="removeSavedItem(${item.id})">إزالة</button>
                    </div>
                </div>
            </div>
        `;
    }

    async loadSavedSearches() {
        const container = document.getElementById('searchesList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/saved-searches/');
            const data = await response.json();
            
            if (data.searches && data.searches.length > 0) {
                container.innerHTML = data.searches.map(search => this.renderSavedSearch(search)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد عمليات بحث محفوظة', 'احفظ عمليات البحث للوصول السريع');
            }
        } catch (error) {
            console.error('Error loading saved searches:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل عمليات البحث المحفوظة');
        }
    }

    renderSavedSearch(search) {
        return `
            <div class="search-item">
                <div class="search-item-content">
                    <h3 class="search-item-title">${search.name}</h3>
                    <p class="search-item-meta">${search.filters_summary}</p>
                    <p class="search-item-meta">آخر استخدام: ${search.last_used}</p>
                </div>
                <div class="search-item-actions">
                    <button class="btn btn-sm btn-primary" onclick="runSearch(${search.id})">تشغيل</button>
                    <button class="btn btn-sm btn-outline" onclick="deleteSearch(${search.id})">حذف</button>
                </div>
            </div>
        `;
    }

    async loadComparisons() {
        const container = document.getElementById('comparisonsList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/comparisons/');
            const data = await response.json();
            
            if (data.comparisons && data.comparisons.length > 0) {
                container.innerHTML = data.comparisons.map(comp => this.renderComparison(comp)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد مقارنات محفوظة', 'قارن بين العقارات لاتخاذ قرار أفضل');
            }
        } catch (error) {
            console.error('Error loading comparisons:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل المقارنات');
        }
    }

    renderComparison(comparison) {
        return `
            <div class="comparison-item">
                <div class="comparison-item-content">
                    <h3 class="comparison-item-title">${comparison.name}</h3>
                    <p class="comparison-item-meta">${comparison.items_count} عقارات</p>
                    <p class="comparison-item-meta">آخر تحديث: ${comparison.updated_at}</p>
                </div>
                <div class="comparison-item-actions">
                    <a href="${comparison.url}" class="btn btn-sm btn-primary">عرض</a>
                    <button class="btn btn-sm btn-outline" onclick="deleteComparison(${comparison.id})">حذف</button>
                </div>
            </div>
        `;
    }

    async loadViewedItems() {
        const container = document.getElementById('viewedGrid');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/viewed-items/');
            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                container.innerHTML = data.items.map(item => this.renderViewedItem(item)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لم تشاهد أي عناصر بعد', 'ابدأ باستكشاف العقارات');
            }
        } catch (error) {
            console.error('Error loading viewed items:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل العناصر المشاهدة');
        }
    }

    renderViewedItem(item) {
        return `
            <div class="viewed-item">
                <img src="${item.image || '/static/img/placeholder.svg'}" alt="${item.title}" class="viewed-item-image">
                <div class="viewed-item-content">
                    <h3 class="viewed-item-title">${item.title}</h3>
                    <p class="viewed-item-price">${item.price}</p>
                    <p class="viewed-item-location">${item.location}</p>
                    <p class="viewed-item-meta">شوهدت: ${item.viewed_at}</p>
                    <div class="viewed-item-actions">
                        <a href="${item.url}" class="btn btn-sm btn-primary">عرض</a>
                        <button class="btn btn-sm btn-outline" onclick="saveItem(${item.id})">حفظ</button>
                    </div>
                </div>
            </div>
        `;
    }

    async loadViewings() {
        const container = document.getElementById('viewingsList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/viewings/');
            const data = await response.json();
            
            if (data.viewings && data.viewings.length > 0) {
                container.innerHTML = data.viewings.map(viewing => this.renderViewing(viewing)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد طلبات معاينة', 'احجز موعد معاينة للعقارات التي تعجبك');
            }
        } catch (error) {
            console.error('Error loading viewings:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل طلبات المعاينة');
        }
    }

    renderViewing(viewing) {
        const statusColors = {
            'pending': '#F59E0B',
            'confirmed': '#10B981',
            'completed': '#3B82F6',
            'cancelled': '#EF4444'
        };

        return `
            <div class="viewing-item">
                <div class="viewing-item-content">
                    <h3 class="viewing-item-title">${viewing.property_title}</h3>
                    <p class="viewing-item-meta">التاريخ: ${viewing.date}</p>
                    <p class="viewing-item-meta">الوقت: ${viewing.time}</p>
                    <span class="viewing-status" style="color: ${statusColors[viewing.status] || '#888'}">
                        ${viewing.status_display}
                    </span>
                </div>
                <div class="viewing-item-actions">
                    ${viewing.status === 'pending' ? `
                        <button class="btn btn-sm btn-primary" onclick="confirmViewing(${viewing.id})">تأكيد</button>
                        <button class="btn btn-sm btn-danger" onclick="cancelViewing(${viewing.id})">إلغاء</button>
                    ` : ''}
                    <a href="${viewing.property_url}" class="btn btn-sm btn-outline">عرض العقار</a>
                </div>
            </div>
        `;
    }

    async loadBookings() {
        const container = document.getElementById('bookingsList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/bookings/');
            const data = await response.json();
            
            if (data.bookings && data.bookings.length > 0) {
                container.innerHTML = data.bookings.map(booking => this.renderBooking(booking)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد حجوزات', 'احجز فنادق ومنتجعات لعطلتك القادمة');
            }
        } catch (error) {
            console.error('Error loading bookings:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل الحجوزات');
        }
    }

    renderBooking(booking) {
        const statusColors = {
            'confirmed': '#10B981',
            'pending': '#F59E0B',
            'cancelled': '#EF4444',
            'completed': '#3B82F6'
        };

        return `
            <div class="booking-item">
                <div class="booking-item-content">
                    <h3 class="booking-item-title">${booking.hotel_name}</h3>
                    <p class="booking-item-meta">من: ${booking.check_in}</p>
                    <p class="booking-item-meta">إلى: ${booking.check_out}</p>
                    <p class="booking-item-price">${booking.total_price}</p>
                    <span class="booking-status" style="color: ${statusColors[booking.status] || '#888'}">
                        ${booking.status_display}
                    </span>
                </div>
                <div class="booking-item-actions">
                    <a href="${booking.url}" class="btn btn-sm btn-primary">عرض التفاصيل</a>
                    ${booking.status === 'confirmed' ? `
                        <button class="btn btn-sm btn-danger" onclick="cancelBooking(${booking.id})">إلغاء</button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async loadMessages() {
        const container = document.getElementById('messagesList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/conversations/');
            const data = await response.json();
            
            if (data.conversations && data.conversations.length > 0) {
                container.innerHTML = data.conversations.map(conv => this.renderMessage(conv)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد محادثات', 'ابدأ محادثة مع الدلالين أو أصحاب العقارات');
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل المحادثات');
        }
    }

    renderMessage(conversation) {
        return `
            <div class="message-item ${conversation.unread ? 'unread' : ''}">
                <div class="message-item-content">
                    <h3 class="message-item-title">${conversation.other_user}</h3>
                    <p class="message-item-meta">${conversation.last_message}</p>
                    <p class="message-item-meta">${conversation.last_message_time}</p>
                    ${conversation.unread ? '<span class="unread-badge">جديد</span>' : ''}
                </div>
                <div class="message-item-actions">
                    <a href="${conversation.url}" class="btn btn-sm btn-primary">فتح المحادثة</a>
                </div>
            </div>
        `;
    }

    async loadNotifications() {
        const container = document.getElementById('notificationsList');
        if (!container) return;

        container.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/notifications/');
            const data = await response.json();
            
            if (data.notifications && data.notifications.length > 0) {
                container.innerHTML = data.notifications.map(notif => this.renderNotification(notif)).join('');
            } else {
                container.innerHTML = this.renderEmptyState('لا توجد إشعارات', 'ستظهر هنا الإشعارات المتعلقة بحسابك');
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            container.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل الإشعارات');
        }
    }

    renderNotification(notification) {
        return `
            <div class="notification-item ${notification.is_read ? '' : 'unread'}">
                <div class="notification-item-content">
                    <h3 class="notification-item-title">${notification.title}</h3>
                    <p class="notification-item-meta">${notification.message}</p>
                    <p class="notification-item-meta">${notification.created_at}</p>
                </div>
                <div class="notification-item-actions">
                    ${notification.link ? `<a href="${notification.link}" class="btn btn-sm btn-primary">عرض</a>` : ''}
                    <button class="btn btn-sm btn-outline" onclick="markAsRead(${notification.id})">تعيين كمقروء</button>
                </div>
            </div>
        `;
    }

    async loadAlerts() {
        const priceAlertsContainer = document.getElementById('priceAlerts');
        const propertyAlertsContainer = document.getElementById('propertyAlerts');
        
        if (!priceAlertsContainer || !propertyAlertsContainer) return;

        priceAlertsContainer.innerHTML = '<div class="loading"></div>';
        propertyAlertsContainer.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/user/alerts/');
            const data = await response.json();
            
            if (data.price_alerts && data.price_alerts.length > 0) {
                priceAlertsContainer.innerHTML = data.price_alerts.map(alert => this.renderAlert(alert, 'price')).join('');
            } else {
                priceAlertsContainer.innerHTML = this.renderEmptyState('لا توجد تنبيهات أسعار', 'فعّل تنبيهات الأسعار للحصول على عروض أفضل');
            }
            
            if (data.property_alerts && data.property_alerts.length > 0) {
                propertyAlertsContainer.innerHTML = data.property_alerts.map(alert => this.renderAlert(alert, 'property')).join('');
            } else {
                propertyAlertsContainer.innerHTML = this.renderEmptyState('لا توجد تنبيهات عقارات', 'فعّل تنبيهات العقارات الجديدة للعثور على فرص');
            }
        } catch (error) {
            console.error('Error loading alerts:', error);
            priceAlertsContainer.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل تنبيهات الأسعار');
            propertyAlertsContainer.innerHTML = this.renderEmptyState('خطأ في التحميل', 'حدث خطأ أثناء تحميل تنبيهات العقارات');
        }
    }

    renderAlert(alert, type) {
        return `
            <div class="alert-item">
                <div class="alert-item-content">
                    <h3 class="alert-item-title">${alert.title}</h3>
                    <p class="alert-item-meta">${alert.description}</p>
                    <p class="alert-item-meta">الحالة: ${alert.is_active ? 'نشط' : 'غير نشط'}</p>
                </div>
                <div class="alert-item-actions">
                    <button class="btn btn-sm btn-outline" onclick="toggleAlert(${alert.id})">
                        ${alert.is_active ? 'إيقاف' : 'تفعيل'}
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteAlert(${alert.id})">حذف</button>
                </div>
            </div>
        `;
    }

    renderEmptyState(title, message) {
        return `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>${title}</h3>
                <p>${message}</p>
            </div>
        `;
    }

    applyFilter(filter, button) {
        // Update active button
        const container = button.closest('.section-filters');
        container.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Reload data with filter
        this.loadTabData(this.currentTab);
    }

    switchAlertsTab(type, button) {
        // Update active tab
        const container = button.closest('.alerts-tabs');
        container.querySelectorAll('.alerts-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        button.classList.add('active');

        // Show corresponding content
        const alertsContent = document.querySelector('.alerts-content');
        alertsContent.querySelectorAll('.alerts-list').forEach(list => {
            list.style.display = 'none';
        });
        
        if (type === 'price') {
            document.getElementById('priceAlerts').style.display = 'flex';
        } else {
            document.getElementById('propertyAlerts').style.display = 'flex';
        }
    }

    updatePriceLabels() {
        const minPrice = document.getElementById('minPrice');
        const maxPrice = document.getElementById('maxPrice');
        const minLabel = document.getElementById('minPriceLabel');
        const maxLabel = document.getElementById('maxPriceLabel');

        if (minPrice && maxPrice && minLabel && maxLabel) {
            minLabel.textContent = this.formatPrice(minPrice.value);
            maxLabel.textContent = this.formatPrice(maxPrice.value);
        }
    }

    formatPrice(price) {
        return new Intl.NumberFormat('ar-IQ').format(price) + ' د.ع';
    }

    async saveProfile() {
        const form = document.getElementById('profileForm');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/user/profile/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('تم حفظ ملفك الشخصي بنجاح', 'success');
            } else {
                this.showNotification('حدث خطأ أثناء حفظ الملف الشخصي', 'error');
            }
        } catch (error) {
            console.error('Error saving profile:', error);
            this.showNotification('حدث خطأ أثناء حفظ الملف الشخصي', 'error');
        }
    }

    async changePassword() {
        const form = document.getElementById('securityForm');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/user/change-password/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('تم تغيير كلمة المرور بنجاح', 'success');
                form.reset();
            } else {
                this.showNotification('حدث خطأ أثناء تغيير كلمة المرور', 'error');
            }
        } catch (error) {
            console.error('Error changing password:', error);
            this.showNotification('حدث خطأ أثناء تغيير كلمة المرور', 'error');
        }
    }

    async saveSearch() {
        const form = document.getElementById('searchForm');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/user/save-search/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('تم حفظ البحث بنجاح', 'success');
                this.closeAllModals();
                this.loadSavedSearches();
            } else {
                this.showNotification('حدث خطأ أثناء حفظ البحث', 'error');
            }
        } catch (error) {
            console.error('Error saving search:', error);
            this.showNotification('حدث خطأ أثناء حفظ البحث', 'error');
        }
    }

    async bookViewing() {
        const form = document.getElementById('viewingForm');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/user/book-viewing/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('تم حجز المعاينة بنجاح', 'success');
                this.closeAllModals();
                this.loadViewings();
            } else {
                this.showNotification('حدث خطأ أثناء حجز المعاينة', 'error');
            }
        } catch (error) {
            console.error('Error booking viewing:', error);
            this.showNotification('حدث خطأ أثناء حجز المعاينة', 'error');
        }
    }

    async createAlert() {
        const form = document.getElementById('alertForm');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/user/create-alert/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('تم إنشاء التنبيه بنجاح', 'success');
                this.closeAllModals();
                this.loadAlerts();
            } else {
                this.showNotification('حدث خطأ أثناء إنشاء التنبيه', 'error');
            }
        } catch (error) {
            console.error('Error creating alert:', error);
            this.showNotification('حدث خطأ أثناء إنشاء التنبيه', 'error');
        }
    }

    async clearViewHistory() {
        if (!confirm('هل أنت متأكد من مسح سجل المشاهدات؟')) return;

        try {
            const response = await fetch('/api/user/clear-history/', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('تم مسح سجل المشاهدات بنجاح', 'success');
                this.loadViewedItems();
            } else {
                this.showNotification('حدث خطأ أثناء مسح السجل', 'error');
            }
        } catch (error) {
            console.error('Error clearing history:', error);
            this.showNotification('حدث خطأ أثناء مسح السجل', 'error');
        }
    }

    async markAllNotificationsRead() {
        try {
            const response = await fetch('/api/user/mark-all-read/', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('تم تعيين جميع الإشعارات كمقروء', 'success');
                this.loadNotifications();
            } else {
                this.showNotification('حدث خطأ أثناء تعيين الإشعارات', 'error');
            }
        } catch (error) {
            console.error('Error marking notifications as read:', error);
            this.showNotification('حدث خطأ أثناء تعيين الإشعارات', 'error');
        }
    }

    editInterests() {
        // Open interests editing modal
        this.showNotification('ميزة تعديل الاهتمامات قيد التطوير', 'info');
    }

    addFavoriteArea() {
        // Open area adding modal
        this.showNotification('ميزة إضافة المنطقة المفضلة قيد التطوير', 'info');
    }

    openComparisonModal() {
        this.showNotification('ميزة المقارنة الجديدة قيد التطوير', 'info');
    }

    openMessageModal() {
        // Redirect to messages page or open modal
        window.location.href = '/messages/';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Global functions for inline event handlers
window.removeSavedItem = function(id) {
    console.log('Remove saved item:', id);
};

window.runSearch = function(id) {
    console.log('Run search:', id);
};

window.deleteSearch = function(id) {
    console.log('Delete search:', id);
};

window.deleteComparison = function(id) {
    console.log('Delete comparison:', id);
};

window.saveItem = function(id) {
    console.log('Save item:', id);
};

window.confirmViewing = function(id) {
    console.log('Confirm viewing:', id);
};

window.cancelViewing = function(id) {
    console.log('Cancel viewing:', id);
};

window.cancelBooking = function(id) {
    console.log('Cancel booking:', id);
};

window.markAsRead = function(id) {
    console.log('Mark as read:', id);
};

window.toggleAlert = function(id) {
    console.log('Toggle alert:', id);
};

window.deleteAlert = function(id) {
    console.log('Delete alert:', id);
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.userDashboard = new UserDashboard();
});
