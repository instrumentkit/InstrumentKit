#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley6220.py: Driver for the Keithley 6220 current source.
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

class Keithley6220(SCPIInstrument):
    
    def output(self, current):
        '''
        Set the output current of the source.
        
        :param float current: Desired output current setting. Must be between
            -105mA and +105mA.
        '''
        if not isinstance(current, float):
            raise TypeError('Current must be specified as a float.')
            
        if (current < -105e-3) or (current > 105e-3):
            raise ValueError('Current must be betwen -105e-3 and 105e-3')
            
        self.sendcmd('SOUR:CURR {}'.format(current))
        
    def disable(self):
        '''
        Set the output current to zero and disable the output.
        '''
        self.sendcmd('SOUR:CLE:IMM')
