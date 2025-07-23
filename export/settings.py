import os
from pathlib import Path
import dj_database_url
import dotenv
dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 'your-dev-secret')
DEBUG = False

ALLOWED_HOSTS = [
    "gk-backend-c2ih.onrender.com",
    "localhost", "127.0.0.1",
    "192.168.1.7","192.168.1.10","192.168.1.8"
]

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'rest_framework', 'rest_framework_simplejwt', 'corsheaders',
    'excelFile', 'orderItem', 'asstimate', 'packing', 'client','invoice','users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',            
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'export.urls'
WSGI_APPLICATION = 'export.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("MYSQL_DATABASE", "gk_database"),
        'USER': os.getenv("MYSQL_USER", "admin"),
        'PASSWORD': os.getenv("MYSQL_PASSWORD", "Gaurav12318"),
        'HOST': os.getenv("MYSQL_HOST", "database-1.c1oq8qkgg1y0.ap-south-1.rds.amazonaws.com"),
        'PORT': os.getenv("MYSQL_PORT", "3306"),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # your templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

# STATIC settings
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS & CSRF
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "https://gk-backend-c2ih.onrender.com",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://192.168.1.6:3000", "http://192.168.1.7:3000",
    "http://192.168.1.4:3000", "http://192.168.1.10:3000",
    "http://192.168.1.8:3000", "http://192.168.172.203:3000"
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "x-csrftoken", "x-requested-with"
]

CSRF_TRUSTED_ORIGINS = [
    "https://gk-backend-c2ih.onrender.com",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://192.168.1.6:3000", "http://192.168.1.7:3000",
    "http://192.168.1.4:3000", "http://192.168.1.10:3000",
    "http://192.168.1.8:3000", "http://192.168.172.203:3000"
]

# Secure cookie settings for production
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}


AUTH_USER_MODEL = 'users.CustomUser'
