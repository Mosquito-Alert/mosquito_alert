'''
Test sending emails with hetzner account
'''
import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from tigaserver_project import settings
import time


def send_test_email():
    subject = 'This is a test message'
    message = 'Hello from info@mosquitoalert.com'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['a.escobar@creaf.uab.cat', ]
    send_mail(subject, message, email_from, recipient_list)
    print("Email sent!")

def main():
    pass


if __name__ == "__main__":
    main()