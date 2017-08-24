from .base import *

# dev overrides
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEBUG = True
IS_DEV = True
COMPRESS = False

SECRET_KEY = 'vjne0crnziu3yp(!(_%6x#53++haump-$-$$w2j5$g0%=)$@lt'

DOMAIN_NAME = 'localhost:8000'
WWW_ROOT = 'http://%s/' % DOMAIN_NAME
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SITE_ID = 1

STATIC_URL = '/static/'
STATIC_ROOT = '{}/staticserve'.format(PROJECT_ROOT)
STATICFILES_DIRS = [
    '{}/static'.format(PROJECT_ROOT),
]
MEDIA_URL = '/uploads/'
MEDIA_ROOT = '{}/uploads'.format(PROJECT_ROOT)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": PROJECT_NAME,
        "USER": "adamlord",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

DEFAULT_FROM_EMAIL = 'no-reply@arriverides.com'
SERVER_EMAIL = 'no-reply@arriverides.com'

INTERNAL_IPS = [
    '127.0.0.1'
]
