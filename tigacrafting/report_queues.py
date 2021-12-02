from tigaserver_app.models import Report, ExpertReportAnnotation, EuropeCountry
from django.core.exceptions import ObjectDoesNotExist
from tigacrafting.models import UserStat
from django.db.models.expressions import RawSQL
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Q
from datetime import date, datetime, timedelta
import operator
import functools

MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT = 3
MAX_N_OF_PENDING_REPORTS = 5
BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}


def get_base_adults_qs():
    return Report.objects.exclude(creation_time__year=2014).exclude(creation_time__year=2015).exclude(note__icontains="#345").exclude(hide=True).exclude(photos__isnull=True).filter(type='adult')


def get_deleted_adult_reports(qs):
    return qs.filter(version_number=-1).values('report_id').distinct()


def filter_reports_for_superexpert(reports):
    # not deleted, last version, completely validated by at least three experts
    deleted_adult_reports = get_deleted_adult_reports(reports)
    # not deleted
    undeleted = reports.exclude(report_id__in=deleted_adult_reports)
    # last version
    latest_versions = undeleted.filter(version_UUID__in=RawSQL("select \"version_UUID\" from tigaserver_app_report r,(select report_id, max(version_number) as higher from tigaserver_app_report group by report_id) maxes where r.report_id = maxes.report_id and r.version_number = maxes.higher",()))
    # fully validated
    experts = User.objects.filter(groups__name='expert')
    fully_validated = ExpertReportAnnotation.objects.filter(report__in=latest_versions).filter(user__in=experts).filter(validation_complete=True).values('report').annotate(n_validations=Count('report')).filter(n_validations__gte=MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT)
    report_ids = set(fully_validated.values_list('report', flat=True))
    filtered_reports = latest_versions.filter(version_UUID__in=report_ids)
    #filtered_reports = filter(lambda x: len(list(filter(lambda y: y.is_expert() and y.validation_complete, x.expert_report_annotations.all()))) >= 3, latest_versions)
    return filtered_reports


def filter_reports(reports):
    #not deleted, last version
    deleted_adult_reports = get_deleted_adult_reports(reports)
    # not deleted
    undeleted = reports.exclude(report_id__in=deleted_adult_reports)
    # last version
    latest_versions = undeleted.filter(version_UUID__in=RawSQL("select \"version_UUID\" from tigaserver_app_report r,(select report_id, max(version_number) as higher from tigaserver_app_report group by report_id) maxes where r.report_id = maxes.report_id and r.version_number = maxes.higher",()))
    return latest_versions


def assign_reports_to_national_supervisor(this_user):
    current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
    supervised_country = this_user.userstat.national_supervisor_of
    if current_pending < MAX_N_OF_PENDING_REPORTS:
        my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
        n_to_get = MAX_N_OF_PENDING_REPORTS - current_pending
        country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
        bounding_boxes = EuropeCountry.objects.filter(is_bounding_box=True)
        reports_supervised_country = get_base_adults_qs().filter(country__gid=supervised_country.gid).annotate(n_annotations=Count('expert_report_annotations'))

        # These are unassigned reports from supervised country, should be prioritized
        reports_supervised_country = reports_supervised_country.filter(n_annotations=0).exclude( Q(country=supervised_country) & ~Q(server_upload_time__gte=datetime.now() - timedelta(days=supervised_country.national_supervisor_report_expires_in)) )

        # list of countries with supervisor (excluding present)
        country_with_supervisor_other_than_this = EuropeCountry.objects.filter(gid__in=country_with_supervisor).exclude(gid=supervised_country.gid)
        reserved_for_supervised_countries_operator_list = []
        for country in country_with_supervisor_other_than_this:
            if country.national_supervisor_report_expires_in is not None:
                expiration_period = country.national_supervisor_report_expires_in
            else:
                expiration_period = 14
            reserved_for_supervised_countries_operator_list.append(Q(country=country) & Q(server_upload_time__gte=datetime.now() - timedelta(days=country.national_supervisor_report_expires_in)))
        new_reports_unfiltered = get_base_adults_qs().exclude(country__in=bounding_boxes).exclude(version_UUID__in=my_reports).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT)
        #reports_unfiltered_excluding_reserved_ns = new_reports_unfiltered.exclude(functools.reduce(operator.or_, reserved_for_supervised_countries_operator_list))
        for condition in reserved_for_supervised_countries_operator_list:
            new_reports_unfiltered = new_reports_unfiltered.exclude(condition)
        reports_unfiltered_excluding_reserved_ns = new_reports_unfiltered.filter(~Q(country__gid=17) & Q(country__gid__isnull=False))
        reports_assigned_to_supervisor_not_yet_validated = ExpertReportAnnotation.objects.filter(user__userstat__national_supervisor_of__in=country_with_supervisor).filter(report__type='adult').filter(validation_complete=False).values('report').distinct()
        blocked_by_experts = get_base_adults_qs().filter(version_UUID__in=reports_assigned_to_supervisor_not_yet_validated)
        reports_unfiltered_excluding_reserved_ns = reports_unfiltered_excluding_reserved_ns.exclude(version_UUID__in=blocked_by_experts)

        country_filtered_reports = filter_reports(reports_supervised_country.order_by('creation_time'))
        other_countries_filtered_reports = filter_reports(reports_unfiltered_excluding_reserved_ns.order_by('creation_time'))

        currently_taken = 0
        user_stats = None
        try:
            user_stats = UserStat.objects.get(user_id=this_user.id)
        except ObjectDoesNotExist:
            pass
        grabbed_reports = -1
        if user_stats:
            grabbed_reports = user_stats.grabbed_reports

        # for national supervisor, reports from supervised country are never simplified if granted first
        for this_report in country_filtered_reports:
            new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
            grabbed_reports += 1
            new_annotation.save()
            currently_taken += 1
            if currently_taken >= MAX_N_OF_PENDING_REPORTS:
                break

        if currently_taken < MAX_N_OF_PENDING_REPORTS:
            for this_report in other_countries_filtered_reports:
                new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                who_has_count = this_report.get_who_has_count()
                if who_has_count == 0 or who_has_count == 1:
                    # No one has the report, is simplified
                    new_annotation.simplified_annotation = True
                grabbed_reports += 1
                new_annotation.save()
                currently_taken += 1
                if currently_taken >= MAX_N_OF_PENDING_REPORTS:
                    break

        if grabbed_reports != -1 and user_stats:
            user_stats.grabbed_reports = grabbed_reports
            user_stats.save()
        # reports_unfiltered = reports_supervised_country.order_by('creation_time') | reports_unfiltered_excluding_reserved_ns.order_by('creation_time')
        # if reports_unfiltered:
        #     new_reports = filter_reports(reports_unfiltered)
        #     reports_to_take = new_reports[0:n_to_get]
        #     user_stats = None
        #     try:
        #         user_stats = UserStat.objects.get(user_id=this_user.id)
        #     except ObjectDoesNotExist:
        #         pass
        #     grabbed_reports = -1
        #     if user_stats:
        #         grabbed_reports = user_stats.grabbed_reports
        #     for this_report in reports_to_take:
        #         if not this_report.user_has_report(this_user):
        #             new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
        #             who_has_count = this_report.get_who_has_count()
        #             if who_has_count == 0 or who_has_count == 1:
        #                 # No one has the report, is simplified
        #                 new_annotation.simplified_annotation = True
        #             grabbed_reports += 1
        #             new_annotation.save()
        #     if grabbed_reports != -1 and user_stats:
        #         user_stats.grabbed_reports = grabbed_reports
        #         user_stats.save()



def assign_reports_to_regular_user(this_user):
    current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
    if current_pending < MAX_N_OF_PENDING_REPORTS:
        my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
        n_to_get = MAX_N_OF_PENDING_REPORTS - current_pending
        country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
        bounding_boxes = EuropeCountry.objects.filter(is_bounding_box=True)
        supervised_countries = EuropeCountry.objects.filter(gid__in=country_with_supervisor)
        reserved_for_supervised_countries_operator_list = []
        for country in supervised_countries:
            if country.national_supervisor_report_expires_in is not None:
                expiration_period = country.national_supervisor_report_expires_in
            else:
                expiration_period = 14
            reserved_for_supervised_countries_operator_list.append( Q(country=country) & Q(server_upload_time__gte=datetime.now() - timedelta(days=country.national_supervisor_report_expires_in)) )
        new_reports_unfiltered = get_base_adults_qs().exclude(country__in=bounding_boxes).exclude(version_UUID__in=my_reports).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT)
        #reports_unfiltered_excluding_reserved_ns = new_reports_unfiltered.exclude( functools.reduce(operator.or_, reserved_for_supervised_countries_operator_list) )
        for condition in reserved_for_supervised_countries_operator_list:
            new_reports_unfiltered = new_reports_unfiltered.exclude(condition)
        if this_user.groups.filter(name='eu_group_europe').exists(): #Europe
            reports_unfiltered_excluding_reserved_ns = new_reports_unfiltered.filter( ~Q(country__gid=17) & Q(country__gid__isnull=False) )
        else: #Spain
            reports_unfiltered_excluding_reserved_ns = new_reports_unfiltered.filter( Q(country__gid=17) | Q(country__gid__isnull=True) )
        #exclude reports assigned to ANY supervisor but not yet validated
        reports_assigned_to_supervisor_not_yet_validated = ExpertReportAnnotation.objects.filter(user__userstat__national_supervisor_of__in=country_with_supervisor).filter(report__type='adult').filter(validation_complete=False)
        for country in supervised_countries:
            reports_assigned_to_supervisor_not_yet_validated = reports_assigned_to_supervisor_not_yet_validated.exclude( Q(report__country=country) & Q(report__server_upload_time__lt=datetime.now() - timedelta(days=country.national_supervisor_report_expires_in)) )
        reports_assigned_to_supervisor_not_yet_validated = reports_assigned_to_supervisor_not_yet_validated.values('report').distinct()
        blocked_by_experts = get_base_adults_qs().filter(version_UUID__in=reports_assigned_to_supervisor_not_yet_validated)
        reports_unfiltered_excluding_reserved_ns = reports_unfiltered_excluding_reserved_ns.exclude(version_UUID__in=blocked_by_experts)
        if reports_unfiltered_excluding_reserved_ns:
            new_reports = filter_reports(reports_unfiltered_excluding_reserved_ns.order_by('creation_time'))
            if not this_user.groups.filter(name='eu_group_europe').exists(): #Spain
                reports_to_take = new_reports[0:n_to_get]
                user_stats = None
                try:
                    user_stats = UserStat.objects.get(user_id=this_user.id)
                except ObjectDoesNotExist:
                    pass
                grabbed_reports = -1
                if user_stats:
                    grabbed_reports = user_stats.grabbed_reports
                for this_report in reports_to_take:
                    new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                    who_has_count = this_report.get_who_has_count()
                    if who_has_count == 0 or who_has_count == 1:
                        # No one has the report, is simplified
                        new_annotation.simplified_annotation = True
                    grabbed_reports += 1
                    new_annotation.save()
                if grabbed_reports != -1 and user_stats:
                    user_stats.grabbed_reports = grabbed_reports
                    user_stats.save()
            else: #Europe -> prioritize reports from own country
                new_reports_own_country = new_reports.filter(country=this_user.userstat.native_of)
                new_reports_other_countries = new_reports.exclude(country=this_user.userstat.native_of)

                currently_taken = 0
                user_stats = None
                try:
                    user_stats = UserStat.objects.get(user_id=this_user.id)
                except ObjectDoesNotExist:
                    pass
                grabbed_reports = -1
                if user_stats:
                    grabbed_reports = user_stats.grabbed_reports

                for this_report in new_reports_own_country:
                    new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                    grabbed_reports += 1
                    new_annotation.save()
                    currently_taken += 1
                    if currently_taken >= MAX_N_OF_PENDING_REPORTS:
                        break

                if currently_taken < MAX_N_OF_PENDING_REPORTS:
                    for this_report in new_reports_other_countries:
                        new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                        who_has_count = this_report.get_who_has_count()
                        if who_has_count == 0 or who_has_count == 1:
                            # No one has the report, is simplified
                            new_annotation.simplified_annotation = True
                        grabbed_reports += 1
                        new_annotation.save()
                        currently_taken += 1
                        if currently_taken >= MAX_N_OF_PENDING_REPORTS:
                            break
                if grabbed_reports != -1 and user_stats:
                    user_stats.grabbed_reports = grabbed_reports
                    user_stats.save()


def assign_superexpert_reports(this_user):
    my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
    new_reports_unfiltered = get_base_adults_qs().exclude(version_UUID__in=my_reports).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT)
    if new_reports_unfiltered and this_user.groups.filter(name='team_bcn').exists():
        new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
    if new_reports_unfiltered and this_user.groups.filter(name='team_not_bcn').exists():
        new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
    if this_user.id == 25:  # it's roger, don't assign reports from barcelona prior to 03/10/2017
        new_reports_unfiltered = new_reports_unfiltered.exclude(Q(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current',current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'],BCN_BB['max_lat']))) & Q(creation_time__lte=date(2017, 3, 10)))
    new_reports = filter_reports_for_superexpert(new_reports_unfiltered)
    for this_report in new_reports:
        new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
        new_annotation.save()


def assign_bb_reports(this_user):
    current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
    if current_pending < MAX_N_OF_PENDING_REPORTS:
        my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
        n_to_get = MAX_N_OF_PENDING_REPORTS - current_pending
        new_reports_unfiltered = get_base_adults_qs().exclude(version_UUID__in=my_reports).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT)
        new_reports_unfiltered = new_reports_unfiltered.filter(country=this_user.userstat.native_of)
        if new_reports_unfiltered:
            new_reports = filter_reports(new_reports_unfiltered.order_by('creation_time'))
            reports_to_take = new_reports[0:n_to_get]
            user_stats = None
            try:
                user_stats = UserStat.objects.get(user_id=this_user.id)
            except ObjectDoesNotExist:
                pass
            grabbed_reports = -1
            if user_stats:
                grabbed_reports = user_stats.grabbed_reports
            for this_report in reports_to_take:
                new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                who_has_count = this_report.get_who_has_count()
                if who_has_count == 0 or who_has_count == 1:
                    # No one has the report, is simplified
                    new_annotation.simplified_annotation = True
                grabbed_reports += 1
                new_annotation.save()
            if grabbed_reports != -1 and user_stats:
                user_stats.grabbed_reports = grabbed_reports
                user_stats.save()


def assign_reports(this_user):
    if this_user.userstat.is_superexpert():
        assign_superexpert_reports(this_user)
    else:
        if this_user.userstat.is_bb_user():
            assign_bb_reports(this_user)
        else:
            if this_user.userstat.is_national_supervisor():
                assign_reports_to_national_supervisor(this_user)
            else: #is regular user
                assign_reports_to_regular_user(this_user)
