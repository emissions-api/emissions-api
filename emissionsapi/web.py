# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Web application to deliver the data stored in the database via an API to
the users.
"""
import connexion
import geojson

import emissionsapi.db
import emissionsapi.logger
from emissionsapi.country_bounding_boxes import country_bounding_boxes

# Logger
logger = emissionsapi.logger.getLogger('emission-api.web')


@emissionsapi.db.with_session
def get_data(session, country=None, geoframe=None):
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
    if geoframe is not None:
        try:
            lo1, lat1, lo2, lat2 = [float(x) for x in geoframe.split(',')]
        except ValueError:
            return 'Invalid geoparam', 400
    elif country is not None:
        if country not in country_bounding_boxes:
            return 'Unknown country code.', 400
        lo1, lat1, lo2, lat2 = country_bounding_boxes[country][1]
    else:
        return 'You must specify either geoframe or country.', 400

    # Init feature list
    features = []
    # Iterate through database query
    for feature in emissionsapi.db.get_points_in_rectangle(
            session, (lo1, lat1), (lo2, lat2)):
        # Create and append single features.
        features.append(geojson.Feature(
            geometry=geojson.Point((feature.longitude, feature.latitude)),
            properties={"carbonmonixide": feature.value}))
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
    app.run()


if __name__ == "__main__":
    entrypoint()
