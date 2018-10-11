# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views
import re

# ZOOM: Zoomlevel
# 1 or 2 decimal digits
re_zoom = re.compile(r"(?P<zoom>\d{1,2})\/?").pattern

# BOUNDS: Geographic bounding box
# Matches 4 coordinates separated by commas: lon, lat, lon, lat
# LON: Longitude
# This solves the problem that won't show data points for very general zooms
#re_lon = "-?(?:180(?:(?:\.0{1,4})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\.[0-9]{1,4})?))"
re_lon = "[-\d\.]*"

# LAT: Latitude
re_lat = "-?(?:90(?:(?:\.0{1,4})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,4})?))"
re_bounds = re.compile(r"(?P<bounds>" + re_lon + "," + re_lat + "," + re_lon + "," + re_lat + ")\/?").pattern

# DATERANGE:
# Matches two date parameters: dateStart and dateEnd
# DATE: Definition of a date, used for daterange.
# Either N or a date
# re_date = "N|[\d]{4}-[\d]{1,2}-[\d]{1,2}"
re_date = "N|([0-9]{4}-?((0[13-9]|1[012])[-]?(0[1-9]|[12][0-9]|30)|(0[13578]|1[02])[-]?31|02[-]?(0[1-9]|1[0-9]|2[0-8]))|([0-9]{2}(([2468][048]|[02468][48])|[13579][26])|([13579][26]|[02468][048]|0[0-9]|1[0-6])00)[-]?02[-]?29)"
re_daterange = re.compile(r"(?P<dateStart>" + re_date + ")/(?P<dateEnd>" + re_date + ")\/?").pattern

# HASHTAG:
# Matches anything except white space and slash. Repeated one or more times.
# re_hashtag = re.compile(r"(?P<hashtag>[\w\.&@'*\(\)\$]+)\/?").pattern
re_hashtag = re.compile(r"(?P<hashtag>[^ /]+)\/?").pattern

# MUNICIPALITIES
# Matches either 'N' or a list of numeric ids.
# A list of ids matches decimal digits plus commas (,), repeated one or more times.
re_municipalities = re.compile(r"(?P<municipalities>N|[\d,]+)\/?", re.I).pattern

# MYNOTIFS
# Matches only one character, which may be N, 0 or 1.
re_mynotifs = re.compile(r"(?P<mynotifs>[N|0|1])\/?").pattern

# NOTIF_TYPES
re_notiftypes = re.compile(r"(?P<notif_types>N|[,\d]+)\/?").pattern

# ID
re_numericid = re.compile(r"(?P<id>[0-9]+)\/?").pattern

# YEAR
re_years = re.compile(r"(?P<years>all|[,\d]+)\/?").pattern

# MONTH
re_months = re.compile(r"(?P<months>all|[,\d]+)\/?").pattern

urlpatterns = [
    # Excel export
    url(r'(?i)map_aux_reports_export\.(?P<format>(xls)|(csv))$',
        views.MapAuxReportsExportView.as_view()),

    #Get clustered data to show on map
    url(r'(?i)map_aux_reports_zoom_bounds/' +
        re_zoom +
        re_bounds + '$',
        views.map_aux_reports_zoom_bounds),

    url(r'(?i)map_aux_reports_bounds/' +
        re_bounds +
        re_daterange +
        re_hashtag +
        re_municipalities +
        re_mynotifs +
        re_notiftypes + '$',
        views.map_aux_reports_bounds_notifs),

    #Get unclustered data to show on map without filters
    url(r'(?i)map_aux_reports_bounds/' +
        re_bounds + '$',
        views.map_aux_reports_bounds),

    #Get all data from one observation
    url(r'(?i)map_aux_reports/' +
        re_numericid + '$',
        views.map_aux_reports),

    #Logged user functions
    url(r'^(?i)ajax_login/$', views.ajax_login),
    url(r'^(?i)ajax_is_logged/$', views.ajax_is_logged),
    url(r'^(?i)ajax_logout/$', views.ajax_logout),

    #Get userfixes data
    url(r'^userfixes/' +
        re_years +
        re_months +
        re_daterange + '$',
        views.userfixes),

    #Get data to show on reports. Params: bbox, years, months, layers, hashtag, municipalities, myNotif, predefinedNotifs
    #A. When myNotif filter is on
    #url(r'^reports/([0-9.,-]+)/(all|[0-9.,-]+)/(all|[0-9.,]+)/([a-zA-Z,_]+)/([#0-9a-zA-Z]+)/([N,0-9]*)/([0|1|2])/[nN]$', views.reports_notif),
    #B. When predefinedNotifs filter is on


    url(r'^reports/([0-9.,-]+)/(all|[0-9.,-]+)/(all|[0-9.,]+)/([a-zA-Z,_]+)/([#0-9a-zA-Z]+)/([N,0-9]*)/([0|1|2|nN])/(n|N|[0-9,]+)$', views.reports_no_daterange),

    url(r'^reports/([0-9.,-]+)/(N|[0-9]{4}-[0-9]{2}-[0-9]{2})/(N|[0-9]{4}-[0-9]{2}-[0-9]{2})/([a-zA-Z,_]+)/([#0-9a-zA-Z]+)/([N,0-9]*)/([0|1|2|nN])/(n|N|[0-9,]+)$', views.reports_daterange),

    #Save notifications
    url(r'^save_notification/$', views.save_notification),

    #Upload image on notification form
    url(r'^imageupload/$', views.imageupload),

    #Getdata inside drawn polygon, to send notifications
    #excluded_categories, years, months, hashtag, notif, notif_types
    url(r'^intersect/([a-zA-Z,_]+)/(all|[0-9.,]+)/(all|[0-9.,]+)/([a-zA-Z0-9]+)/([N,0-9]*)/(all|0|1)/(all|[0-9.,]+)/$', views.intersects_no_daterange),

    #excluded_categories, startdate, enddate, hashtag, notif, notif_types
    url(r'^intersect/([a-zA-Z,_]+)/([0-9]{4}-[0-9]{2}-[0-9]{2})/([0-9]{4}-[0-9]{2}-[0-9]{2})/([a-zA-Z0-9]+)/([N,0-9]*)/(all|0|1)/(all|[0-9.,]+)/$', views.intersects_daterange),

        #Get StormDrain to show on map
    url(r'^embornals/$', views.getStormDrainData),

    #Get StormDrain style
    url(r'^getStormDrainUserSetup/$', views.getStormDrainUserSetup),

    #Put StormDrain style
    url(r'^put/style/version/$', views.putStormDrainStyle),

    #Import StormDrain data
    url(r'^fileupload/$', views.stormDrainUpload),

    #Download StormDrain template
    url(r'^stormdrain/get/template/$', views.getStormDrainTemplate),

    #Get predefined notifications of logged user
    url(r'^getpredefinednotifications/$', views.getPredefinedNotifications),

    #Get list of all predefined notifications to show on client filter
    url(r'^getlistnotifications/$', views.getListNotifications),

    #Municipalities auto-suggestion
    #url(r'^municipalities/search/([^ /]*)\/?$', views.getMunicipalities)
    url(r'^municipalities/search/([^ /]*)\/?$', views.getMunicipalities),

    #GetMunicipalities by Id
    url(r'^get/municipalities/id/$', views.getMunicipalitiesById),

]
