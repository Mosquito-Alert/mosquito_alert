# Generated by Django 2.2.7 on 2021-03-08 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0010_auto_20210308_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtopic',
            name='topic_code',
            field=models.CharField(help_text='Code for the topic.', max_length=100, unique=True),
        ),
    ]
