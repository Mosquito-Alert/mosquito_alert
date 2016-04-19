# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaa"

ALLOWED_HOSTS = []

if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'tigadata',
            'USER': 'tigadata_user',
            'PASSWORD': 'tigadata_user',
            'HOST': 'localhost',
            'PORT': '',
        }
    }

STATIC_URL = '/static/'

STATIC_ROOT = '/home/webuser/webapps/tigaserver/static/'
MEDIA_ROOT = '/home/webuser/webapps/tigaserver/media/'

PHOTO_SECRET_KEY = 'bbbbbbbbbbbbbbbbbbbbbbbbbbb'

