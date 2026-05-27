
from django.db import migrations


def merge_incorrect_countries(apps, schema_editor):
    Country = apps.get_model('geo', 'Country')
    OWCampaigns = apps.get_model('campaigns', 'OWCampaigns')
    Report = apps.get_model('reports', 'Report')
    UserStat = apps.get_model('users', 'UserStat')

    def migrate_fk_countries(from_country, to_country):
        if from_country and to_country:
            OWCampaigns.objects.filter(country=from_country).update(country=to_country)
            Report.objects.filter(country=from_country).update(country=to_country)
            UserStat.objects.filter(country=from_country).update(country=to_country)

        if from_country:
            from_country.delete()

    norway = Country.objects.filter(iso3_code='NOR').first()
    svalbard = Country.objects.filter(iso3_code='SJM').first()
    migrate_fk_countries(from_country=svalbard, to_country=norway)

    rapa_nui = Country.objects.filter(iso3_code='RPN').first()
    chile = Country.objects.filter(iso3_code='CHL').first()
    migrate_fk_countries(from_country=rapa_nui, to_country=chile)

    saint_lious_missouri = Country.objects.filter(iso3_code='STL').first()
    usa = Country.objects.filter(iso3_code='USA').first()
    migrate_fk_countries(from_country=saint_lious_missouri, to_country=usa)


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0006_remove_europecountry_is_bounding_box_and_more'),
        ('users', '0004_remove_userstat_national_supervisor_of_and_more')
    ]

    operations = [
        migrations.RunPython(
            merge_incorrect_countries, reverse_code=migrations.RunPython.noop
        ),
    ]