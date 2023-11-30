from django.db.models import Manager

from .querysets import SpecieDistributionQuerySet

SpecieDistributionManager = Manager.from_queryset(SpecieDistributionQuerySet)
