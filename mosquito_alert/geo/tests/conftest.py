import pytest

from ..models import BoundaryLayer
from .factories import BoundaryFactory, BoundaryLayerFactory


@pytest.fixture()
def country_bl(db):
    return BoundaryLayerFactory(
        boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE, level=0, boundary=None
    )


@pytest.fixture()
def boundary_without_geometry(country_bl):
    return BoundaryFactory(boundary_layer=country_bl, geometry_model=None)
