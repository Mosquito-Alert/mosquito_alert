from datetime import timedelta
import pytest

from django.utils import timezone

from tigaserver_app.models import OWCampaigns


@pytest.fixture
def active_campaign(country):
    return OWCampaigns.objects.create(
        country=country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(days=10),
        campaign_end_date=timezone.now() + timedelta(days=5),
    )


@pytest.fixture
def inactive_campaign(country):
    return OWCampaigns.objects.create(
        country=country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(days=10),
        campaign_end_date=timezone.now() - timedelta(days=5),
    )


@pytest.fixture
def spanish_campaign(es_country):
    return OWCampaigns.objects.create(
        country=es_country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(hours=1),
        campaign_end_date=timezone.now() + timedelta(hours=1),
    )


@pytest.fixture
def italian_campaign(it_country):
    return OWCampaigns.objects.create(
        country=it_country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(hours=1),
        campaign_end_date=timezone.now() + timedelta(hours=1),
    )


@pytest.fixture
def first_campaign(country):
    return OWCampaigns.objects.create(
        country=country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(days=365),
        campaign_end_date=timezone.now() - timedelta(days=30),
    )


@pytest.fixture
def last_campaign(country):
    return OWCampaigns.objects.create(
        country=country,
        posting_address="Test",
        campaign_start_date=timezone.now() - timedelta(days=7),
        campaign_end_date=timezone.now() + timedelta(days=7),
    )
