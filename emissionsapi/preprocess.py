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
        if session.query(emissionsapi.db.File)\
                  .filter(emissionsapi.db.File.filename == f).count():
            logger.info("Skipping %s", f)
            continue
        # Join directory and filename
        filepath = os.path.join(storage, f)
        # yield file ending with '.nc'
        if os.path.isfile(filepath) and filepath.endswith('.nc'):
            yield filepath


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


def main():
    """Entrypoint for running this as a module or from the binary.
    Triggers the preprocessing of the data.
    """
    # Iterate through all find nc files
    for ncfile in list_ncfiles():
        logger.info("Reading file '%s'", ncfile)
        scan = s5a.load_ncfile(ncfile)

        logger.info("Filtering %s points by quality", scan.size)
        scan = s5a.filter_by_quality(scan)

        logger.info('Writing %s points to database', scan.size)
        write_to_database(scan, ncfile)

        logger.info('Finished database import')


if __name__ == "__main__":
    main()
