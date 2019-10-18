# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Preprocess the locally stored data and store them in the database.
"""
import logging
import os

import gdal
import iso8601
import numpy

from datetime import timedelta

from emissionsapi.config import config
import emissionsapi.db

# Logger
logger = logging.getLogger(__name__)

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
    filename = None
    data = None
    longitude = None
    latitude = None
    quality = None
    timestamps = None


@emissionsapi.db.with_session
def list_ncfiles(session):
    """Generator yielding all nc files in download path.
    """
    # Iterate through the files and directories in storage path
    for f in os.listdir(storage):
        # Check if file was already added
        filename = session.query(emissionsapi.db.File).filter(
            emissionsapi.db.File.filename == f).first()
        if filename is not None:
            logger.info(f"Skipping {f}")
            continue
        # Join directory and filename
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

    # Store filename
    scan.filename = os.path.basename(ncfile)

    # Get data, longitude, latitude and quality from nc file and
    # create flattened numpy array from data
    ds = gdal.Open(f'HDF5:{ncfile}:{LAYER_NAME}')
    scan.data = ds.ReadAsArray()

    ds = gdal.Open(f'HDF5:{ncfile}:{LONGITUDE_NAME}')
    scan.longitude = ds.ReadAsArray()

    ds = gdal.Open(f'HDF5:{ncfile}:{LATITUDE_NAME}')
    scan.latitude = ds.ReadAsArray()

    ds = gdal.Open(f'HDF5:{ncfile}:{QA_VALUE_NAME}')
    scan.quality = ds.ReadAsArray()

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


def filter_data(data, qa_percent):
    """Filter data before processing them further
    All corresponding values in the Scan objects are set to NaN
    if the quality requirement is not met

    :param data: scan object with data
    :type data: emissionsapi.preprocess.Scan
    :param qa_percent: quality to filter in percent
    :type qa_percent: int
    :return: scan object with filtered data
    :rtype: emissionsapi.preprocess.Scan
    """

    # cast Scan objects to float because numpy.nan is float
    data.quality = data.quality.astype('float')
    data.data = data.data.astype('float')
    data.longitude = data.longitude.astype('float')
    data.latitude = data.latitude.astype('float')

    # set all corresponding Scan object values to numpy.nan
    # if the quality value is too low
    data.data[data.quality < qa_percent] = numpy.nan
    data.longitude[data.quality < qa_percent] = numpy.nan
    data.latitude[data.quality < qa_percent] = numpy.nan

    # at least set all too low quality values to numpy.nan
    data.quality[data.quality < qa_percent] = numpy.nan

    # return data
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
    shape = data.data.shape
    for i in range(shape[0]):
        for j in range(shape[1]):

            # Check if any of the data objects are set to NotANumber with
            # filter_data() to skip writing them into the database
            if (not(numpy.isnan(data.longitude[i, j]) or
                    numpy.isnan(data.latitude[i, j]) or
                    numpy.isnan(data.data[i, j]))):

                # Add new carbon monoxide object to the session
                session.add(
                    emissionsapi.db.Carbonmonoxide(
                        longitude=float(data.longitude[i, j]),
                        latitude=float(data.latitude[i, j]),
                        value=float(data.data[i, j]),
                        timestamp=data.timestamps[i],
                    )
                )

    session.add(emissionsapi.db.File(filename=data.filename))
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
        # filter data for quality >=50
        data = filter_data(data, 50)
        # Write the filtered data to the database
        write_to_database(data)
    pass


if __name__ == "__main__":
    entrypoint()