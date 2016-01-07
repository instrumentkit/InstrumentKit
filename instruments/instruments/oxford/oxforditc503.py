#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# oxforditc503.py: Driver for the Oxford ITC 503 temperature controller.
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList, assume_units

## CLASSES #####################################################################

class OxfordITC503(Instrument):
    """
    The Oxford ITC503 is a multi-sensor temperature controller.
    
    Example usage::
    
    >>> import instruments as ik
    >>> itc = ik.oxford.OxfordITC503.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print itc.sensor[0].temperature
    >>> print itc.sensor[1].temperature
    """
    
    def __init__(self, filelike):
        super(OxfordITC503, self).__init__(filelike)
        self.terminator = 13 # Set EOS char to CR
        self.sendcmd('C3') # Enable remote commands
        
    ## INNER CLASSES ##
    
    class Sensor(object):
        """
        Class representing a probe sensor on the Oxford ITC 503.
        
        .. warning:: This class should NOT be manually created by the user. It is 
            designed to be initialized by the `OxfordITC503` class.
        """
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1
            
        ## PROPERTIES ##
        
        @property
        def temperature(self):
            """
            Read the temperature of the attached probe to the specified channel.
            
            :units: Kelvin
            :rtype: `~quantities.quantity.Quantity`
            """
            value = float(self._parent.query('R{}'.format(self._idx))[1:])
            return pq.Quantity(value, pq.Kelvin)
       
    ## PROPERTIES ##
    
    @property
    def sensor(self):
        """
        Gets a specific sensor object. The desired sensor is specified like
        one would access a list.
        
        For instance, this would query the temperature of the first sensor::
        
        >>> itc = ik.other.OxfordITC503.open_gpibusb('/dev/ttyUSB0', 1)
        >>> print itc.sensor[0].temperature
        """
        return ProxyList(self, OxfordITC503.Sensor, xrange(3))
