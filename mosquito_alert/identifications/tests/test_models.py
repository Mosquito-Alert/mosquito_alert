import pytest

from ..models import IdentifierUserProfile
from .factories import IdentifierUserProfileFactory


@pytest.mark.django_db
class TestIdentifierUserProfile:
    def test_pk_is_same_as_user(self):
        u_profile = IdentifierUserProfileFactory()
        assert u_profile.pk == u_profile.user.pk

    def test_cascade_user_on_delete(self, user):
        u_profile = IdentifierUserProfileFactory(user=user)

        qs = IdentifierUserProfile.objects.filter(pk=u_profile.pk)

        assert qs.exists()

        user.delete()

        assert not qs.exists()

    def test_is_superexpert_is_not_active_by_default(self):
        u_profile = IdentifierUserProfileFactory()

        assert not u_profile.is_superexpert

    def test__str__(self, user):
        u_profile = IdentifierUserProfileFactory(user=user)
        assert u_profile.__str__() == user.__str__()


@pytest.mark.django_db
class TestIdentificationResult:
    def test_TODO(self):
        raise
