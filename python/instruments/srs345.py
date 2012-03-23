#!/usr/bin/python
# Filename: srs345.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class SRS345(Instrument):
    def __init__(self, port, address,timeout_length):
        Instrument.__init__(self,port,address,timeout_length)
        
    def amplitude(self,units=None,amplitude=None):
        '''
        Set the output voltage amplitude of the function generator.
        Units must be specified to change the amplitude.
        
        If neither units or amplitude is specified, function queries instrument for the currently set amplitude and units displayed.
        If only units are specified, function returns the currently set amplitude with the units specified.
        
        Return type is a string. Last two characters are the units.
        
        units: Amplitude units
        units = {VPP|VRMS|DBM}
        
        amplitude: Desired output amplitude
        amplitude = <voltage>
        '''
        validUnits = ['vpp','vrms','dbm']
        validUnits2 = ['vp','vr','db']
        
        if amplitude == None and units == None: # No arguments specified.
            return self.query('AMPL?')
        elif amplitude == None and units != None: # Only units specified
            if isinstance(units,str):
                units = units.lower()
            else:
                raise Exception('Units must be a string.')
            
            if units in validUnits:
                units = validUnits2[validUnits.index(units)]
            elif units not in validUnits2:
                raise Exception('Valid units are "VPP", "VRMS" and "DBM".')
            
            return self.query('AMPL? ' + units)
        
        else: # Amplitude has been specified
            if not isinstance(units,str):
                raise Exception('Units must be a string.')
            units = units.lower()
            if units in validUnits:
                units = validUnits2[validUnits.index(units)]
            elif units not in validUnits2:
                raise Exception('Valid units are "VPP", "VRMS" and "DBM".')
            
            if not isinstance(amplitude,int) and not isinstance(amplitude,float):
                raise Exception('Amplitude must be specified as an integer or a float.')
            
            self.write('AMPL ' + str(amplitude) + units)
    
    def frequency(self,freq=None):
        '''
        Set the output frequency.
        
        If no frequency is specified, function queries instrument for current frequency setting.
        
        Return type is a string, with units of Hertz.
        
        freq: Desired output frequency, given in Hertz.
        freq = <frequency>
        '''
        if freq == None:
            return self.query('FREQ?')
        
        if not isinstance(freq,int) and not isinstance(freq,float):
            raise Exception('Frequency must be specified as an integer or a float.')
        
        self.write('FREQ ' + str(freq))
        
    def function(self,func = None):
        '''
        Set the output function of the function generator.
        
        If argument "func" is omitted, the instrument is queried for its current output setting.
        
        Return type is a string.
        
        func: Output function type.
        func = {SINusoid|SQUare|TRIangle|RAMP|NOISe|ARBitrary},string
        '''
        valid = ['sinusoid','square','triangle','ramp','noise','arbitrary']
        valid2 = ['sin','squ','tri','ramp','nois','arb']
        
        if func == None:
            func = self.query('FUNC?')
            return valid[int(func)]
        
        if not isinstance(func,str):
            raise Exception('Function type must be specified as a string.')
        
        func = func.lower()
        if func in valid:
            func = valid.index(func)
        elif func in valid2:
            func = valid2.index(func)
        elif func == 'sine':
            func = 0
        else:
            raise Exception('Valid output function types are: ' + str(valid))
        
        self.write('FUNC ' + str(func))
        
    def offset(self,offset = None):
        '''
        Set the offset voltage for the output waveform.
        
        If no offset is specified, function queries the instrument for the current offset voltage.
        
        Return type is a float.
        
        offset: Desired voltage offset in volts.
        offset = <voltage>,integer/float
        '''
        if offset == None:
            return float( self.query('OFFS?') )
        
        if not isinstance(offset,int) and not isinstance(offset,float):
            raise Exception('Offset must be an integer or a float.')
        
        self.write('OFFS ' + str(offset))
        
    def phase(self, phase = None):
        '''
        Set the phase for the output waveform.
        
        If no phase is specified, function queries the instrument for the current phase.
        
        Return type is a float.
        
        phase: Desired phase in degrees.
        phase = <voltage>,integer/float
        '''
        if phase == None:
            return float( self.query('PHSE?') )
        
        if not isinstance(phase,int) and not isinstance(phase,float):
            raise Exception('Phase must be an integer or a float.')
        
        if phase < 0 or phase > 7200:
            raise Exception('Phase must be between 0 and 7200 degrees.')
        
        self.write('PHSE ' + str(phase))
            
        
        
        
        
        
        
        
        
        
        
        
        
        
            
        
