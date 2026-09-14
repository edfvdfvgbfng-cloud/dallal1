/**
 * User Behavior Tracking and Personalization System
 * Tracks user interactions and provides personalized recommendations
 */

class UserBehaviorTracker {
    constructor() {
        this.userPreferences = this.loadUserPreferences();
        this.viewHistory = this.loadViewHistory();
        this.savedItems = this.loadSavedItems();
        this.interactionHistory = this.loadInteractionHistory();
    }

    loadUserPreferences() {
        const stored = localStorage.getItem('userPreferences');
        return stored ? JSON.parse(stored) : {
            propertyTypes: [],
            locations: [],
            priceRange: { min: null, max: null },
            preferredFeatures: [],
            behaviorPattern: 'explorer' // explorer, focused, decisive
        };
    }

    saveUserPreferences() {
        localStorage.setItem('userPreferences', JSON.stringify(this.userPreferences));
    }

    loadViewHistory() {
        const stored = localStorage.getItem('viewHistory');
        return stored ? JSON.parse(stored) : [];
    }

    saveViewHistory() {
        localStorage.setItem('viewHistory', JSON.stringify(this.viewHistory));
    }

    loadSavedItems() {
        const stored = localStorage.getItem('savedItems');
        return stored ? JSON.parse(stored) : [];
    }

    saveSavedItems() {
        localStorage.setItem('savedItems', JSON.stringify(this.savedItems));
    }

    loadInteractionHistory() {
        const stored = localStorage.getItem('interactionHistory');
        return stored ? JSON.parse(stored) : [];
    }

    saveInteractionHistory() {
        localStorage.setItem('interactionHistory', JSON.stringify(this.interactionHistory));
    }

    trackView(item) {
        const timestamp = new Date().toISOString();
        
        // Add to view history
        this.viewHistory.unshift({
            itemId: item.id,
            itemType: item.type || 'property',
            timestamp: timestamp,
            duration: null // Will be updated when user leaves
        });

        // Keep only last 100 views
        this.viewHistory = this.viewHistory.slice(0, 100);
        this.saveViewHistory();

        // Update preferences based on view
        this.updatePreferencesFromView(item);

        // Trigger event
        document.dispatchEvent(new CustomEvent('userViewTracked', {
            detail: { item, timestamp }
        }));
    }

    trackSave(item) {
        const timestamp = new Date().toISOString();
        
        // Add to saved items
        if (!this.savedItems.find(i => i.id === item.id)) {
            this.savedItems.push({
                id: item.id,
                type: item.type || 'property',
                timestamp: timestamp
            });
            this.saveSavedItems();
        }

        // Update preferences
        this.updatePreferencesFromSave(item);

        // Track interaction
        this.trackInteraction('save', item);

        // Trigger event
        document.dispatchEvent(new CustomEvent('userSaveTracked', {
            detail: { item, timestamp }
        }));
    }

    trackShare(item, platform) {
        const timestamp = new Date().toISOString();
        
        // Track interaction
        this.trackInteraction('share', item, { platform });

        // Trigger event
        document.dispatchEvent(new CustomEvent('userShareTracked', {
            detail: { item, platform, timestamp }
        }));
    }

    trackInteraction(action, item, metadata = {}) {
        const timestamp = new Date().toISOString();
        
        this.interactionHistory.push({
            action,
            itemId: item.id,
            itemType: item.type || 'property',
            timestamp,
            metadata
        });

        // Keep only last 200 interactions
        this.interactionHistory = this.interactionHistory.slice(0, 200);
        this.saveInteractionHistory();

        // Update behavior pattern
        this.updateBehaviorPattern();
    }

    updatePreferencesFromView(item) {
        // Track property type preference
        if (item.type && !this.userPreferences.propertyTypes.includes(item.type)) {
            this.userPreferences.propertyTypes.push(item.type);
            // Keep only last 5 types
            this.userPreferences.propertyTypes = this.userPreferences.propertyTypes.slice(-5);
        }

        // Track location preference
        if (item.location || item.district) {
            const location = item.location || item.district;
            if (!this.userPreferences.locations.includes(location)) {
                this.userPreferences.locations.push(location);
                this.userPreferences.locations = this.userPreferences.locations.slice(-5);
            }
        }

        // Track price range preference
        if (item.price) {
            this.updatePriceRange(item.price);
        }

        this.saveUserPreferences();
    }

    updatePreferencesFromSave(item) {
        // Saved items have higher weight
        if (item.type) {
            // Move to front of preferences
            const index = this.userPreferences.propertyTypes.indexOf(item.type);
            if (index > -1) {
                this.userPreferences.propertyTypes.splice(index, 1);
            }
            this.userPreferences.propertyTypes.unshift(item.type);
        }

        if (item.location || item.district) {
            const location = item.location || item.district;
            const index = this.userPreferences.locations.indexOf(location);
            if (index > -1) {
                this.userPreferences.locations.splice(index, 1);
            }
            this.userPreferences.locations.unshift(location);
        }

        this.saveUserPreferences();
    }

    updatePriceRange(price) {
        const currentMin = this.userPreferences.priceRange.min;
        const currentMax = this.userPreferences.priceRange.max;

        if (currentMin === null || price < currentMin) {
            this.userPreferences.priceRange.min = price;
        }

        if (currentMax === null || price > currentMax) {
            this.userPreferences.priceRange.max = price;
        }
    }

    updateBehaviorPattern() {
        const recentInteractions = this.interactionHistory.slice(0, 20);
        
        const actionCounts = {};
        recentInteractions.forEach(interaction => {
            actionCounts[interaction.action] = (actionCounts[interaction.action] || 0) + 1;
        });

        const totalInteractions = recentInteractions.length;
        const saveRatio = (actionCounts.save || 0) / totalInteractions;
        const viewRatio = (actionCounts.view || 0) / totalInteractions;

        if (saveRatio > 0.3) {
            this.userPreferences.behaviorPattern = 'decisive';
        } else if (viewRatio > 0.7) {
            this.userPreferences.behaviorPattern = 'explorer';
        } else {
            this.userPreferences.behaviorPattern = 'focused';
        }

        this.saveUserPreferences();
    }

    getPersonalizedRecommendations(availableItems, count = 10) {
        const recommendations = [];
        const scoredItems = [];

        availableItems.forEach(item => {
            let score = 0;
            const reasons = [];

            // Score based on property type preference
            if (item.type && this.userPreferences.propertyTypes.includes(item.type)) {
                const typeIndex = this.userPreferences.propertyTypes.indexOf(item.type);
                score += (5 - typeIndex) * 0.3; // Earlier types get higher score
                reasons.push('نوع مفضل');
            }

            // Score based on location preference
            if (item.location || item.district) {
                const location = item.location || item.district;
                if (this.userPreferences.locations.includes(location)) {
                    const locationIndex = this.userPreferences.locations.indexOf(location);
                    score += (5 - locationIndex) * 0.25;
                    reasons.push('موقع مفضل');
                }
            }

            // Score based on price range
            if (item.price && this.userPreferences.priceRange.min && this.userPreferences.priceRange.max) {
                if (item.price >= this.userPreferences.priceRange.min && 
                    item.price <= this.userPreferences.priceRange.max) {
                    score += 0.4;
                    reasons.push('ضمن الميزانية');
                }
            }

            // Score based on view history
            const viewCount = this.viewHistory.filter(v => v.itemId === item.id).length;
            if (viewCount > 0) {
                score += viewCount * 0.1;
                reasons.push('تمت مشاهدته من قبل');
            }

            // Score based on saved items
            if (this.savedItems.find(i => i.id === item.id)) {
                score += 0.5;
                reasons.push('محفوظ');
            }

            // Bonus for featured items
            if (item.is_featured) {
                score += 0.2;
                reasons.push('مميز');
            }

            if (score > 0) {
                scoredItems.push({
                    item,
                    score,
                    reasons
                });
            }
        });

        // Sort by score and return top recommendations
        scoredItems.sort((a, b) => b.score - a.score);
        
        return scoredItems.slice(0, count).map(result => ({
            ...result.item,
            recommendationScore: result.score,
            recommendationReasons: result.reasons
        }));
    }

    getRecentlyViewed(count = 10) {
        // Get unique recently viewed items
        const uniqueItems = [];
        const seenIds = new Set();

        for (view of this.viewHistory) {
            if (!seenIds.has(view.itemId)) {
                seenIds.add(view.itemId);
                uniqueItems.push(view);
            }

            if (uniqueItems.length >= count) {
                break;
            }
        }

        return uniqueItems;
    }

    getBehaviorInsights() {
        const insights = {
            totalViews: this.viewHistory.length,
            totalSaves: this.savedItems.length,
            totalInteractions: this.interactionHistory.length,
            topPropertyTypes: this.getTopPropertyTypes(),
            topLocations: this.getTopLocations(),
            averageSessionDuration: this.getAverageSessionDuration(),
            behaviorPattern: this.userPreferences.behaviorPattern,
            recommendations: this.getBehaviorRecommendations()
        };

        return insights;
    }

    getTopPropertyTypes(count = 5) {
        const typeCounts = {};
        this.viewHistory.forEach(view => {
            const type = view.itemType;
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });

        return Object.entries(typeCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, count)
            .map(([type, count]) => ({ type, count }));
    }

    getTopLocations(count = 5) {
        const locationCounts = {};
        this.viewHistory.forEach(view => {
            // Extract location from item data (would need to be passed)
            const location = view.metadata?.location || 'unknown';
            locationCounts[location] = (locationCounts[location] || 0) + 1;
        });

        return Object.entries(locationCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, count)
            .map(([location, count]) => ({ location, count }));
    }

    getAverageSessionDuration() {
        // Calculate average time spent on each item
        const durations = [];
        
        for (let i = 0; i < this.viewHistory.length - 1; i++) {
            const current = new Date(this.viewHistory[i].timestamp);
            const next = new Date(this.viewHistory[i + 1].timestamp);
            const duration = (next - current) / 1000; // in seconds
            
            if (duration < 300) { // Only count sessions under 5 minutes
                durations.push(duration);
            }
        }

        if (durations.length === 0) return 0;
        
        return durations.reduce((a, b) => a + b, 0) / durations.length;
    }

    getBehaviorRecommendations() {
        const recommendations = [];

        switch (this.userPreferences.behaviorPattern) {
            case 'explorer':
                recommendations.push('أنت مكتشف! حاول استكشاف أنواع عقارات جديدة');
                recommendations.push('فعّل الفلاتر للعثور على فرص مخفية');
                break;
            case 'focused':
                recommendations.push('أنت مركز! continue looking at similar properties');
                recommendations.push('استخدم المقارنة لتضبط خيارك');
                break;
            case 'decisive':
                recommendations.push('أنت حاسم! اتصل بالدلالين بسرعة');
                recommendations.push('احجز زيارة للعقارات المفضلة');
                break;
        }

        if (this.userPreferences.propertyTypes.length > 0) {
            recommendations.push(`تفضل: ${this.userPreferences.propertyTypes.join('، ')}`);
        }

        if (this.userPreferences.locations.length > 0) {
            recommendations.push(`المناطق المفضلة: ${this.userPreferences.locations.join('، ')}`);
        }

        return recommendations;
    }

    clearHistory() {
        this.viewHistory = [];
        this.interactionHistory = [];
        this.saveViewHistory();
        this.saveInteractionHistory();
        
        document.dispatchEvent(new CustomEvent('userHistoryCleared'));
    }

    exportUserData() {
        const userData = {
            preferences: this.userPreferences,
            viewHistory: this.viewHistory,
            savedItems: this.savedItems,
            interactionHistory: this.interactionHistory,
            exportDate: new Date().toISOString()
        };

        const dataStr = JSON.stringify(userData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `user-data-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
}

// Global instance
const userBehaviorTracker = new UserBehaviorTracker();

// Auto-track page views
document.addEventListener('DOMContentLoaded', () => {
    // Track view duration when user leaves
    window.addEventListener('beforeunload', () => {
        if (userBehaviorTracker.viewHistory.length > 0) {
            const lastView = userBehaviorTracker.viewHistory[0];
            if (lastView && !lastView.duration) {
                const viewStart = new Date(lastView.timestamp);
                const duration = (new Date() - viewStart) / 1000;
                lastView.duration = duration;
                userBehaviorTracker.saveViewHistory();
            }
        }
    });
});
