# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.


def bounding_box_to_wkt(lon1, lat1, lon2, lat2):
    """Convert a bounding box specified by its top-left and bottom-right
    coordinates to a wkt string defining a polygon.
    """
    return f'POLYGON(({lon1} {lat1},{lon1} {lat2},{lon2} {lat2},'\
           f'{lon2} {lat1},{lon1} {lat1}))'
