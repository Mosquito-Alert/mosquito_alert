from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import mixins, GenericAPIView
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.exceptions import ParseError
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django_filters import rest_framework as filters
#import django_filters
from datetime import datetime, timedelta
import pytz
import calendar
import json
from operator import attrgetter
from tigaserver_app.serializers import NotificationSerializer, NotificationContentSerializer, UserSerializer, ReportSerializer, MissionSerializer, PhotoSerializer, FixSerializer, ConfigurationSerializer, MapDataSerializer, SiteMapSerializer, CoverageMapSerializer, CoverageMonthMapSerializer, TagSerializer, NearbyReportSerializer, ReportIdSerializer, UserAddressSerializer, TigaProfileSerializer, DetailedTigaProfileSerializer, SessionSerializer, DetailedReportSerializer, OWCampaignsSerializer, OrganizationPinsSerializer, AcknowledgedNotificationSerializer, UserSubscriptionSerializer, CoarseReportSerializer, BookMarkSerializer
from tigaserver_app.models import Notification, NotificationContent, TigaUser, Mission, Report, Photo, Fix, Configuration, CoverageArea, CoverageAreaMonth, TigaProfile, Session, ExpertReportAnnotation, OWCampaigns, OrganizationPin, SentNotification, AcknowledgedNotification, NotificationTopic, UserSubscription, EuropeCountry, Categories, ReportResponse
from tigacrafting.models import FavoritedReports, BookMark
from tigacrafting.report_queues import assign_crisis_report
from tigacrafting.views import auto_annotate, issue_notification, get_current_domain
from math import ceil
from taggit.models import Tag
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance
from tigacrafting.views import get_reports_imbornal,get_reports_unfiltered_sites_embornal,get_reports_unfiltered_sites_other,get_reports_unfiltered_adults,filter_reports,get_reports_unfiltered_adults_except_being_validated
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page
from tigacrafting.criteria import users_with_pictures,users_with_storm_drain_pictures, users_with_score, users_with_score_range, users_with_topic
from tigascoring.maUsers import smmry
from tigascoring.xp_scoring import compute_user_score_in_xp_v2
from tigaserver_app.serializers import custom_render_notification,score_label
import tigaserver_project.settings as conf
import copy
from django.db import connection
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.db.models.expressions import RawSQL
from rest_framework.parsers import JSONParser
from rest_framework.decorators import parser_classes
import time
import math

#from celery.task.schedules import crontab
#from celery.decorators import periodic_task



class ReadOnlyModelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides `retrieve`, and 'list` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class WriteOnlyModelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides`create` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ReadWriteOnlyModelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    A viewset that provides `retrieve`, 'list`, and `create` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


@api_view(['GET'])
def get_current_configuration(request):
    """
API endpoint for getting most recent app configuration created by Movelab.

**Fields**

* id: Auto-incremented primary key record ID.
* samples_per_day: Number of randomly-timed location samples to take per day.
* creation_time: Date and time when this configuration was created by MoveLab. Automatically generated when
record is saved.
    """
    if request.method == 'GET':
        current_config = Configuration.objects.order_by('creation_time').last()
        serializer = ConfigurationSerializer(current_config)
        return Response(serializer.data)


@api_view(['GET'])
def get_new_missions(request):
    """
API endpoint for getting most missions that have not yet been downloaded.

**Fields**

* id: Unique identifier of the mission. Automatically generated by server when mission created.
* title_catalan: Title of mission in Catalan.
* title_spanish: Title of mission in Spanish.
* title_english: Title of mission in English.
* short_description_catalan: Catalan text to be displayed in mission list.
* short_description_spanish: Spanish text to be displayed in mission list.
* short_description_english: English text to be displayed in mission list.
* long_description_catalan: Catalan text that fully explains mission to user.
* long_description_spanish: Spanish text that fully explains mission to user.
* long_description_english: English text that fully explains mission to user.
* help_text_catalan: Catalan text to be displayed when user taps mission help button.
* help_text_spanish: Spanish text to be displayed when user taps mission help button.
* help_text_english: English text to be displayed when user taps mission help button.
* platform: What type of device is this mission is intended for? It will be sent only to these devices.
* creation_time: Date and time mission was created by MoveLab. Automatically generated when mission saved.
* expiration_time: Optional date and time when mission should expire (if ever). Mission will no longer be displayed to users after this date-time.
* photo_mission: Should this mission allow users to attach photos to their responses? (True/False).
* url: Optional URL that wll be displayed to user for this mission. (The entire mission can consist of user going to that URL and performing some action there. For security reasons, this URL must be within a MoveLab domain.
* mission_version: Optional integer that can be used to ensure that new mission parameters that we may create in the
future do not cause problems on older versions of the app. The Android app is currently set to respond only to
missions with mission_version=1 or null.
* triggers:
    * lat_lower_bound:Optional lower-bound latitude for triggering mission to appear to user. Given in decimal degrees.
    * lat_upper_bound: Optional upper-bound latitude for triggering mission to appear to user. Given in decimal degrees.
    * lon_lower_bound: Optional lower-bound longitude for triggering mission to appear to user. Given in decimal
    degrees.
    * lon_upper_bound: Optional upper-bound longitude for triggering mission to appear to user. Given in decimal degrees.
    * time_lowerbound: Lower bound of optional time-of-day window for triggering mission. If location trigger also is specified, mission will be triggered only if user is found in that location within the window; if location is not specified, the mission will be triggered for all users who have their phones on during the time window. Given as time without date, formatted as [ISO 8601](http://www.w3.org/TR/NOTE-datetime) time string (e.g. "12:34:00") with no time zone specified (trigger is always based on local time zone of user.)
    * time_upperbound: Lower bound of optional time-of-day window for triggering mission. If location trigger also is specified, mission will be triggered only if user is found in that location within the window; if location is not specified, the mission will be triggered for all users who have their phones on during the time window. Given as time without date, formatted as [ISO 8601](http://www.w3.org/TR/NOTE-datetime) time string (e.g. "12:34:00") with no time zone specified (trigger is always based on local time zone of user.)
* items:
    * question_catalan: Question displayed to user in Catalan.
    * question_spanish: Question displayed to user in Spanish.
    * question_english: Question displayed to user in English.
    * answer_choices_catalan: Response choices, with each choice surrounded by square brackets (e.g. _[Yes][No]_).
    * answer_choices_spanish: Response choices, with each choice surrounded by square brackets (e.g. _[Yes][No]_).
    * answer_choices_english: Response choices, with each choice surrounded by square brackets (e.g. _[Yes][No]_).
    * help_text_catalan: Help text displayed to user for this item.
    * help_text_spanish: Help text displayed to user for this item.
    * help_text_english: Help text displayed to user for this item.
    * prepositioned_image_reference: Optional image displayed to user within the help message. Integer reference to image prepositioned on device.')
    * attached_image: Optional Image displayed to user within the help message. File.

**Query Parameters**

* id_gt: Returns records with id greater than the specified value. Use this for getting only those missions that have not yet been downloaded. Default is 0.
* platform: Returns records matching exactly the platform code or those with 'all' or null. Default is 'all'.
* version_lte: returns records with mission_version less than or equal to the value specified or those with
mission_version null. Defaults to 100.
    """
    if request.method == 'GET':
        these_missions = Mission.objects.filter(Q(id__gt=request.query_params.get('id_gt', 0)),
                                                Q(platform__exact=request.query_params.get('platform', 'all')) | Q(platform__isnull=True) | Q(platform__exact='all'),
                                                Q(mission_version__lte=request.query_params.get('version_lte',100)) | Q(mission_version__isnull=True)).order_by('id')
        serializer = MissionSerializer(these_missions, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def get_photo(request):
    if request.method == 'GET':
        user_id = request.query_params.get('user_id', -1)
        #get user reports by user id
        these_photos = Photo.objects.filter(report__user_id=user_id)
        serializer = PhotoSerializer(these_photos,many=True)
        return Response(serializer.data)


@api_view(['POST'])
def post_photo(request):
    """
API endpoint for uploading photos associated with a report. Data must be posted as multipart form,
with with _photo_ used as the form key for the file itself, and _report_ used as the key for the report
version_UUID linking this photo to a specific report version.

**Fields**

* photo: The photo's binary image data
* report: The version_UUID of the report to which this photo is attached.
    """
    if request.method == 'POST':
        this_report = Report.objects.get(version_UUID=request.data['report'])
        instance = Photo(photo=request.FILES['photo'], report=this_report)
        instance.save()
        return Response('uploaded')

def filter_partial_uuid(queryset, user_UUID):
    if not user_UUID:
        return queryset
    return queryset.filter(user_UUID__startswith=user_UUID)

class UserFilter(filters.FilterSet):
    user_UUID = filters.Filter(method='filter_partial_uuid')

    def filter_partial_uuid(self, qs, name, value):
        user_UUID = value
        if not user_UUID:
            return qs
        return qs.filter(user_UUID__startswith=user_UUID)

    class Meta:
        model = TigaUser
        fields = ['user_UUID']

# For production version, substitute WriteOnlyModelViewSet
class UserViewSet(ReadWriteOnlyModelViewSet):
    """
API endpoint for getting and posting user registration. The only information required is a 36 digit UUID generated on
user's
device. (Registration time is also added by server automatically and included in the database, but is not accessible
through the API.)

**Fields**

* user_UUID: UUID randomly generated on phone to identify each unique user. Must be exactly 36 characters (32 hex digits plus 4 hyphens).
    """
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer
    filter_class = UserFilter


class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONRenderer()


# For production version, substitute WriteOnlyModelViewSet
class ReportViewSet(ReadWriteOnlyModelViewSet):
    """
API endpoint for getting and posting new reports and report versions. (Every time a user edits a report,
a new version is
posted; user keeps only most recent version on phone but server retains all versions.) Note that photos attached to the
report must be uploaded separately through the [photo](/api/photos/) endpoint. (Also note that the HTML form, below,
for testing posts does not work for including responses in posted reports; use the raw/JSON format instead.)

**Fields**

* version_UUID: UUID randomly generated on phone to identify each unique report version. Must be exactly 36 characters (32 hex digits plus 4 hyphens).
* version_number: The report version number. Should be an integer that increments by 1 for each repor version. Note
that the user keeps only the most recent version on the device, but all versions are stored on the server. To
delete a report, submit a version with version_number = -1. This will cause the report to no longer be displated on
the server map (although it will still be retained internally).
* user: user_UUID for the user sending this report. Must be exactly 36 characters (32 hex digits plus 4 hyphens) and user must have already registered this ID.
* report_id: 4-digit alpha-numeric code generated on user phone to identify each unique report from that user. Digits should lbe randomly drawn from the set of all lowercase and uppercase alphabetic characters and 0-9, but excluding 0, o, and O to avoid confusion if we ever need user to be able to refer to a report ID in correspondence with MoveLab (as was previously the case when we had them sending samples).
* phone_upload_time: Date and time on phone when it uploaded fix. Format as [ECMA 262](http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15) date time string (e.g. "2014-05-17T12:34:56.123+01:00".
* creation_time:Date and time on phone when first version of report was created. Format as [ECMA 262](http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15) date time string
(e.g. "2014-05-17T12:34:56.123+01:00".
* version_time:Date and time on phone when this version of report was created. Format as [ECMA 262](http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15) date time string (e
.g. "2014-05-17T12:34:56.123+01:00".
* type: Type of report: 'adult', 'site', or 'mission'.
* mission: If this report was a response to a mission, the unique id field of that mission.
* location_choice: Did user indicate that report relates to current location of phone ("current") or to a location selected manually on the map ("selected")?
* current_location_lon: Longitude of user's current location. In decimal degrees.
* current_location_lat: Latitude of user's current location. In decimal degrees.
* selected_location_lon: Latitude of location selected by user on map. In decimal degrees.
* selected_location_lat: Longitude of location selected by user on map. In decimal degrees.
* note: Note user attached to report.
* package_name: Name of tigatrapp package from which this report was submitted.
* package_version: Version number of tigatrapp package from which this report was submitted.
* device_manufacturer: Manufacturer of device from which this report was submitted.
* device_model: Model of device from which this report was submitted.
* os:  Operating system of device from which this report was submitted.
* os_version: Operating system version of device from which this report was submitted.
* os_language: Language setting of operating system on device from which this report was submitted. 2-digit [ISO 639-1](http://www.iso.org/iso/home/standards/language_codes.htm) language code.
* app_language:Language setting, within tigatrapp, of device from which this report was submitted. 2-digit [ISO 639-1](http://www.iso.org/iso/home/standards/language_codes.htm) language code.
* responses:
    * question: Question that the user responded to.
    * answer: Answer that user selected.

**Query Parameters**

* user_UUID: The user_UUID for a particular user.
* version_number: The report version number.
* report_id: The 4-digit report ID.
* type: The report type (adult, site, or mission).
    """
    queryset = Report.objects.all().prefetch_related("responses", "photos")
    serializer_class = ReportSerializer
    filter_fields = ('user', 'version_number', 'report_id', 'type')

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get the filters from the request
        is_deleted = self.request.query_params.get('is_deleted', None)
        is_last_version = self.request.query_params.get('is_last_version', None)

        # Apply additional filters if provided
        if is_deleted is not None:
            if is_deleted.lower() not in ['true', 'false']:
                raise ParseError("Invalid value for 'is_deleted'. It should be 'true', 'false', or not provided.")

            if is_deleted.lower() == 'true':
                # Filter queryset to include only deleted records
                queryset = queryset.deleted(state=True)
            elif is_deleted.lower() == 'false':
                # Filter queryset to exclude deleted records
                queryset = queryset.deleted(state=False)

        if is_last_version is not None:
            if is_last_version.lower() not in ['true', 'false']:
                raise ParseError("Invalid value for 'is_last_version'. It should be 'true', 'false', or not provided.")

            if is_last_version.lower() == 'true':
                # Filter queryset to include only deleted records
                queryset = queryset.last_version_of_each(state=True)
            elif is_last_version.lower() == 'false':
                # Filter queryset to exclude deleted records
                queryset = queryset.last_version_of_each(state=False)

        return queryset


# For production version, substitute WriteOnlyModelViewSet
class PhotoViewSet(ReadWriteOnlyModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

class BookMarkViewSet(ReadWriteOnlyModelViewSet):
    queryset = BookMark.objects.all()
    serializer_class = BookMarkSerializer
    filter_fields = ('module','user')

# For production version, substitute WriteOnlyModelViewSet
class FixViewSet(ReadWriteOnlyModelViewSet):
    """
API endpoint for getting and posting masked location fixes.

**Fields**

* user: The 36-digit user_UUID for the user sending this location fix.
* fix_time: Date and time when fix was recorded on phone. Format as [ECMA 262](http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15) date time string (e.g. "2014-05-17T12:34:56'
                                              '.123+01:00".
* server_upload_time: Date and time registered by server when it received fix upload. Automatically generated by server.'
* phone_upload_time: Date and time on phone when it uploaded fix. Format as [ECMA 262](http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15) date time string (e.g. "2014-05-17T12:34:56.123+01:00".
* masked_lon: Longitude rounded down to nearest 0.05 decimal degree (floor(lon/.05)*.05).
* masked_lat: Latitude rounded down to nearest 0.05 decimal degree (floor(lat/.05)*.05).
* power: Power level of phone at time fix recorded, expressed as proportion of full charge. Range: 0-1.

**Query Parameters**

* user_UUID: The UUID of the user sending this fix.
    """
    queryset = Fix.objects.all()
    serializer_class = FixSerializer
    filter_fields = ('user_coverage_uuid', )


class SessionPartialUpdateView(GenericAPIView, mixins.UpdateModelMixin):
    '''
    You just need to provide the field which is to be modified.
    '''
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class SessionViewSet(viewsets.ModelViewSet):
    """
API endpoint for sessions
A session is the full set of information uploaded by a user, usually in form of several reports
    """
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    filter_fields = ('id', 'user' )

    def filter_queryset(self, queryset):
        queryset = super(SessionViewSet, self).filter_queryset(queryset)
        return queryset.order_by('-session_ID')


def lookup_photo(request, token, photo_uuid, size):
    if token == settings.PHOTO_SECRET_KEY:
        this_photo = Photo.objects.get(uuid=photo_uuid)
        if size == 'small':
            url = this_photo.get_small_url()
        elif size == 'medium':
            url = this_photo.get_medium_url()
        else:
            url = this_photo.photo.url
        return HttpResponseRedirect(url)


def get_data_time_info(request):
    # setting fixed start time based on release date to avoid the pre-release beta reports
    start_time = settings.START_TIME
    end_time = Report.objects.latest('creation_time').creation_time
    days = (end_time - start_time).days + 1
    weeks = ceil(days / 7.0)
    months = ceil(days / 28.0)
    json_response = {'start_time_posix': calendar.timegm(start_time.utctimetuple()), 'end_time_posix': calendar.timegm(end_time.utctimetuple()), 'n_days': days, 'n_weeks': weeks, 'n_months': months}
    return HttpResponse(json.dumps(json_response))


def get_n_days():
    # setting fixed start time based on release date to avoid the pre-release beta reports
    start_time = settings.START_TIME
    end_time = Report.objects.latest('creation_time').creation_time
    # adding 1 to include the last dayin the set
    return (end_time - start_time).days + 1


def get_n_months():
    # setting fixed start time based on release date to avoid the pre-release beta reports
    start_time = settings.START_TIME
    end_time = Report.objects.latest('creation_time').creation_time
    # adding 1 to include the last dayin the set
    return ((end_time - start_time).days / 28) + 1


def filter_creation_day(queryset, days_since_launch):
    if not days_since_launch:
        return queryset
    try:
        target_day_start = settings.START_TIME + timedelta(days=int(days_since_launch))
        target_day_end = settings.START_TIME + timedelta(days=int(days_since_launch)+1)
        result = queryset.filter(creation_time__range=(target_day_start, target_day_end))
        return result
    except ValueError:
        return queryset


def filter_creation_week(queryset, weeks_since_launch):
    if not weeks_since_launch:
        return queryset
    try:
        target_week_start = settings.START_TIME + timedelta(weeks=int(weeks_since_launch))
        target_week_end = settings.START_TIME + timedelta(weeks=int(weeks_since_launch)+1)
        result = queryset.filter(creation_time__range=(target_week_start, target_week_end))
        return result
    except ValueError:
        return queryset


def filter_creation_month(queryset, months_since_launch):
    if not months_since_launch:
        return queryset
    try:
        target_month_start = settings.START_TIME + timedelta(weeks=int(months_since_launch)*4)
        target_month_end = settings.START_TIME + timedelta(weeks=(int(months_since_launch)*4)+4)
        result = queryset.filter(creation_time__range=(target_month_start, target_month_end))
        return result
    except ValueError:
        return queryset


def filter_creation_year(queryset, year):
    if not year:
        return queryset
    try:
        result = queryset.filter(creation_time__year=year)
        return result
    except ValueError:
        return queryset


class MapDataFilter(filters.FilterSet):

    day = filters.Filter(method='filter_day')
    week = filters.Filter(method='filter_week')
    month = filters.Filter(method='filter_month')
    year = filters.Filter(method='filter_year')

    def filter_day(self, qs, name, value):
        days_since_launch = value
        if not days_since_launch:
            return qs
        try:
            target_day_start = settings.START_TIME + timedelta(days=int(days_since_launch))
            target_day_end = settings.START_TIME + timedelta(days=int(days_since_launch) + 1)
            result = qs.filter(creation_time__range=(target_day_start, target_day_end))
            return result
        except ValueError:
            return qs

    def filter_week(self, qs, name, value):
        weeks_since_launch = value
        if not weeks_since_launch:
            return qs
        try:
            target_week_start = settings.START_TIME + timedelta(weeks=int(weeks_since_launch))
            target_week_end = settings.START_TIME + timedelta(weeks=int(weeks_since_launch) + 1)
            result = qs.filter(creation_time__range=(target_week_start, target_week_end))
            return result
        except ValueError:
            return qs

    def filter_month(self, qs, name, value):
        months_since_launch = value
        if not months_since_launch:
            return qs
        try:
            target_month_start = settings.START_TIME + timedelta(weeks=int(months_since_launch) * 4)
            target_month_end = settings.START_TIME + timedelta(weeks=(int(months_since_launch) * 4) + 4)
            result = qs.filter(creation_time__range=(target_month_start, target_month_end))
            return result
        except ValueError:
            return qs

    def filter_year(self, qs, name, value):
        year = value
        if not year:
            return qs
        try:
            result = qs.filter(creation_time__year=year)
            return result
        except ValueError:
            return qs

    class Meta:
        model = Report
        fields = ['day', 'week', 'month', 'year']


class CoverageMapFilter(filters.FilterSet):
    id_range_start = filters.NumberFilter(field_name='id', lookup_type='gte')
    id_range_end = filters.NumberFilter(field_name='id', lookup_type='lte')

    class Meta:
        model = CoverageArea
        fields = ['id_range_start', 'id_range_end']


class CoverageMonthMapFilter(filters.FilterSet):
    id_range_start = filters.NumberFilter(field_name='id', lookup_expr='gte')
    id_range_end = filters.NumberFilter(field_name='id', lookup_expr='lte')

    class Meta:
        model = CoverageAreaMonth
        fields = ['id_range_start', 'id_range_end']


def get_latest_reports_qs(reports, property_filter=None):
    if property_filter == 'movelab_cat_ge1':
        unique_report_ids = set(r.report_id for r in filter(lambda x: hasattr(x, 'movelab_annotation') and x.movelab_annotation is not None and 'tiger_certainty_category' in x.movelab_annotation and x.movelab_annotation['tiger_certainty_category'] >= 1, reports.iterator()))
    elif property_filter == 'movelab_cat_ge2':
        unique_report_ids = set(r.report_id for r in filter(lambda x: hasattr(x, 'movelab_annotation') and x.movelab_annotation is not None and 'tiger_certainty_category' in x.movelab_annotation and x.movelab_annotation['tiger_certainty_category'] == 2, reports.iterator()))
    elif property_filter == 'embornals_fonts':
        unique_report_ids = set(r.report_id for r in filter(lambda x: x.embornals or x.fonts, reports.iterator()))
    elif property_filter == 'basins':
        unique_report_ids = set(r.report_id for r in filter(lambda x: x.basins, reports.iterator()))
    elif property_filter == 'buckets_wells':
        unique_report_ids = set(r.report_id for r in filter(lambda x: x.buckets or x.wells, reports.iterator()))
    elif property_filter == 'other':
        unique_report_ids = set(r.report_id for r in filter(lambda x: x.other, reports.iterator()))
    else:
        unique_report_ids = set([r.report_id for r in reports])
    result_ids = list()
    for this_id in unique_report_ids:
        these_reports = sorted([report for report in reports if report.report_id == this_id], key=attrgetter('version_number'))
        if these_reports[0].version_number > -1:
            # taking the version with the highest movelab score, if this is a adult report cat_ge1 or cat_ge2 request, otherwise most recent version
            if property_filter in ('movelab_cat_ge1', 'movelab_cat_ge2'):
                movelab_sorted_reports = sorted(filter(lambda x: hasattr(x, 'movelab_annotation') and x.movelab_annotation is not None and 'tiger_certainty_category' in x.movelab_annotation, these_reports), key=attrgetter('movelab_score'))
                this_version_UUID = movelab_sorted_reports[-1].version_UUID
            else:
                this_version_UUID = these_reports[-1].version_UUID
            result_ids.append(this_version_UUID)
    return Report.objects.filter(version_UUID__in=result_ids)


def get_latest_validated_reports(reports):
    reports = filter(lambda x: x.show_on_map(), reports.iterator())
    unique_report_ids = set([r.report_id for r in reports])
    result_ids = list()
    for this_id in unique_report_ids:
        these_reports = sorted([report for report in reports if report.report_id == this_id], key=attrgetter('version_number'))
        if these_reports[0].version_number > -1:
            this_version_UUID = these_reports[-1].version_UUID
            result_ids.append(this_version_UUID)
    return Report.objects.filter(version_UUID__in=result_ids)

# non_visible_report_id is veeeeery slow - try to replace with query (this is a work in progress)
# select "version_UUID" from tigaserver_app_report where "version_UUID" in (select "version_UUID" from tigaserver_app_report where to_char(creation_time,'YYYY') = '2014')
# UNION
# select tigaserver_app_report."version_UUID" from tigaserver_app_report left join tigaserver_app_photo on tigaserver_app_report."version_UUID" = tigaserver_app_photo.report_id where tigaserver_app_photo.id is null
# UNION
# select expert_validated."version_UUID" from (select r."version_UUID" from tigaserver_app_report r,tigacrafting_expertreportannotation an,auth_user_groups g,auth_group gn WHERE r."version_UUID" = an.report_id AND an.user_id = g.user_id AND g.group_id = gn.id AND gn.name='expert' AND an.validation_complete = True GROUP BY r."version_UUID" HAVING count(r."version_UUID") >= 3 AND min(an.status) = 1) expert_validated
# UNION
# select r."version_UUID" from tigaserver_app_report r,tigacrafting_expertreportannotation an,auth_user_groups g,auth_group gn WHERE r."version_UUID" = an.report_id AND an.user_id = g.user_id AND g.group_id = gn.id AND gn.name='superexpert' AND an.validation_complete = True AND an.revise = True GROUP BY r."version_UUID" HAVING min(an.status) = 1

'''
class CoarseFilterAdultReports(ReadOnlyModelViewSet):
    new_reports_unfiltered_adults = get_reports_unfiltered_adults()
    unfiltered_clean_reports = filter_reports(new_reports_unfiltered_adults, False)
    unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id).exclude(hide=True)
    #there seems to be some kind of caching issue .all() forces the queryset to refresh
    queryset = unfiltered_clean_reports_query.all()
    serializer_class = ReportIdSerializer

class CoarseFilterSiteReports(ReadOnlyModelViewSet):
    reports_imbornal = get_reports_imbornal()
    new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
    new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
    new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
    unfiltered_clean_reports = filter_reports(new_reports_unfiltered_sites, False)
    unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id).exclude(hide=True)
    # there seems to be some kind of caching issue .all() forces the queryset to refresh
    queryset = unfiltered_clean_reports_query.all()
    serializer_class = ReportIdSerializer
'''

'''
class NonVisibleReportsMapViewSet(ReadOnlyModelViewSet):

    reports_imbornal = get_reports_imbornal()
    new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
    new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
    new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
    new_reports_unfiltered_adults = get_reports_unfiltered_adults()

    new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

    unfiltered_clean_reports = filter_reports(new_reports_unfiltered,False)
    unfiltered_clean_reports_id = [ report.version_UUID for report in unfiltered_clean_reports ]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id)

    #new_reports_unfiltered_id = [ report.version_UUID for report in filtered_reports ]
    if conf.FAST_LOAD and conf.FAST_LOAD == True:
        non_visible_report_id = []
    else:
        non_visible_report_id = [report.version_UUID for report in Report.objects.exclude(version_UUID__in=unfiltered_clean_reports_id) if not report.visible]

    hidden_reports = Report.objects.exclude(hide=True).exclude(type='mission').filter(version_UUID__in=non_visible_report_id).filter(Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) | Q(package_name='Mosquito Alert') ).exclude(package_name='ceab.movelab.tigatrapp', package_version=10)
    queryset = hidden_reports | unfiltered_clean_reports_query

    serializer_class = MapDataSerializer
    filter_class = MapDataFilter
'''

'''
class AllReportsMapViewSetPaginated(ReadOnlyModelViewSet):
    if conf.FAST_LOAD and conf.FAST_LOAD == True:
        non_visible_report_id = []
    else:
        non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
    queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(version_UUID__in=non_visible_report_id).filter(Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) | Q(package_name='Mosquito Alert') ).exclude(package_name='ceab.movelab.tigatrapp', package_version=10)
    serializer_class = MapDataSerializer
    filter_class = MapDataFilter
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100
'''

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class AcknowledgedNotificationFilter(filters.FilterSet):
    class Meta:
        model = AcknowledgedNotification
        fields = ['user', 'notification']


class AcknowledgedNotificationViewSetPaginated(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet ):
    queryset = AcknowledgedNotification.objects.all().select_related('notification').select_related('user')
    serializer_class = AcknowledgedNotificationSerializer
    filter_class = AcknowledgedNotificationFilter
    pagination_class = StandardResultsSetPagination


@api_view(['POST'])
def photo_blood(request):
    photo_id = request.POST.get('photo_id', -1)
    _status = request.POST.get('status', '')
    if photo_id == -1:
        raise ParseError(detail='photo_id param is mandatory')
    if _status == '':
        raise ParseError(detail='status param is mandatory')
    try:
        photo = Photo.objects.get(pk=int(photo_id))
        photo.blood_genre = _status
        photo.save()
        return Response(status=status.HTTP_200_OK)
    except Photo.DoesNotExist:
        raise ParseError(detail='This picture does not exist')


@api_view(['POST'])
def photo_blood_reset(request):
    report_id = request.POST.get('report_id', '')
    if report_id == '':
        raise ParseError(detail='report_id param is mandatory')
    photos = Photo.objects.filter(report=report_id)
    for p in photos:
        p.blood_genre = None
        p.save()
    return Response(status=status.HTTP_200_OK)


'''
This implementation is weird AF. The correct ack to be used should be /api/ack_notif. This one does the same, but
uses the DELETE verb and answers with no content in case of success, which is really counter-intuitive because
in fact it CREATES an AcknowledgedNotification
'''
@api_view(['DELETE'])
def mark_notif_as_ack(request):
    user = request.query_params.get('user','-1')
    notif = request.query_params.get('notif', -1)
    u = None
    n = None
    if user == '-1':
        raise ParseError(detail='user param is mandatory')
    if notif == -1:
        raise ParseError(detail='notif param is mandatory')
    try:
        u = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='This user does not exist')
    try:
        n = Notification.objects.get(pk=notif)
    except Notification.DoesNotExist:
        raise ParseError(detail='This notification does not exist')
    if AcknowledgedNotification.objects.filter(user=u).filter(notification=n).exists():
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        try:
            #ack_notif = AcknowledgedNotification.objects.get(user=user,notification=notif)
            #ack_notif.delete()
            ack_notif = AcknowledgedNotification(user=u, notification=n)
            ack_notif.save()
            map_notif = Notification.objects.get(id=notif)
            map_notif.acknowledged = True
            map_notif.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AcknowledgedNotification.DoesNotExist:
            raise ParseError(detail='Acknowledged not found')


@api_view(['POST'])
def toggle_crisis_mode(request, user_id=None):
    if user_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User.objects.all(), pk=user_id)
    user.userstat.crisis_mode = not user.userstat.crisis_mode
    user.userstat.save()
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def crisis_report_assign(request, user_id=None, country_id=None):
    if user_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if country_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User.objects.all(), pk=user_id)
    country = get_object_or_404(EuropeCountry.objects.all(), pk=country_id)
    retval = assign_crisis_report(user, country)
    user.userstat.last_emergency_mode_grab = country
    user.userstat.save()
    return Response(data=retval, status=status.HTTP_200_OK)


@api_view(['POST'])
def unsub_from_topic(request):
    code = request.query_params.get('code', '-1')
    user = request.query_params.get('user', '-1')
    if user == '-1':
        raise ParseError(detail='user param is mandatory')
    if code == '-1':
        raise ParseError(detail='code param is mandatory')
    if code == 'global':
        raise ParseError(detail='unsubscription from global not allowed')
    n = None
    usr = None
    try:
        n = NotificationTopic.objects.get(topic_code=code)
    except NotificationTopic.DoesNotExist:
        raise ParseError(detail='topic with this code does not exist')
    try:
        usr = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='no user with id')

    try:
        sub = UserSubscription.objects.get(user=usr, topic=n)
        sub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserSubscription.DoesNotExist:
        raise ParseError(detail="this user is not subscribed to this topic")

@api_view(['POST'])
def subscribe_to_topic(request):
    code = request.query_params.get('code','-1')
    user = request.query_params.get('user','-1')
    if user == '-1':
        raise ParseError(detail='user param is mandatory')
    if code == '-1':
        raise ParseError(detail='code param is mandatory')
    if code == 'global':
        raise ParseError(detail='subscription to global not allowed')
    n = None
    usr = None
    try:
        n = NotificationTopic.objects.get(topic_code=code)
    except NotificationTopic.DoesNotExist:
        n = NotificationTopic(topic_code=code)
        n.save()
    try:
        usr = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='no user with id')

    try:
        with transaction.atomic():
            sub = UserSubscription(user=usr, topic=n)
            sub.save()
            serializer = UserSubscriptionSerializer(sub)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    except IntegrityError:
        raise ParseError(detail='Subscription already exists')


@api_view(['GET'])
def topics_subscribed(request):
    user = request.query_params.get('user', '-1')
    if user == '-1':
        raise ParseError(detail='user param is mandatory')
    usr = None
    try:
        usr = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='no user with this id')
    subs = UserSubscription.objects.filter(user=user).select_related("topic")
    serializer = UserSubscriptionSerializer(subs,many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)

'''
class AllReportsMapViewSetPaginated(ReadOnlyModelViewSet):
    if conf.FAST_LOAD and conf.FAST_LOAD == True:
        non_visible_report_id = []
    else:
        non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
    queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(version_UUID__in=non_visible_report_id).filter(Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) | Q(package_name='Mosquito Alert') ).exclude(package_name='ceab.movelab.tigatrapp', package_version=10).order_by('version_UUID')
    serializer_class = MapDataSerializer
    filter_class = MapDataFilter
    pagination_class = StandardResultsSetPagination
'''

'''
class AllReportsMapViewSet(ReadOnlyModelViewSet):
    if conf.FAST_LOAD and conf.FAST_LOAD == True:
        non_visible_report_id = []
    else:
        non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
    queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(version_UUID__in=non_visible_report_id).filter(Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) | Q(package_name='Mosquito Alert') ).exclude(package_name='ceab.movelab.tigatrapp', package_version=10)
    serializer_class = MapDataSerializer
    filter_class = MapDataFilter
'''

def lon_function(this_lon, these_lons, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2]).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2])
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], year=this_lat[1],month=this_lat[2], n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lon_function_m0(this_lon, these_lons_m0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons_m0 if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0)
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], year=this_lat[1], month=0, n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lon_function_y0(this_lon, these_lons_y0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    n_fixes = len([l for l in these_lons_y0 if l == this_lon])
    if CoverageAreaMonth.objects.filter(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0).count() > 0:
        this_coverage_area = CoverageAreaMonth.objects.get(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0)
        this_coverage_area.n_fixes += n_fixes
    else:
        this_coverage_area = CoverageAreaMonth(lat=this_lat[0], lon=this_lon[0], month=this_lat[1], year=0, n_fixes=n_fixes)
    if fix_list and fix_list.count() > 0:
        this_coverage_area.latest_fix_id = fix_list.order_by('id').last().id
    else:
        this_coverage_area.latest_fix_id = latest_fix_id
    if report_list and report_list.count() > 0:
        this_coverage_area.latest_report_server_upload_time = report_list.order_by('server_upload_time').last().server_upload_time
    else:
        this_coverage_area.latest_report_server_upload_time = latest_report_server_upload_time
    this_coverage_area.save()


def lat_function(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons = [(f.masked_lon, f.fix_time.year, f.fix_time.month) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.year == this_lat[1] and f.fix_time.month == this_lat[2])] + [(r.masked_lon, r.creation_time.year, r.creation_time.month) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.year == this_lat[1] and r.creation_time.month == this_lat[2])]
    unique_lons = set(these_lons)
    [lon_function(this_lon, these_lons, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons]


def lat_function_m0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons_m0 = [(f.masked_lon, f.fix_time.year) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.year == this_lat[1])] + [(r.masked_lon, r.creation_time.year) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.year == this_lat[1])]
    unique_lons_m0 = set(these_lons_m0)
    [lon_function_m0(this_lon, these_lons_m0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons_m0]


def lat_function_y0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time):
    these_lons_y0 = [(f.masked_lon, f.fix_time.month) for f in fix_list if (f.masked_lat == this_lat[0] and f.fix_time.month == this_lat[1])] + [(r.masked_lon, r.creation_time.month) for r in report_list if (r.masked_lat is not None and r.masked_lat == this_lat and r.creation_time.month == this_lat[1])]
    unique_lons_y0 = set(these_lons_y0)
    [lon_function_y0(this_lon, these_lons_y0, this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lon in unique_lons_y0]


def update_coverage_area_month_model_manual():
    json_response = {'updated': False}
    # turning off for now
    if True:
        if CoverageAreaMonth.objects.all().count() > 0:
            latest_report_server_upload_time = CoverageAreaMonth.objects.order_by('latest_report_server_upload_time').last().latest_report_server_upload_time
            latest_fix_id = CoverageAreaMonth.objects.order_by('latest_fix_id').last().latest_fix_id
        else:
            latest_report_server_upload_time = pytz.utc.localize(datetime(1970, 1, 1))
            latest_fix_id = 0
        if CoverageAreaMonth.objects.all().count() == 0 or latest_report_server_upload_time < Report.objects.order_by('server_upload_time').last().server_upload_time or latest_fix_id < Fix.objects.order_by('id').last().id:
            report_list = get_latest_reports_qs(Report.objects.exclude(hide=True).filter(Q(package_name='Tigatrapp',  creation_time__gte=settings.IOS_START_TIME) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)).filter(server_upload_time__gt=latest_report_server_upload_time))
            fix_list = Fix.objects.filter(fix_time__gt=settings.START_TIME, id__gt=latest_fix_id)
            full_lat_list = [(f.masked_lat, f.fix_time.year, f.fix_time.month) for f in fix_list] + [(r.masked_lat, r.creation_time.year, r.creation_time.month) for r in report_list if r.masked_lat is not None]
            full_lat_list_m0 = [(f.masked_lat, f.fix_time.year) for f in fix_list] + [(r.masked_lat, r.creation_time.year) for r in report_list if r.masked_lat is not None]
            full_lat_list_y0 = [(f.masked_lat, f.fix_time.month) for f in fix_list] + [(r.masked_lat, r.creation_time.month) for r in report_list if r.masked_lat is not None]
            unique_lats = set(full_lat_list)
            unique_lats_m0 = set(full_lat_list_m0)
            unique_lats_y0 = set(full_lat_list_y0)
            [lat_function(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats]
            [lat_function_m0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats_m0]
            [lat_function_y0(this_lat, fix_list, latest_fix_id, report_list, latest_report_server_upload_time) for this_lat in unique_lats_y0]
            json_response['updated'] = True
    return json.dumps(json_response)


def coverage_month_internal():
    queryset = CoverageAreaMonth.objects.all()
    serializer = CoverageMonthMapSerializer(queryset, many=True)
    return serializer.data


class CoverageMonthMapViewSet(ReadOnlyModelViewSet):
    queryset = CoverageAreaMonth.objects.all()
    serializer_class = CoverageMonthMapSerializer
    filter_class = CoverageMonthMapFilter

def filter_partial_name(queryset, name):
    if not name:
        return queryset
    return queryset.filter(name__icontains=name)

class TagFilter(filters.FilterSet):
    name = filters.Filter(method='filter_partial_name')

    def filter_partial_name(self, qs, name, value):
        name = value
        if not name:
            return qs
        return qs.filter(name__icontains=name)

    class Meta:
        model = Tag
        fields = ['name']

class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_class = TagFilter

def string_par_to_bool(string_par):
    if string_par:
        string_lower = string_par.lower()
        if string_lower == 'true':
            return True
    return False

def get_cfa_reports():
    new_reports_unfiltered_adults = get_reports_unfiltered_adults()
    unfiltered_clean_reports = filter_reports(new_reports_unfiltered_adults, False)
    unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id).exclude(
        hide=True)
    # there seems to be some kind of caching issue .all() forces the queryset to refresh
    results = []
    for report in unfiltered_clean_reports_query:
        results.append({"version_UUID": report.version_UUID})
    return results

@api_view(['GET'])
def force_refresh_cfa_reports(request):
    if request.method == 'GET':
        results = get_cfa_reports()
        return Response(results)

def get_cfs_reports():
    reports_imbornal = get_reports_imbornal()
    new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
    new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
    new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
    unfiltered_clean_reports = filter_reports(new_reports_unfiltered_sites, False)
    unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id).exclude(
        hide=True)
    # there seems to be some kind of caching issue .all() forces the queryset to refresh
    results = []
    for report in unfiltered_clean_reports_query:
        results.append({"version_UUID": report.version_UUID})
    return results

@api_view(['GET'])
def force_refresh_cfs_reports(request):
    if request.method == 'GET':
        results = get_cfs_reports()
        return Response(results)

@api_view(['POST'])
def msg_ios(request):
    user_id = request.query_params.get('user_id', -1)
    alert_message = request.query_params.get('alert_message', -1)
    link_url = request.query_params.get('link_url', -1)
    if user_id != -1 and alert_message != -1 and link_url != -1:
        this_user = get_object_or_404(TigaUser.objects.all(), pk=user_id)
        notificaiton = Notification.objects.create(
            notification_content=NotificationContent.objects.create(
                title_en=alert_message,
                body_html_en=link_url
            )
        )
        push_message_id = notificaiton.send_to_user(user=this_user)

        return Response({'token': this_user.device_token, 'alert_message': alert_message, 'link_url':link_url, 'push_is_success': bool(push_message_id)})

    else:
        raise ParseError(detail='Invalid parameters')


@api_view(['POST'])
def msg_android(request):
    user_id = request.query_params.get('user_id', -1)
    message = request.query_params.get('message', -1)
    title = request.query_params.get('title', -1)
    if user_id != -1 and message != -1 and title != -1:
        this_user = get_object_or_404(TigaUser.objects.all(), pk=user_id)
        notificaiton = Notification.objects.create(
            notification_content=NotificationContent.objects.create(
                title_en=title,
                body_html_en=message
            )
        )
        push_message_id = notificaiton.send_to_user(user=this_user)

        return Response({'token': this_user.device_token, 'message': message, 'title': title, 'push_is_success': bool(push_message_id)})
    else:
        raise ParseError(detail='Invalid parameters')


@api_view(['POST'])
def token(request):
    token = request.query_params.get('token', -1)
    user_id = request.query_params.get('user_id', -1)
    if( user_id != -1 and token != -1 ):
        queryset = TigaUser.objects.all()
        this_user = get_object_or_404(queryset, pk=user_id)
        this_user.device_token = token
        this_user.save()
        return Response({'token' : token})
    else:
        raise ParseError(detail='Invalid parameters')


@api_view(['GET'])
@cache_page(60 * 5)
def report_stats(request):
    user_id = request.query_params.get('user_id', -1)
    if user_id == -1:
        r_count = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=3).count()
    else:
        user_reports = Report.objects.filter(user__user_UUID=user_id).filter(type='adult')
        r_count = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(version_UUID__in=user_reports).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=3).count()
    content = {'report_count' : r_count}
    return Response(content)


@api_view(['GET'])
@cache_page(60)
def user_count(request):
    filter_criteria = request.query_params.get('filter_criteria', -1)
    if filter_criteria == -1:
        raise ParseError(detail="Invalid filter criteria")
    if filter_criteria == 'uploaded_pictures':
        results = users_with_pictures()
    elif filter_criteria == 'uploaded_pictures_sd':
        results = users_with_storm_drain_pictures()
    elif filter_criteria.startswith('score_arbitrary'):
        range = filter_criteria.split('-')
        results = users_with_score_range(range[1],range[2])
    elif filter_criteria.startswith('score'):
        results = users_with_score(filter_criteria)
    elif filter_criteria.startswith('topic'):
        topic_code = request.query_params.get('value')
        results = users_with_topic(topic_code)
    else:
        raise ParseError(detail="Invalid filter criteria")
    content = { "user_count" : len(results) }
    return Response(content)

'''
def score_label(score):
    if score > 66:
        return "user_score_pro"
    elif 33 < score <= 66:
        return "user_score_advanced"
    else:
        return "user_score_beginner"
'''


def get_user_score(user_id):
    summary = smmry()
    return summary.getScore(user_id)


def refresh_user_scores():
    summary = smmry()
    queryset = TigaUser.objects.all()
    for user in queryset:
        score = summary.getScore(user.user_UUID)
        if user.profile:
            user.profile.score = score[0]
            user.profile.save()
        else:
            if user.score != score[0]:
                user.score = score[0]
                user.save()


@api_view(['GET'])
def user_score_v2(request):
    user_id = request.query_params.get('user_id', -1)
    if user_id == -1:
        raise ParseError(detail='user_id is mandatory')
    user = get_object_or_404(TigaUser.objects.all(), pk=user_id)
    result = compute_user_score_in_xp_v2(user_id, update=True)
    return Response(result)


@api_view(['GET', 'POST'])
def user_score(request):
    user_id = request.query_params.get('user_id', -1)
    if user_id == -1:
        raise ParseError(detail='user_id is mandatory')
    queryset = TigaUser.objects.all()
    user = get_object_or_404(queryset, pk=user_id)
    if request.method == 'GET':
        if user.profile:
            if user.profile.score == 0:
                content = {"user_id": user_id, "score": 1, "score_label": score_label(1)}
            else:
                content = {"user_id": user_id, "score": user.profile.score, "score_label": score_label(user.profile.score)}
        else:
            if user.score == 0:
                content = {"user_id": user_id, "score": 1, "score_label": score_label(1)}
            else:
                content = {"user_id": user_id, "score": user.score, "score_label": score_label(user.score)}
        return Response(content)
    if request.method == 'POST':
        score = request.query_params.get('score', -1)
        if score == -1:
            raise ParseError(detail='score is mandatory')
        try:
            if user.profile:
                p = user.profile
                p.score = int(score)
                p.save()
            else:
                user.score = int(score)
                user.save()
        except ValueError:
            raise ParseError(detail='Invalid score integer value')
        if user.profile:
            content = {"user_id": user_id, "score": user.profile.score, "score_label": score_label(user.profile.score)}
        else:
            content = {"user_id": user_id, "score": user.score, "score_label": score_label(user.score)}
        return Response(content)

'''
def custom_render_notification(notification,locale):
    expert_comment = notification.notification_content.get_title(language_code=locale)
    expert_html = notification.notification_content.get_body_html(language_code=locale)
    content = {
        'id':notification.id,
        'report_id':notification.report.version_UUID,
        'user_id':notification.user.user_UUID,
        'user_score':notification.user.score,
        'user_score_label': score_label(notification.user.score),
        'expert_id':notification.expert.id,
        'date_comment':notification.date_comment,
        'expert_comment':expert_comment,
        'expert_html':expert_html,
        'acknowledged':notification.acknowledged,
        'public':notification.public,
    }
    return content
'''

'''
def custom_render_notification_queryset(queryset,locale):
    content = []
    for notification in queryset:
        content.append(custom_render_notification(notification,locale))
    return content
'''

def custom_render_map_notifications(map_notification):
    expert_comment = map_notification.notification_content.title_es
    expert_html = map_notification.notification_content.body_html_es
    content = {
        'id': map_notification.id,
        'report_id': map_notification.report.version_UUID,
        'user_id': map_notification.user.user_UUID,
        'user_score': map_notification.user.score,
        'user_score_label': score_label(map_notification.user.score),
        'expert_id': map_notification.expert.id,
        'date_comment': map_notification.date_comment,
        'expert_comment': expert_comment,
        'expert_html': expert_html,
        'acknowledged': map_notification.acknowledged,
        'public': map_notification.public,
    }
    return content

def custom_render_mapnotification_queryset(queryset):
    content = []
    for notification in queryset:
        content.append(custom_render_map_notifications(notification))
    return content

def custom_render_sent_notifications(queryset, acknowledged_queryset, locale):
    content = []
    ack_ids = [ a.notification.id for a in acknowledged_queryset ]
    for sent_notif in queryset:
        notification = sent_notif.notification
        expert_comment = notification.notification_content.get_title(language_code=locale)
        expert_html = notification.notification_content.get_body_html(language_code=locale)
        this_content = {
            'id': notification.id,
            'report_id': notification.report.version_UUID if notification.report is not None else None,
            'user_id': sent_notif.sent_to_user.user_UUID if sent_notif.sent_to_user is not None else None,
            'topic': sent_notif.sent_to_topic.topic_code if sent_notif.sent_to_topic is not None else None,
            'user_score': sent_notif.sent_to_user.score if sent_notif.sent_to_user is not None else None,
            'user_score_label': score_label(sent_notif.sent_to_user.score) if sent_notif.sent_to_user is not None else None,
            'expert_id': notification.expert.id,
            'date_comment': notification.date_comment,
            'expert_comment': expert_comment,
            'expert_html': expert_html,
            'acknowledged': True if sent_notif.notification.id in ack_ids else False,
            'public': notification.public,
        }
        content.append(this_content)
    return content


@api_view(['GET'])
def user_notifications(request):
    if request.method == 'GET':
        locale = request.query_params.get('locale', 'en')
        user_id = request.query_params.get('user_id', -1)
        acknowledged = 'ignore'
        if request.query_params.get('acknowledged') != None:
            acknowledged = request.query_params.get('acknowledged', False)
        #all_notifications = Notification.objects.all()
        all_notifications = SentNotification.objects.all().select_related('notification')
        if user_id == -1:
            raise ParseError(detail='user_id is mandatory')
        else:
            all_notifications = all_notifications.filter(sent_to_user__user_UUID=user_id).order_by('-notification__date_comment')

        # we exclude from this the notifications sent via the new system (the ones which have an id entry in SentNotification)
        # these are the notifications sent directly to a user + the notifications sent to a topic
        new_notif_ids = SentNotification.objects.filter(Q(sent_to_user__user_UUID=user_id) | Q( sent_to_topic__isnull = False )).values("notification__id").distinct()
        map_notifications_queryset = Notification.objects.filter(user__user_UUID=user_id).exclude(id__in=new_notif_ids).order_by('-date_comment')

        #global_topic notifications
        global_notifications = SentNotification.objects.filter(sent_to_topic__topic_code='global').select_related('notification')

        #other notifications
        this_user = TigaUser.objects.get(pk=user_id)
        user_subscriptions = this_user.user_subscriptions.all()
        subscribed_topics = [ a.topic for a in  user_subscriptions]
        other_topic_notifications = SentNotification.objects.filter(sent_to_topic__in=subscribed_topics).select_related('notification')

        notifications_all_of_them = all_notifications | global_notifications | other_topic_notifications

        acknowledgements = AcknowledgedNotification.objects.filter(user__user_UUID=user_id)
        if acknowledged != 'ignore':
            ack_bool = string_par_to_bool(acknowledged)
            acknowledged_notifs = acknowledgements.values('notification')
            if ack_bool is True:
                notifications_all_of_them = notifications_all_of_them.filter(notification__in=acknowledged_notifs).order_by('-notification__date_comment')
            else:
                notifications_all_of_them = notifications_all_of_them.exclude(notification__in=acknowledged_notifs).order_by('-notification__date_comment')
        #serializer = NotificationSerializer(all_notifications)
        content = custom_render_sent_notifications(notifications_all_of_them, acknowledgements, locale)
        map_content = custom_render_mapnotification_queryset(map_notifications_queryset)

        final_content = content + map_content

        final_content = sorted(final_content, key=lambda x: x['date_comment'], reverse=True)

        #return Response(serializer.data)
        return Response(final_content)
    # we keep the post method so the old ack method keeps working
    if request.method == 'POST':
        id = request.query_params.get('id', -1)
        try:
            int(id)
        except ValueError:
            raise ParseError(detail='Invalid id integer value')
        queryset = Notification.objects.all()
        this_notification = get_object_or_404(queryset, pk=id)
        if request.query_params.get('acknowledged') is not None:
            ack = request.query_params.get('acknowledged', True)
        if ack != 'ignore':
            ack_bool = string_par_to_bool(ack)
            this_notification.acknowledged = ack_bool
        this_notification.save()
        serializer = NotificationSerializer(this_notification)
        return Response(serializer.data)
    '''
    if request.method == 'POST':
        id = request.query_params.get('id', -1)
        try:
            int(id)
        except ValueError:
            raise ParseError(detail='Invalid id integer value')
        queryset = Notification.objects.all()
        this_notification = get_object_or_404(queryset,pk=id)
        notification_content = this_notification.notification_content
        #body_html_es = request.query_params.get('body_html_es', '-1')
        #title_es = request.query_params.get('title_es', '-1')
        #body_html_ca = request.query_params.get('body_html_ca', '-1')
        #title_ca = request.query_params.get('title_ca', '-1')
        body_html_en = request.query_params.get('body_html_en', '-1')
        title_en = request.query_params.get('title_en', '-1')
        body_html_native = request.query_params.get('body_html_native', '-1')
        title_native = request.query_params.get('title_native', '-1')
        native_locale = request.query_params.get('native_locale', '-1')
        public = request.query_params.get('public', '-1')
        if body_html_en != '-1':
            notification_content.body_html_en = body_html_en
        if title_en != '-1':
            notification_content.title_en = title_en
        if body_html_native != '-1':
            notification_content.body_html_native = body_html_native
        if title_native != '-1':
            notification_content.title_native = title_native
        if native_locale != '-1':
            notification_content.native_locale = native_locale
        if public != '-1':
            public_bool = string_par_to_bool(public)
            this_notification.public = public_bool
        notification_content.save()
        this_notification.save()
        serializer = NotificationSerializer(this_notification)
        return Response(serializer.data)
    if request.method == 'PUT':
        this_notification = Notification()
        serializer = NotificationSerializer(this_notification,data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        id = request.query_params.get('id', -1)
        try:
            int(id)
        except ValueError:
            raise ParseError(detail='Invalid id integer value')
        queryset = Notification.objects.all()
        this_notification = get_object_or_404(queryset, pk=id)
        notification_content = this_notification.notification_content
        this_notification.delete()
        notification_content.delete()
        return HttpResponse(status=204)
    '''


@api_view(['PUT'])
def notification_content(request):
    if request.method == 'PUT':
        this_notification_content = NotificationContent()
        serializer = NotificationContentSerializer(this_notification_content,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def send_notifications(request):
    if request.method == 'PUT':
        data = request.data
        id = data['notification_content_id']
        sender = data['user_id']
        push = bool(data['ppush'].lower() == 'true')
        # report with oldest creation date
        r = None
        try:
            r = data['report_id']
        except KeyError:
            pass
        report = None
        #queryset = NotificationContent.objects.all()
        #notification_content = get_object_or_404(queryset, pk=id)
        notification_content = get_object_or_404(NotificationContent, pk=id)
        recipients = data['recipients']
        topic = None
        send_to = None

        notification_estimate = 0

        if recipients == 'all':
            topic = NotificationTopic.objects.get(topic_code='global')
            #if global, estimate is all users with token
            notification_estimate = TigaUser.objects.exclude(device_token='').filter(device_token__isnull=False).count()
        elif "$" in recipients:
            ids_list = recipients.split('$')
            send_to = TigaUser.objects.filter(user_UUID__in=ids_list)
            notification_estimate = len(ids_list)
        else: #it's either a topic or a single UUID
            try:
                topic = NotificationTopic.objects.get(topic_code=recipients)
                #users subscribed to topic
                notification_estimate = UserSubscription.objects.filter(topic=topic).count()
            except NotificationTopic.DoesNotExist:
                notification_estimate = 1
                send_to = [TigaUser.objects.get(pk=recipients)]

        if r is not None:
            try:
                report = Report.objects.get( pk=r )
            except Report.DoesNotExist:
                pass

        n = Notification(expert_id=sender, notification_content=notification_content, report=report)
        n.save()

        push_success = False
        if topic is not None:
            # send to topic
            try:
                message_id = n.send_to_topic(topic=topic, push=push)
            except Exception:
                pass
            else:
                push_success = bool(message_id)
        else:
            # send to recipient(s)
            message_ids = []
            for recipient in send_to:
                try:
                    message_ids.append(
                        n.send_to_user(user=recipient, push=push)
                    )
                except Exception:
                    pass
            push_success = bool(message_ids) and all(message_ids)

        results = {'non_push_estimate_num': notification_estimate, 'push_success': push_success}
        return Response(results)


@api_view(['GET'])
def nearby_reports_no_dwindow(request):
    if request.method == 'GET':

        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        show_hidden = request.query_params.get('show_hidden', 0)
        show_versions = request.query_params.get('show_versions', 0)

        center_buffer_lat = request.query_params.get('lat', None)
        center_buffer_lon = request.query_params.get('lon', None)

        user = request.query_params.get('user', None)
        tigauser = None
        user_uuids = None
        if user is not None:
            tigauser = get_object_or_404(TigaUser.objects.all(), pk=user)
            if tigauser.profile is not None:
                user_uuids = TigaUser.objects.filter(profile=tigauser.profile).values('user_UUID')

        radius = request.query_params.get('radius', 5000)
        try:
            int(radius)
            if int(radius) > 10000:
                raise ParseError(detail='Values above 10000 not allowed for radius')
        except ValueError:
            raise ParseError(detail='invalid radius number must be integer')

        try:
            int(page_size)
            if int(page_size) > 200:
                raise ParseError(detail='page size can\'t be greater than 200')
            if int(page_size) < 1:
                raise ParseError(detail='page size can\'t be lower than 1')
        except ValueError:
            raise ParseError(detail='invalid radius number must be integer')

        if center_buffer_lat is None or center_buffer_lon is None:
            raise ParseError(detail='invalid parameters')

        '''
        sql = "SELECT \"version_UUID\"  " + \
            "FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT({0} {1})'::geography) <= {2} " + \
            "ORDER BY point::geography <-> 'SRID=4326;POINT({3} {4})'::geography "
        '''

        #Older postgis versions didn't like the second ::geography cast
        sql = "SELECT \"version_UUID\"  " + \
              "FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT(%s %s)'::geography) <= %s " + \
              "ORDER BY point <-> 'SRID=4326;POINT(%s %s)'"

        cursor = connection.cursor()
        cursor.execute(sql, (float(center_buffer_lon), float(center_buffer_lat), float(radius), float(center_buffer_lon), float(center_buffer_lat)))
        data = cursor.fetchall()
        flattened_data = [element for tupl in data for element in tupl]

        reports_adult = Report.objects.exclude(cached_visible=0)\
            .filter(version_UUID__in=flattened_data)\
            .exclude(creation_time__year=2014)\
            .exclude(note__icontains="#345")\
            .exclude(hide=True)\
            .exclude(photos__isnull=True)\
            .filter(type='adult')\
            .annotate(n_annotations=Count('expert_report_annotations'))\
            .filter(n_annotations__gte=3)
        if user is not None:
            if tigauser.profile is None:
                reports_adult = reports_adult.exclude(user=user)
            else:
                reports_adult = reports_adult.exclude(user__user_UUID__in=user_uuids)
        if show_hidden == 0:
            reports_adult = reports_adult.exclude(version_number=-1)

        reports_bite = Report.objects.exclude(cached_visible=0)\
            .filter(version_UUID__in=flattened_data)\
            .exclude(creation_time__year=2014)\
            .exclude(note__icontains="#345")\
            .exclude(hide=True) \
            .filter(type='bite')
        if user is not None:
            if tigauser.profile is None:
                reports_bite = reports_bite.exclude(user=user)
            else:
                reports_bite = reports_bite.exclude(user__user_UUID__in=user_uuids)
        if show_hidden == 0:
            reports_bite = reports_bite.exclude(version_number=-1)

        reports_site = Report.objects.exclude(cached_visible=0)\
            .filter(version_UUID__in=flattened_data)\
            .exclude(creation_time__year=2014)\
            .exclude(note__icontains="#345")\
            .exclude(hide=True) \
            .filter(type='site')
        if user is not None:
            if tigauser.profile is None:
                reports_site = reports_site.exclude(user=user)
            else:
                reports_site = reports_site.exclude(user__user_UUID__in=user_uuids)
        if show_hidden == 0:
            reports_site = reports_site.exclude(version_number=-1)

        if show_versions == 0:
            #classified_reports_in_max_radius = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0 and x.latest_version, reports_adult)
            classified_reports_in_max_radius = filter(lambda x: x.latest_version and x.show_on_map, reports_adult)
        else:
            # classified_reports_in_max_radius = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0 , reports_adult)
            classified_reports_in_max_radius = filter(lambda x: x.show_on_map, reports_adult)


        if user is not None:
            if tigauser.profile is None:
                user_reports = Report.objects.filter(user=user)
            else:
                user_reports = Report.objects.filter(user__user_UUID__in=user_uuids)
            if show_hidden == 0:
                user_reports = user_reports.exclude(version_number=-1)
            if show_versions == 0:
                user_reports = filter(lambda x: x.latest_version, user_reports)
            all_reports = list(classified_reports_in_max_radius) + list(reports_bite) + list(reports_site) + list(user_reports)
        else:
            all_reports = list(classified_reports_in_max_radius) + list(reports_bite) + list(reports_site)

        all_reports_sorted = sorted(all_reports, key=lambda x: x.creation_time, reverse=True)

        paginator = Paginator( all_reports_sorted, int(page_size) )

        try:
            current_page = paginator.page(page)
        except EmptyPage:
            raise ParseError(detail='Empty page')

        serializer = NearbyReportSerializer(current_page.object_list, many=True)

        next = current_page.next_page_number() if current_page.has_next() else None

        previous = current_page.previous_page_number() if current_page.has_previous() else None

        if user_uuids is None:
            if user is not None:
                response = { "user_uuids": [user], "count": paginator.count, "next": next, "previous": previous, "results": serializer.data}
            else:
                response = {"count": paginator.count, "next": next, "previous": previous, "results": serializer.data}
        else:
            user_uuids_flat = [x['user_UUID'] for x in user_uuids]
            response = { "user_uuids": user_uuids_flat, "count": paginator.count, "next": next, "previous": previous, "results": serializer.data}

        return Response(response)


@api_view(['GET'])
def nearby_reports_fast(request):
    if request.method == 'GET':
        dwindow = request.query_params.get('dwindow', 90)
        try:
            int(dwindow)
        except ValueError:
            raise ParseError(detail='Invalid dwindow integer value')
        if int(dwindow) > 365:
            raise ParseError(detail='Values above 365 not allowed for dwindow')

        date_n_days_ago = datetime.now() - timedelta(days=int(dwindow))

        center_buffer_lat = request.query_params.get('lat', None)
        center_buffer_lon = request.query_params.get('lon', None)

        radius = request.query_params.get('radius', 5000)
        if radius >= 10000:
            raise ParseError(detail='Values above 10000 not allowed for radius')

        if center_buffer_lat is None or center_buffer_lon is None:
            return Response(status=400,data='invalid parameters')

        sql = "SELECT \"version_UUID\"  " + \
            "FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT(%s %s)'::geography) <= %s " + \
            "ORDER BY point::geography <-> 'SRID=4326;POINT(%s %s)'::geography "

        cursor = connection.cursor()
        cursor.execute(sql, (float(center_buffer_lon), float(center_buffer_lat), float(radius), float(center_buffer_lon), float(center_buffer_lat)))
        data = cursor.fetchall()
        flattened_data = [element for tupl in data for element in tupl]

        reports = Report.objects.exclude(cached_visible=0)\
            .filter(version_UUID__in=flattened_data)\
            .exclude(creation_time__year=2014)\
            .exclude(note__icontains="#345")\
            .exclude(hide=True)\
            .exclude(photos__isnull=True)\
            .filter(type='adult')\
            .annotate(n_annotations=Count('expert_report_annotations'))\
            .filter(n_annotations__gte=3)\
            .exclude(creation_time__lte=date_n_days_ago)

        classified_reports_in_max_radius = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0, reports)

        if len(classified_reports_in_max_radius) < 10:
            serializer = NearbyReportSerializer(classified_reports_in_max_radius)
        else:
            serializer = NearbyReportSerializer(classified_reports_in_max_radius[:10])
        return Response(serializer.data)

# This is the old method which used a Window. It is now deprecated

# @api_view(['GET'])
# def nearby_reports(request):
#     if request.method == 'GET':
#         dwindow = request.query_params.get('dwindow', 30)
#         try:
#             int(dwindow)
#         except ValueError:
#             raise ParseError(detail='Invalid dwindow integer value')
#         if int(dwindow) > 365:
#             raise ParseError(detail='Values above 365 not allowed for dwindow')
#
#         date_N_days_ago = datetime.now() - timedelta(days=int(dwindow))
#
#         center_buffer_lat = request.query_params.get('lat', None)
#         center_buffer_lon = request.query_params.get('lon', None)
#         radius = request.query_params.get('radius', '2500')
#         if center_buffer_lat is None or center_buffer_lon is None:
#             return Response(status=400,data='invalid parameters')
#
#         center_point_4326 = GEOSGeometry('SRID=4326;POINT(' + center_buffer_lon + ' ' + center_buffer_lat + ')')
#         center_point_3857 = center_point_4326.transform(3857,clone=True)
#
#         swcorner_3857 = GEOSGeometry('SRID=3857;POINT(' + str(center_point_3857.x - float(radius)) + ' ' + str(center_point_3857.y - float(radius)) + ')')
#         nwcorner_3857 = GEOSGeometry('SRID=3857;POINT(' + str(center_point_3857.x - float(radius)) + ' ' + str(center_point_3857.y + float(radius)) + ')')
#         secorner_3857 = GEOSGeometry('SRID=3857;POINT(' + str(center_point_3857.x + float(radius)) + ' ' + str(center_point_3857.y - float(radius)) + ')')
#         necorner_3857 = GEOSGeometry('SRID=3857;POINT(' + str(center_point_3857.x + float(radius)) + ' ' + str(center_point_3857.y + float(radius)) + ')')
#
#         swcorner_4326 = swcorner_3857.transform(4326,clone=True)
#         nwcorner_4326 = nwcorner_3857.transform(4326, clone=True)
#         secorner_4326 = secorner_3857.transform(4326, clone=True)
#         necorner_4326 = necorner_3857.transform(4326, clone=True)
#
#         min_lon = swcorner_4326.x
#         min_lat = swcorner_4326.y
#
#         max_lon = necorner_4326.x
#         max_lat = necorner_4326.y
#
#         all_reports = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=3).exclude(creation_time__lte=date_N_days_ago)
#         #all_reports = Report.objects.exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=3).exclude(creation_time__lte=date_N_days_ago)
#         #Broad square filter
#         all_reports = all_reports.filter(Q(location_choice='selected', selected_location_lon__range=(min_lon,max_lon),selected_location_lat__range=(min_lat, max_lat)) | Q(location_choice='current', current_location_lon__range=(min_lon,max_lon), current_location_lat__range=(min_lat, max_lat)))
#         classified_reports = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0,all_reports)
#         serializer = NearbyReportSerializer(classified_reports)
#         return Response(serializer.data)


def filter_partial_name_address(queryset, name):
    if not name:
        return queryset
    return queryset.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))

class UserAddressFilter(filters.FilterSet):
    name = filters.Filter(method='filter_partial_name_address')

    def filter_partial_name_address(self, qs, name, value):
        name = value
        if not name:
            return qs
        return qs.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class UserAddressViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.exclude(first_name='').filter(groups__name__in=['expert','superexpert'])
    serializer_class = UserAddressSerializer
    filter_class = UserAddressFilter

def report_to_point(report):
    return GEOSGeometry('SRID=4326;POINT(' + str(report.point.x) + ' ' + str(report.point.y) + ')')

def distance_matrix(center_point, all_points):
    center_point_meters = center_point.transform(3857,True)
    points_by_distance = []
    for report in all_points:
        point = report_to_point(report)
        point_meters = point.transform(3857,True)
        distance = point_meters.distance(center_point_meters)
        this_point_by_distance = [report,distance]
        points_by_distance.append(this_point_by_distance)
    sorted_list = sorted(points_by_distance, key=lambda x: x[1])
    return sorted_list


@api_view(['GET'])
def nearby_reports(request):
    if request.method == 'GET':
        MAX_SEARCH_RADIUS = 100000
        dwindow = request.query_params.get('dwindow', 90)
        try:
            int(dwindow)
        except ValueError:
            raise ParseError(detail='Invalid dwindow integer value')
        if int(dwindow) > 365:
            raise ParseError(detail='Values above 365 not allowed for dwindow')

        date_N_days_ago = datetime.now() - timedelta(days=int(dwindow))

        center_buffer_lat = request.query_params.get('lat', None)
        center_buffer_lon = request.query_params.get('lon', None)
        radius = request.query_params.get('radius', 5000)
        if center_buffer_lat is None or center_buffer_lon is None:
            return Response(status=400,data='invalid parameters')

        center_point_4326 = GEOSGeometry('SRID=4326;POINT(' + center_buffer_lon + ' ' + center_buffer_lat + ')')

        all_reports = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=3).exclude(creation_time__lte=date_N_days_ago)
        reports_in_max_radius = all_reports.filter(point__distance_lt=(center_point_4326,Distance(m=MAX_SEARCH_RADIUS)))
        classified_reports_in_max_radius = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0,reports_in_max_radius)
        dst = distance_matrix(center_point_4326,classified_reports_in_max_radius)
        reports_sorted_by_distance = [dst[i][0] for i in range(0,len(dst))]
        if(len(reports_sorted_by_distance) < 10):
            serializer = NearbyReportSerializer(reports_sorted_by_distance, many=True)
        else:
            serializer = NearbyReportSerializer(reports_sorted_by_distance[:10], many=True)
        return Response(serializer.data)

        '''
        -- All points within a given distance from given coordinate - this is FAST
        SELECT st_distance(point::geography, 'SRID=4326;POINT(2.06999 41.62729)'::geography) as d
        FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT(2.06999 41.62729)'::geography) <= 5000
        ORDER BY point::geography <-> 'SRID=4326;POINT(2.06999 41.62729)'::geography;
        '''

        '''
        keep_looping = True
        while( (len(classified_reports) < minimum_points) and keep_looping ):
            radius = radius + RADIUS_INCREASE
            reports_in_radius = all_reports.filter(point__distance_lt=(center_point_4326,Distance(m=radius)))
            classified_reports = filter(lambda x: x.simplified_annotation is not None and x.simplified_annotation['score'] > 0,reports_in_radius)
            if radius > MAX_SEARCH_RADIUS:
                keep_looping = False
        '''


@api_view(['POST'])
def profile_new(request):
    if request.method == 'POST':
        firebase_token = request.query_params.get('fbt', -1)
        user_id = request.query_params.get('usr', -1)
        if firebase_token == -1:
            raise ParseError(detail='firebase token is mandatory')
        if user_id == -1:
            raise ParseError(detail='user is mandatory')
        tigauser = get_object_or_404(TigaUser,pk=user_id)
        if tigauser.profile is None:
            #profile exists?
            try:
                p = TigaProfile.objects.get(firebase_token=firebase_token)
            except TigaProfile.DoesNotExist:
                p = TigaProfile(firebase_token=firebase_token,score=tigauser.score)
                p.save()
            tigauser.profile = p
            tigauser.save()
            serializer = TigaProfileSerializer(p)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            #profile exists?
            try:
                p = TigaProfile.objects.get(firebase_token=firebase_token)
            except TigaProfile.DoesNotExist:
                p = TigaProfile(firebase_token=firebase_token, score=tigauser.score)
                p.save()
            profile = p
            devices = profile.profile_devices
            # Get all devices for profile - if it existed there will already be devices registered
            for device in devices.all():
                if device.score > profile.score:
                    profile.score = device.score
                if device.user_UUID == user_id:
                    raise ParseError(detail='this device is already associated with this profile')
            profile.profile_devices.add(tigauser)
            profile.save()
            serializer = TigaProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)


def send_unblock_email(name, email):
    lock_period = settings.ENTOLAB_LOCK_PERIOD
    send_to = copy.copy(settings.ADDITIONAL_EMAIL_RECIPIENTS)
    send_to.append(email)
    subject = 'MOSQUITO ALERT - blocked report release warning'
    plaintext = get_template('tigaserver_app/report_release/report_release_template')
    context = {
        'name': name,
        'n_days': lock_period
    }
    text_content = plaintext.render(context)
    email = EmailMessage(subject, text_content, to=send_to)
    email.send(fail_silently=True)


@api_view(['DELETE'])
def clear_blocked_all(request):
    if request.method == 'DELETE':
        lock_period = settings.ENTOLAB_LOCK_PERIOD
        superexperts = User.objects.filter(groups__name='superexpert')
        annos = ExpertReportAnnotation.objects.filter(validation_complete=False).exclude(user__in=superexperts).order_by('user__username', 'report')
        to_delete = []
        recipients = []
        for anno in annos:
            elapsed = (datetime.now(timezone.utc) - anno.created).days
            if elapsed > lock_period:
                to_delete.append(anno.id)
                if anno.user.email is not None and anno.user.email != '':
                    if anno.user not in recipients:
                        recipients.append(anno.user)
        ExpertReportAnnotation.objects.filter(id__in=to_delete).delete()
        for r in recipients:
            name = r.first_name if r.first_name != '' else r.username
            email = r.email
            send_unblock_email( name, email )
        return Response(status=status.HTTP_200_OK)


@api_view(['DELETE'])
def clear_blocked(request, username, report=None):
    lock_period = settings.ENTOLAB_LOCK_PERIOD
    if request.method == 'DELETE':
        if username is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User.objects.all(), username=username)
        actual_report = None
        if report is not None:
            actual_report = get_object_or_404(Report.objects.all(), pk=report)
        if report is not None:
            annotations_for_user = ExpertReportAnnotation.objects.filter(user=user).filter(validation_complete=False).filter(report=actual_report)
        else:
            annotations_for_user = ExpertReportAnnotation.objects.filter(user=user).filter(validation_complete=False)
        to_delete = []
        recipients = []
        for anno in annotations_for_user:
            elapsed = (datetime.now(timezone.utc) - anno.created).days
            if elapsed > lock_period:
                to_delete.append(anno.id)
                if anno.user.email is not None and anno.user.email != '':
                    if anno.user not in recipients:
                        recipients.append(anno.user)
        ExpertReportAnnotation.objects.filter(id__in=to_delete).delete()
        for r in recipients:
            name = r.first_name if r.first_name != '' else r.username
            email = r.email
            send_unblock_email( name, email )

        return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def profile_detail(request):
    if request.method == 'GET':
        firebase_token = request.query_params.get('fbt', -1)
        uuid = request.query_params.get('usr_uuid', -1)
        if firebase_token == -1:
            if uuid == -1:
                raise ParseError(detail='either firebase token or usr_uuid are mandatory')
            else:
                user = get_object_or_404(TigaUser,user_UUID=uuid)
                reports = Report.objects.filter(user=user).exclude(type='bite').exclude(type='mission')
                serializer = DetailedReportSerializer(reports, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            profile = get_object_or_404(TigaProfile.objects,firebase_token=firebase_token)
            serializer = DetailedTigaProfileSerializer(profile)

            #This is probably very wrong. We filter a copy of the serialized data to exclude missions
            copied_data = copy.deepcopy(serializer.data)
            for device in copied_data['profile_devices']:
                for idx, report in reversed(list(enumerate(device['user_reports']))):
                    if report['type'] == 'mission':
                        del device['user_reports'][idx]
                    r = Report.objects.get(pk=report['version_UUID'])
                    if not r.latest_version:
                        del device['user_reports'][idx]

            return Response(copied_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def reports_id_filtered(request):
    if request.method == 'GET':
        report_id = request.query_params.get('report_id', -1)
        if report_id == -1:
            raise ParseError(detail='report_id is mandatory')
        qs = Report.objects.filter(type='adult').exclude(version_number=-1).filter(report_id__startswith=report_id).order_by('-version_time')
        serializer = ReportSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def uuid_list_autocomplete(request):
    if request.method == 'GET':
        loc = request.query_params.get('loc', -1)
        user = request.user
        uuid = request.query_params.get('uuid', -1)

        if uuid == -1:
            raise ParseError(detail='uuid is mandatory')

        qs = ExpertReportAnnotation.objects.filter(user=user).filter(report__type='adult').filter(report__version_UUID__startswith=uuid)
        if loc == 'spain':
            qs = qs.filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values('report__version_UUID').distinct()
        elif loc == 'europe':
            qs = qs.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values('report__version_UUID').distinct()
        else:
            qs = qs.values('report__version_UUID').distinct()
        return Response(qs, status=status.HTTP_200_OK)

package_filter = (
        Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) |
        Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) |
        Q(package_name='cat.ibeji.tigatrapp') |
        Q(package_name='Mosquito Alert')
)

@api_view(['GET'])
def all_reports_paginated(request):
    if request.method == 'GET':
        if conf.FAST_LOAD and conf.FAST_LOAD == True:
            non_visible_report_id = []
        else:
            non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
        queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(
            version_UUID__in=non_visible_report_id).filter( package_filter )\
            .exclude(package_name='ceab.movelab.tigatrapp', package_version=10).order_by('version_UUID')
        f = MapDataFilter(request.GET, queryset=queryset)
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(f.qs, request)
        serializer = MapDataSerializer(result_page, many=True, context={'request':request})
        return paginator.get_paginated_response(serializer.data)
        #return Response(serializer.data)

# this function can be called by scripts and replicates the api behaviour, without calling API. Therefore, no timeouts
def all_reports_internal(year):
    non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
    queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(
        version_UUID__in=non_visible_report_id).filter( package_filter )\
        .exclude(package_name='ceab.movelab.tigatrapp', package_version=10).filter(creation_time__year=year)
    serializer = MapDataSerializer(queryset, many=True)
    return serializer.data

@api_view(['GET'])
def all_reports(request):
    if request.method == 'GET':
        if conf.FAST_LOAD and conf.FAST_LOAD == True:
            non_visible_report_id = []
        else:
            non_visible_report_id = [report.version_UUID for report in Report.objects.all() if not report.visible]
        queryset = Report.objects.exclude(hide=True).exclude(type='mission').exclude(
            version_UUID__in=non_visible_report_id).filter( package_filter )\
            .exclude(package_name='ceab.movelab.tigatrapp', package_version=10)
        f = MapDataFilter(request.GET, queryset=queryset)
        serializer = MapDataSerializer(f.qs, many=True)
        return Response(serializer.data)


def non_visible_reports_internal(year):
    reports_imbornal = get_reports_imbornal()
    new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
    new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
    new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
    new_reports_unfiltered_adults = get_reports_unfiltered_adults()

    new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

    unfiltered_clean_reports = filter_reports(new_reports_unfiltered, False)
    unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
    unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id)

    # new_reports_unfiltered_id = [ report.version_UUID for report in filtered_reports ]
    if conf.FAST_LOAD and conf.FAST_LOAD == True:
        non_visible_report_id = []
    else:
        non_visible_report_id = [report.version_UUID for report in
                                 Report.objects.exclude(version_UUID__in=unfiltered_clean_reports_id) if
                                 not report.visible]

    hidden_reports = Report.objects.exclude(hide=True).exclude(type='mission').filter(
        version_UUID__in=non_visible_report_id).filter( package_filter )\
        .exclude(package_name='ceab.movelab.tigatrapp', package_version=10)

    queryset = hidden_reports | unfiltered_clean_reports_query
    if year is not None:
        queryset = queryset.filter(creation_time__year=year)

    serializer = MapDataSerializer(queryset, many=True)
    return serializer.data


@api_view(['GET'])
def non_visible_reports_paginated(request):
    if request.method == 'GET':
        year = request.query_params.get('year', None)

        reports_imbornal = get_reports_imbornal()
        new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
        new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
        new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
        new_reports_unfiltered_adults = get_reports_unfiltered_adults()

        new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

        unfiltered_clean_reports = filter_reports(new_reports_unfiltered, False)
        unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
        unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id)

        # new_reports_unfiltered_id = [ report.version_UUID for report in filtered_reports ]
        if conf.FAST_LOAD and conf.FAST_LOAD == True:
            non_visible_report_id = []
        else:
            non_visible_report_id = [report.version_UUID for report in
                                     Report.objects.exclude(version_UUID__in=unfiltered_clean_reports_id) if
                                     not report.visible]

        hidden_reports = Report.objects.exclude(hide=True).exclude(type='mission').filter(
            version_UUID__in=non_visible_report_id).filter( package_filter )\
            .exclude(package_name='ceab.movelab.tigatrapp', package_version=10).order_by('version_UUID')

        queryset = hidden_reports | unfiltered_clean_reports_query
        if year is not None:
            queryset = queryset.filter(creation_time__year=year)

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = MapDataSerializer(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def non_visible_reports(request):
    if request.method == 'GET':
        year = request.query_params.get('year', None)

        reports_imbornal = get_reports_imbornal()
        new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
        new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
        new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
        new_reports_unfiltered_adults = get_reports_unfiltered_adults()

        new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

        unfiltered_clean_reports = filter_reports(new_reports_unfiltered, False)
        unfiltered_clean_reports_id = [report.version_UUID for report in unfiltered_clean_reports]
        unfiltered_clean_reports_query = Report.objects.filter(version_UUID__in=unfiltered_clean_reports_id)

        # new_reports_unfiltered_id = [ report.version_UUID for report in filtered_reports ]
        if conf.FAST_LOAD and conf.FAST_LOAD == True:
            non_visible_report_id = []
        else:
            non_visible_report_id = [report.version_UUID for report in
                                     Report.objects.exclude(version_UUID__in=unfiltered_clean_reports_id) if
                                     not report.visible]

        hidden_reports = Report.objects.exclude(hide=True).exclude(type='mission').filter(
            version_UUID__in=non_visible_report_id).filter( package_filter )\
            .exclude(package_name='ceab.movelab.tigatrapp', package_version=10)

        queryset = hidden_reports | unfiltered_clean_reports_query
        if year is not None:
            queryset = queryset.filter(creation_time__year=year)

        serializer = MapDataSerializer(queryset, many=True)
        return Response(serializer.data)

class OWCampaignsViewSet(ReadOnlyModelViewSet):
    serializer_class = OWCampaignsSerializer

    def get_queryset(self):
        qs = OWCampaigns.objects.all()
        country_id = self.request.query_params.get('country_id', None)
        if country_id is not None:
            try:
                country_int = int(country_id)
                qs = qs.filter(country__gid=country_int)
            except ValueError:
                return None
        return qs


class OrganizationsPinViewSet(ReadOnlyModelViewSet):
    serializer_class = OrganizationPinsSerializer

    def get_queryset(self):
        qs = OrganizationPin.objects.all()
        return qs


@api_view(['POST'])
def favorite(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id', -1)
        report_id = request.POST.get('report_id', '')
        note = request.POST.get('note', '')
        if user_id == -1:
            raise ParseError(detail='user_id param is mandatory')
        if report_id == '':
            raise ParseError(detail='report_id param is mandatory')
        user = get_object_or_404(User, pk=user_id)
        report = get_object_or_404(Report, pk=report_id)
        fav = FavoritedReports.objects.filter(user=user).filter(report=report).first()
        if fav:
            fav.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            new_fav = FavoritedReports(user=user, report=report, note=note)
            new_fav.save()
            return Response(status=status.HTTP_200_OK)

def get_filter_params_from_q(q):
    if q == '':
        return {
            'type':'all',
            'visibility':'visible',
            'aithr':1.00,
            'note': '',
            'country': 'all',
            'country_exclude': ''
        } #default values
    else:
        json_filter = json.loads(q);
        return {
            'type': json_filter['report_type'],
            'visibility': json_filter['visibility'],
            'aithr': float(json_filter['ia_threshold']),
            'note': json_filter['note'],
            'country': json_filter['country'],
            'country_exclude': json_filter['country_exclude']
        }

@api_view(['PATCH'])
def hide_report(request):
    if request.method == 'PATCH':
        #print(request.data)
        report_id = request.data.get('report_id','-1')
        hide_val = request.data.get('hide')
        if report_id == '-1':
            raise ParseError(detail='report_id param is mandatory')
        if not hide_val:
            raise ParseError(detail='hide param is mandatory')
        hide = hide_val == 'true'
        report = get_object_or_404(Report,pk=report_id)
        if ExpertReportAnnotation.objects.filter(report=report).count() > 0:
            return Response(data={'message': 'success', 'opcode': -1}, status=status.HTTP_400_BAD_REQUEST)
        report.hide = hide
        report.save()
        return Response(data={'message': 'hide set to {0}'.format( hide ), 'opcode': 0}, status=status.HTTP_200_OK)

@api_view(['GET'])
def bookmarks(request):
    if request.method == 'GET':
        bookmarks = BookMark.objects.all()
        serializer = BookMarkSerializer(bookmarks, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)



@api_view(['POST', 'DELETE'])
def bookmark_report(request):
    if request.method == 'POST':
        report_id = request.data.get('report_id', '')
        user_id = request.data.get('user_id', '')
        label = request.data.get('label', None)
        module = request.data.get('module', None)
        json_filter = request.data.get('json_filter', None)
        user = get_object_or_404(User, pk=user_id)
        report = get_object_or_404(Report, pk=report_id)
        if label is None:
            raise ParseError(detail='Label parameter is mandatory')
        if module is None:
            raise ParseError(detail='Module parameter is mandatory')
        b = BookMark( user=user, report=report, label=label, module=module, json_filter=json_filter )
        try:
            b.save()
            serializer = BookMarkSerializer(b, many=False)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response(data={'message': "You have already a bookmark with the label '{0}', please use another".format(label), 'opcode': -1}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        id = request.data.get('id', '')
        report = get_object_or_404(BookMark, pk=id)
        report.delete()
        return Response(data={}, status=status.HTTP_204_NO_CONTENT)



@api_view(['PATCH'])
def flip_report(request):
    if request.method == 'PATCH':
        flip_to_type = request.data.get('flip_to_type', '')
        flip_to_subtype = request.data.get('flip_to_subtype', '')
        report_id = request.data.get('report_id', '')
        report = get_object_or_404(Report,pk=report_id)
        if ExpertReportAnnotation.objects.filter(report=report).count() > 0:
            return Response(data={'message': 'success', 'opcode': -1}, status=status.HTTP_400_BAD_REQUEST)
        if flip_to_type == '': # adult | site
            raise ParseError(detail='flip_to_type param is mandatory')
        if flip_to_type not in [Report.TYPE_ADULT, Report.TYPE_SITE]:
            raise ParseError(detail='value not allowed, possible values are \'adult\', \'site\'')
        if flip_to_type == Report.TYPE_SITE:
            if flip_to_subtype == '':
                raise ParseError(detail='flip_to_subtype param is mandatory if type is site')
            else:
                if flip_to_subtype not in ['storm_drain_water','storm_drain_dry', 'other_water', 'other_dry']:
                    raise ParseError(detail='value not allowed, possible values are \'storm_drain_water\',\'storm_drain_dry\', \'other_water\', \'other_dry\' ')

        if report.type == Report.TYPE_ADULT and flip_to_type == Report.TYPE_ADULT:
            return Response(
                data={'message': 'Type is already adult, doing nothing', 'opcode': -2}, status=status.HTTP_400_BAD_REQUEST)
        # delete questions and answers ?

        # set new questions and answers
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_12	question_12_answer_122	122		12 -> Other
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_10	question_10_answer_101	101		10 -> Water

        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_12	question_12_answer_121	121		12 -> Storm Drain
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_10	question_10_answer_101	101		10 -> Water
        with transaction.atomic():
            ReportResponse.objects.filter(report=report).delete()
            rr_type_stormdrain = ReportResponse(report=report,question='question_12',answer='question_12_answer_121',question_id=12,answer_id=121)
            rr_type_other = ReportResponse(report=report, question='question_12', answer='question_12_answer_122', question_id=12, answer_id=122)
            rr_yes_water = ReportResponse(report=report, question='question_10', answer='question_10_answer_101', question_id=10, answer_id=101)
            rr_no_water = ReportResponse(report=report, question='question_10', answer='question_10_answer_102', question_id=10, answer_id=102)
            report.flipped = True
            report.flipped_on = timezone.now()
            if flip_to_type == Report.TYPE_SITE:
                report.flipped_to = report.type + '#site'
                report.type = Report.TYPE_SITE
                report.save()
                if flip_to_subtype == 'storm_drain_water':
                    rr_type_stormdrain.save()
                    rr_yes_water.save()
                    message = "Report changed to Site - Storm Drain, Water"
                elif flip_to_subtype == 'storm_drain_dry':
                    rr_type_stormdrain.save()
                    rr_no_water.save()
                    message = "Report changed to Site - Storm Drain, No Water"
                elif flip_to_subtype == 'other_dry':
                    rr_type_other.save()
                    rr_no_water.save()
                    message = "Report changed to Site - Other, No Water"
                elif flip_to_subtype == 'other_water':
                    rr_type_other.save()
                    rr_yes_water.save()
                    message = "Report changed to Site - Other, Water"
            elif flip_to_type == Report.TYPE_ADULT:
                report.flipped_to = report.type + '#adult'
                report.type = Report.TYPE_ADULT
                report.save()
                message = "Report changed to Adult"

            return Response(data={'message': message, 'new_type': flip_to_type, 'new_subtype': flip_to_subtype, 'opcode': 0}, status=status.HTTP_200_OK)

@api_view(['POST'])
def quick_upload_report(request):
    if request.method == 'POST':
        report_id = request.POST.get('report_id', '-1')
        if report_id == '-1':
            raise ParseError(detail='report_id param is mandatory')
        report = get_object_or_404(Report, pk=report_id)
        if ExpertReportAnnotation.objects.filter(report=report).count() > 0:
            return Response(data={'message': 'success', 'opcode': -1}, status=status.HTTP_400_BAD_REQUEST)
        super_movelab = User.objects.get(pk=24)
        if not ExpertReportAnnotation.objects.filter(report=report).filter(user=super_movelab).exists():
            new_annotation = ExpertReportAnnotation(report=report, user=super_movelab)
            photo = report.photos.first()
            new_annotation.site_certainty_notes = 'auto'
            new_annotation.best_photo_id = photo.id
            new_annotation.validation_complete = True
            new_annotation.revise = True
            new_annotation.save()
            BookMark.objects.filter(report=report).delete()
            return Response(data={'message': 'success', 'opcode': 0}, status=status.HTTP_200_OK)
        else:
            return Response(data={'message': 'success', 'opcode': 1}, status=status.HTTP_200_OK)


@api_view(['POST'])
def annotate_coarse(request):
    if request.method == 'POST':
        report_id = request.POST.get('report_id', '-1')
        category_id = request.POST.get('category_id', -1)
        validation_value = request.POST.get('validation_value', None)
        if report_id == '-1':
            raise ParseError(detail='report_id param is mandatory')
        # if category_id == -1:
        #     raise ParseError(detail='category_id param is mandatory')
        report = get_object_or_404(Report, pk=report_id)
        # This prevents auto annotating a report which has been claimed by someone between reloads
        if ExpertReportAnnotation.objects.filter(report=report).count() > 0:
            return Response(data={'message': 'success', 'opcode': -1}, status=status.HTTP_400_BAD_REQUEST)
        category = get_object_or_404(Categories, pk=category_id)
        if validation_value == '' or not category.specify_certainty_level:
            validation_value = None
        annotation = auto_annotate(report, category, validation_value)
        current_domain = get_current_domain(request)
        issue_notification(annotation, current_domain)
        BookMark.objects.filter(report=report).delete()
        return Response(data={'message':'success', 'opcode': 0}, status=status.HTTP_200_OK)

@api_view(['GET'])
def coarse_filter_reports(request):
    if request.method == 'GET':

        new_reports_unfiltered_adults = get_reports_unfiltered_adults_except_being_validated()
        reports_imbornal = get_reports_imbornal()
        # new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
        # new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
        # new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other
        new_reports_unfiltered_sites = (Report.objects.filter(type='site')
                                        .exclude(note__icontains='#345')
                                        .exclude(photos=None).annotate(
                                            n_annotations=Count('expert_report_annotations')
                                        )
                                        .filter(n_annotations=0).order_by('-creation_time').all())

        seek = request.query_params.get("seek", '')
        bookmark_report = None
        current_text_filter = None

        if seek != '':
            bookmark = get_object_or_404(BookMark, pk=seek)
            bookmark_report = bookmark.report
            filter_params = get_filter_params_from_q(bookmark.json_filter)
            current_text_filter = bookmark.json_filter
        else:
            q = request.query_params.get("q", '')
            filter_params = get_filter_params_from_q(q)

        aithr = filter_params['aithr']
        type = filter_params['type']
        visibility = filter_params['visibility']
        note = filter_params['note']
        country = filter_params['country']
        country_exclude = filter_params['country_exclude']

        limit = request.query_params.get("limit", 300)
        offset = request.query_params.get("offset", 1)

        new_reports_unfiltered_adults = new_reports_unfiltered_adults.filter(ia_filter_1__lte=float(aithr))

        new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

        if type == 'adult':
            new_reports_unfiltered = new_reports_unfiltered_adults
        elif type == 'site':
            new_reports_unfiltered = new_reports_unfiltered_sites
        if visibility == 'visible':
            new_reports_unfiltered = new_reports_unfiltered.exclude(hide=True)
        elif visibility == 'hidden':
            new_reports_unfiltered = new_reports_unfiltered.exclude(hide=False)
        if note != '':
            new_reports_unfiltered = new_reports_unfiltered.filter(note__icontains=note)
        if country and country != '' and country != 'all':
            new_reports_unfiltered = new_reports_unfiltered.filter(country__gid=int(country))
        elif country == 'all' and country_exclude != '':
            new_reports_unfiltered = new_reports_unfiltered.exclude(country__gid=int(country_exclude))

        report_id_deleted_reports_adults = Report.objects.filter(version_UUID__in=RawSQL(
            "select \"version_UUID\" from tigaserver_app_report r, (select report_id, user_id, count(\"version_UUID\") from tigaserver_app_report where type = 'adult' and report_id in (select distinct report_id from tigaserver_app_report where version_number = -1) group by report_id, user_id having count(\"version_UUID\") >1) as deleted where r.report_id = deleted.report_id and r.user_id = deleted.user_id",
            ())).values("version_UUID").distinct()
        report_id_deleted_reports_sites = Report.objects.filter(version_UUID__in=RawSQL(
            "select \"version_UUID\" from tigaserver_app_report r, (select report_id, user_id, count(\"version_UUID\") from tigaserver_app_report where type = 'site' and report_id in (select distinct report_id from tigaserver_app_report where version_number = -1) group by report_id, user_id having count(\"version_UUID\") >1) as deleted where r.report_id = deleted.report_id and r.user_id = deleted.user_id",
            ())).values("version_UUID").distinct()

        new_reports_unfiltered = new_reports_unfiltered.exclude(
            version_UUID__in=report_id_deleted_reports_adults).exclude(version_UUID__in=report_id_deleted_reports_sites)

        new_reports_unfiltered = new_reports_unfiltered.filter(version_UUID__in=RawSQL(
            "select \"version_UUID\" from tigaserver_app_report r,(select report_id,max(version_number) as higher from tigaserver_app_report where type = 'adult' group by report_id) maxes where r.type = 'adult' and r.report_id = maxes.report_id and r.version_number = maxes.higher union select \"version_UUID\" from tigaserver_app_report r, (select report_id,max(version_number) as higher from tigaserver_app_report where type = 'site' group by report_id) maxes where r.type = 'site' and r.report_id = maxes.report_id and r.version_number = maxes.higher",
            ()))

        #results = new_reports_unfiltered.prefetch_related('photos','users')
        results = new_reports_unfiltered.select_related('user').prefetch_related('photos')

        try:
            paginator = Paginator(results, limit)
        except:
            paginator = Paginator(results, limit)

        if bookmark_report is not None:
            index = results.filter(creation_time__gt=bookmark_report.creation_time).count()
            offset = int(index / int(limit)) + (index % int(limit) > 0)
            if offset == 0:
                offset = 1

        try:
            results = paginator.page(offset)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(1)


        api_count = paginator.count
        api_next = None if not results.has_next() else results.next_page_number()
        api_previous = None if not results.has_previous() else results.previous_page_number()

        #serializer = ReportSerializer(results, many=True)
        serializer = CoarseReportSerializer(results, many=True)

        data = {
            'per_page': limit,
            'count_pages': paginator.num_pages,
            'current': offset,
            'count': api_count,
            'next': api_next,
            'previous': api_previous,
            'results': serializer.data
        }

        if current_text_filter is not None:
            data['filter'] = current_text_filter

        return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
def user_favorites(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id', -1)
        if user_id == -1:
            raise ParseError(detail='user_id param is mandatory')
        user = get_object_or_404(User, pk=user_id)
        favorites = FavoritedReports.objects.filter(user=user).values('report__version_UUID')
        retval = [ f['report__version_UUID'] for f in favorites]
        return Response(retval, status=status.HTTP_200_OK)