DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = 'h0v(25z3u9yquh+01+#%tj@7iyk*raq!-6)jwz+0ac^h2grd0@'

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tigadata',
        'USER': 'tigadata_user',
        'PASSWORD': 'XIEAzdwDDYJlfjVMzFz2YJIEIrYP6GfkBFUcM|xWj^nyX7imfLdsZ0NydFrTniCLz[g@KdmgvBUpQZSQnvuQqGR"Wh[ic@OU8Bbw',
        'HOST': 'localhost',
        'PORT': '',
    }
}

STATIC_URL = '/static/'

STATIC_ROOT = '/home/palmer/tigatrapp/tigaserver_project/tigaserver_app/static/'

MEDIA_ROOT = '/var/www/'

