"""
Django settings for news_project.

This consolidated settings file supports multiple deployment scenarios:
- Development with MariaDB (default - current working setup)
- Production deployment with environment variables
- Simple SQLite setup for quick testing

Environment Variables:
- DJANGO_ENV: 'development' (default), 'production', 'simple'
- DATABASE_ENGINE: 'mysql' (default), 'sqlite', 'postgresql'
- DEBUG: 'True'/'False' (auto-detected based on DJANGO_ENV)
"""

import os
from pathlib import Path

# Environment Configuration
DJANGO_ENV = os.environ.get(
    'DJANGO_ENV', 'development'
)  # development, production, simple
DEBUG_MODE = os.environ.get('DEBUG', 'auto')

# Auto-detect DEBUG based on environment if not explicitly set
if DEBUG_MODE == 'auto':
    DEBUG = DJANGO_ENV != 'production'
else:
    DEBUG = DEBUG_MODE.lower() in ('true', '1', 'yes', 'on')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
if DJANGO_ENV == 'production':
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY environment variable is required for production"
        )
else:
    # Development/testing secret key (maintains current setup)
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'django-insecure-!*qk@#76up@yc-t*-vmu-l)#n)7uyeyc7-q(!+a1v^%!3y03n$'
    )

# Allowed Hosts Configuration
if DJANGO_ENV == 'production':
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
        ALLOWED_HOSTS = ['localhost']  # Safe default
elif DJANGO_ENV == 'simple':
    ALLOWED_HOSTS = ['*']  # Allow all for simple setup
else:
    # Development (current setup)
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'news_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add WhiteNoise for production static files
if DJANGO_ENV == 'production':
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'news_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'news_app.context_processors.notifications',
                'news_app.context_processors.categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'news_project.wsgi.application'

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE_ENGINE = os.environ.get('DATABASE_ENGINE', 'mysql')

if DATABASE_ENGINE == 'sqlite' or DJANGO_ENV == 'simple':
    # SQLite Configuration (simple setup)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'database' / 'db.sqlite3',
        }
    }
elif DATABASE_ENGINE == 'postgresql':
    # PostgreSQL Configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'news_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    # MariaDB/MySQL Configuration (DEFAULT - maintains current working setup)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'news_db'),
            'USER': os.environ.get('DB_USER', 'testuser'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'test123'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
            'TEST': {
                'CHARSET': 'utf8mb4',
                'COLLATION': 'utf8mb4_unicode_ci',
            }
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'news_app.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files are served from app-level static directories
# No additional STATICFILES_DIRS needed

# Media files (user-uploaded)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/logout redirect URLs
LOGOUT_REDIRECT_URL = 'article_list'
LOGIN_REDIRECT_URL = 'article_list'

# ==========================================
# EMAIL CONFIGURATION
# ==========================================

if DJANGO_ENV == 'simple':
    # Console email backend for simple setup (no SMTP configuration needed)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # SMTP Configuration (maintains current working setup)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.mail.yahoo.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get(
        'EMAIL_HOST_USER',
        'hemjaliyadav@yahoo.com'
    )
    EMAIL_HOST_PASSWORD = os.environ.get(
        'EMAIL_HOST_PASSWORD',
        'zczehqtcmukeywvj'
    )
    DEFAULT_FROM_EMAIL = os.environ.get(
        'DEFAULT_FROM_EMAIL',
        'News Application <hemjaliyadav@yahoo.com>'
    )
    SERVER_EMAIL = os.environ.get(
        'SERVER_EMAIL',
        'hemjaliyadav@yahoo.com'
    )

# Email settings
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
EMAIL_SUBJECT_PREFIX = '[News App] '

# Base URL for email tracking (update for production)
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')

# Production environment detection
PRODUCTION = os.environ.get('DJANGO_ENV') == 'production'

# REST Framework Configuration for API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Add XML support if rest_framework_xml is installed (optional)
try:
    import importlib.util
    if importlib.util.find_spec('rest_framework_xml') is not None:
        # Type hints for mypy
        from typing import List
        renderer_classes: List[str] = (
            REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']  # type: ignore
        )
        parser_classes: List[str] = (
            REST_FRAMEWORK['DEFAULT_PARSER_CLASSES']  # type: ignore
        )
        renderer_classes.insert(
            1, 'rest_framework_xml.renderers.XMLRenderer'
        )
        parser_classes.append(
            'rest_framework_xml.parsers.XMLParser'
        )
except ImportError:
    # XML support is optional - no action needed if not installed
    pass

# Email tracking configuration - Performance optimized
EMAIL_TRACKING_ENABLED = True
EMAIL_TRACKING_PIXEL_CACHE_SECONDS = 86400  # 24 hours
EMAIL_TRACKING_READ_TIMEOUT = 300  # 5 minutes before marking as auto-read

# Performance settings
EMAIL_TRACKING_RATE_LIMIT_PIXEL = 10  # requests per minute per IP per token
EMAIL_TRACKING_RATE_LIMIT_MARK_READ = 20  # requests per minute per IP
EMAIL_TRACKING_BATCH_SIZE = 100  # batch notifications for bulk operations
EMAIL_TRACKING_SLOW_QUERY_THRESHOLD = 1.0  # seconds for slow query logging

# Cache settings for email tracking
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'email-tracking-cache',
        'TIMEOUT': 300,  # 5 minutes default
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Production email settings
EMAIL_USE_LOCALTIME = False
EMAIL_CHARSET = 'utf-8'

# Security settings for production email
if PRODUCTION or not DEBUG:
    # Production email settings
    EMAIL_SSL_KEYFILE = None
    EMAIL_SSL_CERTFILE = None
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 30  # Increased for production stability

# X (Twitter) API Configuration
# To enable automatic posting to X when articles are published:
# 1. Create a X Developer account and app at https://developer.twitter.com/
# 2. Generate API keys and bearer token
# 3. Set the X_API_KEY environment variable or uncomment and set below
X_API_KEY = os.environ.get('X_API_KEY', '')

# Facebook Graph API Configuration
# To enable automatic posting to Facebook when articles are published:
# 1. Create a Facebook App at https://developers.facebook.com/
# 2. Get a Page Access Token for your Facebook page
# 3. Set the environment variables or uncomment and set below
FACEBOOK_PAGE_ID = os.environ.get('FACEBOOK_PAGE_ID', '')
FACEBOOK_ACCESS_TOKEN = os.environ.get('FACEBOOK_ACCESS_TOKEN', '')

# Instagram API Configuration (future enhancement)
# INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', '')
# INSTAGRAM_USER_ID = os.environ.get('INSTAGRAM_USER_ID', '')

# LinkedIn API Configuration (future enhancement)
# LINKEDIN_ACCESS_TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN', '')
# LINKEDIN_COMPANY_ID = os.environ.get('LINKEDIN_COMPANY_ID', '')

# Social Media Posting Configuration
SOCIAL_MEDIA_POSTING_ENABLED = (
    os.environ.get('SOCIAL_MEDIA_POSTING_ENABLED', 'False').lower() == 'true'
)

# Social media post templates
SOCIAL_MEDIA_POST_TEMPLATES = {
    'x_twitter': {
        'max_length': 280,
        'template': '{title}\n\nBy {author}\n\n{summary}...',
    },
    'facebook': {
        'max_length': 2000,
        'template': (
            '{title}\n\nBy {author_name}\n\n{summary}\n\nRead: {article_url}'
        ),
    },
}

# Social media posting timeout settings
SOCIAL_MEDIA_REQUEST_TIMEOUT = 10  # seconds
SOCIAL_MEDIA_RETRY_ATTEMPTS = 3
SOCIAL_MEDIA_RETRY_DELAY = 2  # seconds between retries

# Development/Testing Settings for Social Media
if DEBUG:
    # In development, you can set test values here
    # X_API_KEY = 'test_x_api_key'  # Uncomment for testing
    # FACEBOOK_PAGE_ID = 'test_page_id'  # Uncomment for testing
    # FACEBOOK_ACCESS_TOKEN = 'test_access_token'  # Uncomment for testing
    pass

# Production Social Media Settings
if PRODUCTION:
    # In production, always use environment variables for security
    # Never hardcode API keys in production!
    X_API_KEY = os.environ.get('X_API_KEY') or ''
    FACEBOOK_PAGE_ID = os.environ.get('FACEBOOK_PAGE_ID') or ''
    FACEBOOK_ACCESS_TOKEN = os.environ.get('FACEBOOK_ACCESS_TOKEN') or ''

    # Enable social media posting in production only if keys are configured
    SOCIAL_MEDIA_POSTING_ENABLED = bool(
        X_API_KEY or (FACEBOOK_PAGE_ID and FACEBOOK_ACCESS_TOKEN)
    )

# Logging Configuration for email debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'email_notifications.log',
        },
    },
    'loggers': {
        'news_app.signals': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'news_app.tasks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ==========================================
# PRODUCTION SECURITY SETTINGS
# ==========================================

if DJANGO_ENV == 'production':
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # SSL settings (enable when HTTPS is configured)
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = True

# ==========================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# ==========================================

# Simple setup configurations
if DJANGO_ENV == 'simple':
    # Disable complex features for simplicity
    EMAIL_TRACKING_ENABLED = False
    SOCIAL_MEDIA_POSTING_ENABLED = False

    # Simplified static files
    STATICFILES_DIRS = [
        BASE_DIR / "news_app" / "static",
    ]

# ==========================================
# STARTUP CONFIGURATION SUMMARY
# ==========================================

# Print configuration when starting the development server
if DEBUG:
    import sys
    if 'runserver' in sys.argv:
        print("\n🚀 Django News Application - Enhanced Settings")
        print(f"📋 Environment: {DJANGO_ENV}")
        print(f"🔧 Debug Mode: {DEBUG}")
        print(f"📁 Database: {DATABASE_ENGINE.upper()}")
        if DATABASE_ENGINE == 'mysql':
            print(
                f"   └─ Host: {DATABASES['default']['HOST']}"
                f":{DATABASES['default']['PORT']}"
            )
            print(
                f"   └─ Database: {DATABASES['default']['NAME']}"
            )
        elif DATABASE_ENGINE == 'sqlite':
            print(f"   └─ File: {DATABASES['default']['NAME']}")
        print(
            f"📧 Email: {'Console' if DJANGO_ENV == 'simple' else 'SMTP'}"
        )
        SECURITY_STATUS = (
            'Enhanced' if DJANGO_ENV == 'production' else 'Development'
        )
        print(f"🔒 Security: {SECURITY_STATUS}")
        print("🌐 Server: http://127.0.0.1:8000/")
        print("✅ Ready to run!\n")

        # Environment switching help
        if DJANGO_ENV == 'development':
            print("💡 Environment Options:")
            print("   - Simple SQLite setup: set DJANGO_ENV=simple")
            print("   - Production mode: set DJANGO_ENV=production")
            print("   - PostgreSQL: set DATABASE_ENGINE=postgresql")
            print("")
