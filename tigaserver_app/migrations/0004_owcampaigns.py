# Generated by Django 2.2.7 on 2020-12-11 08:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tigaserver_app', '0003_auto_20200921_0844'),
    ]

    operations = [
        migrations.CreateModel(
            name='OWCampaigns',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posting_address', models.TextField(help_text='Full posting address of the place where the samples will be sent')),
                ('campaign_start_date', models.DateTimeField(help_text='Date when the campaign starts. No samples should be collected BEFORE this date.')),
                ('campaign_end_date', models.DateTimeField(help_text='Date when the campaign ends. No samples should be collected AFTER this date.')),
                ('country', models.ForeignKey(help_text='Country in which the campaign is taking place', on_delete=django.db.models.deletion.DO_NOTHING, related_name='campaigns', to='tigaserver_app.EuropeCountry')),
            ],
        ),
    ]
