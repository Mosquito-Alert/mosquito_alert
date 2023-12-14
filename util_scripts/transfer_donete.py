from datetime import datetime
import os, sys
import time
from tqdm import tqdm

# **** Before running this, make sure the parameter DISABLE_MAYBE_GIVE_AWARDS = True in the settings ****
# this avoids creating awards automatically when saving a report

proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.db import transaction
from django.db.models import ForeignKey
from django.utils import timezone

from tigaserver_app.models import TigaUser, Report, Fix, AcknowledgedNotification

# NOTE: it is recommended to set DISABLE_PUSH_ANDROID and DISABLE_PUSH_IOS to True in settings

# Define constants
FROM_DATETIME_UTC = datetime(year=2022, month=7, day=5, tzinfo=timezone.utc)
FROM_DATABASE = "donete"
TO_DATABASE = "default"


def get_diff_objects_between_databases(model, filters=None, from_db=FROM_DATABASE):
    from_qs = model.objects.using(from_db)
    if filters:
        from_qs = from_qs.filter(**filters)
    ids_not_found = set(from_qs.values_list("pk", flat=True)) - set(
        model.objects.values_list("pk", flat=True)
    )
    return model.objects.using(from_db).filter(pk__in=ids_not_found)


def create_replica(obj, skip_fields=[], using=TO_DATABASE):
    replica_data = {}
    for field in obj._meta.fields:
        if field.name in skip_fields:
            continue

        field_value = getattr(obj, field.name)
        replica_data[field.name] = field_value
        # Check if the field is a ForeignKey and not from current database alias
        if (
            field_value is not None
            and isinstance(field, ForeignKey)
            and field_value._state.db != using
        ):
            # Refresh from the database
            refreshed_value = field.related_model.objects.using(using).get(
                pk=field_value.pk
            )
            replica_data[field.name] = refreshed_value

    # Create a new instance of the model with the replica data
    return obj._meta.model(**replica_data)


@transaction.atomic(using=TO_DATABASE)
def main():
    # Moving users
    users_not_in_prod = get_diff_objects_between_databases(
        model=TigaUser, filters=dict(registration_time__gte=FROM_DATETIME_UTC)
    )

    for user in tqdm(
        users_not_in_prod.prefetch_related("user_subscriptions")
        .order_by("registration_time")
        .iterator(),
        desc="Moving users",
        unit="user",
        total=users_not_in_prod.count(),
    ):
        new_user = create_replica(obj=user, using=TO_DATABASE)
        new_user.save(using=TO_DATABASE)

        for user_subscription in user.user_subscriptions.all():
            _new_user_subscription = create_replica(
                obj=user_subscription, skip_fields=["id", "user"], using=TO_DATABASE
            )
            _new_user_subscription.pk = None
            # Setting user here to avoid extra queries on create_replica
            _new_user_subscription.user = new_user
            _new_user_subscription.save(using=TO_DATABASE)

    # Create reports
    reports_not_in_prod = get_diff_objects_between_databases(
        model=Report, filters=dict(server_upload_time__gte=FROM_DATETIME_UTC)
    )

    for report in tqdm(
        reports_not_in_prod.prefetch_related("photos", "responses")
        .order_by("server_upload_time")
        .iterator(),
        desc="Moving reports",
        unit="report",
        total=reports_not_in_prod.count(),
    ):
        new_report = create_replica(
            obj=report,
            skip_fields=[
                "country",
                "nuts_3",
                "nuts_2",
            ],  # See Report.save(), these fields are auto generated
            using=TO_DATABASE,
        )
        new_report.save(using=TO_DATABASE)

        # ACK all notifications
        for notification in new_report.report_notifications.all():
            _ = AcknowledgedNotification.objects.using(TO_DATABASE).create(
                user=new_report.user,
                notification=notification,
            )

        for photo in report.photos.all():
            _new_photo = create_replica(
                obj=photo, skip_fields=["id", "report"], using=TO_DATABASE
            )
            _new_photo.pk = None
            # Setting report here to avoid extra queries on create_replica
            _new_photo.report = new_report
            _new_photo.save(using=TO_DATABASE)

        for response in report.responses.all():
            _new_response = create_replica(
                obj=response, skip_fields=["id", "report"], using=TO_DATABASE
            )
            _new_response.pk = None
            # Setting report here to avoid extra queries on create_replica
            _new_response.report = new_report
            _new_response.save(using=TO_DATABASE)

    # Create user fixes
    fixes_not_in_prod = Fix.objects.using(FROM_DATABASE).filter(
        server_upload_time__gte=FROM_DATETIME_UTC
    )

    for fix in tqdm(
        fixes_not_in_prod.order_by("server_upload_time").iterator(),
        desc="Moving fixes",
        unit="fix",
        total=fixes_not_in_prod.count(),
    ):
        _new_fix = create_replica(obj=fix, using=TO_DATABASE)
        _new_fix.pk = None
        _new_fix.save(using=TO_DATABASE)


if __name__ == "__main__":
    start = time.time()

    main()

    end = time.time()
    elapsed = end - start
    print("Elapsed time {0}".format(str(elapsed)))
