#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# agilent33220a.py: Driver for the Agilent 33220a function generator.
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

from instruments.generic_scpi import SCPIInstrument

## CLASSES #####################################################################

class Agilent33220a(SCPIInstrument):
    
    def set_output(self, func, freq=None, amplitude=None, offset=None):
        '''
        Set the output of the function generator.
        
        :param str func: Output function type, one of 
            ``{SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}``.
        
        :param freq: Output frequency. Ignored for noise and dc mode.
        :type freq: `int` or `float` [Hz]
        
        :param amplitude: Peak to peak amplitude of the output.
            Ignored for dc mode.
        :type amplitude: `int` or `float` [V]
        
        :param offset: DC offset.
        :type offset: `int` or `float` [V]
        '''
        if not isinstance(func,str):
            raise TypeError('Output function (func) must be a string.')
        
        validFunc = ['sinusoid','square','ramp','pulse','noise','dc','user']
        validFunc2 = ['sin','squ','ramp','puls','nois','dc','user']
        
        func = func.lower()
        if func in validFunc:
            func = validFunc2[validFunc.index(func)]
        elif func not in validFunc2:
            raise ValueError('Valid output functions are: ' + str(validFunc))
        
        if freq == None: # No frequency specified, just set function
            self.sendcmd( 'APPL:' + func )
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
                raise ValueError('Not valid frequency')
        else:
            raise TypeError('Frequency (freq) must be an integer, '
                 'a float, or a string.')
        
        if amplitude == None: # If amplitude is not defined
            self.sendcmd('APPL:%s %s' %(func,freq) )
            return
        
        if not isinstance(amplitude,int) and not isinstance(amplitude,float):
            raise TypeError('Amplitude must be an integer or a float.')
        
        if offset == None: # If offset was not specified
            self.sendcmd('APPL:%s %s,%s' %(func,freq,amplitude) )
            return
        
        if not isinstance(offset,int) and not isinstance(offset,float):
            raise TypeError('Offset must be an integer or a float.')
         
        self.sendcmd('APPL:%s %s,%s,%s' %( func,freq,amplitude,offset ) )
        
    def function(self,func = None):
        '''
        Set the output function of the function generator.
        
        If argument "func" is omitted, the instrument is queried for its 
        current output setting. Return type is a string.
        
        :param str func: Output function type, one of 
            ``{SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}``.
        '''
        if func == None:
            return self.query('FUNC?')
        
        if type(func) != type(str()):
            raise TypeError('Output function (func) must be a string.')
        
        validFunc = ['sinusoid','square','ramp','pulse','noise','dc','user']
        validFunc2 = ['sin','squ','ramp','puls','nois','dc','user']
        
        func = func.lower()
        if func in validFunc:
            func = validFunc2[validFunc.index(func)]
        elif func not in validFunc2:
            raise ValueError('Valid output functions are: ' + str(validFunc))
        
        self.sendcmd( 'FUNC:' + func )
    
    def frequency(self,freq = None):
        '''
        Set the output frequency of the function generator. Consult the manual 
        for specific ranges depending on the function.
        
        If a frequency is not specified, function queries the instrument for the
        current frequency setting, and returns it as a float. Units are Hertz.
        
        :param freq: Desired output frequency. One of 
            ``{<frequency>|MINimum|MAXimum}``
        :type: `int` or `str`
        '''
        if freq == None: # If no frequency is specified, query 
                         # instrument for current frequency setting
            return float( self.query('FREQ?') )
        
        if isinstance(freq,int) or isinstance(freq,float):
            if freq < 0:
                raise ValueError('Frequency must be a positive quantity.')
        elif isinstance(freq,str):
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if freq in valid:
                freq = valid2[valid.index(freq)]
            elif freq not in valid2:
                raise ValueError('Frequency must be either "MINimum" '
                    'or "MAXimum" when specified as a string.')
        else:
            raise TypeError('Frequency must be specified as a float or '
                'an integer in Hertz, or as a string.')
        
        self.sendcmd( 'FREQ ' + str(freq) )
    
    def voltage(self, amplitude=None):
        '''
        Set the output voltage amplitude of the function generator.
        Units are defined by the voltageUnits method.
        
        If no amplitude is specified, function queries the instrument for 
        the current amplitude.
        Also returns the minimum and maximum values for the current settings.
        Units are defined by the voltageUnits method.
        
        Return type is a tuple of the form (current value, minimum allowed, 
        maximum allowed)
        
        :param amplitude: Desired output voltage amplitude. One of
            ``{<amplitude>|MINimum|MAXimum}``
        :type amplitude: `int` or `str`
        '''
        if amplitude == None: # Voltage is not specified
            return (float(self.query('VOLT?')), 
                float(self.query('VOLT? MIN')),
                float(self.query('VOLT? MAX'))
                )
        
        if isinstance(amplitude,str):
            amplitude = amplitude.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if amplitude in valid:
                amplitude = valid2[valid.index(amplitude)]
            elif amplitude not in valid2:
                raise ValueError('Amplitude must be "MINimum" or "MAXimum" '
                    'when specified as a string.')
        elif isinstance(amplitude, int) or isinstance(amplitude, float):
            if amplitude < 0:
                raise ValueError('Amplitude must be a positive quantity.')
        else:
            raise TypeError('Signal amplitude must be specified as a string '
                'or number.')
        
        self.sendcmd('VOLT {}'.format(str(amplitude)))
        
    def voltage_units(self,unit = None):
        '''
        Set the voltage amplitude units of the function generator.
        
        If no units are specified, function queries the instrument for 
        the currently set voltage units.
        
        Return type is a string.
        
        :param str unit: Desired voltage unit. One of ``{VPP|VRMS|DBM}``.
        '''
        if unit == None: # No unit is defined
            return self.query('VOLT:UNIT?')
        
        if not isinstance(unit,str):
            raise TypeError('Voltage units must be a string.')
        
        unit = unit.lower()
        valid = ['vpp','vrms','dbm']
        if unit not in valid:
            raise ValueError('Valid voltage amplitude units are "VPP", '
                '"VRMS", and "DBM".')
        
        self.sendcmd('VOLT:UNIT ' + unit)
        
    def voltage_offset(self,offset = None):
        '''
        Set the offset voltage for the output waveform.
        
        If no offset is specified, function queries the instrument for the 
        current offset voltage.
        It also queries the minimum and maximum offset for the current settings.
        
        Return type is a tuple of the form (current offset, minimum offset, 
        maximum offset )
        
        :param offset: Desired voltage offset in volts. One of
             ``{<voltage>|MINimum|MAXimum}``
        :type offset: `int` or `str`
        '''
        if offset == None: # No offset is defined
            return (float(self.query('VOLT:OFFS?')), 
                float(self.query('VOLT:OFFS? MIN')), 
                float(self.query('VOLT:OFFS? MAX'))
                )
        
        if isinstance(offset,str):
            offset = offset.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if offset in valid:
                offset = valid2[valid.index(offset)]
            elif offset not in valid2:
                raise ValueError('Offset must be "MINimum" or "MAXimum" '
                    'when specified as a string.')
        elif not isinstance(offset,int) and not isinstance(offset,float):
            raise TypeError('Signal amplitude must be specified as a string '
                'or number.')
        
        self.sendcmd('VOLT:OFFS ' + str(offset))
        
    def duty_cycle(self,duty = None):
        '''
        Set the duty cycle of a square wave.
        Duty cycle represents the amount of time that the square wave is at a 
        high level.
        
        If no duty is specified, function queries the instrument for the 
        current duty cycle, along with the minimum and maximum duty cycles 
        for the current settings.
        
        Return type is a tuple of the form 
        (current duty, minimum duty, maximum duty)
        
        :param duty: Desired duty cycle as a percent. One of
            ``{<duty cycle>|MINimum|MAXimum}``
        :type duty: `int` or `str`
        '''
        if duty == None:
            return (int(self.query('FUNC:SQU:DCYC?')),
                int(self.query('FUNC:SQU:DCYC? MIN')),
                int(self.query('FUNC:SQU:DCYC? MAX'))
                )
        
        if isinstance(duty,str):
            duty = duty.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if duty in valid:
                duty = valid2[valid.index(duty)]
            elif duty not in valid2:
                raise TypeError('Duty must be "MINimum" or "MAXimum" when '
                    'specified as a string.')
        elif not isinstance(duty,int) or duty < 0:
            raise ValueError('Duty cycle must be a positive integer.')
        
        self.sendcmd('FUNC:SQU:DCYC ' + str(duty))
        
    def ramp_symmetry(self,symmetry = None):
        '''
        Set the ramp symmetry for ramp waves.
        Symmetry represents the amount of time per cycle that the ramp wave is 
        rising (unless polarity is inverted).
        
        If no percent is specified, function queries instrument for the current 
        ramp symmetry, along with the minimum and maximum.
        
        Return type is a tuple in the form (current symmetry, minimum symmetry, 
        maximum symmetry)
        
        :param symmetry: Desired ramp symmetry as a percent. One of
            {<ramp symmetry>|MINimum|MAXimum}
        :type: `int` or `str`
        '''
        if symmetry == None:
            return (int(self.query('FUNC:RAMP:SYMM?')),
                int(self.query('FUNC:RAMP:SYMM? MIN')),
                int(self.query('FUNC:RAMP:SYMM? MAX'))
                )
        
        if isinstance(symmetry,str):
            symmetry = symmetry.lower()
            valid = ['minimum','maximum']
            valid2 = ['min','max']
            if symmetry in valid:
                symmetry = valid2[valid.index(symmetry)]
            elif symmetry not in valid2:
                raise ValueError('Symmetry must be "MINimum" or "MAXimum" '
                    'when specified as a string.')
        elif not isinstance(symmetry,int) or symmetry < 0:
            raise ValueError('Symmetry cycle must be a positive integer.')
        
    def output(self,state=None):
        '''
        Disable or enable the front panel output connector.
        
        If no state is specified, function queries instrument for the current 
        state.
        
        Return type is a string.
        
        :param state: Desired state of front panel output connector. One of
            {OFF|ON|0|1}
        :type: `int` or `str`
        '''
        if state == None:
            return self.query('OUTP?')
        
        if isinstance(state,str):
            state = state.lower()
        
        if state in ('off','0',0):
            self.sendcmd('OUTP OFF')
        elif state in ('on','1',1):
            self.sendcmd('OUTP ON')
        else:
            raise ValueError('Valid output states are "OFF", "ON", 0 and 1.')
        
    def output_load(self,load=None):
        '''
        Desired output termination load (ie, the impedance of the load attached 
        to the front panel output connector).
        When specified as a string, they equate to:
        
        #. MINimum: 1ohm
        #. MAXimum: 10kohm
        #. INFinity: High-impedance mode (>10kohm)
        
        The instrument has a fixed series output impedance of 50ohms. This 
        function allows the instrument to compensate of the voltage divider 
        and accurately report the voltage across the attached load.
        
        If no load is specified, function queries instrument for the current 
        output load setting, along with the minimum and maximum values.
        
        Return type is a tuple of the form (current load, min load, max load)
        
        :param load: The impedance of the load attached to the front panel 
            output connector. One of ``{<ohms>|MINimum|MAXimum|INFinity}``
        :type load: `int` or `str`
        '''
        if load == None:
            return (int(self.query('OUTP:LOAD?')),
                int(self.query('OUTP:LOAD? MIN')),
                int(self.query('OUTP:LOAD? MAX'))
                )
        
        if isinstance(load,str):
            load = load.lower()
            valid = ['minimum','maximum','infinity']
            valid2 = ['min','max','inf']
            if load in valid:
                load = valid2[valid.index(load)]
            elif load not in valid2:
                raise ValueError('Output load must be "MINimum" or'
                    ' "MAXimum" when specified as a string.')
        elif isinstance(load,int):
            if load < 1 or load > 10000:
                raise ValueError('Output load must be between 1 and 10k ohm.')
        else:
            raise TypeError('Output load must be specified as a integer or '
                'a string.')
        
        self.sendcmd('OUTP:LOAD ' + str(load))
        
    def output_polarity(self, polarity=None):
        '''
        Inverts the waveform relative to the offset voltage.
        
        If no polarity is specified, function queries instrument for current 
        output polarity.
        
        Return type is a string. For example: "NORM" without quotes.
        
        :param str polarity: Desired output polarity. One of 
            ``{NORMal|INVerted}``.
        '''
        if polarity == None:
            return self.query('OUTP:POL?')
        
        if polarity in ('normal','norm'):
            self.sendcmd('OUTP:POL NORM')
        elif polarity in ('inverted','inv'):
            self.sendcmd('OUTP:POL INV')
    
    def output_sync(self,state = None):
        '''
        Enable or disable the front panel sync connector.
        
        If no state is specified, function queries instrument for the current 
        state.
        
        Return type is a string.
        
        :param state: Desired state of front panel sync connector. One of 
            ``{OFF|ON|0|1}``
        :type state: `int` or `str`
        '''
        if state == None:
            return self.query('OUTP:SYNC?')
        
        if isinstance(state,str):
            state = state.lower()
        
        if state in ('off','0',0):
            self.sendcmd('OUTP:SYNC OFF')
        elif state in ('on','1',1):
            self.sendcmd('OUTP:SYNC ON')
        else:
            raise ValueError('Valid output sync states are "OFF", "ON", 0 '
                'and 1.')
            
            
            
            
            
            
            
            
            
        
        
        
        
        
        
        
