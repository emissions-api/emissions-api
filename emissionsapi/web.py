# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Web application to deliver the data stored in the database via an API to
the users.
"""
import datetime

import connexion
import geojson

import emissionsapi.db
import emissionsapi.logger
from emissionsapi.country_bounding_boxes import country_bounding_boxes
from emissionsapi.utils import bounding_box_to_wkt

# Logger
logger = emissionsapi.logger.getLogger('emission-api.web')


@emissionsapi.db.with_session
def get_data(session, country=None, geoframe=None, begin=None, end=None):
    """Get data in GeoJSON format.

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :param country: 'country' url parameter
    :type country: string
    :param geoframe: 'geoframe' url parameter
    :type geoframe: string
    :return: Feature Collection with requested Points
    :rtype: geojson.FeatureCollection
    """
    rectangle = None
    # Parse parameter geoframe
    if geoframe is not None:
        try:
            rectangle = bounding_box_to_wkt(
                *[float(x) for x in geoframe.split(',')])
        except ValueError:
            return 'Invalid geoparam', 400
    # parse parameter country
    elif country is not None:
        if country not in country_bounding_boxes:
            return 'Unknown country code.', 400
        rectangle = bounding_box_to_wkt(*country_bounding_boxes[country][1])

    # Parse parameter begin
    try:
        if begin is not None:
            begin = datetime.datetime.fromisoformat(begin)
    except ValueError:
        return 'Invalid begin', 400

    # Parse parameter end
    try:
        if end is not None:
            end = datetime.datetime.fromisoformat(end)
    except ValueError:
        return 'Invalid end', 400

    # Init feature list
    features = []
    # Iterate through database query
    query = emissionsapi.db.get_points(
        session, polygon=rectangle, begin=begin, end=end)
    for feature in query:
        # Create and append single features.
        features.append(geojson.Feature(
            geometry=geojson.Point((feature.longitude, feature.latitude)),
            properties={
                "carbonmonixide": feature.value,
                "timestamp": feature.timestamp
            }))
    # Create feature collection from gathered points
    feature_collection = geojson.FeatureCollection(features)
    return feature_collection


# Create connexion app
app = connexion.App(__name__)

# Add swagger description to api
app.add_api('openapi.yml', )

# Create app to run with wsgi server
application = app.app


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    It starts the Connexion Debug Server. It is not meant to be used for
    production, but only during the development.
    """
    logger.info("Starting the Connexion Debug Server")
    app.run(host='127.0.0.1')


if __name__ == "__main__":
    entrypoint()
