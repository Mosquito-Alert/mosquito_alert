import os

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains

from ..models import Boundary, BoundaryLayer
from .factories import BoundaryFactory, BoundaryLayerFactory


class TestBoundaryAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "boundary_name, query",
        [
            ("Test", "test"),  # lowercase query
            ("Test", "TEST"),  # uppercase query
            ("In Test middle", "test"),  # icontain query
        ],
    )
    def test_search_by_name(self, admin_client, country_bl, boundary_name, query):
        url = reverse("admin:geo_boundary_changelist")

        expected_obj = BoundaryFactory(name=boundary_name, boundary_layer=country_bl)
        other_obj = BoundaryFactory(name="Other", boundary_layer=country_bl)

        response = admin_client.get(url, data={"q": query})
        assert response.status_code == 200
        assertContains(response=response, text=f'value="{expected_obj.id}"')
        assertNotContains(response=response, text=f'value="{other_obj.id}"')

    @pytest.mark.parametrize(
        "boundary_code, query",
        [
            ("Code", "code"),  # lowercase query
            ("Code", "CODE"),  # uppercase query
            ("RCodeR", "code"),  # icontain query
        ],
    )
    def test_search_by_code(self, admin_client, country_bl, boundary_code, query):
        url = reverse("admin:geo_boundary_changelist")

        expected_obj = BoundaryFactory(code=boundary_code, boundary_layer=country_bl)
        other_obj = BoundaryFactory(code="OTHER", boundary_layer=country_bl)

        response = admin_client.get(url, data={"q": query})
        assert response.status_code == 200
        assertContains(response=response, text=f'value="{expected_obj.id}"')
        assertNotContains(response=response, text=f'value="{other_obj.id}"')

    def test_filter_by_objects_with_conflicts(self, admin_client, country_bl):
        # Dummy country boundary
        b1 = BoundaryFactory(boundary_layer=country_bl)

        # Dummy province boundary layer
        province_bl = BoundaryLayerFactory(boundary=b1, boundary_type=country_bl.boundary_type, parent=country_bl)
        b2 = BoundaryFactory(boundary_layer=province_bl, parent=b1)

        url = reverse("admin:geo_boundary_changelist")

        response = admin_client.get(url, data={"conflicts": "False"})
        assert response.status_code == 200
        assertContains(response=response, text=f'value="{b1.id}"')
        assertContains(response=response, text=b2.id)

        response = admin_client.get(url, data={"conflicts": "True"})
        assert response.status_code == 200
        assertNotContains(response=response, text=f'value="{b1.id}"')
        assertNotContains(response=response, text=f'value="{b2.id}"')

        # Generate conflict in b2
        b2.depth = country_bl.depth
        b2.save()

        response = admin_client.get(url, data={"conflicts": "True"})
        assert response.status_code == 200
        assertNotContains(response=response, text=f'value="{b1.id}"')
        assertContains(response=response, text=f'value="{b2.id}"')

    def test_filter_by_boundary_layer_type(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url, data={"boundary_layer__boundary_type__exact": "adm"})
        assert response.status_code == 200

    def test_filter_by_boundary_layer(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url, data={"boundary_layer__exact": "1"})
        assert response.status_code == 200

    def test_filter_by_creation_time(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url, data={"created_at": timezone.now()})
        assert response.status_code == 200

    def test_filter_by_updated_time(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url, data={"updated_at": timezone.now()})
        assert response.status_code == 200

    def test_filter_by_depth(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url, data={"depth__exact": "1"})
        assert response.status_code == 200

    def test_add_is_forbidden(self, admin_client):
        url = reverse("admin:geo_boundary_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        boundary = BoundaryFactory()
        url = reverse("admin:geo_boundary_change", kwargs={"object_id": boundary.pk})
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_import_button_is_displayed(self, admin_client):
        url = reverse("admin:geo_boundary_changelist")
        response = admin_client.get(url)

        url_import = reverse("admin:geo_boundary_import")
        assertContains(
            response=response,
            text=f"<a href='{url_import}' class=\"import_link\">Import</a>",
        )

    def test_import_url(self, admin_client):
        url = reverse("admin:geo_boundary_import")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_import_zipped_shapefile(self, admin_client, country_bl):
        url = reverse("admin:geo_boundary_import")

        # Generating post. Code is XAD
        dummy_shp_zip = os.path.join(os.path.dirname(__file__), "files", "islands_shp.zip")

        assert Boundary.objects.count() == 0

        with open(dummy_shp_zip, "rb") as f:
            data = {
                "input_format": 0,  # zipped shp format index
                "import_file": f,
                "code_field_name": "GID_0",
                "name_field_name": "COUNTRY",
                "boundary_layer": country_bl.id,
            }

            response = admin_client.post(url, data=data)

        assert response.status_code == 200
        assert "result" in response.context
        assert not response.context["result"].has_errors()
        assert "confirm_form" in response.context

        confirm_form = response.context["confirm_form"]

        # Confirm import
        data = confirm_form.initial
        data.update({"boundary_layer": country_bl.id})

        assert data["original_file_name"] == "islands_shp.zip"

        process_import_url = reverse("admin:geo_boundary_process_import")

        response = admin_client.post(process_import_url, data=data, follow=True)
        assert response.status_code == 200

        assert Boundary.objects.filter(code="XAD").exists()

        # Check that file has been removed.
        assert not os.path.exists(data["import_file_name"])


class TestBoundaryLayerAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:geo_boundarylayer_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client, country_bl):
        url = reverse("admin:geo_boundarylayer_changelist")

        province_bl = BoundaryLayerFactory(name="Test", boundary_type=country_bl.boundary_type, parent=country_bl)

        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200

        assertNotContains(response=response, text=f'value="{country_bl.id}"')
        assertContains(response=response, text=f'value="{province_bl.id}"')

    def test_filter_by_boundary_type(self, admin_client):
        url = reverse("admin:geo_boundarylayer_changelist")
        response = admin_client.get(url, data={"boundary_type__exact": "adm"})
        assert response.status_code == 200

    def test_filter_by_level(self, admin_client):
        url = reverse("admin:geo_boundarylayer_changelist")
        response = admin_client.get(url, data={"level__exact": "1"})
        assert response.status_code == 200

    def test_filter_by_boundary(self, admin_client):
        url = reverse("admin:geo_boundarylayer_changelist")
        response = admin_client.get(url, data={"boundary": "1"})
        assert response.status_code == 200

    def test_add(self, admin_client):
        url = reverse("admin:geo_boundarylayer_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "_position": "sorted-child",
                "_ref_node_id": "",
                "name": "Test name",
                "boundary_type": "adm",
                "boundaries-TOTAL_FORMS": "0",
                "boundaries-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        assert BoundaryLayer.objects.filter(name="Test name", boundary_type="adm").exists()

    def test_view(self, admin_client, country_bl):
        url = reverse(
            "admin:geo_boundarylayer_change",
            kwargs={"object_id": country_bl.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
