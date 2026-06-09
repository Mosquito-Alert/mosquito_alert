import rules
from typing import Optional, Union

from mosquito_alert.users.models import User, TigaUser
from mosquito_alert.utils.rules import has_global_permission
from mosquito_alert.workspaces.rules import is_workspace_reviewer

from .models import Notification, NotificationTopic


@rules.predicate
def can_add_message(user: Union[User, TigaUser]):
    if isinstance(user, TigaUser):
        return False

    if is_workspace_reviewer(user=user):
        return True

    return False


@rules.predicate
def can_view_message(
    user: Union[User, TigaUser], message: Optional[Notification] = None
):
    if isinstance(user, TigaUser):
        return message.recipients.filter(user=user).exists()

    if is_workspace_reviewer(user=user):
        return True

    if message is None:
        return False

    # If is sender
    if message.expert == user:
        return True

    return False


@rules.predicate
def can_view_message_topic(
    user: Union[User, TigaUser], topic: Optional[NotificationTopic] = None
):
    if isinstance(user, TigaUser):
        return False

    return can_view_message(user=user)


rules.add_perm(
    "%(app_label)s.add_%(model_name)s"
    % {
        "app_label": Notification._meta.app_label,
        "model_name": Notification._meta.model_name,
    },
    can_add_message,
)

rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": Notification._meta.app_label,
        "model_name": Notification._meta.model_name,
    },
    can_view_message | has_global_permission(Notification, type="view"),
)

rules.add_perm(
    "%(app_label)s.view_%(model_name)s"
    % {
        "app_label": NotificationTopic._meta.app_label,
        "model_name": NotificationTopic._meta.model_name,
    },
    can_view_message_topic | has_global_permission(NotificationTopic, type="view"),
)
