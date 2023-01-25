import argparse
import difflib
import logging
import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import geopandas
import pandas as pd
import pycountry
import shapely
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.collections import MultiPoint, MultiPolygon
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.point import Point as GeopyPoint

from .base import BaseDataSource, DownloadableDataSource
from .utils import (
    get_biggest_polygon,
    get_country_from_iso_code,
    get_language_from_iso_code,
)

LOCATION_CATEGORY_COUNTRY = "country"  # LEVEL 0
LOCATION_CATEGORY_STATE = "state"  # LEVEL 1
LOCATION_CATEGORY_COUNTY = "county"  # LEVEL 2
LOCATION_CATEGORY_PROVINCE = "province"  # LEVEL 2
LOCATION_CATEGORY_REGION = "region"  # LEVEL 3
LOCATION_CATEGORY_VILLAGE = "village"  # LEVEL 4
LOCATION_CATEGORIES = (
    LOCATION_CATEGORY_COUNTRY,
    LOCATION_CATEGORY_STATE,
    LOCATION_CATEGORY_COUNTY,
    LOCATION_CATEGORY_PROVINCE,
    LOCATION_CATEGORY_REGION,
    LOCATION_CATEGORY_VILLAGE,
)


@dataclass
class Location:
    latitude: float
    longitude: float
    name: str
    lang: str
    category: str  # Needed for the validation to happen.
    _category: str = field(init=False, repr=False, default="baz")

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if value not in LOCATION_CATEGORIES:
            raise ValueError(f"Category must be one of {LOCATION_CATEGORIES}")
        self._category = value


class BaseBoundaryNameDataSource(BaseDataSource, ABC):
    @property
    @abstractmethod
    def LOCATION_DICT(self):
        raise NotImplementedError

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument(
            "-l", "--location_type", choices=cls.LOCATION_DICT.keys(), required=False
        )

        cls.add_custom_arguments(parser=parser)

    @classmethod
    def get_field_by_location_type(cls, value):
        cls.validate_location_type(value=value)
        return cls.LOCATION_DICT[value]

    @classmethod
    def validate_location_type(cls, value):
        if value not in cls.LOCATION_DICT.keys():
            raise ValueError(f"Location type must be one of {cls.LOCATION_DICT.keys()}")

    @abstractmethod
    def reverse(
        self, geometry, location_type, language_iso="en", exactly_one=True
    ) -> Location:
        return NotImplementedError


class NominatimDataSource(BaseBoundaryNameDataSource):

    CLI_NAME = "nominatim"

    LOCATION_DICT = {
        LOCATION_CATEGORY_COUNTRY: "country",
        LOCATION_CATEGORY_STATE: "state",
        LOCATION_CATEGORY_COUNTY: "county",
        LOCATION_CATEGORY_PROVINCE: "county",
        LOCATION_CATEGORY_VILLAGE: "village",
    }

    @classmethod
    def add_custom_arguments(cls, parser):
        pass

    def __init__(self, **kwargs) -> None:
        geolocator = Nominatim(
            user_agent="mosquito_alert_{rnd_str}".format(
                rnd_str="".join(random.choices(string.ascii_letters, k=5))
            )
        )

        self._reverse_func = RateLimiter(geolocator.reverse, min_delay_seconds=1)
        logging.debug(
            f"Set RateLimit with a min_delay of {self._reverse_func.min_delay_seconds} sec to avoid being blocked."
        )

    def reverse(self, geometry, location_type, language_iso="en", exactly_one=True):

        location_type = self.get_field_by_location_type(value=location_type)

        geometry_point = None
        if isinstance(geometry, (MultiPolygon, Polygon)):
            logging.debug("Detected geomtry as (Multi)polygon.")
            geometry_point = get_biggest_polygon(geometry).point_on_surface
        elif isinstance(geometry, (MultiPoint, Point)):
            logging.debug("Detected geomtry as (Multi)Point.")
            geometry_point = geometry
        else:
            raise ValueError("Geometry can only be (Multi)Polygon or (Multi)Point.")

        point = GeopyPoint(latitude=geometry_point.y, longitude=geometry_point.x)

        language_iso = get_language_from_iso_code(language_iso=language_iso)
        language_iso = (
            language_iso.alpha_2
            if hasattr(language_iso, "alpha_2")
            else language_iso.alpha_3
        )
        result = self._reverse_func(
            query=point,
            exactly_one=exactly_one,
            language=language_iso,
            addressdetails=True,
            namedetails=False,
        )

        if not isinstance(result, (tuple, list)):
            result = list(result)

        # Keep only those that have a field with the selected location_type
        result = list(filter(lambda x: x.raw["address"].get(location_type), result))

        if not result:
            return None

        location_results = []
        for r in result:
            logging.debug(f"Nominatim raw result {r.raw}")
            location_results.append(
                Location(
                    latitude=r.latitude,
                    longitude=r.longitude,
                    name=r.raw["address"][location_type],
                    lang=language_iso,
                    category=location_type,
                )
            )

        return location_results[0] if exactly_one else location_results


class GeonamesDataSource(BaseBoundaryNameDataSource, DownloadableDataSource):

    CLI_NAME = "geonames"

    URL = {
        "geoname": "http://download.geonames.org/export/dump/{country_iso2}.zip",
        "alternate": "http://download.geonames.org/export/dump/alternatenames/{country_iso2}.zip",
    }
    COMPRESSED_DESIRED_FILENAME = "{country_iso2}.txt"

    # Source: http://download.geonames.org/export/dump/readme.txt
    geoname_columns = {
        "geonameid": int,
        "name": str,
        "asciiname": str,
        "alternatenames": str,
        "latitude": float,
        "longitude": float,
        "featureclass": str,
        "featurecode": str,
        "countrycode": str,
        "countrycode2": str,
        "admin1code": str,
        "admin2code": str,
        "admin3code": str,
        "admin4code": str,
        "population": float,
        "elevation": float,
        "dem": float,  # dem (digital elevation model)
        "timezone": str,
        "modificationdate": str,
    }
    geoname_id_column = "geonameid"

    alternatenames_columns = {
        "alternateNameId": int,
        "geonameid": int,
        "isolanguage": str,
        "alternatename": str,
        "isPreferredName": str,
        "isShortName": str,
        "isColloquial": str,
        "isHistoric": str,
        "from": str,
        "to": str,
    }
    alternatenames_id_column = "alternateNameId"

    # See: http://www.geonames.org/export/codes.html
    LOCATION_DICT = {
        LOCATION_CATEGORY_STATE: "ADM1",
        LOCATION_CATEGORY_PROVINCE: "ADM2",
        LOCATION_CATEGORY_COUNTY: "ADM2",
        LOCATION_CATEGORY_REGION: "ADMD",
        LOCATION_CATEGORY_VILLAGE: "ADM3",
    }

    @classmethod
    def add_custom_arguments(cls, parser):
        class keyvalue(argparse.Action):
            # Constructor calling
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, dict())

                for value in values:
                    # split it into key and value
                    key, value = value.split("=")
                    # assign into dictionary
                    getattr(namespace, self.dest)[key] = value

        parser.add_argument(
            "-c",
            "--country_iso",
            choices=[x.alpha_2 for x in pycountry.countries],
            required=True,
        )

        parser.add_argument(
            "-f",
            "--filters",
            metavar="KEY=VALUE",
            nargs="*",
            action=keyvalue,
            help="Recommended using 'featureclass' filtering. dict. See: http://www.geonames.org/export/codes.html",
        )

    @classmethod
    def create_for_country(cls, country_iso):
        return cls.from_online_source(country_iso=country_iso)

    @classmethod
    def from_online_source(cls, country_iso, **kwargs):

        country = get_country_from_iso_code(country_iso=country_iso)

        geoname_url = cls.URL["geoname"]
        alternate_url = cls.URL["alternate"]

        geonames_file = DownloadableDataSource.from_online_source(
            url=geoname_url,
            country_iso2=country.alpha_2.upper(),
            desired_filename=cls.COMPRESSED_DESIRED_FILENAME,
            **kwargs,
        )

        altnames_file = DownloadableDataSource.from_online_source(
            url=alternate_url,
            country_iso2=country.alpha_2.upper(),
            desired_filename=cls.COMPRESSED_DESIRED_FILENAME,
            **kwargs,
        )

        return cls(
            geonames_filepath=geonames_file.file,
            alternate_names_filepath=altnames_file.file,
            **kwargs,
        )

    def __init__(
        self, geonames_filepath, alternate_names_filepath, filters={}, **kwargs
    ) -> None:

        # Super init. TODO multiple file_path?
        super().__init__(file_path=None)

        self._geonames_df = pd.read_csv(
            geonames_filepath,
            sep="\t",
            dtype=self.geoname_columns,
            names=tuple(self.geoname_columns),
            index_col=self.geoname_id_column,
        )[["name", "latitude", "longitude", "featureclass", "featurecode"]]
        self._geonames_df = geopandas.GeoDataFrame(
            data=self._geonames_df,
            geometry=geopandas.points_from_xy(
                x=self._geonames_df.longitude,
                y=self._geonames_df.latitude,
                crs="EPSG:4326",
            ),
        )

        if filters:
            self._geonames_df = self._filter_df(self._geonames_df, **filters)

        self._alternatenames_df = pd.read_csv(
            alternate_names_filepath,
            sep="\t",
            dtype=self.alternatenames_columns,
            names=tuple(self.alternatenames_columns),
            index_col=self.alternatenames_id_column,
        )[
            [
                "geonameid",
                "isolanguage",
                "alternatename",
                "isPreferredName",
                "isShortName",
                "isColloquial",
                "isHistoric",
            ]
        ]

        # Cast all "is*" fields to bool
        self._alternatenames_df.fillna(
            {
                "isPreferredName": 0,
                "isShortName": 0,
                "isColloquial": 0,
                "isHistoric": 0,
            },
            inplace=True,
        )
        self._alternatenames_df = self._alternatenames_df.astype(
            {
                "isPreferredName": bool,
                "isShortName": bool,
                "isColloquial": bool,
                "isHistoric": bool,
            }
        )

        self.df = pd.merge(
            left=self._geonames_df,
            right=self._alternatenames_df,
            how="left",
            left_index=True,
            right_on="geonameid",
        )

    @staticmethod
    def _filter_df(df, **kwargs):
        data = df
        # Filter data before
        filters = {**kwargs}
        for key, val in filters.items():
            logging.debug(f"Filtering df with {key}={val}")
            if isinstance(val, (tuple, list)):
                data = data[data[key].isin(val)]
            else:
                data = data[data[key] == val]

        return data

    def reverse(
        self, geometry, location_type, language_iso="en", exactly_one=True
    ) -> Location:

        result_ids = self.get_ids_by_region(
            geometry=geometry,
            **{"featurecode": self.get_field_by_location_type(value=location_type)},
        )
        logging.debug(f"Results ids {result_ids}")

        if not result_ids:
            return None

        if exactly_one:
            # Keeping only first result
            result_ids = result_ids[0]

        location_results = []
        for id in result_ids:
            _name = self.get_locale_by_id(id=id, language_iso=language_iso)
            _geonames_result = self.get_by_id(id=id)

            location_results.append(
                Location(
                    latitude=_geonames_result["latitude"],
                    longitude=_geonames_result["longitude"],
                    name=_name,
                    lang=language_iso,
                    category=location_type,
                )
            )

        return location_results[0] if exactly_one else location_results

    def filter_by_region(self, geometry, converter=None, **kwargs):
        # Make a copy of the dataset to preserve the original
        data = self._geonames_df

        data = self._filter_df(data, **kwargs)

        # Only keep the one with biggest area.
        geometry = get_biggest_polygon(geometry)
        geometry = shapely.from_wkt(geometry=geometry.wkt).simplify(0.05)

        # result is a pandas series: index geonameid, value True/False
        result = data.within(geometry)

        # Keep only geonameid of the result that are True
        geoname_ids = result[result].index.values

        result = self.df[self.df["geonameid"].isin(geoname_ids)]

        return converter(result) if converter else result

    def get_by_id(self, id):
        return self._geonames_df.loc[id]

    def get_id_by_name(self, name, **kwargs):
        result_generator = self.search(name=name, converter=dict, **kwargs)
        first_result = next(result_generator)
        return first_result["geonameid"]

    def get_ids_by_region(self, geometry, **kwargs):
        result = self.filter_by_region(geometry=geometry, **kwargs)

        return list(result["geonameid"].unique())

    def get_locale_by_id(self, id, language_iso=None):
        """Full list of supported languages can be found here:
        https://www.geonames.org/countries/
        """

        language = None
        if language_iso:
            language = get_language_from_iso_code(language_iso=language_iso)

        id_filter = self.df["geonameid"] == id

        if language:

            language_iso_list = []
            try:
                language_iso_list.append(language.alpha_2.lower())
            except AttributeError:
                pass

            try:
                language_iso_list.append(language.alpha_3.lower())
            except AttributeError:
                pass

            df_filtered = self.df.loc[
                (id_filter) & (self.df["isolanguage"].isin(language_iso_list)),
            ]
        else:
            df_filtered = self.df.loc[
                (id_filter) & (self.df["isolanguage"].isnull()),
            ]

        if df_filtered["isPreferredName"].any():
            df_filtered = df_filtered.loc[df_filtered["isPreferredName"]]

        result = None
        if len(df_filtered):
            result = df_filtered.iloc[0]["alternatename"]
            if result is None:
                result = df_filtered.iloc[0]["name"]

        return result

    def search(self, name, converter=None, strict=True, **kwargs):
        """Returns the most likely result as a pandas Series"""
        # Make a copy of the dataset to preserve the original
        data = self.df

        # Filter data before searching
        filters = {**kwargs}
        for key, val in filters.items():
            if isinstance(val, (tuple, list)):
                data = data[data[key].isin(val)]
            else:
                data = data[data[key] == val]

        data = data[data["name"].notnull()]
        if strict:
            matches = data[data["name"].str.contains(name, case=False, na=False)]
        else:
            # Use difflib to find matches
            diffs = difflib.get_close_matches(
                name, data["name"].tolist(), n=1, cutoff=0
            )
            matches = data[data["name"] == diffs[0]]

        for index, result in matches.iterrows():
            certainty = difflib.SequenceMatcher(None, result["name"], name).ratio()

            # Convert result if converter specified
            if converter:
                result = converter(result)

            result["certainty"] = certainty
            yield result
