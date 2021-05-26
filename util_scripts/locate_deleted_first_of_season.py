import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report, Award, Notification, NotificationContent, grant_first_of_season, get_translation_in
from django.db.models import Q
from django.contrib.auth.models import User, Group

reports = Report.objects.all()
super_movelab = User.objects.get(pk=24)

'''
for r in reports:
    if Award.objects.filter(report=r).filter(category__category_label='start_of_season').exists():
        if r.deleted:
            print("Deleted report {0} has been granted first_of_season".format(r.version_UUID))
'''

for r in reports:
    if Award.objects.filter(report=r).filter(category__category_label='start_of_season').exists():
        if r.deleted:
            print("Deleted report {0} has been granted first_of_season".format(r.version_UUID))
            deleted_versions = Report.objects.filter(report_id=r.report_id).filter(user_id=r.user.user_UUID).values('version_UUID')
            first_of_season_to_deleted_report = Award.objects.filter(report__report_id=r.report_id).filter(given_to=r.user).filter(category__category_label='start_of_season')
            current_year = r.creation_time.year
            if first_of_season_to_deleted_report.exists():
                award = first_of_season_to_deleted_report.first()
                award.delete()
                # recover all reports before this one
                posterior_reports = Report.objects.exclude(version_UUID__in=deleted_versions).filter(user_id=r.user.user_UUID).filter(Q(type='adult') | Q(type='site')).filter(creation_time__gte=r.creation_time).order_by('creation_time')
                award_relocated = False
                for r in posterior_reports:
                    if r.latest_version:
                        if r.can_be_first_of_season(current_year):
                            if not Award.objects.filter(given_to=r.user).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season').exists():
                                grant_first_of_season(r, super_movelab)
                                award_relocated = True
                                # update notification
                                start_of_season_en_text = get_translation_in('start_of_season', 'en')
                                n = Notification.objects.filter(report__in=deleted_versions).filter(
                                    notification_content__body_html_en__icontains=start_of_season_en_text).first()
                                if n is not None:
                                    n.report = r
                                    n.save()
                                break
                if award_relocated == False:
                    start_of_season_en_text = get_translation_in('start_of_season', 'en')
                    n = Notification.objects.filter(report=r).filter(notification_content__body_html_en__icontains=start_of_season_en_text).first()
                    nc = None
                    if n is not None:
                        nc = n.notification_content
                        n.delete()
                        if nc is not None:
                            nc.delete()
