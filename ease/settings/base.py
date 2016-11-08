import os

from secret_settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_NAME = 'ease'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WSGI_APPLICATION = 'ease.wsgi.application'

TIME_ZONE = 'UTC'
USE_TZ = True
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
DEFAULT_CHARSET = 'utf-8'
ROOT_URLCONF = 'ease.urls'

DEBUG = False
IS_DEV = False
IS_STAGING = False
IS_PROD = False

COMPRESS_ENABLED = False

ENV = os.getenv('ENV')
if not ENV:
    raise Exception('Environment variable ENV is required!')

DATABASES = {}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'compressor',
    'django_common',

    'accounts',
    'common',
    'concierge',
    'marketing',
    'rides',
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

ROOT_URLCONF = 'ease.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            PROJECT_ROOT + '/templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.csrf',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',

                'django.contrib.messages.context_processors.messages',

                'django_common.context_processors.common_settings',
            ],
        },
    },
]

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Django Registration
ACCOUNT_ACTIVATION_DAYS = 7
