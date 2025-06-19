from dataclasses import dataclass

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
    annotation: AnnotationPermission
    identification_task: IdentificationTaskPermission
    review: ReviewPermission