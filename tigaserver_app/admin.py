from django.conf.urls import *
from tastypie.api import Api
from tigaserver_app.api import ReportResource, UserResource
from django.contrib import admin
admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(ReportResource())


urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),
    url(r'api/v1/doc/', include('tastypie_swagger.urls', namespace='tastypie_swagger')),
    url(r'^admin/', include(admin.site.urls)),
)

