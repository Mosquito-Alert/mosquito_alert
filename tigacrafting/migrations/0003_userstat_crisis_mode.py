# Generated by Django 2.2.7 on 2021-11-22 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0002_auto_20200807_0619'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstat',
            name='crisis_mode',
            field=models.BooleanField(default=False, verbose_name='Tells if the validator is working in crisis mode or not'),
        ),
    ]
