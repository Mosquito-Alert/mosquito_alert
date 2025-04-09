import uuid
from typing import Optional

from django.contrib.auth.models import User, Group

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation


def add_annotation(identification_task: IdentificationTask, user: Optional[User] = None, **kwargs) -> ExpertReportAnnotation:
    expert_group, _ = Group.objects.get_or_create(name='expert')
    if user is None:
        user = User.objects.create(
            username=str(uuid.uuid4())
        )
    user.groups.add(expert_group)

    return ExpertReportAnnotation.objects.create(
        report=identification_task.report,
        user=user,
        validation_complete=True,
        **kwargs
    )

def add_revision(identification_task: IdentificationTask, overwrite: bool = False, user: Optional[User] = None, **kwargs) -> ExpertReportAnnotation:
    superexpert_group, _ = Group.objects.get_or_create(name='superexpert')

    if user is None:
        user = User.objects.create(
            username=str(uuid.uuid4())
        )
    user.groups.add(superexpert_group)

    return ExpertReportAnnotation.objects.create(
        report=identification_task.report,
        user=user,
        revise=overwrite,
        validation_complete=True,
        **kwargs
    )