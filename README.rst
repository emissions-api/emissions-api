Emissions API
=============

.. image:: https://img.shields.io/travis/com/emissions-api/emissions-api?label=Docs
   :target: https://docs.emissions-api.org
   :alt: Documentation Status
.. image:: https://img.shields.io/circleci/build/github/emissions-api/emissions-api?label=Build
   :target: https://circleci.com/gh/emissions-api/emissions-api
   :alt: Build Status

This is the main repository for the `Emissions API <https://emissions-api.org/>`_.

If you just want to use Emissions API as a service, take a look at our `API documentation <https://api.emissions-api.org/>`_
or visit our `website <https://emissions-api.org/>`_ for additional information and examples.

Below you will find a small introduction about setting the services in this repository up for development.

If you want to take a deeper dive into this, you can take a look at the `documentation <https://docs.emissions-api.org/>`_,
visit the `issues <https://github.com/emissions-api/emissions-api/issues>`_
or take a look into the `libraries and tools <https://github.com/emissions-api>`_ we created around this project.

Installation
------------

To install the requirements execute

.. code-block:: bash

   pip install -r requirements.txt

You might have to explicitly deal with C-dependencies like ``psycopg2`` yourself,
One way to do this is to use your corresponding system packages.

After that you can run the different services using

* **download**\ : ``python -m emissionsapi.download``
* **preprocess**\ : ``python -m emissionsapi.preprocess``
* **web**\ : ``python -m emissionsapi.web``

Configuration
-------------

Emissions API will look for configuration files in the following order:

* ``./emissionsapi.yml``
* ``~/emissionsapi.yml``
* ``/etc/emissionsapi.yml``

A configuration file template can be found at ``etc/emissionsapi.yml``.
To get started, just copy this to the main project directory and adjust the
values if the defaults do not work for you.

Database Setup
--------------

This project is using a `PostgreSQL <https://postgresql.org>`_ database with the `PostGIS <https://postgis.net>`_ extension.

There is a simple ``docker-compose.yml`` file to make it easier to setup a
database for development.
