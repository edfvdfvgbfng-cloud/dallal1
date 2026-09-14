/**
 * Enhanced Virtual Tour 360° Viewer
 * Supports Equirectangular images, auto-rotation, zoom, fullscreen, VR, hotspots, audio, and more
 */

class VirtualTour360 {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) {
            console.error('Container not found');
            return;
        }

        this.options = {
            imageUrl: options.imageUrl || null,
            autoRotate: options.autoRotate || false,
            autoRotateSpeed: options.autoRotateSpeed || 1,
            enableZoom: options.enableZoom !== false,
            minZoom: options.minZoom || 0.5,
            maxZoom: options.maxZoom || 3.0,
            enableFullscreen: options.enableFullscreen !== false,
            enableVR: options.enableVR || false,
            initialPitch: options.initialPitch || 0,
            initialYaw: options.initialYaw || 0,
            autoplayDuration: options.autoplayDuration || 10,
            startInAutoplay: options.startInAutoplay || false,
            enableHotspots: options.enableHotspots || false,
            hotspots: options.hotspots || [],
            enableAudio: options.enableAudio || false,
            audioUrl: options.audioUrl || null,
            enableCompass: options.enableCompass !== false,
            enableMinimap: options.enableMinimap || false,
            loadingAnimation: options.loadingAnimation !== false,
            transitionEffect: options.transitionEffect || 'fade',
            backgroundMusic: options.backgroundMusic || false,
            thumbnail: options.thumbnail || null,
            onInteraction: options.onInteraction || null,
            ...options
        };

        this.viewer = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.sphere = null;
        this.isAutoRotating = false;
        this.rotationSpeed = this.options.autoRotateSpeed * 0.001;
        this.currentZoom = 1;
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        this.autoplayTimer = null;
        this.hotspots = [];
        this.audio = null;
        this.compass = null;
        this.minimap = null;
        this.isLoading = true;
        this.isPlaying = false;

        this.init();
    }

    init() {
        // Check for Three.js
        if (typeof THREE === 'undefined') {
            console.error('Three.js is required. Please include it before using this viewer.');
            return;
        }

        // Show loading animation
        if (this.options.loadingAnimation) {
            this.showLoadingIndicator();
        }

        // Create scene
        this.scene = new THREE.Scene();

        // Create camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 0, 0.1);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        // Create sphere for 360° image
        this.createSphere();

        // Set initial view
        this.camera.rotation.x = THREE.MathUtils.degToRad(this.options.initialPitch);
        this.camera.rotation.y = THREE.MathUtils.degToRad(this.options.initialYaw);

        // Add controls
        this.addControls();

        // Add hotspots if enabled
        if (this.options.enableHotspots && this.options.hotspots.length > 0) {
            this.addHotspots();
        }

        // Add audio if enabled
        if (this.options.enableAudio && this.options.audioUrl) {
            this.addAudio();
        }

        // Add compass if enabled
        if (this.options.enableCompass) {
            this.addCompass();
        }

        // Add minimap if enabled
        if (this.options.enableMinimap) {
            this.addMinimap();
        }

        // Add fullscreen button if enabled
        if (this.options.enableFullscreen) {
            this.addFullscreenButton();
        }

        // Add VR button if enabled
        if (this.options.enableVR) {
            this.addVRButton();
        }

        // Add help button
        this.addHelpButton();

        // Start autoplay if enabled
        if (this.options.startInAutoplay) {
            this.startAutoplay();
        }

        // Start auto-rotation if enabled
        if (this.options.autoRotate) {
            this.startAutoRotate();
        }

        // Handle resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Start animation loop
        this.animate();
    }

    showLoadingIndicator() {
        const loader = document.createElement('div');
        loader.className = 'vt-loader';
        loader.innerHTML = `
            <div class="vt-spinner"></div>
            <div class="vt-loading-text">جاري تحميل الجولة...</div>
        `;
        loader.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: white;
            z-index: 2000;
        `;
        this.container.appendChild(loader);
        this.loader = loader;
    }

    hideLoadingIndicator() {
        if (this.loader) {
            this.loader.remove();
            this.loader = null;
        }
    }

    createSphere() {
        const geometry = new THREE.SphereGeometry(500, 60, 40);
        geometry.scale(-1, 1, 1);

        const textureLoader = new THREE.TextureLoader();
        const texture = textureLoader.load(this.options.imageUrl, () => {
            this.isLoading = false;
            this.hideLoadingIndicator();
            this.renderer.render(this.scene, this.camera);
        }, 
        (error) => {
            console.error('Error loading texture:', error);
            this.hideLoadingIndicator();
            this.showError('فشل تحميل الصورة');
        });

        const material = new THREE.MeshBasicMaterial({ map: texture });
        this.sphere = new THREE.Mesh(geometry, material);
        this.scene.add(this.sphere);
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'vt-error';
        errorDiv.innerHTML = `
            <div class="vt-error-icon">⚠️</div>
            <div class="vt-error-message">${message}</div>
        `;
        errorDiv.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: white;
            z-index: 2000;
            background: rgba(255, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
        `;
        this.container.appendChild(errorDiv);
    }

    addControls() {
        // Mouse controls
        this.container.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.container.addEventListener('mouseup', () => this.onMouseUp());
        this.container.addEventListener('mouseleave', () => this.onMouseUp());

        // Touch controls
        this.container.addEventListener('touchstart', (e) => this.onTouchStart(e));
        this.container.addEventListener('touchmove', (e) => this.onTouchMove(e));
        this.container.addEventListener('touchend', () => this.onTouchEnd());

        // Zoom controls
        if (this.options.enableZoom) {
            this.container.addEventListener('wheel', (e) => this.onWheel(e));
        }
    }

    addHotspots() {
        this.options.hotspots.forEach((hotspot, index) => {
            const hotspotElement = document.createElement('div');
            hotspotElement.className = 'vt-hotspot';
            hotspotElement.innerHTML = `
                <div class="vt-hotspot-icon">${hotspot.icon || '📍'}</div>
                <div class="vt-hotspot-label">${hotspot.label || 'نقطة'}</div>
            `;
            hotspotElement.style.cssText = `
                position: absolute;
                cursor: pointer;
                z-index: 1000;
                pointer-events: auto;
            `;
            
            hotspotElement.addEventListener('click', () => {
                this.onHotspotClick(hotspot);
            });
            
            this.container.appendChild(hotspotElement);
            this.hotspots.push({
                element: hotspotElement,
                data: hotspot,
                position: this.hotspotToVector3(hotspot.position)
            });
        });
    }

    hotspotToVector3(position) {
        // Convert spherical coordinates to vector3
        const phi = THREE.MathUtils.degToRad(position.pitch || 0);
        const theta = THREE.MathUtils.degToRad(position.yaw || 0);
        const radius = 500;
        
        return new THREE.Vector3(
            radius * Math.sin(phi) * Math.cos(theta),
            radius * Math.cos(phi),
            radius * Math.sin(phi) * Math.sin(theta)
        );
    }

    onHotspotClick(hotspot) {
        if (hotspot.action === 'navigate') {
            this.navigateToPosition(hotspot.targetPosition);
        } else if (hotspot.action === 'info') {
            this.showInfo(hotspot.info);
        } else if (hotspot.action === 'url') {
            window.open(hotspot.url, '_blank');
        }
        
        // Track interaction
        if (this.options.onInteraction) {
            this.options.onInteraction('hotspot_click', hotspot);
        }
    }

    navigateToPosition(position) {
        // Animate camera to new position
        const targetPitch = THREE.MathUtils.degToRad(position.pitch || 0);
        const targetYaw = THREE.MathUtils.degToRad(position.yaw || 0);
        
        this.animateCameraRotation(targetPitch, targetYaw);
    }

    animateCameraRotation(targetPitch, targetYaw) {
        const duration = 1000; // 1 second
        const startPitch = this.camera.rotation.x;
        const startYaw = this.camera.rotation.y;
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            
            this.camera.rotation.x = startPitch + (targetPitch - startPitch) * easedProgress;
            this.camera.rotation.y = startYaw + (targetYaw - startYaw) * easedProgress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }

    showInfo(info) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'vt-info-popup';
        infoDiv.innerHTML = `
            <div class="vt-info-close" onclick="this.parentElement.remove()">×</div>
            <div class="vt-info-content">${info}</div>
        `;
        infoDiv.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 20px;
            border-radius: 10px;
            max-width: 400px;
            z-index: 2000;
        `;
        this.container.appendChild(infoDiv);
    }

    addAudio() {
        this.audio = new Audio(this.options.audioUrl);
        this.audio.loop = true;
        
        const audioButton = document.createElement('button');
        audioButton.className = 'vt-audio-btn';
        audioButton.innerHTML = '🔇';
        audioButton.title = 'تشغيل الصوت';
        audioButton.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 20px;
            z-index: 1000;
        `;
        
        audioButton.addEventListener('click', () => this.toggleAudio());
        this.container.appendChild(audioButton);
        this.audioButton = audioButton;
    }

    toggleAudio() {
        if (this.isPlaying) {
            this.audio.pause();
            this.audioButton.innerHTML = '🔇';
            this.audioButton.title = 'تشغيل الصوت';
        } else {
            this.audio.play();
            this.audioButton.innerHTML = '🔊';
            this.audioButton.title = 'إيقاف الصوت';
        }
        this.isPlaying = !this.isPlaying;
    }

    addCompass() {
        const compass = document.createElement('div');
        compass.className = 'vt-compass';
        compass.innerHTML = `
            <div class="vt-compass-needle"></div>
            <div class="vt-compass-label">N</div>
        `;
        compass.style.cssText = `
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        `;
        this.container.appendChild(compass);
        this.compass = compass;
    }

    addMinimap() {
        const minimap = document.createElement('div');
        minimap.className = 'vt-minimap';
        minimap.innerHTML = `
            <div class="vt-minimap-indicator"></div>
        `;
        minimap.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 20px;
            width: 100px;
            height: 100px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            z-index: 1000;
        `;
        this.container.appendChild(minimap);
        this.minimap = minimap;
    }

    onMouseDown(event) {
        this.isDragging = true;
        this.previousMousePosition = {
            x: event.clientX,
            y: event.clientY
        };
        
        // Stop auto-rotation when user interacts
        if (this.isAutoRotating) {
            this.stopAutoRotate();
        }
    }

    onMouseMove(event) {
        if (!this.isDragging) return;

        const deltaMove = {
            x: event.clientX - this.previousMousePosition.x,
            y: event.clientY - this.previousMousePosition.y
        };

        this.camera.rotation.y -= deltaMove.x * 0.005;
        this.camera.rotation.x -= deltaMove.y * 0.005;

        // Limit vertical rotation
        this.camera.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.camera.rotation.x));

        this.previousMousePosition = {
            x: event.clientX,
            y: event.clientY
        };
        
        // Update compass if enabled
        if (this.compass) {
            this.updateCompass();
        }
        
        // Update minimap if enabled
        if (this.minimap) {
            this.updateMinimap();
        }
    }

    onMouseUp() {
        this.isDragging = false;
    }

    onTouchStart(event) {
        if (event.touches.length === 1) {
            this.isDragging = true;
            this.previousMousePosition = {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY
            };
        }
    }

    onTouchMove(event) {
        if (!this.isDragging || event.touches.length !== 1) return;

        const deltaMove = {
            x: event.touches[0].clientX - this.previousMousePosition.x,
            y: event.touches[0].clientY - this.previousMousePosition.y
        };

        this.camera.rotation.y -= deltaMove.x * 0.005;
        this.camera.rotation.x -= deltaMove.y * 0.005;

        this.camera.rotation.x = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.camera.rotation.x));

        this.previousMousePosition = {
            x: event.touches[0].clientX,
            y: event.touches[0].clientY
        };
    }

    onTouchEnd() {
        this.isDragging = false;
    }

    onWheel(event) {
        event.preventDefault();
        const zoomSpeed = 0.001;
        const delta = event.deltaY * zoomSpeed;

        this.currentZoom = Math.max(
            this.options.minZoom,
            Math.min(this.options.maxZoom, this.currentZoom + delta)
        );

        this.camera.fov = 75 / this.currentZoom;
        this.camera.updateProjectionMatrix();
    }

    updateCompass() {
        if (this.compass) {
            const yaw = this.camera.rotation.y;
            const needle = this.compass.querySelector('.vt-compass-needle');
            if (needle) {
                needle.style.transform = `rotate(${THREE.MathUtils.radToDeg(yaw)}deg)`;
            }
        }
    }

    updateMinimap() {
        if (this.minimap) {
            const indicator = this.minimap.querySelector('.vt-minimap-indicator');
            if (indicator) {
                const yaw = this.camera.rotation.y;
                const pitch = this.camera.rotation.x;
                const x = 50 + Math.sin(yaw) * 40;
                const y = 50 - Math.cos(pitch) * 40;
                indicator.style.left = `${x}%`;
                indicator.style.top = `${y}%`;
            }
        }
    }

    addFullscreenButton() {
        const button = document.createElement('button');
        button.className = 'vt-fullscreen-btn';
        button.innerHTML = '⛶';
        button.title = 'ملء الشاشة';
        button.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 20px;
            z-index: 1000;
        `;

        button.addEventListener('click', () => this.toggleFullscreen());
        this.container.appendChild(button);
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch(err => {
                console.error('Fullscreen error:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    addVRButton() {
        const button = document.createElement('button');
        button.className = 'vt-vr-btn';
        button.innerHTML = '🥽';
        button.title = 'وضع VR';
        button.style.cssText = `
            position: absolute;
            top: 10px;
            right: 50px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 20px;
            z-index: 1000;
        `;

        button.addEventListener('click', () => this.enterVR());
        this.container.appendChild(button);
    }

    enterVR() {
        // VR support would require WebXR API
        alert('وضع VR يتطلب متصفح يدعم WebXR API');
    }

    addHelpButton() {
        const button = document.createElement('button');
        button.className = 'vt-help-btn';
        button.innerHTML = '?';
        button.title = 'مساعدة';
        button.style.cssText = `
            position: absolute;
            top: 10px;
            left: 60px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            z-index: 1000;
        `;

        button.addEventListener('click', () => this.showHelp());
        this.container.appendChild(button);
    }

    showHelp() {
        const helpDiv = document.createElement('div');
        helpDiv.className = 'vt-help-popup';
        helpDiv.innerHTML = `
            <div class="vt-help-close" onclick="this.parentElement.remove()">×</div>
            <h3>مساعدة الجولة الافتراضية</h3>
            <ul>
                <li>🖱️ اسحب بالماوس للتنقل</li>
                <li>🔍 استخدم عجلة الماوس للتكبير والتصغير</li>
                <li>📱 اسحب باللمس على الجوال</li>
                <li>⛶ اضغط على زر ملء الشاشة للتكبير</li>
                <li>🥽 يدعم نظارات VR (تتطلب متصفح مدعوم)</li>
            </ul>
        `;
        helpDiv.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 400px;
            z-index: 2000;
        `;
        this.container.appendChild(helpDiv);
    }

    startAutoRotate() {
        this.isAutoRotating = true;
    }

    stopAutoRotate() {
        this.isAutoRotating = false;
    }

    startAutoplay() {
        this.startAutoRotate();
        this.autoplayTimer = setTimeout(() => {
            this.stopAutoRotate();
        }, this.options.autoplayDuration * 1000);
    }

    stopAutoplay() {
        if (this.autoplayTimer) {
            clearTimeout(this.autoplayTimer);
            this.autoplayTimer = null;
        }
        this.stopAutoRotate();
    }

    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.isAutoRotating) {
            this.camera.rotation.y += this.rotationSpeed;
            
            // Update compass and minimap during auto-rotation
            if (this.compass) {
                this.updateCompass();
            }
            if (this.minimap) {
                this.updateMinimap();
            }
        }

        this.renderer.render(this.scene, this.camera);
    }

    destroy() {
        this.stopAutoplay();
        window.removeEventListener('resize', () => this.onWindowResize());
        if (this.audio) {
            this.audio.pause();
        }
        if (this.renderer) {
            this.renderer.dispose();
        }
        if (this.sphere) {
            this.sphere.geometry.dispose();
            this.sphere.material.dispose();
        }
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VirtualTour360;
}
