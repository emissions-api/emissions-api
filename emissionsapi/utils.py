# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.


class RESTParamError(ValueError):
    """User-specific exception, used in
    :func:`~emissionsapi.utils.polygon_to_wkt`.
    """
    pass


def bounding_box_to_wkt(lon1, lat1, lon2, lat2):
    """Convert a bounding box specified by its top-left and bottom-right
    coordinates to a wkt string defining a polygon.
    """
    return f'POLYGON(({lon1} {lat1},{lon1} {lat2},{lon2} {lat2},'\
           f'{lon2} {lat1},{lon1} {lat1}))'


def polygon_to_wkt(polygon):
    """Converts a list of points to a WKT string defining a polygon.

    :param polygon: List of values with every pair of values representing a
     consecutive vertex of the polygon.
    :type polygon: list
    :return: WKT defining the polygon.
    :rtype: str
    """
    # check if element number is even
    if len(polygon) % 2 != 0:
        raise RESTParamError('Number of elements has to be even')

    # check if polygon is closed
    if polygon[-2:] != polygon[:2]:
        # close polygon by adding the first lon/lat pair at the end of the list
        polygon.extend(polygon[0:2])

    # check if we have at least 3 (+1 to close the polygon) coordinate points
    if len(polygon) < 8:
        raise RESTParamError('At least 4 points are needed to define a '
                             'polygon')

    # create list with x-y points as strings
    points = []
    for index in range(0, len(polygon), 2):
        points.append(f'{polygon[index]} {polygon[index+1]}')

    # return string with points, joined by ','
    return f'POLYGON(({",".join(points)}))'
