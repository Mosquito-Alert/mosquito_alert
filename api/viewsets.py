from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import GenericViewSet as DRFGenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework_nested.viewsets import NestedViewSetMixin as OriginalNestedViewSetMixin, _force_mutable

from .auth.authentication import AppUserJWTAuthentication, NonAppUserSessionAuthentication
from .parsers import MultiPartJsonNestedParser
from .permissions import UserObjectPermissions, IsMobileUser, DjangoRegularUserModelPermissions


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
    parser_classes = (JSONParser, FormParser, MultiPartJsonNestedParser)
    renderer_classes = (JSONRenderer,)


class GenericMobileOnlyViewSet(GenericViewSet):
    permission_classes = (IsMobileUser, ) + GenericViewSet.permission_classes

class GenericNoMobileViewSet(GenericViewSet):
    permission_classes = (DjangoRegularUserModelPermissions, )

class NestedViewSetMixin(OriginalNestedViewSetMixin):
    def initialize_request(self, request, *args, **kwargs):
        """
        Adds the parent params from URL inside the children data available
        """
        drf_request = super(DRFGenericViewSet, self).initialize_request(request, *args, **kwargs)  # type: ignore[misc]

        # NOTE: only added this. Can not upgrade to 0.93.5 due to conflict in requirements versions.
        # See: https://github.com/alanjds/drf-nested-routers/commit/a217c14b3aefe4cd22ed08ae369b766dbca2c99b
        if getattr(self, 'swagger_fake_view', False):
            return drf_request

        for url_kwarg, fk_filter in self._get_parent_lookup_kwargs().items():
            # fk_filter is alike 'grandparent__parent__pk'
            parent_arg = fk_filter.partition('__')[0]
            for querydict in [drf_request.data, drf_request.query_params]:
                with _force_mutable(querydict):
                    querydict[parent_arg] = kwargs[url_kwarg]
        return drf_request