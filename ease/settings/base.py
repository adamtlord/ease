import os

from secret_settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_NAME = 'ease'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WSGI_APPLICATION = 'ease.wsgi.application'

DEFAULT_TIMEZONE = 'America/Los_Angeles'
TIME_ZONE = DEFAULT_TIMEZONE
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
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'compressor',
    'django_common',
    'rest_framework',
    'django_filters',

    'accounts',
    'billing',
    'common',
    'concierge',
    'marketing',
    'rides',
    'webhooks'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'common.middleware.TimezoneMiddleware'
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

                'common.context_processors.global_settings'
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

# Django Registration/Accounts
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = True

GEOIP_DATABASE = PROJECT_ROOT + '/path/to/your/geoip/database/GeoLiteCity.dat'

LOGIN_REDIRECT_URL = '/profile/'
LOGIN_URL = '/login/'

TERMS_OF_SERVICE_URL = 'http://arriverides.com/terms-of-service/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'PAGE_SIZE': 10,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination'
}
