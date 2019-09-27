from flask import Flask, jsonify

# Flask Web App
app = Flask(__name__)


@app.route('/api/v1/geo.json')
def get_data():
    return jsonify({})


def entrypoint():
    # Run the Flask Debug Server.
    # Not for production!
    app.run()


if __name__ == "__main__":
    entrypoint()
