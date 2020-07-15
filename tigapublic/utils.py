"""Utility functions."""
# -*- coding: utf-8 -*-
import datetime
import decimal
import json
import requests
import os
from django.contrib.auth.models import User
import re
from .constants import (managers_group, superusers_group, user_roles,
                       epidemiologist_editor_group,
                       epidemiologist_viewer_group)


###################
# User extensions #
###################


class ExtendedUser(User):
    """Custom User Methods.

    Extend the default Django User model with:

    >>> user = UserMethods.objects.get(pk=user.id)

    Or:

    >>> extendUser(user)
    """

    def is_valid(self):
        """Return True if user is valid.

        A valid user is an authenticated and active user.
        """
        return self.is_authenticated and self.is_active

    def is_manager(self):
        """Return True if user is manager.

        A manager must be valid and belong to the managers_group.
        """
        return (self.is_valid() and
                self.groups.filter(name=managers_group).exists())

    def is_epidemiologist_editor(self):
        """Return True if user is epidemiologist editor.

        A epidemiologist must be valid user and belong to the groups
        epidemiologist_editor.
        """
        return (self.is_valid() and
                self.groups.filter(name=epidemiologist_editor_group).exists())

    def is_epidemiologist_viewer(self):
        """Return True if user is epidemiologist viewer.

        A epidemiologist must be valid user and belong to the groups
        is_epidemiologist_viewer  or editor
        """
        return (
                self.groups.filter(
                            name=epidemiologist_viewer_group
                            ).exists()
                or
                self.groups.filter(
                            name=epidemiologist_editor_group
                            ).exists()
                or
                self.groups.filter(
                            name=superusers_group
                            ).exists()
                )

    def is_root(self):
        """Return True if user is root/superadmin.

        A root must be valid and belong to the superusers_group.
        """
        return (self.is_valid() and
                self.groups.filter(name=superusers_group).exists())

    def in_group(self, group):
        """Return True if user is in groupself."""
        return (self.is_valid() and
                self.groups.filter(name=group).exists())

    def is_authorized(self):
        """Return True if user is either root or manager."""
        return (self.is_root() or self.is_manager())

    def get_highest_role(self):
        """Return the name of the role/group it belongs to.

        Returns only the most permissive role.

        Ex: if user belongs to superusers and managers, it returns superusers.
        """
        # Get the groups of the user matching the roles defined in constants
        roles = [group for group in self.groups.values_list('name', flat=True)
                 if group in user_roles]
        # Return the first matching role (as it is the most permissive one)
        if roles:
            return roles[0]
        else:
            return 'anonymous'

    class Meta:
        """Meta."""

        proxy = True


class AnonymousUser(User):
    """Anonymous user to fake extended methods."""

    def is_valid(self):
        """Return True if user is valid.

        A valid user is an authenticated and active user.
        """
        return False

    def is_manager(self):
        """Return True if user is manager.

        A manager must be valid and belong to the managers_group.
        """
        return False

    def is_root(self):
        """Return True if user is root/superadmin.

        A root must be valid and belong to the superusers_group.
        """
        return False

    def is_authorized(self):
        """Return True if user is either root or manager."""
        return False

    def get_highest_role(self):
        """Return the name of the role/group it belongs to."""
        return 'anonymous'


def extendUser(user):
    """Return a User with extended methods."""
    if user.id is not None:
        return ExtendedUser.objects.get(pk=user.id)
    else:
        return AnonymousUser(user.id)


def userIsValid(user):
    """Return True if user is valid.

    A valid user is an active & authenticated user.
    """
    return user.is_authenticated and user.is_active


def userIsManager(user):
    """Return True if user is manager.

    A manager must be valid and belong to the managers_group.
    """
    return (userIsValid(user) and
            user.groups.filter(name=managers_group).exists())


def userIsRoot(user):
    """Return True if user is root.

    A root must be valid and belong to the superusers_group.
    """
    return (userIsValid(user) and
            user.groups.filter(name=superusers_group).exists())


#################
# JSON encoding #
#################

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder."""

    def default(self, o):
        """Parse JSON attribute."""
        if isinstance(o, decimal.Decimal):
            # if it is decimal, float it
            return float(o)
        elif isinstance(o, datetime.datetime):
            # if it is datetime, return the isoformat
            return o.isoformat()
        else:
            # if it is another type of field, call the parent class
            return super(CustomJSONEncoder, self).default(o)


# class Struct:
#    """Struct."""
#
#    def __init__(self, **entries):
#        """Constructor."""
#        self.__dict__.update(entries)

# def dictfetchall(cursor):
#     "Return all rows from a cursor as a dict"
#     columns = [col[0] for col in cursor.description]
#     return [
#         dict(zip(columns, row))
#         for row in cursor.fetchall()
#     ]

#############
# Tools
#############

def ValuesQuerySetToDict(vqs):
    """Turn Queryset to array of dicts."""
    return [item for item in vqs]


def julianDay(date):
    """Get julianDay from date."""
    julianDay = '%03d' % (date.timetuple().tm_yday)
    return int(julianDay)


def urlExists(url):
    """Check if url exists."""
    r = requests.head(url)
    return r.status_code == requests.codes.ok


def get_directory_structure(rootdir, filename):
    """
    Nested dictionaryself.

    Creates an ordered list (desc) that represents the availability of models
    """
    valid_ext = [filename]
    files = []
    folders = []
    dictlist = []
    dict = {}

    # models folder patterns yyyy/mm
    pattern = re.compile("^(\d{4}\/(0[1-9]|1[0-2]))$")
    # pattern = re.compile("^(\d{4}\/0[1-9]|\d{4}\/1[0-2])$")

    for root, dirs, files in sorted(os.walk(rootdir)):
        if root[len(rootdir)+1:].count(os.sep) < 2:
            for f in files:
                if f.endswith(tuple(valid_ext)):
                    root = root.replace(rootdir, '')
                    root = root.replace('\\', '/')
                    if (re.match(pattern, root)):
                        # split
                        folders = root.split('/')
                        if not folders[0] in dict:
                            # initialize all 12 months as disabled
                            dict[folders[0]] = [0, 0, 0, 0, 0, 0,
                                                0, 0, 0, 0, 0, 0]

                        # Enable current month
                        dict[folders[0]][int(folders[1]) - 1] = 1

    # Turn dict into array
    for key, value in dict.items():
        temp = [key, value]
        dictlist.append(temp)
    # Return properly ordered list
    return sorted(dictlist, key=lambda l: l[0], reverse=True)
