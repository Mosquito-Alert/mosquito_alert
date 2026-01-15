from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import mixins, GenericAPIView
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.conf import settings
from django_filters import rest_framework as filters
from datetime import timedelta
import json
from tigaserver_app.serializers import NotificationSerializer, NotificationContentSerializer, UserSerializer, ReportSerializer, PhotoSerializer, FixSerializer, MapDataSerializer, CoverageMonthMapSerializer, TagSerializer, UserAddressSerializer, SessionSerializer, OWCampaignsSerializer, OrganizationPinsSerializer, UserSubscriptionSerializer, CoarseReportSerializer
from tigaserver_app.models import Notification, NotificationContent, TigaUser, Report, Photo, Fix, CoverageAreaMonth, Session, ExpertReportAnnotation, OWCampaigns, OrganizationPin, SentNotification, AcknowledgedNotification, NotificationTopic, UserSubscription, EuropeCountry, Categories, ReportResponse, Device
from tigacrafting.models import FavoritedReports, UserStat
from taggit.models import Tag
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page
from tigacrafting.criteria import users_with_pictures,users_with_storm_drain_pictures, users_with_score, users_with_score_range, users_with_topic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import get_template


def score_label(score):
    if score > 66:
        return "user_score_pro"
    elif 33 < score <= 66:
        return "user_score_advanced"
    else:
        return "user_score_beginner"

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
        try:
            this_report = Report.objects.get(pk=request.data['report'])
        except Report.DoesNotExist:
            return Response()
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

class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
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
    filterset_class = UserFilter


class ReportViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Report.objects.all().prefetch_related("responses", "photos")
    serializer_class = ReportSerializer
    filterset_fields = ('user', 'version_number', 'report_id', 'type')

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get the filters from the request
        is_deleted = self.request.query_params.get('is_deleted', None)

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

        return queryset

    def create(self, request, *args, **kwargs):
        # For the legacy version, mobile app only use POST.
        # Will emulate the following cases depending on the
        #    version_number used in the POST call.
        # - CREATE: Case version_number == 0
        # - UPDATE: Case version_number > 0
        # - DELETE: Case version_number == -1
        version_number = request.data.get('version_number')
        version_UUID = request.data.get('version_UUID')

        # Validate version_number and version_UUID
        if version_number is None or version_UUID is None:
            return Response(
                {"error": "version_number and version_UUID are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if version_number < -1:
            raise ValidationError({'version_number': 'Invalid version number provided.'})

        # Handle case when version_number is 0 and report already exists
        if version_number == 0 and Report.objects.filter(pk=version_UUID).exists():
            return Response(
                {"error": "Object with this PK already exists."},
                status=status.HTTP_409_CONFLICT
            )

        instance = None
        if version_number != 0:
            # Updates/deletion of the original version
            instance = get_object_or_404(
                self.get_queryset(),
                **{
                    # NOTE: version_UUID is different on every user's POST
                    #'pk': request.data.get('version_UUID'),
                    'user': request.data.get('user'),
                    'report_id': request.data.get('report_id'),
                    'type': request.data.get('type')
                }
            )
            instance._history_user = instance.user

            # May raise a permission denied
            self.check_object_permissions(self.request, instance)

        if version_number == -1:
            self.perform_destroy(instance=instance)
            serializer = self.get_serializer(instance)
        elif version_number >= 0:
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        result_data = serializer.data
        result_headers = self.get_success_headers(serializer.data)

        # NOTE: Always return 201
        # See: https://github.com/Mosquito-Alert/Mosquito-Alert-Mobile-App/blob/6c5993a230a86f958c8dca8bcfef2994a6b93ebe/lib/api/api.dart#L381
        return Response(data=result_data, status=status.HTTP_201_CREATED, headers=result_headers)

    def perform_destroy(self, instance):
        instance.soft_delete()

class PhotoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request=request, *args, **kwargs)

        # Always return 200
        # See: https://github.com/Mosquito-Alert/Mosquito-Alert-Mobile-App/blob/6c5993a230a86f958c8dca8bcfef2994a6b93ebe/lib/api/api.dart#L508
        response.status = status.HTTP_200_OK
        return response

    def perform_create(self, serializer):
        # Restrict image saving to the initial report creation only.
        # Although the mobile app generates a new version_UUID for each
        # report update or deletion, the reports are versioned, and
        # only the original UUID is preserved. If the provided UUID is not
        # found, indicating an update/deletion, image saving is bypassed.
        if not Report.objects.filter(pk=serializer.report).exists():
            return
        else:
            super().perform_create(serializer=serializer)


class FixViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for getting and posting masked location fixes.
    """
    queryset = Fix.objects.all()
    serializer_class = FixSerializer
    filterset_fields = ('user_coverage_uuid', )


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
    filterset_fields = ('id', 'user' )

    def filter_queryset(self, queryset):
        queryset = super(SessionViewSet, self).filter_queryset(queryset)
        return queryset.order_by('-session_ID')

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


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
            ack_notif = AcknowledgedNotification(user=u, notification=n)
            ack_notif.save()
            map_notif = Notification.objects.get(id=notif)
            map_notif.acknowledged = True
            map_notif.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AcknowledgedNotification.DoesNotExist:
            raise ParseError(detail='Acknowledged not found')


@api_view(['POST'])
def crisis_report_assign(request, user_id=None, country_id=None):
    if user_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if country_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    userstat = get_object_or_404(UserStat.objects.all(), pk=user_id)
    country = get_object_or_404(EuropeCountry.objects.all(), pk=country_id)

    userstat.assign_crisis_report(country=country)
    return Response(status=status.HTTP_200_OK)


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

def coverage_month_internal():
    queryset = CoverageAreaMonth.objects.all()
    serializer = CoverageMonthMapSerializer(queryset, many=True)
    return serializer.data


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

class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_class = TagFilter


@api_view(['POST'])
def token(request):
    token = request.query_params.get('token', -1)
    user_id = request.query_params.get('user_id', -1)
    if( user_id != -1 and token != -1 ):
        device, _ = Device.objects.update_or_create(
            user=get_object_or_404(TigaUser.objects.all(), pk=user_id),
            registration_id=token,
            defaults={
                'active': True,
                'active_session': True,
                'last_login': timezone.now()
            }
        )
        return Response({'token' : device.registration_id})
    else:
        raise ParseError(detail='Invalid parameters')


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
            'expert_id': notification.expert.id if notification.expert else None,
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
            ack_bool = acknowledged.lower() == 'true' if acknowledged else False
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
            ack_bool = ack.lower() == 'true' if ack else False
            this_notification.acknowledged = ack_bool
        this_notification.save()
        serializer = NotificationSerializer(this_notification)
        return Response(serializer.data)


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
            notification_estimate = UserSubscription.objects.filter(topic=topic, user__fcmdevice__active=True).count()
        elif "$" in recipients:
            ids_list = recipients.split('$')
            send_to = TigaUser.objects.filter(user_UUID__in=ids_list)
            notification_estimate = len(ids_list)
        else: #it's either a topic or a single UUID
            try:
                topic = NotificationTopic.objects.get(topic_code=recipients)
                #users subscribed to topic
                notification_estimate = UserSubscription.objects.filter(topic=topic, user__fcmdevice__active=True).count()
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
                send_response = n.send_to_topic(topic=topic, push=push)
                push_success = send_response.success
            except Exception:
                pass
        else:
            # send to recipient(s)
            for recipient in send_to:
                try:
                    batch_response = n.send_to_user(user=recipient, push=push)
                    push_success = batch_response.success_count >= 0
                except Exception:
                    pass

        results = {'non_push_estimate_num': notification_estimate, 'push_success': push_success}
        return Response(results)


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

class UserAddressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.exclude(first_name='').filter(groups__name__in=['expert','superexpert'])
    serializer_class = UserAddressSerializer
    filterset_class = UserAddressFilter


def send_unblock_email(name, email):

    send_to = (settings.ADDITIONAL_EMAIL_RECIPIENTS or []) + [email]

    subject = 'MOSQUITO ALERT - blocked report release warning'
    plaintext = get_template('tigaserver_app/report_release/report_release_template')
    context = {
        'name': name,
        'n_days': settings.ENTOLAB_LOCK_PERIOD
    }
    text_content = plaintext.render(context)
    email = EmailMessage(subject, text_content, to=send_to)
    email.send(fail_silently=True)


def delete_annotations_and_notify(annotations_qs):
    recipients = []
    for obj in annotations_qs.select_related('user'):
        if obj.user.email is not None and obj.user.email != '':
            recipients.append(obj.user)

        obj.delete()

    for r in set(recipients):
        name = r.first_name if r.first_name != '' else r.username
        email = r.email
        send_unblock_email(name, email)


@api_view(['DELETE'])
def clear_blocked_all(request):
    if request.method == 'DELETE':
        delete_annotations_and_notify(
            annotations_qs=ExpertReportAnnotation.objects.blocking()
        )

        return Response(status=status.HTTP_200_OK)


@api_view(['DELETE'])
def clear_blocked(request, username, report=None):
    if request.method == 'DELETE':
        if username is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)

        annotations_qs = user.expert_report_annotations.blocking()

        if report:
            annotations_qs = annotations_qs.filter(report=get_object_or_404(Report, pk=report))

        delete_annotations_and_notify(
            annotations_qs=annotations_qs
        )

        return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def reports_id_filtered(request):
    if request.method == 'GET':
        report_id = request.query_params.get('report_id', -1)
        if report_id == -1:
            raise ParseError(detail='report_id is mandatory')
        qs = Report.objects.filter(type='adult').non_deleted().filter(report_id__startswith=report_id).order_by('-version_time')
        serializer = ReportSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def uuid_list_autocomplete(request):
    if request.method == 'GET':
        user = request.user
        uuid = request.query_params.get('uuid', -1)

        if uuid == -1:
            raise ParseError(detail='uuid is mandatory')

        qs = ExpertReportAnnotation.objects.filter(user=user).filter(report__type='adult').filter(report__version_UUID__startswith=uuid)
        qs = qs.values('report__version_UUID').distinct()
        return Response(qs, status=status.HTTP_200_OK)

package_filter = (
        Q(package_name='Tigatrapp', creation_time__gte=settings.IOS_START_TIME) |
        Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3) |
        Q(package_name='cat.ibeji.tigatrapp') |
        Q(package_name='Mosquito Alert')
)

# this function can be called by scripts and replicates the api behaviour, without calling API. Therefore, no timeouts
def all_reports_internal(year: int):
    queryset = Report.objects.published().filter( package_filter )\
        .exclude(package_name='ceab.movelab.tigatrapp', package_version=10).filter(server_upload_time__year=year)

    serializer = MapDataSerializer(
        queryset.prefetch_related('expert_report_annotations', 'responses', 'photos').select_related('identification_task'),
        many=True
    )
    return serializer.data


def non_visible_reports_internal(year: int):
    queryset = Report.objects.published(False)

    if year is not None:
        queryset = queryset.filter(server_upload_time__year=year)

    serializer = MapDataSerializer(
        queryset.prefetch_related('expert_report_annotations', 'responses', 'photos').select_related('identification_task'),
        many=True
    )
    return serializer.data


class OWCampaignsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = OWCampaignsSerializer
    queryset = OWCampaigns.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()

        country_id = self.request.query_params.get('country_id', None)
        if country_id is not None:
            try:
                country_int = int(country_id)
                qs = qs.filter(country__gid=country_int)
            except ValueError:
                return None
        return qs


class OrganizationsPinViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = OrganizationPinsSerializer
    queryset = OrganizationPin.objects.all()



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
            ExpertReportAnnotation.create_super_expert_approval(report=report)
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
        else:
            validation_value = int(validation_value)

        ExpertReportAnnotation.create_auto_annotation(
            report=report,
            category=category,
            validation_value=validation_value
        )

        return Response(data={'message':'success', 'opcode': 0}, status=status.HTTP_200_OK)

@api_view(['GET'])
def coarse_filter_reports(request):
    if request.method == 'GET':

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

        new_reports_unfiltered_qs = Report.objects.in_coarse_filter()

        if type == 'adult':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                type=Report.TYPE_ADULT,
                identification_task__pred_insect_confidence__lte=float(aithr)
            )
        elif type == 'site':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                type=Report.TYPE_SITE
            )

        if visibility == 'visible':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(hide=False)
        elif visibility == 'hidden':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(hide=True)

        if note != '':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(note__icontains=note)
        if country and country != '' and country != 'all':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(country__gid=int(country))
        elif country == 'all' and country_exclude != '':
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.exclude(country__gid=int(country_exclude))

        results = new_reports_unfiltered_qs.select_related('user', 'country', 'identification_task').prefetch_related('photos').order_by('-server_upload_time')

        try:
            paginator = Paginator(results, limit)
        except:
            paginator = Paginator(results, limit)

        try:
            results = paginator.page(offset)
        except PageNotAnInteger:
            results = paginator.page(offset)
        except EmptyPage:
            results = []

        api_count = paginator.count
        api_next = None if not results.has_next() else results.next_page_number()
        api_previous = None if not results.has_previous() else results.previous_page_number()

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