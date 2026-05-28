from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon
from django.core.management.base import BaseCommand

from mosquito_alert.campaigns.models import OWCampaigns
from mosquito_alert.geo.models import Country, Continent
from mosquito_alert.reports.models import Report
from mosquito_alert.users.models import UserStat
from mosquito_alert.workspaces.models import Workspace, WorkspaceCollaborationGroup


class Command(BaseCommand):
    help = "Fix workspace and countries"

    def handle(self, *args, **options):
        def migrate_fk_countries(from_country, to_country):
            if from_country and to_country:
                OWCampaigns.objects.filter(country=from_country).update(
                    country=to_country
                )
                Report.objects.filter(country=from_country).update(country=to_country)
                UserStat.objects.filter(country=from_country).update(country=to_country)
            if from_country:
                from_country.delete()

        norway = Country.objects.filter(iso3_code="NOR").first()
        svalbard = Country.objects.filter(iso3_code="SJM").first()
        migrate_fk_countries(from_country=svalbard, to_country=norway)

        rapa_nui = Country.objects.filter(iso3_code="RPN").first()
        chile = Country.objects.filter(iso3_code="CHL").first()
        migrate_fk_countries(from_country=rapa_nui, to_country=chile)

        saint_lious_missouri = Country.objects.filter(iso3_code="STL").first()
        usa = Country.objects.filter(iso3_code="USA").first()
        migrate_fk_countries(from_country=saint_lious_missouri, to_country=usa)

        # Populate incorrect country workspace
        Workspace.objects.filter(name="Rapa Nui", country__isnull=True).update(
            country=Country.objects.get(iso3_code="CHL")
        )
        Workspace.objects.filter(
            name="Saint Louis, Missouri", country__isnull=True
        ).update(country=Country.objects.get(iso3_code="USA"))

        # Fix Rapa Nui Workspace.geom
        rapa_nui_workspace = Workspace.objects.get(name="Rapa Nui")
        chile = Country.objects.get(iso3_code="CHL")
        rapa_nui_workspace.geom = MultiPolygon(
            chile.geom.intersection(rapa_nui_workspace.geom.buffer(0.01))
        )

        # Ensure Workspace with country=None exists
        Workspace.objects.get_or_create(country=None, geom=None)

        # Populate Europe Collaboration Group
        collaboration_group, _ = WorkspaceCollaborationGroup.objects.get_or_create(
            name="European Collaboration Group"
        )
        if superexpert := User.objects.filter(pk=25).first():
            collaboration_group.reviewers.add(superexpert)

        collaborating_workspaces = Workspace.objects.filter(
            country__subregion__continent=Continent.EUROPE
        )
        collaboration_group.workspaces.set(collaborating_workspaces)
