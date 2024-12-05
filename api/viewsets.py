from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.viewsets import GenericViewSet as DRFGenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer


from .auth.authentication import AppUserJWTAuthentication
from .permissions import UserObjectPermissions


class ResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class GenericViewSet(DRFGenericViewSet):

    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
        AppUserJWTAuthentication,
    )
    _pagination_class = ResultsSetPagination

    @property
    def pagination_class(self):
        return self._pagination_class

    permission_classes = (UserObjectPermissions,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    renderer_classes = (JSONRenderer,)


class GenericMobileOnlyViewSet(GenericViewSet):
    authentication_classes = (
        AppUserJWTAuthentication,
    )

class GenericNoMobileViewSet(GenericViewSet):
    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
    )
    permission_classes = (permissions.DjangoModelPermissions,)
