/**
 * Advanced Lazy Loading Script
 * Handles progressive image loading with blur effect and error handling
 */

document.addEventListener('DOMContentLoaded', function() {
    // Image observer for lazy loading
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                
                // Add blur effect initially
                img.classList.add('blur');
                
                // When image loads, remove blur and add loaded class
                img.onload = function() {
                    this.classList.remove('blur');
                    this.classList.add('loaded');
                };
                
                // Handle image loading errors
                img.onerror = function() {
                    // Use the onerror handler in HTML, but add fallback here too
                    if (!this.getAttribute('data-fallback-handled')) {
                        this.setAttribute('data-fallback-handled', 'true');
                        const placeholder = this.getAttribute('data-placeholder') || '/static/images/property-placeholder.jpg';
                        this.src = placeholder;
                        this.classList.add('loaded');
                    }
                };
                
                // Stop observing once loaded
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px 0px', // Start loading 50px before element is visible
        threshold: 0.01
    });
    
    // Observe all images with loading="lazy"
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    lazyImages.forEach(img => {
        imageObserver.observe(img);
    });
    
    // Handle images that are already in viewport on load
    window.addEventListener('load', function() {
        lazyImages.forEach(img => {
            if (img.complete) {
                img.classList.add('loaded');
            }
        });
    });
    
    // Preload critical images (above the fold)
    function preloadCriticalImages() {
        const criticalImages = document.querySelectorAll('.listing-card:first-child img, .hero img');
        criticalImages.forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.classList.add('loaded');
            }
        });
    }
    
    // Preload critical images after small delay
    setTimeout(preloadCriticalImages, 100);
    
    // Progressive image loading for gallery
    function setupGalleryLazyLoading() {
        const galleryImages = document.querySelectorAll('.gallery-image');
        
        galleryImages.forEach((img, index) => {
            // Load images in batches
            if (index < 3) {
                // Load first 3 images immediately
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                }
            } else {
                // Load rest when they come into view
                img.loading = 'lazy';
            }
        });
    }
    
    setupGalleryLazyLoading();
    
    // Performance monitoring
    if ('PerformanceObserver' in window) {
        const perfObserver = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.entryType === 'resource' && entry.initiatorType === 'img') {
                    console.log(`Image loaded: ${entry.name} - ${entry.duration}ms`);
                }
            });
        });
        
        perfObserver.observe({entryTypes: ['resource']});
    }
});