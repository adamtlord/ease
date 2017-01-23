from .base import *

IS_PROD = True


DOMAIN_NAME = 'app.arriverides.com'
WWW_ROOT = 'https://%s/' % DOMAIN_NAME

ALLOWED_HOSTS = [
    'app.arriverides.com',
    '207.38.86.26',
    '[2605:de00:1:1:4a:14:0:44]'
]

SSH_HOSTS = 'app.arriverides.com'
STATIC_URL = '%sstatic/' % WWW_ROOT
STATIC_ROOT = '/home/easerideapp/webapps/ease_staticserve'
MEDIA_URL = '%suploads/' % WWW_ROOT
MEDIA_ROOT = '/home/easerideapp/webapps/ease_uploadsserve'

STATICFILES_DIRS = [
    '/home/easerideapp/webapps/django_app/ease/static'
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = ''
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter'
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ease',
        'USER': 'ease',
        'PASSWORD': PROD_DB_PASSWORD,
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'unix:/home/easerideapp',
    }
}
