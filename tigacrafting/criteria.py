from tigaserver_app.models import Photo,Report,TigaUser

def filter_users_with_storm_drain_pictures(reports):
    reports_filtered = filter(lambda x: not x.deleted and x.latest_version and x.embornals, reports)
    return reports_filtered

def filter_users_with_pictures(reports):
    reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
    return reports_filtered

def users_with_pictures():
    return filter_reports('users_with_pictures')

def users_with_storm_drain_pictures():
    return filter_reports('users_with_storm_drain_pictures')

def filter_reports(type):
    photos = Photo.objects.filter(hide=False)
    report_ids = set(photos.values_list('report_id', flat=True))
    reports = Report.objects.filter(hide=False).filter(version_UUID__in=report_ids).filter(type='site')
    if type == 'users_with_storm_drain_pictures':
        reports_filtered = filter_users_with_storm_drain_pictures(reports)
    elif type == 'users_with_pictures':
        reports_filtered = filter_users_with_pictures(reports)
    user_ids = []
    for r in reports_filtered:
        user_ids.append(r.user_id)
    unique_user_ids = set(user_ids)
    return TigaUser.objects.filter(user_UUID__in=unique_user_ids)
    #return unique_user_ids
