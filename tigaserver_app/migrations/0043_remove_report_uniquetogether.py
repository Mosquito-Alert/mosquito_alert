# Generated by Django 2.2.7 on 2024-01-24 07:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0042_update_on_delete_actions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tigauser',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together=set(),
        ),
    ]