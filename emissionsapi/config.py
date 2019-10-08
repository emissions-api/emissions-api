# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
'''
Load and handle Emission API configuration.
'''

import yaml
import os

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
    if os.path.isfile('~/emissionsapi.yml'):
        return '~/emissionsapi.yml'
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
    return cfg


def config(key=None):
    '''Get a specific configuration value or the whole configuration, loading
    the configuration file if it was not before.

    :param key: optional configuration key to return
    :type key: string
    :return: dictionary containing the configuration or configuration value
    '''
    cfg = __config or update_configuration()
    return cfg.get(key) if key else cfg
