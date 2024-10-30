import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from tigaserver_app.models import Report, Photo
from django.db import connection
import csv
from progress.bar import Bar


def main():
    cursor = connection.cursor()
    sql = """
    select foo.best_photo_id from (
    select distinct an.best_photo_id, count(an.report_id) 
    from tigacrafting_expertreportannotation an, tigaserver_app_report tar 
    where an.report_id = tar."version_UUID" and tar."type" = 'adult'
    group by an.best_photo_id having count(an.report_id) = 1
    ) as foo
    """
    results = cursor.execute(sql)
    data = cursor.fetchall()
    data_array = [d[0] for d in data]
    photos = Photo.objects.filter(id__in=data_array)
    bar = Bar('listing photos...', max=photos.count())
    with open('/tmp/photo_data_summer_2022.csv', mode='w') as photo_data:
        photo_data_writer = csv.writer(photo_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        photo_data_writer.writerow( ['photo_uuid', 'photo_url', 'report_classification', 'report_uuid', 'report_creation_time'] )
        for p in photos:
            if not p.hide:
                report = p.report
                if report.creation_time.year == 2022 and report.creation_time.month == 9:
                    if not report.hide:
                        #report.get_final_combined_expert_category_euro_struct()
                        # print("{} {} {} {} {}".format( str(p.uuid), str(p.photo), report.get_final_combined_expert_category_euro(), report.version_UUID, report.creation_time ))
                        photo_data_writer.writerow([str(p.uuid), p.photo.url, report.get_final_combined_expert_category_euro(), report.version_UUID, report.creation_time])
                        bar.next()
    bar.finish()

if __name__ == '__main__':
    main()

