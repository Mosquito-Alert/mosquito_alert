# Generated by Django 2.2.7 on 2021-05-03 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0019_auto_20210412_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationcontent',
            name='body_html_en',
            field=models.TextField(blank=True, default=None, help_text='Expert comment, expanded and allows html, in english', null=True),
        ),
        migrations.AlterField(
            model_name='notificationcontent',
            name='title_en',
            field=models.TextField(blank=True, default=None, help_text='Title of the comment, shown in non-detail view, in english', null=True),
        ),
    ]