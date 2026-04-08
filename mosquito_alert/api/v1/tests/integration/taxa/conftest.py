import pytest

from mosquito_alert.taxa.models import Taxon


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Taxon


@pytest.fixture
def taxon_children(taxon_root):
    return taxon_root.add_child(
        rank=Taxon.TaxonomicRank.ORDER, name="Children", common_name=""
    )


@pytest.fixture
def taxon_italian_localized(taxon_root):
    taxon = taxon_root.add_child(
        rank=Taxon.TaxonomicRank.ORDER,
        name="Children",
        common_name="English common name",
    )
    taxon.common_name_it = "Italian common name"
    taxon.save()
    return taxon
