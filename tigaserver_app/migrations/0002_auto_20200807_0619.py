# Generated by Django 2.2.7 on 2020-08-07 06:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fix',
            name='mask_size',
            field=models.FloatField(blank=True, help_text='size of location mask used', null=True),
        ),
        migrations.AddField(
            model_name='reportresponse',
            name='answer_id',
            field=models.IntegerField(blank=True, help_text='Numeric identifier of the answer.', null=True),
        ),
        migrations.AddField(
            model_name='reportresponse',
            name='answer_value',
            field=models.CharField(blank=True, help_text='The value right now can contain 2 things: an integer representing the number or bites, or either a WKT representation of a point for a location answer. In all other cases, it will be blank', max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='reportresponse',
            name='question_id',
            field=models.IntegerField(blank=True, help_text='Numeric identifier of the question.', null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='type',
            field=models.CharField(choices=[('bite', 'Bite'), ('adult', 'Adult'), ('site', 'Breeding Site'), ('mission', 'Mission')], help_text="Type of report: 'adult', 'site', or 'mission'.", max_length=7),
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(help_text='Unique identifier of the session. Automatically generated by server when session created.', primary_key=True, serialize=False)),
                ('session_ID', models.IntegerField(db_index=True, help_text='The session ID number. Should be an integer that increments by 1 for each session from a given user.')),
                ('session_start_time', models.DateTimeField(help_text='Date and time on phone when the session was started. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".')),
                ('session_end_time', models.DateTimeField(blank=True, help_text='Date and time on phone when the session was ended. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".', null=True)),
                ('user', models.ForeignKey(help_text='user_UUID for the user sending this report. Must be exactly 36 characters (32 hex digits plus 4 hyphens) and user must have already registered this ID.', on_delete=django.db.models.deletion.DO_NOTHING, related_name='user_sessions', to='tigaserver_app.TigaUser')),
            ],
            options={
                'unique_together': {('session_ID', 'user')},
            },
        ),
        migrations.AddField(
            model_name='report',
            name='session',
            field=models.ForeignKey(blank=True, help_text='Session ID for session in which this report was created ', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='session_reports', to='tigaserver_app.Session'),
        ),
    ]