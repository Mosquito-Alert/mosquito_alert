from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from django.db import models

class Role(models.TextChoices):
    BASE = 'base'
    ANNOTATOR = 'annotator'
    SUPERVISOR = 'supervisor'
    REVIEWER = 'reviewer'
    ADMIN = 'admin'

@dataclass
class BasePermission:
    add: bool = False
    change: bool = False
    view: bool = False
    delete: bool = False

@dataclass
class IdentificationTaskPermission(BasePermission):
    pass

@dataclass
class AnnotationPermission(BasePermission):
    mark_as_decisive: bool = False
    pass

@dataclass
class ReviewPermission(BasePermission):
    pass

@dataclass
class Permissions:
    annotation: AnnotationPermission = AnnotationPermission()
    identification_task: IdentificationTaskPermission = IdentificationTaskPermission()
    review: ReviewPermission = ReviewPermission()

class UserRolePermissionMixin:
    @abstractmethod
    def get_countries_with_roles(self) -> List['tigaserver_app.EuropeCountry']:
        raise NotImplementedError

    def get_countries_with_permissions(self, action, model) -> List['tigaserver_app.EuropeCountry']:
        countries = []
        for country in self.get_countries_with_roles():
            if self.has_role_permission_by_model(action=action, model=model, country=country):
                countries.append(country)
        return countries

    @abstractmethod
    def get_role(self, country: Optional['tigaserver_app.EuropeCountry'] = None) -> Role:
        raise NotImplementedError

    def get_role_permissions(self, role: Role) -> Permissions:
        return Permissions(
            annotation=self.get_role_annotation_permission(role),
            identification_task=self.get_role_identification_task_permission(role),
            review=self.get_role_review_permission(role)
        )

    def get_role_annotation_permission(self, role: Role) -> AnnotationPermission:
        return AnnotationPermission(
            add=role in [Role.ANNOTATOR, Role.SUPERVISOR, Role.REVIEWER, Role.ADMIN],
            mark_as_decisive=role in [Role.SUPERVISOR, Role.ADMIN],
            change=role in [Role.ADMIN],
            view=role in [Role.ANNOTATOR, Role.SUPERVISOR, Role.REVIEWER, Role.ADMIN],
            delete=role in [Role.ADMIN],
        )

    def get_role_identification_task_permission(self, role: Role) -> IdentificationTaskPermission:
        return IdentificationTaskPermission(
            add=False,
            change=role in [Role.ADMIN],
            view=role in [Role.SUPERVISOR, Role.REVIEWER, Role.ADMIN],
            delete=role in [Role.ADMIN],
        )

    def get_role_review_permission(self, role: Role) -> ReviewPermission:
        return ReviewPermission(
            add=role in [Role.REVIEWER, Role.ADMIN],
            change=role in [Role.ADMIN],
            view=role in [Role.REVIEWER, Role.ADMIN],
            delete=role in [Role.ADMIN],
        )

    def _get_role_permission_by_model(self, model, country: Optional['tigaserver_app.EuropeCountry'] = None) -> BasePermission:
        from tigacrafting.models import ExpertReportAnnotation, IdentificationTask
        if model == IdentificationTask:
            return self.get_role_identification_task_permission(role=self.get_role(country=country))
        elif model == ExpertReportAnnotation:
            return self.get_role_annotation_permission(role=self.get_role(country=country))

        return BasePermission(
            add=False,
            view=False,
            change=False,
            delete=False
        )

    def has_role_permission_by_model(self, action, model, country: Optional['tigaserver_app.EuropeCountry'] = None) -> BasePermission:
        permission = self._get_role_permission_by_model(model=model, country=country)
        return getattr(permission, action, False)

    def has_role_permission(self, action, obj_or_klass, *args, **kwargs) -> bool:
        if isinstance(obj_or_klass, type):
            model = obj_or_klass
            countries = [None,] + self.get_countries_with_roles()
        else:
            model = obj_or_klass.__class__
            countries = [obj_or_klass.country]

        for country in countries:
            if self.has_role_permission_by_model(action=action, model=model, country=country):
                return True
        return False