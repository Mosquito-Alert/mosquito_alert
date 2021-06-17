import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report, ExpertReportAnnotation
from django.db import connection
from django.db.models import Count
from progress.bar import Bar
import redis


def compute_show_on_map(report):
    if report.creation_time.year == 2014:
        return True
    else:
        return (not report.photos.all().exists()) or ((ExpertReportAnnotation.objects.filter(report=report,
                                                                                               user__groups__name='expert',
                                                                                               validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(
                report=report, user__groups__name='superexpert', validation_complete=True,
                revise=True).exists()) and report.get_final_expert_status() == 1)


def compute_latest_version(report):
    if report.version_number == -1:
        return False
    elif Report.objects.filter(report_id=report.report_id).filter(type=report.type).count() == 1:
        return True
    else:
        all_versions = Report.objects.filter(report_id=report.report_id).filter(type=report.type).order_by('version_number')
        if all_versions[0].version_number == -1:
            return False
        elif all_versions.reverse()[0].version_number == report.version_number:
            return True
        else:
            return False


def add_reports_to_redis():
    reports = Report.objects.all()
    for report in reports:
        show_on_map = compute_show_on_map(report)
        is_latest_version = compute_latest_version(report)
        r = redis.Redis()
        show_on_map_str = "0" if not show_on_map else "1"
        latest_str = "0" if not is_latest_version else "1"
        print("adding report {0}, visible {1}, latest {2}".format(report.version_UUID, show_on_map_str, latest_str))
        r.hset(report.version_UUID,"show_on_map", show_on_map_str)
        r.hset(report.version_UUID, "latest", latest_str)

    # qs = Report.objects.exclude(point__isnull=True).exclude(creation_time__year=2014)
    # radius = 5000
    # cursor = connection.cursor()
    # sql = "SELECT \"version_UUID\"  " + \
    #       "FROM tigaserver_app_report where st_distance(point::geography, 'SRID=4326;POINT({0} {1})'::geography) <= {2} " + \
    #       "ORDER BY point <-> 'SRID=4326;POINT({3} {4})'"
    # bar = Bar('Computing', max=qs.count())
    # r = redis.Redis()
    # with r.pipeline() as pipe:
    #     for report in qs:
    #         center_buffer_lon = report.point.x
    #         center_buffer_lat = report.point.y
    #         sql_formatted = sql.format(center_buffer_lon, center_buffer_lat, radius, center_buffer_lon,
    #                                    center_buffer_lat)
    #         cursor.execute(sql_formatted)
    #         data = cursor.fetchall()
    #         flattened_data = [element for tupl in data for element in tupl]
    #
    #         nearby_reports = Report.objects.exclude(cached_visible=0) \
    #             .filter(version_UUID__in=flattened_data) \
    #             .exclude(creation_time__year=2014) \
    #             .exclude(note__icontains="#345") \
    #             .exclude(hide=True) \
    #             .exclude(photos__isnull=True) \
    #             .filter(type='adult') \
    #             .annotate(n_annotations=Count('expert_report_annotations')) \
    #             .filter(n_annotations__gte=3)
    #
    #         uuids = [report.version_UUID for report in nearby_reports]
    #         pipe.rpush(report.version_UUID, uuids)
    #         bar.next()
    #     pipe.execute()
    # bar.finish()


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
