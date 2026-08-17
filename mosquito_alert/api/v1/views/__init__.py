# views/__init__.py

from .boundaries import BoundaryViewSet
from .campaigns import CampaignsViewSet
from .countries import CountriesViewSet
from .devices import DeviceViewSet
from .fixes import FixViewSet
from .identification_tasks import (
    MyAnnotationViewSet,
    IdentificationTaskViewSet,
    MyIdentificationTaskViewSet,
)
from .messages import MessageViewSet, MySentMessageViewSet
from .notifications import NotificationViewSet, MyNotificationViewSet
from .partners import PartnersViewSet
from .permissions import MyPermissionViewSet
from .photos import PhotoViewSet
from .ping import ping
from .reports import (
    BiteViewSet,
    MyBiteViewSet,
    BreedingSiteViewSet,
    MyBreedingSiteViewSet,
    ObservationViewSet,
    MyObservationViewSet,
)
from .taxa import TaxaViewSet
from .users import UserViewSet, MyUserViewSet
from .workspaces import (
    WorkspaceViewSet,
    MyWorkspaceViewSet,
    WorkspaceCollaboratoratorViewSet,
    MyWorkspaceCollaboratoratorViewSet,
)

__all__ = [
    ping,
    UserViewSet,
    MyUserViewSet,
    MyPermissionViewSet,
    FixViewSet,
    CampaignsViewSet,
    PartnersViewSet,
    CountriesViewSet,
    NotificationViewSet,
    MyNotificationViewSet,
    PhotoViewSet,
    ObservationViewSet,
    MyObservationViewSet,
    BiteViewSet,
    MyBiteViewSet,
    BreedingSiteViewSet,
    MyBreedingSiteViewSet,
    DeviceViewSet,
    MyAnnotationViewSet,
    IdentificationTaskViewSet,
    MyIdentificationTaskViewSet,
    TaxaViewSet,
    BoundaryViewSet,
    MessageViewSet,
    MySentMessageViewSet,
    WorkspaceViewSet,
    MyWorkspaceViewSet,
    WorkspaceCollaboratoratorViewSet,
    MyWorkspaceCollaboratoratorViewSet,
]
