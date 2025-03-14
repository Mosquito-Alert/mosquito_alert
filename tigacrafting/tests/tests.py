# Create your tests here.
from abc import ABC, abstractmethod
import pytest
from unittest.mock import PropertyMock, patch

from django.test import TestCase
from django.utils.translation import activate, deactivate, gettext as _
from tigaserver_app.models import NutsEurope, EuropeCountry, TigaUser, Report, ExpertReportAnnotation, Photo, NotificationContent, Notification
from tigacrafting.models import UserStat, ExpertReportAnnotation, Categories, Complex, OtherSpecies, Taxon
from tigacrafting.views import must_be_autoflagged
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ValidationError
from operator import attrgetter
from tigacrafting.messaging import send_finished_validation_notification
import tigaserver_project.settings as conf
from django.utils import timezone
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
    p = Photo.objects.create(report=r, photo='./testdata/splash.png')
    p.save()
    return r


class NewReportAssignment(TestCase):
    fixtures = ['auth_group.json','europe_countries_new.json', 'reritja_like.json', 'granter_user.json', 'awardcategory.json', 'nutseurope.json']

    # just regular european users
    def create_regular_team(self):
        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        experts = Group.objects.get(name='expert')
        superexperts = Group.objects.get(name='superexpert')

        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_eu'
        u2.userstat.native_of = EuropeCountry.objects.get(pk=45)  # Isle of man
        u2.save()

        u9 = User.objects.create(pk=9)
        u9.username = 'expert_9_eu'
        u9.userstat.native_of = EuropeCountry.objects.get(pk=22)  # Faroes
        u9.save()

        u10 = User.objects.create(pk=10)
        u10.username = 'expert_10_eu'
        u10.userstat.native_of = EuropeCountry.objects.get(pk=22)  # Faroes
        u10.save()

        europe_group.user_set.add(u2)
        europe_group.user_set.add(u9)
        europe_group.user_set.add(u10)

        experts.user_set.add(u2)
        experts.user_set.add(u9)
        experts.user_set.add(u10)

        reritja = User.objects.get(pk=25)
        superexperts.user_set.add(reritja)

    def create_austria_team(self):
        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.get(name='expert')
        superexperts = Group.objects.get(name='superexpert')

        # National supervisor
        u1 = User.objects.create(pk=3)
        u1.username = 'expert_3_eu'
        c = EuropeCountry.objects.get(pk=34)  # Austria NS
        u1.userstat.national_supervisor_of = c
        u1.save()

        # Regular eu user 1
        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_eu'
        u2.userstat.native_of = EuropeCountry.objects.get(pk=34)  # Austria regular user 1
        u2.save()

        # Regular eu user 2
        u3 = User.objects.create(pk=5)
        u3.username = 'expert_5_eu'
        u3.userstat.native_of = EuropeCountry.objects.get(pk=34)  # Austria regular user 2
        u3.save()

        europe_group.user_set.add(u1)
        europe_group.user_set.add(u2)
        europe_group.user_set.add(u3)

        experts.user_set.add(u1)
        experts.user_set.add(u2)
        experts.user_set.add(u3)

        reritja = User.objects.get(pk=25)
        superexperts.user_set.add(reritja)

    def create_micro_team(self):

        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.get(name='expert')
        superexperts = Group.objects.get(name='superexpert')

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
        experts = Group.objects.get(name='expert')
        superexperts = Group.objects.get(name='superexpert')

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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1

    def create_small_regionalized_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        extremadura = NutsEurope.objects.get(name_latn='Extremadura')
        spain = EuropeCountry.objects.get(pk=17)
        # Two reports from Extremadura
        a = 1
        while a < 3:
            point_on_surface = extremadura.geom.point_on_surface
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1

        # Two reports from not extremadura
        not_extremadura = NutsEurope.objects.filter(europecountry=spain).exclude(name_latn='Extremadura')
        a = 1
        while a < 3:
            point_on_surface = not_extremadura[a].geom.point_on_surface
            r = Report(
                version_UUID=str(a + 10),
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1

        # Two reports from Europe
        a = 1
        while a < 3:
            not_spain = EuropeCountry.objects.exclude(gid=17)[a]
            point_on_surface = not_spain.geom.point_on_surface
            r = Report(
                version_UUID=str(a + 100),
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1

        # Two unlocated reports
        a = 1
        while a < 3:
            r = Report(
                version_UUID=str(a + 1000),
                version_number=0,
                user_id='00000000-0000-0000-0000-000000000000',
                phone_upload_time=non_naive_time,
                server_upload_time=non_naive_time,
                creation_time=non_naive_time,
                version_time=non_naive_time,
                location_choice="current",
                current_location_lon=0,
                current_location_lat=0,
                type='adult',
            )
            r.save()
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1


    def create_regionalized_report_pool(self):
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        non_naive_time = timezone.now()
        extremadura = NutsEurope.objects.get(name_latn='Extremadura')
        catalonia = NutsEurope.objects.get(name_latn='Cataluña')
        andalucia = NutsEurope.objects.get(name_latn='Andalucía')
        a = 1
        while a < 6:
            point_on_surface = extremadura.geom.point_on_surface
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1
        a = 1
        while a < 6:
            point_on_surface = catalonia.geom.point_on_surface
            r = Report(
                version_UUID=str(a + 10),
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1
        a = 1
        while a < 6:
            point_on_surface = andalucia.geom.point_on_surface
            r = Report(
                version_UUID=str(a + 100),
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
            p.save()
            a = a + 1

    def create_small_region_team(self):
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.get(name='expert')

        extremadura = NutsEurope.objects.get(name_latn='Extremadura')

        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()
        u1.userstat.nuts2_assignation = extremadura
        u1.userstat.save()

        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_es'
        u2.save()
        u2.userstat.nuts2_assignation = None
        u2.userstat.save()

        spain_group.user_set.add(u1)
        spain_group.user_set.add(u2)

        experts.user_set.add(u1)
        experts.user_set.add(u2)

    def create_region_team(self):
        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()

        experts = Group.objects.get(name='expert')

        catalonia = NutsEurope.objects.get(name_latn='Cataluña')
        andalucia = NutsEurope.objects.get(name_latn='Andalucía')
        greece = EuropeCountry.objects.get(pk=16)

        u1 = User.objects.create(pk=1)
        u1.username = 'expert_1_es'
        u1.save()
        u1.userstat.nuts2_assignation = catalonia
        u1.userstat.save()

        u2 = User.objects.create(pk=2)
        u2.username = 'expert_2_es'
        u2.save()
        u2.userstat.nuts2_assignation = andalucia
        u2.userstat.save()

        u3 = User.objects.create(pk=3)
        u3.username = 'expert_1_eu'
        u3.userstat.native_of = greece
        u3.save()

        spain_group.user_set.add(u1)
        spain_group.user_set.add(u2)
        europe_group.user_set.add(u3)

        experts.user_set.add(u1)
        experts.user_set.add(u2)
        experts.user_set.add(u3)


    def create_stlouis_team(self):
        europe_group = Group.objects.create(name='eu_group_europe')
        europe_group.save()
        spain_group = Group.objects.create(name='eu_group_spain')
        spain_group.save()
        experts = Group.objects.get(name='expert')

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
            p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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

    def test_last_assignment(self):
        self.create_regular_team()
        self.create_report_pool()
        # they are all regular users but ...
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
        for r in Report.objects.all():
            annos = ExpertReportAnnotation.objects.filter(report=r)
            if annos.count() == 3:
                long_report_count = annos.filter(simplified_annotation=False).count()
                short_report_count = annos.filter(simplified_annotation=True).count()
                long_annotation_id = annos.filter(simplified_annotation=False).first().id
                short_annotation_ids = [ a.id for a in annos.filter(simplified_annotation=True) ]
                self.assertTrue( long_report_count == 1, "Report {0} has {0} LONG assignations, should be 1".format( r.version_UUID, str(long_report_count) )  )
                self.assertTrue(short_report_count == 2, "Report {0} has {0} SHORT assignations, should be 2".format(r.version_UUID, str(short_report_count)))
                # since long annotation is last to be assigned, id should be the highest
                ids = []
                for i in short_annotation_ids:
                    ids.append(i)
                ids.append(long_annotation_id)
                latest_id = max(ids)
                self.assertTrue(latest_id == long_annotation_id, "For report {0} long annotation id is not the highest (highest is {1}, actual id is {2}".format(r.version_UUID, str(latest_id), str(long_annotation_id)))

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
        # THIS TEST DOES NOT APPLY ANYMORE - eu experts can be assigned reports from SPAIN        
        # euro_users = User.objects.filter( groups__name='eu_group_europe' ).exclude(id__in=[24, 25]).filter( userstat__national_supervisor_of__isnull = True )
        # for this_user in euro_users:
        #     # All reports should be euro
        #     assigned_reports_spain = ExpertReportAnnotation.objects.filter(user=this_user).filter( report__country__gid = 17).count()
        #     self.assertTrue(assigned_reports_spain == 0, "Euro user {0} has been assigned some reports ({1}) from spain".format(this_user.username, assigned_reports_spain))        

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


    def test_simplified_assignation_two_experts_and_ns_report_from_not_supervised_country(self):
        self.create_micro_team()
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        c = EuropeCountry.objects.get(pk=23) #France
        report = create_report(0, "1", t, c)
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

    def test_simplified_assignation_two_experts_and_ns_report_from_supervised_country(self):
        #self.create_micro_team()
        # team exclusively composed by austrian experts (2 regular, 1 ns)
        self.create_austria_team()
        t = TigaUser.objects.create(user_UUID='00000000-0000-0000-0000-000000000000')
        t.save()
        c = EuropeCountry.objects.get(pk=34)  # Austria
        # we create an austrian report, with current time. That means it's locked by ns
        report = create_report(0, "1", t, c)
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
        # There should be ONE assignation
        n = ExpertReportAnnotation.objects.all().count()
        self.assertTrue(n == 1, "There should be {0} annotations, {1} found".format(1, n))
        # NS Validates
        ns_validation = ExpertReportAnnotation.objects.get(user_id=3)
        ns_validation.validation_complete = True
        ns_validation.save()
        # Now report it's validated AND NO LONGER LOCKED, reassign
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
        n = ExpertReportAnnotation.objects.all().count()
        # it should now be assigned to 3 experts (ns, and two regulars)
        self.assertTrue(n == 3, "There should be {0} annotations, {1} found".format(1, n))
        annos = ExpertReportAnnotation.objects.all().order_by('id')
        anno_1 = annos[0]
        anno_2 = annos[1]
        anno_3 = annos[2]
        # First assignation is to NS, should be complete
        self.assertFalse(anno_1.simplified_annotation,"Annotation with id {0} (NS) should NOT be simplified, it is".format(anno_1.id))
        self.assertTrue(anno_2.simplified_annotation,"Annotation with id {0} should be simplified, it is NOT".format(anno_2.id))
        self.assertTrue(anno_3.simplified_annotation,"Annotation with id {0} should be simplified, it is NOT".format(anno_3.id))


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
        p = Photo.objects.create(report=r, photo='./testdata/splash.png')
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
        superexperts_group = Group.objects.get(name='superexpert')
        superexperts_group.user_set.add(reritja_user)
        reritja_user.save()

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

        for l in conf.LANGUAGES:
            locale = l[0]
            if locale != 'zh-cn':
                r.app_language = locale
                r.save()
                anno_reritja = ExpertReportAnnotation.objects.create(user=reritja_user, report=r, category=c_3,
                                                                     validation_complete=True, revise=True,
                                                                     validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY)
                anno_reritja.save()
                send_finished_validation_notification(anno_reritja)
                nc = NotificationContent.objects.order_by('-id').first()
                # native title should be in the same language as the report
                activate(locale)

                self.assertEqual(_("your_picture_has_been_validated_by_an_expert"), nc.title_native )
                deactivate()
                # we do this to avoid triggering the unique(user_id,report_id) constraint
                anno_reritja.delete()


    def test_spanish_regionalization(self):
        self.create_regionalized_report_pool()
        self.create_region_team()

        # Check that report pool is correct
        for r in Report.objects.all():
            self.assertTrue(r.country is not None, "Country should not be null, it is")
            self.assertTrue(r.nuts_3 is not None, "Nuts 3 level should not be null it is")
            self.assertTrue(r.nuts_2 is not None, "Nuts 2 level should not be null it is")

        # There should be only reports for Catalonia and Andalucia
        catalonia = NutsEurope.objects.get(name_latn='Cataluña')
        andalucia = NutsEurope.objects.get(name_latn='Andalucía')
        extremadura = NutsEurope.objects.get(name_latn='Extremadura')
        reports_catalonia_exists = Report.objects.filter(nuts_2=catalonia.nuts_id).exists()
        reports_andalucia_exists = Report.objects.filter(nuts_2=andalucia.nuts_id).exists()
        reports_extremadura_exists = Report.objects.filter(nuts_2=extremadura.nuts_id).exists()

        self.assertTrue(reports_catalonia_exists, "There should be some reports in Catalonia, but there are 0")
        self.assertTrue(reports_andalucia_exists, "There should be some reports in Andalucia, but there are 0")
        self.assertTrue(reports_extremadura_exists, "There should be some reports in Andalucia, but there are 0")

        # Check that expert group is correct
        users = User.objects.filter(groups__name='expert').order_by('-id')
        self.assertTrue(users.count() == 3, "There should be 3 experts, there are {0}".format(users.count()))

        self.assertTrue(users[0].id == 3, "First expert to be assigned should be eu, is not")

        for this_user in users:
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

        # All reports assigned to catalan expert should be from Catalonia
        catalan = User.objects.get(pk=1)
        self.assertTrue(catalan.userstat.nuts2_assignation == catalonia, "User {0} should be regionalized to Catalonia, is not".format(catalan.id))
        catalan_assignments = ExpertReportAnnotation.objects.filter(user=catalan)
        self.assertTrue(catalan_assignments.count() == 5, "User {0} should be assigned 5 reports, has {1}".format(catalan.id, catalan_assignments.count()))
        for anno in catalan_assignments:
            self.assertTrue( anno.report.nuts_2 == 'ES51', "Report {0} should be located in Catalonia, but is assigned to nuts2 {1}".format( anno.report.version_UUID, anno.report.nuts_2 ) )

        # All reports assigned to andalusian expert should be from Andalucía
        andalusian = User.objects.get(pk=2)
        self.assertTrue(andalusian.userstat.nuts2_assignation == andalucia, "User {0} should be regionalized to Andalucía, is not".format(andalusian.id))
        andalusian_assignments = ExpertReportAnnotation.objects.filter(user=andalusian)
        self.assertTrue(andalusian_assignments.count() == 5, "User {0} should be assigned 5 reports, has {1}".format(andalusian.id, andalusian_assignments.count()))
        for anno in andalusian_assignments:
            self.assertTrue(anno.report.nuts_2 == 'ES61', "Report {0} should be located in Andalucía, but is assigned to nuts2 {1}".format(anno.report.version_UUID, anno.report.nuts_2))

        '''
        european_expert = User.objects.get(pk=3)
        self.assertTrue(european_expert.userstat.nuts2_assignation is None, "User {0} should not be regionalized, it is")
        european_assignments = ExpertReportAnnotation.objects.filter(user=european_expert)
        self.assertTrue(european_assignments.count() == 5, "User {0} should be assigned 5 reports, has {1}".format(european_expert.id, european_assignments.count()))
        for anno in european_assignments:
            self.assertFalse(anno.report.nuts_2 == 'ES51', "Report {0} should not be located in Catalunya, it is")
            self.assertFalse(anno.report.nuts_2 == 'ES61', "Report {0} should not be located in Andalucía, it is")
        '''


    def test_regionalization_priority_queues(self):
        self.create_small_regionalized_report_pool()
        self.create_small_region_team()

        #check report pool
        # 2 extremadura, 2 not extremadura, 2 european and 2 unassigned
        self.assertTrue( Report.objects.all().count() == 8, "N of reports should be 8, is {0}".format( Report.objects.all().count() ) )
        self.assertTrue( Report.objects.filter(nuts_2='ES43').count() == 2, "N of reports in extremadura should be 2, is {0}".format( Report.objects.filter(nuts_2='ES43').count() ) )
        self.assertTrue( Report.objects.filter(country__gid=17).exclude(nuts_2='ES43').count() == 2, "N of reports spain but not extremadura should be 2, is {0}".format( Report.objects.filter(country__gid=17).exclude(nuts_2='ES43').count() ))
        self.assertTrue(Report.objects.exclude(country__gid=17).exclude(country__isnull=True).count() == 2, "N of reports europe should be 2, is {0}".format(Report.objects.exclude(country__gid=17).exclude(country__isnull=True).count()))
        self.assertTrue(Report.objects.filter(country__isnull=True).count() == 2, "N of non-located reports be 2, is {0}".format( Report.objects.filter(country__isnull=True).count() ))

        users = User.objects.filter(groups__name='expert').order_by('-id')
        self.assertTrue(users.count() == 2, "There should be 2 experts, there are {0}".format(users.count()))

        for this_user in users:
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

        extremadura = NutsEurope.objects.get(name_latn='Extremadura')
        extremaduran = User.objects.get(pk=1)
        self.assertTrue(extremaduran.userstat.nuts2_assignation == extremadura, "User {0} should be regionalized to Extremadura, is not".format(extremaduran.id))
        extremaduran_assignments = ExpertReportAnnotation.objects.filter(user=extremaduran)
        self.assertTrue(extremaduran_assignments.count() == 5, "User {0} should be assigned 5 reports, has {1}".format(extremaduran.id, extremaduran_assignments.count()))

        # Assign reports to expert 1 - they should get 2 extremadura, 2 spain and 1 european
        self.assertTrue( extremaduran_assignments.filter(report__nuts_2='ES43').count() == 2, "Expert should be assigned 2 extremadura reports, has been assigned {0}".format( extremaduran_assignments.filter(report__nuts_2='ES43').count() ) )
        self.assertTrue( extremaduran_assignments.filter(report__country__gid=17).exclude(report__nuts_2='ES43').count() == 2, "Expert should be assigned 2 spanish not extremadura reports, has been assigned {0}".format( extremaduran_assignments.filter(report__country__gid=17).exclude(report__nuts_2='ES43').count() ))
        self.assertTrue( extremaduran_assignments.exclude(report__country__gid=17).exclude(report__country__isnull=True).count() == 1, "Expert should be assigned 1 european report, has been assigned {0}".format( extremaduran_assignments.exclude(report__country__gid=17).exclude(report__country__isnull=True).count() ))

        generic_spain = User.objects.get(pk=2)
        self.assertTrue(generic_spain.userstat.nuts2_assignation == None, "User {0} should not be regionalized it is ({1}) ".format(extremaduran.id, generic_spain.userstat.nuts2_assignation))
        generic_assignments = ExpertReportAnnotation.objects.filter(user=generic_spain)
        self.assertTrue(generic_assignments.count() == 5, "User {0} should be assigned 5 reports, has {1}".format(generic_spain.id, generic_assignments.count()))
        self.assertTrue(generic_assignments.filter(report__country__gid=17).count() == 4, "Expert should be assigned 4 spanish reports, has been assigned {0}".format( generic_assignments.filter(report__country__gid=17).count() ))
        n_european = generic_assignments.exclude(report__country__gid=17).exclude(report__country__isnull=True).count()
        self.assertTrue(n_european == 1,"Expert should be 1 european report, has been assigned {0}".format(n_european))
        # print( generic_assignments.exclude(report__country__gid=17).exclude(report__country__isnull=True).first().report.country.name_engl )

@pytest.mark.django_db
class BaseTestTaxonRelationModel(ABC):
    model = None  # This must be defined in subclasses

    @classmethod
    @abstractmethod
    def create_obj(cls):
        raise NotImplementedError

    # fields
    def test_taxa_should_return_None_if_no_taxon_linked(self):
        obj = self.create_obj()
        assert obj.taxa.first() is None

    def test_taxa_should_return_taxon_if_linked(self, taxon_root):
        obj = self.create_obj()
        obj.taxa.set([taxon_root,])

        assert obj.taxa.first() == taxon_root
        assert taxon_root.content_object == obj


class TestCategoriesModel(BaseTestTaxonRelationModel):
    model = Categories

    @classmethod
    def create_obj(self):
        return Categories.objects.create(
            name='test'
        )

class TestComplexModel(BaseTestTaxonRelationModel):
    model = Complex

    @classmethod
    def create_obj(self):
        return Complex.objects.create(
            description='test'
        )

class TestOtherSpeciesModel(BaseTestTaxonRelationModel):
    model = OtherSpecies

    @classmethod
    def create_obj(self):
        return OtherSpecies.objects.create(
            name='test'
        )

@pytest.mark.django_db
class TestTaxonModel:

    # classmethods
    def test_get_root_return_root_node(self, taxon_root):
        assert Taxon.get_root() == taxon_root

    def test_get_root_return_None_if_root_node_does_not_exist(self):
        Taxon.objects.all().delete()

        assert Taxon.get_root() is None

    # fields
    def test_rank_can_not_be_null(self):
        assert not Taxon._meta.get_field("rank").null

    def test_rank_can_not_be_blank(self):
        assert not Taxon._meta.get_field("rank").blank

    def test_name_can_not_be_null(self):
        assert not Taxon._meta.get_field("name").null

    def test_name_can_not_be_blank(self):
        assert not Taxon._meta.get_field("name").blank

    def test_name_max_length_is_32(self):
        assert Taxon._meta.get_field("name").max_length == 32

    def test_common_name_can_be_null(self):
        assert Taxon._meta.get_field("common_name").null

    def test_common_name_can_not_be_blank(self):
        assert Taxon._meta.get_field("common_name").blank

    def test_common_name_max_length_is_64(self):
        assert Taxon._meta.get_field("common_name").max_length == 64

    # properties
    def test_node_order_by_name(self):
        assert Taxon.node_order_by == ["name"]

    def test_is_specie_must_be_true_for_taxon_with_rank_species_complex_or_higher(self):
        obj = Taxon(
            rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )

        assert obj.is_specie

        obj.rank = Taxon.TaxonomicRank.SPECIES_COMPLEX.value - 1

        assert not obj.is_specie

    # methods
    @pytest.mark.parametrize(
        "name, expected_result, is_specie",
        [
            ("dumMy StrangE nAme", "Dummy strange name", True),
            ("dumMy StrangE nAme", "dumMy StrangE nAme", False),
        ],
    )
    def test_name_is_capitalized_on_save_only_for_species(self, name, expected_result, is_specie, taxon_root):
        with patch(
            f"{Taxon.__module__}.{Taxon.__name__}.is_specie", new_callable=PropertyMock
        ) as mocked_is_specie:
            mocked_is_specie.return_value = is_specie
            obj = taxon_root.add_child(name=name, rank=taxon_root.rank + 1)

            assert obj.name == expected_result

    def test_tree_is_ordered_by_name_on_parent_change(self, taxon_root):
        z_child = taxon_root.add_child(name="z", rank=Taxon.TaxonomicRank.GENUS)
        b_child = z_child.add_child(name="b", rank=Taxon.TaxonomicRank.SPECIES)
        a_child = taxon_root.add_child(name="a", rank=Taxon.TaxonomicRank.SPECIES)
        # NOTE: Need to refresh since last move changes the object.
        # See: https://django-treebeard.readthedocs.io/en/latest/caveats.html#raw-queries
        z_child.refresh_from_db()

        assert frozenset(Taxon.objects.all()) == frozenset([taxon_root, a_child, z_child, b_child])

        # Change parent
        a_child.move(z_child)

        assert frozenset(Taxon.objects.all()) == frozenset([taxon_root, z_child, a_child, b_child])

    def test_raise_when_rank_higher_than_parent_rank(self, taxon_root):
        taxon_specie = taxon_root.add_child(
            name='specie',
            rank=Taxon.TaxonomicRank.SPECIES
        )
        with pytest.raises(ValidationError):
            taxon_specie.add_child(
                rank=Taxon.TaxonomicRank.CLASS,
                name='class'
            )

    # meta
    def test_unique_name_rank_constraint(self, taxon_root):
        taxon_root.add_child(
            name="Same Name",
            rank=Taxon.TaxonomicRank.SPECIES,
        )

        with pytest.raises(IntegrityError):
            # Create duplicate children name
            taxon_root.add_child(
                name="Same Name",
                rank=Taxon.TaxonomicRank.SPECIES,
            )

    def test_unique_root_constraint(self, taxon_root):
        with pytest.raises(IntegrityError):
            Taxon.add_root(name="", rank=taxon_root.rank)

    def test_unique_content_type_object_id_constraint(self, taxon_root):
        content_type = ContentType.objects.first()
        object_id = 1

        taxon = taxon_root.add_child(
            name="Same Name",
            rank=Taxon.TaxonomicRank.SPECIES,
            content_type=content_type,
            object_id=object_id
        )
        with pytest.raises(IntegrityError):
            taxon_root.add_child(
            name=taxon.name + " test",
            rank=Taxon.TaxonomicRank.SPECIES,
            content_type=content_type,
            object_id=object_id
        )

    def test__str__(self, taxon_root):
        taxon = taxon_root.add_child(
            name="Aedes Albopictus",
            rank=Taxon.TaxonomicRank.SPECIES
        )

        expected_result = "Aedes albopictus [Species]"
        assert taxon.__str__() == expected_result