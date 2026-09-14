/**
 * Dalal Listing Pages JavaScript
 * Interactive functionality for listing pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all listing page functionality
    initListingPages();
});

function initListingPages() {
    initViewToggle();
    initMobileFilters();
    initListingActions();
    initLazyLoading();
    initLocalStorage();
}

// ============================================================================
// VIEW TOGGLE (Grid/List)
// ============================================================================

function initViewToggle() {
    const viewToggle = document.querySelector('.listing-view-toggle');
    if (!viewToggle) return;

    const gridBtn = viewToggle.querySelector('[data-view="grid"]');
    const listBtn = viewToggle.querySelector('[data-view="list"]');
    const listingsGrid = document.querySelector('.listings-grid');

    // Load saved preference
    const savedView = localStorage.getItem('listingView') || 'grid';
    setView(savedView);

    gridBtn.addEventListener('click', () => setView('grid'));
    listBtn.addEventListener('click', () => setView('list'));

    function setView(view) {
        if (view === 'grid') {
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
            listingsGrid.classList.remove('list-view');
        } else {
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
            listingsGrid.classList.add('list-view');
        }
        localStorage.setItem('listingView', view);
    }
}

// ============================================================================
// MOBILE FILTERS
// ============================================================================

function initMobileFilters() {
    const filterBtn = document.querySelector('.listing-filter-btn');
    const filtersSidebar = document.querySelector('.listing-filters');
    const filtersOverlay = document.querySelector('.listing-filters-overlay');
    const closeBtn = document.querySelector('.listing-filters-close');

    if (!filterBtn || !filtersSidebar) return;

    // Create overlay if it doesn't exist
    if (!filtersOverlay) {
        const overlay = document.createElement('div');
        overlay.className = 'listing-filters-overlay';
        document.body.appendChild(overlay);
        
        overlay.addEventListener('click', closeFilters);
    }

    filterBtn.addEventListener('click', openFilters);

    if (closeBtn) {
        closeBtn.addEventListener('click', closeFilters);
    }

    function openFilters() {
        filtersSidebar.classList.add('open');
        document.querySelector('.listing-filters-overlay').classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeFilters() {
        filtersSidebar.classList.remove('open');
        document.querySelector('.listing-filters-overlay').classList.remove('open');
        document.body.style.overflow = '';
    }
}

// ============================================================================
// LISTING ACTIONS (Save, Share, Compare)
// ============================================================================

function initListingActions() {
    // Save/Favorite buttons
    const saveButtons = document.querySelectorAll('.btn-favorite, [data-action="save"]');
    saveButtons.forEach(btn => {
        btn.addEventListener('click', handleSaveAction);
    });

    // Share buttons
    const shareButtons = document.querySelectorAll('[data-action="share"]');
    shareButtons.forEach(btn => {
        btn.addEventListener('click', handleShareAction);
    });

    // Compare buttons
    const compareButtons = document.querySelectorAll('[data-action="compare"]');
    compareButtons.forEach(btn => {
        btn.addEventListener('click', handleCompareAction);
    });
}

async function handleSaveAction(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const propertyId = btn.dataset.propertyId || btn.dataset.favId;
    
    if (!propertyId) return;

    try {
        const isSaved = btn.classList.contains('active');
        const url = isSaved 
            ? `/api/properties/${propertyId}/unsave/`
            : `/api/properties/${propertyId}/save/`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            btn.classList.toggle('active');
            const icon = btn.querySelector('.fav-icon');
            if (icon) {
                icon.textContent = isSaved ? '🤍' : '❤️';
            }
            showNotification(isSaved ? 'تمت الإزالة من المفضلة' : 'تمت الإضافة إلى المفضلة');
        }
    } catch (error) {
        console.error('Save action failed:', error);
        showNotification('حدث خطأ، يرجى المحاولة مرة أخرى', 'error');
    }
}

async function handleShareAction(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const propertyUrl = btn.dataset.propertyUrl || window.location.href;
    const propertyTitle = btn.dataset.propertyTitle || 'هذا العقار';

    if (navigator.share) {
        try {
            await navigator.share({
                title: propertyTitle,
                url: propertyUrl,
            });
        } catch (error) {
            console.log('Share canceled or failed:', error);
        }
    } else {
        // Fallback: copy to clipboard
        copyToClipboard(propertyUrl);
        showNotification('تم نسخ الرابط');
    }
}

async function handleCompareAction(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const propertyId = btn.dataset.propertyId || btn.dataset.compareId;
    
    if (!propertyId) return;

    // Get current comparison list from localStorage
    let compareList = JSON.parse(localStorage.getItem('compareList') || '[]');
    
    if (compareList.includes(propertyId)) {
        // Remove from comparison
        compareList = compareList.filter(id => id !== propertyId);
        btn.classList.remove('active');
        showNotification('تمت الإزالة من المقارنة');
    } else {
        // Add to comparison (max 4 items)
        if (compareList.length >= 4) {
            showNotification('يمكنك مقارنة 4 عقارات كحد أقصى', 'warning');
            return;
        }
        compareList.push(propertyId);
        btn.classList.add('active');
        showNotification('تمت الإضافة للمقارنة');
    }

    localStorage.setItem('compareList', JSON.stringify(compareList));
    updateCompareButton();
}

function updateCompareButton() {
    const compareList = JSON.parse(localStorage.getItem('compareList') || '[]');
    const compareBtn = document.querySelector('.compare-button');
    
    if (compareBtn) {
        if (compareList.length > 0) {
            compareBtn.classList.add('active');
            compareBtn.querySelector('.count').textContent = compareList.length;
        } else {
            compareBtn.classList.remove('active');
        }
    }
}

// ============================================================================
// LAZY LOADING IMAGES
// ============================================================================

function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    
                    if (src) {
                        img.src = src;
                        img.onload = () => {
                            img.classList.add('loaded');
                        };
                        img.onerror = () => {
                            img.classList.add('error');
                        };
                    }
                    
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback for older browsers
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// ============================================================================
// LOCAL STORAGE HELPERS
// ============================================================================

function initLocalStorage() {
    // Initialize compare list if not exists
    if (!localStorage.getItem('compareList')) {
        localStorage.setItem('compareList', '[]');
    }
    
    // Update compare button on page load
    updateCompareButton();
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        document.execCommand('copy');
        showNotification('تم نسخ الرابط');
    } catch (error) {
        console.error('Copy failed:', error);
        showNotification('فشل نسخ الرابط', 'error');
    }
    
    document.body.removeChild(textarea);
}

function showNotification(message, type = 'success') {
    // Remove existing notification
    const existing = document.querySelector('.listing-notification');
    if (existing) {
        existing.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `listing-notification listing-notification-${type}`;
    notification.textContent = message;
    
    // Add styles
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: type === 'success' ? '#22C55E' : type === 'warning' ? '#F59E0B' : '#EF4444',
        color: '#FFFFFF',
        padding: '12px 24px',
        borderRadius: '12px',
        fontSize: '0.95rem',
        fontWeight: '500',
        zIndex: '10000',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        animation: 'slideUp 0.3s ease'
    });

    document.body.appendChild(notification);

    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateX(-50%) translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
    }
    
    @keyframes slideDown {
        from {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
        to {
            opacity: 0;
            transform: translateX(-50%) translateY(20px);
        }
    }
`;
document.head.appendChild(style);

// ============================================================================
// FILTER FORM HANDLING
// ============================================================================

function initFilterForm() {
    const filterForm = document.querySelector('.listing-filters-form');
    if (!filterForm) return;

    // Handle form submission
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get all form data
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        
        // Update URL without reloading
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({}, '', newUrl);
        
        // Close mobile filters if open
        const filtersSidebar = document.querySelector('.listing-filters');
        if (filtersSidebar && filtersSidebar.classList.contains('open')) {
            closeFilters();
        }
        
        // Trigger reload with new filters
        window.location.reload();
    });

    // Handle clear filters
    const clearBtn = document.querySelector('.listing-filters-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            filterForm.reset();
            window.location.href = window.location.pathname;
        });
    }
}

// ============================================================================
// INFINITE SCROLL / LOAD MORE
// ============================================================================

function initLoadMore() {
    const loadMoreBtn = document.querySelector('.listing-load-more');
    if (!loadMoreBtn) return;

    loadMoreBtn.addEventListener('click', async function() {
        const btn = this;
        const nextPage = btn.dataset.nextPage;
        const currentUrl = window.location.href;

        if (!nextPage) return;

        // Show loading state
        btn.disabled = true;
        btn.textContent = 'جاري التحميل...';

        try {
            const response = await fetch(`${currentUrl}?page=${nextPage}`);
            const html = await response.text();
            
            // Parse the response and extract new listings
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newListings = doc.querySelectorAll('.listing-card');
            const listingsGrid = document.querySelector('.listings-grid');

            // Append new listings
            newListings.forEach(card => {
                listingsGrid.appendChild(card);
            });

            // Update button state
            const nextNextPage = doc.querySelector('.listing-load-more')?.dataset.nextPage;
            if (nextNextPage) {
                btn.dataset.nextPage = nextNextPage;
                btn.disabled = false;
                btn.textContent = 'تحميل المزيد';
            } else {
                btn.remove();
            }

            // Reinitialize lazy loading for new images
            initLazyLoading();
            initListingActions();

        } catch (error) {
            console.error('Load more failed:', error);
            btn.disabled = false;
            btn.textContent = 'إعادة المحاولة';
        }
    });
}

// ============================================================================
// SEARCH SUGGESTIONS
// ============================================================================

function initSearchSuggestions() {
    const searchInput = document.querySelector('.listing-search-input');
    if (!searchInput) return;

    let debounceTimer;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();

        if (query.length < 2) {
            hideSuggestions();
            return;
        }

        debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
        }, 300);
    });

    searchInput.addEventListener('blur', function() {
        setTimeout(hideSuggestions, 200);
    });

    async function fetchSuggestions(query) {
        try {
            const response = await fetch(`/api/search/suggestions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            showSuggestions(data.suggestions || []);
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
        }
    }

    function showSuggestions(suggestions) {
        hideSuggestions();

        if (suggestions.length === 0) return;

        const suggestionsBox = document.createElement('div');
        suggestionsBox.className = 'listing-search-suggestions';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'listing-search-suggestion-item';
            item.textContent = suggestion.title;
            item.addEventListener('click', () => {
                searchInput.value = suggestion.title;
                hideSuggestions();
                searchInput.closest('form').submit();
            });
            suggestionsBox.appendChild(item);
        });

        searchInput.parentNode.appendChild(suggestionsBox);
    }

    function hideSuggestions() {
        const existing = document.querySelector('.listing-search-suggestions');
        if (existing) existing.remove();
    }
}

// ============================================================================
// PRICE RANGE SLIDER
// ============================================================================

function initPriceRange() {
    const priceMin = document.querySelector('[name="price_min"]');
    const priceMax = document.querySelector('[name="price_max"]');
    const rangeSlider = document.querySelector('.price-range-slider');

    if (!priceMin || !priceMax || !rangeSlider) return;

    // Add dual slider functionality if needed
    // This is a placeholder for enhanced price range slider
}

// Export functions for global access
window.ListingPages = {
    init: initListingPages,
    setView: (view) => {
        const gridBtn = document.querySelector('[data-view="grid"]');
        const listBtn = document.querySelector('[data-view="list"]');
        const listingsGrid = document.querySelector('.listings-grid');
        
        if (view === 'grid') {
            gridBtn?.classList.add('active');
            listBtn?.classList.remove('active');
            listingsGrid?.classList.remove('list-view');
        } else {
            listBtn?.classList.add('active');
            gridBtn?.classList.remove('active');
            listingsGrid?.classList.add('list-view');
        }
        localStorage.setItem('listingView', view);
    },
    openFilters: () => {
        const filtersSidebar = document.querySelector('.listing-filters');
        const overlay = document.querySelector('.listing-filters-overlay');
        
        filtersSidebar?.classList.add('open');
        overlay?.classList.add('open');
        document.body.style.overflow = 'hidden';
    },
    closeFilters: () => {
        const filtersSidebar = document.querySelector('.listing-filters');
        const overlay = document.querySelector('.listing-filters-overlay');
        
        filtersSidebar?.classList.remove('open');
        overlay?.classList.remove('open');
        document.body.style.overflow = '';
    }
};