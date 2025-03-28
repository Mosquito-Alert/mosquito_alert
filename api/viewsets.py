from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import GenericViewSet as DRFGenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer


from .auth.authentication import AppUserJWTAuthentication, NonAppUserSessionAuthentication
from .permissions import UserObjectPermissions


class ResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class GenericViewSet(DRFGenericViewSet):

    # NOTE: AppUserJWTAuthentication must be on top to return 401 with correct headers
    # See: https://www.django-rest-framework.org/api-guide/authentication/#unauthorized-and-forbidden-responses
    authentication_classes = (
        AppUserJWTAuthentication,
        TokenAuthentication,
        NonAppUserSessionAuthentication,
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
        NonAppUserSessionAuthentication,
        TokenAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)
