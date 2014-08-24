=============================
Utility Functions and Classes
=============================

.. currentmodule:: instruments.util_fns

Unit Handling
=============

.. autofunction:: assume_units

Enumerating Instrument Functionality
====================================

To expose parts of an instrument or device in a Python-ic way, the
:class:`ProxyList` class can be used to emulate a list type by calling the
initializer for some inner class. This is used to expose everything from
channels to axes.

.. _property_factories:

Property Factories
==================

To help expose instrument properties in a consistent and predictable manner,
InstrumentKit offers several functions that return instances of `property`
that are backed by the :meth:`~instruments.Instrument.sendcmd` and
:meth:`~instruments.Instrument.query` protocol. These factories assume
a command protocol that at least resembles the SCPI style::

    -> FOO:BAR?
    <- 42
    -> FOO:BAR 6
    -> FOO:BAR?
    <- 6

.. autofunction:: bool_property

.. autofunction:: enum_property

.. autofunction:: unitless_property

.. autofunction:: int_property

.. autofunction:: unitful_property

.. autofunction:: string_property


