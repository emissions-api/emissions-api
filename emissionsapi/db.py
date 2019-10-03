"""Database Layer for the Emmission API.
"""

from functools import wraps
import os

from sqlalchemy import create_engine, Column, Integer, Float
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
    # PostGis type
    geom = Column(geoalchemy2.Geometry(geometry_type="POINT"))

    def __init__(self, value, longitude, latitude):
        self.value = value
        self.longitude = longitude
        self.latitude = latitude
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


def get_points_in_polygon(session, polygon):
    """Get all points from within the specified polygon.

    :param session: SQL Alchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param polygon: Polygon where to search for points
    :type polygon: geoalchemy2.WKTElement
    :return: SQLAlchemy Query Object with the points from within the polygon.
    :rtype: sqlalchemy.orm.query.Query
    """
    return session.query(Carbonmonoxide).filter(
        geoalchemy2.func.ST_WITHIN(Carbonmonoxide.geom, polygon))


def get_points_in_rectangle(session, upper_left, lower_right):
    """Get all points from within a rectangle.

    :param session: SQL Alchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param polygon: Polygon where to search for points
    :type polygon: geoalchemy2.WKTElement
    :param upper_left: Upper left point of the rectangle
    :type upper_left: tuple
    :param lower_right: Lower right point of the rectangle
    :type lower_right: tuple
    :return: SQLAlchemy Query Object with the points from within the polygon.
    :rtype: sqlalchemy.orm.query.Query
    """
    # Defining the rectangle
    rectangle = geoalchemy2.elements.WKTElement(
        f'POLYGON(({upper_left[0]} {upper_left[1]},'
        f' {lower_right[0]} {upper_left[1]},'
        f' {lower_right[0]} {lower_right[1]},'
        f' {upper_left[0]} {lower_right[1]},'
        f' {upper_left[0]} {upper_left[1]}))')
    return get_points_in_polygon(session, rectangle)
