from django.urls import reverse

from rest_framework import serializers

from mosquito_alert.api.v0.serializers import NotificationContentSerializer
from mosquito_alert.tigaserver_app.models import Notification, NotificationTopic, SentNotification
from mosquito_alert.tigacrafting.models import Alert

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