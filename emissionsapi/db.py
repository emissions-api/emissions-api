from functools import wraps
import os

from sqlalchemy import create_engine, Column, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import geoalchemy2

# Database uri as described in
# https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
# Retrieved as environment variable.
database = os.environ.get(
    'EMISSIONS_API',
    'postgresql://user:user@localhost/db')

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
