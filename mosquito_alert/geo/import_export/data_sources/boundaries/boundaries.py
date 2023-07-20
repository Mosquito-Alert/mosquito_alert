import logging
import re
from abc import ABC, abstractmethod

import pycountry
from django.contrib.gis.gdal.datasource import DataSource

from ....models import BoundaryLayer
from ..base import BaseDataSource, CompressedDataSourceMixin, OnlineDataSource
from ..utils import get_country_from_iso_code
from .files import uri_to_vsi_path


class BaseBoundaryDataSource(BaseDataSource, CompressedDataSourceMixin, ABC):
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument(
            "-l",
            "--level",
            required=True,
            type=int,
            help="Select only a level from the data source.",
        )

        if cls.DEFAULT_BOUNDARY_LEVEL_TYPE:
            logging.debug(f"Setting parser defaults for bl_type to {cls.DEFAULT_BOUNDARY_LEVEL_TYPE.value}")
            parser.set_defaults(bl_type=cls.DEFAULT_BOUNDARY_LEVEL_TYPE.value)

        cls._add_custom_arguments(parser=parser)

    def __init__(self, uri, level, **kwargs) -> None:
        super().__init__(**kwargs)

        self.level = int(level)
        self.ds = DataSource(uri_to_vsi_path(uri))

    @property
    @abstractmethod
    def DEFAULT_BOUNDARY_LEVEL_TYPE(self):
        return NotImplementedError

    @property
    @abstractmethod
    def code_field_name(self):
        return NotImplementedError

    @property
    @abstractmethod
    def level_name(self):
        return NotImplementedError

    @property
    @abstractmethod
    def level_description(self):
        return NotImplementedError

    @property
    @abstractmethod
    def name_field_name(self):
        return NotImplementedError


class BaseOnlineBoundaryDataSource(BaseBoundaryDataSource, OnlineDataSource):
    @classmethod
    def from_online_source(cls, **kwargs):
        url = cls._construct_url(**kwargs)

        zipped_file_path = cls._get_compressed_desired_filename(**kwargs)
        uri = url
        if zipped_file_path:
            # See 'uri_to_vsi_path' method,
            uri = uri + "!" + zipped_file_path

        return cls(url=url, uri=uri, **kwargs)


#########################################################


class NutsBoundarySource(BaseOnlineBoundaryDataSource):
    CLI_NAME = "nuts"
    COMPRESSED_DESIRED_FILENAME = "NUTS_RG_{scale}_{db_version}_{coor}_LEVL_{level}.shp"
    URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/shp/{shapefile}.zip".format(
        shapefile=COMPRESSED_DESIRED_FILENAME
    )
    DEFAULT_BOUNDARY_LEVEL_TYPE = BoundaryLayer.BoundaryType.STATISTICAL

    @classmethod
    def _add_custom_arguments(cls, parser):
        parser.add_argument(
            "--db_version",
            type=int,
            choices=[2006, 2010, 2013, 2016, 2021],
            default=2021,
        )

        parser.add_argument(
            "--scale",
            type=str,
            choices=["01M", "03M", "10M", "20M", "60M"],
            default="20M",
        )

        parser.add_argument(
            "--coor",
            type=int,
            choices=[3035, 4326, 3857],
            default=4326,
            help="Coordinate reference system",
        )

    @classmethod
    def from_online_source(cls, db_version, scale, coor, **kwargs):
        # Forcinig only arguments.
        return super().from_online_source(db_version=db_version, scale=scale, coor=coor, **kwargs)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        if self.level < 0 or self.level > 3:
            raise ValueError(f"Invalid level ({self.level}). NUTS allowed levels are between 0 and 3")

    @property
    def code_field_name(self):
        return "NUTS_ID"

    @property
    def level_name(self):
        return f"NUTS {self.level}"

    @property
    def level_description(self):
        return {
            0: "National boundaries.",
            1: "Major socio-economic regions.",
            2: "Basic regions for the application of regional policies.",
            3: "Small regions for specific diagnoses.",
        }[self.level]

    @property
    def name_field_name(self):
        return "NAME_LATN"


class GadmBoundarySource(BaseOnlineBoundaryDataSource):
    CLI_NAME = "gadm"

    URL = "https://geodata.ucdavis.edu/gadm/gadm{db_version}/shp/gadm{db_version_str}_{country_iso3}_shp.zip"
    COMPRESSED_DESIRED_FILENAME = "gadm{db_version_str}_{country_iso3}_{level}.shp"

    DEFAULT_BOUNDARY_LEVEL_TYPE = BoundaryLayer.BoundaryType.ADMINISTRATIVE

    @classmethod
    def _add_custom_arguments(cls, parser):
        parser.add_argument("--db_version", type=float, default=4.1)

        parser.add_argument(
            "-c",
            "--country_code",
            choices=[x.alpha_2 for x in pycountry.countries],
            required=True,
        )

    @classmethod
    def from_online_source(cls, db_version, country_code, **kwargs):
        db_version_str = str(db_version).replace(".", "")
        country = get_country_from_iso_code(country_iso=country_code)

        return super().from_online_source(
            db_version_str=db_version_str,
            country_iso3=country.alpha_3.upper(),
            db_version=db_version,
            **kwargs,
        )

    @property
    def code_field_name(self):
        return f"GID_{self.level}"

    @property
    def level_name(self):
        if self.level == 0:
            level_name = "Country"
        else:
            level_name = self.ds[0][0].get(f"ENGTYPE_{self.level}")
            # CamelCase splitting
            level_name_groups = re.findall(pattern=r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", string=level_name)
            level_name = " ".join(level_name_groups)
        return level_name

    @property
    def level_description(self):
        return None

    @property
    def name_field_name(self):
        return "COUNTRY" if self.level == 0 else f"NAME_{self.level}"
