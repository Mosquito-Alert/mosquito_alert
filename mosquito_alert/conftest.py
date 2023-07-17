import pytest

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory
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
    return TaxonFactory(name="life", rank=Taxon.TaxonomicRank.DOMAIN)


@pytest.fixture
def taxon_specie(db, taxon_root):
    return TaxonFactory(rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)
