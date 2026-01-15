import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import NotificationTopic, EuropeCountry, SentNotification
from tigaserver_project import settings as settings
from django.utils.translation import gettext_lazy as _


def create_topics():
    # cleanup
    SentNotification.objects.filter(sent_to_topic__isnull=False).delete()
    NotificationTopic.objects.all().delete()

    t = NotificationTopic(topic_code="global", topic_description='Global topic', topic_group=5)
    t.save()

    # language topics
    for lang in settings.LANGUAGES:
        language_name = str(lang[1])
        t = NotificationTopic(topic_code=lang[0],topic_description='Language topic for language ' + language_name, topic_group=1)
        t.save()

    # country topics
    countries = EuropeCountry.objects.all().order_by('name_engl')
    for country in countries:
        country_name = country.name_engl
        topic_code = str(country.gid)
        topic_description = 'Country topic for country {0}'.format(country_name)
        t = NotificationTopic(topic_code=topic_code, topic_description=topic_description, topic_group=2)
        t.save()

    # nuts3
    countries = EuropeCountry.objects.all().order_by('name_engl')
    for country in countries:
        nuts3 = country.nuts.filter(europecountry=country).filter(levl_code=3).order_by('name_latn')
        for n in nuts3:
            country_name = country.name_engl
            topic_code = n.nuts_id
            topic_description = 'Nuts3 topic for country {0} division {1}'.format(country_name, n.name_latn)
            t = NotificationTopic(topic_code=topic_code, topic_description=topic_description, topic_group=3)
            t.save()
    # nuts2
    countries = EuropeCountry.objects.all().order_by('name_engl')
    for country in countries:
        nuts2 = country.nuts.filter(europecountry=country).filter(levl_code=2).order_by('name_latn')
        for n in nuts2:
            country_name = country.name_engl
            topic_code = n.nuts_id
            topic_description = 'Nuts2 topic for country {0} division {1}'.format(country_name, n.name_latn)
            t = NotificationTopic(topic_code=topic_code, topic_description=topic_description, topic_group=4)
            t.save()


create_topics()