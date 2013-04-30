#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# scpi_instrument.py: Provides base class for SCPI-controlled instruments.
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

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class SCPIInstrument(Instrument):
    
    def __init__(self, filelike):
        super(SCPIInstrument, self).__init__(filelike)
    
    ## PROPERTIES ##
    
    @property
    def name(self):
        """
        The name of the connected instrument, as reported by the
        standard SCPI command ``*IDN?``.
        
        :type: `str`
        """
        return self.query('*IDN?')
        
    @property
    def op_complete(self):
        '''
        Check if all operations sent to the instrument have been completed.
        
        :rtype: `bool`
        '''
        result = self.query('*OPC?')
        return bool(int(result))
    
    @property
    def power_on_status(self):
        '''
        Gets/sets the power on status for the instrument.
        
        :type: `bool`
        '''
        result = self.query('*PSC?')
        return bool(int(result))
    @power_on_status.setter
    def power_on_status(self, newval):
        on = ['on', '1', 1, True]
        off = ['off', '0', 0, False]
        if isinstance(newval, str):
            newval = newval.lower()
        if newval in on:
            self.sendcmd('*PSC 1')
        elif newval in off:
            self.sendcmd('*PSC 0')
        else:
            raise ValueError
    
    @property
    def self_test_ok(self):
        '''
        Gets the results of the instrument's self test. This lets you check 
        if the self test was sucessful or not.
        
        :rtype: `bool`
        '''
        result = self.query('*TST?')
        try:
            result = int(result)
            return result == 0
        except:
            return False
    
    ## BASIC SCPI COMMANDS ##
    
    def reset(self):
        '''
        Reset instrument. On many instruments this is a factory reset and will 
        revert all settings to default.
        '''
        self.sendcmd('*RST')
        
    def clear(self):
        '''
        Clear instrument. Consult manual for specifics related to that 
        instrument.
        '''
        self.sendcmd('*CLS')
    
    def trigger(self):
        '''
        Send a software trigger event to the instrument. On most instruments 
        this will cause some sort of hardware event to start. For example, a 
        multimeter might take a measurement.
        
        This software trigger usually performs the same action as a hardware 
        trigger to your instrument.
        '''
        self.sendcmd('*TRG')
    
    def wait_to_continue(self):
        '''
        Instruct the instrument to wait until it has completed all received 
        commands before continuing.
        '''
        self.sendcmd('*WAI')
    
