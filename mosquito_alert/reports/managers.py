from polymorphic.managers import PolymorphicManager

from .querysets import ReportQueryset

ReportManager = PolymorphicManager.from_queryset(ReportQueryset)
