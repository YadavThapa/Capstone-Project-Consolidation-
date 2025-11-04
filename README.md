# 📰 The Himalayan News - Django News Application

> **Production-ready Django news platform with subscription-based content delivery, RESTful API, and automated notifications**

## 🎯 Project Overview

A comprehensive Django 5.2.7 news application featuring:
- **Multi-role authentication** (Reader, Journalist, Editor, Publisher Admin)
- **Subscription-based content filtering**  
- **RESTful API with token authentication**
- **Automated email notifications**
- **MariaDB backend with professional deployment**

## 📦 Updated Project Structure

```
News-Application/
├── backups/                  # Database & data backups
├── config/                   # Environment and config files (.env, .pylintrc, pyrightconfig.json)
├── logs/                     # Application logs
├── manage.py                 # Django management script
├── media/                    # User-uploaded files (articles, profiles)
├── news_app/                 # Main Django app
│   ├── admin.py              # Admin configuration
│   ├── admin_views.py        # Custom admin views
│   ├── api_views.py          # API endpoints
│   ├── apps.py               # AppConfig and signal registration
│   ├── context_processors.py # Template context processors
│   ├── editor_permissions.py # Editor access control
│   ├── email_tracking.py     # Email notification tracking
│   ├── forms.py              # Django forms
│   ├── management/
│   │   └── commands/         # Custom management commands
│   ├── migrations/           # Django migrations
│   ├── models.py             # Core business models
│   ├── serializers.py        # DRF serializers
│   ├── signals.py            # Signal handlers
│   ├── static/               # App-specific static files
│   ├── tasks.py              # Background tasks
│   ├── templates/            # App templates
│   ├── templatetags/         # Custom template tags
│   ├── tests_api.py          # API unit tests
│   ├── urls.py               # App URL patterns
│   ├── views.py              # Main views
│   └── __init__.py
├── news_project/             # Django project settings
│   ├── asgi.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __init__.py
├── requirements.txt          # Python dependencies
├── scripts/                  # Utility scripts
│   ├── .flake8
│   ├── .gitignore
│   ├── email_notifications.log
│   ├── start-server.bat
│   └── start-server.sh
├── staticfiles/              # Collected static assets
└── README.md                 # Project documentation
```

- The `setup` folder has been removed for safety and organization.
- All setup and migration scripts are now managed via Django management commands in `news_app/management/commands/`.
- The `email_notifications.log` file is now located in `scripts/` for easier access.
- No test/setup scripts remain outside their proper locations.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **MariaDB 12.0+** (or MySQL)
- **Windows/Mac/Linux**

### 1️⃣ Setup Environment
# or
cd ~/News-App     # Mac/Linux

# Install all required packages (no virtual environment needed)
pip install -r requirements.txt
```

### 🗄️ Step 3: Setup Database
```bash
# Create database tables
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Enter: username, email, password (remember these!)

# Add sample data (optional but recommended)
python manage.py news_admin --setup-sample-data
```

### � Step 4: Start the Website
```bash
python manage.py runserver
```

**🎉 Your news website is now running at:** http://127.0.0.1:8000/

---

## 🎯 Super Quick Setup (1-Click)

**For Windows Users**:
1. Double-click `setup-windows.bat`
2. Wait for setup to complete
3. Double-click `start-server.bat`
4. Visit http://127.0.0.1:8000/

**For Mac/Linux Users**:
```bash
chmod +x setup-unix.sh && ./setup-unix.sh
chmod +x start-server.sh && ./start-server.sh
```

---

## 🌟 What You Get

### 🏠 Website Features
- **Modern News Homepage** with categorized articles
- **18 News Categories**: Breaking News, Politics, Technology, Sports, etc.
- **User Registration & Login** system
- **Article Search** functionality
- **Publisher & Journalist** profiles
- **Subscription System** - follow your favorite publishers

### 👨‍💼 Admin Panel (at `/django-admin/`)
- **Article Management** - Create, edit, approve articles
- **User Management** - Manage all user accounts
- **Publisher Management** - Organize news sources
- **Statistics Dashboard**

### 📱 API Access
- **REST API** for mobile apps or third-party integration
- **Token Authentication** for secure access
- **Complete CRUD operations**

---

## 🔑 Default Login Credentials

**Admin Account:**
- **URL**: http://127.0.0.1:8000/django-admin/
- **Username**: `admin`
- **Password**: `Admin@2025!` (if using sample data)

**Test User Account:**
- **Username**: `hemja_test`
- **Email**: `hemjaliyadav@yahoo.com`


## 🔧 Having Issues?

### 🚨 Most Common Problems & Quick Fixes

**"python command not found"**
- Install Python 3.10+ from https://python.org
- ✅ Check "Add Python to PATH" during installation

**"pip install failed"**
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**📖 For detailed solutions**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 🎯 What Can You Do Now?

### 🌐 Explore the Website
1. **Homepage**: http://127.0.0.1:8000/
   - Browse articles by category
   - Use search functionality
   - Register as a new user

2. **Admin Panel**: http://127.0.0.1:8000/django-admin/
   - Create new articles
   - Manage users and publishers
   - View system statistics

3. **API Testing**: http://127.0.0.1:8000/api/articles/
   - Test REST API endpoints
   - Generate authentication tokens

### 📝 Create Content
1. **Login to Admin** using your superuser account
2. **Add Publishers** (news organizations)
3. **Create Articles** with categories and images
4. **Approve Articles** to make them live
5. **Manage Users** and their subscriptions

### 🔌 API Usage
```bash
# Get authentication token
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -d "username=admin&password=yourpassword"

# Use token to access API
curl -H "Authorization: Token your-token-here" \
  http://127.0.0.1:8000/api/articles/
```

---

## 📧 Email Notifications (Optional)

To enable email notifications when articles are published:

1. **Edit** `news_project/settings.py`
2. **Update email settings**:
   ```python
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-app-password'
   ```
3. **For Gmail**: Use App Passwords (not regular password)
4. **Test email**: Use the admin panel to approve an article

---

## 🚀 Advanced Features

### 🗄️ Using MariaDB/MySQL (Optional)
If you want to use a more powerful database:

1. **Install MariaDB**: https://mariadb.org/download/
2. **Create database**:
   ```sql
   CREATE DATABASE news_db;
   CREATE USER 'newsuser'@'localhost' IDENTIFIED BY 'password123';
   GRANT ALL ON news_db.* TO 'newsuser'@'localhost';
   ```
3. **Update** `news_project/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'news_db',
           'USER': 'newsuser',
           'PASSWORD': 'password123',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```
4. **Migrate**: `python manage.py migrate`

---

## 📚 Technology Stack

- **Backend**: Django 5.2.7 (Python web framework)
- **Database**: SQLite (default) or MariaDB/MySQL
- **Frontend**: Bootstrap 5 + Custom CSS
- **API**: Django REST Framework
- **Authentication**: Django Auth + Token Auth
- **Email**: SMTP integration

---

## 📞 Support

### 🆘 Still Having Issues?

1. **Check Python version**: `python --version` (needs 3.10+)
2. **Check pip version**: `pip --version`
3. **Update pip**: `python -m pip install --upgrade pip`
4. **Reinstall packages**: `pip install -r requirements.txt --force-reinstall`
5. **Read troubleshooting guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 📋 Common Commands Reference
```bash
# Start the website
python manage.py runserver

# Create admin user
python manage.py createsuperuser

# Add sample data
python manage.py news_admin --setup-sample-data

# Reset database
python manage.py flush

# Run tests
python manage.py test

# Check for issues
python manage.py check
```

---

## 🎓 Learning Resources

This project is perfect for learning:
- ✅ **Django web development**
- ✅ **Database management**
- ✅ **REST API development**
- ✅ **User authentication**
- ✅ **Email integration**
- ✅ **Frontend development**

---

## 📝 License

This project is for educational purposes and learning Django development.

---

**🎉 Happy coding! Your Django news platform is ready to use!**

*Need help? Check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide - it covers 95% of common issues.*

---

**Project Status**: ✅ Ready to run (No virtual environment needed!)  
**Last Updated**: November 3, 2025  
**Django Version**: 5.2.7  
**Python Required**: 3.10+  
**Setup Time**: 5 minutes



## 🌟 Key FeaturesA **production-ready Django 5.2.7** news application featuring advanced subscription management, automated email notifications, RESTful API with token authentication, and real-time content delivery. Successfully migrated from SQLite to **MariaDB 12.0.2** with comprehensive testing and zero data loss.



- **Multi-Role Authentication** - Reader, Journalist, Editor roles with permissions**🚀 Status**: ✅ **100% Production Ready** - All features tested and operational

- **Article Management** - Full CRUD operations with rich content editing  

- **Publisher System** - Organization and publisher management

- **REST API** - Complete API with authentication and pagination---

- **Email Integration** - Notifications and tracking system

- **Production Ready** - Professional deployment configuration## 📋 Table of Contents



## 🚀 Quick Start1. [Key Features](#-key-features)

2. [Technology Stack](#-technology-stack)

### Development Mode3. [Database Migration Success](#-database-migration-mariadb)

```bash4. [Email Notification System](#-automated-email-notifications)

# Install dependencies5. [RESTful API](#-restful-api)

pip install -r requirements.txt6. [Installation & Setup](#-installation--setup)

7. [Testing Summary](#-comprehensive-testing)

# Run database migrations8. [Documentation](#-documentation)

python manage.py migrate9. [Credentials](#-default-credentials)



### Core Functionality

### Production Mode- ✅ **User Authentication System**

```bash  - Role-based access control (Admin, Editor, Journalist, Reader)

# Complete production setup  - Secure registration and login with password hashing

python deployment/production_manager.py setup  - Profile management with image uploads

  - Permission-based content access

# Start production server (Windows)

python deployment/launch_production.py- ✅ **Advanced Subscription System**

  - Subscribe to publishers and individual journalists

# Start production server (Linux/macOS)   - Personalized content feeds based on subscriptions

python deployment/production_manager.py server  - Real-time subscription management

```  - Duplicate prevention (one email per user per article)




- **Python**: 3.12.0

## 🧪 Testing- **Package Manager**: pip

- **Version Control**: Git

```bash- **Testing**: Django TestCase, Postman

# Run comprehensive tests- **Database Client**: MariaDB Command Line

python manage.py test

### Security Features

# API-specific testing- CSRF protection

python tests/comprehensive_test_runner.py- Rate limiting (email tracking: 10 req/min)

- Token-based API authentication

# Production verification- Password hashing (PBKDF2)

python tests/final_perfect_test.py- SQL injection protection (Django ORM)

```- XSS protection



## 🔧 Configuration---



### Environment Setup## 🗄️ Database Migration (MariaDB)

Copy `.env.example` to `.env` and configure:

```env### Migration Success ✅

SECRET_KEY=your-production-secret-key

DEBUG=False**Successfully migrated from SQLite to MariaDB 12.0.2** with **zero data loss**!

DOMAIN_NAME=yourdomain.com

DB_NAME=your_database#### Verified Data After Migration:

EMAIL_HOST_USER=your_email@example.com- ✅ **30 Users** (11 Journalists, 12 Readers, 2 Editors, 4 Superusers, 1 Staff)

```- ✅ **41 Articles** (All approved and accessible)

- ✅ **23 Publishers** (All relationships intact)

### Database Options- ✅ **10 Notifications** (Email tracking preserved)

- **SQLite** (default) - Development & small deployments- ✅ **11 API Tokens** (Authentication working)

- **MySQL/MariaDB** - Production scaling- ✅ **Subscriptions** (5 publisher, 2 journalist)

- **PostgreSQL** - Advanced features- ✅ **Contact Messages** (All preserved)



## 🎯 Current Status        'PORT': '3306',

        'OPTIONS': {

✅ **Production Ready**            'charset': 'utf8mb4',

- 36 Users preserved with zero data loss            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",

- 44 Articles active and accessible        }

- 23 Publishers properly managed    }

- Complete API functionality tested}

- Professional project structure implemented```



## 🛠️ Technology Stack#### Migration Highlights:

- **Consolidated Migration**: All migrations merged into `0001_initial_consolidated.py`

- **Backend**: Django 5.2.7, Django REST Framework 3.15.0- **Migration Backup**: Original migrations preserved in `migrations_backup/`

- **Database**: SQLite/MySQL/PostgreSQL support- **Django System Check**: 0 issues found

- **Frontend**: Bootstrap 5, JavaScript ES6- **All Tests Passing**: API tests, email tests, functionality tests

- **Production**: Gunicorn, WhiteNoise, python-dotenv

- **Development**: Python 3.13+, pip package management**📄 Full Report**: See [MARIADB_MIGRATION_SUCCESS.md](./MARIADB_MIGRATION_SUCCESS.md)



## 🚀 Deployment Commands---



| Command | Purpose |## 📧 Automated Email Notifications

|---------|---------|

| `pip install -r requirements.txt` | Install dependencies |### Implementation Overview

| `python deployment/launch_production.py` | Start production server |

| `python deployment/production_manager.py setup` | Complete setup |**Django signals-based system** that automatically sends targeted email notifications when articles are approved, distinguishing between publisher and journalist subscriptions.

| `python deployment/quick_start.py` | Interactive wizard |

### Key Features:

## 📝 License- ✅ **Automatic Triggering**: Sends emails when articles are approved via Django signals

- ✅ **Smart Subscriber Detection**: Separates publisher vs journalist followers

This project is developed for educational purposes as part of a software development capstone project.- ✅ **Duplicate Prevention**: Users with both subscriptions receive only 1 email

- ✅ **Email Read Tracking**: 

---  - Tracking pixels for automatic read detection

  - Manual "Mark as Read" buttons for fallback

**🎉 Status**: Production-ready Django news platform with professional architecture and comprehensive documentation.  - UUID-based tracking tokens

  - Database persistence of read status and timestamps

**Last Updated**: November 2, 2025  - ✅ **Production SMTP**: Yahoo Mail integration with TLS

**Version**: Django 5.2.7  - ✅ **Async Processing**: Celery integration with sync fallback

**Python**: 3.13+ Compatible- ✅ **Comprehensive Logging**: All email events tracked
- ✅ **Error Handling**: Robust exception management

### Email Tracking System:

#### Automatic Tracking (Tracking Pixel):
```html
<img src="http://yourdomain.com/track-email/{uuid_token}/" 
     width="1" height="1" style="display:none;" />
```
- Loads when email is opened (if images enabled)
- Marks notification as read automatically
- Records timestamp in `email_opened_at`

#### Manual Tracking (Fallback Button):
```html
<a href="http://yourdomain.com/mark-read/{notification_id}/">
    ✓ Mark as Read
</a>
```
- Always works (no image loading required)
- Opens confirmation page
- Updates database immediately

### Email Configuration:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'hemjaliyadav@yahoo.com'
DEFAULT_FROM_EMAIL = 'News Application <hemjaliyadav@yahoo.com>'
```

### Testing:
- ✅ Live email sent to `hemjaiyadav@yahoo.com`
- ✅ Tracking pixel tested and working (HTTP 200 OK)
- ✅ Manual button tested and working (HTTP 200 OK)
- ✅ Database updates confirmed (notifications marked as read)
- ✅ Rate limiting functional (10 req/min per IP)
- ✅ Caching operational (performance optimized)

**📄 Full Guide**: See [EMAIL_TRACKING_GUIDE.md](./EMAIL_TRACKING_GUIDE.md) and [EMAIL_TRACKING_TEST_RESULTS.md](./EMAIL_TRACKING_TEST_RESULTS.md)

---

## 🔌 RESTful API

### API Endpoints

#### Authentication:
```bash
POST /api-token-auth/
# Generate authentication token
# Body: {"username": "admin", "password": "Admin@2025!"}
# Returns: {"token": "your-token-here"}
```

#### Articles:
```bash
GET /api/articles/
# List articles (filtered by user subscriptions)
# Headers: Authorization: Token {your-token}

GET /api/articles/{id}/
# Retrieve specific article

POST /api/articles/
# Create new article (requires permissions)

PUT /api/articles/{id}/
# Update article

DELETE /api/articles/{id}/
# Delete article
```

#### Publishers:
```bash
GET /api/publishers/
# List all publishers

GET /api/publishers/{id}/
# Get publisher details with articles
```

#### Subscriptions:
```bash
GET /api/subscriptions/publishers/
# List user's publisher subscriptions

POST /api/subscriptions/publishers/
# Subscribe to publisher
# Body: {"publisher_id": 5}

DELETE /api/subscriptions/publishers/{publisher_id}/
# Unsubscribe from publisher

GET /api/subscriptions/journalists/
# List user's journalist subscriptions

POST /api/subscriptions/journalists/
# Subscribe to journalist
# Body: {"journalist_id": 3}

DELETE /api/subscriptions/journalists/{journalist_id}/
# Unsubscribe from journalist
```

### API Features:
- ✅ **Token Authentication**: Secure access control
- ✅ **Subscription Filtering**: Users only see subscribed content
- ✅ **Comprehensive Error Handling**: Detailed error responses
- ✅ **Pagination Support**: Efficient data delivery
- ✅ **CORS Configuration**: Cross-origin requests supported
- ✅ **Rate Limiting**: Prevents abuse

### API Testing:

#### Unit Tests (32 tests):
```bash
python manage.py test news_app.tests_api
```
- ✅ Authentication tests
- ✅ Subscription filtering tests
- ✅ CRUD operation tests
- ✅ Error handling tests
- ✅ Permission tests

#### Postman Collection:
- **15+ automated test scenarios**
- **Built-in assertions**
- **Environment variables**
- **Token auto-management**

**📄 Testing Guide**: See [API_TESTING_SUMMARY.md](./API_TESTING_SUMMARY.md) and [Postman_Testing_Guide.md](./Postman_Testing_Guide.md)

---

## 🚀 Installation & Setup

### Prerequisites:
- Python 3.12.0+
- MariaDB 12.0.2+
- pip (Python package manager)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd New_Application_APP_Folder_Copy_second_cpy
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Key packages**:
- Django==5.2.7
- mysqlclient==2.2.8
- djangorestframework==3.15.2
- Pillow==11.1.0
- celery==5.5.0 (optional)

### Step 3: Configure MariaDB
```bash
# Start MariaDB service (as Administrator)
net start MariaDB

# Create database
"C:\Program Files\MariaDB 12.0\bin\mysql.exe" -u root -padmin123
```

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'testuser'@'localhost' IDENTIFIED BY 'test123';
GRANT ALL PRIVILEGES ON news_db.* TO 'testuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 4: Update Settings
Edit `news_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_db',
        'USER': 'testuser',
        'PASSWORD': 'test123',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Email configuration (optional - for testing)
EMAIL_HOST_USER = 'your-email@yahoo.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: Admin@2025!
```

### Step 7: Load Sample Data (Optional)
```bash
python manage.py news_admin --setup-sample-data
```

### Step 8: Start Server
```bash
python manage.py runserver
```

**Access at**: http://127.0.0.1:8000/

---

## 🧪 Comprehensive Testing

### What Was Tested:

#### 1. Database Migration ✅
- **Migration Script**: All tables created successfully
- **Data Verification**: Zero data loss confirmed
- **System Check**: Django system check passed (0 issues)
- **Manual Verification**: Browsed admin, created data, verified persistence

**Results**: 
- 30 users migrated
- 41 articles migrated
- 23 publishers migrated
- All relationships intact

#### 2. API Testing ✅
- **Unit Tests**: 32 Django test cases (100% pass rate)
- **Postman Tests**: 15+ automated scenarios (all passing)
- **Coverage Areas**:
  - Authentication and authorization
  - Subscription filtering
  - CRUD operations
  - Error handling
  - Edge cases

**Test Execution**:
```bash
# Run API unit tests
python manage.py test news_app.tests_api

# Results: 32/32 tests passed
```

#### 3. Email System Testing ✅
- **Live Email Test**: Successfully sent to hemjaiyadav@yahoo.com
- **Tracking Pixel**: HTTP 200 OK, notification marked as read
- **Manual Button**: HTTP 200 OK, confirmation page displayed
- **Database Updates**: Verified `is_read=1` and timestamps
- **Rate Limiting**: Confirmed 10 req/min limit working
- **Caching**: Verified cache hits for repeat requests

**Test Results**:
```bash
# Tracking pixel test
curl http://127.0.0.1:8000/track-email/{token}/
# Result: HTTP/1.1 200 OK, Content-Type: image/gif

# Database verification
SELECT is_read, email_opened_at FROM news_app_notification WHERE id=31;
# Result: is_read=1, email_opened_at=2025-10-30 17:07:24
```

#### 4. Web Functionality Testing ✅
- **User Registration**: New users created successfully
- **Login/Logout**: Authentication working properly
- **Article Creation**: Articles saved to MariaDB
- **Subscriptions**: Publisher/journalist subscriptions functional
- **Admin Portal**: All CRUD operations working
- **Profile Management**: Image uploads and updates working

#### 5. Security Testing ✅
- **CSRF Protection**: Verified on all forms
- **Token Authentication**: API access controlled
- **Rate Limiting**: Email tracking limited to 10/min
- **SQL Injection**: Protected by Django ORM
- **XSS Protection**: Template auto-escaping enabled

### Test Coverage Summary:
| Component | Tests | Status |
|-----------|-------|--------|
| Database Migration | Manual + Auto | ✅ Passed |
| RESTful API | 32 unit tests | ✅ 100% Pass |
| Email Notifications | Live + Automated | ✅ Working |
| Web Interface | Manual | ✅ Functional |
| Security | Automated | ✅ Protected |

---

## 📚 Documentation

### Complete Documentation Files:

1. **[MARIADB_MIGRATION_SUCCESS.md](./MARIADB_MIGRATION_SUCCESS.md)**
   - Full migration report with data verification
   - Before/after comparison
   - Technical details and commands

2. **[EMAIL_TRACKING_GUIDE.md](./EMAIL_TRACKING_GUIDE.md)**
   - How email tracking works
   - User instructions for Yahoo Mail
   - Testing procedures

3. **[EMAIL_TRACKING_TEST_RESULTS.md](./EMAIL_TRACKING_TEST_RESULTS.md)**
   - Comprehensive test results
   - Code changes documented
   - Production deployment checklist

4. **[API_TESTING_SUMMARY.md](./API_TESTING_SUMMARY.md)**
   - API implementation details
   - Endpoint documentation
   - Testing results

5. **[Postman_Testing_Guide.md](./Postman_Testing_Guide.md)**
   - Postman collection setup
   - 15+ test scenarios
   - Automated testing guide

6. **[PRODUCTION_DEPLOYMENT.md](./markdown_files/PRODUCTION_DEPLOYMENT.md)**
   - Production setup guide
   - Security configurations
   - Performance optimizations

---

## 🔑 Default Credentials

### Superuser Account:
- **Username**: `admin`
- **Password**: `Admin@2025!`
- **Email**: admin@example.com
- **Access**: Full admin portal access

### Test User:
- **Username**: `hemja_test`
- **Email**: `hemjaiyadav@yahoo.com`
- **Role**: Reader with subscriptions

### Database:
- **Database**: `news_db`
- **User**: `testuser`
- **Password**: `test123`
- **Host**: `localhost:3306`

### API Token Generation:
```bash
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -d "username=admin&password=Admin@2025!"
```

---

## 🎮 Quick Start Guide

### Start the Application:
```bash
# 1. Start MariaDB (if not running)
net start MariaDB

# 2. Navigate to project directory
cd c:\Users\hemja\OneDrive\Desktop\New Application 2 Folder-2 -V1\New_Application_APP_Folder_Copy_second_cpy

# 3. Start Django server
python manage.py runserver
```

### Access the Application:

#### Main Website:
- **Home**: http://127.0.0.1:8000/
- **Publishers**: http://127.0.0.1:8000/publishers/
- **Journalists**: http://127.0.0.1:8000/journalists/
- **About**: http://127.0.0.1:8000/about/
- **Contact**: http://127.0.0.1:8000/contact/

#### User Features:
- **Sign Up**: http://127.0.0.1:8000/signup/
- **Login**: http://127.0.0.1:8000/accounts/login/
- **Profile**: http://127.0.0.1:8000/profile/
- **Edit Profile**: http://127.0.0.1:8000/profile/edit/

#### Admin Portal:
- **Django Admin**: http://127.0.0.1:8000/django-admin/
- **Article Management**: http://127.0.0.1:8000/django-admin/news_app/article/
- **User Management**: http://127.0.0.1:8000/django-admin/news_app/customuser/
- **Publisher Management**: http://127.0.0.1:8000/django-admin/news_app/publisher/
- **Notifications**: http://127.0.0.1:8000/django-admin/news_app/notification/
- **Contact Messages**: http://127.0.0.1:8000/django-admin/news_app/contactmessage/

#### API Endpoints:
- **Token Auth**: http://127.0.0.1:8000/api-token-auth/
- **Articles API**: http://127.0.0.1:8000/api/articles/
- **Publishers API**: http://127.0.0.1:8000/api/publishers/
- **Publisher Subscriptions**: http://127.0.0.1:8000/api/subscriptions/publishers/
- **Journalist Subscriptions**: http://127.0.0.1:8000/api/subscriptions/journalists/
- **Generate Token**: http://127.0.0.1:8000/api/auth/generate-token/

---

## 📊 Project Achievements Summary

### What Was Built:
✅ **Complete News Application** with subscription-based content delivery  
✅ **RESTful API** with 32 unit tests (100% pass rate)  
✅ **Email Notification System** with tracking pixels and fallback buttons  
✅ **MariaDB Integration** with zero data loss migration  
✅ **Admin Portal** with custom workflows and permissions  
✅ **Social Media Sharing** (X/Twitter, Facebook)  
✅ **Security Features** (CSRF, rate limiting, token auth)  

### Technologies Mastered:
✅ Django 5.2.7 framework  
✅ MariaDB database administration  
✅ Django REST Framework  
✅ Django Signals for automation  
✅ Email SMTP integration  
✅ Token-based authentication  
✅ Database migrations  
✅ Unit testing and Postman testing  

### Documentation Created:
✅ 5+ comprehensive markdown files  
✅ API testing guide with Postman collection  
✅ Email tracking implementation guide  
✅ Database migration report  
✅ Production deployment guide  

---

## 🔄 Optional Features

### Celery for Async Email Processing:
```bash
# Start Celery worker (optional)
celery -A news_project worker -l info

# Without Celery, emails send synchronously (works fine)
```

### Social Media Integration:
- Share to X/Twitter: Automatic on article approval
- Share to Facebook: Manual sharing available
- Configure in Django admin per article

---

## 🛡️ Security Notes

⚠️ **For Production Deployment**:
1. Change `DEBUG = False` in settings.py
2. Update `SECRET_KEY` to a new random value
3. Change all default passwords
4. Configure ALLOWED_HOSTS
5. Enable HTTPS
6. Set up proper CORS policies
7. Use environment variables for sensitive data
8. Enable Django security middleware

---

## 🤝 Support & Troubleshooting

### Common Issues:

**MariaDB Not Starting:**
```bash
# As Administrator
net start MariaDB
```

**Module Not Found:**
```bash
pip install -r requirements.txt
```

**Migration Errors:**
```bash
python manage.py migrate --fake news_app 0001_initial_consolidated
python manage.py migrate
```

**Email Not Sending:**
- Check SMTP credentials in settings.py
- Verify Yahoo app password is correct
- Check firewall/antivirus settings

**API Token Issues:**
```bash
# Generate new token
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -d "username=admin&password=Admin@2025!"
```

---

## 📜 License

This project is for educational purposes.

---

## 👨‍💻 Author

Built as a comprehensive Django learning project demonstrating:
- Full-stack web development
- Database administration and migration
- RESTful API design and testing
- Email automation systems
- Production-ready deployment practices

---

## 🎓 Learning Outcomes

This project demonstrates proficiency in:
- ✅ Django MVT architecture
- ✅ Database design and relationships
- ✅ API development and testing
- ✅ Email system integration
- ✅ Security best practices
- ✅ Production deployment
- ✅ Comprehensive documentation

**🎉 Project Status: Complete and Production Ready!**

---

**Last Updated**: October 30, 2025  
**Django Version**: 5.2.7  
**Database**: MariaDB 12.0.2  
**Python**: 3.12.0


## key API end points

## Article Management System -- Only for Admin( Article Approval Management)
http://127.0.0.1:8000/admin/articles/

amin can see all status, pending, approved or rejected etc.

## The publisher can check multiple editors and journalists. 
for ex. http://127.0.0.1:8000/publisher/31/

## for custom user access only admin or staff can control access.(Permission)

http://127.0.0.1:8000/django-admin/

user access: admin
p/w : Admin@2025!

## Role based permission granted for user in Main Web UI0
http://127.0.0.1:8000/
admin - Can view articles and newsletters only
editor: Can view, update, delete articles and newsletters
journalist : Can create, view, update, delete articles and newsletters


## user profile
http://127.0.0.1:8000/profile/


## user's publisher  subscrition dashboard 
http://127.0.0.1:8000/publishers/


## user's Jounalist subscrition dashboard 
http://127.0.0.1:8000/journalists/


##  Journalist's role Independent/Dependent:  


## user group
http://127.0.0.1:8000/django-admin/news_app/customuser/


## Journalist independent role check for article-- click the article and you can see check mark for Is independent
http://127.0.0.1:8000/django-admin/news_app/article/?author__id__exact=23

## Journalist independent role check for newsletter-- -- click the newsletter and you can see check mark for Is independent
http://127.0.0.1:8000/django-admin/news_app/newsletter/?author__id__exact=23


## Journalist role change, reader value and vice versa
http://127.0.0.1:8000/django-admin/news_app/customuser/35/change/

## Access Control for Management Control-- Can see approved by and appproved time etc.
http://127.0.0.1:8000/django-admin/news_app/article/175/change/

---

## 🐍 Running with Python venv

1. **Clone the repository:**
   ```sh
   git clone https://github.com/YadavThapa/Capstone-Project-Consolidation-.git
   cd Capstone-Project-Consolidation-
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Set up environment variables:**
   - Copy `config/.env.example` to `config/.env` and fill in your secrets (e.g., `SECRET_KEY`, database credentials).
   - **Do not commit your `.env` file!**
5. **Apply migrations and run the server:**
   ```sh
   python manage.py migrate
   python manage.py runserver
   ```

## 🐳 Running with Docker

1. **Build the Docker image:**
   ```sh
   docker build -t capstone-news-app .
   ```
2. **Run the container:**
   ```sh
   docker run -it --rm -p 8000:8000 --env-file config/.env capstone-news-app
   ```
   - Ensure you have a valid `config/.env` file with all required secrets.

## ⚠️ Security Notice
- **Never commit secrets** (passwords, API keys, tokens) to the repository.
- Use `.env` files for secrets and ensure `.gitignore` excludes them.
- For reviewers: temporary credentials can be provided in a separate text file if needed for testing.

## 📚 Documentation
- User and developer documentation is available in the `docs/` folder. Open `docs/_build/html/index.html` in your browser after building docs with Sphinx.



