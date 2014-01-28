#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley195.py: Driver for the Keithley 195 multimeter.
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

import time
from flufl.enum import Enum

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Multimeter

## CLASSES #####################################################################

class Keithley195(Multimeter):
    '''
    The Keithley 195 is a 5 1/2 digit auto-ranging digital multimeter. You can 
    find the full specifications list in the `user's guide`_.
    
    Example usage:
    
    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
    >>> print dmm.measure(dmm.Mode.resistance)
    
    .. _user's guide: http://www.keithley.com/data?asset=803
    '''

    def __init__(self, filelike):
        super(Keithley195, self).__init__(filelike)
        self.sendcmd('YX') # Removes the termination CRLF 
                           # characters from the instrument

    ## ENUMS ##
    
    class Mode(Enum):
        voltage_dc = 0
        voltage_ac = 1
        resistance = 2
        current_dc = 3
        current_ac = 4
        
    ## PROPERTIES ##    
        
    @property
    def mode(self):
        '''
        Sets the current measurement mode for the Keithley 195.
        
        Example use:
        
        >>> import instruments as ik
        >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
        >>> dmm.mode = dmm.Mode.resistance
        
        :type: `Keithley195.Mode`
        '''
        raise NotImplementedError
    @mode.setter
    def mode(self, newval):
        if isinstance(newval, str):
            newval = self.Mode[newval]
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                            Keithley195.Mode):
            raise TypeError("Mode must be specified as a Keithley195.Mode "
                            "value, got {} instead.".format(type(newval)))
        self.sendcmd('F{}X'.format(newval.value))
        
    ## METHODS ##
    
    def measure(self, mode = None):
        '''
        Instruct the Keithley 195 to perform a one time measurement. The 
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are 
        directly sent to the instrument's output buffer.
        
        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units.
        
        Example usage:
    
        >>> import instruments as ik
        >>> import quantities as pq
        >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
        >>> print dmm.measure(dmm.Mode.resistance)
        
        :param mode: Desired measurement mode. If not specified, the current 
            mode that the 195 is set to will be used.
        :type mode: `Keithley195.Mode`
        :rtype: `~quantities.quantity.Quantity`
        '''
        if mode is not None:
            self.mode = mode
            time.sleep(0.1)
        value = float(self.query(''))
        return value * UNITS[mode]
    
    def trigger(self):
        '''
        Tell the Keithley 195 to execute all commands that it has received.
        
        Do note that this is different from the standard SCPI \*TRG command
        (which is not supported by the 195 anyways).
        '''
        self.sendcmd('X')
        
    def set_voltage_dc_range(self, voltage='AUTO'):
        '''
        Manually set the voltage DC range of the Keithley 195.
        
        :param voltage: Voltage DC range. One of 
            ``{AUTO|20e-3|200e-3|2|20|200|1000}``
        :type: `str` or `int`
        '''
        if isinstance(voltage, str):
            voltage = voltage.lower()
            if voltage == 'auto':
                voltage = 0
            else:
                raise ValueError('Only valid string for voltage range '
                    'is "auto".')
        elif isinstance(voltage, float) or isinstance(voltage, int):
            valid = [20e-3, 200e-3, 2, 20, 200, 1000]
            if voltage in valid:
                voltage = valid.index(voltage) + 1
            else:
                raise ValueError('Valid voltage ranges are: ' + str(valid))
        else:
            raise TypeError('Instrument voltage range must be specified as '
                'a float, integer, or string.')
            
        self.sendcmd('R{}X'.format(voltage))
    
    def set_voltage_ac_range(self, voltage='AUTO'):
        '''
        Manually set the voltage AC range of the Keithley 195.
        
        :param voltage: Voltage AC range. One of 
            ``{AUTO|20e-3|200e-3|2|20|200|700}``
        :type: `str` or `int`
        '''
        if isinstance(voltage,str):
            voltage = voltage.lower()
            if voltage == 'auto':
                voltage = 0
            else:
                raise ValueError('Only valid string for voltage range '
                    'is "auto".')
        elif isinstance(voltage, float) or isinstance(voltage, int):
            valid = [20e-3, 200e-3, 2, 20, 200, 700]
            if voltage in valid:
                voltage = valid.index(voltage) + 1
            else:
                raise ValueError('Valid voltage ranges are: ' + str(valid))
        else:
            raise TypeError('Instrument voltage range must be specified as '
                'a float, integer, or string.')
            
        self.sendcmd('R{}X'.format(voltage))
            
    def set_current_range(self, current='AUTO'):
        '''
        Manually set the current range of the Keithley 195.
        
        :param current: Current range. One of 
            ``{AUTO|20e-6|200e-6|2e-3|20e-3|200e-3|2}``
        :type: `str` or `int`
        '''
        if isinstance(current, str):
            current = current.lower()
            if current == 'auto':
                current = 0
            else:
                raise ValueError('Only valid string for current range '
                    'is "auto".')
        elif isinstance(current, float) or isinstance(current, int):
            valid = [20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2]
            if current in valid:
                current = valid.index(current) + 1
            else:
                raise ValueError('Valid current ranges are: ' + str(valid))
        else:
            raise TypeError('Instrument current range must be specified as '
                'a float, integer, or string.')
            
        self.sendcmd('R' + current + 'X')
            
    def set_resistance_range(self, res='AUTO'):
        '''
        Manually set the resistance range of the Keithley 195.
        
        :param res: Resistance range. One of 
            ``{AUTO|20|200|2000|20e3|200e3|2e6|20e6}``
        :type: `str` or `int`
        '''
        if isinstance(res,str):
            res = res.lower()
            if res == 'auto':
                res = 0
            else:
                raise ValueError('Only valid string for resistance range '
                    'is "auto".')
        elif isinstance(res, float) or isinstance(res, int):
            valid = [20, 200, 2000, 20e3, 200e3, 2e6, 20e6]
            if res in valid:
                res = valid.index(res) + 1
            else:
                raise ValueError('Valid resistance ranges are: ' + str(valid))
        else:
            raise TypeError('Instrument resistance range must be specified '
                'as a float, integer, or string.')
            
        self.sendcmd('R{}X'.format(res))
            
    def auto_range(self):
        '''
        Turn on auto range for the Keithley 195. 
        
        This is the same as calling the associated set_[function]_range method
        and setting the parameter to "AUTO".
        '''
        self.sendcmd('R0X')
            
## UNITS #######################################################################

UNITS = {
    Keithley195.Mode.voltage_dc:  pq.volt,
    Keithley195.Mode.voltage_ac:  pq.volt,
    Keithley195.Mode.current_ac:  pq.amp,
    Keithley195.Mode.current_dc:  pq.amp,
    Keithley195.Mode.resistance:  pq.ohm,
}            
        
