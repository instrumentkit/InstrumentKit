#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley2182.py: Driver for the Keithley 2182 nano-voltmeter.
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

class Keithley2182(Instrument):
        
    def configure(self, mode=None):
        '''
        Set the measurement mode the Keithley 2182 is in.
        
        :param str mode: Desired measurement mode. One of 
            {TEMPerature|VOLTage}
        '''
        if mode == None:
            return self.query('CONF?')
        
        valid = ['voltage', 'temperature']
        valid2 = ['volt', 'temp']
        
        if not isinstance(mode, str):
            raise TypeError('Mode must be specified as a string.')
        
        mode = mode.lower()
        if mode in valid:
            mode = valid2[valid.index(mode)]
        elif mode not in valid2:
            raise ValueError('Valid measurement modes are {}.'.format(valid))
        
        self.sendcmd('CONF:' + mode)
        
    def fetch(self):
        '''
        Transfer readings from instrument memory to the output buffer, and thus 
        to the computer.
        If currently taking a reading, the instrument will wait until it is 
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? command 
        to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not 
        recommended to transfer a large number of data points using GPIB.
        
        :rtype: `list` of `float`
        '''
        return map(float, self.query('FETC?').split(','))
    
    def measure(self, mode):
        '''
        Perform and transfer a measurement of the desired type.
        
        :param str mode: Desired measurement mode. One of 
            {TEMPerature|VOLTage}
        
        :rtype: `list` of `float`
        '''
        valid = ['voltage', 'temperature']
        valid2 = ['volt', 'temp']
        
        if not isinstance(mode, str):
            raise TypeError('Mode must be specified as a string.')
        
        mode = mode.lower()
        if mode in valid:
            mode = valid2[valid.index(mode)]
        elif mode not in valid2:
            raise ValueError('Valid measurement modes are {}.'.format(valid))
        
        return float(self.query('MEAS:{}?'.format(mode)))
        
    def trigger_source(self, source=None):
        '''
        This function sets the trigger source for measurements.
        
        If no source is specified, function queries the instrument for the 
        current setting. This is returned as a string. An example value is 
        "EXT", without quotes.
            
        :param str source: Desired trigger source. One of 
            {IMMediate|EXTernal|BUS|TIMer|MANual}
        
        :rtype: `str`
        '''
        if source == None: # If source was not specified, perform query.
            return self.query('TRIG:SOUR?')
        
        if not isinstance(source,str):
            raise TypeError('Parameter "source" must be a string.')
        source = source.lower()
        
        valid = ['immediate','external','bus','timer','manual']
        valid2 = ['imm','ext','bus','tim','man']
        
        if source in valid:
            source = valid2[valid.index(source)]
        elif source not in valid2:
            raise ValueError('Valid trigger sources are {}.'.format(valid))
        
        self.sendcmd('TRIG:SOUR {}'.format(source))
        
    def trigger_count(self, count = None):
        '''
        This function sets the number of triggers that the 2182 will accept 
        before returning to an "idle" trigger state.
        
        Note that if the sample count parameter has been changed, the number of 
        readings taken will be a multiplication of sample count and trigger 
        count (see function sampleCount).
        
        If count is not specified, function queries the instrument for the 
        current trigger count setting. This is returned as an integer.
        
        :param count: Number of triggers before returning to an "idle" 
            trigger state. One of {<count>|INFinity}
        :type: `int` or `str`
        
        :rtype: `int`
        '''
        if count == None: # If count not specified, perform query.
            return int(self.query('TRIG:COUN?'))
        
        if isinstance(count,str):
            count = count.lower()
            if count == 'infinity':
                count = 'inf'
            elif count != 'inf':
                raise ValueError('Valid trigger count value is "infinity" '
                    'when specified as a string.')
        elif isinstance(count,int):
            if count < 1 or count > 9999:
                raise ValueError('Trigger count must be a between '
                    '1 and 9999.')
            count = str(count)
        else:
            raise TypeError('Trigger count must be a string or an integer.')
        
        self.sendcmd('TRIG:COUN {}'.format(count))
        
    def trigger_delay(self, period=None):
        '''
        This command sets the time delay which the instrument will use 
        following receiving a trigger event before starting the measurement.
        
        Note that this function does not contain proper screening for "period" 
        being a malformed string. This allows you to include the units of your 
        specified value in the string.
        If no units are specified, the number will be read by the instrument as 
        having units of seconds.
        
        If no period is specified, function queries the instrument for the 
        current trigger delay and returns a float.
        
        :param period: Time between receiving a trigger event and the instrument 
            taking the reading. Values range from 0s to ~3600s, in ~20us 
            increments. One of {<seconds>|AUTO}
        :type: `float` or `str`
        
        :rtype: `float`
        '''
        if period == None: # If no period is specified, perform query.
            return float(self.query('TRIG:DEL?'))
        
        if isinstance(period,str):
            period = period.lower()
            if period == 'auto':
                self.sendcmd('TRIG:DEL:AUTO 1')
        elif isinstance(period, int) or isinstance(period, float):
            if period < 0 or period >  999999.999:
                raise ValueError('The trigger delay needs to be between 0 '
                    'and 1000000 seconds.')
        
        self.sendcmd('TRIG:DEL {}'.format(period))
        
    def sample_count(self, count=None):
        '''
        This command sets the number of readings (samples) that the meter will 
        take per trigger.
        
        Note that if the sample count parameter has been changed, the number of 
        readings taken will be a multiplication of sample count and trigger 
        count (see function `~Keithley2182.sample_count`).
            
        If count is not specified, function queries the instrument for the 
        current sample count and returns an integer.
        
        :param int count: Number of triggers before returning to an "idle" 
            trigger state.
            
        :rtype: `int`
        '''
        if count == None: # If count is not specified, perform query.
            return int(self.query('SAMP:COUN?'))
        
        if isinstance(count,int):
            if count < 1 or count > 1024:
                raise ValueError('Trigger count must be an integer, '
                    '1 to 1024.')
            count = str(count)
        else:
            raise TypeError('Trigger count must be an integer.')
        
        self.sendcmd('SAMP:COUN {}'.format(count))
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
