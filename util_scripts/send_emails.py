'''
Automatic send email script
'''
import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMessage
import time


USERS_FILE = '/home/webuser/Documents/filestigaserver/registre_usuaris_aimcost/clean_copy_last.csv'
#USERS_FILE = '/home/webuser/Documents/filestigaserver/registre_usuaris_aimcost/test.csv'


def crunch():
    with open(USERS_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            name = row[0]
            send_to = [row[1]]
            login = row[3]
            password = row[4]
            test_link = "http://madev.creaf.cat/experts"
            production_link = "http://webserver.mosquitoalert.com/experts"
            document_autoria = "https://drive.google.com/file/d/10gxhi67f_PX8BlL5q_NQWPQ5N0dSriQi/view?usp=sharing"
            #plaintext = get_template('tigacrafting/aimsurv_email_model.txt')
            plaintext = get_template('tigacrafting/aimsurv_prod_email_model.txt')
            context = Context(
                    {
                        'login': login,
                        'password': password,
                        'name': name,
                        'test_link': test_link,
                        'production_link': production_link,
                        'document_autoria': document_autoria
                    }
            )
            text_content = plaintext.render(context)
            email = EmailMessage( "Moving to production EntoLab", text_content, to=send_to)
            print("Sending email to {0}".format(name,))
            email.send(fail_silently=False)
            time.sleep(5)

crunch()