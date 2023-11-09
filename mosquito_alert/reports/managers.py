from polymorphic.managers import PolymorphicManager

from .querysets import IndividualReportQueryset, ReportQueryset

ReportManager = PolymorphicManager.from_queryset(ReportQueryset)

IndividualReportManager = PolymorphicManager.from_queryset(IndividualReportQueryset)
