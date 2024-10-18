import factory
from factory.django import DjangoModelFactory

from mosquito_alert.geo.tests.factories import BoundaryFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import BoundaryAuthorization, BoundaryMembership


class BoundaryAuthorizationFactory(DjangoModelFactory):
    boundary = factory.SubFactory(BoundaryFactory)

    class Meta:
        model = BoundaryAuthorization


class BoundaryMembershipFactory(factory.django.DjangoModelFactory):
    boundary_authorization = factory.SubFactory(BoundaryAuthorizationFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.Faker("random_element", elements=BoundaryMembership.RoleType.values)

    class Meta:
        model = BoundaryMembership
