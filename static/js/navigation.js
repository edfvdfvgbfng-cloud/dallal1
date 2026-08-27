/**
 * Platform Navigation Manager
 * Centralized navigation system for Dalal platform
 * Prevents broken links and ensures consistent routing
 */

(function() {
  'use strict';

  // Platform Navigation Registry
  const PlatformRoutes = {
    // Properties
    properties: {
      list: '/category/inside-iraq/',
      outside: '/properties-outside-iraq/',
      create: '/add/dynamic/',
      detail: (id) => `/property/${id}/`
    },
    
    // Hotels
    hotels: {
      list: '/hotels/',
      inside: '/category/hotels/',
      outside: '/category/hotels-outside/',
      createInside: '/hotels/create/inside-iraq/',
      createOutside: '/hotels/create/outside-iraq/',
      detail: (id) => `/hotels/${id}/`
    },
    
    // Resorts
    resorts: {
      list: '/resorts/',
      category: '/category/resorts/',
      inside: '/resorts-inside-iraq/',
      outside: '/resorts-outside-iraq/',
      createInside: '/resorts-inside-iraq/create/',
      createOutside: '/resorts-outside-iraq/create/',
      detail: (slug) => `/resorts/${slug}/`
    },
    
    // Travel
    travel: {
      list: '/travel-companies/',
      create: '/dashboard/dallal/travel-companies/create/',
      detail: (id) => `/travel-companies/${id}/`
    },
    
    // Jobs
    jobs: {
      list: '/jobs/',
      create: '/jobs/post/',
      my: '/jobs/my/',
      detail: (id) => `/jobs/${id}/`
    },

    // Services
    services: {
      list: '/services/',
      create: '/service-provider/advertisement/create/',
      detail: (id) => `/services/${id}/`
    },
    
    // Auctions
    auctions: {
      list: '/auctions/',
      create: '/broker/auctions/create/',
      detail: (id) => `/auction/${id}/`
    },
    
    // Platform
    platform: {
      home: '/',
      map: '/dashboard/map/',
      services: '/services-categories/',
      search: '/search/',
      dashboard: '/dashboard/',
      contact: '/contact/',
      about: '/about/'
    }
  };

  /**
   * Navigation Manager Class
   */
  class NavigationManager {
    constructor() {
      this.currentRoute = null;
      this.navigationHistory = [];
      this.maxHistorySize = 50;
    }

    /**
     * Navigate to a specific route
     * @param {string} category - Category name
     * @param {string} action - Action type (list, create, detail, etc.)
     * @param {string|number} id - Optional ID for detail pages
     * @param {Object} params - Optional query parameters
     */
    navigate(category, action = 'list', id = null, params = {}) {
      try {
        const routeConfig = PlatformRoutes[category];
        
        if (!routeConfig) {
          console.error(`Navigation: Category '${category}' not found in route registry`);
          this.showError('الصفحة غير متوفرة');
          return false;
        }

        let url = routeConfig[action];
        
        if (!url) {
          console.error(`Navigation: Action '${action}' not found for category '${category}'`);
          this.showError('الصفحة غير متوفرة');
          return false;
        }

        // Handle function routes (detail pages)
        if (typeof url === 'function') {
          if (!id) {
            console.error(`Navigation: ID required for detail pages`);
            this.showError('معرف العنصر مطلوب');
            return false;
          }
          url = url(id);
        }

        // Add query parameters
        if (Object.keys(params).length > 0) {
          const queryString = new URLSearchParams(params).toString();
          url += (url.includes('?') ? '&' : '?') + queryString;
        }

        // Store in history
        this.addToHistory(category, action, id, url);

        // Navigate
        window.location.href = url;
        return true;

      } catch (error) {
        console.error('Navigation error:', error);
        this.showError('حدث خطأ في التنقل');
        return false;
      }
    }

    /**
     * Navigate to property page
     */
    navigateToProperty(id, params = {}) {
      return this.navigate('properties', 'detail', id, params);
    }

    /**
     * Navigate to hotel page
     */
    navigateToHotel(id, params = {}) {
      return this.navigate('hotels', 'detail', id, params);
    }

    /**
     * Navigate to resort page
     */
    navigateToResort(slug, params = {}) {
      return this.navigate('resorts', 'detail', slug, params);
    }

    /**
     * Navigate to job page
     */
    navigateToJob(id, params = {}) {
      return this.navigate('jobs', 'detail', id, params);
    }

    /**
     * Navigate to service page
     */
    navigateToService(id, params = {}) {
      return this.navigate('services', 'detail', id, params);
    }

    /**
     * Navigate to auction page
     */
    navigateToAuction(id, params = {}) {
      return this.navigate('auctions', 'detail', id, params);
    }

    /**
     * Navigate to platform page
     */
    navigateToPlatform(page, params = {}) {
      return this.navigate('platform', page, null, params);
    }

    /**
     * Add to navigation history
     */
    addToHistory(category, action, id, url) {
      this.navigationHistory.push({
        category,
        action,
        id,
        url,
        timestamp: Date.now()
      });

      // Limit history size
      if (this.navigationHistory.length > this.maxHistorySize) {
        this.navigationHistory.shift();
      }
    }

    /**
     * Show error message and redirect to error page
     */
    showError(message) {
      console.error('Navigation Error:', message);
      
      // Redirect to error page instead of alert
      window.location.href = '/navigation-error/';
    }

    /**
     * Get URL for a route without navigating
     */
    getUrl(category, action = 'list', id = null, params = {}) {
      const routeConfig = PlatformRoutes[category];
      
      if (!routeConfig) {
        console.error(`getUrl: Category '${category}' not found`);
        return null;
      }

      let url = routeConfig[action];
      
      if (!url) {
        console.error(`getUrl: Action '${action}' not found for category '${category}'`);
        return null;
      }

      if (typeof url === 'function') {
        if (!id) return null;
        url = url(id);
      }

      if (Object.keys(params).length > 0) {
        const queryString = new URLSearchParams(params).toString();
        url += (url.includes('?') ? '&' : '?') + queryString;
      }

      return url;
    }
  }

  // Create global instance
  window.NavigationManager = new NavigationManager();

  // AI Navigation Actions
  window.AINavigationActions = {
    navigateToCategory: (category, params = {}) => {
      return window.NavigationManager.navigate(category, 'list', null, params);
    },
    
    navigateToDetail: (category, id, params = {}) => {
      return window.NavigationManager.navigate(category, 'detail', id, params);
    },
    
    navigateToCreate: (category, params = {}) => {
      return window.NavigationManager.navigate(category, 'create', null, params);
    },
    
    searchProperties: (params = {}) => {
      return window.NavigationManager.navigate('properties', 'list', null, params);
    },
    
    searchHotels: (params = {}) => {
      return window.NavigationManager.navigate('hotels', 'list', null, params);
    },
    
    searchResorts: (params = {}) => {
      return window.NavigationManager.navigate('resorts', 'list', null, params);
    },
    
    searchJobs: (params = {}) => {
      return window.NavigationManager.navigate('jobs', 'list', null, params);
    },
    
    showPlatformMap: () => {
      return window.NavigationManager.navigateToPlatform('map');
    },
    
    showServices: () => {
      return window.NavigationManager.navigateToPlatform('services');
    }
  };

  console.log('Navigation Manager initialized');

})();