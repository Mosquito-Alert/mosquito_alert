# Generated by Django 3.2.25 on 2024-11-29 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigapublic', '0006_auto_20241030_1326'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapauxreports',
            name='expert_validated',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='activity',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='sand',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='species1',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='species2',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='treatment',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stormdrain',
            name='water',
            field=models.BooleanField(blank=True, max_length=10, null=True),
        ),
    ]
