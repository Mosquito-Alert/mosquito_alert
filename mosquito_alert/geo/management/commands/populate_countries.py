from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from django.db import transaction

from itertools import groupby
from pathlib import Path

from mosquito_alert.geo.models import Country, Subregion, Continent

WORLD_GPKG = "/vsizip/" + str(
    Path(__file__).parent.parent.parent / "fixtures" / "ne_10m_admin_0_countries.zip"
)


class Command(BaseCommand):
    help = "Populate countries"

    @staticmethod
    def _convert_to_multi(geom):
        if geom.geom_type == "Polygon":
            return MultiPolygon(geom)
        return geom

    @transaction.atomic
    def handle(self, *args, **options):
        # Need to clear the geom field before populating it,
        # otherwise the unique constraint on iso3_code will cause issues when trying to update the geom field for existing records
        ds = DataSource(WORLD_GPKG)
        layer = ds[0]

        orphan_features = []
        for iso2, g in groupby(
            sorted(layer, key=lambda f: f.get("ISO_A2_EH")),
            key=lambda f: f.get("ISO_A2_EH"),
        ):
            if str(iso2) == "-99":
                orphan_features = list(g)
                continue

            features = list(g)

            # Some countries have multiple features (e.g., mainland and islands)
            # we need to union them together to get the full geometry of the country
            if len(features) == 1:
                main_feature = features[0]
            else:
                main_feature = next(
                    f for f in features if f.get("ISO_A3_EH") == f.get("ADM0_A3")
                )

            other_features = list(filter(lambda f: f != main_feature, features))

            # Start with the geometry of the main feature and union it with the geometries
            # of the other features to get the full geometry of the country
            geom = main_feature.geom.geos
            for feature in other_features:
                geom = geom.union(feature.geom.geos)

            # Use the ISO_A3_EH code as the iso3 code, but if it's -99, use the ADM0_A3 code instead
            iso3 = main_feature.get("ISO_A3_EH")
            if iso3 == "-99":
                iso3 = main_feature.get("ADM0_A3")

            subregion, _ = Subregion.objects.get_or_create(
                name=main_feature.get("SUBREGION"),
                continent=Continent.get_by_most_similar_name(
                    main_feature.get("CONTINENT")
                ),
            )

            Country.objects.update_or_create(
                iso3_code=iso3,
                defaults={
                    "subregion": subregion,
                    "name_engl": main_feature.get("NAME_LONG"),
                    "wikidata_id": main_feature.get("WIKIDATAID"),
                    "geom": self._convert_to_multi(geom),
                },
            )

        # Treat now the orphan features, which are those that don't have a valid ISO_A2_EH code
        # but we can still use them to populate the database
        for orphan_feature in orphan_features:
            # Union geometry according to what ADM0_A3_ES (Spain) recognizes as the country representative geometry
            # but if it's -99, use the ADM0_A3 code instead.
            # There are island that Spain consider to be Colombia.
            # The major of these countries are disputed territories...
            country_representative_iso3 = orphan_feature.get("ADM0_A3_ES")
            if str(country_representative_iso3) == "-99":
                country_representative_iso3 = orphan_feature.get("ADM0_A3")

            subregion, _ = Subregion.objects.get_or_create(
                name=orphan_feature.get("SUBREGION"),
                continent=Continent.get_by_most_similar_name(
                    orphan_feature.get("CONTINENT")
                ),
            )

            country, created = Country.objects.get_or_create(
                iso3_code=country_representative_iso3,
                defaults={
                    "subregion": subregion,
                    "name_engl": orphan_feature.get("NAME_LONG"),
                    "wikidata_id": orphan_feature.get("WIKIDATAID"),
                    "geom": self._convert_to_multi(orphan_feature.geom.geos),
                },
            )

            # If the country already exists
            # we need to union the geometry of the orphan feature with the existing geometry of the country
            if not created:
                new_geom = country.geom.union(orphan_feature.geom.geos)

                country.geom = self._convert_to_multi(new_geom)
                country.save()
