# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from datetime import datetime
# import datetime
import pytz
import logging
from django.db.models import Count
from tigaserver_app.models import Report
from django.contrib.auth.models import User
from tigacrafting.models import ExpertReportAnnotation
from tigaserver_app.models import ReportResponse
from django.db.models import Q


def load_fast_track_ids():
    try:
        with open('/home/webuser/webapps/data_preprocessing/fast_track') as f:
            content = f.readlines()
        content = [x.strip() for x in content]
    except IOError:
        return []
    return content

def auto_validate(report,dryRun,auto_validation_user):
    if dryRun:
        logging.info(
            "Dry run - Auto validating report {0}, elapsed days {1}".format(report.version_UUID, elapsed_days))
    else:
        logging.info("Auto validating report {0}, elapsed days {1}".format(report.version_UUID, elapsed_days))
    if not dryRun:
        photo = report.photos.first()
        new_annotation = ExpertReportAnnotation(report=report, user=auto_validation_user)
        new_annotation.site_certainty_notes = 'auto'
        new_annotation.best_photo_id = photo.id
        new_annotation.validation_complete = True
        new_annotation.revise = True
        new_annotation.save()

# validation user is super_movelab
args = sys.argv
dryRun = False
if len(args) > 1 and args[1] == 'dryrun':
    dryRun = True
auto_validation_user = User.objects.get(pk=24)
# we use datetimes with time zone info
now = datetime.utcnow().replace(tzinfo=pytz.utc)
logname = "/home/webuser/webapps/data_preprocessing/auto-validation-" + now.strftime("%d-%m-%Y") + ".log"
logging.basicConfig(filename=logname, level=logging.INFO)


reports_imbornal = Report.objects.filter(breeding_site_type=Report.BREEDING_SITE_TYPE_STORM_DRAIN, type=Report.TYPE_SITE)

new_reports_unfiltered_sites_embornal = reports_imbornal.exclude(note__icontains='#345').exclude(photos=None).exclude(hide=True).annotate(
    n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')

new_reports_unfiltered_sites_embornal = Report.objects.exclude(type='adult').filter(
    version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).exclude(hide=True).annotate(
    n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')

new_reports_unfiltered_sites_other = Report.objects.exclude(type='adult').exclude(
    version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).exclude(hide=True).annotate(
    n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')


new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other

new_reports_unfiltered_sites = new_reports_unfiltered_sites.exclude(version_number=-1)

fast_track = load_fast_track_ids()

if len(list(new_reports_unfiltered_sites)) == 0:
    logging.info("No site reports to validate")

for report in new_reports_unfiltered_sites:
    # we use datetimes with time zone info
    report_time = report.server_upload_time
    elapsed_seconds = (now - report_time).total_seconds()
    elapsed_minutes = elapsed_seconds / 60.0
    elapsed_hours = elapsed_minutes / 60
    elapsed_days = elapsed_hours / 24.0
    if elapsed_days >= 2:
        auto_validate(report,dryRun,auto_validation_user)
    elif report.version_UUID in fast_track:
        logging.info("Auto validating " + report.version_UUID + " through fast track")
        auto_validate(report, dryRun, auto_validation_user)
    else:
        if dryRun:
            logging.info(
                "Dry run - NOT AUTO VALIDATING report {0}, elapsed days {1}".format(report.version_UUID, elapsed_days))