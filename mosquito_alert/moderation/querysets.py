from django.db.models import Q, QuerySet
from polymorphic.managers import PolymorphicQuerySet


class FlagQuerySet(QuerySet):
    def active(self, bool: bool = True):
        return self.filter(is_active=bool)

    def moderated(self, bool: bool = True):
        return self.exclude(moderated_at__isnull=bool)


class FlagModeratedQueryset(QuerySet):
    def flagged(self, bool: bool = True):
        qs_kwargs = Q(flags__is_active=bool)

        if not bool:
            qs_kwargs |= Q(flags__isnull=True)

        return self.filter(qs_kwargs)


class FlagModeratedPolymorphicModelQuerySet(PolymorphicQuerySet, FlagModeratedQueryset):
    pass
