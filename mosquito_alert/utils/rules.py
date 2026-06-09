import rules
from typing import Optional

from django.contrib.auth.backends import ModelBackend

from mosquito_alert.users.models import User

model_backend = ModelBackend()


def has_global_permission(
    klass, type: Optional[str] = None, name: Optional[str] = None
) -> bool:
    perm = "%(app_label)s.%(name)s" % {
        "app_label": klass._meta.app_label,
        "name": name or f"{type}_{klass._meta.model_name}",
    }

    @rules.predicate
    def user_has_global_permission(user: User):
        return model_backend.has_perm(user, perm)

    return user_has_global_permission
