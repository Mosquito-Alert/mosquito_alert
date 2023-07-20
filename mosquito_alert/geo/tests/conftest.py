import pytest

from .factories import BoundaryFactory


@pytest.fixture()
def boundary_without_geometry(country_bl):
    return BoundaryFactory(boundary_layer=country_bl, geometry_model=None)
