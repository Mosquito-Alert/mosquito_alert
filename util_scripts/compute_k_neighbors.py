import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report
from django.db import connection
from django.db.models import Count
from progress.bar import Bar
import redis

def add_reports_to_redis():
    qs = Report.objects.exclude(point__isnull=True).exclude(creation_time__year=2014)
    radius = 5000
    cursor = connection.cursor()
    sql = "SELECT \"version_UUID\"  " + \
          "FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT({0} {1})'::geography) <= {2} " + \
          "ORDER BY point <-> 'SRID=4326;POINT({3} {4})'"
    bar = Bar('Computing', max=qs.count())
    r = redis.Redis()
    with r.pipeline() as pipe:
        for report in qs:
            center_buffer_lon = report.point.x
            center_buffer_lat = report.point.y
            sql_formatted = sql.format(center_buffer_lon, center_buffer_lat, radius, center_buffer_lon,
                                       center_buffer_lat)
            cursor.execute(sql_formatted)
            data = cursor.fetchall()
            flattened_data = [element for tupl in data for element in tupl]

            nearby_reports = Report.objects.exclude(cached_visible=0) \
                .filter(version_UUID__in=flattened_data) \
                .exclude(creation_time__year=2014) \
                .exclude(note__icontains="#345") \
                .exclude(hide=True) \
                .exclude(photos__isnull=True) \
                .filter(type='adult') \
                .annotate(n_annotations=Count('expert_report_annotations')) \
                .filter(n_annotations__gte=3)

            uuids = [report.version_UUID for report in nearby_reports]
            pipe.rpush(report.version_UUID, uuids)
            bar.next()
        pipe.execute()
    bar.finish()

def redis_test():
    r = redis.Redis()
    list = ['a','b','c','d','e','f']
    with r.pipeline() as pipe:
        pipe.rpush("1", *list)
        pipe.execute()

def main():
    #redis_test()
    add_reports_to_redis()

if __name__ == "__main__":
    main()
