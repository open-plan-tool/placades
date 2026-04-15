======================================
Easy Energy System Planning - eesyPlan
======================================

The Easy Energy System Planning library is part of the `oemof <https://github.com/oemof/>`_ family.

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |github-actions| |codecov_stable| |coveralls|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations| |commits-since|
.. |docs| image:: https://readthedocs.org/projects/oemof-eesyplan/badge/?style=flat
    :target: https://oemof-eesyplan.readthedocs.io/en/latest/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/oemof/oemof-eesyplan/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/oemof/oemof-eesyplan/actions

.. |coveralls| image:: https://coveralls.io/repos/github/oemof/oemof-eesyplan/badge.svg?branch=main
    :alt: Coveralls coverage status
    :target: https://coveralls.io/github/oemof/oemof-eesyplan?branch=main

.. |codecov_stable| image:: https://codecov.io/gh/oemof/oemof-eesyplan/branch/main/graph/badge.svg
   :alt: Codecov Coverage Status
   :target: https://codecov.io/gh/oemof/oemof-eesyplan

.. |version| image:: https://img.shields.io/pypi/v/oemof.eesyplan.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/oemof-eesyplan

.. |wheel| image:: https://img.shields.io/pypi/wheel/oemof.eesyplan.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/oemof-eesyplan

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/oemof.eesyplan.svg
    :alt: Supported versions
    :target: https://pypi.org/project/oemof-eesyplan

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/oemof.eesyplan.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/oemof-eesyplan

.. |commits-since| image:: https://img.shields.io/github/commits-since/oemof/oemof-eesyplan/v0.0.1.svg
    :alt: Commits since latest release
    :target: https://github.com/oemof/oemof-eesyplan/compare/v0.0.1...main



.. end-badges

SHORT DESCRIPTION

* Free software: MIT license

Installation
============

::

    pip install oemof-eesyplan

You can also install the in-development version with::

    pip install https://github.com/oemof/oemof-eesyplan/archive/main.zip


Documentation
=============

https://oemof-eesyplan.readthedocs.io/en/latest/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
