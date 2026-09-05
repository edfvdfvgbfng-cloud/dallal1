/**
 * Search Autocomplete with Debounce
 * Provides intelligent search suggestions with Arabic normalization
 */

class SearchAutocomplete {
    constructor(inputSelector, options = {}) {
        this.input = document.querySelector(inputSelector);
        if (!this.input) return;

        this.options = {
            minLength: 2,
            debounceDelay: 300,
            maxSuggestions: 10,
            apiUrl: '/api/search-suggestions/',
            searchType: 'all', // all, properties, hotels, resorts, jobs
            ...options
        };

        // Adjust API URL for Django
        if (this.options.apiUrl.startsWith('/api/')) {
            this.options.apiUrl = '/properties' + this.options.apiUrl;
        }

        this.suggestionsContainer = null;
        this.debounceTimer = null;
        this.currentSuggestions = [];

        this.init();
    }

    init() {
        // Create suggestions container
        this.createSuggestionsContainer();

        // Add event listeners
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        this.input.addEventListener('blur', this.handleBlur.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));

        // Add autocomplete attribute
        this.input.setAttribute('autocomplete', 'off');
    }

    createSuggestionsContainer() {
        this.suggestionsContainer = document.createElement('div');
        this.suggestionsContainer.className = 'search-suggestions';
        this.suggestionsContainer.style.display = 'none';
        this.input.parentNode.appendChild(this.suggestionsContainer);
    }

    handleInput(e) {
        const query = e.target.value.trim();

        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Hide if query is too short
        if (query.length < this.options.minLength) {
            this.hideSuggestions();
            return;
        }

        // Debounce the search
        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(query);
        }, this.options.debounceDelay);
    }

    handleFocus() {
        const query = this.input.value.trim();
        if (query.length >= this.options.minLength && this.currentSuggestions.length > 0) {
            this.showSuggestions();
        }
    }

    handleBlur() {
        // Delay hiding to allow click on suggestions
        setTimeout(() => {
            this.hideSuggestions();
        }, 200);
    }

    handleKeydown(e) {
        if (!this.suggestionsContainer || this.suggestionsContainer.style.display === 'none') {
            return;
        }

        const suggestions = this.suggestionsContainer.querySelectorAll('.suggestion-item');
        const currentIndex = Array.from(suggestions).findIndex(s => s.classList.contains('active'));

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (currentIndex < suggestions.length - 1) {
                    suggestions[currentIndex]?.classList.remove('active');
                    suggestions[currentIndex + 1].classList.add('active');
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (currentIndex > 0) {
                    suggestions[currentIndex]?.classList.remove('active');
                    suggestions[currentIndex - 1].classList.add('active');
                }
                break;
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0) {
                    suggestions[currentIndex].click();
                }
                break;
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }

    async fetchSuggestions(query) {
        try {
            const url = new URL(this.options.apiUrl, window.location.origin);
            url.searchParams.append('q', query);
            url.searchParams.append('type', this.options.searchType);

            const response = await fetch(url);
            const data = await response.json();

            this.currentSuggestions = data.suggestions || [];
            this.renderSuggestions();
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.hideSuggestions();
        }
    }

    renderSuggestions() {
        if (this.currentSuggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        this.suggestionsContainer.innerHTML = '';

        this.currentSuggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            if (index === 0) item.classList.add('active');

            // Icon based on type
            const typeIcons = {
                property: '🏠',
                hotel: '🏨',
                resort: '🏝️',
                job: '💼'
            };

            const icon = typeIcons[suggestion.type] || '📍';

            item.innerHTML = `
                <div class="suggestion-icon">${icon}</div>
                <div class="suggestion-content">
                    <div class="suggestion-title">${this.highlightMatch(suggestion.title)}</div>
                    <div class="suggestion-meta">
                        ${suggestion.district ? `<span>${suggestion.district}</span>` : ''}
                        ${suggestion.governorate ? `<span>${suggestion.governorate}</span>` : ''}
                        ${suggestion.price ? `<span class="suggestion-price">${suggestion.price}</span>` : ''}
                    </div>
                </div>
            `;

            item.addEventListener('click', () => {
                if (suggestion.url) {
                    window.location.href = suggestion.url;
                } else {
                    this.input.value = suggestion.title;
                    this.hideSuggestions();
                    this.input.form?.submit();
                }
            });

            this.suggestionsContainer.appendChild(item);
        });

        this.showSuggestions();
    }

    highlightMatch(text, query = this.input.value) {
        if (!text || !query) return text || '';
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    showSuggestions() {
        this.suggestionsContainer.style.display = 'block';
    }

    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
    }

    destroy() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.input.removeEventListener('input', this.handleInput);
        this.input.removeEventListener('focus', this.handleFocus);
        this.input.removeEventListener('blur', this.handleBlur);
        this.input.removeEventListener('keydown', this.handleKeydown);
        this.suggestionsContainer?.remove();
    }
}

// Initialize search autocomplete on all search inputs
document.addEventListener('DOMContentLoaded', () => {
    // Main search input
    const mainSearch = new SearchAutocomplete('#search-input', {
        searchType: 'all'
    });

    // Property search
    const propertySearch = new SearchAutocomplete('.property-search-input', {
        searchType: 'properties'
    });

    // Hotel search
    const hotelSearch = new SearchAutocomplete('.hotel-search-input', {
        searchType: 'hotels'
    });

    // Resort search
    const resortSearch = new SearchAutocomplete('.resort-search-input', {
        searchType: 'resorts'
    });

    // Job search
    const jobSearch = new SearchAutocomplete('.job-search-input', {
        searchType: 'jobs'
    });
});
