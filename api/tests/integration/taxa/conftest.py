import pytest

from tigacrafting.models import Taxon

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Taxon

@pytest.fixture
def taxon_children(taxon_root):
    return taxon_root.add_child(
        rank=Taxon.TaxonomicRank.ORDER,
        name="Children",
        common_name=""
    )