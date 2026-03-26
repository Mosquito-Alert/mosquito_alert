# coding=utf-8
from django.shortcuts import render

from rest_framework.decorators import api_view

from mosquito_alert.tigacrafting.models import Alert
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from mosquito_alert.tigacrafting.querystring_parser import parser
import functools
import operator

from rest_framework.response import Response

from .serializers import DataTableAimalertSerializer
# -----------------------------------#


@login_required
def aimalog(request):
    return render(request, "tigacrafting/aimalog.html", {})


# used by datatables
def get_order_clause(params_dict, translation_dict=None):
    order_clause = []
    try:
        order = params_dict["order"]
        if len(order) > 0:
            for key in order:
                sort_dict = order[key]
                column_index_str = sort_dict["column"]
                if translation_dict:
                    column_name = translation_dict[
                        params_dict["columns"][int(column_index_str)]["data"]
                    ]
                else:
                    column_name = params_dict["columns"][int(column_index_str)]["data"]
                direction = sort_dict["dir"]
                if direction != "asc":
                    order_clause.append("-" + column_name)
                else:
                    order_clause.append(column_name)
    except KeyError:
        pass
    return order_clause


# used by datatables
def get_filter_clause(params_dict, fields, translation_dict=None):
    filter_clause = []
    try:
        q = params_dict["search"]["value"]
        if q != "":
            for field in fields:
                if translation_dict:
                    translated_field_name = translation_dict[field]
                    filter_clause.append(
                        Q(**{translated_field_name + "__icontains": q})
                    )
                else:
                    filter_clause.append(Q(**{field + "__icontains": q}))
    except KeyError:
        pass
    return filter_clause


def generic_datatable_list_endpoint(
    request,
    search_field_list,
    queryset,
    classSerializer,
    field_translation_dict=None,
    order_translation_dict=None,
    paginate=True,
):

    draw = -1
    start = 0

    try:
        draw = request.GET["draw"]
    except Exception:
        pass
    try:
        start = request.GET["start"]
    except Exception:
        pass

    length = 25

    get_dict = parser.parse(request.GET.urlencode())

    order_clause = get_order_clause(get_dict, order_translation_dict)
    filter_clause = get_filter_clause(
        get_dict, search_field_list, field_translation_dict
    )

    if len(filter_clause) == 0:
        queryset = queryset.order_by(*order_clause)
    else:
        queryset = queryset.order_by(*order_clause).filter(
            functools.reduce(operator.or_, filter_clause)
        )

    if paginate:
        paginator = Paginator(queryset, length)
        recordsTotal = queryset.count()
        recordsFiltered = recordsTotal
        page = int(start) / int(length) + 1
        serializer = classSerializer(paginator.page(page), many=True)

    else:
        serializer = classSerializer(queryset, many=True, context={"request": request})
        recordsTotal = queryset.count()
        recordsFiltered = recordsTotal

    return Response(
        {
            "draw": draw,
            "recordsTotal": recordsTotal,
            "recordsFiltered": recordsFiltered,
            "data": serializer.data,
        }
    )


@api_view(["GET"])
def aimalog_datatable(request):
    if request.method == "GET":
        search_field_list = (
            "xvb",
            "report_id",
            "report_datetime",
            "loc_code",
            "cat_id",
            "species",
            "certainty",
            "status",
            "hit",
            "review_species",
            "review_status",
            "review_datetime",
        )
        queryset = Alert.objects.all()
        field_translation_list = {
            "xvb": "xvb",
            "report_id": "report_id",
            "report_datetime": "report_datetime",
            "loc_code": "loc_code",
            "cat_id": "cat_id",
            "species": "species",
            "certainty": "certainty",
            "status": "status",
            "hit": "hit",
            "review_species": "review_species",
            "review_status": "review_status",
            "review_datetime": "review_datetime",
        }
        sort_translation_list = {
            "xvb": "xvb",
            "report_id": "report_id",
            "report_datetime": "report_datetime",
            "loc_code": "loc_code",
            "cat_id": "cat_id",
            "species": "species",
            "certainty": "certainty",
            "status": "status",
            "hit": "hit",
            "review_species": "review_species",
            "review_status": "review_status",
            "review_datetime": "review_datetime",
        }
        response = generic_datatable_list_endpoint(
            request,
            search_field_list,
            queryset,
            DataTableAimalertSerializer,
            field_translation_list,
            sort_translation_list,
        )
        return response
