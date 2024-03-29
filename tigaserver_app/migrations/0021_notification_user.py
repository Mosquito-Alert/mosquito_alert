# Generated by Django 2.2.7 on 2021-05-03 08:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0020_auto_20210503_0754'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(default='00000000-0000-0000-0000-000000000000', help_text='User to which the notification will be sent', on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_notifications', to='tigaserver_app.TigaUser'),
        ),
    ]
