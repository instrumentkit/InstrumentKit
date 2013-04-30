#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lakeshore370.py: Driver for the Lakeshore 370 AC resistance bridge.
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

class Lakeshore370(SCPIInstrument):

    def __init__(self, filelike):
        super(Lakeshore370, self).__init__(filelike)
        self.sendcmd('IEEE 3,0') # Disable termination characters and enable EOI
    
    def resistance(self, channel):
        '''
        Query resistance from a specific channel.
        
        :param int channel: Channel to measure resistance of. Valid channels are
            the numbers 1-16.
            
        :rtype: `float`
        '''
        if not isinstance(channel, int):
            raise Exception('Channel number must be specified as an integer.')
        
        if (channel < 1) or (channel > 16):
            raise Exception('Channel must be 1-16 (inclusive).')
        
        return float(self.query('RDGR? {}'.format(channel)))
            
            
            
            
            
            
            
        
        
        
        
        
        
        
