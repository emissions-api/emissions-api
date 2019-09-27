import os
import gdal
import numpy

PATH = 'data'

# Specify the layer name to read
LAYER_NAME = '//PRODUCT/carbonmonoxide_total_column'
LONGITUDE_NAME = '//PRODUCT/longitude'
LATITUDE_NAME = '//PRODUCT/latitude'
QA_VALUE_NAME = '//PRODUCT/qa_value'

class Scan():
    data = []
    longitude = []
    latitude = []
    quality = []


def list_ncfiles():
    for f in os.listdir(PATH):
        filepath = os.path.join(PATH, f)
        if os.path.isfile(filepath) and filepath.endswith('.nc'):
            yield filepath


def read_file(ncfile):
    scan = Scan()
    ds = gdal.Open(f'HDF5:{ncfile}:{LAYER_NAME}')
    scan.data = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LONGITUDE_NAME}')
    scan.longitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{LATITUDE_NAME}')
    scan.latitude = numpy.ndarray.flatten(ds.ReadAsArray())

    ds = gdal.Open(f'HDF5:{ncfile}:{QA_VALUE_NAME}')
    scan.quality = numpy.ndarray.flatten(ds.ReadAsArray())

    return scan


def filter_data(data):
    return data

def write_to_database(data):
    pass

def entrypoint():
    for ncfile in list_ncfiles():
        print(ncfile)
        data = read_file(ncfile)
        print(data)
        data = filter_data(data)
        write_to_database(data)
    pass


if __name__ == "__main__":
    entrypoint()
