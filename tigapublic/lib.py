from django.http import HttpResponse
from shpformat import *
from django.db.models import Q
from operator import __or__ as OR
from constants import *


def time_filter(years, months, qs):

    if years is not None and years != 'all':
        years = years.split(',')
        years_lst = []
        for i in years:
            years_lst.append(Q(observation_date__year=str(i)))
        qs = qs.filter(reduce(OR, years_lst))


    if months is not None and months != 'all':
        months = months.split(',')
        lst = []
        for a in months:
            lst.append(Q(observation_date__month=str(a).zfill(2)))
        qs = qs.filter(reduce(OR, lst))


    return qs


def bbox_filter(bbox, qs):

    if bbox is None:
        return HttpResponse(request, status=400)

    bbox = bbox.split(',')

    if len(bbox) is not 4:
        return HttpResponse('400 Bad Request', status=400)

    southwest_lng = bbox[0]
    southwest_lat = bbox[1]
    northeast_lng = bbox[2]
    northeast_lat = bbox[3]

    qs = qs.filter(
        lon__gte=southwest_lng
    ).filter(
        lon__lte=northeast_lng
    ).filter(
        lat__gte=southwest_lat
    ).filter(
        lat__lte=northeast_lat
    )
    return qs

def category_filter(categories, qs):
    args = Q()
    if categories is not None:
        categories = categories.split(',')
        for c in categories:
            args.add(Q(private_webmap_layer__exact=c), Q.OR)

    qs = qs.filter(args)
    return qs


def apply_all_filters(request, qs):
    qs = bbox_filter(request, qs)
    qs = time_filter(request, qs)
    qs = category_filter(request, qs)
    return qs


def ValuesQuerySetToDict(vqs):
    return [item for item in vqs]

def export_stormdrain_shape(request):
    attribs = StormDrainShpAttribs
    schema = {'geometry': 'Point', 'properties': attribs}

    data = StormDrain.objects.extra(select={'lon': 'original_lon', 'lat':'original_lat'})
    data = data.filter(user_id__exact=37)
    data = data.values('municipality', 'water', 'code', 'lon','lat','date')
    result = SHPFormat(schema, 'storm_drain').export_data(data)

    response = HttpResponse(mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=mosquito_alert.zip"
    response.write(result)

    return response

def get_mapauxreports_shape( qs):
    attribs = MapAuxReportsShpAttribs
    schema = {'geometry': 'Point', 'properties': attribs}
    return SHPFormat(schema, 'observations').export_data(qs)

def get_notification_shape(request, qs):
    #Get corresponding attribs
    if request.user.groups.filter(name='supermosquito').exists():
        attribs = NotificationReportsShpAttribs
    else:
        attribs = NotificationLimitedReportsShpAttribs

    schema = {'geometry': 'Point', 'properties': attribs}
    return SHPFormat(schema, 'notifications', 'report__lon', 'report__lat').export_data(qs)
