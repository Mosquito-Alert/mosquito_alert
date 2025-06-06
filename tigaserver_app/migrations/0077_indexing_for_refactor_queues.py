# Generated by Django 2.2.7 on 2024-11-12 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0076_fix_device_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='europecountry',
            name='is_bounding_box',
            field=models.BooleanField(db_index=True, default=False, help_text='If true, this geometry acts as a bounding box. The bounding boxes act as little separate entolabs, in the sense that no reports located inside a bounding box should reach an expert outside this bounding box'),
        ),
        migrations.AlterField(
            model_name='europecountry',
            name='national_supervisor_report_expires_in',
            field=models.IntegerField(db_index=True, default=14, help_text='Number of days that a report in the queue is exclusively available to the nagional supervisor. For example, if the field value is 6, after report_creation_time + 6 days a report will be available to all users'),
        ),
        migrations.AlterField(
            model_name='historicalreport',
            name='type',
            field=models.CharField(choices=[('bite', 'Bite'), ('adult', 'Adult'), ('site', 'Breeding Site'), ('mission', 'Mission')], db_index=True, help_text="Type of report: 'adult', 'site', or 'mission'.", max_length=7),
        ),
        migrations.AlterField(
            model_name='report',
            name='hide',
            field=models.BooleanField(db_index=True, default=False, help_text='Hide this report from public views?'),
        ),
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.CharField(choices=[('bite', 'Bite'), ('adult', 'Adult'), ('site', 'Breeding Site'), ('mission', 'Mission')], db_index=True, help_text="Type of report: 'adult', 'site', or 'mission'.", max_length=7),
        ),
        migrations.DeleteModel(
            name='GlobalAssignmentStat',
        ),
    ]
