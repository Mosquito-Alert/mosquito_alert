# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.contrib.auth.models import User


# def list_users():
#     for u in User.objects.all().order_by('username'):
#         assign_tester(u)


def get_user_groups(user):
    groups = []
    for g in user.groups.all():
        groups.append(g.name)
    return ",".join(groups)


def print_user_info(category, user):
    groups = get_user_groups(user)
    if category == 'no_userstat':
        native_of = "no native country"
    else:
        native_of = user.userstat.native_of.name_engl if user.userstat.native_of is not None else "no native country"
    print("{0} - {1} - {2} - {3}".format(category, user.username, groups, native_of))


def print_user_info_list(category, users):
    for u in users:
        print_user_info(category,u)
    print("")


def assign_tester():
    no_userstat = []
    superexperts = []
    bb_users = []
    national_supervisors = []
    regular_users = []
    for this_user in User.objects.all().order_by('username'):
        if not hasattr(this_user, 'userstat'):
            #print_user_info('no_userstat', this_user)
            no_userstat.append(this_user)
        else:
            if this_user.userstat.is_superexpert():
                #print_user_info('superexpert',this_user)
                superexperts.append(this_user)
            else:
                if this_user.userstat.is_bb_user():
                    #print_user_info('bb_user',this_user)
                    bb_users.append(this_user)
                else:
                    if this_user.userstat.is_national_supervisor():
                        #print_user_info('national_supervisor',this_user)
                        national_supervisors.append(this_user)
                    else: #is regular user
                        #print_user_info('regular_user',this_user)
                        regular_users.append(this_user)
    print_user_info_list('no_userstat', no_userstat)
    print_user_info_list('superexpert', superexperts)
    print_user_info_list('bb_user', bb_users)
    print_user_info_list('national_supervisor', national_supervisors)
    print_user_info_list('regular_user', regular_users)


if __name__ == '__main__':
    assign_tester()