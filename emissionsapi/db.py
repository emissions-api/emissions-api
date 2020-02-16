# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Database layer for the Emmission API.
"""

from functools import wraps
import logging

import sqlalchemy
from sqlalchemy import and_, or_, create_engine, Column, DateTime, Float, \
    String, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import pandas
import psycopg2.extensions
import geoalchemy2

from emissionsapi.config import config

# Logger
logger = logging.getLogger(__name__)

# Database uri as described in
# https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
# Retrieved as environment variable.
database = config('database') or 'postgresql://user:user@localhost/db'

# Global session variable. Set on initialization.
__session__ = None

# Base Class of all ORM objects.
Base = declarative_base()

# Add psycopg2 adapter for pandas Series
psycopg2.extensions.register_adapter(
    pandas.core.series.Series,
    lambda arr: psycopg2.extensions.adapt(list(arr)))


class AlembicVersion(Base):
    __tablename__ = 'alembic_version'
    version_num = Column(String(32), primary_key=True)


class File(Base):
    """ORM object for the nc files.
    """
    __tablename__ = 'file'
    filename = Column(String, primary_key=True)
    """Name of processed data file"""


class Cache(Base):
    """ORM object for the request cache
    """
    __tablename__ = 'cache'
    request = Column(String, primary_key=True)
    """Primary key identifying the request"""
    begin = Column(DateTime)
    """Begin of the time interval involved in this request (used for
    efficiently invalidating caches)
    """
    end = Column(DateTime)
    """End of the time interval involved in this request (used for efficiently
    invalidating caches)
    """
    response = Column(PickleType)
    """Cached response"""

    @classmethod
    def invalidate(cache, session, earliest, latest):
        """Invalidates/deletes all cached responses in the given interval to
        ensure these data is generated anew. This is meant to be run when the
        underlying data for this interval changes, for instance since new data
        has been imported.

        :param session: SQLAlchemy Session
        :type session: sqlalchemy.orm.session.Session
        :param earliest: Earliest time of the interval to invalidate
        :type earliest: datetime.datetime
        :param latest: Latest time of the interval to invalidate
        :type latest: datetime.datetime

        """
        logger.debug('Invalidating cache in interval %s..%s',
                     earliest.isoformat(), latest.isoformat())
        session.query(cache)\
               .filter(and_(or_(cache.begin.is_(None),
                                cache.begin <= latest),
                            or_(cache.end.is_(None),
                                cache.end > earliest)))\
               .delete()
        session.commit()


carbonmonoxide = sqlalchemy.Table(
    'carbonmonoxide', Base.metadata,
    Column('value', Float),
    Column('timestamp', DateTime, index=True),
    Column('geom', geoalchemy2.Geometry(geometry_type='POINT')))


def with_session(f):
    """Wrapper for f to make a SQLAlchemy session present within the function

    :param f: Function to call
    :type f: Function
    :raises e: Possible exception of f
    :return: Result of f
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get new session
        session = get_session()
        try:
            # Call f with the session and all the other arguments
            result = f(session, *args, **kwargs)
        except Exception as e:
            # Rollback session, something bad happend.
            session.rollback()
            session.close()
            raise e
        # Close session and return the result of f
        session.close()
        return result
    return decorated


def get_session():
    """Get a new session.

    Lazy load the database connection and create the tables.

    Returns:
        sqlalchemy.orm.session.Session -- SQLAlchemy Session object
    """
    global __session__
    # Create database connection, tables and Sessionmaker if neccessary.
    if not __session__:
        Engine = create_engine(
            database, echo=logger.getEffectiveLevel() == logging.DEBUG)
        __session__ = sessionmaker(bind=Engine)
        Base.metadata.create_all(Engine)

    # Return new session object
    return __session__()


def insert_dataset(session, data, tbl=carbonmonoxide):
    '''Batch insert data into the database using PostGIS specific functions.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param data: DataFrame containing value, timestamp, longitude and latitude
    :type data: pandas.core.frame.DataFrame
    :param tbl: Base class representing the database table for the data
    :type tbl: sqlalchemy.ext.declarative.api.DeclarativeMeta
    '''
    values = sqlalchemy.select([sqlalchemy.func.unnest(data.value),
                                sqlalchemy.func.unnest(data.timestamp),
                                sqlalchemy.func.ST_MakePoint(
                                    sqlalchemy.func.unnest(data.longitude),
                                    sqlalchemy.func.unnest(data.latitude))])
    query = sqlalchemy.insert(tbl).from_select(tbl.columns, values)
    session.execute(query)


def get_points(session):
    """Get all points.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :return: SQLAlchemy Query returning tuples of value, timestamp, longitude,
             and latitude.
    :rtype: sqlalchemy.orm.query.Query
    """
    return session.query(
        carbonmonoxide.c.value,
        carbonmonoxide.c.timestamp,
        carbonmonoxide.c.geom.ST_X(),
        carbonmonoxide.c.geom.ST_Y())


def get_averages(session):
    """Get daily averages of all points.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :return: SQLAlchemy Query with tuple of the daily carbon monoxide average,
             the maximal timestamp the minimal timestamp and the timestamp
             truncated by day.
    :rtype: sqlalchemy.orm.query.Query
    """
    day = sqlalchemy.func.date(carbonmonoxide.c.timestamp)
    return session.query(
        sqlalchemy.func.avg(carbonmonoxide.c.value),
        sqlalchemy.func.max(carbonmonoxide.c.timestamp),
        sqlalchemy.func.min(carbonmonoxide.c.timestamp),
        day).group_by(day)


def get_statistics(session, interval_length='day'):
    """Get statistical data like amount, average, min, or max values for a
    specified time interval. Optionally, time and location filters can be
    applied.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param interval_length: Length of the time interval for which data is being
                            aggregated as accepted by PostgreSQL's date_trunc_
                            function like ``day`` or ``week``.
    :type interval_length: str
    :return: SQLAlchemy Query requesting the following statistical values for
             the specified time interval:

             - number of considered measurements
             - average carbon monoxide value
             - minimum carbon monoxide value
             - maximum carbon monoxide value
             - time of the first measurement
             - time of the last measurement
             - start of the interval
    :rtype: sqlalchemy.orm.query.Query

    .. _date_trunc: https://postgresql.org/docs/9.1/functions-datetime.html
    """
    interval = sqlalchemy.func.date_trunc(interval_length,
                                          carbonmonoxide.c.timestamp)
    return session.query(
        sqlalchemy.func.count(carbonmonoxide.c.value),
        sqlalchemy.func.avg(carbonmonoxide.c.value),
        sqlalchemy.func.stddev(carbonmonoxide.c.value),
        sqlalchemy.func.min(carbonmonoxide.c.value),
        sqlalchemy.func.max(carbonmonoxide.c.value),
        sqlalchemy.func.min(carbonmonoxide.c.timestamp),
        sqlalchemy.func.max(carbonmonoxide.c.timestamp),
        interval).group_by(interval)


def filter_query(query, wkt=None, distance=None, begin=None, end=None):
    """Filter query by time and location.

    :param query: SQLAlchemy Query
    :type query: sqlalchemy.orm.Query
    :param wkt: WKT Element specifying an area in which to search for points,
                defaults to None.
    :type wkt: geoalchemy2.WKTElement, optional
    :param distance: Distance as defined in PostGIS' ST_DWithin_ function.
    :type distance: float, optional
    :param begin: Get only points after this timestamp, defaults to None
    :type begin: datetime.datetime, optional
    :param end: Get only points before this timestamp, defaults to None
    :type end: datetime.datetime, optional
    :return: SQLAlchemy Query filtered by time and location.
    :rtype: sqlalchemy.orm.query.Query

    .. _ST_DWithin: https://postgis.net/docs/ST_DWithin.html
    """
    # Filter by WKT
    if wkt is not None:
        if distance is not None:
            query = query.filter(geoalchemy2.func.ST_DWITHIN(
                carbonmonoxide.c.geom, wkt, distance))
        else:
            query = query.filter(geoalchemy2.func.ST_WITHIN(
                carbonmonoxide.c.geom, wkt))

    # Filter for points after the time specified as begin
    if begin is not None:
        query = query.filter(begin <= carbonmonoxide.c.timestamp)

    # Filter for points before the time specified as end
    if end is not None:
        query = query.filter(end > carbonmonoxide.c.timestamp)

    return query


def limit_offset_query(query, limit=None, offset=None):
    """Apply limit and offset to the query.

    :param query: SQLAlchemy Query
    :type query: sqlalchemy.orm.Query
    :param limit: Limit number of Items returned, defaults to None
    :type limit: int, optional
    :param offset: Specify the offset of the first hit to return,
                   defaults to None
    :type offset: int, optional
    :return: SQLAlchemy Query with limit and offset applied.
    :rtype: sqlalchemy.orm.query.Query
    """
    # Apply limit
    if limit is not None:
        query = query.limit(limit)

    # Apply offset
    if offset is not None:
        query = query.offset(offset)
    return query


def get_data_range(session):
    """Get the range of data currently available from the API.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :return: SQLAlchemy Query requesting the minimum and maximum measurement
             time from all values.
    :rtype: sqlalchemy.orm.query.Query
    """
    return session.query(
        sqlalchemy.func.min(carbonmonoxide.c.timestamp),
        sqlalchemy.func.max(carbonmonoxide.c.timestamp))
