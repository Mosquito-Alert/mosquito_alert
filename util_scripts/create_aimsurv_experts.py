# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


import csv
import string
import random
from django.contrib.auth.models import User, Group


def split_name(s):
    split = s.split(" ")
    name = split[0]
    first_name = split[1]
    return { "name": name, "last_name": first_name }


def get_username(s):
    split = split_name(s)
    elem1 = split['name'][0].lower()
    elem2 = split['last_name'].lower().split("-")[0]
    return elem1 + "." + elem2


def generate_password( size=6, chars= string.ascii_uppercase + string.ascii_lowercase + string.digits ):
    return ''.join(random.choice(chars) for _ in range(size))


def delete_users():
    with open('/home/webuser/Documents/filestigaserver/registre_usuaris_aimcost/clean_copy.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            name = row[0]
            username = get_username(name)
            user = User.objects.get(username=username)
            user.delete()


def create_users():
    with open('/home/webuser/Documents/filestigaserver/registre_usuaris_aimcost/clean_copy.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            name = row[0]
            email = row[1]
            country = row[2]
            sp = split_name(name)
            username = get_username(name)
            password = row[4]
            experts_group = Group.objects.get(name="expert")
            user = User.objects.create_user(username=username,first_name=sp['name'],last_name=sp['last_name'],email=email,password=password)
            experts_group.user_set.add(user)
            print("{0} {1} {2}".format( username, email, password ))

create_users()