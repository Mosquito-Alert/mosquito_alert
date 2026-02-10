from django.utils.translation import gettext_lazy as _
import tigaserver_project as project_module
import django.conf.global_settings as DEFAULT_SETTINGS
from datetime import datetime
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import DataSource

from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin.credentials import Certificate

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

# Change this in prod
DEFAULT_TIGAUSER_PASSWORD = 'TEST_PASSWORD'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

OCEAN_GEOM = GEOSGeometry.from_ewkt(
    DataSource(PROJECT_DIR  + '/ne_10m_ocean_b8km.gpkg')[0][1].geom.ewkt
)
MIN_ALLOWED_LATITUDE = -66.5
MAX_ALLOWED_LATITUDE = 83

# Application definition


# TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
#     'django.core.context_processors.request',
# )

INSTALLED_APPS = (
    'modeltranslation', # NOTE: must be before admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework.authtoken',
    'api',
    'tigaserver_app',
    'tigacrafting',
    'rest_framework',
    'rest_framework_gis',
    'leaflet',
    'stats',
    'floppyforms',
    'taggit',
    'tigascoring',
    'drf_spectacular',
    'django.contrib.sites',
    'django_filters',
    'corsheaders',
    'simple_history',
    'imagekit',
    'django_hosts',
    'drf_standardized_errors',
    'treebeard',
    "django_lifecycle_checks",
    "admin_numeric_filter"
)

'''
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
'''
MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware'
]

CORS_ALLOWED_ORIGINS = [
    "http://webserver.mosquitoalert.com",
    "http://www.mosquitoalert.com",
    "https://app.mosquitoalert.com",
    "https://map.mosquitoalert.com",
    "https://map2.mosquitoalert.com"
]

ROOT_URLCONF = 'tigaserver_project.urls'

WSGI_APPLICATION = 'tigaserver_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        # Using defaults according to CI configuration.
        # Will be replaced when importing the settings_local
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = (
    ('es', _('Spanish')),
    ('ca', _('Catalan')),
    ('eu', _('Basque')),
    ('bn', _('Bengali')),
    ('sv', _('Swedish')),
    ('en', _('English')),
    ('de', _('German')),
    ('sq', _('Albanian')),
    ('el', _('Greek')),
    ('gl', _('Galician')),
    ('hu', _('Hungarian')),
    ('pt', _('Portuguese')),
    ('sl', _('Slovenian')),
    ('it', _('Italian')),
    ('fr', _('French')),
    ('bg', _('Bulgarian')),
    ('ro', _('Romanian')),
    ('hr', _('Croatian')),
    ('mk', _('Macedonian')),
    ('sr', _('Serbian')),
    ('lb', _('Letzeburgesch')),
    ('nl', _('Dutch')),
    ('tr', _('Turkish')),
    ('zh-cn', _('Chinese')),
)

# Django modeltranslations
MODELTRANSLATION_LANGUAGES = ('en', 'es', 'ca')

# generate locale files
# ./manage.py makemessages -l en
# ./manage.py makemessages -l ca
# ./manage.py makemessages -l es
# ./manage.py makemessages -d djangojs -l en
# ./manage.py makemessages -d djangojs -l ca
# ./manage.py makemessages -d djangojs -l es
# ./manage.py compilemessages

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

# The static web URL
STATIC_URL = 'https://webserver.mosquitoalert.com/static/'

STATIC_ROOT = ''

# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# The static web URL
MEDIA_URL = 'https://webserver.mosquitoalert.com/media/'

MEDIA_ROOT = ''

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "api.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend',]
}

DRF_STANDARDIZED_ERRORS = {
    "ALLOWED_ERROR_STATUS_CODES": ["400", "401", "403", "404", "429"],
    "ERROR_SCHEMAS": {
        "401": "api.error_serializers.ErrorResponse401Serializer"
    }
}

SIMPLE_JWT = {
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "pk",
    "USER_ID_CLAIM": "user_pk",
    "TOKEN_OBTAIN_SERIALIZER": "api.auth.serializers.AppUserTokenObtainPairSerializer",
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Mosquito Alert API',
    'DESCRIPTION': "Introducing API v1 for Mosquito Alert platform, a project desgined to facilitate citizen science initiatives and enable collaboration among scientists, public health officials, and environmental managers in the investigation and control of disease-carrying mosquitoes.",
    'VERSION': None,
    'CONTACT': {
            'name': 'Developers',
            'email': 'it@mosquitoalert.com',
            'x-role': 'responsible developer'
    },
    'LICENSE': {
        # NOTE: identifier is necessary for the openapi-generator python SDK to work.
        # If every update to openapi 3.1.0, a new field 'identifier' can be added
        'name': 'GPL-3.0-only',  # IMPORTANT: for openapi 3.0.3 must be a valid SPDX identifier. See: https://spdx.org/licenses/
        'url': 'https://github.com/Mosquito-Alert/mosquito_alert/blob/master/LICENSE.md'
    },
    'SERVERS': [
        {
            'url': 'https://api.mosquitoalert.com/v1/',
            'description': 'Production API v1'
        },
    ],
    'TOS': 'https://www.mosquitoalert.com/en/user-agreement/',
    'OAS_VERSION': '3.0.3',
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'SERVE_INCLUDE_SCHEMA': False,
    'ENUM_NAME_OVERRIDES': {
        'MosquitoTypeEnum': 'tigaserver_app.models.Report.MOSQUITO_SPECIE_CHOICES',
        'ReportTypeEnum': 'tigaserver_app.models.Report.TYPE_CHOICES',
        "DeviceTypeEnum": 'fcm_django.models.DeviceType',
        "ValidationErrorEnum": "drf_standardized_errors.openapi_serializers.ValidationErrorEnum.choices",
        "AnnotationTypeEnum": ['short', 'long'],
        "ClientErrorEnum": "drf_standardized_errors.openapi_serializers.ClientErrorEnum.choices",
        "ServerErrorEnum": "drf_standardized_errors.openapi_serializers.ServerErrorEnum.choices",
        "ErrorCode401Enum": "api.error_serializers.ErrorCode401Enum.choices",
        "ErrorCode403Enum": "drf_standardized_errors.openapi_serializers.ErrorCode403Enum.choices",
        "ErrorCode404Enum": "drf_standardized_errors.openapi_serializers.ErrorCode404Enum.choices",
        "ErrorCode405Enum": "drf_standardized_errors.openapi_serializers.ErrorCode405Enum.choices",
        "ErrorCode406Enum": "drf_standardized_errors.openapi_serializers.ErrorCode406Enum.choices",
        "ErrorCode415Enum": "drf_standardized_errors.openapi_serializers.ErrorCode415Enum.choices",
        "ErrorCode429Enum": "drf_standardized_errors.openapi_serializers.ErrorCode429Enum.choices",
        "ErrorCode500Enum": "drf_standardized_errors.openapi_serializers.ErrorCode500Enum.choices",
    },
    'POSTPROCESSING_HOOKS': [],  # NOTE: needed for the openapi-generator
    'ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE': False,  # See: https://github.com/tfranzel/drf-spectacular/issues/235
    'ENUM_GENERATE_CHOICE_DESCRIPTION': False,
    'EXTENSIONS_INFO': {
        'x-logo': {
            'altText': 'Mosquito Alert Logo',
            'backgroundColor': "#fafafa",
            'url': 'api/icons/og_logo.png'
        },
    },
    'REDOC_UI_SETTINGS': {
        'maxDisplayedEnumValues': '5',
        'sortTagsAlphabetically': True,
        'sortOperationsAlphabetically': True
    },
    'COMPONENT_SPLIT_REQUEST': True,
}

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (40.0, -4.0),
    'DEFAULT_ZOOM': 6,
    'MINIMAP': True,
}

#TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

START_TIME = datetime(2014, 6, 13, tzinfo=ZoneInfo("UTC"))

IOS_START_TIME = datetime(2014, 6, 24, tzinfo=ZoneInfo("UTC"))

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}

USERS_IN_STATS = [16, 33, 18, 17, 31, 32, 35, 34, 54, 55, 49, 130, 123, 126, 131, 129, 127, 124, 128, 125]

#Completely disables notifications for achievements/rewards
DISABLE_ACHIEVEMENT_NOTIFICATIONS = False
#Minimum package version for scoring notifications
MINIMUM_PACKAGE_VERSION_SCORING_NOTIFICATIONS = 32

# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
#every 15 minutes
CELERY_REFRESH_SCORE_FREQUENCY = '*/15'

IDENTICON_FOREGROUNDS = [ "rgb(45,79,255)",
               "rgb(254,180,44)",
               "rgb(226,121,234)",
               "rgb(30,179,253)",
               "rgb(232,77,65)",
               "rgb(49,203,115)",
               "rgb(141,69,170)" ]

# Awards stuff
# Starting year - awards are given from this year onward
AWARD_START_YEAR = 2020
# Season start - These mark the beginning of the season (Diada de Sant Jordi)
SEASON_START_MONTH = 4
SEASON_START_DAY = 23

# This email shows up for contact in case of technical issues
ENTOLAB_ADMIN = 'a.escobar@creaf.uab.cat'
SHOW_USER_AGREEMENT_ENTOLAB = False

SITE_ID = 1


# FCM Notification settings
DRY_RUN_PUSH = True
DISABLE_PUSH = True

# NOTE: paste json data here
# See: https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk?authuser=1
FIREBASE_SERVICE_ACCOUNT_CREDENTIAL = {}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'tigaserver_app.backends.AppUserBackend'
]

#django taggit
TAGGIT_CASE_INSENSITIVE=True

# For django-hsots
ROOT_HOSTCONF = 'tigaserver_project.hosts'
DEFAULT_HOST = 'webserver'

# for fcm-django
FCM_DJANGO_SETTINGS = {
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": False,
}
FCM_DJANGO_FCMDEVICE_MODEL = "tigaserver_app.Device"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Entolab
MAX_N_OF_PENDING_REPORTS = 5
MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT = 3
DEFAULT_EXPIRATION_DAYS = 14
# number of days after a report is considered blocked
ENTOLAB_LOCK_PERIOD = 14

ADDITIONAL_EMAIL_RECIPIENTS = []

try:
    from tigaserver_project.settings_local import *
except ModuleNotFoundError:
    pass

FIREBASE_APP = None
if FIREBASE_SERVICE_ACCOUNT_CREDENTIAL:
    FIREBASE_APP = firebase_admin.initialize_app(
        credential=Certificate(FIREBASE_SERVICE_ACCOUNT_CREDENTIAL)
    )

# NOTE: Since STATIC_URL might change in settings_local
# we are redifining all variables that depend on it.
SPECTACULAR_SETTINGS['EXTENSIONS_INFO']['x-logo']['url'] = STATIC_URL + SPECTACULAR_SETTINGS['EXTENSIONS_INFO']['x-logo']['url']

# Disable history reverting
SIMPLE_HISTORY_REVERT_DISABLED=True

# Mainly concerning files in media (i.e pictures). In some cases, the files have 0600 permissions, so they can't be
# opened from a internet browser. This ensures that all files in media will be world (and group) readable
FILE_UPLOAD_PERMISSIONS = 0o644
