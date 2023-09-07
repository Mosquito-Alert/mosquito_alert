import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from mosquito_alert.users.tests.factories import UserFactory

from ..admin import PhotoAdmin
from ..models import Photo
from . import testdata
from .factories import PhotoFactory


@pytest.mark.django_db
class TestPhotoAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:images_photo_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_user_filter(self, admin_client, user):
        url = reverse("admin:images_photo_changelist")
        response = admin_client.get(url, data={"user__id__exact": user.pk})
        assert response.status_code == 200

    def test_add(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse("admin:images_photo_add")
        response = client.get(url)
        assert response.status_code == 200

        image = SimpleUploadedFile(
            "sample_image.jpeg",
            content=File(open(testdata.TESTEXIFIMAGE_PATH, "rb")).read(),
            content_type="image/jpeg",
        )

        assert Photo.objects.all().count() == 0

        response = client.post(
            url,
            data={
                "image": image,
                "flag-flag-content_type-object_id-TOTAL_FORMS": "0",
                "flag-flag-content_type-object_id-INITIAL_FORMS": "0",
                "flag-flag-content_type-object_id-empty-flags-TOTAL_FORMS": "0",
                "flag-flag-content_type-object_id-empty-flags-INITIAL_FORMS": "0",
                "photo_identification_tasks-TOTAL_FORMS": "0",
                "photo_identification_tasks-INITIAL_FORMS": "0",
            },
        )

        assert response.status_code == 302
        assert Photo.objects.first().user.pk == admin_user.pk

    def test_update_does_not_modify_user(self, client):
        u_creator = UserFactory()
        p = PhotoFactory(user=u_creator)

        url = reverse(
            "admin:images_photo_change",
            kwargs={"object_id": p.pk},
        )

        u_logged_in = UserFactory()
        client.force_login(u_logged_in)

        response = client.post(
            url,
            data={"user": u_logged_in.pk},
        )

        assert response.status_code == 302

        p.refresh_from_db()
        assert p.user == u_creator

    def test_created_at_field_is_readonly(self):
        assert "created_at" in PhotoAdmin.readonly_fields

    def test_preview_is_readonly(self):
        assert "preview" in PhotoAdmin.readonly_fields

    def test_preview_html(self):
        p = PhotoFactory()

        photo_admin = PhotoAdmin(model=Photo, admin_site=AdminSite())

        assert photo_admin.preview(p) == f"<img src='{p.image.url}' height='150' />"

    def test_view(self, admin_client):
        p = PhotoFactory()
        url = reverse(
            "admin:images_photo_change",
            kwargs={"object_id": p.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_exif_dict_not_shows_if_not_perm(self, user, rf):
        p = PhotoFactory()

        assert not user.has_perm(f"{p._meta.app_label}.view_exif")

        request = rf.get(
            path=reverse(
                "admin:images_photo_change",
                kwargs={"object_id": p.pk},
            )
        )
        request.user = user

        kwargs = {"request": request, "obj": p}

        photo_admin = PhotoAdmin(model=Photo, admin_site=AdminSite())

        assert "exif_dict" not in photo_admin.get_fields(**kwargs)
        assert "exif_dict" not in photo_admin.get_readonly_fields(**kwargs)

    def test_exif_dict_shows_if_permission(self, user, rf):
        perm = Permission.objects.get(codename="view_exif")
        user.user_permissions.add(perm)

        p = PhotoFactory()

        assert user.has_perm(f"{p._meta.app_label}.view_exif")

        request = rf.get(
            path=reverse(
                "admin:images_photo_change",
                kwargs={"object_id": p.pk},
            )
        )
        request.user = user

        photo_admin = PhotoAdmin(model=Photo, admin_site=AdminSite())

        kwargs = {"request": request, "obj": p}
        assert "exif_dict" in photo_admin.get_fields(**kwargs)
        assert "exif_dict" in photo_admin.get_readonly_fields(**kwargs)

    def test_exif_dict_shows_if_superuser(self, admin_user, rf):
        p = PhotoFactory()

        request = rf.get(
            path=reverse(
                "admin:images_photo_change",
                kwargs={"object_id": p.pk},
            )
        )
        request.user = admin_user

        photo_admin = PhotoAdmin(model=Photo, admin_site=AdminSite())

        kwargs = {"request": request, "obj": p}
        assert "exif_dict" in photo_admin.get_fields(**kwargs)
        assert "exif_dict" in photo_admin.get_readonly_fields(**kwargs)
