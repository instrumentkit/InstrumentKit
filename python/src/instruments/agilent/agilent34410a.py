#!/usr/bin/python
# Filename: agilent34410a.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class Agilent34410a(Instrument):
    def __init__(self, port, address, timeout_length):
        super(Agilent34410a, self).__init__(self,port,address,timeout_length)
    
    # Clear Memory    
    def clearMemory(self):
        '''
        Clears the non-volatile memory of the Agilent 34410a.
        '''
        self.write('DATA:DEL NVMEM')
    
    # Measurement
    def measure(self,mode):
        '''
        Instruct the multimeter to perform a one time measurement. 
        The instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are directly sent to the instrument's output buffer.
        
        Function returns a float.
        
        :param str mode: Desired measurement mode, one of ``{CAPacitance|CONTinuity|CURRent:AC|CURRent:DC|DIODe|FREQuency|FRESistance|PERiod|RESistance|TEMPerature|VOLTage:AC|VOLTage:DC}``.
        '''
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
        
        return float( self.query( 'MEAS:' + mode.upper() + '?' ) )
    
    # Configure measurement mode, using default parameters    
    def configure(self, mode=None, deviceRange=None, resolution=None):
        '''
        Change the measurement mode of the multimeter.
        No actual measurement will take place, but the instrument is then able to do so using the INITiate or READ? command.
        
        All arguments are optional. Passing no arguments will query the device for the current configuration settings. This returns a string such as ``VOLT +1.000000E+01,+3.000000E-06``.
        
        :param str mode: Desired measurement mode, one of ``{CAPacitance|CONTinuity|CURRent:AC|CURRent:DC|DIODe|FREQuency|FRESistance|PERiod|RESistance|TEMPerature|VOLTage:AC|VOLTage:DC}``.
        :param deviceRange: It is recommended this is user specified, but is optional. Sets the range of the instrument. No value checking when passed as a number.
        :type mode: `str` (one of ``MINimum, MAXimum, DEFault, AUTOmatic``) or range
        :param float resolution: Measurement that the instrument will use. This is ignored for most modes. It is assumed that the user has entered a valid number.
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
            self.write( 'CONF:' + mode )
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
                self.write( 'CONF:' + mode + ' ' + str(deviceRange) )
            else: # User specified resolution
                self.write( 'CONF:%s %s,%s' %(mode,deviceRange,resolution) )
        
    # Fetch
    def fetch(self):
        '''
        Transfer readings from instrument memory to the output buffer, and thus to the computer.
        If currently taking a reading, the instrument will wait until it is complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not recommended to transfer a large number of data points using GPIB.
        
        :rtype: `list` of `float` elements
        '''
        return map(float, self.query( 'FETC?' ).split(',') )
    
    # Data Point Count
    def dataPointCount(self):
        '''
        Returns the total number of readings that are located in reading memory (RGD_STORE).
        
        :rtype: `int`
        '''
        return int( self.query('DATA:POIN?') )
    
    # Read Data in Reading Memory (RDG_STORE)    
    def readData(self,sampleCount):
        '''
        Transfer specified number of data points from reading memory (RGD_STORE) to output buffer.
        First data point sent to output buffer is the oldest.
        Data is erased after being sent to output buffer.
        
        :param int sampleCount: Number of data points to be transfered to output buffer. If set to 0, all points in memory will be transfered.
        
        :rtype: `list` of `float` elementa
        '''
        if not isinstance(sampleCount,int):
            raise TypeError('Parameter "sampleCount" must be an integer.')
        
        if sampleCount == 0:
            sampleCount = self.dataPointCount()
        
        self.write('FORM:DATA ASC')
        return map( float, self.query('DATA:REM? ' + str(sampleCount)).split(',') )
    
    # Read Data in Non-Volatile Memory (NVMEM)
    def readDataNVMEM(self):
        '''
        Returns all readings in non-volatile memory (NVMEM).
        
        :rtype: `list` of `float` elementa
        '''
        return map( float, self.query('DATA:DATA? NVMEM').split(',') )
    
    # Read the Last Data Point
    def readLastData(self):
        '''
        Retrieve the last measurement taken. This can be executed at any time, including when the instrument is currently taking measurements.
        If there are no data points available, the value 9.91000000E+37 is returned.
        
        :rtype: `float` or `int` (if an error occurs)
        '''
        data = self.query('DATA:LAST?')
        
        if data == '9.91000000E+37':
            return int(data)
        else:
            data = data[0:data.index(' ')] # Remove units
            return float(data)
    
    # Init: Set to "Wait-for-trigger" state        
    def init(self):
        '''
        Switch device from "idle" state to "wait-for-trigger state".
        Measurements will begin when specified triggering conditions are met, following the receipt of the INIT command.
        
        Note that this command will also clear the previous set of readings from memory.
        '''
        self.write('INIT')
    
    # Read: Set to "Wait-for-trigger" state, and immediately send result to output
    def read(self):
        '''
        Switch device from "idle" state to "wait-for-trigger" state. Immediately after the trigger conditions are met, the data will be sent to the output buffer of the instrument.
        
        This is similar to calling :meth:`~Agilent34410a.init` and then immediately falling :math:`~Agilent34410a.fetch`.
        
        :rtype: `float`
        '''
        return float( self.query('READ?') )
    
    # Read and Erase a set number of data points from memory
    def r(self,count):
        '''
        HERP DERP
        '''
        if not isinstance(count,int):
            raise Exception('Parameter "count" must be an integer')
        if count == 0:
            msg = 'R?'
        else:
            msg = 'R? ' + str(count)
        
        self.write('FORM:DATA REAL,32')
        self.write(msg)
        return self.binblockread(4)
        
    
    # Set Trigger Source
    def triggerSource(self,source=None):
        '''
        This function sets the trigger source for measurements.
        The 34410a accepts the following trigger sources:
        
        #. "Immediate": This is a continuous trigger. This means the trigger signal is always present.
        #. "External": External TTL pulse on the back of the instrument. It is active low. 
        #. "Bus": Causes the instrument to trigger when a ``*TRG`` command is sent by software. This means calling the trigger() function.
        
        If no source is specified, function queries the instrument for the current setting. This is returned as a string. An example value is "EXT", without quotes.
            
        :param str source: Desired trigger source, one of ``{IMMediate|EXTernal|BUS}``.
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
        
        self.write('TRIG:SOUR ' + source)
        
    # Trigger Count
    def triggerCount(self,count = None):
        '''
        This function sets the number of triggers that the multimeter will accept before returning to an "idle" trigger state.
        
        Note that if the sample count parameter has been changed, the number of readings taken will be a multiplication of sample count and trigger count (see function sampleCount).
        If specified as a string, the following options apply:
        
        #. "MINimum": 1 trigger
        #. "MAXimum": 50 000 triggers
        #. "DEF": Default
        #. "INFinity": Continuous. When the buffer is filled, the oldest data points are overwritten.
        
        If count is not specified, function queries the instrument for the current trigger count setting. This is returned as an integer.
            
        Note that when using triggered measurements, it is recommended that you disable autorange by either explicitly disabling it or specifying your desired range.
        
        count: Number of triggers before returning to an "idle" trigger state.
        count = {<count>|MINimum|MAXimum|DEF|INFinity},integer/string
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
        
        self.write( 'TRIG:COUN ' + str(count) )
        
    # Trigger delay
    def triggerDelay(self,period=None):
        '''
        This command sets the time delay which the instrument will use following receiving a trigger event before starting the measurement.
        
        Note that this function does not contain proper screening for "period" being a malformed string. This allows you to include the units of your specified value in the string.
        If no units are specified, the number will be read by the instrument as having units of seconds.
        
        If no period is specified, function queries the instrument for the current trigger delay and returns a float.
        
        period: Time between receiving a trigger event and the instrument taking the reading. Values range from 0s to ~3600s, in ~20us increments.
        period = {<seconds>|MINimum|MAXimum|DEF},float/string 
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
        
        self.write( 'TRIG:DEL ' + str(period) )
    
    # Sample Count
    def sampleCount(self, count=None):
        '''
        This command sets the number of readings (samples) that the multimeter will take per trigger.
        The time between each measurement is defined with the sampleTimer function.
        
        Note that if the sample count parameter has been changed, the number of readings taken will be a multiplication of sample count and trigger count (see function sampleCount).
        If specified as a string, the following options apply:
        
        #. "MINimum": 1 sample per trigger
        #. "MAXimum": 50 000 samples per trigger
        #. "DEF": Default, 1 sample
            
        If count is not specified, function queries the instrument for the current smaple count and returns an integer.
            
        Note that when using triggered measurements, it is recommended that you disable autorange by either explicitly disabling it or specifying your desired range.
        
        count: Number of triggers before returning to an "idle" trigger state.
        count = {<count>|MINimum|MAXimum|DEF},integer/string
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
        
        self.write( 'SAMP:COUN ' + str(count) )
    
    # Sample Timer
    def sampleTimer(self,period = None):
        '''
        This command sets the sample interval when the sample counter is greater than one and when the sample source is set to timer (timed sampling).
        
        This command does not effect the delay between the trigger occuring and the start of the first sample. This trigger delay is set with the triggerDelay function.
        
        Note that this function does not contain proper screening for "period" being a malformed string. This allows you to include the units of your specified value in the string.
        If no units are specified, the number will be read by the instrument as having units of seconds.
        
        If period is not specified, function queries the instrument for the current sample interval and returns it as a float.
        
        period: Time period between samples. An example including units is "500 ms".
        period = {<period>|MINimum|MAXimum},float/string
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
        
        self.write( 'SAMP:TIM ' + str(period) )
        
    # Sample Source
    def sampleSource(self,source = None):
        '''
        This command determines whether the trigger delay or the sample timer is used to determine sample timing when the sample count is greater than one.
        In both cases, the first sample is taken one trigger delay time after the trigger. After that, it depends on which mode is used:
        
        1) "IMMediate": The trigger delay time is inserted between successive samples. After the first measurement is completed, the instrument waits the time specified by
            the trigger delay and then performs the next sample.
        2) "TIMer": Successive samples start one sample interval after the START of the previous sample.
        
        If source is not specified, function queries the instrument for the currently set sample source and returns its as a string. An example is "TIM" without quotes.
        
        source: Desired successive sample timing mode.
        source = {IMMediate|TIMer},string
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
        
        self.write( 'SAMP:SOUR ' + str(source) )
    
    # Abort Measurements
    def abort(self):
        '''
        Abort a measurements currently in progress.
        '''
        self.write('ABOR')
        
        
        
        
        
        
        
        
        
        
        
        
        
