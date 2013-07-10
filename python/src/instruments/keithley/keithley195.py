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

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class Keithley195(Instrument):
    def __init__(self, filelike):
        super(Keithley195, self).__init__(filelike)
        self.sendcmd('YX') # Removes the termination CRLF 
                         # characters from the instrument
        
    def read(self):
        '''
        Force the Keithley 195 to perform a measurement.
        
        On the 195, there is no command that is sent to instruct it to take
        a measurement. Instead we just directly address the 195 to talk on the
        GPIB bus. Since the only connectivity option for the 195 is GPIB, this
        works just nicely.
        
        The instrument will return a measurement of the current mode it is in.
        
        :rtype: `str`
        '''
        self.sendcmd('+read')
        return self.readline()
    
    def trigger(self):
        '''
        Tell the Keithley 195 to execute all commands that it has received.
        
        Do note that this is different from the standard SCPI *TRG command
        (which is not supported by the 195 anyways).
        '''
        self.sendcmd('X')
    
    def set_function(self, func):
        '''
        Set the measurement mode that the Keithley 195 is in.
        
        :param str func: Desired measurement mode. One of
            {VOLTage:DC|VOLTage:AC|RESistance|CURRent:DC|CURRent:AC}
        '''
        if not isinstance(func, str):
            raise TypeError('Meaurement mode must be a string.')
        func = func.lower()
        
        valid = ['volt:dc','volt:ac','res','curr:dc','curr:ac']
        valid2 = ['voltage:dc','voltage:ac','resistance',
            'current:dc','current:ac']
        
        if func in valid2:
            func = valid2.index(func)
        elif func in valid:
            func = valid.index(func)
        else:
            raise ValueError('Valid measurement modes are'
                ': {}'.format(str(valid2)))
        
        self.sendcmd('F{}X'.format(func))
        
    def set_voltage_dc_range(self, voltage='AUTO'):
        '''
        Manually set the voltage DC range of the Keithley 195.
        
        :param voltage: Voltage DC range. One of 
            {AUTO|20e-3|200e-3|2|20|200|1000}
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
            {AUTO|20e-3|200e-3|2|20|200|700}
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
            {AUTO|20e-6|200e-6|2e-3|20e-3|200e-3|2}
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
            {AUTO|20|200|2000|20e3|200e3|2e6|20e6}
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
            
            
            
            
            
            
            
            
            
