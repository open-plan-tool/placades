========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |github-actions|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations| |commits-since|
.. |docs| image:: https://readthedocs.org/projects/placades/badge/?style=flat
    :target: https://readthedocs.org/projects/placades/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/open-plan-tool/placades/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/open-plan-tool/placades/actions

.. |version| image:: https://img.shields.io/pypi/v/placades.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/placades

.. |wheel| image:: https://img.shields.io/pypi/wheel/placades.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/placades

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/placades.svg
    :alt: Supported versions
    :target: https://pypi.org/project/placades

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/placades.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/placades

.. |commits-since| image:: https://img.shields.io/github/commits-since/open-plan-tool/placades/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/open-plan-tool/placades/compare/v0.0.0...main



.. end-badges

SHORT DESCRIPTION

* Free software: MIT license

Installation
============

::

    pip install placades

You can also install the in-development version with::

    pip install https://github.com/open-plan-tool/placades/archive/main.zip


Documentation
=============


https://placades.readthedocs.io/


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
