from datetime import timedelta
from typing import Tuple, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import fields
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from fcm_django.models import FCMDeviceQuerySet, FCMDeviceManager

from tigacrafting.models import ExpertReportAnnotation, UserStat

class ReportQuerySet(models.QuerySet):
    def has_photos(self, state: bool = True):
        from .models import Photo

        return self.annotate(
            photo_exist=models.Exists(
                Photo.objects.filter(
                    report=models.OuterRef('pk')
                ).visible()
            )
        ).filter(
            photo_exist=state
        )

    def deleted(self, state: bool = True):
        return self.exclude(deleted_at__isnull=state)

    def non_deleted(self):
        return self.deleted(state=False)
    
    def published(self, state: bool = True):
        PRIVATE_LAYERS = [
            "breeding_site_not_yet_filtered",
            "conflict",
            "not_yet_validated",
            "trash_layer",
        ]
        return self.non_deleted().filter(
            models.Q(
                models.Q(map_aux_report__isnull=False)
                & ~models.Q(map_aux_report__private_webmap_layer__in=PRIVATE_LAYERS),
                _negated=not state
            )
        )

    def browsable(self):
        return self.filter(
            hide=False
        ).exclude(
            note__icontains="#345"
        )

    def with_finished_validation(self, state: bool = True) -> QuerySet:
        # All assignations (maximum) has validated.
        subquery = ExpertReportAnnotation.objects.filter(
            validation_complete=True
        ).values('report').annotate(
            count=models.Count(1)
        ).filter(
            models.Q(count__gte=settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT) |
            models.Q(validation_complete_executive=True),
        ).filter(report=models.OuterRef('pk'))

        return self.annotate(
            has_finished_validation=models.Exists(subquery.values('pk'))
        ).filter(
            has_finished_validation=state
        )

    def annotate_final_status(self):
        return self.annotate(
            superexpert_status=models.Subquery(
                ExpertReportAnnotation.objects.filter(
                    report=models.OuterRef('pk'),
                    user__groups__name='superexpert',
                    validation_complete=True,
                    revise=True
                ).order_by('-last_modified').values('status')[:1],
                output_field=models.IntegerField()
            ),
            worst_expert_status=models.Subquery(
                ExpertReportAnnotation.objects.filter(
                    report=models.OuterRef('pk'),
                    user__groups__name='expert',
                    validation_complete=True,
                ).values('status').annotate(
                    worst_status=models.Case(
                        models.When(
                            validation_complete_executive=True, then=models.F('status')
                        ),
                        default=models.Min('status')
                    )
                ).values('worst_status')[:1],
                output_field=models.IntegerField()
            ),
            final_status=models.Case(
                models.When(
                    models.Q(
                        superexpert_status__isnull=False,
                    ),
                    then=models.F('superexpert_status')
                ),
                default=models.F("worst_expert_status"),
                output_field=models.IntegerField()
            )
        )

    def filter_by_status(self, status):
        return self.annotate_final_status().filter(
            final_status=status
        )

    def with_blocked_validations(self, days=settings.ENTOLAB_LOCK_PERIOD):
        return self.filter(
            pk__in=ExpertReportAnnotation.objects.blocked(days=days).values('report_id').distinct()
        )

    def unassigned(self, state: bool = True) -> QuerySet:
        # With no assignations at all.
        return self.annotate(
            has_annotations=models.Exists(
                ExpertReportAnnotation.objects.filter(
                    report=models.OuterRef('pk')
                ).values('pk')
            )
        ).filter(
            has_annotations=not state
        )

    def with_pending_validation_to_finish(self) -> QuerySet:
        return self.with_max_annotations(state=True).with_finished_validation(state=False)

    def in_progress(self):
        return self.queued().unassigned(state=False)

    def _filter_and_prioritize(self, user: Optional[User] = None) -> QuerySet:
        from .models import EuropeCountry

        qs = self

        if not user:
            # Nothing extra to prioritze. Return as is.
            return qs

        # Remove reports already asigned.
        qs = qs.exclude(
            expert_report_annotations__user=user
        )

        supervised_countries = UserStat.objects.filter(
            national_supervisor_of__isnull=False,
        ).values('national_supervisor_of').distinct()
        qs = qs.annotate(
            # NOTE: if ever need to order_by country count.
            # country_count=models.Window(
            #     expression=models.Count(1),
            #     partition_by=['country']
            # ),
            in_supervised_country=models.Case(
                models.When(country__in=supervised_countries, then=True),
                default=False,
                output_field=models.BooleanField()
            )
        ).order_by("-in_supervised_country", "-server_upload_time")

        if user.userstat.is_superexpert():
            # Nothing extra to prioritze. Return as is.
            return qs

        # Start pioritization:
        # Summary:
        # - Case user in bounding box:
        #       1. Report.country is the bounding box
        # - Other (expert and national supervisor):
        #       1. Report.country is not bounding box
        #       2. Report is not in the exclusivity period (except for its country if user is national supervisor)
        #       3. Sort by:
        #           European user:
        #               1. Report is in europe
        #               2. Report is user's country
        #               3. Append default ordering
        #           Spanish user:
        #               1. Report is in spain and nuts2 region
        #               2. Report is in spain
        #               3. Report is in europe
        #               4. Append default ordering
        if user.userstat.is_bb_user():
            # Case user in a bounding box
            qs = qs.filter(
                country=user.userstat.native_of
            )
        else:
            # Case regular user (expert and national supervisors)
            qs = qs.filter(
                country__is_bounding_box=False
            )

            # Reports outside the exclusivity period
            qs = qs.in_supervisor_exclusivity_period(
                state=False,
                for_user=user
            )

            # Prioritize for user
            if user.groups.filter(name='eu_group_europe').exists():
                # Case European user: Prioritize reports from own country
                qs = qs.annotate(
                    in_user_country=models.Case(
                        models.When(
                            country=user.userstat.national_supervisor_of or user.userstat.native_of,
                            then=True
                        ),
                        default=False,
                        output_field=models.BooleanField()
                    )
                ).order_by(
                    # NOTE: appending here all the field to be ordered_by since order_by function
                    #       can not be chained, and each order_by cal will clear any previous ordering.
                    *(
                        ('-in_user_country',) + qs.query.order_by
                    )
                )
            else:
                # Case Non European user: Prioritize reports from nuts2 assignation, then spain, the Europe.
                spain_country = EuropeCountry.objects.spain()
                qs = qs.annotate(
                    in_spain_own_region=models.Case(
                        models.When(
                            models.Q(
                                country=spain_country,
                                nuts_2=user.userstat.nuts2_assignation.nuts_id if user.userstat.nuts2_assignation else None
                            ),
                            then=True
                        ),
                        default=False,
                        output_field=models.BooleanField()
                    ),
                    # NOTE: can not name "is_spain" due to conflict with a @property named the same in the model class.
                    in_spain=models.Case(
                        models.When(
                            country=spain_country,
                            then=True
                        ),
                        default=False,
                        output_field=models.BooleanField()
                    ),
                    in_europe=models.Case(
                        models.When(
                            country__isnull=False,
                            then=True
                        ),
                        default=False,
                        output_field=models.BooleanField()
                    )
                ).order_by(
                    # NOTE: appending here all the field to be ordered_by since order_by function
                    #       can not be chained, and each order_by cal will clear any previous ordering.
                    *(
                        ('-in_spain_own_region', '-in_spain', '-in_europe') + qs.query.order_by
                    )
                )

        return qs

    def queueable(self) -> QuerySet:
        return self.browsable().non_deleted().has_photos().filter(
            server_upload_time__year__gt=2021,
        )

    def with_max_annotations(self, state: bool = True) -> QuerySet:
        # Available to assign
        subquery = ExpertReportAnnotation.objects.filter(
            report=models.OuterRef('pk')
        ).annotate(
            count=models.Count(1)
        ).filter(
            count__gte=settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT
        )

        return self.annotate(
            has_max_annotations=models.Exists(subquery)
        ).filter(
            has_max_annotations=state,
        )

    def queued(self, user_prioritized: Optional[User] = None) -> QuerySet:

        qs = self.queueable().filter(type=self.model.TYPE_ADULT)

        if user_prioritized and user_prioritized.userstat and user_prioritized.userstat.is_superexpert():
            # Only get reports with all annotations finished.
            qs = qs.with_finished_validation(state=True)
        else:
            # Available to assign
            qs = qs.with_finished_validation(state=False).with_max_annotations(state=False)

        return qs._filter_and_prioritize(user=user_prioritized)

    def in_supervisor_exclusivity_period(self, state: bool = True, for_user: Optional[User] = None):
        # Get reports that (meet all of):
        #     1. Inside the exclusivity window
        #     2. Country has supervisors
        #     3. Supervisor has not validated yet.
        lookup = models.Q(
            models.Q(
                country__isnull=False,
                country_has_supervisors=True,
                server_upload_time__gte=models.ExpressionWrapper(
                    timezone.now() - timedelta(days=1) * Coalesce(
                        models.F('country__national_supervisor_report_expires_in'),
                        settings.DEFAULT_EXPIRATION_DAYS
                    ),
                    output_field=fields.DateTimeField()
                ),
                supervisor_has_validated=False
            ),
            _negated=not state
        )

        if not state and for_user:
            if for_user.userstat.national_supervisor_of:
                # Supervisor can bypass the exclusivity period only in its country
                lookup |= models.Q(country=for_user.userstat.national_supervisor_of)

        # Using Exists subquery since it's faster than using JOIN.
        supervisor_has_validated_subquery = ExpertReportAnnotation.objects.filter(
            report=models.OuterRef('pk'),
            validation_complete=True,
            user__userstat__national_supervisor_of__isnull=False,
            user__userstat__national_supervisor_of=models.OuterRef('country'),
        )
        country_has_supervisors_subquery = UserStat.objects.filter(
            national_supervisor_of__isnull=False,
            national_supervisor_of=models.OuterRef('country')
        )

        return self.annotate(
            supervisor_has_validated=models.Exists(supervisor_has_validated_subquery.values('pk')),
            country_has_supervisors=models.Exists(country_has_supervisors_subquery.values('pk'))
        ).filter(lookup)

ReportManager = models.Manager.from_queryset(ReportQuerySet)

class PhotoQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(hide=False)

PhotoManager = models.Manager.from_queryset(PhotoQuerySet)

class NotificationQuerySet(models.QuerySet):
    def for_user(self, user: 'TigaUser'):
        from .models import SentNotification

        sent_notifications_subquery = SentNotification.objects.filter(
            notification=models.OuterRef('pk')
        ).filter(
            models.Q(sent_to_user=user) |
            models.Q(sent_to_topic__topic_code='global') |
            models.Q(sent_to_topic__topic_users__user=user)
        ).values('notification').distinct('notification')

        return self.filter(
            models.Q(user=user) | 
            #models.Q(report__user=user) | 
            models.Q(pk__in=models.Subquery(sent_notifications_subquery))
        )

    def seen_by_user(self, user: 'TigaUser', state: bool = True):
        return self.filter(
            models.Q(
                models.Q(
                    notification_acknowledgements__user=user
                ) | models.Q(
                    user=user,
                    acknowledged=True
                ),
                _negated=not state
            )
        )

NotificationManager = models.Manager.from_queryset(NotificationQuerySet)

class DeviceQuerySet(FCMDeviceQuerySet):
    def deactivate_devices_with_error_results(self, *args, **kwargs):
        deactivated_ids = super().deactivate_devices_with_error_results(*args, **kwargs)

        self.filter(registration_id__in=deactivated_ids).update(is_logged_in=False)

        return deactivated_ids

class DeviceManager(FCMDeviceManager):
    def get_queryset(self):
        return DeviceQuerySet(self.model)

class EuropeCountryQuerySet(models.QuerySet):
    def spain(self):
        return self.get(gid=17)

EuropeCountryManager = models.Manager.from_queryset(EuropeCountryQuerySet)