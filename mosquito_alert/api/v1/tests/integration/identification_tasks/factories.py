import uuid
from typing import Optional

from django.contrib.auth.models import User, Group

from mosquito_alert.identification_tasks.models import IdentificationTask, ExpertReportAnnotation

from mosquito_alert.api.v1.tests.utils import grant_permission_to_user


def create_annotation(identification_task: IdentificationTask, user: Optional[User] = None, **kwargs) -> ExpertReportAnnotation:
    expert_group, _ = Group.objects.get_or_create(name='expert')
    if user is None:
        user = User.objects.create(
            username=str(uuid.uuid4())
        )
    user.groups.add(expert_group)

    return ExpertReportAnnotation.objects.create(
        identification_task=identification_task,
        user=user,
        **kwargs
    )

def create_review(identification_task: IdentificationTask, user: Optional[User] = None, **kwargs) -> ExpertReportAnnotation:
    if user is None:
        user = User.objects.create(
            username=str(uuid.uuid4())
        )
    grant_permission_to_user(
        codename="add_review", model_class=IdentificationTask, user=user
    )
    return ExpertReportAnnotation.objects.create(
        identification_task=identification_task,
        user=user,
        decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
        **kwargs
    )