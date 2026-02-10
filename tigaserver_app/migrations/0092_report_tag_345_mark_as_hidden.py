from django.db import migrations, models
from django.contrib.contenttypes.models import ContentType


def mark_reports_with_tag_345_as_hidden(apps, schema_editor):
    Report = apps.get_model('tigaserver_app', 'Report')
    ReportContentType = ContentType.objects.get_for_model(Report)
    UUIDTaggedItem = apps.get_model('tigaserver_app', 'UUIDTaggedItem')

    Report.objects.filter(
        models.Exists(
            UUIDTaggedItem.objects.filter(
                object_id=models.OuterRef('pk'),
                content_type__pk=ReportContentType.pk,
                tag__name='345'
            )
        )
    ).update(hide=True, published_at=None)

class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0091_report_report_visible_published_idx'),
    ]

    operations = [
        migrations.RunPython(mark_reports_with_tag_345_as_hidden, migrations.RunPython.noop),

    ]
