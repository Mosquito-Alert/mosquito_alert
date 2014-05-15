from rest_framework import serializers
from tigaserver_app.models import Report, TigaUser, Mission, Photo


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = TigaUser
        fields = ['user_UUID']


class MissionSerializer(serializers.HyperlinkedModelSerializer):
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

    class Meta:
        model = Report
        depth = 0
        fields = ['user',
                  'report_id',
                  'version_UUID',
                  'version_number',
                  'server_upload_time',
                  'phone_upload_time',
                  'creation_time',
                  'version_time',
                  'type',
                  'mission',
                  'confirmation',
                  'confirmation_code',
                  'location_choice',
                  'current_location_lon',
                  'current_location_lat',
                  'selected_location_lon',
                  'selected_location_lat',
                  'note',
                  'package_name',
                  'package_version',
                  'phone_manufacturer',
                  'phone_model',
                  'os',
                  'os_version']


class ReportListingField(serializers.RelatedField):
    def to_native(self, value):
        return value.version_UUID


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    report = ReportListingField

    class Meta:
        model = Photo
        depth = 0
        fields = ['photo', 'report']
