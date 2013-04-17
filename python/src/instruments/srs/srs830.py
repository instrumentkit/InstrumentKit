#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srs830.py: Driver for the SRS830 lock-in amplifier.
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

import math
import time

from flufl.enum import Enum
from flufl.enum._enum import EnumValue
import quantities as pq

from instruments.generic_scpi import SCPIInstrument
import instruments.abstract_instruments.gi_gpib as gw
import instruments.abstract_instruments.serialwrapper as sw
from instruments.util_fns import assume_units

## ENUMS #######################################################################

class SRS830FreqSource(Enum):
    external = 0
    internal = 1
    
class SRS830Coupling(Enum):
    ac = 0
    dc = 1

class SRS830BufferMode(Enum):
    one_shot = 0
    loop = 1

## CONSTANTS ###################################################################

VALID_SAMPLE_RATES = [2.0**n for n in xrange(-4, 10)]

## CLASSES #####################################################################

class SRS830(SCPIInstrument):
    '''
    Communicates with a Stanford Research Systems 830 Lock-In Amplifier
    '''
    def __init__(self, filelike, outx_mode=None):
        '''
        Class initialization method. 
        
        :param int outx_mode: Manually over-ride which ``OUTX`` command to send
            at startup. This is a command that needs to be sent as specified
            by the SRS830 manual. If left default, the correct ``OUTX`` command
            will be sent depending on what type of wrapper self._file is.
        '''
        super(SRS830, self).__init__(self,filelike)
        if outx_mode is 1:
            self.sendcmd('OUTX 1')
        elif outx_mode is 2:
            self.sendcmd('OUTX 2')
        else:
            if isinstance(self._file, gw.GPIBWarapper):
                self.sendcmd('OUTX 1')
            elif isinstance(self._file, sw.SerialWrapper):
                self.sendcmd('OUTX 2')
            else:
                print 'OUTX command has not been set. Instrument behavour is '\
                        'unknown.'
    
    ## PROPERTIES ##
    
    @property
    def freq_source(self):
        '''
        Gets/sets the frequency source used. This is either an external source,
            or uses the internal reference.
        
        :type: `SRS830FreqSource`
        '''
        return SRS830FreqSource[self.query('FMOD?')]
    @freq_source.setter
    def freq_source(self, newval):
        if not isinstance(newval, EnumValue) or 
                (newval.enum is not SRS830FreqSource):
            raise TypeError("Frequency source setting must be a "
                              "SRS830FreqSource value, got {} "
                              "instead.".format(type(newval)))
        self.sendcmd('FMOD {}'.format(newval.value))
        
    @property
    def freq(self):
        '''
        Gets/sets the lock-in amplifier reference frequency.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Hertz.
        :type: `~quantities.Quantity` with units Hertz.
        '''
        return pq.Quantity(float(self.query('FREQ?')),pq.hertz)
    @freq.setter
    def freq(self, newval):
        newval = float(assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude)
        
        self.sendcmd('FREQ {}'.format(newval))
    
    @property
    def phase(self):
        '''
        Gets/set the phase of the internal reference signal.
        
        Set value should be -360deg <= newval < +730deg.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units degrees.
        :type: `~quantities.Quantity` with units degrees.
        '''
        return pq.Quantity(float(self.query('PHAS?')), pq.degrees)
    phase.setter
    def phase(self, newval):
        newval = float(assume_units(newval, pq.degree)
                        .rescale(pq.degree).magnitude)
        if (newval >= 730) or (newval <- 360):
            raise ValueError('Phase must be -360 <= phase < +730')
        self.sendcmd('PHAS {}'.format(newval))
    
    @property
    def amplitude(self):
        '''
        Gets/set the amplitude of the internal reference signal.
        
        Set value should be 0.004 <= newval <= 5.000
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units volts. Value should be specified as peak-to-peak.
        :type: `~quantities.Quantity` with units volts peak-to-peak.
        '''
        return pq.Quantity(float(self.query('SLVL?')), pq.volt)
    @amplitude.setter
    def amplitude(self, newval):
        newval = float(assume_units(newval, pq.volt).rescale(pq.volt).magnitude)
        if ((newval > 5) or (newval < 0.004)):
            raise ValueError('Amplitude must be +0.004 <= amplitude <= +5 .')
        self.sendcmd('SLVL {}'.format(newval))
        
    @property
    def input_shield_ground(self):
        '''
        Function sets the input shield grounding to either 'float' or 'ground'.
        
        grounding: Desired input shield grounding
        grounding = {float|ground},string
        '''
        return int(self.query('IGND?')) == 1
    @input_shield_ground.setter
    def input_shield_ground(self, newval):
        self.sendcmd('IGND {}'.format(1 if newval else 0))
    
    @property 
    def coupling(self):
        '''
        Gets/sets the input coupling to either 'ac' or 'dc'.
        
        :type: `SRS830Coupling`
        '''
        return SRS830Coupling[self.query('ICPL?')]
    @coupling.setter
    def coupling(self, newval):
        if not isinstance(newval, EnumValue) or 
                (newval.enum is not SRS830Coupling):
            raise TypeError("Input coupling setting must be a "
                              "SRS830Coupling value, got {} "
                              "instead.".format(type(newval)))
        self.sendcmd('ICPL {}'.format(newval.value))
        
    @property
    def sample_rate(self):
        '''
        Gets/sets the data sampling rate of the lock-in.
        
        Acceptable set values are :math:`2^n` where :math:`n=\{-4...+9\}` or
            the string `trigger`.
        
        :type: `~quantities.Quantity` with units Hertz.
        '''
        return pq.Quantity(float(self.query('SRAT?')), pq.Hz)
    @sample_rate.setter
    def sample_rate(self, newval):
        if isinstance(newval, str):
            newval = newval.lower()
            if newval == 'trigger':
                self.sendcmd('SRAT 14')
        
        if newval in VALID_SAMPLE_RATES:
            self.sendcmd('SRAT {}'.format(VALID_SAMPLE_RATES.index(newval)))
        else:
            raise ValueError('Valid samples rates given by {} and "trigger".'
                                .format(VALID_SAMPLE_RATES))
    
    @property
    def buffer_mode(self):
        '''
        Gets/sets the end of buffer mode.
        
        This sets the behaviour of the instrument when the data storage buffer
        is full. Setting to `one_shot` will stop acquisition, while `loop`
        will repeat from the start.
        
        :type: `SRS830BufferMode`
        '''
        return SRS830BufferMode[self.query('SEND?')]
    @buffer_mode.setter
    def buffer_mode(self, newval):
        if not isinstance(newval, EnumValue) or 
                (newval.enum is not SRS830BufferMode):
            raise TypeError("Input coupling setting must be a "
                              "SRS830BufferMode value, got {} "
                              "instead.".format(type(newval)))
        self.sendcmd('SEND {}'.format(newval.value))     
    
    @property
    def num_data_points(self):
        '''
        Gets the number of data sets in the SRS830 buffer.
        
        :type: `int`
        '''
        return int( self.query('SPTS?') )
    
    @property    
    def data_transfer(self):
        '''
        Gets/sets the data transfer status.
        
        Note that this function only makes use of 2 of the 3 data transfer modes
        supported by the SRS830. The supported modes are FAST0 and FAST2. The
        other, FAST1, is for legacy systems which this package does not support.
        
        :type: `bool`
        '''
        return int(self.query('FAST?')) == 2
    @data_transfer.setter
    def data_transfer(self, newval):
        self.sendcmd('FAST {}'.format(2 if newval else 0))
    
    ## AUTO- METHODS ##
    
    def auto_offset(self,mode):
        '''
        % Function sets a specific channel mode to auto offset. This is the
        % same as pressing the auto offset key on the display.
        % It sets the offset of the mode specified to zero.
        %
        % mode: Mode who's offset will be set to zero.
        % mode = {X|Y|R},string
        '''
        if not isinstance(mode,str):
            raise Exception('Parameter "mode" must be a string.')
            
        mode = mode.lower()
        
        valid = ['x','y','r']
        if mode in valid:
            mode = str( valid.index(mode) + 1 )
        else:
            raise Exception('Only "x" , "y" and "r" are valid modes '
                              'for setting the auto offset.')
        
        self.write( 'AOFF ' + mode )
    
    def auto_phase(self):
        '''
        % Function sets the lock-in to auto phase.
        % This does the same thing as pushing the auto phase button.
        % Do not send this message again without waiting the correct amount
        % of time for the lock-in to finish.
        '''
        self.write('APHS')
        
    ## META-METHODS ##
    
    def init(self, sample_rate, buffer_mode):
        '''
        Wrapper function to prepare the srs830 for measurement.
        Sets both the data sampling rate and the end of buffer mode
        
        sampleRate: The sampling rate in Hz, or the string "trigger".
        When specifing the rate in Hz, acceptable values are integer
        powers of 2. This means 2^n, n={-4...+9}.
        sampleRate = {<freq>|TRIGGER}
        
        mode = {1SHOT|LOOP},string
        '''
        self.clear_data_buffer()
        self.sample_rate = sample_rate
        self.buffer_mode = buffer_mode
    
    def start_data_transfer(self):
        '''
        Wrapper function to start the actual data transfer.
        Sets the transfer mode to FAST2, and triggers the data transfer
        to start after a delay of 0.5 seconds.
        '''
        self.data_transfer('on') # FIXME
        self.start_scan()
    
    ## OTHER METHODS ##
  
    def set_offset_expand(self,mode,offset,expand):
        '''
        % Function sets the channel offset and expand parameters.
        % Offset is a percentage, and expand is given as a multiplication
        % factor of 1, 10, or 100.
        %
        % mode: The channel mode that you wish to change the offset /
        % expand of
        % mode = {X|Y|R},sting
        %
        % offset: Offset of the mode, given as a percent
        % offset = <-105...+105>,float
        %
        % expand: Expansion factor for the measurement
        % expand = {1|10|100},integer
        '''
        if not isinstance(mode,str):
            raise Exception('Parameter "mode" must be a string.')
            
        mode = mode.lower()
        
        valid = ['x','y','r']
        if mode in valid:
            mode = valid.index(mode) + 1
        else:
            raise Exception('Only "x" , "y" and "r" are valid modes for '
                              'setting the offset & expand.')
        
        if type(offset) != type(int()) or type(offset) != type(float()):
            raise Exception('Offset parameter must be an integer or a float.')
        if type(expand) != type(int()) or type(expand) != type(float()):
            raise Exception('Expand parameter must be an integer or a float.')
        
        if offset > 105 or offset < -105:
            raise Exception('Offset mustbe -105 <= offset <= +105 .')
        
        valid = [1,10,100]
        if expand in valid:
            expand = valid.index(expand)
        else:
            raise Exception('Expand must be 1, 10, 100.')
        
        self.write( 'OEXP %s,%s,%s' % (mode,offset,expand) )
    
    
      
    def start_scan(self):
        '''
        % After setting the data transfer on via the dataTransfer function,
        % this is used to start the scan. The scan starts after a delay of
        % 0.5 seconds.
        '''
        self.write('STRD')
       
    def pause(self):
        '''
        Has the instrument pause data capture.
        '''
        self.write('PAUS')
      
    def data_snap(self,mode1,mode2):
        '''
        Function takes a snapshot of the current parameters are defined
        by variables mode1 and mode2.
        For combinations (X,Y) and (R,THETA) , they are taken at the same
        instant. All other combinations are done sequentially, and may
        not represent values taken from the same timestamp.
        
        Returns a list of floats, arranged in the order that they are
        given in the function input parameters.
        
        mode = {X|Y|R|THETA|AUX1|AUX2|AUX3|AUX4|REF|CH1|CH2},string
        '''
        if not isinstance(mode1,str):
            raise Exception('Parameter "mode1" must be a string.')
        if not isinstance(mode2,str):
            raise Exception('Parameter "mode2" must be a string.')
            
        mode1 = mode1.lower()
        mode2 = mode2.lower()
        
        if mode1 == mode2:
            raise Exception('Both parameters for teh data snapshot are the same.')
        
        valid = ['x','y','r','theta','aux1','aux2','aux3','aux4','ref','ch1','ch2']
        if mode1 in valid:
            mode1 = valid.index(mode1) + 1
        else:
            raise Exception('Only "x" , "y" , "r" , "theta" , "aux1" , "aux2" , "aux3" , "aux4" , "ref" , "ch1" and "ch2" are valid snapshot parameters.')
        
        if mode2 in valid:
            mode2 = valid.index(mode1) + 1
        else:
            raise Exception('Only "x" , "y" , "r" , "theta" , "aux1" , "aux2" , "aux3" , "aux4" , "ref" , "ch1" and "ch2" are valid snapshot parameters.')
        
        result = self.query( 'SNAP? %s,%s' % (mode1,mode2) )
        return map( float, result.split(',') )
    
    def read_data_buffer(self,channel):
        '''
        Function reads the entire data buffer for a specific channel.
        Transfer is done in ASCII mode. Although binary would be faster,
        I haven't yet figured out how to get that to work.
        
        Returns a list of floats containing instrument's measurements.
        
        channel: Channel data buffer to read from
        channel = {CH1|CH2|1|2},string/integer
        '''
        if not isinstance(channel,str) and not isinstance(channel,int):
            raise Exception('Parameter "channel" must be a string or an integer.')
        
        if isinstance(channel,str):
            channel = channel.lower()
        
        if channel == 'ch1' or channel == '1' or channel == 1:
            channel = 1
        elif channel == 'ch2' or channel == '2' or channel == 2:
            channel = 2
        else:
            raise Exception('Only "ch1" and "ch2" are valid channels.')
    
        N = self.numDataPoints() - 1 # Retrieve number of data points stored
        
        # Query device for entire buffer, returning in ASCII, then
        # converting to an array of doubles before returning to the
        # calling method
        return     map( float, self.query( 'TRCA?%s,0,%s' % (channel,N) ).split(',') )
    
    def clear_data_buffer(self):
        '''
        Clears the data buffer of the SRS830.
        '''
        self.write('REST')
    
    def take_measurement(self, sample_rate, num_samples):
        numSamples = float(num_samples)
        if numSamples > 16383:
            raise ValueError('Number of samples cannot exceed 16383.')
        
        sample_time = math.ceil( num_samples/sample_rate )
        
        self.init(sample_rate, SRS830BufferMode['one_shot'])
        self.start_data_transfer()
        
        print 'Sampling will take ' + sample_time + ' seconds.'
        time.sleep(sample_time)
        
        self.pause()
        
        ch1 = self.read_data_buffer('ch1')
        ch2 = self.read_data_buffer('ch2')
        
        return [ch1,ch2]
               
    def set_channel_display(self,channel,display,ratio):
        '''
        % Function sets the display of the two channels.
        % Channel 1 can display X, R, X Noise, Aux In 1, Aux In 2
        % Channel 2 can display Y, Theta, Y Noise, Aux In 3, Aux In 4
        %
        % Channel 1 can have ratio of None, Aux In 1, Aux In 2
        % Channel 2 can have ratio of None, Aux In 3, Aux In 4
        %
        % channel = {CH1|CH2|1|2},string/int
        % display = {X|Y|R|THETA|XNOISE|YNOISE|AUX1|AUX2|AUX3|AUX4},string
        % ratio = {NONE|AUX1|AUX2|AUX3|AUX4},string
        '''
        if not isinstance(channel,str) and not isinstance(channel,int):
            raise Exception('Parameter "channel" must be a string or integer.')
        if not isinstance(display,str):
            raise Exception('Parameter "display" must be a string.')
        if not isinstance(ratio,str):
            raise Exception('Parameter "ratio" must be a string.')
        
        if type(channel) == type(str()):    
            channel = channel.lower()
        display = display.lower()
        ratio = ratio.lower()
        
        if channel == 'ch1' or channel == '1' or channel == 1:
            channel = '1'
            valid = ['x','r','xnoise','aux1','aux2']
            if display in valid:
                display = str( valid.index(display) )
            else:
                raise Exception('Only "x" , "r" , "xnoise" , "aux1" and "aux2" are valid displays for channel 1.')
            
            valid = ['none','aux1','aux2']
            if ratio in valid:
                ratio = str( valid.index(ratio) )
            else:
                raise Exception('Only "none" , "aux1" and "aux2" are valid ratios for channel 1.')
        
        elif channel == 'ch2' or channel == '2' or channel == 2:
            channel = '2'
            valid = ['y','theta','ynoise','aux3','aux4']
            if display in valid:
                display = str( valid.index(display) )
            else:
                raise Exception('Only "y" , "theta" , "ynoise" , "aux3" and "aux4" are valid displays for channel 2.')
                
            valid = ['none','aux3','aux4']
            if ratio in valid:
                ratio = str( valid.index(ratio) )
            else:
                raise Exception('Only "none" , "aux3" and "aux4" are valid ratios for channel 2.')
        
        else:
            raise Exception('Only "ch1" and "ch2" are valid channels.')
        
        self.write( 'DDEF %s,%s,%s' % (channel,display,ratio) )        
            
            
            
            
            
