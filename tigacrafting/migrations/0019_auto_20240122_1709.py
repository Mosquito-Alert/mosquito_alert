# Generated by Django 2.2.7 on 2024-01-22 17:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0018_auto_20231221_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='tigacrafting.CrowdcraftingTask'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='annotations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='crowdcraftingresponse',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='tigacrafting.CrowdcraftingTask'),
        ),
        migrations.AlterField(
            model_name='crowdcraftingresponse',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='responses', to='tigacrafting.CrowdcraftingUser'),
        ),
        migrations.AlterField(
            model_name='crowdcraftingtask',
            name='photo',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='tigaserver_app.Photo'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='best_photo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expert_report_annotations', to='tigaserver_app.Photo'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Simple category assigned by expert or superexpert. Mutually exclusive with complex. If this field has value, then probably there is a validation value', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expert_report_annotations', to='tigacrafting.Categories'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='complex',
            field=models.ForeignKey(blank=True, help_text='Complex category assigned by expert or superexpert. Mutually exclusive with category. If this field has value, there should not be a validation value', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expert_report_annotations', to='tigacrafting.Complex'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='other_species',
            field=models.ForeignKey(blank=True, help_text='Additional info supplied if the user selected the Other species category', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expert_report_annotations', to='tigacrafting.OtherSpecies'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expert_report_annotations', to='tigaserver_app.Report'),
        ),
        migrations.AlterField(
            model_name='expertreportannotation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expert_report_annotations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='movelabannotation',
            name='task',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='movelab_annotation', to='tigacrafting.CrowdcraftingTask'),
        ),
        migrations.AlterField(
            model_name='userstat',
            name='last_emergency_mode_grab',
            field=models.ForeignKey(blank=True, help_text='Last country user pulled map data from', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emergency_pullers', to='tigaserver_app.EuropeCountry'),
        ),
        migrations.AlterField(
            model_name='userstat',
            name='national_supervisor_of',
            field=models.ForeignKey(blank=True, help_text='Country of which the user is national supervisor. It means that the user will receive all the reports in his country', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='supervisors', to='tigaserver_app.EuropeCountry'),
        ),
        migrations.AlterField(
            model_name='userstat',
            name='native_of',
            field=models.ForeignKey(blank=True, help_text='Country in which the user operates. Used mainly for filtering purposes', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='natives', to='tigaserver_app.EuropeCountry'),
        ),
        migrations.AlterField(
            model_name='userstat',
            name='nuts2_assignation',
            field=models.ForeignKey(blank=True, help_text='Nuts2 division in which the user operates. Influences the priority of report assignation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nuts2_assigned', to='tigaserver_app.NutsEurope'),
        ),
    ]
