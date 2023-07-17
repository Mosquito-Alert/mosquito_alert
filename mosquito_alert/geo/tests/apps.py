from django.apps import AppConfig


class GeoTestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.geo.tests"
    label = "geo_tests"
