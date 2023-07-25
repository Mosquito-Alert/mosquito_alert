from django.db.models import QuerySet
from polymorphic.managers import PolymorphicQuerySet


class FlagModeratedQueryset(QuerySet):
    def with_permitted_state(self):
        return self.exclude(flags__state__in=self.model.IS_BANNED_STATES)

    def with_banned_state(self):
        return self.filter(flags__state__in=self.model.IS_BANNED_STATES)


class FlagModeratedPolymorphicModelQuerySet(PolymorphicQuerySet, FlagModeratedQueryset):
    pass
