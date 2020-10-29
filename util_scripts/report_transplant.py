import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import ExpertReportAnnotation, Categories
from tigaserver_app.models import Report
import json

# ./manage.py dumpdata tigaserver_app.Report > all_reports.json
# ./manage.py dumpdata tigaserver_app.ReportResponse > all_reportresponses.json
# ./manage.py dumpdata tigacrafting.ExpertReportAnnotation > all_expertreportannotation.json
# ./manage.py dumpdata tigaserver_app.Photo > all_photos.json

IMAGINARY_USER_UUID = '15dde966-19ca-11eb-bc13-c85b76d93ea4'

def read_json_file_and_write_filtered(origin_file, destiny_file, filter_function,filter_list,substitution_function):
    f = open(origin_file, "r")
    file = f.read()
    json_file = json.loads(file)
    filtered_elems = []
    for elem in json_file:
        if filter_function(elem,filter_list) == True:
            subst_elem = substitution_function(elem)
            filtered_elems.append(subst_elem)
    filtered_string = json.dumps(filtered_elems)
    f = open(destiny_file, "w")
    f.write(filtered_string)
    f.close()


def report_filter_element_in_list(elem,list):
    if elem['pk'] in list:
        return True
    return False


def response_filter_element_in_list(elem,list):
    if elem['fields']['report'] in list:
        return True
    return False


def report_replacer(elem):
    elem['fields']['user'] = IMAGINARY_USER_UUID
    return elem


def null_replacer(elem):
    return elem


def photo_compress_generator(photos_file, out_file):
    f = open(photos_file, "r")
    file = f.read()
    json_file = json.loads(file)
    command_line = "tar zcvf photos.tar.gz "
    photo_list = ""
    for elem in json_file:
        photo_list += elem['fields']['photo'].replace("tigapics/","") + " "
    command_line += photo_list
    f = open(out_file, "w")
    f.write(command_line)
    f.close()


def report_links_generator(report_file, out_file):
    f = open(report_file, "r")
    file = f.read()
    json_file = json.loads(file)
    fo = open(out_file, "w")
    for elem in json_file:
        fo.write("http://madev.creaf.cat/en/experts/status/reports/?version_uuid=" + elem['pk'] + "\n")
    fo.close()
    f.close()


def get_uuid_of_all_production_reports():
    f = open("all_production_reports.json", "r")
    file = f.read()
    json_file = json.loads(file)
    f.close()
    uuids = []
    for elem in json_file:
        uuids.append(elem['pk'])
    return uuids;


def generate_dump_files(country_id, report_type, reports_in_production):
    target_reports = Report.objects.filter(country_id=country_id).filter(creation_time__year=2020).filter(type=report_type).exclude(photos__isnull=True).exclude(version_UUID__in=reports_in_production)
    target_reports_uuid = target_reports.values("version_UUID")
    uuids = [r_v['version_UUID'] for r_v in target_reports_uuid]

    out_reports = "some_" + report_type + "_reports_" + str(country_id) + ".json"
    out_reportresponses = "some_" + report_type + "_reportresponses_" + str(country_id) + ".json"
    if report_type == 'adult':
        out_expertreportannotations = "some_" + report_type + "_expertreportannotation_" + str(country_id) + ".json"
    out_photos = "some_" + report_type + "_photos_" + str(country_id) + ".json"
    out_photo_script = "some_" + report_type + "_photos_" + str(country_id) + ".script"
    out_links_file = "some_" + report_type + "_links_" + str(country_id) + ".txt"

    read_json_file_and_write_filtered("all_reports.json", out_reports, report_filter_element_in_list, uuids, report_replacer)
    read_json_file_and_write_filtered("all_reportresponses.json", out_reportresponses, response_filter_element_in_list, uuids, null_replacer)
    if report_type == 'adult':
        read_json_file_and_write_filtered("all_expertreportannotation.json", out_expertreportannotations, response_filter_element_in_list, uuids, null_replacer)
    read_json_file_and_write_filtered("all_photos.json", out_photos, response_filter_element_in_list, uuids, null_replacer)
    photo_compress_generator(out_photos, out_photo_script)
    report_links_generator(out_reports,out_links_file)


def work():
    country_ids = [32]
    for id in country_ids:
        reports_already_in_production = get_uuid_of_all_production_reports()
        generate_dump_files(id, 'adult', reports_already_in_production)
        generate_dump_files(id, 'site', reports_already_in_production)


# do some work
work()