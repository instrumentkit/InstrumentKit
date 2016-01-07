#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lakeshore370.py: Driver for the Lakeshore 370 AC resistance bridge.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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

class Lakeshore370(SCPIInstrument):
    """
    The Lakeshore 370 is a multichannel AC resistance bridge for use in low 
    temperature dilution refridgerator setups.
    
    Example usage:
    
    >>> import instruments as ik
    >>> bridge = ik.lakeshore.Lakeshore370.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print inst.channel[0].resistance
    """

    def __init__(self, filelike):
        super(Lakeshore370, self).__init__(filelike)
        self.sendcmd('IEEE 3,0') # Disable termination characters and enable EOI
    
    ## INNER CLASSES ##
    
    class Channel(object):
        """
        Class representing a sensor attached to the Lakeshore 370.
        
        .. warning:: This class should NOT be manually created by the user. It is 
            designed to be initialized by the `Lakeshore370` class.
        """
        
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1
            
        ## PROPERTIES ##
        
        @property
        def resistance(self):
            """
            Gets the resistance of the specified sensor.
            
            :units: Ohm
            :rtype: `~quantities.quantity.Quantity`
            """
            value = self._parent.query('RDGR? {}'.format(self._idx))
            return pq.Quantity(float(value), pq.ohm)
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like 
        one would access a list. 
        
        For instance, this would query the resistance of the first channel::
        
        >>> import instruments as ik
        >>> bridge = ik.lakeshore.Lakeshore370.open_serial("COM5")
        >>> print bridge.channel[0].resistance
        
        The Lakeshore 370 supports up to 16 channels (index 0-15).
        
        :rtype: `~Lakeshore370.Channel`
        """
        return ProxyList(self, Lakeshore370.Channel, xrange(16))
        
