import os
from os.path import isfile, join

PATH = 'data'

def list_ncfiles():
    for f in os.listdir(PATH):
        filepath = os.path.join(PATH, f)
        if os.path.isfile(filepath) and filepath.endswith('.nc'):
            yield filepath

def read_file(ncfile):
    return {}

def filter_data(data):
    return data

def write_to_database(data):
    pass

def entrypoint():
    for ncfile in list_ncfiles():
        print(ncfile)
        data = read_file(ncfile)
        data = filter_data(data)
        write_to_database(data)
    pass


if __name__ == "__main__":
    entrypoint()
