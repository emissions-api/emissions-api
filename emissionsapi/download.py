"""Module to filter and download the data from the ESA and store it locally.
"""

import os
import urllib3

from emissionsapi.config import config
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.download')

storage = config('storage') or 'data'

def download():
    os.makedirs(storage, exist_ok=True)

    # TODO: Replace this with sentinalsat
    filename = 'S5P_NRTI_L2__CO_____20190921T122303_20190921T122803_'\
        + '10046_01_010302_20190921T130405.nc'
    url = 'https://data.lkiesow.io/emissions-api/' + filename
    connection_pool = urllib3.PoolManager()
    resp = connection_pool.request('GET', url)
    with open('data/' + filename, 'wb') as f:
        f.write(resp.data)
    resp.release_conn()


if __name__ == "__main__":
    download()
