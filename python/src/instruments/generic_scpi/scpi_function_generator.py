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

    ## ENUMS ##
    
    class VoltageMode(Enum):
        peak_to_peak = 'VPP'
        rms = 'VRMS'
    
    class Function(Enum):
        sinusoid = 'SIN'
        square = 'SQU'
        triangle = 
        ramp = 'RAMP'
        noise = 'NOIS'
        arbitrary = '
    
    ## PROPERTIES ##
    
    @property
    def amplitude(self):
        '''
        Gets/sets the output amplitude of the function generator.
        
        If set with units of :math:`\\text{dBm}`, then no voltage mode can
        be passed.
        
        If set with units of :math:`\\text{V}` as a `~quantities.Quantity` or a
        `float` without a voltage mode, then the voltage mode is assumed to be
        peak-to-peak.
        
        :units: As specified, or assumed to be :math:`\\text{V}` if not
            specified.        
        :type: Either a `tuple` of a `~quantities.Quantity` and a
            `SCPIFunctionGenerator.VoltageMode`, or a `~quantities.Quantity` 
            if no voltage mode applies.
        '''
        mag = float(self.query('VOLT?'))
        units = self.query('VOLT:UNITS?').upper()
        
        if units == 'DBM':
            return pq.Quantity(mag, dBm)
        else:
            return pq.Quantity(mag, pq.V), VoltageMage[units]
    @amplitude.setter
    def amplitude(self, newval):
        # Try and rescale to dBm... if it succeeds, set the magnitude
        # and units accordingly, otherwise handle as a voltage.
        try:
            newval_dBm = newval.rescale(dBm)
            mag = float(newval_dBm.magnitude)
            units = "DB"
        except (AttributeError, ValueError):
            # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
            if not isinstance(newval, tuple):
                mag = newval
                units = VoltageMode.peak_to_peak
            else:
                mag, units = newval
                
            # Get the mneonic for the units.
            units = units.value
                
            # Finally, convert the magnitude out to a float.
            mag = float(assume_units(mag, pq.V).rescale(pq.V).magnitude)
        
        
        self.sendcmd("VOLT {}".format(mag))
        self.sendcmd("VOLT:UNITS {}".format(units))
    
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
    
