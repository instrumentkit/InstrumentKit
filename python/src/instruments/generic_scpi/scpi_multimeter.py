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

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Multimeter
from instruments.generic_scpi import SCPIInstrument

## CONSTANTS ###################################################################

VALID_MODES = [
    'capacitance', 
    'continuity', 
    'current:ac', 
    'current:dc', 
    'diode', 
    'frequency', 
    'fresistance', 
    'period', 
    'resistance', 
    'temperature', 
    'voltage:dc', 
    'voltage:ac', 
]

VALID_MODES_SHORT = [
    'cap',
    'cont',
    'curr:ac',
    'curr:dc',
    'diod',
    'freq',
    'fres',
    'per',
    'res',
    'temp',
    'volt:dc',
    'volt:ac'
]

VALID_FRES_NAMES = ['4res','4 res','four res','f res']

UNITS_CAPACITANCE = ['cap']
UNITS_VOLTAGE = ['volt:dc','volt:ac','diod']
UNITS_CURRENT = ['curr:dc','curr:ac']
UNITS_RESISTANCE = ['res','fres'] + VALID_FRES_NAMES
UNITS_FREQUENCY = ['freq']
UNITS_TIME = ['per']
UNITS_TEMPERATURE = ['temp']

## CLASSES #####################################################################

class SCPIMultimeter(Multimeter, SCPIInstrument):
    
    ## PROPERTIES ##
    
    @property
    def mode(self):
        '''
        Read measurement mode the multimeter is currently in.
        '''
        return self.query('CONF?')
    @mode.setter
    def mode(self, newval):
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
        
        mode: Desired measurement mode
        mode = {CAPacitance|CONTinuity|CURRent:AC|CURRent:DC|DIODe|
                FREQuency|FRESistance|PERiod|RESistance|TEMPerature|
                VOLTage:AC|VOLTage:DC},string
        '''
        if isinstance(mode, str):
            mode = mode.lower()
        if mode in VALID_MODES:
            mode = VALID_MODES_SHORT[VALID_MODES.index(mode)]
        self.mode = mode
        value = float(self.query('MEAS:{}?'.format(mode)))
        
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
            
        
