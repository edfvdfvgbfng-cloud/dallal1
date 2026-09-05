/**
 * Interactive Property Feed - Instagram-like Experience
 * Swipe-based property discovery with smooth animations
 */

class PropertyFeed {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.options = {
            items: [],
            currentIndex: 0,
            swipeThreshold: 100,
            enableSwipe: true,
            enableKeyboard: true,
            enableAutoPlay: false,
            autoPlayInterval: 5000,
            ...options
        };

        this.cards = [];
        this.swipeDirection = null;
        this.isDragging = false;
        this.startX = 0;
        this.currentX = 0;
        this.autoPlayTimer = null;

        this.init();
    }

    init() {
        this.renderFeed();
        this.attachEventListeners();

        if (this.options.enableAutoPlay) {
            this.startAutoPlay();
        }
    }

    renderFeed() {
        this.container.innerHTML = '';
        this.container.className = 'property-feed-container';

        // Create feed wrapper
        const feedWrapper = document.createElement('div');
        feedWrapper.className = 'feed-wrapper';

        // Create cards
        this.options.items.forEach((item, index) => {
            const card = this.createCard(item, index);
            this.cards.push(card);
            feedWrapper.appendChild(card);
        });

        this.container.appendChild(feedWrapper);

        // Add navigation controls
        this.addNavigationControls();

        // Add action buttons
        this.addActionButtons();

        // Update current card
        this.updateCurrentCard();
    }

    createCard(item, index) {
        const card = document.createElement('div');
        card.className = 'feed-card';
        card.dataset.index = index;
        card.dataset.id = item.id;

        const price = item.price ? this.formatPrice(item.price) : '';
        const location = item.location || item.district || '';
        const rating = item.rating ? `⭐ ${item.rating}` : '';

        card.innerHTML = `
            <div class="card-image-container">
                <img src="${item.image || '/static/img/placeholder-property.svg'}" 
                     alt="${item.title}" 
                     class="card-image"
                     loading="lazy">
                <div class="card-overlay">
                    <div class="card-likes">
                        <span class="likes-count">${item.likes || 0}</span>
                        <span class="likes-icon">❤️</span>
                    </div>
                    <div class="card-badge ${item.is_featured ? 'featured' : ''}">
                        ${item.is_featured ? '⭐ مميز' : ''}
                    </div>
                </div>
            </div>
            <div class="card-content">
                <h3 class="card-title">${item.title}</h3>
                <div class="card-meta">
                    <span class="card-location">📍 ${location}</span>
                    ${rating ? `<span class="card-rating">${rating}</span>` : ''}
                </div>
                <div class="card-price">${price}</div>
                <div class="card-details">
                    ${item.bedrooms ? `<span>🛏️ ${item.bedrooms} غرف</span>` : ''}
                    ${item.bathrooms ? `<span>🚿 ${item.bathrooms} حمام</span>` : ''}
                    ${item.area ? `<span>📐 ${item.area} م²</span>` : ''}
                </div>
            </div>
            <div class="card-actions-overlay">
                <div class="swipe-indicator left">
                    <span>← حفظ</span>
                </div>
                <div class="swipe-indicator right">
                    <span>رفض →</span>
                </div>
            </div>
        `;

        return card;
    }

    addNavigationControls() {
        const nav = document.createElement('div');
        nav.className = 'feed-navigation';

        nav.innerHTML = `
            <button class="nav-btn prev-btn" aria-label="السابق">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M15 18l-6-6 6-6"/>
                </svg>
            </button>
            <div class="page-indicator">
                <span class="current-page">1</span>
                <span class="page-separator">/</span>
                <span class="total-pages">${this.options.items.length}</span>
            </div>
            <button class="nav-btn next-btn" aria-label="التالي">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 18l6-6-6-6"/>
                </svg>
            </button>
        `;

        this.container.appendChild(nav);

        // Add event listeners
        nav.querySelector('.prev-btn').addEventListener('click', () => this.previousCard());
        nav.querySelector('.next-btn').addEventListener('click', () => this.nextCard());
    }

    addActionButtons() {
        const actions = document.createElement('div');
        actions.className = 'feed-actions';

        actions.innerHTML = `
            <button class="action-btn save-btn" aria-label="حفظ">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                </svg>
            </button>
            <button class="action-btn share-btn" aria-label="مشاركة">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="18" cy="5" r="3"/>
                    <circle cx="6" cy="12" r="3"/>
                    <circle cx="18" cy="19" r="3"/>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                </svg>
            </button>
            <button class="action-btn whatsapp-btn" aria-label="WhatsApp">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.407.622-.612.985-.227.386-.504.923-.504 1.637 0 .836.416 1.638.816 2.363.4.725.805 1.453.816 2.277.013.803.396 1.577.783 2.277.403.73.783 1.513.785 2.344.002.846-.385 1.66-.821 2.373-.779.719-.806 1.593-.822 2.345-.016.726-.376 1.432-.788 2.13-.413.697-.914 1.234-1.493 1.592.504.525.914 1.128 1.185 1.795.273.67.402 1.393.386 2.134-.016.735-.383-1.432-.805-2.086-.424-.656-.938-1.162-1.537-1.525.556-.376 1.14-.665 1.75-.866.608-.2 1.229-.354 1.868-.462.64-.107 1.282-.177 1.925-.208.64-.03 1.285-.073 1.925-.108.648-.036 1.288-.08 1.923-.13.654-.05 1.285-.11 1.912-.18.632-.07 1.257-.152 1.873-.237.617-.086 1.227-.182 1.818-.287.595-.106 1.177-.22 1.746-.344.57-.124 1.122-.257 1.657-.4.535.584-.18 1.135-.382 1.657-.603.52-.22 1.01-.463 1.47-.728.46-.265.886-.556 1.277-.87.39-.316.747-.663 1.05-1.04.303-.376.545-.783.727-1.215.182-.432.332-.886.447-1.365.115-.48.174-.987.245-1.504.07-.518.145-1.053.236-1.597.092-.545.192-1.1.336-1.65.144-.55.285-1.07.578-1.55.88.48-.302.92-.62 1.325-.948.405-.328.768-.677 1.085-1.047.317-.37.587-.764.808-1.2.22-.437.57-.738 1.18-.885 1.88-.147.7-.205 1.44-.175 2.174.03.734.162 1.45.39 2.126.228.676.533 1.304.92 1.883.387.58.728 1.187 1.015 1.85.328.663.576 1.298.76 1.967.184.67.376 1.27.82 1.79 1.298.52.478.724 1.06.826 1.6.102.574.276 1.143.6 1.695.88.552.28 1.142.508 1.695.73.553.222 1.09.48 1.595.783.505.303.994.585 1.453.768.459.183.91.384 1.33.623 1.813.24.24.42.506.55 1.27.627 1.895.077.647.13 1.31.253 1.94.5.63.254 1.15.545 1.737.78.588.235 1.173.444 1.705.675.532.23 1.092.47 1.672.735.58.265 1.16.548 1.698.79.55.242.253.514 1.644.732.479.484.95.692 1.648.945.494.253 1.02.518 1.633.747.615.229.316.475.638 1.612.884.49.246.98.557 1.55.774.496.227.994.485 1.527.702-.292.708-.6 1.383-.897 2.063-.297.68-.594 1.36-.89 2.035-.296.674-.592 1.34-.886 2.018-.295.678-.59 1.35-.883 2.028-.295.68-.59 1.355-.883 2.035z"/>
                </svg>
            </button>
            <button class="action-btn details-btn" aria-label="التفاصيل">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
            </button>
        `;

        this.container.appendChild(actions);

        // Add event listeners
        actions.querySelector('.save-btn').addEventListener('click', () => this.saveCurrentCard());
        actions.querySelector('.share-btn').addEventListener('click', () => this.shareCurrentCard());
        actions.querySelector('.whatsapp-btn').addEventListener('click', () => this.shareWhatsApp());
        actions.querySelector('.details-btn').addEventListener('click', () => this.viewDetails());
    }

    attachEventListeners() {
        // Touch events for swipe
        if (this.options.enableSwipe) {
            this.attachSwipeEvents();
        }

        // Keyboard events
        if (this.options.enableKeyboard) {
            this.attachKeyboardEvents();
        }

        // Prevent context menu on images
        this.container.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }

    attachSwipeEvents() {
        const card = this.container.querySelector('.feed-wrapper');

        card.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        card.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: true });
        card.addEventListener('touchend', (e) => this.handleTouchEnd(e));

        // Mouse events for desktop
        card.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        card.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        card.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        card.addEventListener('mouseleave', (e) => this.handleMouseUp(e));
    }

    attachKeyboardEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousCard();
            } else if (e.key === 'ArrowRight') {
                this.nextCard();
            } else if (e.key === 's' || e.key === 'S') {
                this.saveCurrentCard();
            } else if (e.key === 'd' || e.key === 'D') {
                this.nextCard(); // Dislike = next
            }
        });
    }

    handleTouchStart(e) {
        this.isDragging = true;
        this.startX = e.touches[0].clientX;
        this.currentX = this.startX;
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;

        this.currentX = e.touches[0].clientX;
        const diff = this.currentX - this.startX;

        // Apply transform
        const currentCard = this.cards[this.options.currentIndex];
        if (currentCard) {
            currentCard.style.transform = `translateX(${diff}px) rotate(${diff * 0.05}deg)`;
            currentCard.style.transition = 'none';

            // Show swipe indicators
            if (Math.abs(diff) > 50) {
                this.swipeDirection = diff > 0 ? 'right' : 'left';
                this.showSwipeIndicator(this.swipeDirection);
            } else {
                this.hideSwipeIndicators();
            }
        }
    }

    handleTouchEnd(e) {
        if (!this.isDragging) return;

        this.isDragging = false;
        const diff = this.currentX - this.startX;

        // Reset card position
        const currentCard = this.cards[this.options.currentIndex];
        if (currentCard) {
            currentCard.style.transition = 'transform 0.3s ease';
            currentCard.style.transform = '';

            if (Math.abs(diff) > this.options.swipeThreshold) {
                if (diff > 0) {
                    this.swipeRight();
                } else {
                    this.swipeLeft();
                }
            }
        }

        this.hideSwipeIndicators();
        this.startX = 0;
        this.currentX = 0;
    }

    handleMouseDown(e) {
        this.isDragging = true;
        this.startX = e.clientX;
        this.currentX = e.clientX;
    }

    handleMouseMove(e) {
        if (!this.isDragging) return;

        this.currentX = e.clientX;
        const diff = this.currentX - this.startX;

        const currentCard = this.cards[this.options.currentIndex];
        if (currentCard) {
            currentCard.style.transform = `translateX(${diff}px) rotate(${diff * 0.05}deg)`;
            currentCard.style.transition = 'none';

            if (Math.abs(diff) > 50) {
                this.swipeDirection = diff > 0 ? 'right' : 'left';
                this.showSwipeIndicator(this.swipeDirection);
            } else {
                this.hideSwipeIndicators();
            }
        }
    }

    handleMouseUp(e) {
        if (!this.isDragging) return;

        this.isDragging = false;
        const diff = this.currentX - this.startX;

        const currentCard = this.cards[this.options.currentIndex];
        if (currentCard) {
            currentCard.style.transition = 'transform 0.3s ease';
            currentCard.style.transform = '';

            if (Math.abs(diff) > this.options.swipeThreshold) {
                if (diff > 0) {
                    this.swipeRight();
                } else {
                    this.swipeLeft();
                }
            }
        }

        this.hideSwipeIndicators();
        this.startX = 0;
        this.currentX = 0;
    }

    showSwipeIndicator(direction) {
        const indicator = this.container.querySelector(`.swipe-indicator.${direction}`);
        if (indicator) {
            indicator.style.opacity = '1';
        }
    }

    hideSwipeIndicators() {
        const indicators = this.container.querySelectorAll('.swipe-indicator');
        indicators.forEach(ind => {
            ind.style.opacity = '0';
        });
    }

    swipeLeft() {
        // Save current card
        this.saveCurrentCard();
        this.nextCard();
    }

    swipeRight() {
        // Dislike current card
        this.nextCard();
    }

    nextCard() {
        if (this.options.currentIndex < this.options.items.length - 1) {
            this.options.currentIndex++;
            this.updateCurrentCard();
        } else {
            // Loop back to start
            this.options.currentIndex = 0;
            this.updateCurrentCard();
        }
    }

    previousCard() {
        if (this.options.currentIndex > 0) {
            this.options.currentIndex--;
            this.updateCurrentCard();
        }
    }

    updateCurrentCard() {
        // Update card visibility
        this.cards.forEach((card, index) => {
            if (index === this.options.currentIndex) {
                card.style.display = 'block';
                card.style.animation = 'cardSlideIn 0.3s ease';
            } else {
                card.style.display = 'none';
                card.style.animation = '';
            }
        });

        // Update page indicator
        const currentPage = this.container.querySelector('.current-page');
        if (currentPage) {
            currentPage.textContent = this.options.currentIndex + 1;
        }

        // Update navigation buttons
        const prevBtn = this.container.querySelector('.prev-btn');
        const nextBtn = this.container.querySelector('.next-btn');

        if (prevBtn) {
            prevBtn.disabled = this.options.currentIndex === 0;
        }

        if (nextBtn) {
            nextBtn.disabled = this.options.currentIndex === this.options.items.length - 1;
        }

        // Track view
        this.trackView();
    }

    saveCurrentCard() {
        const currentItem = this.options.items[this.options.currentIndex];
        if (currentItem) {
            // Trigger save event
            this.container.dispatchEvent(new CustomEvent('cardSaved', {
                detail: { item: currentItem }
            }));

            // Show save animation
            const saveBtn = this.container.querySelector('.save-btn');
            if (saveBtn) {
                saveBtn.classList.add('active');
                setTimeout(() => saveBtn.classList.remove('active'), 1000);
            }
        }
    }

    shareCurrentCard() {
        const currentItem = this.options.items[this.options.currentIndex];
        if (currentItem) {
            // Trigger share event
            this.container.dispatchEvent(new CustomEvent('cardShared', {
                detail: { item: currentItem }
            }));

            // Open share modal (implementation depends on your app)
            this.openShareModal(currentItem);
        }
    }

    shareWhatsApp() {
        const currentItem = this.options.items[this.options.currentIndex];
        if (currentItem) {
            const message = `شاهد هذا العقار: ${currentItem.title}\nالسعر: ${currentItem.price}\nالموقع: ${currentItem.location}\n${currentItem.url}`;
            const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        }
    }

    viewDetails() {
        const currentItem = this.options.items[this.options.currentIndex];
        if (currentItem && currentItem.url) {
            window.location.href = currentItem.url;
        }
    }

    openShareModal(item) {
        // Create share modal
        const modal = document.createElement('div');
        modal.className = 'share-modal';
        modal.innerHTML = `
            <div class="share-modal-content">
                <div class="share-modal-header">
                    <h3>مشاركة العقار</h3>
                    <button class="close-modal" aria-label="إغلاق">✕</button>
                </div>
                <div class="share-modal-body">
                    <div class="share-options">
                        <button class="share-option whatsapp" data-platform="whatsapp">
                            <span>📱</span>
                            <span>WhatsApp</span>
                        </button>
                        <button class="share-option facebook" data-platform="facebook">
                            <span>📘</span>
                            <span>Facebook</span>
                        </button>
                        <button class="share-option twitter" data-platform="twitter">
                            <span>🐦</span>
                            <span>Twitter</span>
                        </button>
                        <button class="share-option telegram" data-platform="telegram">
                            <span>✈️</span>
                            <span>Telegram</span>
                        </button>
                        <button class="share-option link" data-platform="link">
                            <span>🔗</span>
                            <span>نسخ الرابط</span>
                        </button>
                        <button class="share-option image" data-platform="image">
                            <span>🖼️</span>
                            <span>مشاركة كصورة</span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add event listeners
        modal.querySelector('.close-modal').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        modal.querySelectorAll('.share-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const platform = btn.dataset.platform;
                this.shareToPlatform(platform, item);
                document.body.removeChild(modal);
            });
        });
    }

    shareToPlatform(platform, item) {
        const url = item.url || window.location.href;
        const title = item.title;
        const message = `شاهد هذا العقار: ${title}\n${url}`;

        switch (platform) {
            case 'whatsapp':
                window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
                break;
            case 'facebook':
                window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
                break;
            case 'twitter':
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`, '_blank');
                break;
            case 'telegram':
                window.open(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`, '_blank');
                break;
            case 'link':
                navigator.clipboard.writeText(url);
                alert('تم نسخ الرابط!');
                break;
            case 'image':
                this.shareAsImage(item);
                break;
        }
    }

    shareAsImage(item) {
        // Create canvas for image sharing
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.crossOrigin = 'anonymous';
        img.onload = () => {
            canvas.width = 800;
            canvas.height = 600;

            // Draw background
            ctx.fillStyle = '#FF7A00';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw image
            ctx.drawImage(img, 50, 50, 700, 400);

            // Draw text
            ctx.fillStyle = '#000';
            ctx.font = 'bold 24px Arial';
            ctx.fillText(item.title, 50, 480);

            ctx.font = '18px Arial';
            ctx.fillText(`السعر: ${item.price}`, 50, 510);
            ctx.fillText(`الموقع: ${item.location}`, 50, 540);

            // Download
            canvas.toBlob((blob) => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `عقار-${item.id}.png`;
                a.click();
                URL.revokeObjectURL(url);
            });
        };

        img.src = item.image;
    }

    trackView() {
        const currentItem = this.options.items[this.options.currentIndex];
        if (currentItem) {
            // Track view in local storage
            const recentlyViewed = JSON.parse(localStorage.getItem('recentlyViewed') || '[]');
            
            // Remove if already exists
            const filtered = recentlyViewed.filter(item => item.id !== currentItem.id);
            
            // Add to front
            filtered.unshift(currentItem);
            
            // Keep only last 20
            const trimmed = filtered.slice(0, 20);
            
            localStorage.setItem('recentlyViewed', JSON.stringify(trimmed));

            // Trigger view event
            this.container.dispatchEvent(new CustomEvent('cardViewed', {
                detail: { item: currentItem }
            }));
        }
    }

    startAutoPlay() {
        this.autoPlayTimer = setInterval(() => {
            this.nextCard();
        }, this.options.autoPlayInterval);
    }

    stopAutoPlay() {
        if (this.autoPlayTimer) {
            clearInterval(this.autoPlayTimer);
            this.autoPlayTimer = null;
        }
    }

    formatPrice(price) {
        if (!price) return '';
        return new Intl.NumberFormat('ar-IQ', {
            style: 'currency',
            currency: 'IQD',
            maximumFractionDigits: 0
        }).format(price);
    }

    destroy() {
        this.stopAutoPlay();
        this.container.innerHTML = '';
    }
}

// Initialize feed when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if feed container exists
    const feedContainer = document.getElementById('property-feed');
    if (feedContainer) {
        // Get feed data from data attribute or API
        const feedData = feedContainer.dataset.feed 
            ? JSON.parse(feedContainer.dataset.feed) 
            : [];

        if (feedData.length > 0) {
            const feed = new PropertyFeed('property-feed', {
                items: feedData,
                enableSwipe: true,
                enableKeyboard: true
            });
        }
    }
});
