===============================
InstrumentKit Development Guide
===============================

.. toctree::
    :maxdepth: 2

    design_philosophy
    code_style
    testing
    util_fns

Introduction
============

This guide details how InstrumentKit is laid out from a developer's point of
view, how to add instruments, communication methods and unit tests.

Getting Started
===============

To get started with development for InstrumentKit, a few additional supporting
packages must be installed. The core development packages can be found in
the supporting requirements file named ``dev-requirements.txt``. These will
allow you to run the tests and check that all your code changes follow our
linting rules (through `pylint`).

Required Development Dependencies
---------------------------------

Using ``pip``, these requirements can be obtained automatically by using the
provided ``dev-requirements.txt``::

$ pip install -r dev-requirements.txt

Optional Development Dependencies
---------------------------------

In addition to the required dev dependencies, there are optional ones.
The package `tox`_ allows you to quickly run the tests against all supported
versions of Python, assuming you have them installed. It is suggested that you
install ``tox`` and regularly run your tests by calling the simple command::

$ tox

More details on running tests can be found in :ref:`testing`.

.. _tox: https://tox.readthedocs.org/en/latest/

Contributing Code
=================

We love getting new instruments and new functionality! When sending
in pull requests, however, it helps us out a lot in maintaining InstrumentKit
as a usable library if you can do a couple things for us with your submission:

- Make sure code follows `PEP 8`_ as best as possible. This helps keep the
  code readable and maintainable.
- Document properties and methods, including units where appropriate.
- Contributed classes should feature complete code coverage to prevent future
  changes from breaking functionality. This is especially important if the lead
  developers do not have access to the physical hardware.
- Please use :ref:`property_factories` when appropriate, to consolidate parsing
  logic into a small number of easily-tested functions. This will also reduce
  the number of tests required to be written.

We can help with any and all of these, so please ask, and thank you for helping
make InstrumentKit even better.

.. _PEP 8: http://legacy.python.org/dev/peps/pep-0008/
