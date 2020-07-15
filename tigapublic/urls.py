"""ROUTER."""
# -*- coding: utf-8 -*-
import re
from django.conf.urls import include, url
from . import views
from django.conf.urls.static import static
from django.conf import settings

"""Define regular expressions for each parameter."""
# ZOOM: Zoomlevel
# 1 or 2 decimal digits
re_zoom = re.compile(r"(?P<zoom>\d{1,2})\/?").pattern

# BOUNDS: Geographic bounding box
# Matches 4 coordinates separated by commas: lon, lat, lon, lat
# LON: Longitude

# re_lon = ("-?(?:480(?:(?:\.0{1,4})?)|"
#           "(?:[0-9]|[1-9][0-9]|1[0-7][0-9]|2[0-7][0-9]|3[0-7][0-9]|4[0-7][0-9])(?:(?:\.[0-9]{1,4})?))")
re_lon = "[-\d\.]*"
# re_lon = "[\d\.]"
# LAT: Latitude
re_lat = "-?(?:90(?:(?:\.0{1,4})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,4})?))"

re_coord = re.compile(r"(?P<lon>" + re_lon + ")/(?P<lat>" +
                      re_lat + ")\/?").pattern

re_bounds = re.compile(r"(?P<bounds>" + re_lon + "," + re_lat + ","
                       + re_lon + "," + re_lat + ")\/?").pattern

# DATERANGE:
# Matches two date parameters: dateStart and dateEnd
# DATE: Definition of a date, used for daterange.
# Either N or a date
# re_date = "N|[\d]{4}-[\d]{1,2}-[\d]{1,2}"
re_date = ("N|([0-9]{4}-?((0[13-9]|1[012])[-]?(0[1-9]|[12][0-9]|30)|"
           "(0[13578]|1[02])[-]?31|02[-]?(0[1-9]|1[0-9]|2[0-8]))|"
           "([0-9]{2}(([2468][048]|[02468][48])|[13579][26])|"
           "([13579][26]|[02468][048]|0[0-9]|1[0-6])00)[-]?02[-]?29)")
re_daterange = re.compile(r"(?P<date_start>" + re_date + ")/(?P<date_end>" +
                          re_date + ")\/?").pattern

# HASHTAG:
# Matches anything except white space and slash. Repeated one or more times.
# re_hashtag = re.compile(r"(?P<hashtag>[\w\.&@'*\(\)\$]+)\/?").pattern
re_hashtag = re.compile(r"(?P<hashtag>[^ /]+)\/?").pattern

# MUNICIPALITIES
# Matches either 'N' or a list of numeric ids.
# A list of ids matches decimal digits plus commas (,).
# Repeated one or more times.
re_municipalities = re.compile(r"(?P<municipalities>N|[\d,]+)\/?").pattern

# MYNOTIFS
# Matches only one character, which may be N, 0 or 1.
re_mynotifs = re.compile(r"(?P<mynotifs>[N|0|1])\/?").pattern

# NOTIF_TYPES
re_notiftypes = re.compile(r"(?P<notif_types>N|[,\d]+)\/?").pattern

# NUMERIC ID
re_numericid = re.compile(r"(?P<id>[0-9]+)\/?").pattern

# YEARS
re_years = re.compile(r"(?P<years>all|[,\d]+)\/?").pattern

# MONTHS
re_months = re.compile(r"(?P<months>all|[,\d]+)\/?").pattern

# ONE YEAR
re_year = re.compile(r"(?P<year>\d{4})\/?").pattern

# ONE MONTH
re_month = re.compile(r"(?P<month>\d{1,2})\/?").pattern

# CATEGORIES (LAYERS)
re_categories = re.compile(r"(?P<categories>[a-zA-Z,_]+)\/?").pattern

# MODELS vectors (tig,jap,yfv)
re_vectors = re.compile(r"(?P<vector>(tig|jap|yfv))\/?").pattern

# SPAN CCAA (01-19)
re_cc_aa = re.compile(r"(?P<ccaa>(0[123456789]|1[0123456789]))\/?").pattern

# EXCLUDED CATEGORIES (LAYERS)
re_excluded_categories = (re.compile(
        r"(?P<excluded_categories>[a-zA-Z,_]+)\/?"
    ).pattern)

re_x = re.compile(r"(?P<x>\d*)\/?").pattern
re_y = re.compile(r"(?P<y>\d*)\/?").pattern
re_z = re.compile(r"(?P<z>\d*)\/?").pattern

"""Observation's data."""
observation_urls = [
    url(r'^geojson/' + re_z + re_x + re_y + '$', views.geojson),
    # Get unfiltered data to show on map
    url(r'^observations/' + re_zoom +
        re_bounds + '$',
        views.observations),

    # Get filtered Data to Show on Map
    url(r'^observations/' + re_bounds +
        re_daterange +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.observations),

    # Get all data from one observation
    url(r'^observations/' +
        re_numericid + '$',
        views.observation),

    # Excel export
    url(r'export\.(?P<format>(xls)|(csv))$',
        views.ObservationsExportView.as_view()),

    # Report based on YEARS & MONTHS
    url(r'report/' +
        re_bounds +
        re_years +
        re_months +
        re_categories +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.observations_report),

    # Report based on DATERANGE
    url(r'report/' +
        re_bounds +
        re_daterange +
        re_categories +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.observations_report),
]

"""User management."""
user_urls = [
    # Do login
    url(r'^ajax_login/$', views.ajax_login),

    # Check if user is logged in
    url(r'^ajax_is_logged/$', views.ajax_is_logged),

    # Do logout
    url(r'^ajax_logout/$', views.ajax_logout),
]

"""Notifications."""
notif_urls = [
    # Upload image on notification form
    url(r'^notifications/imageupload/$',
        views.imageupload),

    # Get observations inside drawn polygon with YEARS+MONTHS
    # filter, to send notifications
    url(r'^notifications/intersect/' +
        re_excluded_categories +
        re_years +
        re_months +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.notifications_intersecting),

    # Get observations inside drawn polygon with DATERANGE
    # filter, to send notifications
    url(r'^notifications/intersect/' +
        re_excluded_categories +
        re_daterange +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.notifications_intersecting),

    # Get predefined notifications of logged user (appears on
    # the new notification form)
    url(r'^notifications/mypredefined/$',
        views.notifications_predefined,
        {'only_my_own': True}),

    # Get list of all predefined notifications to show on
    # client filter
    url(r'^notifications/predefined/$',
        views.notifications_predefined),

    # Manage Notifications (SAVE)
    url(r'^notifications/$',
        views.notifications),
]

"""Userfixes layer."""
ufix_urls = [
    # Get userfixes data
    url(r'userfixes/' +
        re_years +
        re_months +
        re_daterange + '$',
        views.userfixes),
]

"""Storm drain layer."""
drain_urls = [
    # Manage StormDrain Data
    url(r'^stormdrain/data/$',
        views.stormDrainData),

    # Get StormDrain data template
    url(r'^stormdrain/data/template/$',
        views.getStormDrainTemplate),

    # Manage StormDrain Configuration
    url(r'^stormdrain/setup/$',
        views.stormDrainSetup),
]

"""Epidemiology layer."""
epi_urls = [
    # Manage StormDrain Data
    url(r'^epi/data/$',
        views.epidemiologyData),

    # Get StormDrain data template
    url(r'^epi/data/template/$',
        views.getEpidemiologyTemplate),

]

"""Get municipalities geometry by region."""
ccaa_geom_urls = [
#     # Manage StormDrain Data
#     url(r'^get/geom/ccaa/' + re_cc_aa + '.geojson' + '$',
#         views.regionGeometries),
#     url(r'^get/centroid/ccaa/' + re_cc_aa + '.geojson' + '$',
#         views.regionSdGeometries),
    url(r'^get/region/' + re_coord +'$', views.getSpainRegionFromCoords)
]


"""Prediction models data. Municipality scale."""
re_model_date = re.compile(r"(?P<prediction_date>" + re_date + ")\/?").pattern
prediction_models_urls = [
    # Manage StormDrain Data
    url(r'^models/vector/grid/' +
        re_vectors + '/' +
        re_year + '/' + re_month + '$',
        views.predictionModelData)
]

# """Prediction models data."""
# re_model_date = re.compile(r"(?P<prediction_date>" + re_date + ")\/?").pattern
# prediction_models_urls = [
#     # Manage StormDrain Data
#     url(r'^get/prediction/' + re_year + '/' + re_month + '$',
#         views.predictionModelData)
# ]

"""Municipalities."""
muni_urls = [
    # Municipalities auto-suggestion
    url(r'^municipalities/search/([^ /]*)\/?$',
        views.getMunicipalities),

    # GetMunicipalities by Id
    url(r'^get/municipalities/id/$',
        views.getMunicipalitiesById),
]

"""Put all patterns together."""
urlpatterns = [
    url(r'', include(observation_urls)),
    url(r'', include(user_urls)),
    url(r'', include(notif_urls)),
    url(r'', include(drain_urls)),
    url(r'', include(epi_urls)),
    url(r'', include(muni_urls)),
    url(r'', include(ufix_urls)),
    url(r'', include(ccaa_geom_urls)),
    url(r'', include(prediction_models_urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
