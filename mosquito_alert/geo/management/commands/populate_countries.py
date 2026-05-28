from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon

from pathlib import Path

from mosquito_alert.geo.models import Country, Subregion, Continent

WORLD_GPKG = "/vsizip/" + str(
    Path(__file__).parent.parent.parent / "fixtures" / "ne_10m_admin_0_countries.zip"
)


class Command(BaseCommand):
    help = "Populate countries"

    def handle(self, *args, **options):
        # Need to clear the geom field before populating it,
        # otherwise the unique constraint on iso3_code will cause issues when trying to update the geom field for existing records
        ds = DataSource(WORLD_GPKG)
        layer = ds[0]

        for feature in layer:
            geom = feature.geom.geos if feature.geom else None

            # Convert Polygon -> MultiPolygon
            if geom and geom.geom_type == "Polygon":
                geom = MultiPolygon(geom)

            iso3 = feature.get("ISO_A3_EH")
            if iso3 == "-99":
                iso3 = feature.get("ADM0_A3")

            subregion, _ = Subregion.objects.get_or_create(
                name=feature.get("SUBREGION"),
                continent=Continent.get_by_most_similar_name(feature.get("CONTINENT")),
            )

            Country.objects.update_or_create(
                iso3_code=iso3,
                defaults={
                    "subregion": subregion,
                    "name_engl": feature.get("NAME_LONG"),
                    "geom": geom,
                },
            )
