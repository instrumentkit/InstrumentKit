#!/usr/bin/python
# Filename: keithley2182.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class Keithley2182(Instrument):
    def __init__(self, port, address,timeout_length):
        super(Keithley2182, self).__init__(self,port,address,timeout_length)
        
    def configure(self,mode = None):
        '''
        
        '''
        if mode == None:
            return self.query(':CONF?')
        
        valid = ['voltage','temperature']
        valid2 = ['volt','temp']
        
        if not isinstance(mode,str):
            raise Exception('Mode must be specified as a string.')
        
        mode = mode.lower()
        if mode in valid:
            mode = valid2[valid.index(mode)]
        elif mode not in valid2:
            raise Exception('Valid measurement modes are "VOLTage" and "TEMPerature".')
        
        self.write(':CONF:' + mode)
        
    def fetch(self):
        '''
        Transfer readings from instrument memory to the output buffer, and thus to the computer.
        If currently taking a reading, the instrument will wait until it is complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not recommended to transfer a large number of data points using GPIB.
        
        Returns a list of floats.
        '''
        return map( float, self.query(':FETC?').split(',') )
    
    def measure(self,mode):
        '''
        
        '''
        valid = ['voltage','temperature']
        valid2 = ['volt','temp']
        
        if not isinstance(mode,str):
            raise Exception('Mode must be specified as a string.')
        
        mode = mode.lower()
        if mode in valid:
            mode = valid2[valid.index(mode)]
        elif mode not in valid2:
            raise Exception('Valid measurement modes are "VOLTage" and "TEMPerature".')
        
        return float( self.query(':MEAS:' + mode + '?') )
        
    def triggerSource(self,source=None):
        '''
        This function sets the trigger source for measurements.
        
        If no source is specified, function queries the instrument for the current setting. This is returned as a string. An example value is "EXT", without quotes.
            
        source: Desired trigger source
        source = {IMMediate|EXTernal|BUS|TIMer|MANual},string
        '''
        if source == None: # If source was not specified, perform query.
            return self.query(':TRIG:SOUR?')
        
        if not isinstance(source,str):
            raise Exception('Parameter "source" must be a string.')
        source = source.lower()
        
        valid = ['immediate','external','bus','timer','manual']
        valid2 = ['imm','ext','bus','tim','man']
        
        if source in valid:
            source = valid2[valid.index(source)]
        elif source not in valid2:
            raise Exception('Trigger source must be "immediate", "external", "bus", "timer", or "manual".')
        
        self.write(':TRIG:SOUR ' + source)
        
    def triggerCount(self,count = None):
        '''
        This function sets the number of triggers that the 2182 will accept before returning to an "idle" trigger state.
        
        Note that if the sample count parameter has been changed, the number of readings taken will be a multiplication of sample count and trigger count (see function sampleCount).
        
        If count is not specified, function queries the instrument for the current trigger count setting. This is returned as an integer.
        
        count: Number of triggers before returning to an "idle" trigger state.
        count = {<count>|INFinity},integer/string
        '''
        if count == None: # If count not specified, perform query.
            return int( self.query('TRIG:COUN?') )
        
        if isinstance(count,str):
            count = count.lower()
            if count == 'infinity':
                count = 'inf'
            elif count != 'inf':
                raise Exception('Valid trigger count value is "infinity" when specified as a string.')
        elif isinstance(count,int):
            if count < 1 or count > 9999:
                raise Exception('Trigger count must be a between 1 and 9999.')
            count = str(count)
        else:
            raise Exception('Trigger count must be a string or an integer.')
        
        self.write( ':TRIG:COUN ' + str(count) )
        
    def triggerDelay(self,period=None):
        '''
        This command sets the time delay which the instrument will use following receiving a trigger event before starting the measurement.
        
        Note that this function does not contain proper screening for "period" being a malformed string. This allows you to include the units of your specified value in the string.
        If no units are specified, the number will be read by the instrument as having units of seconds.
        
        If no period is specified, function queries the instrument for the current trigger delay and returns a float.
        
        period: Time between receiving a trigger event and the instrument taking the reading. Values range from 0s to ~3600s, in ~20us increments.
        period = {<seconds>|AUTO},number/string 
        '''
        if period == None: # If no period is specified, perform query.
            return float( self.query(':TRIG:DEL?') )
        
        if isinstance(period,str):
            period = period.lower()
            if period == 'auto':
                self.write(':TRIG:DEL:AUTO 1')
            #elif period not in valid2:
            #    raise Exception('Valid trigger delay values are "minimum", "maximum", and "def" when specified as a string.')
        elif isinstance(period,int) or isinstance(period,float):
            if period < 0 or period >  999999.999:
                raise Exception('The trigger delay needs to be between 0 and 1000000 seconds.')
        
        self.write( ':TRIG:DEL ' + str(period) )
        
    def sampleCount(self,count = None):
        '''
        This command sets the number of readings (samples) that the meter will take per trigger.
        
        Note that if the sample count parameter has been changed, the number of readings taken will be a multiplication of sample count and trigger count (see function sampleCount).
            
        If count is not specified, function queries the instrument for the current sample count and returns an integer.
        
        count: Number of triggers before returning to an "idle" trigger state.
        count = <count>,integer
        '''
        if count == None: # If count is not specified, perform query.
            return int( self.query(':SAMP:COUN?') )
        
        if isinstance(count,int):
            if count < 1 or count > 1024:
                raise Exception('Trigger count must be an integer, 1 to 1024.')
            count = str(count)
        else:
            raise Exception('Trigger count must be an integer.')
        
        self.write( ':SAMP:COUN ' + str(count) )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
