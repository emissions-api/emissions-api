# emissions-api
The main repository for the Emissions API

## Prerequisites

* numpy
* gdal (C Library and Python bindings)
* [SQLAlchemy](https://sqlalchemy.org)
* [GeoAlchemy2](https://github.com/geoalchemy/geoalchemy2)
* [psycopg2](https://pypi.org/project/psycopg2/)
* [flask](https://flask.palletsprojects.com)
* [geojson](https://pypi.org/project/geojson/)

These can be installed by executing
```
pip install -r requirements.txt
```

### GDAL for Windows
Follow [this guide](https://sandbox.idre.ucla.edu/sandbox/tutorials/installing-gdal-for-windows) to install GDAL. For some reason pip have trouble to install the gdal package using pip. The easiest way to fix this is to manually install the wheel package from [lfd.uci.edu](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal). Note that the packages are unoffical windows binaries. Install the wheel package with
```
pip install <FILENAME>
```

## Installation

Note that you do not need to install this project to run the different parts of it. But you can install this tool and its binaries in your environment by executing

```
python setup.py install
```

## Execute

To execute the programs in this project run

* **download**: `python -m emissionsapi.download`
* **preprocess**: `python -m emissionsapi.preprocess`
* **web**: `python -m emissionsapi.web`

or execute the binaries after installation

* **download**: `emissionsapi-download`
* **preprocess**: `emissionsapi-preprocess`
* **web**: `emissionsapi-web`

## Database Setup

This project is using a [PostgreSQL](https://postgresql.org) database with the [PostGIS](https://postgis.net) extension.

There is a simple `docker-compose.yml` file to make it easier to setup a database for development.

You can also setup the database on your own.
