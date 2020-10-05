from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from tigaserver_app.models import EuropeCountry, TigaUser, Report, ExpertReportAnnotation, Photo, NotificationContent, Notification
from tigacrafting.models import UserStat, ExpertReportAnnotation, Categories, Complex
from tigacrafting.views import must_be_autoflagged
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from operator import attrgetter
from tigacrafting.views import assign_reports_to_user, issue_notification
import tigaserver_project.settings as conf
from django.utils import timezone
import pytz

###                 HELPER STUFF                ########################################################################

BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}


def user_summary(user):
    print("############################################".format(user.username, ))
    print("#### USER - {0} \t\t####".format(user.username,))
    assigned_reports = ExpertReportAnnotation.objects.filter(user=user).filter(report__type='adult').values('report').distinct()
    assigned_reports_count = assigned_reports.count()
    if user.groups.filter(name='eu_group_europe').exists():
        print("#### Group - europe \t\t####")
    elif user.groups.filter(name='eu_group_spain').exists:
        print("#### Group - spain \t\t####")
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
    fixtures = ['europe_countries.json','reritja_like.json','granter_user.json','awardcategory.json']

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
            p = Photo.objects.create(report=r, photo='/home/webuser/webapps/tigaserver/media/tigapics/splash.png')
            p.save()
            a = a + 1

    def create_team(self):

        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.create(name='expert')
        experts.save()

        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()
        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_eu'
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
        c = EuropeCountry.objects.get(pk=22)  # Faroes
        u5.userstat.national_supervisor_of = c
        u5.save()
        u6 = User.objects.create(pk=6)
        u6.username = 'expert_6_es'
        u6.save()
        u7 = User.objects.create(pk=7)
        u7.username = 'expert_7_eu'
        c = EuropeCountry.objects.get(pk=8)  # Norway
        u7.userstat.national_supervisor_of = c
        u7.save()
        u8 = User.objects.create(pk=8)
        u8.username = 'expert_8_es'
        u8.save()
        u9 = User.objects.create(pk=9)
        u9.username = 'expert_9_eu'
        u9.save()
        u10 = User.objects.create(pk=10)
        u10.username = 'expert_10_eu'
        u10.save()

        europe_group.user_set.add(u2)
        europe_group.user_set.add(u3)
        europe_group.user_set.add(u5)
        europe_group.user_set.add(u7)
        europe_group.user_set.add(u9)
        europe_group.user_set.add(u10)

        experts.user_set.add(u1)
        experts.user_set.add(u2)
        experts.user_set.add(u3)
        experts.user_set.add(u4)
        experts.user_set.add(u5)
        experts.user_set.add(u6)
        experts.user_set.add(u7)
        experts.user_set.add(u8)
        experts.user_set.add(u9)
        experts.user_set.add(u10)

    # tests that user creation triggers userstat creation
    def test_create_user_and_userstat(self):
        u = User.objects.create(pk=1)
        u.username = 'test_user_1'
        u.save()
        # should have created user stat
        self.assertNotEqual(u.userstat, None)
        u.delete()

    # tests that u.save() also saves state of u.userstat
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

    # tests that national_supervisor_of is correctly assigned and control methods is_national_supervisor and
    # is_national_supervisor_for_country work correctly
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


    @staticmethod
    def has_national_supervisor_assigned(annotations, country):
        for anno in annotations:
            if anno.user.userstat.is_national_supervisor_for_country(country):
                return True
        return False

    @staticmethod
    def national_supervisor_assigned_last(annotations, country):
        last_annotation = annotations.order_by('-created').first()
        return last_annotation.user.userstat.is_national_supervisor() and last_annotation.user.userstat.is_national_supervisor_for_country(country)
        #return True

    # tests that all users are:
    # - assigned max_pending reports
    # - if users are supervisors, they are assigned the report(s) for the country they supervise
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
            assign_reports_to_user(this_user, national_supervisor_ids, current_pending, country_with_supervisor_set, max_pending, max_given)
            #user_summary(this_user)

        for report in Report.objects.all():
            annotations = ExpertReportAnnotation.objects.filter(report=report).filter(user__groups__name='expert')
            assigned_to = annotations.count()
            self.assertLessEqual(assigned_to, 3, msg="Report {0} assigned to more than 3 experts!".format(report.version_UUID))
            if assigned_to == 3:
                #check if there is regional manager for country of report
                if self.has_national_supervisor_assigned(annotations.all(), report.country):
                    #if there is regional manager, it should be assigned last
                    self.assertEqual(self.national_supervisor_assigned_last(annotations, report.country), True, msg="Report {0} not assigned last to national supervisor".format(report.version_UUID))

        # for usr in User.objects.all():
        #     n = ExpertReportAnnotation.objects.filter(user=usr).filter(report__type='adult').values('report').distinct().count()
        #     if usr.userstat.is_national_supervisor():
        #         assigned_supervised = ExpertReportAnnotation.objects.filter(user=usr).filter(report__type='adult').filter(report__country__gid=usr.userstat.national_supervisor_of.gid).exists()
        #         if assigned_supervised == False:
        #             print("User " + usr.username + " has not been assigned supervised")
        #         self.assertEqual(n, max_pending)
        #         self.assertEqual(assigned_supervised, True)
        #     else:
        #         if usr.groups.filter(name='eu_group_europe').exists():
        #             self.assertEqual(n, max_pending)
        #         elif usr.groups.filter(name='eu_group_spain').exists():
        #             self.assertTrue(n == 1 or n == 0)

        # Enable this for extra verbose info
        # for usr in User.objects.all():
        #     user_summary(usr)


    def test_autoflag_report(self):
        self.create_team()
        self.create_report_pool()
        r = Report.objects.get(pk='1')
        self.assertEqual(r.version_UUID,'1')

        user_spain_1 = User.objects.get(username='expert_1_es')
        user_spain_4 = User.objects.get(username='expert_4_es')
        user_spain_6 = User.objects.get(username='expert_6_es')

        c_1 = Categories.objects.create(pk=1,name='Red',specify_certainty_level=False)
        c_1.save()
        c_2 = Categories.objects.create(pk=2, name='Orange', specify_certainty_level=False)
        c_2.save()
        c_3 = Categories.objects.create(pk=3, name='Blue', specify_certainty_level=False)
        c_3.save()

        cp_1 = Complex.objects.create(pk=1, description="Green/Teal")
        cp_1.save()

        anno_u1 = ExpertReportAnnotation.objects.create(user=user_spain_1, report=r, category=c_1, validation_complete=True)
        anno_u1.save()
        anno_u4 = ExpertReportAnnotation.objects.create(user=user_spain_4, report=r, category=c_2,validation_complete=True)
        anno_u4.save()
        anno_u6 = ExpertReportAnnotation.objects.create(user=user_spain_6, report=r, category=c_3,validation_complete=True)
        anno_u6.save()

        #Three different categories -> Conflict
        autoflag_question_mark = must_be_autoflagged(anno_u6, anno_u6.validation_complete)
        self.assertEqual( autoflag_question_mark, True )

        anno_u6.category = None
        anno_u6.complex = cp_1
        anno_u6.save()

        # Two categories, one conflict -> Conflict
        autoflag_question_mark = must_be_autoflagged(anno_u6, anno_u6.validation_complete)
        self.assertEqual(autoflag_question_mark, True)

        anno_u6.category = c_1
        anno_u6.complex = None
        anno_u6.save()

        # Two equal categories, one different -> No Conflict
        autoflag_question_mark = must_be_autoflagged(anno_u6, anno_u6.validation_complete)
        self.assertEqual(autoflag_question_mark, False)

    def test_validation_notification(self):
        self.create_report_pool()
        r = Report.objects.get(pk='1')
        reritja_user = User.objects.get(pk=25)
        superexperts_group = Group.objects.create(name='superexpert')
        superexperts_group.user_set.add(reritja_user)
        reritja_user.save()
        superexperts_group.save()

        c_1 = Categories.objects.create(pk=1, name="Unclassified", specify_certainty_level=False)
        c_1.save()
        c_2 = Categories.objects.create(pk=2, name="Other species", specify_certainty_level=False)
        c_2.save()
        c_3 = Categories.objects.create(pk=3, name="Aedes albopictus", specify_certainty_level=True)
        c_3.save()
        c_4 = Categories.objects.create(pk=4, name="Aedes aegypti", specify_certainty_level=True)
        c_4.save()
        c_5 = Categories.objects.create(pk=5, name="Aedes japonicus", specify_certainty_level=True)
        c_5.save()
        c_6 = Categories.objects.create(pk=6, name="Aedes koreicus", specify_certainty_level=True)
        c_6.save()
        c_7 = Categories.objects.create(pk=7, name="Complex", specify_certainty_level=False)
        c_7.save()
        c_8 = Categories.objects.create(pk=8, name="Not sure", specify_certainty_level=False)
        c_8.save()
        c_9 = Categories.objects.create(pk=9, name="Culex sp.", specify_certainty_level=True)
        c_9.save()

        validation_value_possible = 1
        validation_value_confirmed = 2

        for l in conf.LANGUAGES:
            locale = l[0]
            if locale != 'zh-cn':
                r.app_language = locale
                r.save()
                anno_reritja = ExpertReportAnnotation.objects.create(user=reritja_user, report=r, category=c_3,
                                                                     validation_complete=True, revise=True,
                                                                     validation_value=validation_value_confirmed)
                anno_reritja.save()
                issue_notification(anno_reritja, "http://127.0.0.1:8000")
                nc = NotificationContent.objects.first()
                print(nc.title_en)
                Notification.objects.all().delete()
                NotificationContent.objects.all().delete()
        pass