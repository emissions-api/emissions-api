# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Preprocess the locally stored data and store them in the database.
"""
import logging
import os

import s5a

from emissionsapi.config import config
import emissionsapi.db

# Logger
logger = logging.getLogger(__name__)

# Path where to store the data
storage = config('storage') or 'data'


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


@emissionsapi.db.with_session
def write_to_database(session, data):
    """Write data to the PostGIS database

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param data: Data to add to the database
    :type data: emissionsapi.preprocess.Scan
    """
    # Iterate through the points of the Scan object
    points = []
    for point in data.points:
        points.append({
            'value': point.value,
            'longitude': point.longitude,
            'latitude': point.latitude,
            'timestamp': point.timestamp
        })
    # Add all points
    if points:
        emissionsapi.db.insert(session, points)
    # Add file to database
    filename = os.path.basename(data.filepath)
    session.add(emissionsapi.db.File(filename=filename))
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
        logger.info(f"Read file '{ncfile}'")
        scan = s5a.Scan(ncfile)
        logger.info(f"Filter {scan.len()} points by quality")
        # filter data for quality >=50
        scan.filter_by_quality(50)
        logger.info(f"Write {scan.len()} points to database")
        # Write the filtered data to the database
        write_to_database(scan)
    pass


if __name__ == "__main__":
    entrypoint()
