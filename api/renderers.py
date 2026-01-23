from rest_framework.renderers import JSONRenderer

class GeoJsonRenderer(JSONRenderer):
    media_type = 'application/geo+json'
    format = 'geojson'