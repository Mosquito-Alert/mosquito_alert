"""
Base settings to build other settings files upon.
"""
import environ
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import DataSource

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# mosquito_alert/
APPS_DIR = BASE_DIR / "mosquito_alert"

# Take environment variables from .env file
env = environ.Env(interpolate=True)
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DJANGO_DEBUG', False)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = 'UTC'
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "locale")]
# https://docs.djangoproject.com/en/dev/ref/settings/#languages
# The first will be used as default
LANGUAGES = (
    ('en', _('English')), # default
    ('es', _('Spanish')),
    ('ca', _('Catalan')),
    ('eu', _('Basque')),
    ('bn', _('Bengali')),
    ('sv', _('Swedish')),
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

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL", engine="django.contrib.gis.db.backends.postgis")}
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.AutoField" # TODO: change to BigAutoField

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'config.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'modeltranslation', # NOTE: must be before admin
    'admin_numeric_filter',
    'django.contrib.admin',
]
THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'leaflet',
    'taggit',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    'simple_history',
    'imagekit',
    'django_hosts',
    'drf_standardized_errors',
    'treebeard',
    "django_lifecycle_checks",
]
LOCAL_APPS = [
    'mosquito_alert.api',
    'mosquito_alert.awards',
    'mosquito_alert.campaigns',
    'mosquito_alert.devices',
    'mosquito_alert.fixes',
    'mosquito_alert.geo',
    'mosquito_alert.identification_tasks',
    'mosquito_alert.notifications',
    'mosquito_alert.partners',
    'mosquito_alert.reports',
    'mosquito_alert.stats',
    'mosquito_alert.taxa',
    'mosquito_alert.tigacrafting',
    'mosquito_alert.tigaserver_app',
    'mosquito_alert.users',
    'mosquito_alert.utils',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'mosquito_alert.users.backends.AppUserBackend'
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
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

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "static")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = env('DJANGO_STATIC_URL', default='/static/')
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
# STATICFILES_DIRS = [str(APPS_DIR / "static")]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(BASE_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = env('DJANGO_MEDIA_URL', default='/media/')

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(APPS_DIR / "templates")],
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

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="Mosquito Alert <noreply@mosquitoalert.com>",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="localhost")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default="")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default="")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = env.int("DJANGO_EMAIL_PORT", default=25)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=False)

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("Mosquito Alert Developers", "it@mosquitoalert.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# Celery
# ------------------------------------------------------------------------------
if USE_TZ:
    # https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ['application/json']
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = 'json'
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = 'json'

# Django modeltranslations
MODELTRANSLATION_LANGUAGES = ('en', 'es', 'ca')

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "mosquito_alert.api.v1.openapi.AutoSchema",
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

# drf-standardized-errors
# -------------------------------------------------------------------------------
DRF_STANDARDIZED_ERRORS = {
    "ALLOWED_ERROR_STATUS_CODES": ["400", "401", "403", "404", "429"],
    "ERROR_SCHEMAS": {
        "401": "mosquito_alert.api.v1.error_serializers.ErrorResponse401Serializer"
    }
}

# drf-spectacular
# -------------------------------------------------------------------------------
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
        'MosquitoTypeEnum': 'mosquito_alert.reports.models.Report.MOSQUITO_SPECIE_CHOICES',
        'ReportTypeEnum': 'mosquito_alert.reports.models.Report.TYPE_CHOICES',
        "DeviceTypeEnum": 'fcm_django.models.DeviceType',
        "ValidationErrorEnum": "drf_standardized_errors.openapi_serializers.ValidationErrorEnum.choices",
        "AnnotationTypeEnum": ['short', 'long'],
        "ClientErrorEnum": "drf_standardized_errors.openapi_serializers.ClientErrorEnum.choices",
        "ServerErrorEnum": "drf_standardized_errors.openapi_serializers.ServerErrorEnum.choices",
        "ErrorCode401Enum": "mosquito_alert.api.v1.error_serializers.ErrorCode401Enum.choices",
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
            'url': STATIC_URL + 'api/icons/og_logo.png'
        },
    },
    'REDOC_UI_SETTINGS': {
        'maxDisplayedEnumValues': '5',
        'sortTagsAlphabetically': True,
        'sortOperationsAlphabetically': True,
        'theme': {
            'sidebar': {
                'width': '380px'
            },
            'logo': {
                'maxWidth': '260px',
            }
        }
    },
    'COMPONENT_SPLIT_REQUEST': True,
}

# djangorestframework-simplejwt
# -------------------------------------------------------------------------------
SIMPLE_JWT = {
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "pk",
    "USER_ID_CLAIM": "user_pk",
    "TOKEN_OBTAIN_SERIALIZER": "mosquito_alert.api.v1.auth.serializers.AppUserTokenObtainPairSerializer",
}

# django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
# -------------------------------------------------------------------------------
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# For django-hosts
# -------------------------------------------------------------------------------
ROOT_HOSTCONF = 'config.hosts'
DEFAULT_HOST = "root"
PARENT_HOST = PROJECT_DOMAIN = env("PROJECT_DOMAIN", default="mosquitoalert.com")
API_HOST = env("API_HOST", default="api")

# For django-simple-history
# -------------------------------------------------------------------------------
SIMPLE_HISTORY_REVERT_DISABLED=True # Disable history reverting

# For django-taggit
# -------------------------------------------------------------------------------
TAGGIT_CASE_INSENSITIVE=True

# For fcm-django
# -------------------------------------------------------------------------------
FCM_DJANGO_SETTINGS = {
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": False,
}
FCM_DJANGO_FCMDEVICE_MODEL = "mosquito_alert.devices.Device"
DISABLE_PUSH = env.bool("DISABLE_PUSH", default=True) # NOTE: This completely disables sending push notifications, independently of the FCM_DJANGO_SETTINGS. Used in dev and staging.

# mosquito_alert.reports
# -------------------------------------------------------------------------------
OCEAN_GEOM = GEOSGeometry.from_ewkt(
    DataSource(BASE_DIR  / 'config' / 'ne_10m_ocean_b8km.gpkg')[0][1].geom.ewkt
)
MIN_ALLOWED_LATITUDE = -66.5
MAX_ALLOWED_LATITUDE = 83

DISABLE_ACHIEVEMENT_NOTIFICATIONS = False # Completely disables notifications for achievements/rewards
MINIMUM_PACKAGE_VERSION_SCORING_NOTIFICATIONS = 32 # Minimum package version for scoring notifications

DEFAULT_TIGAUSER_PASSWORD = env("DEFAULT_TIGAUSER_PASSWORD", default="TEST_PASSWORD")

# Season start - These mark the beginning of the season (Diada de Sant Jordi)
SEASON_START_MONTH = 4
SEASON_START_DAY = 23

# mosquito_alert.users & mosquito_alert.identification_tasks
# -------------------------------------------------------------------------------
# Entolab
MAX_N_OF_PENDING_REPORTS = 5
MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT = 3
DEFAULT_EXPIRATION_DAYS = 14
ENTOLAB_LOCK_PERIOD = 14 # number of days after a report is considered blocked

# tigatrapp variables (legacy)
# -------------------------------------------------------------------------------
START_TIME = datetime(2014, 6, 13, tzinfo=ZoneInfo("UTC"))
IOS_START_TIME = datetime(2014, 6, 24, tzinfo=ZoneInfo("UTC"))

USERS_IN_STATS = [16, 33, 18, 17, 31, 32, 35, 34, 54, 55, 49, 130, 123, 126, 131, 129, 127, 124, 128, 125]

ENTOLAB_ADMIN = 'it@mosquitoalert.com'
SHOW_USER_AGREEMENT_ENTOLAB = False

ADDITIONAL_EMAIL_RECIPIENTS = env.list("ADDITIONAL_EMAIL_RECIPIENTS", default=[])