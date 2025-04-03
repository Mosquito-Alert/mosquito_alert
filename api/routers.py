from rest_framework_nested import routers

class RouterEmptyLookupMixin:
    def get_lookup_regex(self, viewset, lookup_prefix=''):
        if lookup_prefix == '_':
            lookup_prefix = ''
        return super().get_lookup_regex(viewset, lookup_prefix)


class SimpleRouter(RouterEmptyLookupMixin,routers.SimpleRouter):
    pass

class NestedSimpleRouter(RouterEmptyLookupMixin,routers.NestedSimpleRouter):
    pass