import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render

from rest_framework.decorators import api_view

from mosquito_alert.tigacrafting.views import generic_datatable_list_endpoint

from .models import (
    Notification,
    SentNotification,
    NotificationTopic,
    TOPIC_GROUPS,
    AcknowledgedNotification,
    UserSubscription,
)
from .serializers import DataTableNotificationSerializer


logger_notification = logging.getLogger("mosquitoalert.notification")


@login_required
def notifications_version_two(request, user_uuid=None):
    this_user = request.user
    this_user_is_notifier = this_user.groups.filter(name="expert_notifier").exists()
    if this_user_is_notifier:
        user_uuid = request.GET.get("user_uuid", None)
        # total_users = TigaUser.objects.exclude(device_token='').filter(device_token__isnull=False).count()
        # TOPIC_GROUPS = ((0, 'General'), (1, 'Language topics'), (2, 'Country topics'))
        languages = []
        sorted_langs = sorted(settings.LANGUAGES, key=lambda tup: tup[1])
        for lang in sorted_langs:
            languages.append({"code": lang[0], "name": str(lang[1])})
        all_topics = []
        for group in TOPIC_GROUPS:
            if group[0] != 5:  # exclude special topics i.e. global
                current_topics = []
                for topic in NotificationTopic.objects.filter(
                    topic_group=group[0]
                ).order_by("topic_description"):
                    current_topics.append(
                        {
                            "topic_text": topic.topic_description,
                            "topic_value": topic.topic_code,
                        }
                    )
                topic_info = {
                    "topic_group_text": group[1],
                    "topic_group_value": group[0],
                    "topics": current_topics,
                }
                all_topics.append(topic_info)
            else:
                pass
        return render(
            request,
            "notifications/notifications_version_two.html",
            {
                "user_id": this_user.id,
                "user_uuid": user_uuid,
                "topics_info": json.dumps(all_topics),
                "languages": languages,
            },
        )
    else:
        return HttpResponse(
            "You don't have permission to issue notifications from EntoLab, please contact MoveLab."
        )


@api_view(["GET"])
def user_notifications_datatable(request):
    if request.method == "GET":
        search_field_list = ("title_en", "title_native")
        sent_to_topic = (
            SentNotification.objects.filter(sent_to_topic__isnull=False)
            .values("notification_id")
            .distinct()
        )
        queryset = Notification.objects.filter(id__in=sent_to_topic).order_by(
            "-date_comment"
        )
        field_translation_list = {
            "date_comment": "date_comment",
            "title_en": "notification_content__title_en",
            "title_native": "notification_content__title_native",
        }
        sort_translation_list = {
            "date_comment": "date_comment",
            "title_en": "notification_content__title_en",
            "title_native": "notification_content__title_native",
        }
        response = generic_datatable_list_endpoint(
            request,
            search_field_list,
            queryset,
            DataTableNotificationSerializer,
            field_translation_list,
            sort_translation_list,
        )
        return response


@login_required
def notifications_table(request):
    return render(request, "notifications/notifications_table.html")


@login_required
def notification_detail(request, notification_id):
    notification_id = request.GET.get("notification_id", notification_id)
    notification = Notification.objects.get(id=notification_id)
    sent_notification = SentNotification.objects.filter(
        notification_id=notification_id
    ).first()

    def clean_list(list_obj):
        # list_obj looks like [('uuid1',),]
        return (
            str(list_obj)
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace(",,", ",")[:-1]
        )

    if sent_notification.sent_to_topic_id:  # count the number of users subscribed
        potential_audience = UserSubscription.objects.aggregate(
            count=Count("id", filter=Q(topic_id=sent_notification.sent_to_topic_id))
        )["count"]
        seen_by = AcknowledgedNotification.objects.aggregate(
            count=Count("id", filter=Q(notification_id=notification_id))
        )["count"]
    else:  # if not sent to topic then we return the user uuids
        potential_audience = clean_list(
            list(
                SentNotification.objects.filter(
                    notification_id=notification_id
                ).values_list("sent_to_user_id")
            )
        )
        seen_by = clean_list(
            list(
                AcknowledgedNotification.objects.filter(
                    notification_id=notification_id
                ).values_list("user_id")
            )
        )

        # displaying 'seen by 0 users' looks better than '[] users'
        if len(seen_by) == 0:
            seen_by = 0

    context = {
        "notification": notification,
        "potential_audience": potential_audience,
        "seen_by": seen_by,
    }
    return render(request, "notifications/notification_detail.html", context)
