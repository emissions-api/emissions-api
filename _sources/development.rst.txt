Development
===========

Dependencies
------------

For dependencies in this project we are following the guidelines from the `Python Packaging Guide`_.

So in detail we are using the `install_requires` in the setup.py_ to specify a list of dependencies this *project minimally needs to run correctly*.
Whereas in the requirements.txt_ we define the *complete Python environment* with *pinned versions for the purpose of achieving repeatable installations*.
So the requirements.txt_ also includes the dependencies of the dependencies and the tools we are using for our setup.

So what has to be done, if you want to add a new dependency?
Well simply try to follow the guideline in the `Python Packaging Guide`_.

Also if you want to update the requirements.txt_ and don't know how, the following steps might be handy.

.. code-block:: bash

    # Create temporary virtual environment and install the current requirements
    python3 -m venv /tmp/env
    . /tmp/env/bin/activate
    pip install -r requirements.txt
    # Install your new fancy package
    pip install my-fancy-package
    # Update the whole list of dependencies
    pip freeze > requirements.txt

.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _Python Packaging Guide: https://packaging.python.org/discussions/install-requires-vs-requirements/
.. _setup.py: https://github.com/emissions-api/emissions-api/blob/master/setup.py
.. _requirements.txt: https://github.com/emissions-api/emissions-api/blob/master/requirements.txt
