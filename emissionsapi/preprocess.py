"""Preprocess the locally stored data and store them in the Database.
"""
import os

import gdal
import numpy

import emissionsapi.db
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.preprocess')

# Path where to store the data
PATH = 'data'

# Specify the layer name to read
LAYER_NAME = '//PRODUCT/carbonmonoxide_total_column'
LONGITUDE_NAME = '//PRODUCT/longitude'
LATITUDE_NAME = '//PRODUCT/latitude'
QA_VALUE_NAME = '//PRODUCT/qa_value'


class Scan():
    """Object to hold the arrays from a nc file.
    """
    data = []
    longitude = []
    latitude = []
    quality = []


def list_ncfiles():
    """Generator yielding all nc files.
    """
    # Iterate through the files and directories in PATH
    for f in os.listdir(PATH):
        # Join directoriy and filename
        filepath = os.path.join(PATH, f)
        # yield file ending with '.nc'
        if os.path.isfile(filepath) and filepath.endswith('.nc'):
            yield filepath


def read_file(ncfile):
    """Read nc file, parse it using gdal and return its result as a
    Scan Object.

    :param ncfile: filename of the nc file
    :type ncfile: string
    :return: scan object
    :rtype: emissionsapi.preprocess.Scan
    """
    # Create a new Scan Object
    scan = Scan()

    # Get data, longitude, latitude and qa from nc file and
    # Create flattend numpy array from data
    ds = gdal.Open(f'HDF5:{ncfile}:{LAYER_NAME}')
    scan.data = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LONGITUDE_NAME}')
    scan.longitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LATITUDE_NAME}')
    scan.latitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{QA_VALUE_NAME}')
    scan.quality = numpy.ndarray.flatten(ds.ReadAsArray())
    # Return scan object
    return scan


def filter_data(data):
    """Filter data before processing them further.

    :param data: scan object with data
    :type data: emissionsapi.preprocess.Scan
    :return: scan object with filtered data
    :rtype: emissionsapi.preprocess.Scan
    """
    return data


@emissionsapi.db.with_session
def write_to_database(session, data):
    """Write data to the PostGIS database

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param data: Data to add to the database
    :type data: emissionsapi.preprocess.Scan
    """
    # Iterate through the data of the Scan object
    for index, d in enumerate(data.data):
        # Add new Carbonmonoxide object to the session
        session.add(
            emissionsapi.db.Carbonmonoxide(
                longitude=float(data.longitude[index]),
                latitude=float(data.latitude[index]),
                value=float(d),
            )
        )
    # Commit the changes done in the session
    session.commit()


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    Triggers the preprocessing of the data.
    """
    # Iterate through all find nc files
    for ncfile in list_ncfiles():
        print(ncfile)
        # Read data from nc file
        data = read_file(ncfile)
        print(data)
        # filter data
        data = filter_data(data)
        # Write the filtered data to the database
        write_to_database(data)
    pass


if __name__ == "__main__":
    entrypoint()
