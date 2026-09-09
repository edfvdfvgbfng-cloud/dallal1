/**
 * Interactive Map JavaScript
 * Handles map initialization, API calls, markers, heatmaps, and user interactions
 */

let map;
let propertyMarkers = [];
let amenityMarkers = [];
let heatmapLayer = null;
let currentPropertyData = null;
let currentTileLayer = null;

// API Base URL
const API_BASE = '/api/map';

// Map layer configurations
const MAP_LAYERS = {
    osm: {
        name: 'OpenStreetMap',
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    satellite: {
        name: 'Satellite',
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    },
    terrain: {
        name: 'Terrain',
        url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="https://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
    },
    dark: {
        name: 'Dark',
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd'
    },
    hybrid: {
        name: 'Hybrid',
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }
};

/**
 * Show error message
 */
function showErrorMessage(message) {
    const notification = document.createElement('div');
    notification.className = 'alert alert-danger alert-dismissible fade show';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.map-container').insertBefore(notification, document.querySelector('.map-container').firstChild);
    setTimeout(() => notification.remove(), 5000);
}

// Initialize map when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    try {
        initializeMap();
        setupEventListeners();
        loadInitialData();
    } catch (error) {
        console.error('Error initializing map:', error);
        showErrorMessage('حدث خطأ أثناء تحميل الخريطة');
    }
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    try {
        // Default center on Iraq
        const defaultCenter = [33.3152, 44.3661]; // Baghdad coordinates
        const defaultZoom = 6;

        map = L.map('map').setView(defaultCenter, defaultZoom);

        // Add default tile layer (OpenStreetMap)
        const defaultLayer = MAP_LAYERS.osm;
        currentTileLayer = L.tileLayer(defaultLayer.url, {
            attribution: defaultLayer.attribution,
            maxZoom: 19
        }).addTo(map);

        // Add scale control
        L.control.scale({
            imperial: false,
            metric: true
        }).addTo(map);

        // Add layer control
        const baseLayers = {};
        Object.keys(MAP_LAYERS).forEach(key => {
            const layer = MAP_LAYERS[key];
            baseLayers[layer.name] = L.tileLayer(layer.url, {
                attribution: layer.attribution,
                subdomains: layer.subdomains || 'abc',
                maxZoom: 19
            });
        });

        L.control.layers(baseLayers).addTo(map);
    } catch (error) {
        console.error('Error creating map:', error);
        throw error;
    }
}

/**
 * Switch map layer
 */
function switchMapLayer(layerKey) {
    try {
        if (!map || !currentTileLayer) return;

        const layerConfig = MAP_LAYERS[layerKey];
        if (!layerConfig) return;

        // Remove current layer
        map.removeLayer(currentTileLayer);

        // Add new layer
        currentTileLayer = L.tileLayer(layerConfig.url, {
            attribution: layerConfig.attribution,
            subdomains: layerConfig.subdomains || 'abc',
            maxZoom: 19
        }).addTo(map);

        // Update active state in UI
        document.querySelectorAll('.layer-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-layer="${layerKey}"]`).classList.add('active');
    } catch (error) {
        console.error('Error switching layer:', error);
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Sidebar toggle
    document.getElementById('toggle-sidebar').addEventListener('click', toggleSidebar);
    document.getElementById('close-sidebar').addEventListener('click', toggleSidebar);

    // Search button
    document.getElementById('search-btn').addEventListener('click', performSearch);

    // Location search
    document.getElementById('use-location-btn').addEventListener('click', getCurrentLocation);
    document.getElementById('location-search-btn').addEventListener('click', performLocationSearch);

    // Radius slider
    document.getElementById('radius-slider').addEventListener('input', function(e) {
        document.getElementById('radius-value').textContent = e.target.value + ' كم';
    });

    // Map layers toggles
    document.getElementById('heatmap-toggle').addEventListener('change', toggleHeatmap);
    document.getElementById('amenities-toggle').addEventListener('change', toggleAmenities);
    document.getElementById('markers-toggle').addEventListener('change', togglePropertyMarkers);

    // Amenity checkboxes
    document.querySelectorAll('.amenity-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateAmenityMarkers);
    });

    // Map controls
    document.getElementById('clear-filters').addEventListener('click', clearFilters);
    document.getElementById('refresh-map').addEventListener('click', refreshMap);

    // Settings toggle
    document.getElementById('settings-toggle').addEventListener('click', toggleSettingsMenu);

    // Layer selector close
    document.getElementById('close-layer-selector').addEventListener('click', hideLayerSelector);

    // Zoom controls
    document.getElementById('zoom-in').addEventListener('click', zoomIn);
    document.getElementById('zoom-out').addEventListener('click', zoomOut);
    document.getElementById('zoom-reset').addEventListener('click', zoomReset);
    document.getElementById('zoom-fit').addEventListener('click', zoomToFit);
    document.getElementById('zoom-location').addEventListener('click', zoomToLocation);

    // Area comparison
    document.getElementById('compare-areas-btn').addEventListener('click', compareAreas);

    // Popup controls
    document.getElementById('close-popup').addEventListener('click', hidePropertyPopup);
    document.getElementById('popup-favorite-btn').addEventListener('click', toggleFavorite);

    // Map click to hide popup and settings menu
    map.on('click', function() {
        hidePropertyPopup();
        hideSettingsMenu();
    });
}

/**
 * Toggle settings menu
 */
function toggleSettingsMenu() {
    const menu = document.getElementById('settings-menu');
    menu.classList.toggle('show');
}

/**
 * Hide settings menu
 */
function hideSettingsMenu() {
    const menu = document.getElementById('settings-menu');
    menu.classList.remove('show');
}

/**
 * Show layer selector
 */
function showLayerSelector() {
    const selector = document.getElementById('layer-selector-panel');
    selector.classList.remove('hidden');
    hideSettingsMenu();
}

/**
 * Hide layer selector
 */
function hideLayerSelector() {
    const selector = document.getElementById('layer-selector-panel');
    selector.classList.add('hidden');
}

/**
 * Zoom in
 */
function zoomIn() {
    try {
        if (map) {
            map.zoomIn();
        }
    } catch (error) {
        console.error('Error zooming in:', error);
    }
}

/**
 * Zoom out
 */
function zoomOut() {
    try {
        if (map) {
            map.zoomOut();
        }
    } catch (error) {
        console.error('Error zooming out:', error);
    }
}

/**
 * Reset zoom to default
 */
function zoomReset() {
    try {
        if (map) {
            map.setView([33.3152, 44.3661], 6); // Baghdad coordinates
        }
    } catch (error) {
        console.error('Error resetting zoom:', error);
    }
}

/**
 * Zoom to fit all markers
 */
function zoomToFit() {
    try {
        if (map && propertyMarkers.length > 0) {
            const bounds = L.latLngBounds(
                propertyMarkers.map(marker => marker.getLatLng())
            );
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    } catch (error) {
        console.error('Error zooming to fit:', error);
    }
}

/**
 * Zoom to current location
 */
function zoomToLocation() {
    try {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    map.setView([lat, lng], 15);
                },
                (error) => {
                    console.error('Error getting location:', error);
                    showErrorMessage('غير قادر على الحصول على موقعك');
                }
            );
        } else {
            showErrorMessage('المتصفح لا يدعم تحديد الموقع');
        }
    } catch (error) {
        console.error('Error in zoomToLocation:', error);
    }
}

/**
 * Load initial data
 */
function loadInitialData() {
    try {
        showLoading();

        // Load properties for default view
        loadPropertiesOnMap();

        // Load area statistics
        loadAreaStatistics();

        hideLoading();
    } catch (error) {
        console.error('Error loading initial data:', error);
        hideLoading();
        showErrorMessage('حدث خطأ أثناء تحميل البيانات');
    }
}

/**
 * Toggle sidebar visibility
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.map-sidebar');
    sidebar.classList.toggle('collapsed');
}

/**
 * Perform property search
 */
function performSearch() {
    showLoading();
    
    const governorate = document.getElementById('governorate-select').value;
    const city = document.getElementById('city-input').value;
    const propertyType = document.getElementById('property-type-select').value;
    const transactionType = document.getElementById('transaction-type-select').value;
    const maxPrice = document.getElementById('max-price-input').value;
    const minArea = document.getElementById('min-area-input').value;

    // Build API URL
    let apiUrl = '/api/map/search/?limit=100';
    
    if (governorate) apiUrl += `&governorate=${encodeURIComponent(governorate)}`;
    if (city) apiUrl += `&city=${encodeURIComponent(city)}`;
    if (propertyType) apiUrl += `&property_type=${encodeURIComponent(propertyType)}`;
    if (transactionType) apiUrl += `&transaction_type=${encodeURIComponent(transactionType)}`;
    if (maxPrice) apiUrl += `&max_price=${encodeURIComponent(maxPrice)}`;
    if (minArea) apiUrl += `&min_area=${encodeURIComponent(minArea)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            displayPropertiesOnMap(data.properties);
            loadAreaStatistics(governorate, city);
            
            // Zoom to fit all markers
            if (data.properties.length > 0) {
                const bounds = L.latLngBounds(
                    data.properties.map(p => [p.latitude, p.longitude])
                );
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        })
        .catch(error => {
            console.error('Error searching properties:', error);
            showNotification('حدث خطأ أثناء البحث', 'error');
        })
        .finally(() => {
            hideLoading();
        });
}

/**
 * Get current user location
 */
function getCurrentLocation() {
    if (navigator.geolocation) {
        showLoading();
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                document.getElementById('lat-input').value = lat;
                document.getElementById('lng-input').value = lng;
                
                // Center map on user location
                map.setView([lat, lng], 13);
                
                // Add user marker
                L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'user-location-marker',
                        html: '🎯',
                        iconSize: [30, 30]
                    })
                }).addTo(map);
                
                hideLoading();
                showNotification('تم تحديد موقعك بنجاح', 'success');
            },
            (error) => {
                hideLoading();
                showNotification('فشل في تحديد الموقع. يرجى إدخال الإحداثيات يدوياً', 'error');
            }
        );
    } else {
        showNotification('المتصفح لا يدعم تحديد الموقع', 'error');
    }
}

/**
 * Perform location-based search
 */
function performLocationSearch() {
    const lat = document.getElementById('lat-input').value;
    const lng = document.getElementById('lng-input').value;
    const radius = document.getElementById('radius-slider').value;

    if (!lat || !lng) {
        showNotification('يرجى إدخال الإحداثيات', 'error');
        return;
    }

    showLoading();

    const apiUrl = `${API_BASE}/location-search/?latitude=${lat}&longitude=${lng}&radius_km=${radius}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            displayPropertiesOnMap(data.properties);
            
            // Draw radius circle
            if (window.radiusCircle) {
                map.removeLayer(window.radiusCircle);
            }
            window.radiusCircle = L.circle([lat, lng], {
                radius: radius * 1000, // Convert km to meters
                color: '#FF7A00',
                fillColor: '#FF7A00',
                fillOpacity: 0.1
            }).addTo(map);
            
            // Center map on search location
            map.setView([lat, lng], 12);
            
            showNotification(`تم العثور على ${data.total_count} عقار`, 'success');
        })
        .catch(error => {
            console.error('Error in location search:', error);
            showNotification('حدث خطأ أثناء البحث', 'error');
        })
        .finally(() => {
            hideLoading();
        });
}

/**
 * Load properties on map
 */
function loadPropertiesOnMap() {
    try {
        const apiUrl = '/api/map/properties/?limit=100';

        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayPropertiesOnMap(data.properties);
                } else {
                    console.error('API error:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading properties:', error);
            });
    } catch (error) {
        console.error('Error in loadPropertiesOnMap:', error);
    }
}

/**
 * Display properties on map
 */
function displayPropertiesOnMap(properties) {
    // Clear existing markers
    clearPropertyMarkers();

    properties.forEach(property => {
        const marker = createPropertyMarker(property);
        propertyMarkers.push(marker);
        marker.addTo(map);
    });

    currentPropertyData = properties;
}

/**
 * Create property marker
 */
function createPropertyMarker(property) {
    const isFeatured = property.is_featured;
    const markerSize = isFeatured ? 30 : 24;
    
    const icon = L.divIcon({
        className: `property-marker ${isFeatured ? 'featured' : ''}`,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize/2, markerSize/2]
    });

    const marker = L.marker([property.latitude, property.longitude], { icon });
    
    // Add click event
    marker.on('click', () => showPropertyPopup(property));
    
    return marker;
}

/**
 * Show property popup
 */
function showPropertyPopup(property) {
    const popup = document.getElementById('property-popup');
    
    // Update popup content
    document.getElementById('popup-title').textContent = property.title;
    document.getElementById('popup-price').textContent = formatPrice(property.price);
    document.getElementById('popup-currency').textContent = property.currency === 'USD' ? 'دولار' : 'دينار';
    document.getElementById('popup-location').textContent = `${property.governorate} - ${property.city}`;
    document.getElementById('popup-type').textContent = getPropertyTypeDisplay(property.type);
    document.getElementById('popup-area').textContent = property.total_area ? `${property.total_area} م²` : '-';
    document.getElementById('popup-bedrooms').textContent = property.bedrooms || '-';
    document.getElementById('popup-bathrooms').textContent = property.bathrooms || '-';
    
    // Set image
    const image = document.getElementById('popup-image');
    if (property.image) {
        image.src = property.image;
    } else {
        image.src = '/static/images/property-placeholder.jpg';
    }
    
    // Set view button link
    document.getElementById('popup-view-btn').href = `/property/${property.slug}/`;
    
    // Show popup
    popup.classList.remove('hidden');
    
    // Center map on property
    map.setView([property.latitude, property.longitude], 15);
}

/**
 * Hide property popup
 */
function hidePropertyPopup() {
    document.getElementById('property-popup').classList.add('hidden');
}

/**
 * Toggle heatmap layer
 */
function toggleHeatmap() {
    const showHeatmap = document.getElementById('heatmap-toggle').checked;
    
    if (showHeatmap) {
        loadHeatmap();
    } else if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
        heatmapLayer = null;
    }
}

/**
 * Load heatmap data
 */
function loadHeatmap() {
    const governorate = document.getElementById('governorate-select').value || 'بغداد';
    const city = document.getElementById('city-input').value || 'بغداد';
    
    const apiUrl = `${API_BASE}/heatmap/?governorate=${encodeURIComponent(governorate)}&city=${encodeURIComponent(city)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.data && data.data.length > 0) {
                displayHeatmap(data.data);
            }
        })
        .catch(error => {
            console.error('Error loading heatmap:', error);
        });
}

/**
 * Display heatmap on map
 */
function displayHeatmap(heatmapData) {
    // Remove existing heatmap
    if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
    }

    // Create rectangles for heatmap cells
    const rectangles = heatmapData.map(cell => {
        const bounds = [
            [cell.lat_min, cell.lng_min],
            [cell.lat_max, cell.lng_max]
        ];
        
        // Color based on price value
        const normalizedValue = cell.value / 10000000; // Normalize for color
        const color = getPriceColor(normalizedValue);
        
        return L.rectangle(bounds, {
            color: color,
            fillColor: color,
            fillOpacity: 0.4,
            weight: 1
        }).bindPopup(`متوسط السعر: ${formatPrice(cell.value)}`);
    });

    // Create layer group
    heatmapLayer = L.layerGroup(rectangles);
    heatmapLayer.addTo(map);
}

/**
 * Get color based on price value
 */
function getPriceColor(normalizedValue) {
    // Red for high prices, green for low prices
    if (normalizedValue > 0.8) return '#ff4444';
    if (normalizedValue > 0.6) return '#ff8800';
    if (normalizedValue > 0.4) return '#ffcc00';
    if (normalizedValue > 0.2) return '#88ff00';
    return '#00ff44';
}

/**
 * Toggle amenities layer
 */
function toggleAmenities() {
    const showAmenities = document.getElementById('amenities-toggle').checked;
    
    if (showAmenities) {
        updateAmenityMarkers();
    } else {
        clearAmenityMarkers();
    }
}

/**
 * Update amenity markers
 */
function updateAmenityMarkers() {
    const showAmenities = document.getElementById('amenities-toggle').checked;
    if (!showAmenities) return;

    // Get selected amenity types
    const selectedTypes = Array.from(document.querySelectorAll('.amenity-checkbox:checked'))
        .map(cb => cb.value);

    if (selectedTypes.length === 0) {
        clearAmenityMarkers();
        return;
    }

    // Get current map center and bounds
    const center = map.getCenter();
    const radius = 5; // 5km radius

    const apiUrl = `${API_BASE}/nearby-amenities/?latitude=${center.lat}&longitude=${center.lng}&radius=${radius}&types=${selectedTypes.join(',')}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            displayAmenities(data.amenities);
        })
        .catch(error => {
            console.error('Error loading amenities:', error);
        });
}

/**
 * Display amenities on map
 */
function displayAmenities(amenities) {
    clearAmenityMarkers();

    amenities.forEach(amenity => {
        const icon = getAmenityIcon(amenity.type);
        const marker = L.marker([amenity.latitude, amenity.longitude], {
            icon: L.divIcon({
                className: 'amenity-marker',
                html: icon,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        });

        marker.bindPopup(`
            <strong>${amenity.name}</strong><br>
            ${amenity.type_display}<br>
            المسافة: ${amenity.distance_km} كم
        `);

        amenityMarkers.push(marker);
        marker.addTo(map);
    });
}

/**
 * Get amenity icon
 */
function getAmenityIcon(type) {
    const icons = {
        'school': '🏫',
        'hospital': '🏥',
        'clinic': '🏥',
        'university': '🎓',
        'market': '🏪',
        'mall': '🏬',
        'supermarket': '🏪',
        'mosque': '🕌',
        'church': '⛪',
        'park': '🌳',
        'gas_station': '⛽',
        'bank': '🏦',
        'atm': '🏧',
        'pharmacy': '💊',
        'restaurant': '🍽️',
        'cafe': '☕',
        'gym': '🏋️',
        'airport': '✈️',
        'train_station': '🚂',
        'bus_station': '🚌',
        'other': '📍'
    };
    return icons[type] || '📍';
}

/**
 * Toggle property markers
 */
function togglePropertyMarkers() {
    const showMarkers = document.getElementById('markers-toggle').checked;
    
    propertyMarkers.forEach(marker => {
        if (showMarkers) {
            marker.addTo(map);
        } else {
            map.removeLayer(marker);
        }
    });
}

/**
 * Clear property markers
 */
function clearPropertyMarkers() {
    propertyMarkers.forEach(marker => map.removeLayer(marker));
    propertyMarkers = [];
}

/**
 * Clear amenity markers
 */
function clearAmenityMarkers() {
    amenityMarkers.forEach(marker => map.removeLayer(marker));
    amenityMarkers = [];
}

/**
 * Clear all filters
 */
function clearFilters() {
    document.getElementById('governorate-select').value = '';
    document.getElementById('city-input').value = '';
    document.getElementById('property-type-select').value = '';
    document.getElementById('transaction-type-select').value = '';
    document.getElementById('max-price-input').value = '';
    document.getElementById('min-area-input').value = '';
    document.getElementById('lat-input').value = '';
    document.getElementById('lng-input').value = '';
    document.getElementById('radius-slider').value = 5;
    document.getElementById('radius-value').textContent = '5 كم';
    
    // Reset amenity checkboxes
    document.querySelectorAll('.amenity-checkbox').forEach(cb => {
        cb.checked = cb.value === 'school' || cb.value === 'hospital' || cb.value === 'market';
    });

    // Reset map view
    map.setView([33.3152, 44.3661], 6);
    
    // Reload initial data
    loadInitialData();
    
    showNotification('تم مسح الفلاتر', 'success');
}

/**
 * Refresh map
 */
function refreshMap() {
    showLoading();
    loadInitialData();
    hideLoading();
    showNotification('تم تحديث الخريطة', 'success');
}

/**
 * Load area statistics
 */
function loadAreaStatistics(governorate = '', city = '') {
    let apiUrl = `${API_BASE}/area-stats/`;
    
    if (governorate) apiUrl += `?governorate=${encodeURIComponent(governorate)}`;
    if (city) apiUrl += `&city=${encodeURIComponent(city)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.areas && data.areas.length > 0) {
                const stats = data.areas[0];
                document.getElementById('avg-price').textContent = formatPrice(stats.avg_price);
                document.getElementById('property-count').textContent = stats.total_properties;
                document.getElementById('price-trend').textContent = getPriceTrendDisplay(stats.price_trend);
            }
        })
        .catch(error => {
            console.error('Error loading area stats:', error);
        });
}

/**
 * Compare areas
 */
function compareAreas() {
    const governorate = document.getElementById('governorate-select').value;
    const city = document.getElementById('city-input').value;
    
    if (!governorate || !city) {
        showNotification('يرجى تحديد المحافظة والمدينة أولاً', 'error');
        return;
    }

    const apiUrl = `${API_BASE}/area-comparison/?areas=${encodeURIComponent(governorate + ',' + city)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            displayComparisonResults(data.areas);
        })
        .catch(error => {
            console.error('Error comparing areas:', error);
            showNotification('حدث خطأ أثناء مقارنة المناطق', 'error');
        });
}

/**
 * Display comparison results
 */
function displayComparisonResults(areas) {
    const resultsDiv = document.getElementById('comparison-results');
    resultsDiv.innerHTML = '';
    resultsDiv.classList.remove('hidden');

    areas.forEach(area => {
        const item = document.createElement('div');
        item.className = 'comparison-item';
        item.innerHTML = `
            <div class="comparison-name">${area.city} - ${area.district || 'الكل'}</div>
            <div class="comparison-score">
                <span>التقييم: ${area.score}/100</span>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${area.score}%"></div>
                </div>
            </div>
            <div class="comparison-score">
                <span>متوسط السعر: ${formatPrice(area.avg_price)}</span>
            </div>
            <div class="comparison-score">
                <span>عدد العقارات: ${area.total_properties}</span>
            </div>
        `;
        resultsDiv.appendChild(item);
    });
}

/**
 * Toggle favorite
 */
function toggleFavorite() {
    const btn = document.getElementById('popup-favorite-btn');
    const isFavorited = btn.textContent.includes('إلغاء');
    
    if (isFavorited) {
        btn.textContent = '❤️ حفظ';
        showNotification('تم إزالة العقار من المفضلة', 'success');
    } else {
        btn.textContent = '❤️ إلغاء الحفظ';
        showNotification('تم إضافة العقار إلى المفضلة', 'success');
    }
}

/**
 * Show loading indicator
 */
function showLoading() {
    document.getElementById('map-loading').classList.remove('hidden');
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    document.getElementById('map-loading').classList.add('hidden');
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 15px 25px;
        background: ${type === 'error' ? '#ff4444' : type === 'success' ? '#00C851' : '#33b5e5'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        animation: slideDown 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Format price
 */
function formatPrice(price) {
    if (!price) return '-';
    return new Intl.NumberFormat('ar-IQ').format(price);
}

/**
 * Get property type display
 */
function getPropertyTypeDisplay(type) {
    const types = {
        'apartment': 'شقة',
        'house': 'فيلا',
        'land': 'أرض',
        'commercial': 'تجاري',
        'office': 'مكتب',
        'villa': 'فيلا'
    };
    return types[type] || type;
}

/**
 * Get price trend display
 */
function getPriceTrendDisplay(trend) {
    const trends = {
        'rising': '📈 ارتفاع',
        'falling': '📉 انخفاض',
        'stable': '➡️ مستقر'
    };
    return trends[trend] || trend;
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    @keyframes slideUp {
        from { transform: translateX(-50%) translateY(0); opacity: 1; }
        to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
    }
`;
document.head.appendChild(style);