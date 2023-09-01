import pytest

from mosquito_alert.geo.models import BoundaryLayer
from mosquito_alert.geo.tests.factories import BoundaryLayerFactory
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory, get_or_create_root_taxon
from mosquito_alert.users.models import User
from mosquito_alert.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def taxon_root(db):
    return get_or_create_root_taxon()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Create root on django_db_setup
        get_or_create_root_taxon()


@pytest.fixture
def taxon_specie(db, taxon_root):
    return TaxonFactory(rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)


@pytest.fixture()
def country_bl(db):
    return BoundaryLayerFactory(boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE, level=0, boundary=None)
