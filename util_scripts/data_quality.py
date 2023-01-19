# scrapes map_aux_reports table appends some quality indicators and outputs to csv
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

import csv
from tigaserver_app.models import Report
from django.db import connection


def do_work():
    with connection.cursor() as cursor:
        cool_data = [
            'mosquito_tiger_probable',
            'mosquito_tiger_confirmed',
            'japonicus_probable',
            'japonicus_confirmed',
            'culex_probable',
            'culex_confirmed',
            'koreicus_probable',
            'yellow_fever_probable',
            'yellow_fever_confirmed'
        ]
        cursor.execute("select * from map_aux_reports")
        results = cursor.fetchall()
        file = open('qual_data.csv', mode='w')
        classif_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        classif_writer.writerow(["report_id", "user_id", "date", "report_type", "has_note", "quality_adult", "n_photos", "location_choice"])
        for row in results:
            version_uuid = row[1]
            r = Report.objects.get(pk=version_uuid)
            location_choice = r.location_choice
            n_photos_file = row[19]
            observation_date = row[2]
            type = row[6]
            user_id = row[38]
            note = row[22]
            has_note = False if note is None else note.strip() != ''
            quality_adult = (row[23] in cool_data) if type == 'adult' else 'n/a'
            #print("{0} {1} {2} {3} {4} {5} {6}".format(version_uuid, user_id, observation_date, type, has_note, quality_adult, str(n_photos_file)))
            classif_writer.writerow([version_uuid, user_id, observation_date, type, has_note, quality_adult, str(n_photos_file), location_choice])

do_work()