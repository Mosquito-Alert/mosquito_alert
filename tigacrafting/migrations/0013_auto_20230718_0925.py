# Generated by Django 2.2.7 on 2023-07-18 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0012_auto_20230718_0924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aimaalertlog',
            name='hit',
            field=models.BooleanField(blank=True, null=True, verbose_name='True if AIMA identification was initially correct, False if AIMA initially failed and was revised'),
        ),
    ]