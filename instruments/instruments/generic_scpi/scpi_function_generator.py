#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# scpimultimeter.py: Python class for SCPI complient multimeters
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from flufl.enum import Enum

import quantities as pq
import numpy as np

from instruments.abstract_instruments import FunctionGenerator
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, enum_property, unitful_property

from instruments.units import dBm

## CLASSES #####################################################################

class SCPIFunctionGenerator(FunctionGenerator, SCPIInstrument):
    
    ## CONSTANTS ##
    
    # TODO: document these.
    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VPP",
        FunctionGenerator.VoltageMode.rms:          "VRMS",
        FunctionGenerator.VoltageMode.dBm:          "DBM",
    }
    
    _MNEMONIC_UNITS = dict((mnem, unit) for unit, mnem in _UNIT_MNEMONICS.iteritems())
    
    ## FunctionGenerator CONTRACT ##
    
    def _get_amplitude_(self):
        """
        
        """
        units = self.query("VOLT:UNIT?").strip()
        
        return (
            float(self.query("VOLT?").strip()),
            self._MNEMONIC_UNITS[units]
        )
        
    def _set_amplitude_(self, magnitude, units):
        """
        
        """
        self.sendcmd("VOLT:UNIT {}".format(self._UNIT_MNEMONICS[units]))
        self.sendcmd("VOLT {}".format(magnitude))
    
    ## PROPERTIES ##
    
    frequency = unitful_property(
        name="FREQ",
        units=pq.Hz,
        doc="""
        Gets/sets the output frequency.
        
        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~quantities.quantity.Quantity`
        """
    )
    
    function = enum_property(
        name="FUNC",
        enum = lambda: self.Function,
        doc="""
        Gets/sets the output function of the function generator
        
        :type: `SCPIFunctionGenerator.Function`
        """
    )
    
    offset = unitful_property(
        name="VOLT:OFFS",
        units=pq.volt,
        doc="""
        Gets/sets the offset voltage of the function generator.
        
        Set value should be within correct bounds of instrument.
        
        :units: As specified  (if a `~quntities.quantity.Quantity`) or assumed 
            to be of units volts.
        :type: `~quantities.quantity.Quantity` with units volts.
        """
    )
    
    @property
    def phase(self):
        raise NotImplementedError
    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
    
