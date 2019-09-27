"""Web Application to deliver the data stored in the database via an API to
the users.
"""
from flask import Flask, jsonify

import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.web')

# Flask Web App
app = Flask(__name__)


@app.route('/api/v1/geo.json')
def get_data():
    return jsonify({})


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    It starts the Flask Debug Server. It is not meant to be used for
    production, but only during the development.
    """
    logger.info("Starting the Flask Debug Server")
    app.run()


if __name__ == "__main__":
    entrypoint()
