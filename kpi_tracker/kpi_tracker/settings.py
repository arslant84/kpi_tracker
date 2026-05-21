from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path resolution — works both in development and when frozen by PyInstaller
# ---------------------------------------------------------------------------
IS_FROZEN = getattr(sys, 'frozen', False)

if IS_FROZEN:
    # sys._MEIPASS → where PyInstaller extracted the bundle (read-only)
    # sys.executable → the .exe itself; its parent folder is writable
    BUNDLE_DIR = Path(sys._MEIPASS)
    DATA_DIR   = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR   = BUNDLE_DIR

BASE_DIR = BUNDLE_DIR

load_dotenv(DATA_DIR / '.env', override=True)

# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
SECRET_KEY = 'django-insecure-r6%#)x!zz!ury5cw)8=0cks1cdx+e=utpt9xc8u80abwrhg6fj'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:*', 'http://localhost:*']
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tasks.middleware.AutoLoginMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kpi_tracker.urls'

# ---------------------------------------------------------------------------
# Templates — explicit DIRS so Django finds them inside the frozen bundle
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'tasks' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tasks.context_processors.active_cycle',
            ],
        },
    },
]

WSGI_APPLICATION = 'kpi_tracker.wsgi.application'

# ---------------------------------------------------------------------------
# Database
# Dev mode  → db.sqlite3 in the project dir (original location, existing data)
# Frozen exe → kpi_tracker.db next to the .exe so users can find / back it up
# ---------------------------------------------------------------------------
if IS_FROZEN:
    _DB_NAME = DATA_DIR / 'kpi_tracker.db'
else:
    _DB_NAME = BUNDLE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DB_NAME,
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
#
# In frozen mode the collected assets live inside the bundle (read-only).
# Django's dev-server (DEBUG=True) serves from STATICFILES_DIRS, NOT from
# STATIC_ROOT, so we point STATICFILES_DIRS at the bundle's staticfiles dir.
# STATIC_ROOT must differ from every entry in STATICFILES_DIRS, so we park it
# in DATA_DIR (the writable folder next to the exe).
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'

if IS_FROZEN:
    STATICFILES_DIRS = [BASE_DIR / 'staticfiles']
    STATIC_ROOT      = DATA_DIR / 'staticfiles_root'
else:
    STATICFILES_DIRS = [BASE_DIR / 'static']
    STATIC_ROOT      = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/tasks/'
LOGOUT_REDIRECT_URL = '/login/'
