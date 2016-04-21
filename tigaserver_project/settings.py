from django.utils.translation import ugettext_lazy as _
import tigaserver_project as project_module
import django.conf.global_settings as DEFAULT_SETTINGS
import pytz
from datetime import datetime
#from custom_storages import StaticStorage

"""
Django settings for tigaserver_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


PROJECT_DIR = os.path.dirname(os.path.realpath(project_module.__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

SECRET_KEY = 'h0v(25z3u9yquh+01+#%tj@7iyk*raq!-6)jwz+0ac^h2grd0@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

# Application definition


TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework.authtoken',
    'tigaserver_app',
    'tigamap',
    'tigahelp',
    'tigacrafting',
    'rest_framework',
    'leaflet',
    'south',
    'stats',
    'floppyforms',
    'storages',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tigaserver_project.urls'

WSGI_APPLICATION = 'tigaserver_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = True

LANGUAGES = (
    ('es', _('Spanish')),
    ('ca', _('Catalan')),
    ('en', _('English')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = ''

# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = '/media/'

MEDIA_ROOT = ''

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',)
}

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

# This is the cuttoff score above which a photo will be considered "crowd-validated"
CROWD_VALIDATION_CUTOFF = 0

START_TIME = pytz.utc.localize(datetime(2014, 6, 13))

IOS_START_TIME = pytz.utc.localize(datetime(2014, 6, 24))

#S3 storage cache headers
AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
  'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
  'Cache-Control': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = 'tigaserver-static-container'
AWS_ACCESS_KEY_ID = 'AKIAJGNAG3WIYJETWPUA'
AWS_SECRET_ACCESS_KEY = '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'

# Tell django-storages that when coming up with the URL for an item in S3 storage, keep
# it simple - just use this domain plus the path. (If this isn't set, things get complicated).
# This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
# We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# This is used by the `static` template tag from `static`, if you're using that. Or if anything else
# refers directly to STATIC_URL. So it's safest to always set it.
STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN

# Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
# you run `collectstatic`).
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
#SEE BELOW


STATICFILES_LOCATION = 'static'
STATICFILES_STORAGE = 'tigaserver_project.custom_storages.StaticStorage'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'tigaserver_project.custom_storages.MediaStorage'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)


LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (40.0, -4.0),
    'DEFAULT_ZOOM': 6,
    'MINIMAP': True,
    'PLUGINS': {
        'marker_cluster_yellow': {
            'css': ["%stigamap/MarkerCluster.css" % STATIC_URL, "%stigamap/MarkerCluster.tigamap_yellow.css" % STATIC_URL],
            'js': "%stigamap/leaflet.markercluster.js" % STATIC_URL,
        },
        'marker_cluster_yellow_single': {
            'css': ["%stigamap/MarkerCluster.css" % STATIC_URL, "%stigamap/MarkerCluster.tigamap_yellow_single.css" % STATIC_URL],
            'js': "%stigamap/leaflet.markercluster.js" % STATIC_URL,
        },
        'marker_cluster_blue': {
            'css': ["%stigamap/MarkerCluster.css" % STATIC_URL, "%stigamap/MarkerCluster.tigamap_blue.css" % STATIC_URL],
            'js': "%stigamap/leaflet.markercluster.js" % STATIC_URL,
        },
        'marker_cluster_blue_yellow': {
            'css': ["%stigamap/MarkerCluster.css" % STATIC_URL, "%stigamap/MarkerCluster.tigamap_blue_yellow.css" % STATIC_URL],
            'js': "%stigamap/leaflet.markercluster.js" % STATIC_URL,
        },
        'oms': {
            'css': [],
            'js': "%stigamap/oms.min.js" % STATIC_URL,
            'auto-include': True,
        }
    }
}


from settings_local import *
