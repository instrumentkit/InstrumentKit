#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley6514.py: Driver for the Keithley 6514 electrometer.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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

import time
from flufl.enum import Enum, IntEnum
import struct

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Electrometer
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList, bool_property, enum_property

## CLASSES #####################################################################

class Keithley6514(SCPIInstrument, Electrometer):
    """
    The Keithley 6514 is an electrometer capable of doing sensitive current, 
    charge, voltage and resistance measurements.
    
    Example usage:
    
    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley6514.open_gpibusb('/dev/ttyUSB0', 12)
    
    .. _Keithley 6514 user's guide: http://www.tunl.duke.edu/documents/public/electronics/Keithley/keithley-6514-electrometer-manual.pdf
    """

    ## ENUMS ##
    
    class Mode(Enum):
        voltage = 'VOLT:DC'
        current = 'CURR:DC'
        resistance = 'RES'
        charge = 'CHAR'
       
    class TriggerMode(Enum):
        immediate = 'IMM'
        tlink = 'TLINK'

    class ArmSource(Enum):
        immediate = 'IMM'
        timer = 'TIM'
        bus = 'BUS'
        tlink = 'TLIN'
        stest = 'STES'
        pstest = 'PST'
        nstest = 'NST'
        manual = 'MAN'
        
    class ValidRange(Enum):
        voltage = (2, 20, 200)
        current = (20e-12, 200e-12, 2e-9, 20e-9, 200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3)
        resistance = (2e3, 20e3, 200e3, 2e6, 20e6, 200e6, 2e9, 20e9, 200e9)
        charge = (20e-9, 200e-9, 2e-6, 20e-6)

    ## CONSTANTS ##

    _MODE_UNITS = {
        Mode.voltage: pq.volt,
        Mode.current: pq.amp,
        Mode.resistance: pq.ohm,
        Mode.charge: pq.coulomb
    }
        
    ## PRIVATE METHODS ##    
    
    def _get_auto_range(self, mode):
        out = self.query('{}:RANGE:AUTO?'.format(mode.value))
        return out.strip() == '1'
    def _set_auto_range(self, mode, value):
        self.sendcmd('{}:RANGE:AUTO {}'.format(mode.value, '1' if value else '0'))

    def _get_range(self, mode):
        out = self.query('{}:RANGE:UPPER?'.format(mode.value)).strip()
        return float(out) * self._MODE_UNITS[mode]
    def _set_range(self, mode, value):
        val = value.rescale(self._MODE_UNITS[mode]).item()
        if val not in self._valid_range(mode):
            raise ValueError('Unexpected range limit for currently selected mode.')
        self.sendcmd('{}:RANGE:UPPER {:e}'.format(mode.value, val))

    def _valid_range(self, mode):
        if mode == self.Mode.voltage:
            vrange = self.ValidRange.voltage
        elif mode == self.Mode.current:
            vrange = self.ValidRange.current
        elif mode == self.Mode.resistance:
            vrange = self.ValidRange.resistance
        elif mode == self.Mode.charge:
            vrange = self.ValidRange.charge
        else:
            raise ValueError('Invalid mode.')
        return vrange
        
    def _parse_measurement(self, ascii):
        # TODO: don't assume ASCII data format
        vals = map(float, ascii.split(','))
        reading = vals[0] * self.unit
        timestamp = vals[1]
        status = vals[2]
        return reading, timestamp, status
    
    ## PROPERTIES ##  

    # The mode values have quotes around them for some annoying reason.
    mode = enum_property('FUNCTION', 
        Mode, 
        doc='Gets/sets the measurement mode of the Keithley 6514.',
        input_decoration=lambda val: val[1:-1],
        output_decoration=lambda val: '"{}"'.format(val)
    )

    trigger_mode = enum_property('TRIGGER:SOURCE', 
        TriggerMode, 
        'Gets/sets the trigger mode of the Keithley 6514.'
    )

    arm_source = enum_property('ARM:SOURCE', 
        ArmSource, 
        'Gets/sets the arm source of the Keithley 6514.'
    )

    zero_check = bool_property('SYST:ZCH', 
        'ON', 'OFF',
        'Gets/sets the zero checking status of the Keithley 6514.'
    )
    zero_correct = bool_property('SYST:ZCOR', 
        'ON', 'OFF',
        'Gets/sets the zero correcting status of the Keithley 6514.'
    )

    @property
    def unit(self):
        return self._MODE_UNITS[self.mode]
  
    @property
    def auto_range(self):
        """
        Gets/sets the auto range setting
               
        :type: `Keithley6514.TriggerMode`
        """
        return self._get_auto_range(self.mode)
    @auto_range.setter
    def auto_range(self, newval):
        self._set_auto_range(self.mode, newval)

    @property
    def input_range(self):
        """
        Gets/sets the upper limit of the current range.
               
        :type: `Keithley6514.TriggerMode`
        """
        return self._get_range(self.mode)
    @input_range.setter
    def input_range(self, newval):
        self._set_range(self.mode, newval)
        
        
    ## METHODS ##

    def auto_config(self, mode):
        '''
        This command causes the device to do the following:
            - Switch to the specified mode
            - Reset all related controls to default values
            - Set trigger and arm to the 'immediate' setting
            - Set arm and trigger counts to 1
            - Set trigger delays to 0
            - Place unit in idle state
            - Disable all math calculations
            - Disable buffer operation
            - Enable autozero
        '''
        self.sendcmd('CONF:{}'.format(mode.value))
    
    def fetch(self):
        '''
        Request the latest post-processed readings using the current mode. 
        (So does not issue a trigger)
        Returns a tuple of the form (reading, timestamp)
        '''
        # TODO: figure out what to do with the status info
        raw = self.query('FETC?')
        reading, timestamp, status = self._parse_measurement(raw)
        return reading, timestamp


    def read(self):
        '''
        Trigger and acquire readings using the current mode.
        Returns a tuple of the form (reading, timestamp)
        '''
        # TODO: figure out what to do with the status info
        raw = self.query('READ?')
        reading, timestamp, status = self._parse_measurement(raw)
        return reading, timestamp

        


