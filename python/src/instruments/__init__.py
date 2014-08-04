#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Defines globally-available subpackages and symbols for the
#     instruments package.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## VERSION METADATA ###########################################################
# In keeping with PEP-396, we define a version number of the form
# {major}.{minor}[.{postrelease}]{prerelease-tag}

__version__ = '1.0a1'

## VERSION CHECKING ###########################################################

# We hide version checking in a function so that imports from here don't
# "leak" out to the __all__ of this package.
def __check_versions():
    from distutils.version import StrictVersion
    
    VERSIONS_NEEDED = {
        'flufl.enum': StrictVersion('4.0')
    }
    
    for module_name, version in VERSIONS_NEEDED.iteritems():
        module = __import__(module_name, fromlist=['__version__'])
        if StrictVersion(module.__version__) < version:
            raise ImportError("Module {} is version {}, but we need version {}.".format(module_name, module.__version__, version))
            
__check_versions()

## IMPORTS ####################################################################

from instruments.abstract_instruments import Instrument
import instruments.abstract_instruments

import instruments.generic_scpi
import instruments.agilent
import instruments.holzworth
import instruments.keithley
import instruments.lakeshore
import instruments.oxford
import instruments.phasematrix
import instruments.picowatt
import instruments.rigol
import instruments.srs
import instruments.tektronix
import instruments.thorlabs
import instruments.qubitekk
import instruments.hp

import instruments.units

from instruments.config import load_instruments

# Replace instruments.other with a deprecation warning.

import instruments.other as _other

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

