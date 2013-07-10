#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lakeshore340.py: Driver for the Lakeshore 340 cryogenic temp controller.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
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

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList

## CLASSES #####################################################################

class Lakeshore340Sensor(object):
    
    def __init__(self, parent, idx):
        self._parent = parent
        self._idx = idx + 1
        
    ## PROPERTIES ##
    
    @property
    def temperature(self):
        '''
        Gets the temperature of the specified sensor.
        
        :units: K
        :type: `~quantities.Quantity` with units Kelvin
        '''
        value = self._parent.query('KRDG?{}'.format(self._idx))
        return pq.Quantity(float(value), pq.Kelvin)

class Lakeshore340(SCPIInstrument):
    '''
    The Lakeshore340 is a multi-sensor cryogenic temperature controller.
    '''    
    
    ## PROPERTIES ##
    
    @property
    def sensor(self):
        '''
        Gets a specific sensor object. The desired sensor is specified like 
        one would access a list. 
        
        For instance, this would query the temperature of the first sensor::
        
        >>> bridge = Lakeshore340.open_serial("COM5")
        >>> print bridge.sensor[0].temperature
        
        The Lakeshore 340 supports up to 2 sensors (index 0-1).
        '''
        return ProxyList(self, Lakeshore340Sensor, xrange(2))
        
