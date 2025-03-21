# Generated by Django 2.2.7 on 2021-04-06 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0012_auto_20210311_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtopic',
            name='topic_group',
            field=models.IntegerField(choices=[(0, 'General'), (1, 'Language topics'), (2, 'Country topics'), (3, 'Special')], default=0, help_text='Your degree of belief that at least one photo shows a tiger mosquito breeding site', verbose_name='Group of topics'),
        ),
        migrations.AlterField(
            model_name='tigauser',
            name='device_token',
            field=models.TextField(blank=True, help_text='Device token, used in messaging. Must be supplied by the client', null=True),
        ),
    ]
