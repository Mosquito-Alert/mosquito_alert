# Generated by Django 2.2.7 on 2021-04-12 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0016_nutseurope'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='nuts_3',
            field=models.CharField(blank=True, max_length=5),
        ),
    ]