# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
"""Module to filter and download the data from the ESA and store it locally.
"""
import os

import sentinel5dl

from emissionsapi.config import config
from emissionsapi.country_bounding_boxes import country_bounding_boxes
from emissionsapi.utils import bounding_box_to_wkt
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.download')

storage = config('storage') or 'data'

start_date = '2019-09-10T00:00:00.000Z'
end_date = '2019-09-11T00:00:00.000Z'
product = 'L2__CO____'
processing_level = 'L2'


def download():
    """Download data files from ESA and store them in the configured storage
    directory.
    """
    wkt = bounding_box_to_wkt(*country_bounding_boxes['DE'][1])

    # create storage folder if not existing
    os.makedirs(storage, exist_ok=True)

    # Search for data matching the parameter
    result = sentinel5dl.search(
            wkt,
            begin_ts=start_date,
            end_ts=end_date,
            product=product,
            processing_level=processing_level,
            logger_fn=logger.info)
    logger.info('Found {0} products'.format(len(result.get('products'))))

    # Download data
    sentinel5dl.download(
        result.get('products'), output_dir=storage, logger_fn=logger.info)


if __name__ == "__main__":
    download()
