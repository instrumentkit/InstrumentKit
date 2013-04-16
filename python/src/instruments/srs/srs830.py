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
    
class SRS830InputShield(Enum):
    floating = 0
    grounded = 1
    
class SRS830Coupling(Enum):
    ac = 0
    dc = 1

## CONSTANTS ###################################################################

VALID_SAMPLE_RATES = [2.0**n for n in xrange(-4, 10)] + 

## CLASSES #####################################################################

class SRS830(SCPIInstrument):
    def __init__(self, port, address, timeout_length, outx_mode=None):
        super(SRS830, self).__init__(self,port,address,timeout_length)
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
        return pq.Quantity(float(self.query('FREQ?')),pq.hertz)
    @freq.setter
    def freq(self, newval):
        newval = float(assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude)
        
        self.sendcmd('FREQ {}'.format(newval))
    
    @property
    def phase(self):
        '''
        Function sets the phase of the internal reference signal.
        
        phase: Desired phase
        phase = <-360...+729.99>,float
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
        Function sets the amplitude of the internal reference signal.
        
        amplitude: Desired peak-to-peak voltage
        amplitude = <0.004...5>,float
        '''
        return pq.Quantity(float(self.query('SLVL?')), pq.volt)
    @amplitude.setter
    def amplitude(self, newval):
        newval = float(assume_units(newval, pq.volt).rescale(pq.volt).magnitude)
        if ((newval > 5) or (newval < 0.004)):
            raise ValueError('Amplitude must be +0.004 <= amplitude <= +5 .')
        self.sendcmd('SLVL {}'.format(newval))
        
    @property
    def input_shield_grounding(self):
        '''
        Function sets the input shield grounding to either 'float' or 'ground'
        
        grounding: Desired input shield grounding
        grounding = {float|ground},string
        '''
        return SRS830InputShield[self.query('IGND?')]
    @input_shield_grounding.setter
    def input_shield_grounding(self, newval):
        if not isinstance(newval, EnumValue) or 
                (newval.enum is not SRS830InputShield):
            raise TypeError("Input shield grounding setting must be a "
                              "SRS830InputShield value, got {} "
                              "instead.".format(type(newval)))
        self.sendcmd('IGND {}'.format(newval.value))
    
    @property 
    def coupling(self):
        '''
        Function sets the input coupling to either 'ac' or 'dc'
        
        coupling: Desired input coupling mode
        coupling = {ac|dc},string
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
        Function sets the data sampling rate of the lock-in
        
        sampleRate: The sampling rate, in Hz as a float, or the string 'trigger'.
        When specifying the rate in Hz, acceptable values are integer powers of 2.
        This means 2^n, n={-4...+9}
        sampleRate = {<freq>,TRIGGER}
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
    
    # Set End of Buffer Mode    
    def setEndOfBufferMode(self,mode):
        '''
        Function sets the end of buffer mode
        
        mode: Desired end of buffer mode
        mode = {1SHOT,LOOP},string
        '''
        if not isinstance(mode,str):
            raise Exception('Parameter "mode" must be a string.')
            
        mode = mode.lower()
        valid = ['1shot','loop']
        
        if mode in valid:
            mode = str( valid.index(mode) )
        else:
            raise Exception('Only "1shot" and "loop" are valid end of buffer modes.')
        
        self.write( 'SEND ' + mode )
    
    # Set Channel Display    
    def setChannelDisplay(self,channel,display,ratio):
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
    
    # Set the Channel Offset and Expand    
    def setOffsetExpand(self,mode,offset,expand):
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
            raise Exception('Only "x" , "y" and "r" are valid modes for setting the offset & expand.')
        
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
    
    # Enable Auto Offset
    def autoOffset(self,mode):
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
            raise Exception('Only "x" , "y" and "r" are valid modes for setting the auto offset.')
        
        self.write( 'AOFF ' + mode )
    
    # Enable Auto Phase
    def autoPhase(self):
        '''
        % Function sets the lock-in to auto phase.
        % This does the same thing as pushing the auto phase button.
        % Do not send this message again without waiting the correct amount
        % of time for the lock-in to finish.
        '''
        self.write('APHS')
    
    # Set Data Transfer on/off
    def dataTransfer(self,mode):
        '''
        % Function used to turn the data transfer from the lockin on or off
        %
        % mode: 
        % mode = {ON|OFF},string
        '''
        if not isinstance(mode,str):
            raise Exception('Parameter "mode" must be a string.')
            
        mode = mode.lower()
        
        if mode == 'off':
            mode = '0'
        elif mode == 'on':
            mode = '2'
        else:
            raise Exception('Only "on" and "off" are valid parameters for setDataTransfer.')
        
        self.write( 'FAST ' + mode )
    
    # Start Scan    
    def startScan(self):
        '''
        % After setting the data transfer on via the dataTransfer function,
        % this is used to start the scan. The scan starts after a delay of
        % 0.5 seconds.
        '''
        self.write('STRD')
    
    # Pause Data Capture    
    def pause(self):
        '''
        Has the instrument pause data capture.
        '''
        self.write('PAUS')
    
    # Start Data Transfer (wrapper)
    def init(self,sampleRate,EoBMode):
        '''
        Wrapper function to prepare the srs830 for measurement.
        Sets both the data sampling rate and the end of buffer mode
        
        sampleRate: The sampling rate in Hz, or the string "trigger".
        When specifing the rate in Hz, acceptable values are integer
        powers of 2. This means 2^n, n={-4...+9}.
        sampleRate = {<freq>|TRIGGER}
        
        mode = {1SHOT|LOOP},string
        '''
        self.clearDataBuffer()
        self.setSampleRate(sampleRate)
        self.setEndOfBufferMode(EoBMode)
    
    # Take Data Snapshot (wrapper)
    def startDataTransfer(self):
        '''
        Wrapper function to start the actual data transfer.
        Sets the transfer mode to FAST2, and triggers the data transfer
        to start after a delay of 0.5 seconds.
        '''
        self.dataTransfer('on')
        self.startScan()
            
    def dataSnap(self,mode1,mode2):
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
    
    # Read Data Buffer
    def readDataBuffer(self,channel):
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
    
    # Check number of data sets in buffer
    def numDataPoints(self):
        '''
        Function checks number of data sets in SRS830 buffer.
        Returns an integer.
        '''
        return int( self.query('SPTS?') )
    
    # Clear data (channel) buffer
    def clearDataBuffer(self):
        '''
        Clears the data buffer of the SRS830.
        '''
        self.write('REST')
    
    # Take measurement (wrapper function)
    def takeMeasurement(self,sampleRate,numSamples):
        numSamples = float( numSamples )
        if numSamples > 16383:
            raise Exception('Number of samples cannot exceed 16383.')
        
        sampleTime = math.ceil( numSamples/sampleRate )
        
        self.init(sampleRate,'1shot')
        self.startDataTransfer()
        
        print 'Sampling will take ' + sampleTime + ' seconds.'
        time.sleep(sampleTime)
        
        self.pause()
        
        print 'Sampling complete, reading channel 1.'
        ch1 = self.readDataBuffer('ch1')
        
        print 'Reading channel 2.'
        ch2 = self.readDataBuffer('ch2')
        
        return [ch1,ch2]
            
            
            
            
            
            
            
