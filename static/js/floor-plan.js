/**
 * Floor Plan Viewer JavaScript
 * Handles floor plan navigation and display
 */

let currentFloorPlanIndex = 0;
let floorPlans = [];

document.addEventListener('DOMContentLoaded', function() {
    // Initialize floor plans
    initFloorPlans();
});

function initFloorPlans() {
    // Get all floor plan thumbs
    const thumbs = document.querySelectorAll('.floor-plan-thumb');
    const mainImage = document.getElementById('floor-plan-main');
    
    if (thumbs.length > 0) {
        floorPlans = Array.from(thumbs).map((thumb, index) => ({
            index: index,
            src: thumb.querySelector('img').src,
            title: thumb.querySelector('.floor-plan-title').textContent
        }));
        
        currentFloorPlanIndex = 0;
        updateFloorPlanDisplay();
    }
}

function changeFloorPlan(direction) {
    if (floorPlans.length === 0) return;
    
    currentFloorPlanIndex += direction;
    
    // Wrap around
    if (currentFloorPlanIndex < 0) {
        currentFloorPlanIndex = floorPlans.length - 1;
    } else if (currentFloorPlanIndex >= floorPlans.length) {
        currentFloorPlanIndex = 0;
    }
    
    updateFloorPlanDisplay();
}

function setFloorPlan(index) {
    if (index >= 0 && index < floorPlans.length) {
        currentFloorPlanIndex = index;
        updateFloorPlanDisplay();
    }
}

function updateFloorPlanDisplay() {
    const mainImage = document.getElementById('floor-plan-main');
    const thumbs = document.querySelectorAll('.floor-plan-thumb');
    
    if (mainImage && floorPlans[currentFloorPlanIndex]) {
        // Add fade effect
        mainImage.style.opacity = '0';
        
        setTimeout(() => {
            mainImage.src = floorPlans[currentFloorPlanIndex].src;
            mainImage.alt = `مخطط الطابق - ${floorPlans[currentFloorPlanIndex].title}`;
            mainImage.style.opacity = '1';
        }, 200);
        
        // Update active thumb
        thumbs.forEach((thumb, index) => {
            if (index === currentFloorPlanIndex) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });
        
        // Scroll active thumb into view
        if (thumbs[currentFloorPlanIndex]) {
            thumbs[currentFloorPlanIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }
}

// Keyboard navigation for floor plans
document.addEventListener('keydown', function(e) {
    // Only handle if floor plan section exists and user is not typing in an input
    if (document.querySelector('.floor-plan-section') && 
        !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        
        if (e.key === 'ArrowLeft') {
            changeFloorPlan(-1);
            e.preventDefault();
        } else if (e.key === 'ArrowRight') {
            changeFloorPlan(1);
            e.preventDefault();
        }
    }
});

// Touch/swipe support for mobile
let touchStartX = 0;
let touchEndX = 0;

const floorPlanContainer = document.querySelector('.floor-plan-main');
if (floorPlanContainer) {
    floorPlanContainer.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    floorPlanContainer.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
}

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swipe left - next
            changeFloorPlan(1);
        } else {
            // Swipe right - previous
            changeFloorPlan(-1);
        }
    }
}

// Zoom functionality for floor plans
let currentZoom = 1;
const ZOOM_STEP = 0.2;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;

function zoomFloorPlan(direction) {
    const mainImage = document.getElementById('floor-plan-main');
    if (!mainImage) return;
    
    if (direction === 'in') {
        currentZoom = Math.min(currentZoom + ZOOM_STEP, MAX_ZOOM);
    } else if (direction === 'out') {
        currentZoom = Math.max(currentZoom - ZOOM_STEP, MIN_ZOOM);
    } else if (direction === 'reset') {
        currentZoom = 1;
    }
    
    mainImage.style.transform = `scale(${currentZoom})`;
    mainImage.style.transition = 'transform 0.3s ease';
}

// Fullscreen mode for floor plan
function toggleFloorPlanFullscreen() {
    const mainImage = document.getElementById('floor-plan-main');
    if (!mainImage) return;
    
    if (!document.fullscreenElement) {
        mainImage.requestFullscreen().catch(err => {
            console.log(`Error attempting to enable fullscreen: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

// Download floor plan
function downloadFloorPlan() {
    const mainImage = document.getElementById('floor-plan-main');
    if (!mainImage) return;
    
    const link = document.createElement('a');
    link.href = mainImage.src;
    link.download = `floor-plan-${Date.now()}.jpg`;
    link.click();
}