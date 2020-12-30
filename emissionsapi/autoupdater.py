import argparse
import datetime
import itertools
import logging
import multiprocessing
import os
import tempfile

import sentinel5dl

from emissionsapi import db, preprocess
from emissionsapi.config import config

# Logger
logger = logging.getLogger(__name__)

# Number of workers
workers = config('workers') or 1

# Earliest data to process
earliest_data = datetime.datetime.fromisoformat(
    config('earliest_data') or '2019-01-01')
# Latest data to process
latest_data = (
    datetime.datetime.fromisoformat(config('latest_data')) if config(
        'latest_data') else datetime.datetime.now()
)


def generate_intervals(start, end, days=5):
    '''Generator for intervals between start and end in days intervals.

    :param start: Starting datetime for the intervals.
    :type start: datetime.datetime
    :param end: End datetime for the intervals.
    :type end: datetime.datetime
    :param days: Days for each interval, defaults to 5
    :type days: int, optional
    :yield: Start and end date of the next interval.
    :rtype: tuple
    '''
    while start < end:
        interval_end = min(start + datetime.timedelta(days=days), end)
        yield start, interval_end
        start = interval_end


@db.with_session
def get_intervals_to_process(session, table, exclude_existing=True):
    '''Get all intervals with associated product files to process.
    Intervals with existing data will be skipped.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param table: Table to search for existing data.
    :type table: sqlalchemy.sql.schema.Table
    :param ignore_existing: Exclude existing intervals, defaults to True
    :type ignore_existing: bool, optional
    :return: Generator yielding the next interval.
    :rtype: generator
    '''
    # Ignore the existing data and return the full interval
    if not exclude_existing:
        return generate_intervals(earliest_data, latest_data)

    # No data present, so return the full interal
    first, last = db.get_data_range(session, table).first()
    if not first or not last:
        return generate_intervals(earliest_data, latest_data)

    # Configured earliest data is behind the current last.
    # We use earliest data as a hard limit for the starting date.
    if earliest_data > last:
        logger.warning(
            'The configured value for "earliest_data" (%s)'
            ' is after the last value in the database (%s) for %s.'
            ' Using "earliest data" as a hard limit for the starting date.',
            earliest_data, last, table)
        return generate_intervals(earliest_data, latest_data)

    # Return interval excluding existing data
    return itertools.chain(
        generate_intervals(earliest_data, first),
        generate_intervals(last, latest_data)
    )


@db.with_session
def single_file_update(session, product_file, directory, product):
    '''Download a single file, add it to the database
    and delete the file afterwards.

    :param session: SQLAlchemy Session
    :type session: sqlalchemy.orm.session.Session
    :param product_file: Metadata of a single product file
                         as received from sentinal5dl.search.
    :type product_file: dict
    :param directory: Directory to download file to.
    :type directory: string
    :param product: Type of the processed product.
                    An entry of emissionsapi.db.products.
    :type product: dict
    '''
    filename = f'{product_file["identifier"]}.nc'

    # Check if file already processed.
    if session.query(db.File)\
            .filter(db.File.filename == filename).first():
        logger.warning('File %s already processed', filename)
        return

    # Download file.
    logger.info('Downloading file %s', filename)
    sentinel5dl.download((product_file,), directory)

    # Read file into database.
    filepath = os.path.join(directory, filename)
    preprocess.preprocess_file(filepath, product['table'],
                               product['product'])

    # Remove the file again.
    logger.info('Removing %s', filepath)
    os.remove(filepath)


def main():
    '''Entrypoint for running this as a module or from the binary.
    Triggers the autoupdater.
    The autoupdater will download and add all missing product files
    of the configured products and the configured interval to the database.
    '''

    parser = argparse.ArgumentParser(
        description='Automagically update the database and '
                    'download and add all missing data to it.')
    parser.add_argument(
        '--ignore-existing', action='store_true',
        help='Ignore the already downloaded intervals.'
        'This is useful to fill the gaps between already downloaded data.')
    args = parser.parse_args()

    def init_worker():
        '''Clear session maker in fork, due to libpq
        '''
        db.__session__ = None

    # Generate temporary directory to work in.
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Iterate through products and import data not already present.
        for name, product in db.products.items():
            logger.info('Updating product %s', name)
            # Iterate through time intervals to update
            for begin_ts, end_ts in get_intervals_to_process(
                    product['table'], not args.ignore_existing):
                logger.info(
                    'Searching for downloadable product files'
                    ' between %s and %s', begin_ts, end_ts)

                # Search for product files from the ESA.
                result = sentinel5dl.search(
                    begin_ts=begin_ts, end_ts=end_ts,
                    processing_mode='Offline', processing_level='L2',
                    product=product['product_key'],
                )
                product_files = result.get('products', [])

                # Process product files
                logger.info(
                    'Processing found product files parallel with %d workers',
                    workers)
                with multiprocessing.Pool(workers, init_worker) as p:
                    p.starmap(
                        single_file_update,
                        zip(product_files, itertools.repeat(tmp_dir),
                            itertools.repeat(product))
                    )
            logger.info('Finished updating product %s', name)
    logger.info('Update complete')


if __name__ == '__main__':
    main()
