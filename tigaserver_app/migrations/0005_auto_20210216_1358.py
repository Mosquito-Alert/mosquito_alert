# Generated by Django 2.2.7 on 2021-02-16 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0004_owcampaigns'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='europecountry',
            options={'managed': True, 'ordering': ['name_engl']},
        ),
    ]
