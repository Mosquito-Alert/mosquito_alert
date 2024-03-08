# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.db import transaction
from tigaserver_app.models import EuropeCountry
from tigacrafting.models import UserStat, AlertNotificationContact

def main():
    with transaction.atomic():
        AlertNotificationContact.objects.all().delete()
        for e in EuropeCountry.objects.all():
            try:
                userstat = UserStat.objects.get(national_supervisor_of=e)
                a = AlertNotificationContact(
                    country=e,
                    email=userstat.user.email
                )
                a.save()
            except UserStat.DoesNotExist:
                pass



if __name__ == "__main__":
    main()