from datetime import timedelta
from typing import Tuple, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import fields
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from tigacrafting.models import ExpertReportAnnotation, UserStat

class ReportQuerySet(models.QuerySet):

    def __version_subquery(self):
        # NOTE: need to force using "objects" (default manager)
        return self.model._default_manager.filter(
            user=models.OuterRef('user'), 
            report_id=models.OuterRef('report_id'), 
            type=models.OuterRef('type')
        )
    
    def __latest_version_subquery(self):
        return self.__version_subquery().order_by('-version_number', '-server_upload_time')

    def last_version_of_each(self):
        return self.filter(
            pk__in=models.Subquery(
                self.__latest_version_subquery().values('pk')[:1]
            )
        )

    def non_deleted(self):
        return self.annotate(
            has_negative_version=models.Exists(
                self.__version_subquery().filter(version_number=-1).values('pk')
            )
        ).exclude(
            version_number=-1
        ).filter(
            has_negative_version=False
        )

    def in_bbox(self, bottom_left_point: Tuple[float, float], top_right_point: Tuple[float, float], state: bool=True):
        # bottom_left_point = (lon, lat)
        # top_right_point = (lon, lat)

        bbox_filter = models.Q(
            models.Q(
                location_choice='selected',
                selected_location_lon__range=(
                    bottom_left_point[0],
                    top_right_point[0]
                ),
                selected_location_lat__range=(
                    bottom_left_point[1],
                    top_right_point[1]
                )
            ) |
            models.Q(
                location_choice='current',
                current_location_lon__range=(
                    bottom_left_point[0],
                    top_right_point[0]
                ),
                current_location_lat__range=(
                    bottom_left_point[1],
                    top_right_point[1]
                )
            ),
            _negated=not state
        )

        return self.filter(bbox_filter)

    def in_barcelona(self, state: bool=True):
        return self.in_bbox(
            bottom_left_point=(
                settings.BCN_BB['min_lon'],
                settings.BCN_BB['min_lat']
            ),
            top_right_point=(
                settings.BCN_BB['max_lon'],
                settings.BCN_BB['max_lat']
            ),
            state=state
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
            has_finished_validation=models.Exists(subquery)
        ).filter(
            has_finished_validation=state
        )

    def with_blocked_validations(self, days=settings.ENTOLAB_LOCK_PERIOD):
        from tigacrafting.models import ExpertReportAnnotation

        return self.filter(
            pk__in=ExpertReportAnnotation.objects.blocked(days=days).values('report')
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
        from .models import Photo

        return self.last_version_of_each().non_deleted().annotate(
            has_photos=models.Exists(
                Photo.objects.filter(report=models.OuterRef('pk')).values('pk')
            )
        ).exclude(
            note__icontains="#345",
        ).filter(
            has_photos=True,
            server_upload_time__year__gt=2021,
            hide=False,
            type=self.model.TYPE_ADULT
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

        qs = self.queueable()

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

class EuropeCountryQuerySet(models.QuerySet):
    def spain(self):
        return self.get(gid=17)
    
EuropeCountryManager = models.Manager.from_queryset(EuropeCountryQuerySet)