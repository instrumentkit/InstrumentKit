#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# agilent34410a.py: Implementation of Agilent 34410A-specific functionality.
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

## IMPORTS #####################################################################

from instruments.generic_scpi import SCPIMultimeter

## CLASSES #####################################################################

class Agilent34410a(SCPIMultimeter):

    # NOTE: No __init__ needed, as it can just inherit.

    ## PROPERTIES ##
    
    @property
    def data_point_count(self):
        '''
        Gets the total number of readings that are located in reading memory (RGD_STORE).
        
        :type: `int`
        '''
        return int(self.query('DATA:POIN?'))
    
    
    ## STATE MANAGEMENT METHODS ##

    def init(self):
        '''
        Switch device from "idle" state to "wait-for-trigger state".
        Measurements will begin when specified triggering conditions are met, 
        following the receipt of the INIT command.
        
        Note that this command will also clear the previous set of readings 
        from memory.
        '''
        self.sendcmd('INIT')
    
    def abort(self):
        '''
        Abort all measurements currently in progress.
        '''
        self.sendcmd('ABOR')
    
    ## MEMORY MANAGEMENT METHODS ##

    def clear_memory(self):
        '''
        Clears the non-volatile memory of the Agilent 34410a.
        '''
        self.sendcmd('DATA:DEL NVMEM')
    
    def r(self, count):
        '''
        Have the multimeter perform a specified number of measurements and then 
        transfer them using a binary transfer method. Data will be cleared from 
        instrument memory after transfer is complete.
        
        :param int count: Number of samples to take.
        
        :rtype: numpy.array
        '''
        if not isinstance(count, int):
            raise TypeError('Parameter "count" must be an integer')
        if count == 0:
            msg = 'R?'
        else:
            msg = 'R? ' + str(count)
        
        self.sendcmd('FORM:DATA REAL,32')
        self.sendcmd(msg)
        return self.binblockread(4)
    
        
    # Configure measurement mode, using default parameters    
    def configure(self, mode=None, deviceRange=None, resolution=None):
        '''
        Change the measurement mode of the multimeter.
        No actual measurement will take place, but the instrument is then able 
        to do so using the INITiate or READ? command.
        
        All arguments are optional. Passing no arguments will query the device 
        for the current configuration settings. This returns a string such as 
        ``VOLT +1.000000E+01,+3.000000E-06``.
        
        :param str mode: Desired measurement mode, one of ``{CAPacitance|
            CONTinuity|CURRent:AC|CURRent:DC|DIODe|FREQuency|FRESistance|PERiod|
            RESistance|TEMPerature|VOLTage:AC|VOLTage:DC}``.
        :param deviceRange: It is recommended this is user specified, but is 
            optional. Sets the range of the instrument. No value checking when 
            passed as a number.
        :type deviceRange: `str` (one of ``MINimum, MAXimum, DEFault, 
            AUTOmatic``) or range
        :param float resolution: Measurement that the instrument will use. 
            This is ignored for most modes. It is assumed that the user has 
            entered a valid number.
        '''
        if mode == None: # If no arguments were passed, perform query and return
            return self.query('CONF?')
        
        if not isinstance(mode,str):
            raise Exception('Measurement mode must be a string.')
        mode = mode.lower()
        
        valid = ['cap','cont','curr:ac','curr:dc','diod','freq','fres','per','res','temp','volt:ac','volt:dc']
        valid2 = ['capacitance','continuity','current:ac','current:dc','diode','frequency','fresistance','period','resistance','temperature','voltage:ac','voltage:dc']
        
        if mode in ['4res','4 res','four res','f res']:
            mode = 'fres'
        
        if mode in valid2:
            mode = valid[valid2.index(mode)]
        elif mode not in valid:
            raise Exception('Valid measurement modes are: ' + str(valid2))
        
        if deviceRange == None: # If deviceRange default
            self.sendcmd( 'CONF:' + mode )
        else: # User specified range
            if isinstance(deviceRange,int) or isinstance(deviceRange,float): # If is an integer for a float
                pass # Assume the input is correct...
            elif isinstance(deviceRange,str): # If it is a string
                deviceRange = deviceRange.lower()
                valid = ['minimum','maximum','default','automatic']
                valid2 = ['min','max','def','auto']
                if deviceRange in valid:
                    deviceRange = valid2[valid.index(deviceRange)]
                elif deviceRange not in valid2:
                    raise Exception('When specified as a string, deviceRange must be "minimum", "maximum", "default", or "automatic".')
            else:
                raise Exception('Argument deviceRange must be a string or a number.')
            
            if resolution == None: # If resolution is default
                self.sendcmd( 'CONF:' + mode + ' ' + str(deviceRange) )
            else: # User specified resolution
                self.sendcmd( 'CONF:%s %s,%s' %(mode,deviceRange,resolution) )
        
    ## DATA READING METHODS ##
    
    def fetch(self):
        '''
        Transfer readings from instrument memory to the output buffer, and 
        thus to the computer.
        If currently taking a reading, the instrument will wait until it is 
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? 
        command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not 
        recommended to transfer a large number of
        data points using this method.
        
        :rtype: `list` of `float` elements
        '''
        return map(float, self.query( 'FETC?' ).split(',') )
    
    def read_data(self, sample_count):
        '''
        Transfer specified number of data points from reading memory 
        (RGD_STORE) to output buffer.
        First data point sent to output buffer is the oldest.
        Data is erased after being sent to output buffer.
        
        :param int sample_count: Number of data points to be transfered to 
            output buffer. If set to -1, all points in memory will be 
            transfered.
        
        :rtype: `list` of `float` elements
        '''
        if not isinstance(sampleCount,int):
            raise TypeError('Parameter "sampleCount" must be an integer.')
        
        if sampleCount == -1:
            sampleCount = self.data_point_count
        
        self.sendcmd('FORM:DATA ASC')
        return map( float, self.query('DATA:REM? ' + str(sampleCount)).split(',') )
    
    def read_data_NVMEM(self):
        '''
        Returns all readings in non-volatile memory (NVMEM).
        
        :rtype: `list` of `float` elements
        '''
        return map( float, self.query('DATA:DATA? NVMEM').split(',') )
    
    # Read the Last Data Point
    def readLastData(self):
        '''
        Retrieve the last measurement taken. This can be executed at any time, 
        including when the instrument is currently taking measurements.
        If there are no data points available, the value ``9.91000000E+37`` is 
        returned.
        
        :rtype: `float` or `int` (if an error occurs)
        '''
        data = self.query('DATA:LAST?')
        
        if data == '9.91000000E+37':
            return int(data)
        else:
            data = data[0:data.index(' ')] # Remove units
            return float(data)
    
    # Read: Set to "Wait-for-trigger" state, and immediately send result to output
    def read(self):
        '''
        Switch device from "idle" state to "wait-for-trigger" state. 
        Immediately after the trigger conditions are met, the data will be sent 
        to the output buffer of the instrument.
        
        This is similar to calling `~Agilent34410a.init` and then immediately 
        following `~Agilent34410a.fetch`.
        
        :rtype: `float`
        '''
        return float( self.query('READ?') )
    
    # Set Trigger Source
    def triggerSource(self, source=None):
        '''
        This function sets the trigger source for measurements.
        The 34410a accepts the following trigger sources:
        
        #. "Immediate": This is a continuous trigger. This means the trigger 
        signal is always present.
        #. "External": External TTL pulse on the back of the instrument. It 
        is active low. 
        #. "Bus": Causes the instrument to trigger when a ``*TRG`` command is 
        sent by software. This means calling the trigger() function.
        
        If no source is specified, function queries the instrument for the 
        current setting. This is returned as a string. An example value is 
        "EXT", without quotes.
            
        :param str source: Desired trigger source, one of 
            ``{IMMediate|EXTernal|BUS}``.
            
        :rtype: `str`
        '''
        if source == None: # If source was not specified, perform query.
            return self.query('TRIG:SOUR?')
        
        if not isinstance(source,str):
            raise Exception('Parameter "source" must be a string.')
        source = source.lower()
        
        valid = ['immediate','external','bus']
        valid2 = ['imm','ext','bus']
        
        if source in valid:
            source = valid2[valid.index(source)]
        elif source not in valid2:
            raise Exception('Trigger source must be "immediate", "external", or "bus".')
        
        self.sendcmd('TRIG:SOUR ' + source)
        
    # Trigger Count
    def triggerCount(self,count = None):
        '''
        This function sets the number of triggers that the multimeter will 
        accept before returning to an "idle" trigger state.
        
        Note that if the sample count parameter has been changed, the number 
        of readings taken will be a multiplication of sample count and trigger 
        count (see function sampleCount).
        If specified as a string, the following options apply:
        
        #. "MINimum": 1 trigger
        #. "MAXimum": 50 000 triggers
        #. "DEF": Default
        #. "INFinity": Continuous. When the buffer is filled, the oldest data 
            points are overwritten.
        
        If count is not specified, function queries the instrument for the 
        current trigger count setting. This is returned as an integer.
            
        Note that when using triggered measurements, it is recommended that you 
        disable autorange by either explicitly disabling it or specifying your 
        desired range.
        
        :param count: Number of triggers before returning to an "idle" trigger 
            state. One of ``{<count>|MINimum|MAXimum|DEF|INFinity}``
        :type count: `int` or `str`
        
        :rtype: `int`
        '''
        if count == None: # If count not specified, perform query.
            return int( self.query('TRIG:COUN?') )
        
        if isinstance(count,str):
            count = count.lower()
            valid = ['minimum','maximum','def','infinity']
            valid2 = ['min','max','def','inf']
            if count in valid:
                count = valid2[valid.index(count)]
            elif count not in valid2:
                raise Exception('Valid trigger count values are "minimum", "maximum", "def", and "infinity" when specified as a string.')
        elif isinstance(count,int):
            if count < 1:
                raise Exception('Trigger count must be a positive integer.')
            count = str(count)
        else:
            raise Exception('Trigger count must be a string or an integer.')
        
        self.sendcmd( 'TRIG:COUN ' + str(count) )
        
    # Trigger delay
    def triggerDelay(self,period=None):
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
        
        :param period: Time between receiving a trigger event and the 
            instrument taking the reading. Values range from ``0s`` to 
            ``~3600s``, in ``~20us`` increments. One of ``{<seconds>|MINimum|
            MAXimum|DEF}``
        :type period: `int` or `str`
        
        :rtype: `int`
        '''
        if period == None: # If no period is specified, perform query.
            return float( self.query('TRIG:DEL?') )
        
        if isinstance(period,str):
            period = period.lower()
            valid = ['minimum','maximum','def']
            valid2 = ['min','max','def']
            if period in valid:
                period = valid2[valid.index(period)]
            #elif period not in valid2:
            #    raise Exception('Valid trigger delay values are "minimum", "maximum", and "def" when specified as a string.')
        elif isinstance(period,int) or isinstance(period,float):
            if period < 0 or period > 3600:
                raise Exception('The trigger delay needs to be between 0 and 3600 seconds.')
        
        self.sendcmd( 'TRIG:DEL ' + str(period) )
    
    # Sample Count
    def sampleCount(self, count=None):
        '''
        This command sets the number of readings (samples) that the multimeter 
        will take per trigger.
        The time between each measurement is defined with the sampleTimer 
        function.
        
        Note that if the sample count parameter has been changed, the number of 
        readings taken will be a multiplication of sample count and trigger 
        count (see function sampleCount).
        If specified as a string, the following options apply:
        
        #. "MINimum": 1 sample per trigger
        #. "MAXimum": 50 000 samples per trigger
        #. "DEF": Default, 1 sample
            
        If count is not specified, function queries the instrument for the 
        current smaple count and returns an integer.
            
        Note that when using triggered measurements, it is recommended that you 
        disable autorange by either explicitly disabling it or specifying your 
        desired range.
        
        :param count: Number of triggers before returning to an "idle" trigger 
            state. One of ``{<count>|MINimum|MAXimum|DEF|INFinity}``
        :type count: `int` or `str`
        
        :rtype: `int`
        '''
        if count == None: # If count is not specified, perform query.
            return int( self.query('SAMP:COUN?') )
        
        if isinstance(count,str):
            count = count.lower()
            valid = ['minimum','maximum','def']
            valid2 = ['min','max','def']
            if count in valid:
                count = valid2[valid.index(count)]
            elif count not in valid2:
                raise Exception('Valid sample count values are "minimum", "maximum", and "def" when specified as a string.')
        elif isinstance(count,int):
            if count < 1:
                raise Exception('Trigger count must be a positive integer.')
            count = str(count)
        else:
            raise Exception('Trigger count must be a string or an integer.')
        
        self.sendcmd( 'SAMP:COUN ' + str(count) )
    
    # Sample Timer
    def sampleTimer(self, period=None):
        '''
        This command sets the sample interval when the sample counter is 
        greater than one and when the sample source is set to timer 
        (timed sampling).
        
        This command does not effect the delay between the trigger occuring and 
        the start of the first sample. This trigger delay is set with the 
        triggerDelay function.
        
        Note that this function does not contain proper screening for "period" 
        being a malformed string. This allows you to include the units of your 
        specified value in the string.
        If no units are specified, the number will be read by the instrument as 
        having units of seconds.
        
        If period is not specified, function queries the instrument for the 
        current sample interval and returns it as a float.
        
        :param period: Time period between samples. An example including units 
            is ``500 ms``. One of period = ``{<period>|MINimum|MAXimum}``.
        :type period: `float` or `str`
        
        :rtype: `float`
        '''
        if period == None: # If period is not specified, perform query.
            return float( self.query('SAMP:TIM?') )
        
        if isinstance(period,str):
            period = period.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if period in valid:
                period = valid2[valid.index(period)]
            #elif period not in valid2:
            #    raise Exception('Valid sample timer values are "minimum" and "maximum" when specified as a string.')
        elif isinstance(period,int) or isinstance(period,float):
            if period < 0:
                raise Exception('Trigger count must be a positive integer.')
        
        self.sendcmd( 'SAMP:TIM ' + str(period) )
        
    # Sample Source
    def sampleSource(self,source = None):
        '''
        This command determines whether the trigger delay or the sample timer 
        is used to determine sample timing when the sample count is greater 
        than one.
        In both cases, the first sample is taken one trigger delay time after 
        the trigger. After that, it depends on which mode is used:
        
        #. "IMMediate": The trigger delay time is inserted between successive 
            samples. After the first measurement is completed, the instrument waits 
            the time specified by the trigger delay and then performs the next 
            sample.
        #. "TIMer": Successive samples start one sample interval after the 
            START of the previous sample.
        
        If source is not specified, function queries the instrument for the 
        currently set sample source and returns its as a string. An example 
        is "TIM" without quotes.
        
        :param str source: Desired successive sample timing mode. One of
            ``{IMMediate|TIMer}``
        '''
        if source == None:
            return self.query('SAMP:SOUR?')
        
        if not isinstance(source,str):
            raise Exception('Sample source must be specified as a string')
        
        valid = ['immediate','timer']
        valid2 = ['imm','tim']
        source = source.lower()
        if source in valid:
            source = valid2[valid.index(source)]
        elif source not in valid2:
            raise Exception('Valid sample sources are "immediate" and "timer".')
        
        self.sendcmd( 'SAMP:SOUR ' + str(source) )
    
        
