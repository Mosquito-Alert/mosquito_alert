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
from tigacrafting.views import issue_notification
import tigaserver_project.settings as conf
from django.utils import timezone
from common.translation import get_translation_in
import pytz
from tigacrafting.report_queues import *

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


def create_report(version_number, version_uuid, user, country):
    non_naive_time = timezone.now()
    point_on_surface = country.geom.point_on_surface
    r = Report(
        version_UUID=version_uuid,
        version_number=version_number,
        user=user,
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
    return r


# def filter_false_validated(reports, sort=True):
#     if sort:
#         reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports), key=attrgetter('n_annotations'), reverse=True)
#     else:
#         reports_filtered = filter(lambda x: (not x.deleted) and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports)
#     return reports_filtered


# def filter_reports(reports, sort=True):
#     if sort:
#         reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version, reports),key=attrgetter('n_annotations'), reverse=True)
#     else:
#         reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
#     return reports_filtered

###                END HELPER STUFF                #####################################################################


class NewReportAssignment(TestCase):
    fixtures = ['europe_countries_new.json', 'reritja_like.json', 'granter_user.json', 'awardcategory.json', 'nutseurope.json']

    def create_micro_team(self):

        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.create(name='expert')
        experts.save()
        superexperts = Group.objects.create(name='superexpert')
        superexperts.save()

        # National supervisor
        u1 = User.objects.create(pk=3)
        u1.username = 'expert_3_eu'
        c = EuropeCountry.objects.get(pk=45)  # Isle of man
        u1.userstat.national_supervisor_of = c
        u1.save()

        # Regular eu user 1
        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_eu'
        u2.userstat.native_of = EuropeCountry.objects.get(pk=8)  # Norway
        u2.save()

        # Regular eu user 2
        u3 = User.objects.create(pk=5)
        u3.username = 'expert_5_eu'
        u3.userstat.native_of = EuropeCountry.objects.get(pk=22)  # Faroes
        u3.save()

        europe_group.user_set.add(u1)
        europe_group.user_set.add(u2)
        europe_group.user_set.add(u3)

        experts.user_set.add(u1)
        experts.user_set.add(u2)
        experts.user_set.add(u3)

        reritja = User.objects.get(pk=25)
        superexperts.user_set.add(reritja)


    def create_team(self):

        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.create(name='expert')
        experts.save()
        superexperts = Group.objects.create(name='superexpert')
        superexperts.save()

        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()

        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_eu'
        u2.userstat.native_of = EuropeCountry.objects.get(pk=45)  # Isle of man
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
        u9.userstat.native_of = EuropeCountry.objects.get(pk=22)  # Faroes
        u9.save()

        u10 = User.objects.create(pk=10)
        u10.username = 'expert_10_eu'
        u10.userstat.native_of = EuropeCountry.objects.get(pk=22)  # Faroes
        u10.save()

        u12 = User.objects.create(pk=12)
        u12.username = 'expert_12_sl'
        u12.userstat.native_of = EuropeCountry.objects.get(pk=53)  # St Louis bb
        u12.save()

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

        reritja = User.objects.get(pk=25)
        superexperts.user_set.add(reritja)


    def create_outdated_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        country = EuropeCountry.objects.get(pk=45) #Isle of man
        # date threshold for reports that the national supervisor has lost priority over
        two_weeks_ago = non_naive_time - timedelta(days=country.national_supervisor_report_expires_in)
        a = 1
        while a < 3:
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
        #queryset update - trick to override the auto_now_add in server upload time. If this is not done, it defaults to current timestamp
        Report.objects.all().update(server_upload_time=two_weeks_ago)

        a = 1
        while a < 4:
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a+10),
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

        country = EuropeCountry.objects.get(pk=53)
        a = 1
        while a < 10:
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a+100),
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

        country = EuropeCountry.objects.get(pk=17)
        a = 1
        while a < 10:
            point_on_surface = country.geom.point_on_surface
            r = Report(
                version_UUID=str(a+1000),
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

    def create_stlouis_team(self):
        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.create(name='expert')
        experts.save()

        stlouis = EuropeCountry.objects.get(pk=53)

        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()

        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_sl'
        u2.userstat.native_of = stlouis
        u2.save()

        u3 = User.objects.create(pk=3)
        u3.username = 'expert_3_sl'
        u3.userstat.native_of = stlouis
        u3.save()

        u4 = User.objects.create(pk=4)
        u4.username = 'expert_4_sl'
        u4.userstat.native_of = stlouis
        u4.save()

        u5 = User.objects.create(pk=5)
        u5.username = 'expert_1_eu'
        u5.save()

        spain_group.user_set.add(u1)
        europe_group.user_set.add(u5)

    def create_stlouis_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        a = 1
        country = EuropeCountry.objects.get(pk=53)
        while a < 20:
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

    def print_assigned_reports(self, this_user):
        assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user)
        print("User {0} has been assigned".format( this_user.username ))
        for assignation in assigned_reports:
            is_supervised = User.objects.filter(userstat__national_supervisor_of=assignation.report.country).exists()
            print( "Report {0} in country {1}, assignation number {2}, country is supervised {3}".format( assignation.report.version_UUID, assignation.report.country, assignation.id, is_supervised ) )



    def test_check_users(self):
        self.create_team()
        #check everyone but the granter user
        for this_user in User.objects.exclude(id=24):
            if this_user.userstat.is_superexpert():
                self.assertEqual(this_user.id, 25, "Super user id should be 25")
            else:
                if this_user.userstat.is_bb_user():
                    self.assertEqual(this_user.userstat.native_of.is_bounding_box, True, "BB user native of should be bounding box")
                else:
                    if this_user.userstat.is_national_supervisor():
                        self.assertIsNotNone(this_user.userstat.national_supervisor_of_id, "National supervisor supervised country should not be null")
                        self.assertTrue( this_user.groups.filter(name="eu_group_europe").exists(), "All national supervisors must belong to eu_group_europe"  )
                    else:  # is regular user
                        #if no native country, it is spain
                        if this_user.userstat.native_of is None:
                            if this_user.userstat.is_superexpert():
                                pass
                            else:
                                self.assertTrue('es' in this_user.username, "User {0} is not assigned native country and has not es suffix in username".format( this_user.username ))
                        else:
                            #it should belong to eu group
                            self.assertTrue(this_user.groups.filter(name="eu_group_europe").exists(), "All regular european users must belong to eu_group_europe, user {0} does not".format(this_user.username))

    def test_check_all_reports_are_located(self):
        self.create_report_pool()
        for r in Report.objects.all():
            self.assertIsNotNone( r.country, "Report {0} has no assigned country".format( r.version_UUID ) )

    def test_assign_reports(self):
        self.create_team()
        self.create_report_pool()

        for this_user in User.objects.exclude(id=24):
            if this_user.userstat.is_superexpert():
                assign_superexpert_reports(this_user)
            else:
                if this_user.userstat.is_bb_user():
                    assign_bb_reports(this_user)
                else:
                    if this_user.userstat.is_national_supervisor():
                        assign_reports_to_national_supervisor(this_user)
                    else:  # is regular user
                        assign_reports_to_regular_user(this_user)

        #get all national supervisors
        for this_user in User.objects.filter(userstat__national_supervisor_of__isnull=False):
            # Get all reports in supervised country
            supervised_country = this_user.userstat.national_supervisor_of
            reports_in_supervised_country = Report.objects.filter(country=supervised_country).count()
            #there's less than 5 reports in supervised country
            assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__country=supervised_country).count()
            if reports_in_supervised_country <= 5:
                #all of them should be assigned to this user
                self.assertEqual( reports_in_supervised_country, assigned_reports, "Less than 5 ({0}) reports available belong to country {1}, all of them should be assigned, but only {2} are".format(reports_in_supervised_country, supervised_country, assigned_reports ) )
            else:
                #there's more than five, all five assigned reports should be in the country
                self.assertEqual( 5, assigned_reports, "More than 5 reports available ({0}) for country {1}, all should be assigned to national supervisor".format( assigned_reports, supervised_country ) )

        # get all bounding box users
        for this_user in User.objects.filter(userstat__native_of__is_bounding_box=True):
            #Get all reports in bounding box
            bb = this_user.userstat.native_of
            reports_in_bounding_box = Report.objects.filter(country=bb).count()
            # there's less than 5 reports in supervised country
            assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__country=bb).count()
            if reports_in_bounding_box <= 5:
                # all of them should be assigned to this user
                self.assertEqual(reports_in_bounding_box, assigned_reports, "Less than 5 ({0}) reports available belong to country {1}, all of them should be assigned, but only {2} are".format(reports_in_bounding_box, bb, assigned_reports))
            else:
                # there's more than five, all five assigned reports should be in the country
                self.assertEqual(5, assigned_reports, "More than 5 reports available ({0}) for country {1}, all should be assigned to national supervisor".format(assigned_reports, bb))

        # get all superexperts
        for this_user in User.objects.filter(groups__name='superexpert'):
            assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user).count()
            #no reports should have been assigned
            self.assertEqual(assigned_reports, 0,"No reports should have been assigned to superexpert {0}".format(this_user.username))

        # get all regular users
        regular_users = User.objects.filter( Q(userstat__native_of__is_bounding_box=False) & Q(userstat__national_supervisor_of__isnull=True) )
        for this_user in regular_users:
            assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user).count()
            supervised_countries_gids = User.objects.filter(userstat__national_supervisor_of__isnull=False).values('userstat__national_supervisor_of__gid')
            supervised_countries = EuropeCountry.objects.filter(gid__in=supervised_countries_gids)
            # everyone should have less than 5 reports assigned
            self.assertTrue( assigned_reports <= 5, "User {0} has been assigned more than 5 reports ({1})".format( this_user.username, assigned_reports ) )
            # no regular user should yet receive reports from supervised countries
            supervised_country_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__country__in=supervised_countries).count()
            try:
                self.assertTrue(supervised_country_reports == 0,"User {0} has been assigned some reports ({1}) from supervised countries".format(this_user.username,supervised_country_reports))
            except AssertionError:
                self.print_assigned_reports(this_user)
                raise
            # ... or from bounding boxes
            bb_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__country__is_bounding_box=True).count()
            self.assertTrue(bb_reports == 0, "User {0} has been assigned some reports ({1}) from bounding boxes".format(this_user.username, bb_reports))

        # let's take a closer look at es experts
        spain_users = User.objects.filter( Q(userstat__native_of__isnull=True) | Q( userstat__native_of__gid=17 ) ).exclude( groups__name='eu_group_europe' ).exclude( id__in=[24,25] )
        for this_user in spain_users:
            # All spain user assigned reports should be in Spain
            assigned_reports_not_spain = ExpertReportAnnotation.objects.filter(user=this_user).exclude( report__country__gid = 17).count()
            self.assertTrue(assigned_reports_not_spain == 0, "Spain user {0} has been assigned some reports ({1}) outside spain".format(this_user.username, assigned_reports_not_spain))

        # for symmetry sake, the same for eu experts
        euro_users = User.objects.filter( groups__name='eu_group_europe' ).exclude(id__in=[24, 25]).filter( userstat__national_supervisor_of__isnull = True )
        for this_user in euro_users:
            # All reports should be euro
            assigned_reports_spain = ExpertReportAnnotation.objects.filter(user=this_user).filter( report__country__gid = 17).count()
            self.assertTrue(assigned_reports_spain == 0, "Euro user {0} has been assigned some reports ({1}) from spain".format(this_user.username, assigned_reports_not_spain))

        #check grabbed reports
        for this_user in User.objects.all():
            grabbed_reports = this_user.userstat.grabbed_reports
            assigned_reports = ExpertReportAnnotation.objects.filter(user=this_user).count()
            self.assertEquals(grabbed_reports, assigned_reports, "User {0} has been assigned {1} reports, grabbed reports in stats is {2}".format( this_user.username, assigned_reports, grabbed_reports ))

        #all reports assigned to national supervisors should be non_simplified
        for this_user in User.objects.filter(userstat__national_supervisor_of__isnull=False):
            # Get all reports in supervised country
            supervised_country = this_user.userstat.national_supervisor_of
            for assigned_report in ExpertReportAnnotation.objects.filter(user=this_user):
                if assigned_report.report.country == supervised_country:
                    self.assertTrue( assigned_report.simplified_annotation==False, "User {0}, national supervisor of {1}, has been assigned report {2} as simplified".format( this_user.username, supervised_country, assigned_report.report ))


    def test_simplified_assignation(self):
        self.create_micro_team()

        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        c = EuropeCountry.objects.get(pk=23) #France
        report = create_report(0, "1", t, c)

        # queryset update - trick to override the auto_now_add in server upload time. If this is not done, it defaults to current timestamp

        for this_user in User.objects.exclude(id=24):
            if this_user.userstat.is_superexpert():
                assign_superexpert_reports(this_user)
            else:
                if this_user.userstat.is_bb_user():
                    assign_bb_reports(this_user)
                else:
                    if this_user.userstat.is_national_supervisor():
                        assign_reports_to_national_supervisor(this_user)
                    else:  # is regular user
                        assign_reports_to_regular_user(this_user)
        # There should be three assignations
        n = ExpertReportAnnotation.objects.all().count()
        self.assertTrue( n == 3, "There should be {0} annotations, {1} found".format( 3, n ) )
        # Two first assignations should be short, third full
        annos = ExpertReportAnnotation.objects.all().order_by('id')
        anno_1 = annos[0]
        anno_2 = annos[1]
        anno_3 = annos[2]
        self.assertTrue( anno_1.simplified_annotation, "Annotation with id {0} should be simplified, it is NOT".format( anno_1.id ) )
        self.assertTrue( anno_2.simplified_annotation, "Annotation with id {0} should be simplified, it is NOT".format( anno_2.id ) )
        self.assertFalse( anno_3.simplified_annotation, "Annotation with id {0} should NOT be simplified, it is".format( anno_3.id ) )



    # tests that reports that should go to national supervisor don't because of expired precedence period
    def test_report_outdate(self):
        self.create_team()
        # all reports are in isle of man, 2 of them were uploaded to the server 2 weeks + 1 day ago
        self.create_outdated_report_pool()
        # assign reports to regular user. All assigned reports should be from isle of man
        user = User.objects.get(pk=10)
        assign_reports_to_regular_user(user)
        # user should have been assigned 2 outdated reports
        assigned_reports = ExpertReportAnnotation.objects.filter(user=user)
        self.assertTrue( assigned_reports.count() == 2, "User {0} has been assigned {1} reports, should have been assigned {2}".format( user.username, assigned_reports.count(), 5 ) )

        national_supervisor_isleofman = User.objects.get(pk=3)
        assign_reports_to_national_supervisor(national_supervisor_isleofman)
        server_upload_time_first_report = ExpertReportAnnotation.objects.filter(user=national_supervisor_isleofman).order_by('id')[0].report.server_upload_time
        server_upload_time_first_report_str = server_upload_time_first_report.strftime('%Y-%m-%d')
        self.assertTrue( server_upload_time_first_report_str == timezone.now().strftime('%Y-%m-%d'), "Server upload time of first assigned report should be {0}, is {1}".format( timezone.now().strftime('%Y-%m-%d'), server_upload_time_first_report_str ) )


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

    def test_assign_stlouis_reports(self):
        # 1 regular euro user, 1 regular spain user, 3 bbox (stlouis) users
        self.create_stlouis_team()
        self.create_stlouis_report_pool()

        number_of_assignments_to_regular_user = 0
        number_of_assignments_to_bb_stlouis = 0

        for this_user in User.objects.exclude(id__in=[24,25]):
            if this_user.userstat.is_superexpert():
                assign_superexpert_reports(this_user)
            else:
                if this_user.userstat.is_bb_user():
                    assign_bb_reports(this_user)
                    number_of_assignments_to_bb_stlouis += 1
                else:
                    if this_user.userstat.is_national_supervisor():
                        assign_reports_to_national_supervisor(this_user)
                    else:  # is regular user
                        assign_reports_to_regular_user(this_user)
                        number_of_assignments_to_regular_user += 1

        self.assertEqual( number_of_assignments_to_regular_user, 2, "Assigned reports to regular users {0} times, should be 2".format( number_of_assignments_to_regular_user ) )
        self.assertEqual( number_of_assignments_to_bb_stlouis, 3, "Assigned reports to bb stlouis users {0} times, should be 3".format( number_of_assignments_to_bb_stlouis ) )

        #all stlouis experts id=2,3,4 should be assigned 5 reports
        for i in [2, 3, 4]:
            u = User.objects.get(pk=i)
            reports_user_i = ExpertReportAnnotation.objects.filter(user=u).count()
            self.assertEqual(reports_user_i, 5, msg="St Louis user {0} has not been assigned 5 reports, but {1}!".format(u.username, reports_user_i))

        #no reports for you, non st Louis users (ids 1 and 5)!
        for i in [1, 5]:
            u = User.objects.get(pk=i)
            reports_user_i = ExpertReportAnnotation.objects.filter(user=u).count()
            self.assertEqual(reports_user_i, 0, msg="NON-St Louis user {0} has been assigned {1} reports, but should have received none!".format(u.username, reports_user_i))



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


    def test_outdated_assign(self):
        self.create_team()
        #create outdated report
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        country = EuropeCountry.objects.get(pk=22)  # Faroes
        # date threshold for reports that the national supervisor has lost priority over
        two_weeks_ago = non_naive_time - timedelta(days=country.national_supervisor_report_expires_in)
        r = Report(
            version_UUID="1",
            version_number=0,
            user_id='00000000-0000-0000-0000-000000000000',
            phone_upload_time=non_naive_time,
            server_upload_time=non_naive_time,
            creation_time=non_naive_time,
            version_time=non_naive_time,
            location_choice="current",
            current_location_lon=country.geom.point_on_surface.x,
            current_location_lat=country.geom.point_on_surface.y,
            type='adult',
        )
        r.save()
        p = Photo.objects.create(report=r, photo='/home/webuser/webapps/tigaserver/media/tigapics/splash.png')
        p.save()
        # queryset update - trick to override the auto_now_add in server upload time. If this is not done, it defaults to current timestamp
        Report.objects.all().update(server_upload_time=two_weeks_ago)

        #Manually assign report to NS. Has been assigned report but report outdated remained long time in assigned not resolved queue...
        ns_user = User.objects.get(username='expert_5_eu')
        new_annotation = ExpertReportAnnotation(report=r, user=ns_user)
        new_annotation.save()

        #Now assign reports to Faroes native. Should receive report with uuid 1
        faroes_native_regular_user = User.objects.get(username='expert_9_eu')
        assign_reports_to_regular_user(faroes_native_regular_user)

        #should have been assigned the Faroes report, since the report is outdated and therefore no longer blocked by NS
        n_assigned_to_faroes_user = ExpertReportAnnotation.objects.filter(user=faroes_native_regular_user).filter(report=r).count()
        self.assertTrue( n_assigned_to_faroes_user == 1, "Number of reports assigned to Faroes user {0} is {1}, should be 1".format( faroes_native_regular_user.username, n_assigned_to_faroes_user ) )



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
                nc = NotificationContent.objects.order_by('-id').first()
                # native title should be in the same language as the report
                self.assertEqual( get_translation_in("your_picture_has_been_validated_by_an_expert", locale), nc.title_native )
                # we do this to avoid triggering the unique(user_id,report_id) constraint
                anno_reritja.delete()