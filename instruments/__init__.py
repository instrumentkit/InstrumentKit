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

# VERSION METADATA ###########################################################
# In keeping with PEP-396, we define a version number of the form
# {major}.{minor}[.{postrelease}]{prerelease-tag}

__version__ = "0.0.5"

__title__ = "instrumentkit"
__description__ = "Test and measurement communication library"
__uri__ = "https://instrumentkit.readthedocs.org/"

__author__ = "Steven Casagrande"
__email__ = "scasagrande@galvant.ca"

__license__ = "AGPLv3"
__copyright__ = "Copyright (c) 2012-2016 Steven Casagrande"
