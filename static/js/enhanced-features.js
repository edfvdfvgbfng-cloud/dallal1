// ===== Enhanced JavaScript Features =====

// Advanced Search with Debounce
class AdvancedSearch {
  constructor() {
    this.searchInput = document.getElementById('search-input');
    this.resultsContainer = document.getElementById('search-results');
    this.debounceTimer = null;
    this.minChars = 2;
    this.init();
  }

  init() {
    if (this.searchInput) {
      this.searchInput.addEventListener('input', this.handleInput.bind(this));
      this.searchInput.addEventListener('focus', this.showResults.bind(this));
      document.addEventListener('click', this.hideResults.bind(this));
    }
  }

  handleInput(e) {
    const query = e.target.value.trim();
    
    clearTimeout(this.debounceTimer);
    
    if (query.length < this.minChars) {
      this.hideResults();
      return;
    }
    
    this.debounceTimer = setTimeout(() => {
      this.performSearch(query);
    }, 300);
  }

  async performSearch(query) {
    try {
      const response = await fetch(`/api/properties/search/?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      this.displayResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
    }
  }

  displayResults(results) {
    if (!this.resultsContainer) return;
    
    if (results.length === 0) {
      this.resultsContainer.innerHTML = '<div class="search-no-results">لا توجد نتائج</div>';
    } else {
      this.resultsContainer.innerHTML = results.map(result => `
        <a href="${result.url}" class="search-result-item">
          <div class="search-result-image">
            <img src="${result.image}" alt="${result.title}" loading="lazy">
          </div>
          <div class="search-result-content">
            <h4>${result.title}</h4>
            <p class="search-result-location">${result.location}</p>
            <p class="search-result-price">${this.formatPrice(result.price)}</p>
          </div>
        </a>
      `).join('');
    }
    
    this.showResults();
  }

  showResults() {
    if (this.resultsContainer) {
      this.resultsContainer.style.display = 'block';
    }
  }

  hideResults(e) {
    if (e && e.target.closest('.search-container')) return;
    if (this.resultsContainer) {
      this.resultsContainer.style.display = 'none';
    }
  }

  formatPrice(price) {
    return new Intl.NumberFormat('ar-IQ').format(price) + ' د.ع';
  }
}

// Real-time Notifications
class NotificationSystem {
  constructor() {
    this.container = document.getElementById('notification-container');
    this.notifications = [];
    this.init();
  }

  init() {
    this.createContainer();
    // Only use polling in development mode since WebSocket is not enabled
    this.startPolling();
  }

  createContainer() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'notification-container';
      this.container.className = 'notification-container';
      document.body.appendChild(this.container);
    }
  }

  connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    try {
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/notifications/`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          this.showNotification(data.notification);
        }
      };
      
      ws.onerror = (error) => {
        console.log('WebSocket error (expected in dev mode):', error);
        // Fall back to polling if WebSocket fails
        this.startPolling();
      };
      
      ws.onclose = () => {
        console.log('WebSocket closed');
        // Reconnect after 5 seconds
        setTimeout(() => this.connectWebSocket(), 5000);
      };
      
      this.ws = ws;
    } catch (error) {
      console.log('WebSocket connection failed, using polling:', error);
      this.startPolling();
    }
  }

  startPolling() {
    // Disabled polling to prevent JavaScript errors
    // setInterval(() => this.checkNotifications(), 30000);
  }

  async checkNotifications() {
    try {
      const response = await fetch('/api/notifications/unread/');
      
      if (response.status === 403 || response.status === 401) {
        // User not authenticated, skip notification check
        return;
      }
      
      const data = await response.json();
      
      if (data.notifications && Array.isArray(data.notifications)) {
        data.notifications.forEach(notification => {
          if (!this.notifications.includes(notification.id)) {
            this.showNotification(notification);
            this.notifications.push(notification.id);
          }
        });
      }
    } catch (error) {
      console.error('Notification polling error:', error);
    }
  }

  showNotification(notification) {
    const notificationEl = document.createElement('div');
    notificationEl.className = `notification notification-${notification.type}`;
    notificationEl.innerHTML = `
      <div class="notification-icon">${this.getIcon(notification.type)}</div>
      <div class="notification-content">
        <h4>${notification.title}</h4>
        <p>${notification.message}</p>
      </div>
      <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    this.container.appendChild(notificationEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      notificationEl.classList.add('notification-hiding');
      setTimeout(() => notificationEl.remove(), 300);
    }, 5000);
  }

  getIcon(type) {
    const icons = {
      'success': '✓',
      'error': '✕',
      'warning': '⚠',
      'info': 'ℹ',
      'message': '💬',
      'property': '🏠'
    };
    return icons[type] || 'ℹ';
  }
}

// Enhanced Property Map
class EnhancedPropertyMap {
  constructor(mapId, properties = []) {
    this.mapId = mapId;
    this.properties = properties;
    this.map = null;
    this.markers = [];
    this.cluster = null;
    this.init();
  }

  init() {
    if (typeof L !== 'undefined') {
      this.loadMap();
    } else {
      console.error('Leaflet not loaded');
    }
  }

  loadMap() {
    const mapElement = document.getElementById(this.mapId);
    if (!mapElement) return;

    this.map = L.map(this.mapId, {
      center: [33.3152, 44.3661], // Iraq center
      zoom: 6,
      zoomControl: true,
      scrollWheelZoom: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.addMarkers();
    this.addCluster();
  }

  addMarkers() {
    this.properties.forEach(property => {
      if (property.latitude && property.longitude) {
        const marker = L.marker([property.latitude, property.longitude])
          .bindPopup(this.createPopup(property))
          .addTo(this.map);
        
        this.markers.push(marker);
      }
    });
  }

  createPopup(property) {
    return `
      <div class="map-popup">
        <img src="${property.image}" alt="${property.title}" class="popup-image">
        <h4>${property.title}</h4>
        <p class="popup-price">${this.formatPrice(property.price)}</p>
        <p class="popup-location">${property.location}</p>
        <a href="${property.url}" class="btn btn-sm btn-primary">عرض التفاصيل</a>
      </div>
    `;
  }

  addCluster() {
    if (typeof L.markerClusterGroup !== 'undefined') {
      this.cluster = L.markerClusterGroup({
        showCoverageOnHover: false,
        maxClusterRadius: 80
      });
      
      this.markers.forEach(marker => this.cluster.addLayer(marker));
      this.map.addLayer(this.cluster);
    }
  }

  formatPrice(price) {
    return new Intl.NumberFormat('ar-IQ').format(price) + ' د.ع';
  }

  fitBounds() {
    if (this.markers.length > 0) {
      const group = L.featureGroup(this.markers);
      this.map.fitBounds(group.getBounds().pad(0.1));
    }
  }
}

// Image Gallery with Zoom
class ImageGallery {
  constructor(galleryId) {
    this.gallery = document.getElementById(galleryId);
    this.currentIndex = 0;
    this.images = [];
    this.lightbox = null;
    this.init();
  }

  init() {
    if (!this.gallery) return;
    
    this.images = Array.from(this.gallery.querySelectorAll('.gallery-image'));
    this.createLightbox();
    this.attachEvents();
  }

  createLightbox() {
    this.lightbox = document.createElement('div');
    this.lightbox.className = 'lightbox';
    this.lightbox.innerHTML = `
      <div class="lightbox-content">
        <button class="lightbox-close">&times;</button>
        <button class="lightbox-prev">&lsaquo;</button>
        <button class="lightbox-next">&rsaquo;</button>
        <img src="" alt="" class="lightbox-image">
        <div class="lightbox-counter"></div>
      </div>
    `;
    document.body.appendChild(this.lightbox);
  }

  attachEvents() {
    this.images.forEach((img, index) => {
      img.addEventListener('click', () => this.openLightbox(index));
    });

    this.lightbox.querySelector('.lightbox-close').addEventListener('click', () => this.closeLightbox());
    this.lightbox.querySelector('.lightbox-prev').addEventListener('click', () => this.prevImage());
    this.lightbox.querySelector('.lightbox-next').addEventListener('click', () => this.nextImage());
    
    this.lightbox.addEventListener('click', (e) => {
      if (e.target === this.lightbox) this.closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
      if (!this.lightbox.classList.contains('active')) return;
      
      if (e.key === 'Escape') this.closeLightbox();
      if (e.key === 'ArrowLeft') this.prevImage();
      if (e.key === 'ArrowRight') this.nextImage();
    });
  }

  openLightbox(index) {
    this.currentIndex = index;
    this.updateLightbox();
    this.lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  closeLightbox() {
    this.lightbox.classList.remove('active');
    document.body.style.overflow = '';
  }

  updateLightbox() {
    const img = this.images[this.currentIndex];
    const lightboxImg = this.lightbox.querySelector('.lightbox-image');
    const counter = this.lightbox.querySelector('.lightbox-counter');
    
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    counter.textContent = `${this.currentIndex + 1} / ${this.images.length}`;
  }

  prevImage() {
    this.currentIndex = (this.currentIndex - 1 + this.images.length) % this.images.length;
    this.updateLightbox();
  }

  nextImage() {
    this.currentIndex = (this.currentIndex + 1) % this.images.length;
    this.updateLightbox();
  }
}

// Performance Monitoring
class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.init();
  }

  init() {
    if ('PerformanceObserver' in window) {
      this.monitorPageLoad();
      this.monitorResources();
    }
  }

  monitorPageLoad() {
    window.addEventListener('load', () => {
      try {
        // Use Performance API for accurate timing
        const perfData = performance.getEntriesByType('navigation')[0];
        if (perfData) {
          const pageLoadTime = perfData.loadEventEnd - perfData.fetchStart;
          const connectTime = perfData.responseEnd - perfData.requestStart;
          const renderTime = perfData.domComplete - perfData.domInteractive;
          
          this.metrics = {
            pageLoadTime: Math.max(0, pageLoadTime),
            connectTime: Math.max(0, connectTime),
            renderTime: Math.max(0, renderTime)
          };
        } else {
          // Fallback to timing API
          const pageLoadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
          this.metrics = {
            pageLoadTime: Math.max(0, pageLoadTime),
            connectTime: 0,
            renderTime: 0
          };
        }
        
        console.log('Performance Metrics:', this.metrics);
        this.sendMetrics();
      } catch (error) {
        console.error('Error calculating performance metrics:', error);
        this.metrics = {
          pageLoadTime: 0,
          connectTime: 0,
          renderTime: 0
        };
      }
    });
  }

  monitorResources() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach(entry => {
        if (entry.entryType === 'resource') {
          console.log(`${entry.name}: ${entry.duration}ms`);
        }
      });
    });
    
    observer.observe({ entryTypes: ['resource'] });
  }

  async sendMetrics() {
    // Disabled metrics sending to avoid connection errors
    // Metrics are optional for now
    return;
  }
}

// Lazy Loading Images
class LazyLoader {
  constructor() {
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(this.handleIntersection.bind(this), {
        rootMargin: '50px 0px',
        threshold: 0.01
      });
      
      document.querySelectorAll('img[data-src]').forEach(img => {
        this.observer.observe(img);
      });
    } else {
      this.fallback();
    }
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.add('loaded');
        this.observer.unobserve(img);
      }
    });
  }

  fallback() {
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
    });
  }
}

// Form Validation Enhancement
class FormValidator {
  constructor(formId) {
    this.form = document.getElementById(formId);
    this.init();
  }

  init() {
    if (!this.form) return;
    
    this.form.addEventListener('submit', this.handleSubmit.bind(this));
    this.form.querySelectorAll('input, select, textarea').forEach(field => {
      field.addEventListener('blur', this.validateField.bind(this));
      field.addEventListener('input', this.clearError.bind(this));
    });
  }

  handleSubmit(e) {
    if (!this.validateForm()) {
      e.preventDefault();
      return false;
    }
  }

  validateField(e) {
    const field = e.target;
    const error = this.getFieldError(field);
    
    if (error) {
      this.showError(field, error);
    } else {
      this.clearError(e);
    }
  }

  getFieldError(field) {
    if (field.required && !field.value.trim()) {
      return 'هذا الحقل مطلوب';
    }
    
    if (field.type === 'email' && field.value && !this.isValidEmail(field.value)) {
      return 'البريد الإلكتروني غير صحيح';
    }
    
    if (field.type === 'tel' && field.value && !this.isValidPhone(field.value)) {
      return 'رقم الهاتف غير صحيح';
    }
    
    if (field.min && parseFloat(field.value) < parseFloat(field.min)) {
      return `القيمة يجب أن تكون ${field.min} على الأقل`;
    }
    
    if (field.max && parseFloat(field.value) > parseFloat(field.max)) {
      return `القيمة يجب أن تكون ${field.max} على الأكثر`;
    }
    
    return null;
  }

  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  isValidPhone(phone) {
    return /^[\d\s\-\+\(\)]+$/.test(phone) && phone.replace(/\D/g, '').length >= 10;
  }

  showError(field, message) {
    const errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }
    field.classList.add('error');
  }

  clearError(e) {
    const field = e.target;
    const errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
      errorElement.style.display = 'none';
    }
    field.classList.remove('error');
  }

  validateForm() {
    let isValid = true;
    this.form.querySelectorAll('input, select, textarea').forEach(field => {
      const error = this.getFieldError(field);
      if (error) {
        this.showError(field, error);
        isValid = false;
      }
    });
    return isValid;
  }
}

// ===== Back to Top Button =====
class BackToTop {
  constructor() {
    this.button = document.getElementById('back-to-top');
    this.init();
  }

  init() {
    if (this.button) {
      // Always show the button
      this.button.classList.add('visible');
      this.button.addEventListener('click', this.scrollToTop.bind(this));
    }
  }

  handleScroll() {
    // Always keep button visible
    this.button.classList.add('visible');
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
}

// Initialize back to top button when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new BackToTop();
});

// Initialize all features when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Initialize search
  if (document.getElementById('search-input')) {
    new AdvancedSearch();
  }
  
  // Initialize notifications
  new NotificationSystem();
  
  // Initialize lazy loading
  new LazyLoader();
  
  // Initialize performance monitoring
  new PerformanceMonitor();
  
  // Initialize form validators - disabled to prevent errors
  // document.querySelectorAll('form[data-validate]').forEach(form => {
  //   new FormValidator(form.id);
  // });
  
  // Initialize image galleries
  document.querySelectorAll('.image-gallery').forEach(gallery => {
    new ImageGallery(gallery.id);
  });
});