# Generated by Django 2.2.7 on 2021-04-12 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0018_report_nuts_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtopic',
            name='topic_group',
            field=models.IntegerField(choices=[(0, 'General'), (1, 'Language topics'), (2, 'Country topics'), (3, 'Country nuts3'), (4, 'Country nuts2'), (5, 'Special')], default=0, help_text='Your degree of belief that at least one photo shows a tiger mosquito breeding site', verbose_name='Group of topics'),
        ),
        migrations.AlterField(
            model_name='report',
            name='nuts_2',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='nuts_3',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]