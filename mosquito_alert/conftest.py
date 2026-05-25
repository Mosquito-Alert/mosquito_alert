import pytest

from django.contrib.gis.geos import GEOSGeometry

from mosquito_alert.taxa.models import Taxon


@pytest.fixture
def taxon_root(db):
    return Taxon.add_root(
        rank=Taxon.TaxonomicRank.CLASS, name="Insecta", common_name=""
    )


@pytest.fixture(autouse=True)
def disable_report_location_masking(settings, request):
    # Skip this fixture for tests marked with @pytest.mark.enable_report_location_masking
    if request.node.get_closest_marker("enable_report_location_masking"):
        return

    settings.OCEAN_GEOM = GEOSGeometry("POLYGON EMPTY", srid=4326)
    settings.MIN_ALLOWED_LATITUDE = -90
    settings.MAX_ALLOWED_LATITUDE = 90
