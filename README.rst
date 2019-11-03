
Emissions API
=============


.. image:: https://travis-ci.com/emissions-api/emissions-api.svg?branch=master
   :target: https://travis-ci.com/emissions-api/emissions-api
   :alt: Build Status


This is the main repository for the `Emissions API <https://emissions-api.org/>`_.

Prerequisites
-------------


* `SQLAlchemy <https://sqlalchemy.org>`_
* `GeoAlchemy2 <https://github.com/geoalchemy/geoalchemy2>`_
* `psycopg2 <https://pypi.org/project/psycopg2/>`_
* `Connexion <https://github.com/zalando/connexion>`_
* `swagger-ui-bundle <https://pypi.org/project/swagger-ui-bundle/>`_
* `geojson <https://pypi.org/project/geojson/>`_
* PyYAML
* `sentinel5dl <https://github.com/emissions-api/sentinel5dl>`_
* `sentinel5algorithms <https://github.com/emissions-api/sentinel5algorithms>`_
* `python-dateutil <https://pypi.org/project/python-dateutil/>`_

These can be installed by executing

.. code-block:: bash

   pip install -r requirements.txt

GDAL for Windows
^^^^^^^^^^^^^^^^

Follow `this guide <https://sandbox.idre.ucla.edu/sandbox/tutorials/installing-gdal-for-windows>`_
to install GDAL.
For some reason pip have trouble to install the gdal package using pip.
The easiest way to fix this is to manually install the wheel package from
`lfd.uci.edu <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal>`_.
Note that the packages are unoffical windows binaries.
Install the wheel package with

.. code-block:: bash

   pip install <FILENAME>

Installation
------------

Note that you do not need to install this project to run the different
parts of it.
But you can install this tool and its binaries in your environment by executing

.. code-block:: bash

   python setup.py install

Configuration
-------------

Emissions API will look for configuration files in the following order:


* ./emissionsapi.yml
* ~/emissionsapi.yml
* /etc/emissionsapi.yml

A configuration file template can be found at ``etc/emissionsapi.yml``.
To get started, just copy this to the main project directory and adjust the
values if the defaults do not work for you.

Documentation
-------------

To build the documentation you need to have ``sphinx`` and ``sphinx-rtd-theme``.

With that installed, simply run

.. code-block:: bash

   make -C docs clean html

Execute
-------

To execute the programs in this project run


* **download**\ : ``python -m emissionsapi.download``
* **preprocess**\ : ``python -m emissionsapi.preprocess``
* **web**\ : ``python -m emissionsapi.web``

or execute the binaries after installation


* **download**\ : ``emissionsapi-download``
* **preprocess**\ : ``emissionsapi-preprocess``
* **web**\ : ``emissionsapi-web``

Database Setup
--------------

This project is using a `PostgreSQL <https://postgresql.org>`_ database with the `PostGIS <https://postgis.net>`_ extension.
Attention: PostGIS is not yet available for the newest PostgreSQL v.12.

There is a simple ``docker-compose.yml`` file to make it easier to setup a
database for development.

You can also setup the database on your own.
