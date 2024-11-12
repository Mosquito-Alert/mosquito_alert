from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'webserver', settings.ROOT_URLCONF, name='webserver'),
    host(r'(api|apidev)', 'tigaserver_project.api_urls', name='api'),
)