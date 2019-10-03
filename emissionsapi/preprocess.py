"""Preprocess the locally stored data and store them in the Database.
"""
import os

import gdal
import iso8601
import numpy

from datetime import timedelta

from emissionsapi.config import config
import emissionsapi.db
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.preprocess')

# Path where to store the data
storage = config('storage') or 'data'

# Specify the layer name to read
LAYER_NAME = '//PRODUCT/carbonmonoxide_total_column'
LONGITUDE_NAME = '//PRODUCT/longitude'
LATITUDE_NAME = '//PRODUCT/latitude'
QA_VALUE_NAME = '//PRODUCT/qa_value'
DELTA_TIME_NAME = '//PRODUCT/delta_time'


class Scan():
    """Object to hold arrays from an nc file.
    """
    data = []
    longitude = []
    latitude = []
    quality = []
    timestamps = []


def list_ncfiles():
    """Generator yielding all nc files in download path.
    """
    # Iterate through the files and directories in storage path
    for f in os.listdir(storage):
        # Join directoriy and filename
        filepath = os.path.join(storage, f)
        # yield file ending with '.nc'
        if os.path.isfile(filepath) and filepath.endswith('.nc'):
            yield filepath


def read_file(ncfile):
    """Read nc file, parse it using GDAL and return its result as a
    Scan object.

    :param ncfile: filename of the nc file
    :type ncfile: string
    :return: scan object
    :rtype: emissionsapi.preprocess.Scan
    """
    # Create a new Scan Object
    scan = Scan()

    # Get data, longitude, latitude and quality from nc file and
    # create flattened numpy array from data
    ds = gdal.Open(f'HDF5:{ncfile}:{LAYER_NAME}')
    scan.data = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LONGITUDE_NAME}')
    scan.longitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LATITUDE_NAME}')
    scan.latitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{QA_VALUE_NAME}')
    scan.quality = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{DELTA_TIME_NAME}')
    deltatime = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'{ncfile}')
    meta_data = ds.GetMetadata_Dict()

    # Get time reference from the meta data.
    # Seems like there are named differently in the different gdal versions.
    time_reference = iso8601.parse_date(
        meta_data.get('NC_GLOBAL#time_reference') or
        meta_data['time_reference'])
    timestamps = []
    for dt in deltatime:
        timestamps.append(time_reference + timedelta(milliseconds=dt.item()))
    scan.timestamps = numpy.array(timestamps)

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
    # Initialize object list
    objects = []
    # Iterate through the data of the Scan object
    for index, d in enumerate(data.data):
        objects.append(
            emissionsapi.db.Carbonmonoxide(
                longitude=float(data.longitude[index]),
                latitude=float(data.latitude[index]),
                value=float(d),
            )
        )
    # Add new carbon monoxide object to the session
    session.bulk_save_objects(objects)
    # Commit the changes done in the session
    session.commit()


def entrypoint():
    """Entrypoint for running this as a module or from the binary.
    Triggers the preprocessing of the data.
    """
    # Iterate through all find nc files
    for ncfile in list_ncfiles():
        logger.info(f"Pre-process '{ncfile}'")
        # Read data from nc file
        data = read_file(ncfile)
        # filter data
        data = filter_data(data)
        # Write the filtered data to the database
        write_to_database(data)
    pass


if __name__ == "__main__":
    entrypoint()
