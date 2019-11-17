"""
Emissions API
~~~~~~~~~~~~~

Emissions API’s mission is to provide easy access to European Space Agency’s
Sentinel-5P satellite data without the need of being an expert in satellite
data analysis and without having to process terabytes of data.

:copyright: 2019, The Emissions API Developers
:url: https://emissions-api.org
:license: MIT
"""
# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
import logging

from emissionsapi.config import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=config('loglevel') or logging.INFO,
)
logging.debug('Log level set to: %s', logging.getLogger().getEffectiveLevel())
