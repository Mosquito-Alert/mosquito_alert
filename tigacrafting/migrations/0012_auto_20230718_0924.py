# Generated by Django 2.2.7 on 2023-07-18 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigacrafting', '0011_aimaalertlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aimaalertlog',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Introduction status label'),
        ),
    ]