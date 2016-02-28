#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines globally-available subpackages and symbols for the instruments package.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from . import abstract_instruments
from .abstract_instruments import Instrument

from . import agilent
from . import generic_scpi
from . import holzworth
from . import hp
from . import keithley
from . import lakeshore
from . import newport
from . import oxford
from . import phasematrix
from . import picowatt
from . import qubitekk
from . import rigol
from . import srs
from . import tektronix
from . import thorlabs
from . import toptica
from . import yokogawa

from . import units
from .config import load_instruments

# Replace instruments.other with a deprecation warning.
import instruments.other as _other

# VERSION METADATA ###########################################################
# In keeping with PEP-396, we define a version number of the form
# {major}.{minor}[.{postrelease}]{prerelease-tag}

__version__ = '1.0a1'

# VERSION CHECKING ###########################################################

# We hide version checking in a function so that imports from here don't
# "leak" out to the __all__ of this package.


def __check_versions():
    from distutils.version import StrictVersion

    _versions_needed = {
        # 'flufl.enum': StrictVersion('4.0')
    }

    for module_name, version in _versions_needed.items():
        module = __import__(module_name, fromlist=['__version__'])
        if StrictVersion(module.__version__) < version:
            raise ImportError("Module {} is version {}, but we need version {}.".format(
                module_name, module.__version__, version))

__check_versions()


class _Other(object):

    def __getattr__(self, name):
        import warnings
        attr = getattr(_other, name)

        msg = (
            "The instruments.other package is deprecated. "
            "Please use the {} package instead.".format(
                ".".join(attr.__module__.split(".")[:2])
            )
        )

        # This really should be a DeprecationWarning, except those are silenced
        # by default. Why?
        warnings.warn(msg, UserWarning)

        return attr

other = _Other()
