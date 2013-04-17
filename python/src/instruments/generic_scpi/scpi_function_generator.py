#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# scpimultimeter.py: Python class for SCPI complient multimeters
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the GPIBUSB adapter project.
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
from instruments.util_fns import assume_units

from instruments.units import dBm

## CLASSES #####################################################################

class SCPIFunctionGenerator(FunctionGenerator, SCPIInstrument):
    
    ## CONSTANTS ##
    
    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VPP",
        FunctionGenerator.VoltageMode.rms:          "VRMS",
        FunctionGenerator.VoltageMode.dBm:          "DBM",
    }
    
    _MNEMONIC_UNITS = {mnem: unit for unit, mnem in _UNIT_MNEMONICS.iteritems()}
    
    ## FunctionGenerator CONTRACT ##
    
    def _get_amplitude_(self):
        """
        
        """
        units = self.query("VOLT:UNITS?").strip()
        
        return (
            float(self.query("VOLT?").strip()),
            self._MNEMONIC_UNITS[units]
        )
        
    def _set_amplitude_(self, magnitude, units):
        """
        
        """
        self.sendcmd("VOLT {}".format(magnitude))
        self.sendcmd("VOLT:UNITS {}".format(self._UNIT_MNEMONICS[units]))
    
    ## PROPERTIES ##
    
    @property
    def frequency(self):
        '''
        Gets/sets the output frequency.
        
        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self.query('FREQ?')), pq.Hz)
    @frequency.setter
    def frequency(self, newval):
        self.sendcmd("FREQ {}".format(
            assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude)
        )
    
    @property
    def function(self):
        '''
        Gets/sets the output function of the function generator
        
        :type: `SCPIFunctionGenerator.Function`
        '''
        return SCPIFunctionGenerator.Function[self.query('FUNC?').strip()]
    @function.setter
    def function(self, newval):
        if not isinstance(newval, SCPIFunctionGenerator.Function):
            raise TypeError('Value must be specified as a '
                                '`SCPIFunctionGenerator.Function` type.')
        self.sendcmd('FUNC:{}'.format(newval.value))
    
    @property
    def offset(self):
        pass
    @offset.setter
    def offset(self, newval):
        pass
    
    @property
    def phase(self):
        pass
    @phase.setter
    def phase(self, newval):
        pass
    
