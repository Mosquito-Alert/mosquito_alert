from rest_framework import serializers
from taggit.models import Tag
from tigaserver_app.models import Notification, TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration, CoverageArea, CoverageAreaMonth
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):

    def validate_user_UUID(self, attrs, source):
        """
        Check that the user_UUID has exactly 36 characters.
        """
        value = attrs[source]
        if len(str(value)) != 36:
            raise serializers.ValidationError("Make sure user_UUID is EXACTLY 36 characters.")
        return attrs

    class Meta:
        model = TigaUser
        fields = ['user_UUID', ]


class MissionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionItem


class MissionTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionTrigger


class MissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    title_catalan = serializers.CharField()
    title_spanish = serializers.CharField()
    title_english = serializers.CharField()
    short_description_catalan = serializers.CharField()
    short_description_spanish = serializers.CharField()
    short_description_english = serializers.CharField()
    long_description_catalan = serializers.CharField()
    long_description_spanish = serializers.CharField()
    long_description_english = serializers.CharField()
    help_text_catalan = serializers.CharField()
    help_text_spanish = serializers.CharField()
    help_text_english = serializers.CharField()
    creation_time = serializers.DateTimeField()
    expiration_time = serializers.DateTimeField()
    platform = serializers.CharField()
    url = serializers.URLField()
    photo_mission = serializers.BooleanField()
    items = MissionItemSerializer(many=True)
    triggers = MissionTriggerSerializer(many=True)
    mission_version = serializers.IntegerField()

    class Meta:
        model = Mission


class UserListingField(serializers.RelatedField):

    def to_native(self, value):
        return value.user_UUID


class MissionListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.mission_id


class ReportListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.version_UUID


class ReportResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportResponse
        fields = ['question', 'answer']

class ReportSerializer(serializers.ModelSerializer):

    user = UserListingField
    version_UUID = serializers.CharField()
    version_number = serializers.IntegerField()
    report_id = serializers.CharField()
    phone_upload_time = serializers.DateTimeField()
    creation_time = serializers.DateTimeField()
    version_time = serializers.DateTimeField()
    type = serializers.CharField()
    mission = MissionListingField
    location_choice = serializers.CharField()
    current_location_lon = serializers.FloatField(required=False)
    current_location_lat = serializers.FloatField(required=False)
    selected_location_lon = serializers.FloatField(required=False)
    selected_location_lat = serializers.FloatField(required=False)
    note = serializers.CharField(required=False)
    package_name = serializers.CharField(required=False)
    package_version = serializers.IntegerField(required=False)
    device_manufacturer = serializers.CharField(required=False)
    device_model = serializers.CharField(required=False)
    os = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)
    os_language = serializers.CharField(required=False)
    app_language = serializers.CharField(required=False)
    responses = ReportResponseSerializer(many=True)

    def validate_report_UUID(self, attrs, source):
        """
        Check that the user_UUID has exactly 36 characters.
        """
        value = attrs[source]
        if len(str(value)) != 36:
            raise serializers.ValidationError("Make sure report_UUID is EXACTLY 36 characters.")
        return attrs

    def validate_type(self, attrs, source):
        """
        Check that the report type is either 'adult', 'site', or 'mission'.
        """
        value = attrs[source]
        if value not in ['adult', 'site', 'mission']:
            raise serializers.ValidationError("Make sure type is 'adult', 'site', or 'mission'.")
        return attrs

    class Meta:
        model = Report
        depth = 0


class PhotoSerializer(serializers.ModelSerializer):
    report = ReportListingField

    class Meta:
        model = Photo
        depth = 0
        fields = ['photo', 'report']


class FixSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fix
        fields = ['user_coverage_uuid', 'fix_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power']


class ConfigurationSerializer(serializers.ModelSerializer):
    samples_per_day = serializers.IntegerField(help_text='Number of samples.')
    creation_time = serializers.DateTimeField(help_text='Creation time help', read_only=True)

    class Meta:
        model = Configuration

class NearbyReportSerializer(serializers.ModelSerializer):
    version_UUID = serializers.CharField()
    lon = serializers.Field()
    lat = serializers.Field()
    simplified_annotation = serializers.Field()
    class Meta:
        model = Report
        exclude = ('version_number', 'user', 'report_id', 'server_upload_time', 'phone_upload_time', 'version_time',
                   'location_choice', 'current_location_lon', 'current_location_lat', 'mission',
                   'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version',
                   'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide', 'type')
class MapDataSerializer(serializers.ModelSerializer):
    version_UUID = serializers.CharField()
    creation_time = serializers.DateTimeField()
    creation_date = serializers.DateTimeField()
    creation_day_since_launch = serializers.Field()
    creation_year = serializers.Field()
    creation_month = serializers.Field()
    site_cat = serializers.Field()
    type = serializers.CharField()
    lon = serializers.Field()
    lat = serializers.Field()
    movelab_annotation = serializers.Field()
    tiger_responses = serializers.Field()
    tiger_responses_text = serializers.Field()
    site_responses = serializers.Field()
    site_responses_text = serializers.Field()
    tigaprob_cat = serializers.Field()
    visible = serializers.Field()
    latest_version = serializers.Field()
    n_photos = serializers.Field()
    final_expert_status_text = serializers.Field()

    class Meta:
        model = Report
        exclude = ('version_number', 'user', 'report_id', 'server_upload_time', 'phone_upload_time', 'version_time', 'location_choice', 'current_location_lon', 'current_location_lat', 'mission', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide')


class SiteMapSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField()
    creation_date = serializers.DateTimeField()
    creation_day_since_launch = serializers.Field()
    type = serializers.CharField()
    lon = serializers.Field()
    lat = serializers.Field()
    site_cat = serializers.Field()

    class Meta:
        model = Report
        exclude = ('version_UUID', 'version_number', 'user', 'report_id', 'server_upload_time', 'phone_upload_time', 'version_time', 'location_choice', 'current_location_lon', 'current_location_lat', 'mission', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide')


class CoverageMapSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoverageArea
        fields = ('lat', 'lon', 'n_fixes')


class CoverageMonthMapSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoverageAreaMonth
        fields = ('lat', 'lon', 'year', 'month', 'n_fixes')

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name','username')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id','name')

class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    report_id = serializers.CharField()
    user_id = serializers.CharField()
    expert_id = serializers.IntegerField()
    date_comment = serializers.Field()
    expert_comment = serializers.CharField()
    expert_html = serializers.CharField()
    photo_url = serializers.CharField()
    acknowledged = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('id','report_id','user_id','expert_id','date_comment','expert_comment','expert_html','photo_url','acknowledged')