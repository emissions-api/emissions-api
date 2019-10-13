# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Module to filter and download the data from the ESA and store it locally.
"""
import os

import logging
import sentinel5dl

from emissionsapi.config import config
from emissionsapi.country_bounding_boxes import country_bounding_boxes
from emissionsapi.utils import bounding_box_to_wkt

# Logger
logger = logging.getLogger(__name__)

# Configure logger for sentinel5dl
logging.basicConfig()
download_logger = logging.getLogger(sentinel5dl.__name__)
download_logger.setLevel(logger.getEffectiveLevel())

product = 'L2__CO____'
processing_level = 'L2'


def download():
    """Download data files from ESA and store them in the configured storage
    directory.
    """

    # Load download configuration
    storage = config('storage') or 'data'
    date_begin = config('download', 'date', 'begin')\
        or '2019-09-10T00:00:00.000Z'
    date_end = config('download', 'date', 'end') or '2019-09-11T00:00:00.000Z'
    countries = config('download', 'country') or ['DE']

    # create storage folder if not existing
    os.makedirs(storage, exist_ok=True)

    for country in countries:
        wkt = bounding_box_to_wkt(*country_bounding_boxes[country][1])

        # Search for data matching the parameter
        logger.info(f'Looking for products in country {country}')
        result = sentinel5dl.search(
                wkt,
                begin_ts=date_begin,
                end_ts=date_end,
                product=product,
                processing_level=processing_level)
        logger.info('Found {0} products'.format(len(result.get('products'))))

        # Download data
        sentinel5dl.download(result.get('products'), output_dir=storage)


if __name__ == "__main__":
    download()
