from datetime import datetime
from itertools import islice
import os, sys
import time
from tqdm import tqdm

proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings_donete")
sys.path.append(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.db import transaction
from django.db.models import ForeignKey
from django.utils import timezone

from tigaserver_app.models import (
    TigaUser,
    Report,
    Fix,
    AcknowledgedNotification,
    UserSubscription,
    Photo,
    ReportResponse,
    Notification,
)

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


def create_replica(obj, skip_fields=[]):
    replica_data = {}
    for field in obj._meta.fields:
        if field.name in skip_fields:
            continue

        if isinstance(field, ForeignKey):
            replica_data[field.name + "_id"] = getattr(obj, field.name + "_id")
        else:
            replica_data[field.name] = getattr(obj, field.name)

    # Create a new instance of the model with the replica data
    return obj._meta.model(**replica_data)


def create_objects(
    model, generator, total, bulk=True, batch_size=1000, using=TO_DATABASE
):
    with tqdm(
        total=total,
        desc=f"Moving {model._meta.verbose_name_plural}",
        unit=str(model._meta.verbose_name_plural),
    ) as progress_bar:
        if bulk:
            while True:
                batch = list(islice(generator, batch_size))
                if not batch:
                    break
                model.objects.using(using).bulk_create(
                    objs=batch, batch_size=batch_size
                )
                progress_bar.update(len(batch))
        else:
            for obj in generator:
                obj.save(using=using)
                progress_bar.update(1)


def move_objects(queryset, skip_fields=["id"], *args, **kwargs):
    generator = (
        create_replica(obj=x, skip_fields=skip_fields) for x in queryset.iterator()
    )
    create_objects(
        model=queryset.model,
        generator=generator,
        total=queryset.count(),
        *args,
        **kwargs,
    )


@transaction.atomic(using=TO_DATABASE)
def main():
    ##############################
    # USER
    ##############################
    # Moving users
    users_not_in_prod = get_diff_objects_between_databases(
        model=TigaUser, filters=dict(registration_time__gte=FROM_DATETIME_UTC)
    ).order_by("registration_time")
    move_objects(
        queryset=users_not_in_prod,
        # setting skip_field to [] because we want to keep the original pk (UUID)
        skip_fields=[],
    )

    # Moving users subscriptions
    move_objects(
        queryset=UserSubscription.objects.using(FROM_DATABASE).filter(
            user__in=users_not_in_prod
        )
    )

    ##############################
    # REPORT
    ##############################
    # Moving reports
    reports_not_in_prod = get_diff_objects_between_databases(
        model=Report, filters=dict(server_upload_time__gte=FROM_DATETIME_UTC)
    ).order_by("server_upload_time")

    move_objects(
        queryset=reports_not_in_prod,
        # Skipping auto generated fields (see Report.save()). Keeping the original pk (UUID)
        skip_fields=["country", "nuts_3", "nuts_2"],
        bulk=False,  # Calling without bulk (calling save) -> post_save signal triggers award creation.
    )

    # Moving photos
    photos_not_in_prod = Photo.objects.using(FROM_DATABASE).filter(
        report__in=reports_not_in_prod
    )
    move_objects(queryset=photos_not_in_prod)

    # Moving report responses
    reponses_not_in_prod = ReportResponse.objects.using(FROM_DATABASE).filter(
        report__in=reports_not_in_prod
    )
    move_objects(queryset=reponses_not_in_prod)

    # Create ACK for all notifications created related to new reports.
    # Using list and values_list since using two different databases...
    notifications_to_ack = Notification.objects.using(TO_DATABASE).filter(
        report__in=list(reports_not_in_prod.values_list("pk", flat=True))
    )
    ack_notifications_generator = (
        AcknowledgedNotification(
            user=notification.report.user, notification=notification
        )
        for notification in notifications_to_ack.select_related(
            "report__user"
        ).iterator()
    )
    create_objects(
        model=AcknowledgedNotification,
        generator=ack_notifications_generator,
        total=notifications_to_ack.count(),
    )

    ##############################
    # USER FIXES
    ##############################
    fixes_not_in_prod = (
        Fix.objects.using(FROM_DATABASE)
        .filter(server_upload_time__gte=FROM_DATETIME_UTC)
        .order_by("server_upload_time")
    )
    move_objects(queryset=fixes_not_in_prod)


if __name__ == "__main__":
    start = time.time()

    main()

    end = time.time()
    elapsed = end - start
    print("Elapsed time {0}".format(str(elapsed)))
