# Generated by Django 2.2.7 on 2022-03-17 15:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0030_auto_20220317_1400'),
        ('tigacrafting', '0005_merge_20220217_0802'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstat',
            name='last_emergency_mode_grab',
            field=models.ForeignKey(blank=True, help_text='Last country user pulled map data from', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='emergency_pullers', to='tigaserver_app.EuropeCountry'),
        ),
    ]