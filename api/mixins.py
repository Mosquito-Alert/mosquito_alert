from typing import Optional

from tigacrafting.models import IdentificationTask

class IdentificationTaskNestedAttribute():
    def get_parent_lookup_url_kwarg(self) -> str:
        return 'observation_uuid'

    def get_identification_task_obj(self) -> Optional[IdentificationTask]:
        if task_id := self.kwargs.get(self.get_parent_lookup_url_kwarg(), None):
            return IdentificationTask.objects.get(pk=task_id)

    def get_permissions(self):
        return [
            permission(identification_task=self.get_identification_task_obj())
            for permission in self.permission_classes
        ]
