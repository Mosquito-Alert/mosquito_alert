from collections import OrderedDict
from typing import Optional, Union
from rest_framework import serializers
from taggit.models import Tag
from tigaserver_app.models import Notification, NotificationContent, NotificationTopic, SentNotification, TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration, CoverageArea, CoverageAreaMonth, Session, EuropeCountry, OWCampaigns, OrganizationPin, AcknowledgedNotification, UserSubscription
from tigacrafting.models import Alert
from django.contrib.auth.models import User
from tigaserver_app.questions_table import data as the_translation_key
from django.urls import reverse
from django.db import models
from django.utils import timezone

from .fields import AutoTimeZoneDatetimeField
from .mixins import AutoTimeZoneOrInstantUploadSerializerMixin

def score_label(score):
    if score > 66:
        return "user_score_pro"
    elif 33 < score <= 66:
        return "user_score_advanced"
    else:
        return "user_score_beginner"

'''
recipient is the TigaUser to which the notification will be displayed
'''
def custom_render_notification(sent_notification, recipìent, locale):
    expert_comment = sent_notification.notification.notification_content.get_title(language_code=locale)
    expert_html = sent_notification.notification.notification_content.get_body_html(language_code=locale)

    ack = False
    if recipìent is not None:
        ack = AcknowledgedNotification.objects.filter(user=recipìent,notification=sent_notification.notification).exists()

    this_content = {
        'id': sent_notification.notification.id,
        'report_id': sent_notification.notification.report.version_UUID if sent_notification.notification.report is not None else None,
        'user_id': sent_notification.sent_to_user.user_UUID if sent_notification.sent_to_user is not None else None,
        'topic': sent_notification.sent_to_topic.topic_code if sent_notification.sent_to_topic is not None else None,
        'user_score': sent_notification.sent_to_user.score if sent_notification.sent_to_user is not None else None,
        'user_score_label': score_label(sent_notification.sent_to_user.score) if sent_notification.sent_to_user is not None else None,
        'expert_id': sent_notification.notification.expert.id,
        'date_comment': sent_notification.notification.date_comment,
        'expert_comment': expert_comment,
        'expert_html': expert_html,
        'acknowledged': ack,
        'public': sent_notification.notification.public,
    }
    return this_content

class UserSerializer(serializers.ModelSerializer):

    user_UUID = serializers.UUIDField(required=True)

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

    translated_question = serializers.SerializerMethodField()
    translated_answer = serializers.SerializerMethodField()

    class Meta:
        model = ReportResponse
        fields = '__all__'

    def get_translated_question(self, obj):
        report_lang = obj.report.app_language
        lang_table = the_translation_key.get(report_lang, the_translation_key['en'])
        return lang_table.get(obj.question,'')

    def get_translated_answer(self, obj):
        report_lang = obj.report.app_language
        lang_table = the_translation_key.get(report_lang, the_translation_key['en'])
        return lang_table.get(obj.answer, '')


class ReportResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportResponse
        fields = ['question', 'answer', 'question_id', 'answer_id', 'answer_value']

class DetailedPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'photo', 'uuid']
class ReportSerializer(AutoTimeZoneOrInstantUploadSerializerMixin, serializers.ModelSerializer):

    # For AutoTimeZoneOrInstantUploadSerializerMixin
    CLIENT_CREATION_FIELD = 'version_time'

    user = UserListingField
    version_UUID = serializers.CharField()
    version_number = serializers.IntegerField()
    report_id = serializers.CharField()
    phone_upload_time = AutoTimeZoneDatetimeField()
    creation_time = AutoTimeZoneDatetimeField()
    version_time = AutoTimeZoneDatetimeField()
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
    photos = DetailedPhotoSerializer(many=True, read_only=True)

    def _get_dict_applied_tz(self, data: OrderedDict, *args, **kwargs) -> OrderedDict:
        data_result = super()._get_dict_applied_tz(data=data, *args, **kwargs)

        # If version_time is in data_result, that means that TZ has been applied.
        if "version_time" in data_result:
            version_time_field = self.fields['version_time']
            _original_version_time = version_time_field.run_validation(
                data=version_time_field.get_value(data)
            )
            data_result["datetime_fix_offset"] = (
                data_result["version_time"] - timezone.make_aware(_original_version_time)
            ).total_seconds()

        return data_result

    def _get_fields_to_apply_tz_from_instant_upload(self, data) -> list:
        # This are fields to apply only if using the TZ from instant upload approach.
        field_names = super()._get_fields_to_apply_tz_from_instant_upload(data=data)

        # If version_number is not 0
        # and version_time when not aware on the POST request.
        if data['version_number'] != 0 and not timezone.is_aware(data['version_time']):
            # Apply version_time after getting tz from the instant upload approach.
            if "version_time" not in field_names:
                field_names.append('version_time')

        return field_names

    def _get_fields_to_apply_tz(self, data) -> list:
        # This are fields to apply only if using the TZ from location.
        field_names = super()._get_fields_to_apply_tz(data=data)

        if data['version_number'] != 0:
            # Removing creation_time and phone_upload_time
            # since they must be the same than the original version
            field_names = list(set(field_names) - set(['phone_upload_time', 'creation_time']))

            # If it's been more than 1 day between the original
            # version of the report and this report version, we consider
            # we can not waranty the user have moved and possibly
            # changed its timezone. So, remove version_time too
            # from the candidate list.
            original_version_upload_time = timezone.make_aware(data['phone_upload_time'], is_dst=False) if not timezone.is_aware(data['phone_upload_time']) else data['phone_upload_time']
            current_version_upload_time = timezone.make_aware(data['version_time'], is_dst=False) if not timezone.is_aware(data['version_time']) else data['version_time']
            if abs(original_version_upload_time - current_version_upload_time).total_seconds() > 24 * 3600:
                field_names = list(set(field_names) - set(['version_time']))

        return field_names

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

    def create(self, validated_data):
        # Adding _history_user
        validated_data['_history_user'] = validated_data.get('user')

        responses_data = validated_data.pop('responses')
        report = Report(**validated_data)

        # Create the report response and updating report fields
        # without saving. We want to save all changes at once.
        responses = []
        for response in responses_data:
            report_responses = ReportResponse(
                report=report, **response
            )
            report_responses._update_report_value(
                commit=False
            )
            responses.append(report_responses)

        # Saving reports (already updated) + responses.
        report.save()
        for response in responses:
            response.save(skip_report_update=True)

        return report

    def update(self, instance, validated_data):
        # Adding _history_user
        validated_data['_history_user'] = validated_data.get('user')

        # Do not updates on the following fields:
        #   - fields marked as non editable
        #   - fields Auto generated
        #   - FKs
        #   - PKs
        non_editable_fields = [
            field.name for field in Report._meta.get_fields() if (
                not field.editable
                or isinstance(field, models.AutoField)
                or isinstance(field, models.ForeignKey)
                or field.primary_key
            )
        ]

        responses_data = validated_data.pop('responses')
        for field in non_editable_fields:
            if field in validated_data:
                del validated_data[field]

        # Create/update the report response and updating report fields
        # without saving. We want to save all changes at once.
        responses = []
        for response in responses_data:
            try:
                report_response = ReportResponse.objects.get(
                    report=instance, question=response['question']
                )
                # Perform update
                for k, v in response.items():
                    setattr(report_response, k, v)
            except ReportResponse.DoesNotExist:
                report_response = ReportResponse(report=instance, **response)

            report_response._update_report_value(
                commit=False
            )
            responses.append(report_response)

        # Saving reports (already updated) + responses.
        instance = super().update(instance=instance, validated_data=validated_data)

        for response in responses:
            response.save(skip_report_update=True)

        return instance

    class Meta:
        model = Report
        depth = 0
        fields = (
            "version_UUID",
            "version_number",
            "report_id",
            "phone_upload_time",
            "creation_time",
            "version_time",
            "type",
            "location_choice",
            "current_location_lon",
            "current_location_lat",
            "selected_location_lon",
            "selected_location_lat",
            "note",
            "package_name",
            "package_version",
            "device_manufacturer",
            "device_model",
            "os",
            "os_version",
            "os_language",
            "app_language",
            "responses",
            "photos",
            "updated_at",
            "server_upload_time",
            "datetime_fix_offset",
            "hide",
            "point",
            "nuts_2",
            "nuts_3",
            "user",
            "mission",
            "country",
            "session"
        )


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

class FixSerializer(AutoTimeZoneOrInstantUploadSerializerMixin, serializers.ModelSerializer):

    # For AutoTimeZoneOrInstantUploadSerializerMixin
    CLIENT_CREATION_FIELD = 'phone_upload_time'

    fix_time = AutoTimeZoneDatetimeField()
    phone_upload_time = AutoTimeZoneDatetimeField()

    class Meta:
        model = Fix
        fields = ['user_coverage_uuid', 'fix_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power', 'mask_size']


class ConfigurationSerializer(serializers.ModelSerializer):
    samples_per_day = serializers.IntegerField(help_text='Number of samples.')
    creation_time = serializers.DateTimeField(help_text='Creation time help', read_only=True)

    class Meta:
        model = Configuration
        fields = '__all__'


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
        fields = (
            "version_UUID",
            "version_number",
            "report_id",
            "phone_upload_time",
            "creation_time",
            "version_time",
            "type",
            "location_choice",
            "current_location_lon",
            "current_location_lat",
            "selected_location_lon",
            "selected_location_lat",
            "note",
            "package_name",
            "package_version",
            "device_manufacturer",
            "device_model",
            "os",
            "os_version",
            "os_language",
            "app_language",
            "responses",
            "photos",
            "updated_at",
            "server_upload_time",
            "datetime_fix_offset",
            "hide",
            "point",
            "nuts_2",
            "nuts_3",
            "user",
            "mission",
            "country",
            "session"
        )


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
                   'type','creation_time', 'timezone')


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
    latest_version = serializers.SerializerMethodField()
    visible = serializers.ReadOnlyField()
    n_photos = serializers.ReadOnlyField()
    final_expert_status_text = serializers.SerializerMethodField(method_name='get_final_expert_status')
    responses = FullReportResponseSerializer(many=True)
    country = serializers.SerializerMethodField(method_name='get_country')

    def get_final_expert_status(self, obj):
        return obj.get_final_expert_status()

    def get_latest_version(self, obj):
        return True

    def get_country(self,obj):
        if obj.country is None:
            return None
        else:
            return obj.country.iso3_code

    class Meta:
        model = Report
        fields = (
            'version_UUID',
            'creation_time',
            'creation_date',
            'creation_day_since_launch',
            'creation_year',
            'creation_month',
            'site_cat',
            'type',
            'lon',
            'lat',
            'location_is_masked',
            'movelab_annotation',
            'movelab_annotation_euro',
            'tiger_responses',
            'tiger_responses_text',
            'site_responses',
            'site_responses_text',
            'tigaprob_cat',
            'latest_version',
            'visible',
            'n_photos',
            'final_expert_status_text',
            'responses',
            'country',
            'updated_at',
            'datetime_fix_offset',
            'point',
            'nuts_2',
            'nuts_3',
            'cached_visible',
            'session',
        )


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
        exclude = ('version_UUID', 'version_number', 'user', 'report_id', 'server_upload_time', 'phone_upload_time', 'version_time', 'location_choice', 'current_location_lon', 'current_location_lat', 'mission', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'hide', 'timezone')


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
    body_html_en = serializers.CharField()
    title_en = serializers.CharField()
    body_html_native = serializers.CharField(required=False)
    title_native = serializers.CharField(required=False)
    native_locale = serializers.CharField(required=False)
    notification_label = serializers.CharField(required=False)

    class Meta:
        model = NotificationContent
        fields = ('id', 'body_html_en', 'body_html_native', 'title_en', 'title_native', 'native_locale', 'notification_label')


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
    map_notification = serializers.BooleanField()

    class Meta:
        model = Notification
        #fields = ('id', 'report_id', 'user_id', 'expert_id', 'date_comment', 'expert_comment', 'expert_html', 'acknowledged', 'notification_content')
        #fields = ('id', 'report_id', 'user_id', 'expert_id', 'date_comment', 'acknowledged','notification_content', 'public')
        fields = ('id', 'report_id', 'expert_id', 'date_comment', 'notification_content', 'public', 'map_notification')


class DataTableAimalertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ('xvb','report_id','report_datetime','loc_code','cat_id','species','certainty','status','hit','review_species','review_status','review_datetime')


class DataTableNotificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    report_id = serializers.CharField()
    expert_id = serializers.IntegerField()
    date_comment = serializers.ReadOnlyField()
    notification_content = NotificationContentSerializer()
    public = serializers.BooleanField()
    sent_to = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'report_id', 'expert_id', 'date_comment', 'notification_content', 'public', 'sent_to', 'link')

    def get_sent_to(self,obj):
        sent_notification = SentNotification.objects.filter(notification_id = obj.id).first()

        if(sent_notification.sent_to_topic_id):
            return NotificationTopic.objects.get(id = sent_notification.sent_to_topic_id).topic_description
        else:
             return SentNotification.objects.filter(notification_id=obj.id).values_list('sent_to_user_id')

    def get_link(self,obj):
        return reverse('notification_detail', kwargs={'notification_id': obj.id})

class UserSubscriptionSerializer(serializers.ModelSerializer):
    topic_code = serializers.SerializerMethodField()

    def get_topic_code(self,obj):
        return obj.topic.topic_code

    class Meta:
        model = UserSubscription
        fields = ('id','user','topic','topic_code')


class TigaUserSerializer(serializers.ModelSerializer):

    device_token = serializers.SerializerMethodField()

    def get_device_token(self, obj) -> Optional[str]:
        return obj.device_token

    class Meta:
        model = TigaUser
        fields = ('user_UUID','registration_time','device_token','score')


class AcknowledgedNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcknowledgedNotification
        fields = '__all__'


class EuropeCountrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EuropeCountry
        fields = ('gid', 'name_engl')


class OWCampaignsSerializer(serializers.ModelSerializer):
    country = EuropeCountrySimpleSerializer(many=False)

    class Meta:
        model = OWCampaigns
        fields = '__all__'


class OrganizationPinsSerializer(serializers.ModelSerializer):
    point = serializers.SerializerMethodField(method_name='get_point')

    class Meta:
        model = OrganizationPin
        fields = '__all__'

    def get_point(self,obj):
        if obj.point is not None:
            return { "lat": obj.point.y, "long": obj.point.x}
        else:
            return None

class CoarsePhotoSerializer(serializers.ModelSerializer):
    small_url = serializers.SerializerMethodField(method_name='get_small_url')

    def get_small_url(self,obj):
        return obj.get_small_url()
    class Meta:
        model = Photo
        fields = ['id', 'photo', 'uuid', 'small_url']

class CoarseReportSerializer(serializers.ModelSerializer):
    photos = CoarsePhotoSerializer(many=True)
    version_UUID = serializers.ReadOnlyField()
    report_id = serializers.ReadOnlyField()
    creation_time = serializers.ReadOnlyField()
    user_id = serializers.SerializerMethodField(method_name='get_user_id')
    type = serializers.ReadOnlyField()
    note = serializers.ReadOnlyField()
    country = EuropeCountrySimpleSerializer(many=False)
    site_cat = serializers.SerializerMethodField(method_name='get_site_cat')
    insect_confidence = serializers.SerializerMethodField()
    hide = serializers.ReadOnlyField()
    lat = serializers.ReadOnlyField()
    lon = serializers.ReadOnlyField()

    def get_insect_confidence(self, obj) -> Union[float, None]:
        if not obj.prediction:
            return None

        return obj.prediction.photo_prediction.insect_confidence

    def get_site_cat(self,obj):
        return obj.site_cat

    def get_user_id(self,obj):
        return obj.user.user_UUID

    class Meta:
        model = Report
        fields = ('photos', 'version_UUID', 'report_id', 'creation_time', 'type', 'note', 'point', 'country', 'site_cat', 'insect_confidence', 'hide', 'user_id', 'lat', 'lon')