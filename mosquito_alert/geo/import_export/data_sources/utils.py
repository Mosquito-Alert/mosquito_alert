import logging
import tempfile
import urllib.request

import pycountry


def download_file(url, filename=None, **kwargs):
    if filename is None:
        tfp = tempfile.NamedTemporaryFile(delete=False, **kwargs)
        filename = tfp.name
    logging.info(f"Downloading {url} to {filename}")
    path, http_message = urllib.request.urlretrieve(url=url, filename=filename)
    logging.debug(f"HTTP MESSAGE: {http_message}")
    return path


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


def get_biggest_polygon(multipolygon):
    m = multipolygon.clone()

    # If num geom is greater than 1
    if m.num_geom > 1:
        m.sort(key=lambda x: x.area, reverse=True)
        m = m[0]
    return m
