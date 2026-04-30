import factory
from factory.django import DjangoModelFactory

from ..models import Workspace, WorkspaceCollaborationGroup


class WorkspaceFactory(DjangoModelFactory):
    class Meta:
        model = Workspace

    country = factory.SubFactory(
        "mosquito_alert.geo.tests.factories.EuropeCountryFactory",
    )


class WorkspaceCollaborationGroupFactory(DjangoModelFactory):
    class Meta:
        model = WorkspaceCollaborationGroup

    name = factory.Sequence(lambda n: "Group %s" % n)

    @factory.post_generation
    def workspaces(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.workspaces.add(*extracted)

    @factory.post_generation
    def reviewers(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.reviewers.add(*extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # workspaces & reviewers is already set. Do not call obj.save againg
        if results:
            _ = results.pop("workspaces", None)
            _ = results.pop("reviewers", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)
