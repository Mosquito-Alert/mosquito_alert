# Generated by Django 2.2.7 on 2021-10-28 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0002_auto_20200807_0619'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='expertreportannotation',
            constraint=models.UniqueConstraint(fields=('user', 'report'), name='unique_assignation'),
        ),
    ]
