#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tekdpo4104.py: Driver for the Tektronix DPO 4104 oscilloscope.
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

import numpy as np

from instruments.generic_scpi import SCPIInstrument

## CLASSES #####################################################################

class Tektds224(SCPIInstrument):
      
    def coupling(self, channel, setting):
        '''
        Set input coupling of specified channel.
        
        :param channel: Input channel which will have the input coupling 
            changed. One of  ``{1|2|3|4|CH1|CH2|CH3|CH4}``.
            
        :type channel: `int` or `str`
        '''
        if isinstance(channel, str):
            channel = channel.lower()
            if channel in ['1','2','3','4']:
                channel = int(channel)
            elif channel in ['ch1','ch2','ch3','ch4']:
                channel = ['ch1','ch2','ch3','ch4'].index(channel) + 1
            else:
                raise ValueError('Only "CH1", "CH2", "CH3", and "CH4" are '
                                 'valid channels to have the input coupling '
                                 'changed.')
        elif isinstance(channel, int) and channel not in [1,2,3,4]:
            raise ValueError('Channel must be 1, 2, 3, or 4 when specified as '
                             'an integer.')
        else:
            raise TypeError('Channel must be specified as an integer or '
                            'string when changing the coupling.')
        
        if setting.upper() in ['AC','DC','GND']:
            self.sendcmd('CH{}:COUPL {}'.format(channel, setting.upper()))
        else:
            raise ValueError('Only AC, DC, and GND are valid coupling '
                             'settings.')
          
    def read_waveform(self, channel, fmt):
        '''
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the 
        oscilloscope, it unpacks the data and scales it accordingly.
        
        Supports both ASCII and binary waveform transfer. For 2500 data 
        points, with a width of 2 bytes, transfer takes approx 2 seconds for 
        binary, and 7 seconds for ASCII over Galvant Industries' GPIBUSB 
        adapter.
        
        Function returns a list [x,y], where both x and y are numpy arrays.
        
        :param str channel: Channel which will have its waveform transfered. 
            One of ``{CH1|CH2|CH3|CH4|REFA|REFB|REFC|REFD|MATH}``
        
        :param str fmt: Data transfer format. Either ASCII or binary. One of 
            ``{ASCII,BINARY}``
        
        :rtype: `list` of `numpy.ndarray`
        '''
        valid_channel = [
                        'CH1',
                        'CH2',
                        'CH3',
                        'CH4',
                        'REFA',
                        'REFB',
                        'REFC',
                        'REFD',
                        'MATH',
                        ]
        if channel.upper() not in valid_channel:
            raise ValueError('Only the following channels are '
                             'supported: {}.'.format(valid_channel))
        
        valid_format = ['ASCII', 'BINARY']
        if format.upper() not in valid_format:
            raise ValueError('Only {} are valid data '
                             'formats'.format(valid_format))
        
        self.sendcmd('DAT:SOU {}'.format(channel.upper())) # Set the acquisition
                                                           # channel
        
        if format.upper() is 'ASCII':
            self.sendcmd('DAT:ENC ASCI') # Set the data encoding format to ASCII
            raw = self.query('CURVE?')
            raw = raw.split(",") # Break up comma delimited string
            raw = map(float, raw) # Convert each list element to int
            raw = array(raw) # Convert into numpy array
        elif format.upper() is 'BINARY':
            self.write('DAT:ENC RIB') # Set encoding to signed, big-endian
            self.write('CURVE?')
            raw = self.binblockread(2) # Read in the binary block, data width 
                                       # of 2 bytes

            #self.ser.read(2) # Read in the two ending \n\r characters
        
        channel = channel.upper()
        yoffs = self.query('WFMP:{}:YOF?'.format(channel)) # Retrieve Y offset
        ymult = self.query('WFMP:{}:YMU?'.format(channel)) # Retrieve Y multiply
        yzero = self.query('WFMP:{}:YZE?'.format(channel)) # Retrieve Y zero
        
        y = ((raw - float(yoffs)) * float(ymult)) + float(yzero)
        
        xzero = self.query('WFMP:XZE?') # Retrieve X zero
        xincr = self.query('WFMP:XIN?') # Retrieve X incr
        ptcnt = self.query('WFMP:{}:NR_P?'.format(channel)) # Retrieve number 
                                                            # of data points
        
        x = np.arange(float(ptcnt)) * float(xincr) + float(xzero)
        
        return [x,y]
        
