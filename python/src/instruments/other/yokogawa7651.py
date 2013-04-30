#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# yokogawa7651.py: Driver for the Yokogawa 7651 power supply.
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

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class Yokogawa7651(Instrument):

    def __init__(self, filelike):
        super(Yokogawa7651, self).__init__(self, filelike)
        self._outputting = 0
        
    def trigger(self):
        '''
        Triggering function for the Yokogawa 7651.
        
        After changing any parameters of the instrument (for example, output 
        voltage), the device needs to be triggered before it will update.
        '''
        self.sendcmd('E;')
    
    def set_voltage_range(self, voltage):
        '''
        Function changes the voltage range of the power supply. 
        A float representing the desired voltage will have the range adjusted 
        accordingly, or a string specifying the range will also work.
        
        Device can output a max of 30V.
        
        :param voltage: Desired voltage (float) or directly specified 
            voltage range (string). One of {<0...+30.0>|10MV|100MV|1V|10V|30V}
        :type: `float`, `int`, or `str`
        '''
        if (isinstance(voltage, float)) or (isinstance(voltage, int)):
            if voltage < 10e-3:
                yokoRange = 2
            elif (voltage >= 10e-3) and (voltage < 100e-3):
                yokoRange = 3
            elif (voltage >= 100e-3) and (voltage < 1):
                yokoRange = 4
            elif (voltage >= 1) and (voltage < 10):
                yokoRange = 5
            elif (voltage >= 10) and (voltage <= 30):
                yokoRange = 6
            else:
                raise ValueError('Highest voltage range is 30V.')
        elif isinstance(voltage, str):
            voltage = voltage.lower()
            valid = ['10mv','100mv','1v','10v','30v']
            if voltage not in valid:
                raise ValueError('Allowed voltage range values '
                                   'are {}.'.format(valid))
            else:
                yokoRange = valid.index(voltage) + 2
        else:
            raise TypeError('Not a valid data type for param voltage.')    
                
        self.sendcmd('R{};'.format(yokoRange))
        self.trigger()
    
    def set_current_range(self, current):
        '''
        Function changes the current range of the power supply. 
        A float representing the desired current will have the range adjusted 
        accordingly, or a string specifying the range will also work.
        
        Device has a output max of 100mA.
        
        :param current: Desired current (float) or directly specified current 
            range (string). One of {<0...+0.1>|1MA|10MA|100MA}
        :type: `float`, `int`, or `str`
        '''
        if (isinstance(current, float)) or (isinstance(current, int)):
            if current < 1e-3:
                yokoRange = 4
            elif (current >= 1e-3) and (current < 10e-3):
                yokoRange = 5
            elif (voltage >= 10e-3) and (voltage < 100e-3):
                yokoRange = 6
            else:
                raise ValueError('Highest current range is 100mA.')
        elif isinstance(current, str):
            current = current.lower()
            valid = ['1ma','10ma','100ma']
            if current not in valid:
                raise ValueError('Allowed current range values are 1mA, '
                                   '10mA and 100mA.')
            else:
                yokoRange = valid.index(current) + 4    
                
        self.sendcmd('R{};'.format(yokoRange))
        self.trigger()
      
    def set_function(self,func):
        '''
        Set the output of the Yokogawa 7651 to either constant voltage or 
        constant current mode.
        
        func: Desired constant (voltage or current) mode.
        func = {VOLTAGE|CURRENT},string
        '''
        if not isinstance(func, str):
            raise TypeError('Parameter "func" must be a string.')
            
        func = func.lower()
        
        if func == 'voltage':
            setting = 1
        elif func == 'current':
            setting = 5
        else:
            raise ValueError('Only allowed values are "voltage" '
                               'and "current".')
        
        self.sendcmd('F{};'.format(setting))
        self.trigger()
       
    def set_voltage(self,voltage):
        '''
        Set the output voltage of the power supply.
        
        :param float voltage: Desired constant output voltage
        voltage = <0...+30.0>,float
        '''
        
        if (isinstance(voltage, float)) or (isinstance(voltage, int)):
            self.setVoltageRange(voltage)
            self.sendcmd('S{};'.format(voltage))
            self.trigger()
        else:
            raise TypeError('Please specify voltage as a integer for float.')
       
    def output(self,setting):
        '''
        Enable or disable the output of the Yokogawa 7651.
        
        :param setting: Specify the state of the power supply output. One of
            {0|1|OFF|ON}
        :type: `int` or `str`
        '''
        if isinstance(setting, str):
            setting = setting.lower()
        
            if setting in ['off','on']:
                setting = ['off','on'].index(setting)
            if setting in ['0','1']:
                setting = int(setting)
                
        if setting not in [0,1]:
            raise ValueError('Valid parameters are "on", "off", 1 and 0.')
        
        if setting == 1: # If we want to turn the output on
            if self._outputting == 0: # and we are NOT currently _outputting
                self.sendcmd('O1;')
                self.trigger()
                self._outputting = 1
        else: # If we want to turn the output off
            if self._outputting == 1: # and we are curently _outputting
                self.sendcmd('O0;')
                self.trigger()
                self._outputting = 0
                
        
        
        
                
                
                
                
                
                
