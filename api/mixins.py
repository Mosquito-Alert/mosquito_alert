from typing import Optional

from rest_framework.exceptions import APIException
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from tigacrafting.models import IdentificationTask

class IdentificationTaskNestedAttribute():
    def get_parent_lookup_url_kwarg(self) -> str:
        return 'observation_uuid'

    def get_identification_task_obj(self) -> Optional[IdentificationTask]:
        if task_id := self.kwargs.get(self.get_parent_lookup_url_kwarg(), None):
            return IdentificationTask.objects.get(pk=task_id)

    def check_parent_permissions(self, request) -> bool:
        from .views import IdentificationTaskViewSet
        if self.action in ['list', 'retrieve']:
            parent_view = IdentificationTaskViewSet()
            parent_view.action = 'retrieve'
            parent_view.request = request
            parent_view.kwargs = self.kwargs

            identification_task_obj = self.get_identification_task_obj()

            try:
                parent_view.check_object_permissions(request, identification_task_obj)
            except APIException:
                pass
            else:
                return True
        return False

    def check_permissions(self, request):
        if self.check_parent_permissions(request):
            return
        # If parent permissions are not checked or failed, check the current view's permissions
        super().check_permissions(request)

    def check_object_permissions(self, request, obj):
        if self.check_parent_permissions(request):
            return
        super().check_object_permissions(request, obj)

class ReportGeoJsonModelSerializerMixin(serializers.Serializer):
    point = GeometryField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        geo_precision = request.query_params.get('geo_precision') if request else None
        if geo_precision is not None:
            self.fields['point'] = GeometryField(precision=int(geo_precision))
