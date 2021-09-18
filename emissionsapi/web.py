# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Web application to deliver the data stored in the database via an API to
the users.
"""
from functools import wraps
import dateutil.parser
import logging
import os.path

import connexion
import json
from flask import redirect, request, jsonify
from h3 import h3

import emissionsapi.db
from emissionsapi.country_shapes import CountryNotFound, get_country_wkt
from emissionsapi.country_shapes import get_country_codes  # noqa - used in API
from emissionsapi.utils import bounding_box_to_wkt, polygon_to_wkt, \
    RESTParamError

# Logger
logger = logging.getLogger(__name__)


def get_table(f):
    '''Function wrapper getting the corresponding table to a product.

    :param f: Function to call
    :type f: Function
    :raises e: Possible exception of f
    :return: Result of f
    '''
    @wraps(f)
    def wrapper(*args, **kwargs):
        logger.debug('Try getting table to product')
        product = kwargs.get('product')

        # Error cases should never happen,
        # since connexion only allows valid values.
        if not product:
            return 'No product specified', 400
        try:
            tbl = emissionsapi.db.products[product]['table']
        except KeyError:
            return 'Unsupported product specified', 400

        return f(*args, **kwargs, tbl=tbl)
    return wrapper


def parse_date(*keys):
    """Function wrapper replacing string date arguments with
    datetime.datetime

    :param keys: keys to be parsed and replaced
    :type keys: list
    :return: wrapper function
    :rtype: func
    """
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            for key in keys:
                logger.debug('Try parsing %s as date', key)
                date = kwargs.get(key)
                if date is None:
                    continue
                try:
                    kwargs[key] = dateutil.parser.parse(date)
                except ValueError:
                    return f'Invalid {key}', 400
            return function(*args, **kwargs)
        return wrapper
    return decorator


def parse_wkt(f):
    """Function wrapper replacing 'geoframe', 'country' and 'polygon' with a
    WKT polygon.

    :param f: Function to call
    :type f: Function
    :raises e: Possible exception of f
    :return: Result of f
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        geoframe = kwargs.pop('geoframe', None)
        country = kwargs.pop('country', None)
        polygon = kwargs.pop('polygon', None)
        point = kwargs.pop('point', None)

        number_of_parameter = sum(x is not None for x in (
            geoframe, country, polygon, point))
        if number_of_parameter > 1:
            return ("'geoframe', 'country', 'polygon' and "
                    "'point' are mutually exclusive", 400)

        # Parse parameter geoframe
        if geoframe is not None:
            try:
                logger.debug('Try parsing geoframe')
                kwargs['wkt'] = bounding_box_to_wkt(*geoframe)
            except ValueError:
                return 'Invalid geoparam', 400
        # parse parameter country
        elif country is not None:
            logger.debug('Try parsing country')
            try:
                kwargs['wkt'] = get_country_wkt(country.upper())
            except CountryNotFound:
                return 'Unknown country code.', 400
        # parse parameter polygon
        elif polygon is not None:
            try:
                logger.debug('Try parsing polygon')
                kwargs['wkt'] = polygon_to_wkt(polygon)
            except RESTParamError as err:
                return str(err), 400
        # parse parameter point
        elif point is not None:
            try:
                logger.debug('Try to parse point')
                point = h3.h3_to_geo(h3.geo_to_h3(
                    point[1], point[0], emissionsapi.db.resolution))
                kwargs['wkt'] = f'POINT({point[1]} {point[0]})'
                # Take a radius from 0.01 decimal degree which are approx.
                # 1113 meter
                kwargs['distance'] = 0.01
            except KeyError:
                return 'Invalid point', 400
        return f(*args, **kwargs)
    return decorated


def cache_with_session(function):
    """Function wrapper caching responses based on their request parameters in
    the PostgreSQL database.

    The established database session is passed to the wrapped function as first
    argument much like :func:`~emissionsapi.db.with_session` in case no cached
    value for this request is present yet.

    Argument names for beginning and end of a time frame affecting the cache
    are automatically assumed to be named ``begin`` and ``end``.  These are
    stored alongside the cached data to determine if the cached values needs to
    be purged when importing new data.

    :return: Function wrapper
    :rtype: func
    """
    date_args = [x for x in ['begin', 'end'] if x]

    @parse_date(*date_args)
    @emissionsapi.db.with_session
    @wraps(function)
    def wrapper(session, *args, **kwargs):
        # Internal parameter for debugging possible future cache problems
        # Deliberately not publishing this via OpenAPI specification
        if request.args.get('cache', '1').lower() in ['false', 'no', '0']:
            return function(session, *args, **kwargs)
        # get time frame parameters
        begin = kwargs.get('begin')
        end = kwargs.get('end')

        # construct a primary key for this request
        req = json.dumps((request.path, request.args), sort_keys=True)
        for cache in session.query(emissionsapi.db.Cache)\
                            .filter(emissionsapi.db.Cache.request == req):
            logger.debug('Using cache')
            return cache.response

        # not in cache, put in cache
        result = function(session, *args, **kwargs)
        session.add(emissionsapi.db.Cache(
            request=req,
            begin=begin,
            end=end,
            response=result))
        session.commit()
        return result
    return wrapper


@get_table
@parse_wkt
@parse_date('begin', 'end')
@emissionsapi.db.with_session
def get_data(session, wkt=None, distance=None, begin=None, end=None,
             limit=None, offset=None, tbl=None, **kwargs):
    """Get data in GeoJSON format.

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :param wkt: Well-known text representation of geometry, defaults to None.

    :type wkt: string, optional
    :param distance: Distance as defined in PostGIS' ST_DWithin_ function.
    :type distance: float, optional
    :type begin: datetime.datetime
    :param end: filter out points after this date
    :type end: datetime.datetime
    :param limit: Limit number of returned items
    :type limit: int
    :param offset: Specify the offset of the first item to return
    :type offset: int
    :param tbl: Table to get data from, defaults to None
    :type tbl: sqlalchemy.sql.schema.Table, optional
    :return: Feature Collection with requested Points
    :rtype: geojson.FeatureCollection

    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    # Iterate through database query
    query = emissionsapi.db.get_points(session, tbl)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, tbl, wkt=wkt, distance=distance, begin=begin, end=end)
    # Apply limit and offset
    query = emissionsapi.db.limit_offset_query(
        query, limit=limit, offset=offset)

    return jsonify({
        'features': [{
            'geometry': {
                'coordinates': [longitude, latitude],
                'type': 'Point',
            },
            'properties': {
                'timestamp': timestamp.isoformat('T') + 'Z',
                'value': value,
            },
            'type': 'Feature'
        } for value, timestamp, longitude, latitude in query],
        "type": "FeatureCollection"
    })


@get_table
@parse_wkt
@cache_with_session
def get_average(session, wkt=None, distance=None, begin=None, end=None,
                limit=None, offset=None, tbl=None, **kwargs):
    """Get daily average for a specified area filtered by time.

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :param wkt: Well-known text representation of geometry, defaults to None.
    :type wkt: string, optional
    :param distance: Distance as defined in PostGIS' ST_DWithin_ function.
    :type distance: float, optional
    :param begin: Filter out points before this date
    :type begin: datetime.datetime
    :param end: filter out points after this date
    :type end: datetime.datetime
    :param limit: Limit number of returned items
    :type limit: int
    :param offset: Specify the offset of the first item to return
    :type offset: int
    :param tbl: Table to get data from, defaults to None
    :type tbl: sqlalchemy.sql.schema.Table, optional
    :return: List of calculated averages
    :rtype: list

    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    query = emissionsapi.db.get_averages(session, tbl)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, tbl, wkt=wkt, distance=distance, begin=begin, end=end)
    # Apply limit and offset
    query = emissionsapi.db.limit_offset_query(
        query, limit=limit, offset=offset)

    result = []
    for avg, max_time, min_time, _ in query:
        result.append({
            'average': avg,
            'start': min_time,
            'end': max_time})
    return result


@get_table
@parse_wkt
@cache_with_session
def get_statistics(session, interval='day', wkt=None, distance=None,
                   begin=None, end=None, limit=None, offset=None, tbl=None,
                   **kwargs):
    """Get statistical data like amount, average, min, or max values for a
    specified time interval. Optionally, time and location filters can be
    applied.

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :param interval: Length of the time interval for which data is being
                     aggregated as accepted by PostgreSQL's date_trunc_
                     function like ``day`` or ``week``.
    :type interval: str
    :param wkt: Well-known text representation of geometry, defaults to None.
    :type wkt: string, optional
    :param distance: Distance as defined in PostGIS' ST_DWithin_ function.
    :type distance: float, optional
    :param begin: Filter out points before this date
    :type begin: datetime.datetime
    :param end: filter out points after this date
    :type end: datetime.datetime
    :param limit: Limit number of returned items
    :type limit: int
    :param offset: Specify the offset of the first item to return
    :type offset: int
    :param tbl: Table to get data from, defaults to None
    :type tbl: sqlalchemy.sql.schema.Table, optional
    :return: List of statistical values
    :rtype: list

    .. _date_trunc: https://postgresql.org/docs/9.1/functions-datetime.html
    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    query = emissionsapi.db.get_statistics(
        session, tbl, interval_length=interval)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, tbl, wkt=wkt, distance=distance, begin=begin, end=end)
    # Apply limit and offset
    query = emissionsapi.db.limit_offset_query(
        query, limit=limit, offset=offset)

    return [
        {
            'value': {
                'count': count,
                'average': avg,
                'standard deviation': stddev,
                'min': min_val,
                'max': max_val},
            'time': {
                'min': min_time,
                'max': max_time,
                'interval_start': inter}
        }
        for count, avg, stddev, min_val, max_val, min_time, max_time, inter
        in query]


@get_table
@emissionsapi.db.with_session
def get_data_range(session, tbl=None, **kwargs):
    """Get the range of data currently available from the API.

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :param tbl: Table to get data from, defaults to None
    :type tbl: sqlalchemy.sql.schema.Table, optional
    :return: Object describing the range of data available
    :rtype: dict
    """
    query = emissionsapi.db.get_data_range(session, tbl)

    for min_time, max_time in query:
        return {'first': min_time,
                'last': max_time}


def get_products():
    """Get all products currently available from the API.

    :return: List of dictionaries describing the available products.
    :rtype: list
    """
    return [
        {
            'name': name,
            'product_variable': attributes.get('product')
        } for name, attributes in emissionsapi.db.products.items()
    ]


# Create connexion app
app = connexion.App(__name__)

# Add swagger description to api
app.add_api(os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'openapi.yml'),
    arguments={'products': list(emissionsapi.db.products.keys())})

# Create app to run with wsgi server
application = app.app


@app.route('/')
def home():
    """Redirect / to the swagger ui

    :return: Redirect response
    :rtype: werkzeug.wrappers.response.Response
    """
    return redirect('/ui', code=302)


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    It starts the Connexion Debug Server. It is not meant to be used for
    production, but only during the development.
    """
    logger.info("Starting the Connexion Debug Server")
    app.run(host='127.0.0.1')


if __name__ == "__main__":
    entrypoint()
