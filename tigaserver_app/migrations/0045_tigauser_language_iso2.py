# Generated by Django 2.2.7 on 2024-03-14 12:05

from django.db import migrations, models
from django.db.models.functions import Coalesce, Length


def set_language_iso2_to_last_report_language(apps, schema_editor):
    TigaUser = apps.get_model("tigaserver_app", "TigaUser")
    Report = apps.get_model("tigaserver_app", "Report")

    latest_report_subquery = Report.objects.annotate(
        language_length=Length('app_language')
    ).filter(
        user_id=models.OuterRef('pk'),
        app_language__isnull=False,
        language_length__lte=TigaUser._meta.get_field('language_iso2').max_length
    ).order_by('-server_upload_time')

    TigaUser.objects.update(
        language_iso2=Coalesce(
            models.Subquery(latest_report_subquery.values('app_language')[:1]),
            models.Value(TigaUser._meta.get_field('language_iso2').default)
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0044_refactor'),
    ]

    operations = [
        migrations.AddField(
            model_name='tigauser',
            name='language_iso2',
            field=models.CharField(default='en', help_text='Language setting of app. 2-digit ISO-639-1 language code.', max_length=2),
        ),
        migrations.RunPython(set_language_iso2_to_last_report_language, migrations.RunPython.noop),
    ]