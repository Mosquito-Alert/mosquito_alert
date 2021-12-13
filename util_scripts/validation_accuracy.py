import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.contrib.auth.models import User
from tigaserver_app.models import ExpertReportAnnotation, Report
import json
import datetime
from datetime import timedelta, datetime
import time
from tzlocal import get_localzone
from progress.bar import Bar
from django.utils.timezone import localtime, now
from django.db.models import Max, F, Q


def adapt_old_category(tiger_certainty_category):
    if tiger_certainty_category == 0:
        return {'category': 9, 'value': None}
    elif tiger_certainty_category == 1: # Probably tiger
        return {'category': 4, 'value': 1}
    elif tiger_certainty_category == 2: # Certainly tiger
        return {'category': 4, 'value': 2}
    elif tiger_certainty_category == -1:  # Not tiger
        return {'category': 2, 'value': None}
    elif tiger_certainty_category == -2:  # Also not tiger, even less so
        return {'category': 2, 'value': None}
    else:
        raise Exception("Unknown value for old category {0}".format( tiger_certainty_category ))


def is_conflict(validation_data):
    try:
        class_label = validation_data['class_label']
        if class_label == 'conflict':
            return True
    except KeyError:
        pass
    return False


def init_report_movelab_annotation_cache():
    reports = Report.objects.filter(type='adult').order_by('server_upload_time')
    bar = Bar('Crunching reports', max=reports.count())
    for r in reports:
        movelab_annotation_euro = r.get_movelab_annotation_euro()
        if movelab_annotation_euro is not None:
            r.cached_movelab_annotation_euro = json.dumps(movelab_annotation_euro)
        else:
            r.cached_movelab_annotation_euro = None
        r.cached_movelab_annotation_euro_last_update = localtime(now()).date()
        r.save()
        bar.next()
    bar.finish()


def compute_accuracy_in_period( period_reports, expert_validation_data ):
    hard_same = 0
    soft_same = 0
    total = 0
    for r in period_reports:
        if r.cached_movelab_annotation_euro is None:
            final_validation = None
        else:
            final_validation = json.loads(r.cached_movelab_annotation_euro)
        if final_validation:
            if not is_conflict(final_validation):
                try:
                    final_validation_class = final_validation['class_id']
                    final_validation_value = final_validation['class_value']
                except KeyError:
                    try:
                        old_validation = final_validation['tiger_certainty_category']
                        data = adapt_old_category(old_validation)
                        final_validation_class = data['category']
                        final_validation_value = data['value']
                    except KeyError:
                        print("Another key error")
                expert_validation = expert_validation_data[r.version_UUID]
                if expert_validation['category_id'] == 8:  # complex
                    expert_validation_class = expert_validation['complex_id']
                else:
                    expert_validation_class = expert_validation['category_id']
                expert_validation_value = expert_validation['validation_value']
                if expert_validation_class == final_validation_class:
                    soft_same += 1
                    if expert_validation_value == final_validation_value:
                        hard_same += 1
                total += 1
    return {'hard_hit': hard_same, 'soft_hit': soft_same, 'total': total}


def get_accuracy_data_per_period(expert_validations, expert_validation_data):
    tz = get_localzone()
    ref_date = datetime(2014, 1, 1, 0, 0, 0, tzinfo=tz)
    end_date = tz.localize(datetime.now())
    accuracy_periods = []
    while ref_date <= end_date:
        bucket = time.mktime(ref_date.timetuple()) * 1000
        #validations_in_bucket = expert_validations.filter(last_modified__year__lte=ref_date.year).filter(last_modified__month__lte=ref_date.month).filter(last_modified__day__lte=ref_date.day).values('report').distinct()
        validations_in_bucket = expert_validations.filter(last_modified__lte=ref_date).values('report').distinct()
        reports_in_bucket = Report.objects.filter(version_UUID__in=validations_in_bucket).filter(type='adult')
        data_bucket = compute_accuracy_in_period( reports_in_bucket, expert_validation_data )
        accuracy_periods.append([bucket, data_bucket])
        ref_date += timedelta(hours=24)
    return accuracy_periods

def update_cached_euro_annotations():
    #reports that need updating
    reports_to_update = Report.objects.filter(type='adult').annotate(latest_expert_anno=Max('expert_report_annotations__last_modified')).filter( Q(latest_expert_anno__gt=F('cached_movelab_annotation_euro_last_update')) | Q(cached_movelab_annotation_euro_last_update__isnull=True) )
    bar = Bar('Updating report classification cache', max=reports_to_update.count())
    for r in reports_to_update:
        euro_movelab_annotation = r.get_movelab_annotation_euro()
        if euro_movelab_annotation is not None:
            r.cached_movelab_annotation_euro = json.dumps(euro_movelab_annotation)
        else:
            r.cached_movelab_annotation_euro = None
        r.cached_movelab_annotation_euro_last_update = localtime(now()).date()
        r.save()
        bar.next()
    bar.finish()


def update_expert_accuracy(expert_id):
    expert = User.objects.get(pk=expert_id)
    validations_expert = ExpertReportAnnotation.objects.filter(user=expert).filter(validation_complete=True)
    reports_expert = validations_expert.values('report').distinct()
    reports_expert_qs = Report.objects.filter(version_UUID__in=reports_expert).filter(type='adult')
    validation_data = {}
    bar = Bar('Caching validation data', max=validations_expert.count())
    for v in validations_expert:
        validation_data[v.report.version_UUID] = {'category_id': v.category_id, 'complex_id': v.complex_id, 'validation_value': v.validation_value}
        bar.next()
    bar.finish()

    hard_same = 0
    soft_same = 0
    total = 0
    bar = Bar('Generating report stats', max=reports_expert_qs.count())
    for r in reports_expert_qs:
        #final_validation = r.get_movelab_annotation_euro()
        if r.cached_movelab_annotation_euro is None:
            final_validation = None
        else:
            final_validation = json.loads(r.cached_movelab_annotation_euro)
        if final_validation:
            if not is_conflict(final_validation):
                try:
                    final_validation_class = final_validation['class_id']
                    final_validation_value = final_validation['class_value']
                except KeyError:
                    try:
                        old_validation = final_validation['tiger_certainty_category']
                        data = adapt_old_category(old_validation)
                        final_validation_class = data['category']
                        final_validation_value = data['value']
                    except KeyError:
                        print("Another key error")
                expert_validation = validation_data[r.version_UUID]
                if expert_validation['category_id'] == 8: #complex
                    expert_validation_class = expert_validation['complex_id']
                else:
                    expert_validation_class = expert_validation['category_id']
                expert_validation_value = expert_validation['validation_value']
                if expert_validation_class == final_validation_class:
                    soft_same +=1
                    if expert_validation_value == final_validation_value:
                        hard_same += 1
                total += 1
        bar.next()
    bar.finish()

    accuracy_periods = get_accuracy_data_per_period( validations_expert, validation_data )

    # print("Expert {0}".format( expert.username ))
    # if total == 0:
    #     print("No activity")
    # else:
    #     print("Class and value identical {0}, Different {1}, Total {2}".format(hard_same, total - hard_same, total))
    #     print("Class identical {0}, Different {1}, Total {2}".format(soft_same, total - soft_same, total))
    #     print("Hard accuracy {0}, Fail {1}".format(hard_same / total * 100, (total - hard_same) / total * 100))
    #     print("Soft accuracy {0}, Fail {1}".format(soft_same / total * 100, (total - soft_same) / total * 100))
    data = {'hard_hit': hard_same, 'soft_hit': soft_same, 'total': total, 'accuracy_periods': accuracy_periods}
    expert.userstat.accuracy_stats = json.dumps(data)
    expert.userstat.accuracy_last_update = localtime(now()).date()
    expert.userstat.save()

experts = User.objects.filter(groups__name='expert').exclude(id__in=[152, 151, 150])
update_cached_euro_annotations()
for expert in experts:
    print("Updating expert {0} ...".format(expert.username))
    update_expert_accuracy(expert.id)
    print("Done!")
    print("\n")
# init_report_movelab_annotation_cache()
