import json

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.gis.geos import GEOSGeometry


class DjangoGEOJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, GEOSGeometry):
            return json.loads(obj.geojson)
        return super().default(obj)


class DjangoGEOJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("object_hook", self._object_hook)
        super().__init__(*args, **kwargs)

    def _object_hook(self, obj):
        if "type" in obj and "coordinates" in obj:
            try:
                return GEOSGeometry(json.dumps(obj))
            except Exception:
                pass
        return obj
