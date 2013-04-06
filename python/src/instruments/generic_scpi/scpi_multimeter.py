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
    
## UNITS #######################################################################

UNITS = {
    MultimeterMode.capacitance: pq.farad,
    MultimeterMode.voltage_dc:  pq.volt,
    MultimeterMode.voltage_ac:  pq.volt,
    MultimeterMode.diode:       pq.volt,
    MultimeterMode.current_ac:  pq.amp,
    MultimeterMode.current_dc:  pq.amp,
    MultimeterMode.resistance:  pq.ohm,
    MultimeterMode.fourpt_resistance: pq.ohm,
    MultimeterMode.frequency:   pq.hertz,
    MultimeterMode.period:      pq.second,
    MultimeterMode.temperature: pq.kelvin,
    MultimeterMode.continuity:  1,
}
    
## CLASSES #####################################################################

class SCPIMultimeter(Multimeter, SCPIInstrument):
    
    ## PROPERTIES ##
    
    @property
    def mode(self):
        '''
        Get or set the current measurement mode for the multimeter.
        '''
        return MultimeterMode[self.query('CONF?')]
    @mode.setter
    def mode(self, newval):
        if not (isinstance(newval, MultimeterMode) or isinstance(newval, str)):
            raise TypeError("Mode must be specified as either a str or a MultimeterMode.")
        if isinstance(newval, str):
            newval = MultimeterMode[newval]
        self.sendcmd('CONF:' + newval._value)
    
    ## METHODS ##
    
    def measure(self, mode=None):
        '''
        Instruct the multimeter to perform a one time measurement. The 
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are 
        directly sent to the instrument's output buffer.
        
        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units. If no appropriate units exist,
        (for example, continuity), then return type is `float`.
        
        :param instruments.generic_scpi.MultimeterMode mode: Desired measurement mode.
            If set to `None`, will default to the current mode.
        '''
        
        # Default to the current mode.
        if mode is None:
            mode = self.mode
            
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
        return value * UNITS[mode]
            
        
