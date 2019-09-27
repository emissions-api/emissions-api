from setuptools import setup, find_packages

setup(
    name='emissions-api',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'emissionsapi-download=emissionsapi.download:entrypoint',
            'emissionsapi-preprocess=emissionsapi.preprocess:entrypoint',
            'emissionsapi-web=emissionsapi.web:entrypoint',
        ],
    },
)
