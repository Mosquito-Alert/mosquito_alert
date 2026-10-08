from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.utils.module_loading import import_string
from rest_framework_simplejwt.settings import api_settings

from mosquito_alert.geo.tests.factories import NutsEuropeFactory
from mosquito_alert.reports.models import Report
from mosquito_alert.reports.tests.factories import ReportFactory


@pytest.fixture
def stats_admin_token(user):
    user.is_superuser = True
    user.save()
    token_class = import_string(api_settings.TOKEN_OBTAIN_SERIALIZER).token_class
    return str(token_class.for_user(user).access_token)


@pytest.fixture
def report_stats_data(db, es_country):
    cache.clear()
    area = NutsEuropeFactory(
        levl_code=2, europecountry=es_country, name_latn="Stats test area"
    )
    adult_region = NutsEuropeFactory(
        levl_code=3, europecountry=es_country, name_latn="Stats adult region"
    )
    bite_region = NutsEuropeFactory(
        levl_code=3, europecountry=es_country, name_latn="Stats bite region"
    )
    reports = [
        (Report.TYPE_ADULT, datetime(2024, 1, 1, 12, tzinfo=timezone.utc)),
        (Report.TYPE_ADULT, datetime(2024, 1, 3, 12, tzinfo=timezone.utc)),
        (Report.TYPE_BITE, datetime(2024, 1, 3, 12, tzinfo=timezone.utc)),
    ]
    created_reports = [ReportFactory(type=report_type) for report_type, _ in reports]
    for report, (_, upload_time), region in zip(
        created_reports, reports, [adult_region, adult_region, bite_region]
    ):
        Report.objects.filter(pk=report.pk).update(
            server_upload_time=upload_time,
            country=es_country,
            nuts_2_fk=area,
            nuts_3_fk=region,
        )

    hidden_report = ReportFactory(type=Report.TYPE_ADULT, hide=True)
    unpublished_report = ReportFactory(type=Report.TYPE_ADULT)
    Report.objects.filter(pk=hidden_report.pk).update(
        server_upload_time=datetime(2024, 1, 2, 12, tzinfo=timezone.utc)
    )
    Report.objects.filter(pk=unpublished_report.pk).update(
        server_upload_time=datetime(2024, 1, 2, 12, tzinfo=timezone.utc),
        published_at=None,
    )
    return SimpleNamespace(
        area=area, adult_region=adult_region, bite_region=bite_region
    )
