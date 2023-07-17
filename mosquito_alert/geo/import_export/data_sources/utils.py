import logging
import tempfile

import pycountry
import requests
from django.contrib.gis.geos import GeometryCollection, MultiPolygon, Polygon


def download_file(url, filename=None, **kwargs):
    if filename is None:
        tfp = tempfile.NamedTemporaryFile(delete=False, **kwargs)
        filename = tfp.name
    logging.info(f"Downloading {url} to {filename}")
    response = requests.get(url, allow_redirects=True)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)
    return filename


def get_pycountry_param_from_iso_code(db_name, iso_code, raise_not_found=True):
    result = None
    pycountry_db = getattr(pycountry, db_name)
    logging.debug(f"pycountry using {db_name} db")
    if len(iso_code) == 2:
        logging.debug("pycountry using alpha_2")
        result = pycountry_db.get(alpha_2=iso_code)
    elif len(iso_code) == 3:
        logging.debug("pycountry using alpha_3")
        result = pycountry_db.get(alpha_3=iso_code)
    else:
        raise ValueError("ISO code must be iso2 or iso3.")

    if result is None and raise_not_found:
        raise KeyError(
            f"Could not find a record for {iso_code} in pycountry {db_name} db"
        )

    return result


def get_language_from_iso_code(language_iso):
    return get_pycountry_param_from_iso_code(db_name="languages", iso_code=language_iso)


def get_country_from_iso_code(country_iso):
    return get_pycountry_param_from_iso_code(db_name="countries", iso_code=country_iso)


def get_biggest_polygon(geometry):
    if not isinstance(geometry, (Polygon, MultiPolygon)):
        raise ValueError("Geometry must be (Multi)Polygon type.")

    g = geometry.clone()

    if isinstance(g, GeometryCollection):
        # Case is multiple
        g.sort(key=lambda x: x.area, reverse=True)
        g = g[0]

    return g
