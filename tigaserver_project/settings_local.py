# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaa"

ALLOWED_HOSTS = []

#if 'RDS_DB_NAME' in os.environ:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['RDS_MY_DBNAME'],
        'USER': os.environ['RDS_MY_USERNAME'],
        'PASSWORD': os.environ['RDS_MY_PASSWORD'],
        'HOST': os.environ['RDS_HOSTNAME'],
        'PORT': os.environ['RDS_PORT'],
    }
}
#else:
#    DATABASES = {
#        'default': {
#            'ENGINE': 'django.db.backends.postgresql_psycopg2',
#            'NAME': 'tigadata',
#            'USER': 'tigadata_user',
#            'PASSWORD': 'tigadata_user',
#            'HOST': 'localhost',
#            'PORT': '',
#        }
#    }

STATIC_URL = '/static/'


STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

PHOTO_SECRET_KEY = 'bbbbbbbbbbbbbbbbbbbbbbbbbbb'

