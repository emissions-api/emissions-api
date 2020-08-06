Installation
============

Linux (Fedora 31)
-----------------

Emissions API relies on a few C libraries.
To be able to build the python bindings for these libraries, we first need to install a few development libraries::

   %> dnf install gcc python3-devel libpq-devel

All other dependencies can easily be installed using pip.
For this we use a virtual environment to avoid installing local dependencies globally in the system.
In the project folder, create and activate the virtual environment::

   %> python3 -m venv venv
   %> . ./venv/bin/activate

Remember to always use the environment while working on the project.
Only this will give you access to the additional local libraries you installed.

Finally, install all necessary requirements using pip::

   (venv) %> PYCURL_SSL_LIBRARY=openssl pip install -r requirements.txt

You can now use the Emissions API. E.g. launch the web interface by running::

   (venv) %> python -m emissionsapi.web
