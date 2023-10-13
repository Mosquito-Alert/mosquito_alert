import pytest
from django.db import models
from django.utils import timezone

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin

from ..models import Bite
from .factories import BiteFactory


@pytest.mark.django_db
class TestBiteModel(AbstractDjangoModelTestMixin):
    model = Bite
    factory_cls = BiteFactory

    # fields
    def test_individual_can_be_null(self):
        assert self.model._meta.get_field("individual").null

    def test_individual_deletion_is_protected(self):
        _on_delete = self.model._meta.get_field("individual").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_datetime_auto_now_add(self):
        assert self.model._meta.get_field("datetime").auto_now_add

    def test_body_part_can_not_be_null(self):
        assert not self.model._meta.get_field("body_part").null

    # meta
    @pytest.mark.freeze_time
    def test__str__(self):
        bite = self.factory_cls(body_part=Bite.BodyParts.HEAD)
        expected_str = "{} ({})".format(Bite.BodyParts.HEAD.label, timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
        assert bite.__str__() == expected_str
