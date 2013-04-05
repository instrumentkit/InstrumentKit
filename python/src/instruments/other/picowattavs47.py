#!/usr/bin/python
# Filename: picowattavs47.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class PicowattAVS47(Instrument):
    def __init__(self, port, address,timeout_length):
        super(PicowattAVS47, self).__init__(self,port,address,timeout_length)
        
    def remote(self,state = None):
        '''
        Enable or disable the remote mode state.
        
        Enabling the remote mode allows all settings to be changed by computer interface and locks-out the front panel.
        
        If not state is specified, function queries instrument for the current remote mode state.
        
        Return type is a string.
        
        state: Remote mode state
        state = {OFF|DISABLE|ON|ENABLE|0|1},string/integer
        '''
        if state == None:
            return self.query('REM?')
        
        if isinstance(state,str):
            state = state.lower()
        
        if state in ('off','0',0,'disable'):
            self.write('REM 0')
        elif state in ('on','1',1,'enable'):
            self.write('REM 1')
        else:
            raise Exception('Remote state must be "off", "on", "disable", "enable", "0" or "1".')
        
    def inputSource(self,source = None):
        '''
        Set the input source.
            1) "GROUND": Connects the bridge input to ground. Recommended before changing other bridge settings.
            2) "ACTUAL": Connects to the actual measurement.
            3) "REFerence": Connects to the internal precision 100ohm resistor. Used for calibrating the scale factor.
            
        If no source is specified, function queries instrument for current input source connection.
        
        source: Input source
        source = {GROund|ACTUAL|REFerence|100ohm|1|2|3},string/integer
        '''
        if source == None:
            return self.query('INP?')
        
        if isinstance(source,str):
            source = source.lower()
        
        if source in ('ground','gro','0',0):
            self.write('INP 0')
        elif source in ('actual','1',1):
            self.write('INP 1')
        elif source in ('reference','ref','100ohm','2',2):
            self.write('INP 2')
        else:
            raise Exception('Valid sources include "ground", "actual", "reference",0,1,2,"100ohm", and "ref".')
        
    def muxChannel(self,channel = None):
        '''
        Set the multiplexer channel.
        It is recommended that you ground the input before switching the multiplexer channel.
        
        If no channel is specified, function queries instrument for the current multiplexer channel setting.
        
        Return type is a string.
        
        channel: Multiplexer channel
        channel = <0..7>,integer
        '''
        if channel == None:
            return self.query('MUX?')
        
        if not isinstance(channel,int):
            raise Exception('Multiplexer channel must be an integer.')
        
        if channel < 0 or channel > 7:
            raise Exception('Multiplexer channel must be between [0,7].')
        
        self.write( 'MUX ' + str(channel) )
        
    def excitation(self,channel = None):
        '''
        Set the excitation channel.
        
        If no channel is specified, function queries instrument for the current excitation channel setting.
        
        Return type is a string.
        
        channel: Excitation channel
        channel = <0..7>,integer
        '''
        if channel == None:
            return self.query('EXC?')
        
        if not isinstance(channel,int):
            raise Exception('Excitation channel must be an integer.')
        
        if channel < 0 or channel > 7:
            raise Exception('Excitation channel must be between [0,7].')
        
        self.write( 'EXC ' + str(channel) )
        
    def display(self,channel = None):
        '''
        Set the channel that is displayed on the front panel.
        
        If no channel is specified, function queries instrument for the current display channel setting.
        
        Return type is a string.
        
        channel: Display channel
        channel = <0..7>,integer
        '''
        if channel == None:
            return self.query('EXC?')
        
        if not isinstance(channel,int):
            raise Exception('Display channel must be an integer.')
        
        if channel < 0 or channel > 7:
            raise Exception('Display channel must be between [0,7].')
        
        self.write( 'DIS ' + str(channel) )
        
    def adc(self):
        '''
        Enable the alarm flag, ensuring that the next measurement reading is up to date.
        
        Call this function before quering the resistance.
        '''
        self.write('ADC')
        
    def resistance(self):
        '''
        Perform a resistance query.
        
        This command requires you to first call the function adc().
        
        Return type is a float.        
        '''
        res = self.query('RES?')
        return float( res[4:len(res)] ) # Remove leading "RES "
        
        
        
        
        
        
        
        
        
