# This script fills the newly created point geofield
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.db import connection
from tigaserver_app.models import TigaUser
import datetime, pytz


def get_reassigned_special_awards(award_text):
    sql = "select a.id, a.given_to_id, a.date_given, a.special_award_text from tigaserver_app_award a, (select given_to_id, special_award_text from ( select given_to_id, special_award_text, count(given_to_id) from tigaserver_app_award where special_award_text is not null group by given_to_id, special_award_text order by 3 desc) as foo where foo.count > 1) as subq where a.given_to_id = subq.given_to_id and a.special_award_text = subq.special_award_text and subq.special_award_text = %s order by 2,3"
    cursor = connection.cursor()
    cursor.execute(sql, (award_text,))
    data = cursor.fetchall()
    return data


def extract_first_award(keep_list, rows):
    last_user_id = -1
    for d in rows:
        if d[1] != last_user_id:
            last_user_id = d[1]
            keep_list.append(d)
    return keep_list


def mark_user_for_score_update(user_id):
    print("Marking user {0} for score update".format(user_id))
    u = TigaUser.objects.get(pk=user_id)
    u.last_score_update = datetime.datetime(2011, 8, 15, 8, 15, 12, 0, pytz.UTC)
    u.save()


def delete_award_repetitions(row):
    sql = 'delete from tigaserver_app_award where id!=%s and given_to_id=%s and special_award_text=%s'
    cursor = connection.cursor()
    cursor.execute(sql, (row[0], row[1], row[3]))
    print("Deleting redundant award for user {0}, award {1}".format(row[1],row[3]))
    mark_user_for_score_update(row[1])


def main():
    data_10 = get_reassigned_special_awards('achievement_10_reports')
    data_20 = get_reassigned_special_awards('achievement_20_reports')
    data_50 = get_reassigned_special_awards('achievement_50_reports')
    keep = []
    keep = extract_first_award(keep,data_10)
    keep = extract_first_award(keep,data_20)
    keep = extract_first_award(keep,data_50)
    for k in keep:
        delete_award_repetitions(k)

if __name__ == "__main__":
    main()