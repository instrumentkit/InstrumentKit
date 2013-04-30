#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# picowattavs47.py: Driver for the Picowatt AVS 47 resistance bridge.
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

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class PicowattAVS47(Instrument):
        
    def remote(self, state=None):
        '''
        Enable or disable the remote mode state.
        
        Enabling the remote mode allows all settings to be changed by computer 
        interface and locks-out the front panel.
        
        If not state is specified, function queries instrument for the current 
        remote mode state.
        
        Return type is a string.
        
        :param state: Remote mode state. One of {OFF|DISABLE|ON|ENABLE|0|1}
        :type: `int` or `str`
        
        :rtype: `str`
        '''
        if state == None:
            return self.query('REM?')
        
        if isinstance(state, str):
            state = state.lower()
        
        if state in ('off', '0', 0, 'disable'):
            self.sendcmd('REM 0')
        elif state in ('on', '1', 1, 'enable'):
            self.sendcmd('REM 1')
        else:
            raise ValueError('Remote state must be "off", "on", "disable", '
                               '"enable", "0" or "1".')
        
    def input_source(self, source=None):
        '''
        Set the input source.
            1) "GROUND": Connects the bridge input to ground. Recommended 
            before changing other bridge settings.
            2) "ACTUAL": Connects to the actual measurement.
            3) "REFerence": Connects to the internal precision 100ohm 
            resistor. Used for calibrating the scale factor.
            
        If no source is specified, function queries instrument for current 
        input source connection.
        
        :param source: Input source {GROund|ACTUAL|REFerence|100ohm|1|2|3}
        :type: `int` or `str`
        
        :rtype: `str`
        '''
        if source == None:
            return self.query('INP?')
        
        if isinstance(source,str):
            source = source.lower()
        
        if source in ('ground', 'gro', '0', 0):
            self.sendcmd('INP 0')
        elif source in ('actual', '1', 1):
            self.sendcmd('INP 1')
        elif source in ('reference', 'ref', '100ohm', '2', 2):
            self.sendcmd('INP 2')
        else:
            raise ValueError('Valid sources include "ground", "actual", '
                               ' "reference",0,1,2,"100ohm", and "ref".')
        
    def mux_channel(self, channel=None):
        '''
        Set the multiplexer channel.
        It is recommended that you ground the input before switching the 
        multiplexer channel.
        
        If no channel is specified, function queries instrument for the current 
        multiplexer channel setting.
        
        :param int channel: Multiplexer channel. One of <0..7>.
        
        :rtype: `str`
        '''
        if channel == None:
            return self.query('MUX?')
        
        if not isinstance(channel, int):
            raise TypeError('Multiplexer channel must be an integer.')
        
        if (channel < 0) or (channel > 7):
            raise ValueError('Multiplexer channel must be between [0,7].')
        
        self.sendcmd('MUX {}'.format(channel))
        
    def excitation(self, channel=None):
        '''
        Set the excitation channel.
        
        If no channel is specified, function queries instrument for the 
        current excitation channel setting.
        
        :param int channel: Excitation channel. One of <0..7>.
        
        :rtype: `str`
        '''
        if channel == None:
            return self.query('EXC?')
        
        if not isinstance(channel, int):
            raise TypeError('Excitation channel must be an integer.')
        
        if (channel < 0) or (channel > 7):
            raise ValueError('Excitation channel must be between [0,7].')
        
        self.sendcmd('EXC {}'.format(channel))
        
    def display(self, channel=None):
        '''
        Set the channel that is displayed on the front panel.
        
        If no channel is specified, function queries instrument for the 
        current display channel setting.
        
        :param int channel: Display channel. One of <0..7>.
        
        :rtype: `str`
        '''
        if channel == None:
            return self.query('EXC?')
        
        if not isinstance(channel, int):
            raise TypeError('Display channel must be an integer.')
        
        if (channel < 0) or (channel > 7):
            raise ValueError('Display channel must be between [0,7].')
        
        self.sendcmd('DIS {}'.format(channel))
        
    def adc(self):
        '''
        Enable the alarm flag, ensuring that the next measurement reading 
        is up to date.
        
        Call this function before quering the resistance.
        '''
        self.write('ADC')
        
    def resistance(self):
        '''
        Perform a resistance query.
        
        This command requires you to first call the function 
        `~Picowattavs47.adc`.
        
        :rtype: `float`        
        '''
        res = self.query('RES?')
        return float( res[4:len(res)] ) # Remove leading "RES "
        
        
        
        
        
        
        
        
        
