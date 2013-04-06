#!/usr/bin/python
# Filename: agilent33220a.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class Agilent33220a(Instrument):
    def __init__(self, port, address,timeout_length):
        super(Agilent33220a, self).__init__(self,port,address,timeout_length)
    
    # Output
    def setOutput(self, func, freq=None, amplitude=None, offset=None):
        '''
        Set the output of the function generator. Only argument "func" is required.
        
        :param str func: Output function type, one of ``{SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}``.
        
        :param freq: Output frequency. Ignored for noise and dc mode.
        :type freq: `int` or `float` [Hz]
        
        :param amplitude: Peak to peak amplitude of the output. Ignored for dc mode.
        :type amplitude: `int` or `float` [V]
        
        :param offset: DC offset.
        :type offset: `int` or `float` [V]
        '''
        if not isinstance(func,str):
            raise Exception('Output function (func) must be a string.')
        
        validFunc = ['sinusoid','square','ramp','pulse','noise','dc','user']
        validFunc2 = ['sin','squ','ramp','puls','nois','dc','user']
        
        func = func.lower()
        if func in validFunc:
            func = validFunc2[validFunc.index(func)]
        elif func not in validFunc2:
            raise Exception( 'Valid output functions are: ' + str(validFunc) )
        
        if freq == None: # No frequency specified, just set function
            self.write( 'APPL:' + func )
            return
        
        if isinstance(freq,int) or isinstance(freq,float):
            pass
        elif isinstance(freq,str):
            freq = freq.lower()
            valid = ['minimum','maximum','default']
            valid2 = ['min','max','def']
            if freq in valid:
                freq = valid2[valid.index(freq)]
            elif freq not in valid2:
                raise Exception('Valid ')
        else:
            raise Exception('Frequency (freq) must be an integer, a float, or a string.')
        
        if amplitude == None: # If amplitude is not defined
            self.write('APPL:%s %s' %(func,freq) )
            return
        
        if not isinstance(amplitude,int) and not isinstance(amplitude,float):
            raise Exception('Amplitude must be an integer or a float.')
        
        if offset == None: # If offset was not specified
            self.write('APPL:%s %s,%s' %(func,freq,amplitude) )
            return
        
        if not isinstance(offset,int) and not isinstance(offset,float):
            raise Exception('Offset must be an integer or a float.')
         
        self.write('APPL:%s %s,%s,%s' %( func,freq,amplitude,offset ) )
        
    def function(self,func = None):
        '''
        Set the output function of the function generator.
        
        If argument "func" is omitted, the instrument is queried for its current output setting. Return type is a string.
        
        :param str func: Output function type, one of ``{SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}``.
        '''
        if func == None: # If func not specified, perform query for current function
            return self.query('FUNC?')
        
        if type(func) != type(str()):
            raise Exception('Output function (func) must be a string.')
        
        validFunc = ['sinusoid','square','ramp','pulse','noise','dc','user']
        validFunc2 = ['sin','squ','ramp','puls','nois','dc','user']
        
        func = func.lower()
        if func in validFunc:
            func = validFunc2[validFunc.index(func)]
        elif func not in validFunc2:
            raise Exception( 'Valid output functions are: ' + str(validFunc) )
        
        self.write( 'FUNC:' + func )
    
    # Frequency
    
    def frequency(self,freq = None):
        '''
        Set the output frequency of the function generator. Consult the manual for specific ranges depending on the function.
        
        If a frequency is not specified, function queries the instrument for the current frequency setting, and returns it as a float. Units are Hertz.
        
        freq: Desired output frequency.
        freq = {<frequency>|MINimum|MAXimum},number/string
        '''
        if freq == None: # If no frequency is specified, query instrument for current frequency setting
            return float( self.query('FREQ?') )
        
        if isinstance(freq,int) or isinstance(freq,float):
            if freq < 0:
                raise Exception('Frequency must be a positive quantity.')
        elif isinstance(freq,str):
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if freq in valid:
                freq = valid2[valid.index(freq)]
            elif freq not in valid2:
                raise Exception('Frequency must be either "MINimum" or "MAXimum" when specified as a string.')
        else:
            raise Exception('Frequency must be specified as a float or an integer in Hertz, or as a string.')
        
        self.write( 'FREQ ' + str(freq) )
    
    def voltage(self, amplitude=None):
        '''
        Set the output voltage amplitude of the function generator.
        Units are defined by the voltageUnits method.
        
        If no amplitude is specified, function queries the instrument for the current amplitude.
        Also returns the minimum and maximum values for the current settings.
        Units are defined by the voltageUnits method.
        
        Return type is a tuple of the form (current value, minimum allowed, maximum allowed)
        
        amplitude: Desired output voltage amplitude
        amplitude = {<amplitude>|MINimum|MAXimum}
        '''
        if amplitude == None: # Voltage is not specified
            return ( float( self.query('VOLT?') ) , float( self.query('VOLT? MIN') ) , float( self.query('VOLT? MAX') ) )
        
        if isinstance(amplitude,str):
            amplitude = amplitude.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if amplitude in valid:
                amplitude = valid2[valid.index(amplitude)]
            elif amplitude not in valid2:
                raise Exception('Amplitude must be "MINimum" or "MAXimum" when specified as a string.')
        elif isinstance(amplitude,int) or isinstance(amplitude,float):
            if amplitude < 0:
                raise Exception('Amplitude must be a positive quantity.')
        else:
            raise Exception('Signal amplitude must be specified as a string or number.')
        
        self.write( 'VOLT ' + str(amplitude) )
        
    def voltageUnits(self,unit = None):
        '''
        Set the voltage amplitude units of the function generator.
        
        If no units are specified, function queries the instrument for the currently set voltage units.
        
        Return type is a string.
        
        unit: Desired voltage unit
        unit = {VPP|VRMS|DBM}
        '''
        if unit == None: # No unit is defined
            return self.query('VOLT:UNIT?')
        
        if not isinstance(unit,str):
            raise Exception('Voltage units must be a string.')
        
        unit = unit.lower()
        valid = ['vpp','vrms','dbm']
        if unit not in valid:
            raise Exception('Valid voltage amplitude units are "VPP", "VRMS", and "DBM".')
        
        self.write('VOLT:UNIT ' + unit)
        
    def voltageOffset(self,offset = None):
        '''
        Set the offset voltage for the output waveform.
        
        If no offset is specified, function queries the instrument for the current offset voltage.
        It also queries the minimum and maximum offset for the current settings.
        
        Return type is a tuple of the form (current offset, minimum offset, maximum offset )
        
        offset: Desired voltage offset in volts.
        offset = {<voltage>|MINimum|MAXimum},number/string
        '''
        if offset == None: # No offset is defined
            return ( float(self.query('VOLT:OFFS?')), float(self.query('VOLT:OFFS? MIN')), float(self.query('VOLT:OFFS? MAX')) )
        
        if isinstance(offset,str):
            offset = offset.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if offset in valid:
                offset = valid2[valid.index(offset)]
            elif offset not in valid2:
                raise Exception('Offset must be "MINimum" or "MAXimum" when specified as a string.')
        elif not isinstance(offset,int) and not isinstance(offset,float):
            raise Exception('Signal amplitude must be specified as a string or number.')
        
        self.write( 'VOLT:OFFS ' + str(offset) )
        
    def dutyCycle(self,duty = None):
        '''
        Set the duty cycle of a square wave.
        Duty cycle represents the amount of time that the square wave is at a high level.
        
        If no duty is specified, function queries the instrument for the current duty cycle, along with the minimum and maximum duty cycles for the current settings.
        
        Return type is a tuple of the form (current duty, minimum duty, maximum duty)
        
        duty: Desired duty cycle as a percent.
        duty = {<duty cycle>|MINimum|MAXimum},integer/string
        '''
        if duty == None:
            return ( int(self.query('FUNC:SQU:DCYC?')), int(self.query('FUNC:SQU:DCYC? MIN')), int(self.query('FUNC:SQU:DCYC? MAX')) )
        
        if isinstance(duty,str):
            duty = duty.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if duty in valid:
                duty = valid2[valid.index(duty)]
            elif duty not in valid2:
                raise Exception('Duty must be "MINimum" or "MAXimum" when specified as a string.')
        elif not isinstance(duty,int) or duty < 0:
            raise Exception('Duty cycle must be a positive integer.')
        
        self.write( 'FUNC:SQU:DCYC ' + str(duty) )
        
    def rampSymmetry(self,symmetry = None):
        '''
        Set the ramp symmetry for ramp waves.
        Symmetry represents the amount of time per cycle that the ramp wave is rising (unless polarity is inverted).
        
        If no percent is specified, function queries instrument for the current ramp symmetry, along with the minimum and maximum.
        
        Return type is a tuple in the form (current symmetry, minimum symmetry, maximum symmetry)
        
        symmetry: Desired ramp symmetry as a percent
        symmetry = {<ramp symmetry>|MINimum|MAXimum},integer/string
        '''
        if symmetry == None:
            return ( int(self.query('FUNC:RAMP:SYMM?')), int(self.query('FUNC:RAMP:SYMM? MIN')), int(self.query('FUNC:RAMP:SYMM? MAX')) )
        
        if isinstance(symmetry,str):
            symmetry = symmetry.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if symmetry in valid:
                symmetry = valid2[valid.index(symmetry)]
            elif symmetry not in valid2:
                raise Exception('Symmetry must be "MINimum" or "MAXimum" when specified as a string.')
        elif not isinstance(symmetry,int) or symmetry < 0:
            raise Exception('Symmetry cycle must be a positive integer.')
        
    def output(self,state=None):
        '''
        Disable or enable the front panel output connector.
        
        If no state is specified, function queries instrument for the current state.
        
        Return type is a string.
        
        state: Desired state of front panel output connector.
        state = {OFF|ON|0|1},string/integer
        '''
        if state == None:
            return self.query('OUTP?')
        
        if isinstance(state,str):
            state = state.lower()
        
        if state in ('off','0',0):
            self.write('OUTP OFF')
        elif state in ('on','1',1):
            self.write('OUTP ON')
        else:
            raise Exception('Valid output states are "OFF", "ON", 0 and 1.')
        
    def outputLoad(self,load=None):
        '''
        Desired output termination load (ie, the impedance of the load attached to the front panel output connector).
        When specified as a string, they equate to:
        
        #. MINimum: 1ohm
        #. MAXimum: 10kohm
        #. INFinity: High-impedance mode (>10kohm)
        
        The instrument has a fixed series output impedance of 50ohms. This function allows the instrument to compensate of the voltage divider and accurately report the voltage across the attached load.
        
        If no load is specified, function queries instrument for the current output load setting, along with the minimum and maximum values.
        
        Return type is a tuple of the form (current load, min load, max load)
        
        load: The impedance of the load attached to the front panel output connector
        load = {<ohms>|MINimum|MAXimum|INFinity},integer/string
        '''
        if load == None:
            return ( int(self.query('OUTP:LOAD?')), int(self.query('OUTP:LOAD? MIN')), int(self.query('OUTP:LOAD? MAX')) )
        
        if isinstance(load,str):
            load = load.lower()
            valid = ['minimum','maximum','infinity']
            valid2 = ['min','max','inf']
            if load in valid:
                load = valid2[valid.index(load)]
            elif load not in valid2:
                raise Exception('Output load must be "MINimum" or "MAXimum" when specified as a string.')
        elif isinstance(load,int):
            if load < 1 or load > 10000:
                raise Exception('Output load must be between 1 and 10k ohm.')
        else:
            raise Exception('Output load must be specified as a integer or a string.')
        
        self.write('OUTP:LOAD ' + str(load))
        
    def outputPolarity(self,polarity = None):
        '''
        Inverts the waveform relative to the offset voltage.
        
        If no polarity is specified, function queries instrument for current output polarity.
        
        Return type is a string. For example: "NORM" without quotes.
        
        polarity: Desired output polarity
        polarity = {NORMal|INVerted},string
        '''
        if polarity == None:
            return self.query('OUTP:POL?')
        
        if polarity in ('normal','norm'):
            self.write('OUTP:POL NORM')
        elif polarity in ('inverted','inv'):
            self.write('OUTP:POL INV')
    
    def outputSync(self,state = None):
        '''
        Enable or disable the front panel sync connector.
        
        If no state is specified, function queries instrument for the current state.
        
        Return type is a string.
        
        state: Desired state of front panel sync connector.
        state = {OFF|ON|0|1},string/integer
        '''
        if state == None:
            return self.query('OUTP:SYNC?')
        
        if isinstance(state,str):
            state = state.lower()
        
        if state in ('off','0',0):
            self.write('OUTP:SYNC OFF')
        elif state in ('on','1',1):
            self.write('OUTP:SYNC ON')
        else:
            raise Exception('Valid output sync states are "OFF", "ON", 0 and 1.')
            
            
            
            
            
            
            
            
            
        
        
        
        
        
        
        
