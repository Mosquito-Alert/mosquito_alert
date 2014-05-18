from rest_framework import serializers
from tigaserver_app.models import TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration


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

    class Meta:
        model = Mission


class UserListingField(serializers.RelatedField):

    def to_native(self, value):
        return value.user_UUID


class MissionListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.mission_id


class ReportSerializer(serializers.ModelSerializer):
    user = UserListingField
    mission = MissionListingField

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
        if value not in ['adult', 'type', 'mission']:
            raise serializers.ValidationError("Make sure type is 'adult', 'site', or 'mission'.")
        return attrs

    class Meta:
        model = Report
        depth = 0


class ReportListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.version_UUID


class ReportResponseSerializer(serializers.ModelSerializer):
    report = ReportListingField

    class Meta:
        model = ReportResponse
        fields = ['report', 'question', 'answer']


class PhotoSerializer(serializers.ModelSerializer):
    report = ReportListingField

    class Meta:
        model = Photo
        depth = 0
        fields = ['photo', 'report']


class FixSerializer(serializers.ModelSerializer):
    user = UserListingField
#    fix_time = serializers.DateTimeField()
#    phone_upload_time = serializers.DateTimeField()
#    masked_lon = serializers.FloatField()
#    masked_lat = serializers.FloatField()

    class Meta:
        model = Fix
        depth = 0
        fields = ['user', 'fix_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power']


class ConfigurationSerializer(serializers.ModelSerializer):
    samples_per_day = serializers.IntegerField(help_text='Number of samples.')
    creation_time = serializers.DateTimeField(help_text='Creation time help', read_only=True)

    class Meta:
        model = Configuration
