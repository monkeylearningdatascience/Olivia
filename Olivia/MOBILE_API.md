# Mobile API Integration Guide

## Django Backend Setup

1. Install required packages:
```bash
cd "C:\Users\l.mathew\OneDrive - Al Majal Alarabi Holding\Project\Olivia\Olivia"
pip install -r requirements_mobile.txt
```

2. Update `Olivia/settings.py`:

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'api',
]
```

Add to `MIDDLEWARE` (at the top):
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... rest of middleware ...
]
```

Add at the bottom of settings.py:
```python
# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS settings for mobile app
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
```

3. Update `Olivia/urls.py` to include API routes:
```python
urlpatterns = [
    # ... existing paths ...
    path('api/', include('api.urls')),
]
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start Django server:
```bash
python manage.py runserver 0.0.0.0:8000
```

## API Endpoints

- POST `/api/auth/register/` - Register new user
- POST `/api/auth/login/` - Login and get token
- POST `/api/auth/logout/` - Logout (requires token)
- GET `/api/auth/profile/` - Get user profile (requires token)

## Testing with curl:

Register:
```bash
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"username\":\"test\",\"email\":\"test@test.com\",\"password\":\"testpass123\",\"password2\":\"testpass123\"}"
```

Login:
```bash
curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"test\",\"password\":\"testpass123\"}"
```
