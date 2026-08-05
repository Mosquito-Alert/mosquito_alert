# serializers/__init__.py

from .base_serializers import FieldPolymorphicSerializer, LocalizedModelSerializerMixin
from .boundaries import TemporaryBoundarySerializer
from .campaigns import CampaignSerializer
from .countries import CountrySerializer
from .devices import DeviceSerializer, DeviceUpdateSerializer
from .fixes import FixSerializer, FixLocationSerializer
from .identification_tasks import (
    CreatePhotoPredictionSerializer,
    PhotoPredictionSerializer,
)
from .messages import (
    AudienceFilterSerializer,
    CreateMessageSerializer,
    CreateAudienceMessageSerializer,
    CreateUserMessageSerializer,
    MessageRecipientSerializer,
    MessageSerializer,
    MessageTargetingSerializer,
)
from .notifications import NotificationSerializer
from .partners import PartnerSerializer
from .permissions import (
    BaseCRUDPermissionSerializer,
    PermissionsSerializer,
)
from .photos import PhotoSerializer, SimplePhotoSerializer
from .reports import (
    BaseReportSerializer,
    BaseReportGeoModelSerializer,
    BaseSimplifiedReportSerializer,
    BaseReportWithPhotosSerializer,
    BaseSimplifiedReportSerializerWithPhoto,
    SimplifiedObservationSerializer,
    SimplifiedObservationWithPhotosSerializer,
    SimpleAnnotatorUserSerializer,
    SpeciesIdentificationSerializer,
    AnnotationSerializer,
    BaseAssignmentSerializer,
    AssignmentSerializer,
    IdentificationTaskSerializer,
    CreateReviewSerializer,
    CreateAgreeReviewSerializer,
    CreateOverwriteReviewSerializer,
    ObservationGeoModelSerializer,
    ObservationGeoJsonModelSerializer,
    ObservationSerializer,
    BiteGeoModelSerializer,
    BiteGeoJsonModelSerializer,
    BiteSerializer,
    BreedingSiteSerializer,
    BreedingSiteGeoModelSerializer,
    BreedingSiteGeoJsonModelSerializer,
)
from .taxa import SimpleTaxonSerializer, TaxonSerializer, TaxonTreeNodeSerializer
from .users import (
    UserSerializer,
    SimpleUserSerializer,
    MinimalUserSerializer,
)
from .workspaces import (
    WorkspaceSerializer,
    SimpleWorkspaceSerializer,
    WorkspaceCollaborationGroupSerializer,
)

__all__ = [
    "FieldPolymorphicSerializer",
    "LocalizedModelSerializerMixin",
    "TemporaryBoundarySerializer",
    "CampaignSerializer",
    "CountrySerializer",
    "DeviceSerializer",
    "DeviceUpdateSerializer",
    "FixSerializer",
    "FixLocationSerializer",
    "CreatePhotoPredictionSerializer",
    "PhotoPredictionSerializer",
    "AudienceFilterSerializer",
    "CreateMessageSerializer",
    "CreateAudienceMessageSerializer",
    "CreateUserMessageSerializer",
    "MessageRecipientSerializer",
    "MessageSerializer",
    "MessageTargetingSerializer",
    "NotificationSerializer",
    "PartnerSerializer",
    "BaseCRUDPermissionSerializer",
    "PermissionsSerializer",
    "PhotoSerializer",
    "SimplePhotoSerializer",
    "BaseReportSerializer",
    "BaseReportGeoModelSerializer",
    "BaseSimplifiedReportSerializer",
    "BaseReportWithPhotosSerializer",
    "BaseSimplifiedReportSerializerWithPhoto",
    "SimplifiedObservationSerializer",
    "SimplifiedObservationWithPhotosSerializer",
    "SimpleAnnotatorUserSerializer",
    "SpeciesIdentificationSerializer",
    "AnnotationSerializer",
    "BaseAssignmentSerializer",
    "AssignmentSerializer",
    "IdentificationTaskSerializer",
    "CreateReviewSerializer",
    "CreateAgreeReviewSerializer",
    "CreateOverwriteReviewSerializer",
    "ObservationGeoModelSerializer",
    "ObservationGeoJsonModelSerializer",
    "ObservationSerializer",
    "BiteGeoModelSerializer",
    "BiteGeoJsonModelSerializer",
    "BiteSerializer",
    "BreedingSiteSerializer",
    "BreedingSiteGeoModelSerializer",
    "BreedingSiteGeoJsonModelSerializer",
    "SimpleTaxonSerializer",
    "TaxonSerializer",
    "TaxonTreeNodeSerializer",
    "UserSerializer",
    "SimpleUserSerializer",
    "MinimalUserSerializer",
    "WorkspaceSerializer",
    "SimpleWorkspaceSerializer",
    "WorkspaceCollaborationGroupSerializer",
]
