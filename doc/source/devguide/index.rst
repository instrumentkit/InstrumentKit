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

Contributing Code
=================

We love getting new instruments and new functionality! When sending
in pull requests, however, it helps us out a lot in maintaining InstrumentKit
as a usable library if you can do a couple things for us with your submission:

- Make sure code follows `PEP 8`_ as best as possible. This helps keep the
  code readable and maintainable.
- Document properties and methods, including units where appropriate.
- Especially if the lead developers don't own an instance of the instrument,
  please make sure to cover your code with unit tests.
- Please use :ref:`property_factories` when appropriate, to consolidate parsing
  logic into a small number of easily-tested functions.

We can help with any and all of these, so please ask, and thank you for helping
make InstrumentKit even better.

.. _PEP 8: http://legacy.python.org/dev/peps/pep-0008/
