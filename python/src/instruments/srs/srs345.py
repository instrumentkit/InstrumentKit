#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srs345.py: Implements a driver for the SRS 345 function generator.
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

from time import time, sleep

from flufl.enum import Enum
from flufl.enum._enum import EnumValue

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

from instruments.units import dBm

import struct
import numpy as np

## ENUMS #######################################################################

class SRS345VoltageMode(Enum):
    peak_to_peak = "VP"
    rms = "VR"

## FUNCTIONS ###################################################################

class SRS345(SCPIInstrument):
    # TODO: docstring
        
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
            `SRS345VoltageMode`, or a `~quantities.Quantity` if no voltage mode
            applies.
        '''
        resp = self.query("AMPL?").strip()
        mag = float(resp[:-2]) # Strip off units and convert to float.
        units = resp[-2:]
        if units == "DB":
            return pq.Quantity(mag, dBm)
        else:
            return pq.Quantity(mag, pq.V), SRS345VoltageMode[units]

    @amplitude.setter
    def amplitude(self, newval):
        
        # Try and rescale to dBm... if it succeeds, set the magnitude
        # and units accordingly, otherwise handle as a voltage.
        try:
            newval_dBm = newval.rescale(dBm)
            mag = float(newval_dBm.magnitude)
            units = "DB"
        except ValueError:
            # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
            if not isinstance(newval, tuple):
                mag = newval
                units = SRS345VoltageMode.peak_to_peak
            else:
                mag, units = newval
                
            # Get the mneonic for the units.
            units = units.value
                
            # Finally, convert the magnitude out to a float.
            mag = float(assume_units(newval, pq.V).rescale(pq.V).magnitude)
        
        
        self.sendcmd("AMPL {mag}{units}".format(mag=mag, units=units))
                
    @property
    def frequency(self):
        '''
        Gets/sets the output frequency.
        
        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self.query('FREQ?')), pq.Hz)
    @frequency.setter(self, newval):
        self.sendcmd("FREQ {}".format(
            assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude)
        )
        
    def function(self,func = None):
        '''
        Set the output function of the function generator.
        
        If argument "func" is omitted, the instrument is queried for its current output setting.
        
        Return type is a string.
        
        func: Output function type.
        func = {SINusoid|SQUare|TRIangle|RAMP|NOISe|ARBitrary},string
        '''
        valid = ['sinusoid','square','triangle','ramp','noise','arbitrary']
        valid2 = ['sin','squ','tri','ramp','nois','arb']
        
        if func == None:
            func = self.query('FUNC?')
            return valid[int(func)]
        
        if not isinstance(func,str):
            raise Exception('Function type must be specified as a string.')
        
        func = func.lower()
        if func in valid:
            func = valid.index(func)
        elif func in valid2:
            func = valid2.index(func)
        elif func == 'sine':
            func = 0
        else:
            raise Exception('Valid output function types are: ' + str(valid))
        
        self.write('FUNC ' + str(func))
        
    def offset(self,offset = None):
        '''
        Set the offset voltage for the output waveform.
        
        If no offset is specified, function queries the instrument for the current offset voltage.
        
        Return type is a float.
        
        offset: Desired voltage offset in volts.
        offset = <voltage>,integer/float
        '''
        if offset == None:
            return float( self.query('OFFS?') )
        
        if not isinstance(offset,int) and not isinstance(offset,float):
            raise Exception('Offset must be an integer or a float.')
        
        self.write('OFFS ' + str(offset))
        
    def phase(self, phase = None):
        '''
        Set the phase for the output waveform.
        
        If no phase is specified, function queries the instrument for the current phase.
        
        Return type is a float.
        
        phase: Desired phase in degrees.
        phase = <voltage>,integer/float
        '''
        if phase == None:
            return float( self.query('PHSE?') )
        
        if not isinstance(phase,int) and not isinstance(phase,float):
            raise Exception('Phase must be an integer or a float.')
        
        if phase < 0 or phase > 7200:
            raise Exception('Phase must be between 0 and 7200 degrees.')
        
        self.write('PHSE ' + str(phase))
            
        
        
        
        
        
        
        
        
        
        
        
        
        
            
        
