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
        '''
        Gets/sets the offset voltage of the function generator.
        
        Set value should be within correct bounds of instrument.
        
        :units: As specified  (if a `~quntities.Quantity`) or assumed to be
            of units volts.
        :type: `~quantities.Quantity` with units volts.
        '''
        return pq.Quantity(float(self.query('VOLT:OFFS?')), pq.volt)
    @offset.setter
    def offset(self, newval):
        newval = float(assume_units(newval, pq.volt).rescale(pq.volt).magnitude)
        self.sendcmd('VOLT:OFFS {}'.format(newval))
    
    @property
    def phase(self):
        raise NotImplementedError
    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
    
