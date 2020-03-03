# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Preprocess the locally stored data and store them in the database.
"""
import glob
import logging
import multiprocessing
import os

import s5a

from emissionsapi.config import config
import emissionsapi.db

# Logger
logger = logging.getLogger(__name__)

# Path where to store the data
storage = config('storage') or 'data'

# Number of workers to preprocess
workers = config('workers') or 1


@emissionsapi.db.with_session
def list_ncfiles(session):
    """list all nc files in storage.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :return: Set of all unprocessed files
    :rtype: set
    """
    # Get all *.nc files as set
    files = set(glob.glob(os.path.join(storage, "*.nc")))
    logger.info('%s nc files to process', len(files))

    # Get all already processes files from the database as set
    processed_files = {
        os.path.join(storage, x.filename) for x in session.query(
            emissionsapi.db.File.filename)}
    logger.info('%s nc files already processed in total', len(processed_files))

    # Get difference
    files_to_process = files.difference(processed_files)
    logger.info('%s nc files still to process', len(files_to_process))

    return files_to_process


@emissionsapi.db.with_session
def write_to_database(session, data, filepath):
    """Write data to the PostGIS database

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param data: Data to add to the database
    :type data: pandas.core.frame.DataFrame
    :param filepath: Path to the file being imported
    :type filepath: str
    """
    # Insert data
    emissionsapi.db.insert_dataset(session, data)

    # Add file to database
    filename = os.path.basename(filepath)
    session.add(emissionsapi.db.File(filename=filename))

    # Invalidate cache
    timestamp = data.timestamp
    emissionsapi.db.Cache.invalidate(session, timestamp.min(), timestamp.max())

    # Commit the changes done in the session
    session.commit()


def preprocess_file(ncfile):
    '''Preprocess a single file and write it to the database

    :param ncfile: path to the ncfile to preprocess
    :type ncfile: str
    '''
    logger.info("Reading file '%s'", ncfile)
    scan = s5a.load_ncfile(ncfile)

    logger.info("Filtering %s points by quality of file '%s'", len(scan),
                ncfile)
    scan = s5a.filter_by_quality(scan)

    # Skip file if no points are present after filtering
    if len(scan) == 0:
        logger.warning("No points left after filtering of '%s'", ncfile)
        return

    logger.info("Apply H3 grid to '%s' points of file '%s'", len(scan), ncfile)
    scan = s5a.point_to_h3(scan, resolution=emissionsapi.db.resolution)
    scan = s5a.aggregate_h3(scan)
    scan = s5a.h3_to_point(scan)

    logger.info("Writing %s points from '%s' to database", len(scan), ncfile)
    write_to_database(scan, ncfile)

    logger.info("Finished writing points from '%s' to database", ncfile)


def main():
    """Entrypoint for running this as a module or from the binary.
    Triggers the preprocessing of the data.
    """
    # Iterate through all find nc files
    with multiprocessing.Pool(workers) as p:
        p.map(preprocess_file, sorted(list_ncfiles()))

    logger.info('Finished database import')


if __name__ == "__main__":
    main()
