Running Tests
=============
Users can run the code below for testing this project.
.. code-block:: python

    docker-compose -f docker-compose.local.yml run web python manage.py test

Running Tests with coverage
---------------------------
.. code-block:: python

    docker-compose -f docker-compose.local.yml run web coverage run -m pytest

Reporting test coverage
-----------------------

Generate coverage report:
.. code-block:: python
    "docker-compose -f docker-compose.local.yml run web coverage report -m --skip-covered"

Exporting test coverage
-----------------------

If you want to view coverage in your editor using, for example, VSCode's Coverage Gutters plugin, export the coverage report to a supported format:

.. code-block:: python

    docker-compose -f docker-compose.local.yml run web coverage xml -o coverage.xml

Export the coverage report with a supported format
