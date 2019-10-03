"""Module to filter and download the data from the ESA and store it locally.
"""

from sentinelsat import SentinelAPI

from emissionsapi.config import config
from emissionsapi.country_bounding_boxes import country_bounding_boxes
import emissionsapi.logger

# Logger
logger = emissionsapi.logger.getLogger('emission-api.download')

storage = config('storage') or 'data'

# These credentials are provided publicly by ESA. There is no real user
# management and we can keep it like this as long as they do not introduce
# custom user accounts.
user = 's5pguest'
password = 's5pguest'
url = 'https://s5phub.copernicus.eu/dhus'

start_date = '20190910'
end_date = '20190911'


def bounding_box_to_wkt(lon1, lat1, lon2, lat2):
    """Convert a bounding box specified by its top-left and bottom-right
    coordinates to a wkt string defining a polygon.
    """
    return f'POLYGON(({lon1} {lat1},{lon1} {lat2},{lon2} {lat2},'\
           f'{lon2} {lat1},{lon1} {lat1}))'


def download():
    """Download data files from ESA and store them in the configured storage
    directory.
    """
    wkt = bounding_box_to_wkt(*country_bounding_boxes['DE'][1])

    # query api for available products
    api = SentinelAPI(user, password, url)
    products = api.query(area=wkt, date=(start_date, end_date))
    products_df = api.to_dataframe(products)

    # filter only one product of CO
    where = products_df.producttypedescription == 'Carbon Monoxide'
    one_id = products_df.uuid[where][0]

    # download one product
    api.download(one_id, directory_path=storage)


if __name__ == "__main__":
    download()
