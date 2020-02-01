import logging

import iso3166
import geopandas


# Logger
logger = logging.getLogger(__name__)

# Global country shape storage
__country_shapes__ = {}


class CountryNotFound(Exception):
    pass


def __load_country_shapes__():
    '''Load country shapes'''
    logger.info('Loading country shapes')
    # load shapefile for country shapes and get records
    world = geopandas.read_file(
        geopandas.datasets.get_path('naturalearth_lowres'))

    for _, country in world.iterrows():
        # Try to find the alpha 3 country code in the iso3166.
        # Sometimes it is not set ( value '-99'). Then we try to match by name.
        country_codes = iso3166.countries_by_alpha3.get(
            country['iso_a3'],
            iso3166.countries_by_name.get(country['name'].upper())
        )

        # log warning if the country is not found.
        if not country_codes:
            logger.warning('Unable to find %s', country['name'])
            continue

        # Save geometry as wkt string with both alpha 2 and 3 code as key.
        shape = country['geometry']
        __country_shapes__[country_codes.alpha2] = shape
        __country_shapes__[country_codes.alpha3] = shape


def get_country_wkt(country):
    '''Get wkt for country.

    :param country: alpha 2 or 3 country code.
    :type country: str
    :raises CountryNotFound: Country is not found in the country codes.
    :return: WKT defining the country.
    :rtype: str
    '''
    if not __country_shapes__:
        __load_country_shapes__()

    try:
        return __country_shapes__[country].wkt
    except KeyError:
        raise CountryNotFound
