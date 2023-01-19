import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from tigaserver_app.models import *
from datetime import date
import csv

def get_daily_data():
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    csv_columns = ["user_UUID","registration_time"]
    with open("register_data_tigausers.csv", 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in real_tigausers:
            row_data = {"user_UUID": data.user_UUID,"registration_time":data.registration_time}
            writer.writerow(row_data)


get_daily_data()