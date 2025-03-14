# Generated by Django 2.2.7 on 2021-12-17 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0003_userstat_crisis_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertreportannotation',
            name='validation_complete_executive',
            field=models.BooleanField(default=False, help_text='Available only to national supervisor. Causes the report to be completely validated, with the final classification decided by the national supervisor'),
        ),
    ]
