# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Web application to deliver the data stored in the database via an API to
the users.
"""
from functools import wraps
import logging
import dateutil.parser

import connexion
import json
import geojson
from flask import redirect, request

import emissionsapi.db
from emissionsapi.country_bounding_boxes import country_bounding_boxes
from emissionsapi.utils import bounding_box_to_wkt, polygon_to_wkt, \
    RESTParamError

# Logger
logger = logging.getLogger(__name__)


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
                logger.debug(f'Try to parse {key} as date')
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
        # Parse parameter geoframe
        if geoframe is not None:
            try:
                logger.debug('Try to parse geoframe')
                kwargs['wkt'] = bounding_box_to_wkt(*geoframe)
            except ValueError:
                return 'Invalid geoparam', 400
        # parse parameter country
        elif country is not None:
            logger.debug('Try to parse country')
            if country not in country_bounding_boxes:
                return 'Unknown country code.', 400
            kwargs['wkt'] = bounding_box_to_wkt(
                *country_bounding_boxes[country][1])
        # parse parameter polygon
        elif polygon is not None:
            try:
                logger.debug('Try to parse polygon')
                kwargs['wkt'] = polygon_to_wkt(polygon)
            except RESTParamError as err:
                return str(err), 400
        # parse paramter point
        elif point is not None:
            try:
                logger.debug('Try to parse point')
                kwargs['wkt'] = f'POINT({point[0]} {point[1]})'
                # Take a radius from 0.2 decimal degree which are approx.
                # 22264 meter
                kwargs['distance'] = 0.2
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


@parse_wkt
@parse_date('begin', 'end')
@emissionsapi.db.with_session
def get_data(session, wkt=None, distance=None, begin=None, end=None,
             limit=None, offset=None, **kwargs):
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
    :return: Feature Collection with requested Points
    :rtype: geojson.FeatureCollection

    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    # Init feature list
    features = []
    # Iterate through database query
    query = emissionsapi.db.get_points(session)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, wkt=wkt, distance=distance, begin=begin, end=end)
    # Apply limit and offset
    query = emissionsapi.db.limit_offset_query(
        query, limit=limit, offset=offset)

    for obj, longitude, latitude in query:
        # Create and append single features.
        features.append(geojson.Feature(
            geometry=geojson.Point((longitude, latitude)),
            properties={
                "carbonmonoxide": obj.value,
                "timestamp": obj.timestamp
            }))
    # Create feature collection from gathered points
    feature_collection = geojson.FeatureCollection(features)
    return feature_collection


@parse_wkt
@cache_with_session
def get_average(session, wkt=None, distance=None, begin=None, end=None,
                limit=None, offset=None, **kwargs):
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
    :return: List of calculated averages
    :rtype: list

    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    query = emissionsapi.db.get_averages(session)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, wkt=wkt, distance=distance, begin=begin, end=end)
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


@parse_wkt
@cache_with_session
def get_statistics(session, interval='day', wkt=None, distance=None,
                   begin=None, end=None, limit=None, offset=None, **kwargs):
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
    :return: List of statistical values
    :rtype: list

    .. _date_trunc: https://postgresql.org/docs/9.1/functions-datetime.html
    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    query = emissionsapi.db.get_statistics(session)
    # Filter result
    query = emissionsapi.db.filter_query(
        query, wkt=wkt, distance=distance, begin=begin, end=end)
    # Apply limit and offset
    query = emissionsapi.db.limit_offset_query(
        query, limit=limit, offset=offset)

    return [{'value': {
                'count': count,
                'average': avg,
                'standard deviation': stddev,
                'min': min_val,
                'max': max_val},
            'time': {
                'min': min_time,
                'max': max_time,
                'interval_start': inter}}
            for count, avg, stddev, min_val, max_val, min_time, max_time, inter
            in query]


# Create connexion app
app = connexion.App(__name__)

# Add swagger description to api
app.add_api('openapi.yml', )

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
