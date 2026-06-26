from typing import Optional

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework_gis.fields import GeometryField

from mosquito_alert.identification_tasks.models import IdentificationTask


class IdentificationTaskNestedAttribute:
    def get_parent_lookup_url_kwarg(self) -> str:
        return "observation_uuid"

    def get_identification_task_obj(self) -> Optional[IdentificationTask]:
        if task_id := self.kwargs.get(self.get_parent_lookup_url_kwarg(), None):
            return get_object_or_404(IdentificationTask, pk=task_id)

    def check_permissions(self, request):
        if request.method == "GET":
            # If user can see identification task, can also see their nested attributes.
            can_view_identification_task = request.user.has_perm(
                "%(app_label)s.view_%(model_name)s"
                % {
                    "app_label": IdentificationTask._meta.app_label,
                    "model_name": IdentificationTask._meta.model_name,
                },
                self.get_identification_task_obj(),
            )
            if can_view_identification_task:
                return

        # If parent permissions are not checked or failed, check the current view's permissions
        super().check_permissions(request)


class ReportGeoJsonModelSerializerMixin(serializers.Serializer):
    point = GeometryField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        geo_precision = request.query_params.get("geo_precision") if request else None
        if geo_precision is not None:
            self.fields["point"] = GeometryField(precision=int(geo_precision))
