from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportStatsGroupBy(models.TextChoices):
    DATE = "date", _("Date")
    TYPE = "type", _("Type")
    REGION = "region", _("Region")


class ReportStatsInterval(models.TextChoices):
    DAY = "day", _("Day")
    WEEK = "week", _("Week")
    MONTH = "month", _("Month")


class NutsLevel(models.IntegerChoices):
    NUTS_2 = 2, _("NUTS 2")
    NUTS_3 = 3, _("NUTS 3")


class AreaLevel(models.TextChoices):
    COUNTRY = "country", _("Country")
    NUTS2 = "nuts2", _("NUTS 2")
    NUTS3 = "nuts3", _("NUTS 3")


# Ordering used to validate that `level` is strictly finer than `area`'s level.
AREA_LEVEL_ORDER = {
    AreaLevel.COUNTRY: 0,
    AreaLevel.NUTS2: 2,
    AreaLevel.NUTS3: 3,
}
