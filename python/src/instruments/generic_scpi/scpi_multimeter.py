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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from flufl.enum import Enum

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Multimeter
from instruments.generic_scpi import SCPIInstrument

## CONSTANTS ###################################################################

VALID_FRES_NAMES = ['4res','4 res','four res','f res']

UNITS_CAPACITANCE = ['cap']
UNITS_VOLTAGE = ['volt:dc','volt:ac','diod']
UNITS_CURRENT = ['curr:dc','curr:ac']
UNITS_RESISTANCE = ['res','fres'] + VALID_FRES_NAMES
UNITS_FREQUENCY = ['freq']
UNITS_TIME = ['per']
UNITS_TEMPERATURE = ['temp']

## ENUMS #######################################################################

class MultimeterMode(Enum):
    capacitance = "CAP"
    continuity = "CONT"
    current_ac = "CURR:AC"
    current_dc = "CURR:DC"
    diode = "DIOD"
    frequency = "FREQ"
    fourpt_resistance = "FRES"
    period = "PER"
    resistance = "RES"
    temperature = "TEMP"
    voltage_ac = "VOLT:AC"
    voltage_dc = "VOLT:DC"
    
## CLASSES #####################################################################

class SCPIMultimeter(Multimeter, SCPIInstrument):
    
    ## PROPERTIES ##
    
    @property
    def mode(self):
        '''
        Read measurement mode the multimeter is currently in.
        '''
        return MultimeterMode[self.query('CONF?')]
    @mode.setter
    def mode(self, newval):
        # FIXME: use the enum above.
        '''
        Change the mode the multimeter is in.
        '''
        if isinstance(newval, str):
            newval = newval.lower()
        if newval in VALID_FRES_NAMES:
            newval = 'fres'
        if newval not in VALID_MODES:
            raise ValueError('Valid inputs for mode are: ' + VALID_MODES)
        self.write('CONF:' + newval)
    
    ## METHODS ##
    
    def measure(self, mode):
        '''
        Instruct the multimeter to perform a one time measurement. The 
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are 
        directly sent to the instrument's output buffer.
        
        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units. If no appropriate units exist,
        (for example, continuity), then return type is float.
        
        :param instruments.generic_scpi.MultimeterMode mode: Desired measurement mode.
        '''
        
        # Throw an error if the mode isn't an enum.
        if not isinstance(mode, MultimeterMode):
            raise TypeError("The mode must be specified as a `MultimeterMode`.")
        
        # Unpack the value from the enumeration.
        mode = mode._value.lower()
        # mode = VALID_MODES_SHORT[VALID_MODES.index(mode)]
        
        # Apply the mode and obtain the measurement.
        self.mode = mode
        value = float(self.query('MEAS:{}?'.format(mode)))
        
        # Put the measurement into the correct units.
        if mode in UNITS_CAPACITANCE:
            return value * pq.farad
        elif mode in UNITS_VOLTAGE:
            return value * pq.volt
        elif mode in UNITS_CURRENT:
            return value * pq.amp
        elif mode in UNITS_RESISTANCE:
            return value * pq.ohm
        elif mode in UNITS_FREQUENCY:
            return value * pq.hertz
        elif mode in UNITS_TIME:
            return value * pq.second
        elif mode in UNITS_TEMPERATURE:
            return value * pq.celsius
        else:
            return value
            
        
