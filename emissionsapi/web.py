"""Web Application to deliver the data stored in the database via an API to
the users.
"""
from flask import Flask, request, Response
import geojson


import emissionsapi.db
import emissionsapi.logger
from emissionsapi.country_bounding_boxes import country_bounding_boxes

# Logger
logger = emissionsapi.logger.getLogger('emission-api.web')

# Flask Web App
app = Flask(__name__)


@app.route('/api/v1/geo.json')
@emissionsapi.db.with_session
def get_data(session):
    """Get data in GeoJSON format.

    URL parameters
    ,,,,,,,,,,,,,,

    You must use exactly one of these URL parameters.

    * 'geoparam' expects 4 comma separated float values representing the
      longitude and latitude of the upper left and lower right points of a
      rectangle.
    * `country` expects a two character country code which is mapped to a
      minimal bounding box of that country as an alternative to specifying that
      rectangle manually.

    Response
    ,,,,,,,,

    The Response contains all known points located within the specified
    rectangle contained in a GeoJSON feature collection.

    Example
    ,,,,,,,

    You can try this with::

        curl http://127.0.0.1:5000/api/v1/geo.json?geoparam=15,45,20,40

    :param session: SQLAlchemy session
    :type session: sqlalchemy.orm.session.Session
    :return: GeoJSON response containing a feature collection
    :rtype: flask.Response
    """
    # Get and parse URL parameter
    geoparam = request.args.get('geoparam')
    country = request.args.get('country')
    if geoparam is not None:
        try:
            lo1, lat1, lo2, lat2 = [float(x) for x in geoparam.split(',')]
        except ValueError:
            return 'Invalid geoparam', 400
    elif country is not None:
        if country not in country_bounding_boxes:
            return 'Unknown country code.', 400
        lo1, lat1, lo2, lat2 = country_bounding_boxes[country][1]
    else:
        return 'You must specify either geoparam or country.', 400

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
    return Response(
        geojson.dumps(feature_collection, sort_keys=True),
        mimetype='application/json')


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    It starts the Flask Debug Server. It is not meant to be used for
    production, but only during the development.
    """
    logger.info("Starting the Flask Debug Server")
    app.run()


if __name__ == "__main__":
    entrypoint()
