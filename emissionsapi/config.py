# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
'''
Load and handle Emissions API configuration.
'''

import logging
import os
import yaml

# Logger
logger = logging.getLogger(__name__)

__config = {}


def configuration_file():
    '''Find the best match for the configuration file.  The configuration file
    locations taken into consideration are (in this particular order):

    - ``./emissionsapi.yml``
    - ``~/emissionsapi.yml``
    - ``/etc/emissionsapi.yml``

    :return: configuration file name or None
    '''
    if os.path.isfile('./emissionsapi.yml'):
        return './emissionsapi.yml'
    expanded_file = os.path.expanduser('~/emissionsapi.yml')
    if os.path.isfile(expanded_file):
        return expanded_file
    if os.path.isfile('/etc/emissionsapi.yml'):
        return '/etc/emissionsapi.yml'


def update_configuration():
    '''Update configuration.
    '''
    cfgfile = configuration_file()
    if not cfgfile:
        return {}
    with open(cfgfile, 'r') as f:
        cfg = yaml.safe_load(f)
    globals()['__config'] = cfg

    # update logger
    loglevel = cfg.get('loglevel', 'INFO').upper()
    logging.root.setLevel(loglevel)
    logger.info('Log level set to %s', loglevel)

    return cfg


def config(*args):
    '''Get a specific configuration value or the whole configuration, loading
    the configuration file if it was not before.

    :param key: optional configuration key to return
    :type key: string
    :return: dictionary containing the configuration or configuration value
    '''
    cfg = __config or update_configuration()
    for key in args:
        if cfg is None:
            return
        cfg = cfg.get(key)
    return cfg
