==========================
Configuration File Support
==========================

.. currentmodule:: instruments

The `instruments` package provides support for loading instruments from a
configuration file, so that instrument parameters can be abstracted from the
software that connects to those instruments. Configuration files recognized
by `instruments` are `YAML`_ files that specify for each instrument a class
responsible for loading that instrument, along with a URI specifying how that
instrument is connected.

Configuration files are loaded by the use of the `load_instruments` function,
documented below.

Functions
=========

.. autofunction:: load_instruments

.. _YAML: http://yaml.org/
