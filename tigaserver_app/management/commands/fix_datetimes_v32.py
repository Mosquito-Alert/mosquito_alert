from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from tqdm import tqdm
from itertools import islice
import pandas as pd
import pytz
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, fields, ExpressionWrapper, Q, OuterRef, Subquery
from django.utils import timezone

from tigaserver_app.models import Award, Report, Fix
from tigaserver_app.utils import is_instant_upload_candidate, apply_tz_to_datetime


class AutoTzDateTimeProcess(ABC):
    FIELDS_TO_FIX = []
    MODEL = None

    @classmethod
    def _get_fields_to_update(cls):
        return cls.FIELDS_TO_FIX

    @classmethod
    def _get_tracked_fields(cls):
        return [cls.MODEL._meta.pk.name, "_tz", "_has_changed"] + cls._get_fields_to_update()

    def _get_timezone(self, obj):
        return obj.get_timezone_from_coordinates()

    def _objs_to_update_generator(self, queryset):
        for obj in queryset.iterator():
            tz = self._get_timezone(obj=obj)

            # Save timezone in tmp variable, needed for writing output CSV
            obj._tz = tz
            obj._has_changed = False  # Default

            for fieldname in self.FIELDS_TO_FIX:
                # Apply TZ and convert to UTC
                datetime_field = apply_tz_to_datetime(
                    getattr(obj, fieldname), tz=tz
                ).astimezone(timezone.utc)

                # Saving original value in a variable
                setattr(obj, "_" + fieldname + "_old", getattr(obj, fieldname))
                if datetime_field != getattr(obj, fieldname):
                    # If is different, apply change.
                    setattr(obj, fieldname, datetime_field)
                    obj._has_changed = True

            yield obj

    def pre_run(self, queryset, dry_run):
        self._run_datetime = datetime.utcnow()
        self._old_records_df = pd.DataFrame.from_records(
            data=list(queryset.all().values()), index=self.MODEL._meta.pk.name
        )
        self._new_records_list = []

    def pre_update(self, batch, dry_run):
        pass

    def post_update(self, batch, dry_run):
        fields = self._get_tracked_fields()
        for obj in batch:
            self._new_records_list.append(
                {fname: getattr(obj, fname) for fname in fields}
            )

    def post_run(self, dry_run):
        def make_path_safe(input_string, replacement="_"):
            # Define a regex pattern for characters not allowed in paths
            invalid_chars = r'[\/:*?"<>|]'

            # Replace invalid characters with the specified replacement
            safe_path = re.sub(invalid_chars, replacement, input_string)

            return safe_path

        def write_csv(df, path_preffix=""):
            df.to_csv(
                "./{path}.csv".format(
                    path=make_path_safe(
                        "_".join(
                            [
                                path_preffix,
                                "fix_auto_tz",
                                str(self.MODEL._meta.verbose_name_plural),
                                str(self._run_datetime),
                            ]
                        )
                    )
                )
            )

        self._new_df = pd.DataFrame.from_dict(data=self._new_records_list)
        self._new_df.set_index(self.MODEL._meta.pk.name, inplace=True)

        self._joint_df = self._old_records_df.join(
            self._new_df, how="left", lsuffix="_old"
        )
        # Write CSV with all results
        write_csv(
            df=self._joint_df,
            path_preffix="all",
        )

        # Write CSV with only the results that has changed.
        # Only save the columns of interest (old and new value).
        write_csv(
            df=self._joint_df.loc[
                self._joint_df["_has_changed"] == True,
                self.FIELDS_TO_FIX + [x + "_old" for x in self.FIELDS_TO_FIX],
            ],
            path_preffix="summary",
        )

    def run(self, queryset, batch_size=1000, dry_run=False):
        if queryset.model != self.MODEL:
            raise ValueError

        self.pre_run(queryset, dry_run)

        generator = self._objs_to_update_generator(queryset=queryset)

        with tqdm(
            total=queryset.count(),
            desc=f"Checking {self.MODEL._meta.verbose_name_plural}",
            unit=str(self.MODEL._meta.verbose_name_plural),
        ) as progress_bar:
            while True:
                batch = list(islice(generator, batch_size))
                if not batch:
                    break
                self.pre_update(batch=batch, dry_run=dry_run)
                batch_with_changes = list(filter(lambda x: x._has_changed, batch))
                if batch_with_changes and not dry_run:
                    # NOTE: bulk_update does not call save().
                    self.MODEL.objects.bulk_update(
                        objs=batch_with_changes,
                        fields=self._get_fields_to_update(),
                        batch_size=batch_size,
                    )
                self.post_update(batch=batch, dry_run=dry_run)
                progress_bar.update(len(batch))

        self.post_run(dry_run)


class AutoTzOrInstantUploadTimeProcess(AutoTzDateTimeProcess):
    @property
    @abstractmethod
    def CLIENT_CREATION_FIELD(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def SERVER_CREATION_FIELD(self):
        raise NotImplementedError

    def _get_timezone_from_instant_upload(self, obj):
        tz = None

        # If considered as instant upload -> return
        # a 'fake' timezone with the utcoffset equal to the
        # difference of upload time (rounded to whole-hour-quarters)
        if is_instant_upload_candidate(
            server_creation_datetime=getattr(obj, self.SERVER_CREATION_FIELD),
            user_creation_datetime=getattr(obj, self.CLIENT_CREATION_FIELD),
        ):
            interval_minutes = 15  # nearest 15min interval
            try:
                tz = pytz.FixedOffset(
                    # In minutes
                    offset=round(
                        (
                            getattr(obj, self.CLIENT_CREATION_FIELD)
                            - getattr(obj, self.SERVER_CREATION_FIELD)
                        ).total_seconds()
                        / 60
                        / interval_minutes
                    )
                    * interval_minutes
                )
            except ValueError:
                # case offset greater than 1day.
                pass
        return tz

    def _get_timezone_from_location(self, obj):
        return super()._get_timezone(obj=obj)

    def _get_timezone(self, obj):
        tz_from_coordinates = self._get_timezone_from_location(obj=obj)
        tz_from_instant_upload = self._get_timezone_from_instant_upload(obj=obj)

        # If after applying the Timezone obtained from cooridinates,
        # the upload is still high (>15min)
        # then: Return tz_from_instant_upload (if not None)
        # else: Return tz_from_coordinates
        _client_creation_time_fix_coordiantes = apply_tz_to_datetime(
            getattr(obj, self.CLIENT_CREATION_FIELD), tz=tz_from_coordinates
        )
        _upload_elapsed_time_fix_coordinates = abs(
            getattr(obj, self.SERVER_CREATION_FIELD)
            - _client_creation_time_fix_coordiantes
        ).total_seconds()
        if tz_from_instant_upload and _upload_elapsed_time_fix_coordinates > 15 * 60:
            return tz_from_instant_upload
        else:
            return tz_from_coordinates


class ReportAutoTzDateTimeProcess(AutoTzOrInstantUploadTimeProcess):
    MODEL = Report
    FIELDS_TO_FIX = ["version_time", "creation_time", "phone_upload_time"]

    CLIENT_CREATION_FIELD = "version_time"
    SERVER_CREATION_FIELD = "server_upload_time"

    @classmethod
    def _get_fields_to_update(cls):
        return super()._get_fields_to_update() + ["updated_at", "datetime_fix_offset"]

    def _objs_to_update_generator(self, queryset):
        # NOTE: Take into account that v32 only have
        # version_number = 0 and version_number = -1
        # This solution does not apply on other package versions
        # than v32.
        version_subquery = Report.objects.filter(
            user=OuterRef('user'),
            report_id=OuterRef('report_id'),
            type=OuterRef('type')
        )
        lowest_version_reports = version_subquery.exclude(
            version_number=-1
        ).order_by('version_number', 'server_upload_time').values('pk')[:1]

        for obj in super()._objs_to_update_generator(
            queryset=queryset.filter(pk__in=Subquery(lowest_version_reports))
        ):
            yield obj

            # Getting versions for this report
            for report_version in Report.objects.filter(
                report_id=obj.report_id,
                user_id=obj.user_id,
                type=obj.type,
            ).exclude(pk=obj.pk):
                # Init with the same values as the original report.
                report_version.phone_upload_time = obj.phone_upload_time
                report_version.creation_time = obj.creation_time
                report_version._has_changed = obj._has_changed
                report_version._tz = None

                # If report version is in same day than original report
                # we can asume that the user has not moved and is using the same
                # TimeZone as the original.
                # Else, try getting its Tz from the instant upload method.
                if (
                    abs(
                        obj._version_time_old - report_version.version_time
                    ).total_seconds()
                    <= 24 * 3600
                ):
                    report_version._tz = obj._tz
                else:
                    report_version._tz = self._get_timezone_from_instant_upload(
                        obj=report_version
                    )

                # Apply the new TZ and convert to UTC.
                new_version_time = apply_tz_to_datetime(
                    report_version.version_time, tz=report_version._tz
                ).astimezone(timezone.utc)

                # Save old value
                report_version._version_time_old = report_version.version_time
                if new_version_time != report_version.version_time:
                    # Apply changes if is different
                    report_version.version_time = new_version_time
                    report_version._has_changed = True

                yield report_version

    def pre_update(self, batch, dry_run):
        # Get the affected awards
        self._award_pks = list(
            Award.objects.filter(
                report__in=batch, date_given__exact=F("report__creation_time")
            ).values_list("pk", flat=True)
        )

        for obj in batch:
            # Setting updated_at to now since bulk_update won't call save().
            obj.updated_at = timezone.now()
            if obj._tz:
                # Setting datetime_fix_offset field
                obj.datetime_fix_offset = int((obj.version_time - obj._version_time_old).total_seconds())

        return super().pre_update(batch, dry_run)

    def post_update(self, batch, dry_run):
        # Assuming award_list is the list of Award instances
        award_updates = []
        for award in (
            Award.objects.filter(pk__in=self._award_pks)
            .select_related("report")
            .iterator()
        ):
            award.date_given = award.report.creation_time
            award_updates.append(award)

        if not dry_run:
            Award.objects.bulk_update(award_updates, fields=["date_given"])

        del self._award_pks

        return super().post_update(batch, dry_run)


class FixAutoTzDateTimeProcess(AutoTzOrInstantUploadTimeProcess):
    MODEL = Fix
    FIELDS_TO_FIX = ["phone_upload_time"]

    CLIENT_CREATION_FIELD = "phone_upload_time"
    SERVER_CREATION_FIELD = "server_upload_time"

    _AFFECTED_RELEASE_DATE = datetime(year=2021, month=3, day=10, tzinfo=timezone.utc)

    def _get_timezone_from_location(self, obj):
        # Only apply to objects after 2021-0310
        # that we are sure the affected version was
        # released in both Apple and Android Stores.
        if obj.server_upload_time > self._AFFECTED_RELEASE_DATE:
            return super()._get_timezone_from_location(obj=obj)
        else:
            return None


class Command(BaseCommand):
    help = "Update timezones in the specified datetime fields of the Report model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from_datetime",
            type=str,
            # required=True,  # For the user fixes.
            help="Filter reports with server_upload_time greater than this datetime (UTC)",
        )
        parser.add_argument(
            "--to_datetime",
            type=str,
            help="Filter reports with server_upload_time less than this datetime (UTC)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for processing the queryset",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without saving changes",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from_datetime_str = options["from_datetime"]
        to_datetime_str = options["to_datetime"]
        from_datetime = (
            timezone.make_aware(datetime.fromisoformat(from_datetime_str))
            if from_datetime_str
            else None
        )
        to_datetime = (
            timezone.make_aware(datetime.fromisoformat(to_datetime_str))
            if to_datetime_str
            else None
        )
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]

        # Fix Reports
        report_qs = Report.objects.filter(package_version=32)
        if from_datetime:
            report_qs = report_qs.filter(server_upload_time__gte=from_datetime)

        if to_datetime:
            report_qs = report_qs.filter(server_upload_time__lte=to_datetime)
        _ = ReportAutoTzDateTimeProcess().run(
            queryset=report_qs, batch_size=batch_size, dry_run=dry_run
        )

        # Fix UserFixes
        # Candidates will be all which upload_time_diff is already greater than 15min.
        fix_qs = Fix.objects.annotate(
            upload_time_diff=ExpressionWrapper(
                F("server_upload_time") - F("phone_upload_time"),
                output_field=fields.DurationField(),
            )
        ).filter(
            Q(upload_time_diff__gt=timedelta(minutes=15))
            or Q(upload_time_diff__lt=timedelta(minutes=-15))
        )

        if from_datetime:
            fix_qs = fix_qs.filter(server_upload_time__gte=from_datetime)

        if to_datetime:
            fix_qs = fix_qs.filter(server_upload_time__lte=to_datetime)

        _ = FixAutoTzDateTimeProcess().run(
            queryset=fix_qs, batch_size=batch_size, dry_run=dry_run
        )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("Dry run completed. No changes were saved.")
            )
