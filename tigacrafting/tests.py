from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import EuropeCountry, TigaUser, Report, ExpertReportAnnotation
from tigacrafting.models import UserStat
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from operator import attrgetter
import pytz

###                 HELPER STUFF                ########################################################################

BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}


def user_summary(user):
    print("############################################".format(user.username, ))
    print("#### USER - {0} \t\t####".format(user.username,))
    assigned_reports = ExpertReportAnnotation.objects.filter(user=user).filter(report__type='adult').values('report').distinct()
    assigned_reports_count = assigned_reports.count()
    print("#### National supervisor - {0} \t\t####".format( 'Yes' if user.userstat.is_national_supervisor() else 'No', ))
    if user.userstat.is_national_supervisor():
        print("#### Supervised country - {0} \t\t####".format(user.userstat.national_supervisor_of.name_engl))
    print("#### Assigned reports - {0} \t\t####".format(str(assigned_reports_count), ))
    reports = Report.objects.filter(version_UUID__in=assigned_reports)
    for r in reports:
        print("#### Report {0} - {1} \t\t####".format(r.version_UUID, str(r.country), ))
    print("############################################".format(user.username, ))
    print("")


def filter_false_validated(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: (not x.deleted) and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports)
    return reports_filtered


def filter_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version, reports),key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
    return reports_filtered

###                END HELPER STUFF                #####################################################################


class UserTestCase(TestCase):
    fixtures = ['europe_countries.json',]

    def create_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        a = 1
        for country in EuropeCountry.objects.all():
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a),
                version_number=0,
                user_id='00000000-0000-0000-0000-000000000000',
                phone_upload_time=non_naive_time,
                server_upload_time=non_naive_time,
                creation_time=non_naive_time,
                version_time=non_naive_time,
                location_choice="current",
                current_location_lon=point_on_surface.x,
                current_location_lat=point_on_surface.y,
                type='adult',
            )
            r.save()
            a = a + 1

    def create_team(self):
        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()
        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_es'
        u2.save()
        u3 = User.objects.create(pk=3)
        u3.username = 'expert_3_eu'
        c = EuropeCountry.objects.get(pk=45)  # Isle of man
        u3.userstat.national_supervisor_of = c
        u3.save()
        u4 = User.objects.create(pk=4)
        u4.username = 'expert_4_es'
        u4.save()
        u5 = User.objects.create(pk=5)
        u5.username = 'expert_5_eu'
        c = EuropeCountry.objects.get(pk=1)  # Bosnia Herzegovina
        u5.userstat.national_supervisor_of = c
        u5.save()
        u6 = User.objects.create(pk=6)
        u6.username = 'expert_6_es'
        u6.save()

    #tests that user creation triggers userstat creation
    def test_create_user_and_userstat(self):
        u = User.objects.create(pk=1)
        u.username = 'test_user_1'
        u.save()
        # should have created user stat
        self.assertNotEqual(u.userstat, None)
        u.delete()

    #tests that u.save() also saves state of u.userstat
    def test_user_save_causes_userstat_save(self):
        u = User.objects.create(pk=2)
        u.username = 'test_user_2'
        u.save()
        initial_grabbed_reports = 1
        final_grabbed_reports = 2
        u.userstat.grabbed_reports = initial_grabbed_reports
        u.save()
        saved_initial_grabbed_reports = u.userstat.grabbed_reports
        u.userstat.grabbed_reports = final_grabbed_reports
        u.save()
        saved_final_grabbed_reports = u.userstat.grabbed_reports
        self.assertNotEqual(saved_initial_grabbed_reports, saved_final_grabbed_reports)
        u.delete()

    #tests that national_supervisor_of is correctly assigned and control methods is_national_supervisor and is_national_supervisor_for_country
    #work correctly
    def test_make_user_national_supervisor(self):
        u = User.objects.create(pk=3)
        u.username = 'test_user_3'
        u.save()
        c = EuropeCountry.objects.get(pk=1) #Bosnia Herzegovina
        u.userstat.national_supervisor_of = c
        u.save()
        self.assertEqual( u.userstat.national_supervisor_of.gid, 1 )
        self.assertEqual( u.userstat.is_national_supervisor(), True )
        self.assertEqual( u.userstat.is_national_supervisor_for_country( c ), True)
        u.delete()

    # available reports
    # separate in available reports own country / available reports other
    # if user is national supervisor
    #   if available reports belong to supervised country
    #       assign to user
    # else if not national supervisor
    #   if there is supervisor for country report belongs to
    #       if is assigned to supervisor
    #           assign to user
    #   else if there is no supervisor
    #       assign to user

    def test_assign_reports(self):
        self.create_team()
        self.create_report_pool()
        current_pending = 0
        max_pending = 5
        max_given = 3
        national_supervisor_ids = UserStat.objects.filter(national_supervisor_of__isnull=False).values('user__id').distinct()
        country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
        country_with_supervisor_set = set([d['national_supervisor_of__gid'] for d in country_with_supervisor])
        for this_user in User.objects.all():
            report_assigned_to_supervisor = ExpertReportAnnotation.objects.filter(user__id__in=national_supervisor_ids).values('report').distinct()
            report_assigned_to_supervisor_set = set([d['report'] for d in report_assigned_to_supervisor])
            this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
            this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
            this_user_is_supervisor = this_user.userstat.is_national_supervisor()
            my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
            if current_pending < max_pending:
                n_to_get = max_pending - current_pending
                new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)
                if new_reports_unfiltered and this_user_is_team_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected',selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if new_reports_unfiltered and this_user_is_team_not_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected',selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'],BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if this_user_is_supervisor:
                    reports_supervised_country = new_reports_unfiltered.filter( country__gid=this_user.userstat.national_supervisor_of.gid )
                    reports_non_supervised_country = new_reports_unfiltered.exclude( version_UUID__in=reports_supervised_country.values('version_UUID') )
                    reports_supervised_country_filtered = filter_reports(reports_supervised_country.order_by('creation_time'))
                    reports_non_supervised_country_filtered = filter_reports(reports_non_supervised_country.order_by('creation_time'))
                    new_filtered_reports = reports_supervised_country_filtered + reports_non_supervised_country_filtered
                else:
                    new_filtered_reports = filter_reports(new_reports_unfiltered.order_by('creation_time'))
                new_reports = new_filtered_reports

                grabbed_reports = -1
                reports_taken = 0
                for this_report in new_reports:
                    new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                    who_has_count = this_report.get_who_has_count()
                    if this_user_is_supervisor:
                        if this_user.userstat.is_national_supervisor_for_country( this_report.country ):
                            new_annotation.simplified_annotation = False
                            grabbed_reports += 1
                            reports_taken += 1
                            new_annotation.save()
                        else:
                            if who_has_count == 0 or who_has_count == 1:
                                new_annotation.simplified_annotation = True
                            grabbed_reports += 1
                            reports_taken += 1
                            new_annotation.save()
                    else:
                        if this_report.country is None:
                            if who_has_count == 0 or who_has_count == 1:
                                new_annotation.simplified_annotation = True
                            else:
                                new_annotation.simplified_annotation = False
                            grabbed_reports += 1
                            reports_taken += 1
                            new_annotation.save()
                        else:
                            if this_report.country.gid in country_with_supervisor_set:
                                if this_report.version_UUID in report_assigned_to_supervisor_set:
                                    #if who_has_count <= 1:
                                    if who_has_count == 0 or who_has_count == 1:
                                        new_annotation.simplified_annotation = True
                                    else:
                                        new_annotation.simplified_annotation = False
                                    grabbed_reports += 1
                                    reports_taken += 1
                                    new_annotation.save()
                            else:
                                if who_has_count == 0 or who_has_count == 1:
                                    new_annotation.simplified_annotation = True
                                else:
                                    new_annotation.simplified_annotation = False
                                grabbed_reports += 1
                                reports_taken += 1
                                new_annotation.save()
                    if reports_taken == n_to_get:
                        break
                this_user.userstat.grabbed_reports = grabbed_reports
                this_user.userstat.save()

        for usr in User.objects.all():
            user_summary(usr)