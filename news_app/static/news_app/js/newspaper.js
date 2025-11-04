// Professional News App JavaScript
// Weather API Configuration
const WEATHER_CONFIG = {
    apiKey: 'YOUR_OPENWEATHER_API_KEY', // Replace with actual API key
    city: 'Pokhara',
    country: 'NP',
    units: 'metric',
    refreshInterval: 600000 // 10 minutes
};

class WeatherWidget {
    constructor() {
        this.container = document.getElementById('weather-widget');
        this.lastUpdate = null;
        this.init();
    }

    init() {
        if (this.container) {
            this.fetchWeather();
            // Set up periodic refresh
            setInterval(() => this.fetchWeather(), WEATHER_CONFIG.refreshInterval);
        }
    }

    async fetchWeather() {
        try {
            this.showLoading();
            
            // Using a demo weather data for now since API key is not provided
            // In production, replace this with actual API call
            const weatherData = await this.getDemoWeather();
            
            this.updateWeatherDisplay(weatherData);
            this.lastUpdate = new Date();
        } catch (error) {
            console.error('Weather fetch error:', error);
            this.showError();
        }
    }

    async getDemoWeather() {
        // Demo weather data for Pokhara, Nepal
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    name: 'Pokhara',
                    main: {
                        temp: Math.floor(Math.random() * 10) + 20, // 20-30°C
                        feels_like: Math.floor(Math.random() * 10) + 22,
                        humidity: Math.floor(Math.random() * 30) + 60,
                        pressure: Math.floor(Math.random() * 20) + 1010
                    },
                    weather: [{
                        main: 'Clear',
                        description: 'clear sky',
                        icon: '01d'
                    }],
                    wind: {
                        speed: (Math.random() * 5 + 2).toFixed(1)
                    },
                    visibility: Math.floor(Math.random() * 5000) + 5000
                });
            }, 500);
        });
    }

    async getActualWeather() {
        const url = `https://api.openweathermap.org/data/2.5/weather?q=${WEATHER_CONFIG.city},${WEATHER_CONFIG.country}&appid=${WEATHER_CONFIG.apiKey}&units=${WEATHER_CONFIG.units}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Weather API request failed');
        return response.json();
    }

    showLoading() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="weather-loading">
                <div class="loading-spinner"></div>
                <div class="mt-2">Loading weather...</div>
            </div>
        `;
    }

    showError() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="weather-location">📍 Pokhara, Nepal</div>
            <div class="weather-temp">--°C</div>
            <div class="weather-desc">Weather unavailable</div>
            <div class="text-center mt-2">
                <small>Unable to fetch weather data</small>
            </div>
        `;
    }

    updateWeatherDisplay(data) {
        if (!this.container) return;

        const temp = Math.round(data.main.temp);
        const feelsLike = Math.round(data.main.feels_like);
        const description = data.weather[0].description;
        const humidity = data.main.humidity;
        const windSpeed = data.wind.speed;
        const pressure = data.main.pressure;

        // Get weather emoji based on weather condition
        const weatherEmoji = this.getWeatherEmoji(data.weather[0].main);

        this.container.innerHTML = `
            <div class="weather-location">📍 ${data.name}, Nepal</div>
            <div class="weather-temp">${weatherEmoji} ${temp}°C</div>
            <div class="weather-desc">${description}</div>
            <div class="weather-details">
                <div>💨 ${windSpeed} m/s</div>
                <div>💧 ${humidity}%</div>
                <div>🌡️ Feels like ${feelsLike}°C</div>
            </div>
            <div class="text-center mt-2">
                <small class="opacity-75">Last updated: ${new Date().toLocaleTimeString()}</small>
            </div>
        `;
    }

    getWeatherEmoji(condition) {
        const emojiMap = {
            'Clear': '☀️',
            'Clouds': '☁️',
            'Rain': '🌧️',
            'Drizzle': '🌦️',
            'Thunderstorm': '⛈️',
            'Snow': '🌨️',
            'Mist': '🌫️',
            'Fog': '🌫️',
            'Haze': '🌫️'
        };
        return emojiMap[condition] || '🌤️';
    }
}

// Breaking News Ticker
class BreakingNewsTicker {
    constructor(selector) {
        this.element = document.querySelector(selector);
        this.news = [
            "🚨 Weather Alert: Beautiful clear skies over Pokhara today",
            "📰 Latest updates from The Himalayan Times newsroom",
            "🌟 Digital edition now available with enhanced features"
        ];
        this.currentIndex = 0;
        this.init();
    }

    init() {
        if (this.element) {
            this.showNews();
            setInterval(() => this.nextNews(), 5000);
        }
    }

    showNews() {
        if (this.element) {
            const textElement = this.element.querySelector('.breaking-text');
            if (textElement) {
                textElement.textContent = this.news[this.currentIndex];
            }
        }
    }

    nextNews() {
        this.currentIndex = (this.currentIndex + 1) % this.news.length;
        this.showNews();
    }
}

// Enhanced Animations
class AnimationManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupSmoothScrolling();
    }

    setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        document.querySelectorAll('.fade-in-up').forEach(el => {
            observer.observe(el);
        });
    }

    setupHoverEffects() {
        document.querySelectorAll('.enhanced-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    }

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

// Share Functionality
class ShareManager {
    constructor() {
        this.init();
    }

    init() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.share-btn') || e.target.closest('.share-btn')) {
                e.preventDefault();
                const button = e.target.closest('.share-btn') || e.target;
                this.handleShare(button);
            }
        });
    }

    handleShare(button) {
        const platform = button.dataset.platform;
        const url = button.dataset.url || window.location.href;
        const title = button.dataset.title || document.title;
        
        let shareUrl = '';
        
        switch(platform) {
            case 'facebook':
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
                break;
            case 'twitter':
                shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`;
                break;
            case 'linkedin':
                shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
                break;
        }
        
        if (shareUrl) {
            window.open(shareUrl, '_blank', 'width=600,height=400');
        }
    }
}

// Search Enhancement
class SearchEnhancer {
    constructor() {
        this.searchInput = document.querySelector('input[name="q"]');
        this.searchForm = document.querySelector('.search-container form');
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.setupSearchSuggestions();
            this.setupSearchHistory();
        }
    }

    setupSearchSuggestions() {
        let timeout;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const query = e.target.value.trim();
                if (query.length > 2) {
                    // In a real app, you'd fetch suggestions from your API
                    this.showSuggestions(query);
                }
            }, 300);
        });
    }

    setupSearchHistory() {
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                const query = this.searchInput.value.trim();
                if (query) {
                    this.saveToHistory(query);
                }
            });
        }
    }

    showSuggestions(query) {
        // Demo suggestions - in production, fetch from API
        const suggestions = [
            'breaking news',
            'weather update',
            'local news',
            'international news',
            'sports news'
        ].filter(s => s.includes(query.toLowerCase()));
        
        // Implementation would create a dropdown with suggestions
        console.log('Suggestions for:', query, suggestions);
    }

    saveToHistory(query) {
        let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        history.unshift(query);
        history = [...new Set(history)]; // Remove duplicates
        history = history.slice(0, 10); // Keep only last 10
        localStorage.setItem('searchHistory', JSON.stringify(history));
    }
}

// Theme Manager
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeToggle();
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }

    applyTheme(theme) {
        document.body.classList.toggle('dark-theme', theme === 'dark');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🗞️ The Himalayan Times - Digital Edition Loaded');
    
    // Initialize all components
    const weather = new WeatherWidget();
    const breakingNews = new BreakingNewsTicker('.breaking-news');
    const animations = new AnimationManager();
    const shareManager = new ShareManager();
    const searchEnhancer = new SearchEnhancer();
    const themeManager = new ThemeManager();
    const imageManager = new NewsImageManager();
    
    // Initialize realistic images
    imageManager.init();
    
    // Add some dynamic behavior to the navbar
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });
    
    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Loading...';
                submitBtn.disabled = true;
                
                // Re-enable after 3 seconds (fallback)
                setTimeout(() => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });
    
    // Add dynamic timestamp updates
    function updateTimestamps() {
        document.querySelectorAll('[data-timestamp]').forEach(element => {
            const timestamp = new Date(element.dataset.timestamp);
            const now = new Date();
            const diff = now - timestamp;
            
            let timeAgo = '';
            if (diff < 60000) {
                timeAgo = 'Just now';
            } else if (diff < 3600000) {
                timeAgo = `${Math.floor(diff / 60000)} minutes ago`;
            } else if (diff < 86400000) {
                timeAgo = `${Math.floor(diff / 3600000)} hours ago`;
            } else {
                timeAgo = timestamp.toLocaleDateString();
            }
            
            element.textContent = timeAgo;
        });
    }
    
    // Update timestamps every minute
    updateTimestamps();
    setInterval(updateTimestamps, 60000);
    
    // Add progressive enhancement
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(err => {
            console.log('Service Worker registration failed:', err);
        });
    }
    
    console.log('✨ All enhancements loaded successfully!');
});

// News Image Manager for realistic placeholders
class NewsImageManager {
    constructor() {
        this.newsImages = [
            // Business & Economy
            'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=250&fit=crop&auto=format',
            
            // Technology & Innovation
            'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=400&h=250&fit=crop&auto=format',
            
            // World News & Politics
            'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=250&fit=crop&auto=format',
            
            // Environment & Nature
            'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400&h=250&fit=crop&auto=format',
            
            // Culture & Society
            'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=400&h=250&fit=crop&auto=format',
            
            // Nepal & Himalayan themes
            'https://images.unsplash.com/photo-1605538883669-825200433431?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=400&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=250&fit=crop&auto=format'
        ];
        
        this.adImages = [
            'https://images.unsplash.com/photo-1560472355-536de3962603?w=300&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=300&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&h=250&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=300&h=250&fit=crop&auto=format'
        ];
    }
    
    getRandomNewsImage() {
        const index = Math.floor(Math.random() * this.newsImages.length);
        return this.newsImages[index];
    }
    
    getRandomAdImage() {
        const index = Math.floor(Math.random() * this.adImages.length);
        return this.adImages[index];
    }
    
    replaceImageOnError(imgElement) {
        // Only replace if it's not already a newspaper source image
        if (this.isSourceImage(imgElement)) {
            // If source image failed, fall back to our Unsplash images
            imgElement.src = this.getRandomNewsImage();
            imgElement.alt = 'News article image (fallback)';
            console.log('Newspaper source image failed, using fallback:', imgElement.src);
        }
    }
    
    isSourceImage(imgElement) {
        // Check if this is a newspaper source image that should be preserved
        const src = imgElement.src;
        return !src.includes('images.unsplash.com') && 
               !src.includes('placeholder') &&
               (src.includes('media/') || src.startsWith('http'));
    }
    
    getFallbackImageForArticle(articleElement, index = 0) {
        // Provide consistent fallback images based on article position
        return this.newsImages[index % this.newsImages.length];
    }
    
    init() {
        // Only replace broken placeholder images, preserve newspaper source images
        document.querySelectorAll('img[src*="placeholder"]').forEach(img => {
            if (img.src.includes('Advertisement')) {
                img.src = this.getRandomAdImage();
                img.alt = 'Advertisement';
                console.log('Replaced placeholder ad image');
            } else {
                img.src = this.getRandomNewsImage();
                img.alt = 'News article image';
                console.log('Replaced placeholder news image');
            }
        });
        
        // Add error handling for all images with priority for source images
        document.querySelectorAll('img').forEach(img => {
            img.addEventListener('error', () => {
                if (!img.dataset.errorHandled) {
                    img.dataset.errorHandled = 'true';
                    
                    // Special handling for newspaper source images
                    if (this.isSourceImage(img)) {
                        console.log('Newspaper source image failed, applying fallback for:', img.src);
                    }
                    
                    this.replaceImageOnError(img);
                }
            });
            
            // Add loading indicator
            img.addEventListener('load', () => {
                img.classList.add('loaded');
            });
        });
        
        // Enhance article images with better fallback system
        this.enhanceArticleImages();
    }
    
    enhanceArticleImages() {
        // Find all article images and enhance them
        document.querySelectorAll('.article-item img, .card img').forEach((img, index) => {
            const article = img.closest('.article-item, .card');
            
            // Skip if this already has a source image
            if (img.dataset.hasSource === 'true') {
                return;
            }
            
            // If image is empty or placeholder, set a fallback
            if (!img.src || img.src.includes('placeholder')) {
                const fallbackImage = this.getFallbackImageForArticle(article, index);
                img.src = fallbackImage;
                img.alt = 'News article image';
                console.log(`Set fallback image for article ${index}:`, fallbackImage);
            }
        });
    }
}

// Utility functions
const utils = {
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    formatDate: function(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
};

// Export for use in other scripts
window.NewsApp = {
    WeatherWidget,
    BreakingNewsTicker,
    AnimationManager,
    ShareManager,
    SearchEnhancer,
    ThemeManager,
    NewsImageManager,
    utils
};