from rest_framework import serializers
from taggit.models import Tag
from tigaserver_app.models import Notification, NotificationContent, TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration, CoverageArea, CoverageAreaMonth, TigaProfile, Session
from django.contrib.auth.models import User

def score_label(score):
    if score > 66:
        return "user_score_pro"
    elif 33 < score <= 66:
        return "user_score_advanced"
    else:
        return "user_score_beginner"

def custom_render_notification(notification,locale):
    expert_comment = notification.notification_content.get_title_locale_safe(locale)
    expert_html = notification.notification_content.get_body_locale_safe(locale)
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

class UserSerializer(serializers.ModelSerializer):

    def validate_user_UUID(self, attrs):
        """
        Check that the user_UUID has exactly 36 characters.
        """
        value = attrs
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
    # id = serializers.IntegerField()
    # title_catalan = serializers.CharField()
    # title_spanish = serializers.CharField()
    # title_english = serializers.CharField()
    # short_description_catalan = serializers.CharField()
    # short_description_spanish = serializers.CharField()
    # short_description_english = serializers.CharField()
    # long_description_catalan = serializers.CharField()
    # long_description_spanish = serializers.CharField()
    # long_description_english = serializers.CharField()
    # help_text_catalan = serializers.CharField()
    # help_text_spanish = serializers.CharField()
    # help_text_english = serializers.CharField()
    # creation_time = serializers.DateTimeField()
    # expiration_time = serializers.DateTimeField()
    # platform = serializers.CharField()
    # url = serializers.URLField()
    # photo_mission = serializers.BooleanField()
    # items = MissionItemSerializer(many=True)
    # triggers = MissionTriggerSerializer(many=True)
    # mission_version = serializers.IntegerField()
    id = serializers.ReadOnlyField()
    title_catalan = serializers.ReadOnlyField()
    title_spanish = serializers.ReadOnlyField()
    title_english = serializers.ReadOnlyField()
    short_description_catalan = serializers.ReadOnlyField()
    short_description_spanish = serializers.ReadOnlyField()
    short_description_english = serializers.ReadOnlyField()
    long_description_catalan = serializers.ReadOnlyField()
    long_description_spanish = serializers.ReadOnlyField()
    long_description_english = serializers.ReadOnlyField()
    help_text_catalan = serializers.ReadOnlyField()
    help_text_spanish = serializers.ReadOnlyField()
    help_text_english = serializers.ReadOnlyField()
    creation_time = serializers.ReadOnlyField()
    expiration_time = serializers.ReadOnlyField()
    platform = serializers.ReadOnlyField()
    url = serializers.ReadOnlyField()
    photo_mission = serializers.ReadOnlyField()
    items = MissionItemSerializer(many=True)
    triggers = MissionTriggerSerializer(many=True)
    mission_version = serializers.ReadOnlyField()

    class Meta:
        model = Mission
        fields = '__all__'


class SessionListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.id


class UserListingField(serializers.RelatedField):

    def to_native(self, value):
        return value.user_UUID


class MissionListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.mission_id


class ReportListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.version_UUID


class FullReportResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportResponse
        fields = '__all__'


class ReportResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportResponse
        fields = ['question', 'answer', 'question_id', 'answer_id', 'answer_value']

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
    note = serializers.CharField(required=False, allow_blank=True)
    package_name = serializers.CharField(required=False)
    package_version = serializers.IntegerField(required=False)
    device_manufacturer = serializers.CharField(required=False)
    device_model = serializers.CharField(required=False)
    os = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)
    os_language = serializers.CharField(required=False)
    app_language = serializers.CharField(required=False)
    responses = ReportResponseSerializer(many=True)
    session = SessionListingField

    def validate_report_UUID(self, attrs):
        """
        Check that the user_UUID has exactly 36 characters.
        """
        value = attrs
        if len(str(value)) != 36:
            raise serializers.ValidationError("Make sure report_UUID is EXACTLY 36 characters.")
        return attrs

    def validate_type(self, attrs):
        """
        Check that the report type is either 'adult', 'site', or 'mission'.
        """
        value = attrs
        if value not in ['adult', 'site', 'mission', 'bite']:
            raise serializers.ValidationError("Make sure type is 'adult', 'site', 'mission' or 'bite'.")
        return attrs

    def create(self,validated_data):
        responses_data = validated_data.pop('responses')
        report = Report.objects.create(**validated_data)
        for response in responses_data:
            ReportResponse.objects.create(report=report, **response)
        return report

    class Meta:
        model = Report
        depth = 0
        fields = '__all__'


class PhotoSerializer(serializers.ModelSerializer):
    report = ReportListingField

    class Meta:
        model = Photo
        depth = 0
        fields = ['photo', 'report']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'session_ID', 'user', 'session_start_time', 'session_end_time']

class FixSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fix
        fields = ['user_coverage_uuid', 'fix_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power', 'mask_size']


class ConfigurationSerializer(serializers.ModelSerializer):
    samples_per_day = serializers.IntegerField(help_text='Number of samples.')
    creation_time = serializers.DateTimeField(help_text='Creation time help', read_only=True)

    class Meta:
        model = Configuration
        fields = '__all__'

class DetailedPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'photo', 'uuid']

class NearbyReportSerializer(serializers.ModelSerializer):
    user = UserListingField
    version_UUID = serializers.CharField()
    version_number = serializers.IntegerField()
    report_id = serializers.CharField()
    server_upload_time = serializers.ReadOnlyField()
    phone_upload_time = serializers.DateTimeField()
    creation_time = serializers.DateTimeField()
    version_time = serializers.DateTimeField()
    type = serializers.CharField()
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
    simplified_annotation = serializers.ReadOnlyField()
    photos = DetailedPhotoSerializer(many=True)

    class Meta:
        model = Report
        fields = '__all__'


'''
class NearbyReportSerializer(serializers.ModelSerializer):
    version_UUID = serializers.ReadOnlyField()
    lon = serializers.ReadOnlyField()
    lat = serializers.ReadOnlyField()
    simplified_annotation = serializers.ReadOnlyField()

    class Meta:
        model = Report
        fields = ['version_UUID','lon','lat','simplified_annotation']
        # exclude = ('version_number', 'user', 'report_id','creation_time','server_upload_time', 'phone_upload_time', 'version_time',
        #            'location_choice', 'current_location_lon', 'current_location_lat', 'mission',
        #            'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version',
        #            'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide',
        #            'type','point')
'''

class ReportIdSerializer(serializers.ModelSerializer):
    version_UUID = serializers.CharField()
    class Meta:
        model = Report
        exclude = ('version_number', 'user', 'report_id', 'server_upload_time', 'phone_upload_time', 'version_time',
                   'location_choice', 'current_location_lon', 'current_location_lat', 'mission',
                   'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version',
                   'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide',
                   'type','creation_time')


class MapDataSerializer(serializers.ModelSerializer):
    version_UUID = serializers.CharField()
    #creation_time = serializers.DateTimeField()
    creation_time = serializers.ReadOnlyField()
    #creation_date = serializers.DateTimeField()
    creation_date = serializers.ReadOnlyField()
    creation_day_since_launch = serializers.ReadOnlyField()
    creation_year = serializers.ReadOnlyField()
    creation_month = serializers.ReadOnlyField()
    site_cat = serializers.ReadOnlyField()
    type = serializers.CharField()
    lon = serializers.ReadOnlyField()
    lat = serializers.ReadOnlyField()
    movelab_annotation = serializers.ReadOnlyField()
    movelab_annotation_euro = serializers.ReadOnlyField()
    tiger_responses = serializers.ReadOnlyField()
    tiger_responses_text = serializers.ReadOnlyField()
    site_responses = serializers.ReadOnlyField()
    site_responses_text = serializers.ReadOnlyField()
    tigaprob_cat = serializers.ReadOnlyField()
    visible = serializers.ReadOnlyField()
    latest_version = serializers.ReadOnlyField()
    n_photos = serializers.ReadOnlyField()
    final_expert_status_text = serializers.ReadOnlyField()
    responses = FullReportResponseSerializer(many=True)

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

class NotificationContentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    body_html_es = serializers.CharField()
    body_html_ca = serializers.CharField(required=False)
    body_html_en = serializers.CharField(required=False)
    title_es = serializers.CharField()
    title_ca = serializers.CharField(required=False)
    title_en = serializers.CharField(required=False)

    class Meta:
        model = NotificationContent
        fields = ('id', 'body_html_es', 'body_html_ca', 'body_html_en', 'title_es', 'title_ca', 'title_en')
        #fields = ('id', 'body_html_es', 'title_es')

class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    report_id = serializers.CharField()
    user_id = serializers.CharField()
    expert_id = serializers.IntegerField()
    date_comment = serializers.Field()
    #expert_comment = serializers.CharField()
    #expert_html = serializers.CharField()
    photo_url = serializers.CharField()
    acknowledged = serializers.BooleanField()
    notification_content = NotificationContentSerializer()
    public = serializers.BooleanField()

    class Meta:
        model = Notification
        #fields = ('id', 'report_id', 'user_id', 'expert_id', 'date_comment', 'expert_comment', 'expert_html', 'acknowledged', 'notification_content')
        fields = ('id', 'report_id', 'user_id', 'expert_id', 'date_comment', 'acknowledged','notification_content', 'public')


class TigaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TigaUser
        fields = ('user_UUID','registration_time','device_token','score')


class TigaProfileSerializer(serializers.ModelSerializer):
    profile_devices = TigaUserSerializer(many=True)

    class Meta:
        model = TigaProfile
        fields = ('id', 'firebase_token', 'score', 'profile_devices')


class DetailedReportSerializer(serializers.ModelSerializer):

    photos = DetailedPhotoSerializer(many=True)
    user = UserListingField
    version_UUID = serializers.ReadOnlyField()
    version_number = serializers.ReadOnlyField()
    report_id = serializers.ReadOnlyField()
    phone_upload_time = serializers.ReadOnlyField()
    creation_time = serializers.ReadOnlyField()
    version_time = serializers.ReadOnlyField()
    type = serializers.ReadOnlyField()
    location_choice = serializers.ReadOnlyField()
    current_location_lon = serializers.ReadOnlyField()
    current_location_lat = serializers.ReadOnlyField()
    selected_location_lon = serializers.ReadOnlyField()
    selected_location_lat = serializers.ReadOnlyField()
    note = serializers.ReadOnlyField()
    package_name = serializers.ReadOnlyField()
    package_version = serializers.ReadOnlyField()
    device_manufacturer = serializers.ReadOnlyField()
    device_model = serializers.ReadOnlyField()
    os = serializers.ReadOnlyField()
    os_version = serializers.ReadOnlyField()
    os_language = serializers.ReadOnlyField()
    app_language = serializers.ReadOnlyField()
    responses = ReportResponseSerializer(many=True)
    point = serializers.SerializerMethodField(method_name='get_point')

    class Meta:
        model = Report
        fields = '__all__'

    def get_point(self,obj):
        if obj.point is not None:
            return { "lat": obj.point.y, "long": obj.point.x}
        else:
            return None



class DetailedTigaUserSerializer(serializers.ModelSerializer):
    user_reports = DetailedReportSerializer(many=True)

    class Meta:
        model = TigaUser
        fields = ('user_UUID','registration_time','device_token','score','user_reports')


class DetailedTigaProfileSerializer(serializers.ModelSerializer):
    profile_devices = DetailedTigaUserSerializer(many=True)

    class Meta:
        model = TigaProfile
        fields = ('id', 'firebase_token', 'score', 'profile_devices')