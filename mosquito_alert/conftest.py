import pytest

from mosquito_alert.taxa.models import Taxon


@pytest.fixture
def taxon_root(db):
    return Taxon.add_root(
        rank=Taxon.TaxonomicRank.CLASS, name="Insecta", common_name=""
    )
