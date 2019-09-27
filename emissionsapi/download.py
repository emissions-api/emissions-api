"""Module to filter and download the data from the ESA and store it locally.
"""

import os

import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.download')


def download():
    os.makedirs('data')


if __name__ == "__main__":
    download()
