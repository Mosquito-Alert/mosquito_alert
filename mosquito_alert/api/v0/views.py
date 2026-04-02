from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import mixins, GenericAPIView
from rest_framework.exceptions import ParseError, ValidationError
from django.conf import settings
from django_filters import rest_framework as filters
import json
from mosquito_alert.devices.models import Device
from mosquito_alert.tigaserver_app.models import Session
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import get_template

from mosquito_alert.campaigns.models import OWCampaigns
from mosquito_alert.fixes.models import Fix
from mosquito_alert.identification_tasks.models import (
    ExpertReportAnnotation,
    IdentificationTask,
)
from mosquito_alert.notifications.models import (
    NotificationRecipient,
    NotificationTopic,
    UserSubscription,
)
from mosquito_alert.partners.models import OrganizationPin
from mosquito_alert.reports.models import Report, ReportResponse, Photo
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.users.models import TigaUser

from .serializers import (
    NotificationSerializer,
    UserSerializer,
    ReportSerializer,
    PhotoSerializer,
    FixSerializer,
    SessionSerializer,
    OWCampaignsSerializer,
    OrganizationPinsSerializer,
    UserSubscriptionSerializer,
    CoarseReportSerializer,
)


@api_view(["POST"])
def post_photo(request):
    """
    API endpoint for uploading photos associated with a report. Data must be posted as multipart form,
    with with _photo_ used as the form key for the file itself, and _report_ used as the key for the report
    version_UUID linking this photo to a specific report version.

    **Fields**

    * photo: The photo's binary image data
    * report: The version_UUID of the report to which this photo is attached.
    """
    if request.method == "POST":
        try:
            this_report = Report.objects.get(pk=request.data["report"])
        except Report.DoesNotExist:
            return Response()
        instance = Photo(photo=request.FILES["photo"], report=this_report)
        instance.save()
        return Response("uploaded")


class UserFilter(filters.FilterSet):
    user_UUID = filters.Filter(method="filter_partial_uuid")

    def filter_partial_uuid(self, qs, name, value):
        user_UUID = value
        if not user_UUID:
            return qs
        return qs.filter(user_UUID__startswith=user_UUID)

    class Meta:
        model = TigaUser
        fields = ["user_UUID"]


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
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


class ReportViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = Report.objects.all().prefetch_related("responses", "photos")
    serializer_class = ReportSerializer
    filterset_fields = ("user", "version_number", "report_id", "type")

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get the filters from the request
        is_deleted = self.request.query_params.get("is_deleted", None)

        # Apply additional filters if provided
        if is_deleted is not None:
            if is_deleted.lower() not in ["true", "false"]:
                raise ParseError(
                    "Invalid value for 'is_deleted'. It should be 'true', 'false', or not provided."
                )

            if is_deleted.lower() == "true":
                # Filter queryset to include only deleted records
                queryset = queryset.deleted(state=True)
            elif is_deleted.lower() == "false":
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
        version_number = request.data.get("version_number")
        version_UUID = request.data.get("version_UUID")

        # Validate version_number and version_UUID
        if version_number is None or version_UUID is None:
            return Response(
                {"error": "version_number and version_UUID are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if version_number < -1:
            raise ValidationError(
                {"version_number": "Invalid version number provided."}
            )

        # Handle case when version_number is 0 and report already exists
        if version_number == 0 and Report.objects.filter(pk=version_UUID).exists():
            return Response(
                {"error": "Object with this PK already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        instance = None
        if version_number != 0:
            # Updates/deletion of the original version
            instance = get_object_or_404(
                self.get_queryset(),
                **{
                    # NOTE: version_UUID is different on every user's POST
                    #'pk': request.data.get('version_UUID'),
                    "user": request.data.get("user"),
                    "report_id": request.data.get("report_id"),
                    "type": request.data.get("type"),
                },
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
        return Response(
            data=result_data, status=status.HTTP_201_CREATED, headers=result_headers
        )

    def perform_destroy(self, instance):
        instance.soft_delete()


class PhotoViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
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
    filterset_fields = ("user_coverage_uuid",)


class SessionPartialUpdateView(GenericAPIView, mixins.UpdateModelMixin):
    """
    You just need to provide the field which is to be modified.
    """

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
    filterset_fields = ("id", "user")

    def filter_queryset(self, queryset):
        queryset = super(SessionViewSet, self).filter_queryset(queryset)
        return queryset.order_by("-session_ID")


# This implementation is weird AF.
@api_view(["DELETE"])
def mark_notif_as_ack(request):
    user = request.query_params.get("user", "-1")
    notif = request.query_params.get("notif", -1)
    if user == "-1":
        raise ParseError(detail="user param is mandatory")
    if notif == -1:
        raise ParseError(detail="notif param is mandatory")
    try:
        u = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail="This user does not exist")
    try:
        notification_recipient = NotificationRecipient.objects.get(
            user=u, notification_id=notif
        )
    except NotificationRecipient.DoesNotExist:
        raise ParseError(detail="This notification does not exist")

    if notification_recipient.is_read:
        return Response(status=status.HTTP_204_NO_CONTENT)

    notification_recipient.is_read = True
    notification_recipient.save()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def unsub_from_topic(request):
    code = request.query_params.get("code", "-1")
    user = request.query_params.get("user", "-1")
    if user == "-1":
        raise ParseError(detail="user param is mandatory")
    if code == "-1":
        raise ParseError(detail="code param is mandatory")
    if code == "global":
        raise ParseError(detail="unsubscription from global not allowed")
    n = None
    usr = None
    try:
        n = NotificationTopic.objects.get(topic_code=code)
    except NotificationTopic.DoesNotExist:
        raise ParseError(detail="topic with this code does not exist")
    try:
        usr = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail="no user with id")

    try:
        sub = UserSubscription.objects.get(user=usr, topic=n)
        sub.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except UserSubscription.DoesNotExist:
        raise ParseError(detail="this user is not subscribed to this topic")


@api_view(["POST"])
def subscribe_to_topic(request):
    code = request.query_params.get("code", "-1")
    user = request.query_params.get("user", "-1")
    if user == "-1":
        raise ParseError(detail="user param is mandatory")
    if code == "-1":
        raise ParseError(detail="code param is mandatory")
    if code == "global":
        raise ParseError(detail="subscription to global not allowed")
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
        raise ParseError(detail="no user with id")

    try:
        with transaction.atomic():
            sub = UserSubscription(user=usr, topic=n)
            sub.save()
            serializer = UserSubscriptionSerializer(sub)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    except IntegrityError:
        raise ParseError(detail="Subscription already exists")


@api_view(["GET"])
def topics_subscribed(request):
    user = request.query_params.get("user", "-1")
    if user == "-1":
        raise ParseError(detail="user param is mandatory")
    try:
        user = TigaUser.objects.get(pk=user)
    except TigaUser.DoesNotExist:
        raise ParseError(detail="no user with this id")
    subs = UserSubscription.objects.filter(user=user).select_related("topic")
    serializer = UserSubscriptionSerializer(subs, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def token(request):
    token = request.query_params.get("token", -1)
    user_id = request.query_params.get("user_id", -1)
    if user_id != -1 and token != -1:
        device, _ = Device.objects.update_or_create(
            user=get_object_or_404(TigaUser.objects.all(), pk=user_id),
            registration_id=token,
            defaults={
                "active": True,
                "active_session": True,
                "last_login": timezone.now(),
            },
        )
        return Response({"token": device.registration_id})
    else:
        raise ParseError(detail="Invalid parameters")


@api_view(["GET"])
def user_notifications(request):
    if request.method == "GET":
        locale = request.query_params.get("locale", "en")
        user_id = request.query_params.get("user_id", -1)
        if user_id == -1:
            raise ParseError(detail="user_id is mandatory")

        notifications_qs = (
            NotificationRecipient.objects.filter(user=user_id)
            .select_related("notification", "notification__notification_content")
            .order_by("-notification__date_comment")
        )

        serializer = NotificationSerializer(
            notifications_qs, many=True, context={"locale": locale}
        )

        return Response(serializer.data)


def send_unblock_email(name, email):

    send_to = (settings.ADDITIONAL_EMAIL_RECIPIENTS or []) + [email]

    subject = "MOSQUITO ALERT - blocked report release warning"
    plaintext = get_template("tigaserver_app/report_release/report_release_template")
    context = {"name": name, "n_days": settings.ENTOLAB_LOCK_PERIOD}
    text_content = plaintext.render(context)
    email = EmailMessage(subject, text_content, to=send_to)
    email.send(fail_silently=True)


def delete_annotations_and_notify(annotations_qs):
    recipients = []
    for obj in annotations_qs.select_related("user"):
        if obj.user.email is not None and obj.user.email != "":
            recipients.append(obj.user)

        obj.delete()

    for r in set(recipients):
        name = r.first_name if r.first_name != "" else r.username
        email = r.email
        send_unblock_email(name, email)


@api_view(["DELETE"])
def clear_blocked_all(request):
    if request.method == "DELETE":
        delete_annotations_and_notify(
            annotations_qs=ExpertReportAnnotation.objects.blocking()
        )

        return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
def clear_blocked(request, username, report=None):
    if request.method == "DELETE":
        if username is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)

        annotations_qs = user.expert_report_annotations.blocking()

        if report:
            annotations_qs = annotations_qs.filter(
                identification_task__report=get_object_or_404(Report, pk=report)
            )

        delete_annotations_and_notify(annotations_qs=annotations_qs)

        return Response(status=status.HTTP_200_OK)


class OWCampaignsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = OWCampaignsSerializer
    queryset = OWCampaigns.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()

        country_id = self.request.query_params.get("country_id", None)
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


def get_filter_params_from_q(q):
    if q == "":
        return {
            "type": "all",
            "visibility": "visible",
            "aithr": 1.00,
            "note": "",
            "country": "all",
            "country_exclude": "",
        }  # default values
    else:
        json_filter = json.loads(q)
        return {
            "type": json_filter["report_type"],
            "visibility": json_filter["visibility"],
            "aithr": float(json_filter["ia_threshold"]),
            "note": json_filter["note"],
            "country": json_filter["country"],
            "country_exclude": json_filter["country_exclude"],
        }


@api_view(["PATCH"])
def hide_report(request):
    if request.method == "PATCH":
        # print(request.data)
        report_id = request.data.get("report_id", "-1")
        hide_val = request.data.get("hide")
        if report_id == "-1":
            raise ParseError(detail="report_id param is mandatory")
        if not hide_val:
            raise ParseError(detail="hide param is mandatory")
        hide = hide_val == "true"
        report = get_object_or_404(Report, pk=report_id)
        if (
            ExpertReportAnnotation.objects.filter(
                identification_task__report=report
            ).count()
            > 0
        ):
            return Response(
                data={"message": "success", "opcode": -1},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.hide = hide
        report.save()
        try:
            identification_task = report.identification_task
            identification_task.refresh()
        except Report.identification_task.RelatedObjectDoesNotExist:
            pass
        return Response(
            data={"message": "hide set to {0}".format(hide), "opcode": 0},
            status=status.HTTP_200_OK,
        )


@api_view(["PATCH"])
def flip_report(request):
    if request.method == "PATCH":
        flip_to_type = request.data.get("flip_to_type", "")
        flip_to_subtype = request.data.get("flip_to_subtype", "")
        report_id = request.data.get("report_id", "")
        report = get_object_or_404(Report, pk=report_id)
        if (
            ExpertReportAnnotation.objects.filter(
                identification_task__report=report
            ).count()
            > 0
        ):
            return Response(
                data={"message": "success", "opcode": -1},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if flip_to_type == "":  # adult | site
            raise ParseError(detail="flip_to_type param is mandatory")
        if flip_to_type not in [Report.TYPE_ADULT, Report.TYPE_SITE]:
            raise ParseError(
                detail="value not allowed, possible values are 'adult', 'site'"
            )
        if flip_to_type == Report.TYPE_SITE:
            if flip_to_subtype == "":
                raise ParseError(
                    detail="flip_to_subtype param is mandatory if type is site"
                )
            else:
                if flip_to_subtype not in [
                    "storm_drain_water",
                    "storm_drain_dry",
                    "other_water",
                    "other_dry",
                ]:
                    raise ParseError(
                        detail="value not allowed, possible values are 'storm_drain_water','storm_drain_dry', 'other_water', 'other_dry' "
                    )

        if report.type == Report.TYPE_ADULT and flip_to_type == Report.TYPE_ADULT:
            return Response(
                data={"message": "Type is already adult, doing nothing", "opcode": -2},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # delete questions and answers ?

        # set new questions and answers
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_12	question_12_answer_122	122		12 -> Other
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_10	question_10_answer_101	101		10 -> Water

        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_12	question_12_answer_121	121		12 -> Storm Drain
        # id	4ada4a1b-c438-4fcc-87e7-eb4696c1466f	question_10	question_10_answer_101	101		10 -> Water
        with transaction.atomic():
            ReportResponse.objects.filter(report=report).delete()
            rr_type_stormdrain = ReportResponse(
                report=report,
                question="question_12",
                answer="question_12_answer_121",
                question_id=12,
                answer_id=121,
            )
            rr_type_other = ReportResponse(
                report=report,
                question="question_12",
                answer="question_12_answer_122",
                question_id=12,
                answer_id=122,
            )
            rr_yes_water = ReportResponse(
                report=report,
                question="question_10",
                answer="question_10_answer_101",
                question_id=10,
                answer_id=101,
            )
            rr_no_water = ReportResponse(
                report=report,
                question="question_10",
                answer="question_10_answer_102",
                question_id=10,
                answer_id=102,
            )
            report.flipped = True
            report.flipped_on = timezone.now()
            if flip_to_type == Report.TYPE_SITE:
                report.flipped_to = report.type + "#site"
                report.type = Report.TYPE_SITE
                try:
                    identification_task = report.identification_task
                    identification_task.delete()
                except Report.identification_task.RelatedObjectDoesNotExist:
                    pass
                report.save()
                if flip_to_subtype == "storm_drain_water":
                    rr_type_stormdrain.save()
                    rr_yes_water.save()
                    message = "Report changed to Site - Storm Drain, Water"
                elif flip_to_subtype == "storm_drain_dry":
                    rr_type_stormdrain.save()
                    rr_no_water.save()
                    message = "Report changed to Site - Storm Drain, No Water"
                elif flip_to_subtype == "other_dry":
                    rr_type_other.save()
                    rr_no_water.save()
                    message = "Report changed to Site - Other, No Water"
                elif flip_to_subtype == "other_water":
                    rr_type_other.save()
                    rr_yes_water.save()
                    message = "Report changed to Site - Other, Water"
            elif flip_to_type == Report.TYPE_ADULT:
                report.flipped_to = report.type + "#adult"
                report.type = Report.TYPE_ADULT
                report.save()
                IdentificationTask.get_or_create_for_report(report=report)
                message = "Report changed to Adult"

            return Response(
                data={
                    "message": message,
                    "new_type": flip_to_type,
                    "new_subtype": flip_to_subtype,
                    "opcode": 0,
                },
                status=status.HTTP_200_OK,
            )


@api_view(["POST"])
def quick_upload_report(request):
    if request.method == "POST":
        report_id = request.POST.get("report_id", "-1")
        if report_id == "-1":
            raise ParseError(detail="report_id param is mandatory")
        report = get_object_or_404(Report, pk=report_id)
        if report.type != Report.TYPE_SITE:
            return Response(
                data={
                    "message": "Report type is not site, cannot be quick uploaded",
                    "opcode": -2,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if report.published:
            return Response(
                data={"message": "success", "opcode": 1}, status=status.HTTP_200_OK
            )
        report.published_at = timezone.now()
        report.save()
        return Response(
            data={"message": "success", "opcode": 0}, status=status.HTTP_200_OK
        )


@api_view(["POST"])
def annotate_coarse(request):
    if request.method == "POST":
        report_id = request.POST.get("report_id", "-1")
        taxon_id = request.POST.get("taxon_id", -1)
        confidence = float(
            request.POST.get(
                "confidence", ExpertReportAnnotation.ConfidenceCategory.PROBABLY
            )
        )
        if report_id == "-1":
            raise ParseError(detail="report_id param is mandatory")
        report = get_object_or_404(Report, pk=report_id)
        if report.type != Report.TYPE_ADULT:
            return Response(
                data={
                    "message": "Report type is not adult, cannot be annotated",
                    "opcode": -2,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # This prevents auto annotating a report which has been claimed by someone between reloads
        if (
            ExpertReportAnnotation.objects.filter(
                identification_task__report=report
            ).count()
            > 0
        ):
            return Response(
                data={"message": "success", "opcode": -1},
                status=status.HTTP_400_BAD_REQUEST,
            )
        taxon = get_object_or_404(Taxon, pk=taxon_id)

        ExpertReportAnnotation.objects.create(
            user=request.user,
            identification_task=report.identification_task,
            public_note=ExpertReportAnnotation._get_auto_message(
                taxon=taxon, confidence=confidence, locale=report.user.locale
            )
            or "",
            status=ExpertReportAnnotation.Status.PUBLIC,
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            best_photo=report.photos.first(),
            is_simplified=False,
            taxon=taxon,
            confidence=confidence,
        )

        return Response(
            data={"message": "success", "opcode": 0}, status=status.HTTP_200_OK
        )


@api_view(["GET"])
def coarse_filter_reports(request):
    if request.method == "GET":
        q = request.query_params.get("q", "")
        filter_params = get_filter_params_from_q(q)
        aithr = filter_params["aithr"]
        type = filter_params["type"]
        visibility = filter_params["visibility"]
        note = filter_params["note"]
        country = filter_params["country"]
        country_exclude = filter_params["country_exclude"]

        limit = request.query_params.get("limit", 300)
        offset = request.query_params.get("offset", 1)

        new_reports_unfiltered_qs = Report.objects.in_coarse_filter()

        if type == "adult":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                type=Report.TYPE_ADULT,
                identification_task__pred_insect_confidence__lte=float(aithr),
            )
        elif type == "site":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                type=Report.TYPE_SITE
            )

        if visibility == "visible":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(hide=False)
        elif visibility == "hidden":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(hide=True)

        if note != "":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                note__icontains=note
            )
        if country and country != "" and country != "all":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.filter(
                country__gid=int(country)
            )
        elif country == "all" and country_exclude != "":
            new_reports_unfiltered_qs = new_reports_unfiltered_qs.exclude(
                country__gid=int(country_exclude)
            )

        results = (
            new_reports_unfiltered_qs.select_related(
                "user", "country", "identification_task"
            )
            .prefetch_related("photos")
            .order_by("-server_upload_time")
        )

        try:
            paginator = Paginator(results, limit)
        except Exception:
            paginator = Paginator(results, limit)

        try:
            results = paginator.page(offset)
        except PageNotAnInteger:
            results = paginator.page(offset)
        except EmptyPage:
            results = []

        api_count = paginator.count
        api_next = None if not results.has_next() else results.next_page_number()
        api_previous = (
            None if not results.has_previous() else results.previous_page_number()
        )

        serializer = CoarseReportSerializer(results, many=True)

        data = {
            "per_page": limit,
            "count_pages": paginator.num_pages,
            "current": offset,
            "count": api_count,
            "next": api_next,
            "previous": api_previous,
            "results": serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)
