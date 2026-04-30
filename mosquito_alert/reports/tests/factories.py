import datetime
import factory
from factory.django import DjangoModelFactory
from random import uniform
import uuid

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db.models.signals import post_save

from mosquito_alert.users.tests.factories import TigaUserFactory

from ..models import Report, Photo


def random_valid_location() -> Point:
    while True:
        lat = uniform(settings.MIN_ALLOWED_LATITUDE, settings.MAX_ALLOWED_LATITUDE)
        lon = uniform(-180, 180)
        p = Point(lon, lat, srid=4326)
        if not settings.OCEAN_GEOM.contains(p):
            return p


class ReportFactory(DjangoModelFactory):
    # NOTE: Using string until Report.version_UUID is UUIDField some day.
    version_UUID = factory.LazyFunction(lambda: str(uuid.uuid4()))

    user = factory.SubFactory(TigaUserFactory)
    type = factory.Iterator(Report.TYPE_CHOICES, getter=lambda c: c[0])

    phone_upload_time = factory.Faker("past_datetime", tzinfo=datetime.timezone.utc)
    creation_time = factory.SelfAttribute("phone_upload_time")

    point = factory.LazyFunction(random_valid_location)

    location_choice = factory.Iterator(
        Report.LOCATION_CHOICE_CHOICES, getter=lambda c: c[0]
    )
    current_location_lon = factory.LazyAttribute(
        lambda o: o.point.x if o.location_choice == Report.LOCATION_CURRENT else None
    )
    current_location_lat = factory.LazyAttribute(
        lambda o: o.point.y if o.location_choice == Report.LOCATION_CURRENT else None
    )

    selected_location_lon = factory.LazyAttribute(
        lambda o: o.point.x if o.location_choice == Report.LOCATION_SELECTED else None
    )
    selected_location_lat = factory.LazyAttribute(
        lambda o: o.point.y if o.location_choice == Report.LOCATION_SELECTED else None
    )

    note = factory.Faker("paragraph")

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.tags.add(*extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # tags is already set. Do not call obj.save againg
        if results:
            _ = results.pop("tags", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)

    class Meta:
        model = Report


class BiteReportFactory(ReportFactory):
    type = Report.TYPE_BITE
    event_environment = factory.Iterator(
        Report.EVENT_ENVIRONMENT_CHOICES, getter=lambda c: c[0]
    )
    event_moment = factory.Iterator(Report.EVENT_MOMENT_CHOICES, getter=lambda c: c[0])

    head_bite_count = factory.Faker("random_int", min=0, max=10)
    left_arm_bite_count = factory.Faker("random_int", min=0, max=10)
    right_arm_bite_count = factory.Faker("random_int", min=0, max=10)
    chest_bite_count = factory.Faker("random_int", min=0, max=10)
    left_leg_bite_count = factory.Faker("random_int", min=0, max=10)
    right_leg_bite_count = factory.Faker("random_int", min=0, max=10)

    class Meta:
        model = Report


class ReportWithPhotosFactory(ReportFactory):
    photos = factory.RelatedFactoryList(
        "mosquito_alert.reports.tests.factories.PhotoFactory",
        factory_related_name="report",
        size=2,
    )

    class Meta:
        model = Report


class BreedingSiteReportFactory(ReportWithPhotosFactory):
    type = Report.TYPE_SITE

    breeding_site_type = factory.Iterator(Report.BreedingSiteType.choices)
    breeding_site_has_water = factory.Faker("boolean")
    breeding_site_in_public_area = factory.Faker("boolean")
    breeding_site_has_near_mosquitoes = factory.Faker("boolean")
    breeding_site_has_larvae = factory.Faker("boolean")

    class Meta:
        model = Report


class ObservationReportFactory(ReportWithPhotosFactory):
    type = Report.TYPE_ADULT

    identification_task = factory.RelatedFactory(
        "mosquito_alert.identification_tasks.tests.factories.IdentificationTaskFactory",
        factory_related_name="report",
    )

    class Meta:
        model = Report


class ObservationReportWithoutSignalFactory(ObservationReportFactory):
    photos = factory.RelatedFactoryList(
        "mosquito_alert.reports.tests.factories.PhotoWithoutSignalFactory",
        factory_related_name="report",
        size=2,
    )

    class Meta:
        model = Report


class PhotoFactory(DjangoModelFactory):
    photo = factory.django.ImageField()
    report = factory.SubFactory(ReportFactory)

    class Meta:
        model = Photo


@factory.django.mute_signals(post_save)
class PhotoWithoutSignalFactory(PhotoFactory):
    class Meta:
        model = Photo
