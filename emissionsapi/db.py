from functools import wraps


from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, LargeBinary, Enum, ForeignKeyConstraint, Table  # noqa 501
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from geoalchemy2 import Geometry

database = 'postgresql://user:user@localhost/db'

Session = None

Base = declarative_base()


class Carbonmonoxide(Base):
    __tablename__ = 'carbonmonoxide'
    id = Column(Integer, primary_key=True)
    Value = Column(Float)
    longitude = Column(Float)
    latitude = Column(Float)
    geo = Column(Geometry(geometry_type="POINT"))


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
    global Session
    if not Session:
        Engine = create_engine(database, echo=True)
        Session = sessionmaker(bind=Engine)
        Base.metadata.create_all(Engine)
    return Session()
