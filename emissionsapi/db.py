"""Database Layer for the Emmission API.
"""

from functools import wraps

from sqlalchemy import create_engine, Column, DateTime, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import geoalchemy2

from emissionsapi.config import config
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.db')

# Database uri as described in
# https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
# Retrieved as environment variable.
database = config('database') or 'postgresql://user:user@localhost/db'

# Global session variable. Set on initialization.
__session__ = None

# Base Class of all ORM objects.
Base = declarative_base()


class File(Base):
    """ORM Object for the nc files.
    """
    # Tablename
    __tablename__ = 'file'
    filename = Column(String, primary_key=True)


class Carbonmonoxide(Base):
    """ORM Object for Carbonmonoxide Point
    """
    # Tablename
    __tablename__ = 'carbonmonoxide'
    # Primary Key
    id = Column(Integer, primary_key=True)
    # Carbonmonoxide Value
    value = Column(Float)
    # Longitude
    longitude = Column(Float)
    # Latitude
    latitude = Column(Float)
    # timestamp
    timestamp = Column(DateTime)
    # PostGis type
    geom = Column(geoalchemy2.Geometry(geometry_type="POINT"))

    def __init__(self, value, longitude, latitude, timestamp):
        self.value = value
        self.longitude = longitude
        self.latitude = latitude
        self.timestamp = timestamp
        self.geom = geoalchemy2.elements.WKTElement(
            f"POINT({longitude} {latitude})")


def with_session(f):
    """Wrapper for f to make a SQLAlchemy session present within the function

    :param f: function to call
    :type f: function
    :raises e: Possible Exception of f
    :return: result of f
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
        sqlalchemy.orm.session.Session -- SQLAlchemy Session Object
    """
    global __session__
    # Create Database Connection, Tables and Sessionmaker if neccessary.
    if not __session__:
        Engine = create_engine(database)
        __session__ = sessionmaker(bind=Engine)
        Base.metadata.create_all(Engine)

    # Return new session object
    return __session__()


def get_points(session, polygon=None, begin=None, end=None):
    """Get all points filtered by time and location.

    :param session: SQL Alchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param polygon: Polygon where to search for points, defaults to None
    :type polygon: geoalchemy2.WKTElement, optional
    :param begin: Get only points after this timestamp, defaults to None
    :type begin: datetime.datetime, optional
    :param end: datetime.datetime, defaults to None
    :type end: Get only points before this timestamp, optional
    :return: SQLAlchemy Query Object with the points from within the polygon.
    :rtype: sqlalchemy.orm.query.Query
    """
    query = session.query(Carbonmonoxide)

    # Filter with polygon
    if polygon is not None:
        query = query.filter(geoalchemy2.func.ST_WITHIN(
            Carbonmonoxide.geom, polygon))

    # Only points after
    if begin is not None:
        query = query.filter(begin <= Carbonmonoxide.timestamp)

    # Filter before
    if end is not None:
        query = query.filter(end > Carbonmonoxide.timestamp)

    return query
