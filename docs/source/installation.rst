Installation
============

Linux (Fedora)
--------------

*Tested on Fedora 30*

The Emissions API relies on a few C libraries. The easiest way to get those as
well as their python bindings is to use dnf and get them from the system
repositories::

   %> dnf install python3-gdal python3-psycopg2 python3-pycurl python3-numpy

All other dependencies can easily be installed using pip. For this we use a
virtual environment to avoid installing local dependencies globally in the
system. In the project folder, create and activate the virtual environment
allowing access to system packages as well::

   %> python3 -m venv --system-site-packages venv
   %> . ./venv/bin/activate

Remember to always use the environment while working on the
project since only this will give you access to the additional local libraries
you installed.

Finally, install all necessary requirements using pip::

   (venv) %> pip install -r requirements.txt

You can now use the Emissions API. E.g. launch the web interface by running::

   (venv) %> python -m emissionsapi.web
