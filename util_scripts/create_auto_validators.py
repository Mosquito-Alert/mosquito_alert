# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import string
import random
from django.contrib.auth.models import User, Group


def generate_password( size=6, chars= string.ascii_uppercase + string.ascii_lowercase + string.digits ):
    return ''.join(random.choice(chars) for _ in range(size))


def create_users():
    try:
        bogus_users = Group.objects.get(name="bogus_users")
    except Group.DoesNotExist:
        bogus_users = Group(name="bogus_users")
        bogus_users.save()
    experts_group = Group.objects.get(name="expert")
    for username in ['innie','minnie','manny']:
        user = User.objects.create_user(username=username, first_name=username, last_name='doe', password=generate_password(size=18))
        experts_group.user_set.add(user)
        user.is_active = False
        user.save()

create_users()