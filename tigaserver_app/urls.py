from django.conf.urls import patterns, url, include
from rest_framework import routers
from tigaserver_app import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'missions', views.MissionViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'configuration', views.ConfigurationViewSet)
router.register(r'all_adults', views.AdultMapViewSetAll, base_name='adult')
router.register(r'cat2_adults', views.AdultMapViewSetCatGE2, base_name='cat2_adult')
router.register(r'cat1_adults', views.AdultMapViewSetCatGE2, base_name='cat1_adult')
router.register(r'all_sites', views.SiteMapViewSetAll, base_name='site')
router.register(r'embornals', views.SiteMapViewSetEmbornals, base_name='embornal')
router.register(r'fonts', views.SiteMapViewSetFonts, base_name='font')
router.register(r'basins', views.SiteMapViewSetBasins, base_name='basin')
router.register(r'buckets', views.SiteMapViewSetBuckets, base_name='bucket')
router.register(r'wells', views.SiteMapViewSetWells, base_name='well')
router.register(r'other', views.SiteMapViewSetOther, base_name='other_site')
router.register(r'coverage', views.CoverageMapViewSet, base_name='coverage')


urlpatterns = patterns('tigaserver_app.views',
    url(r'^time_info/$', 'get_data_time_info'),
    url(r'^photos/$', 'post_photo'),
    url(r'^configuration/$', 'get_current_configuration'),
    url(r'^missions/$', 'get_new_missions'),
    url(r'^', include(router.urls)),
)