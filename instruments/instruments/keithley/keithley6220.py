#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley6220.py: Driver for the Keithley 6220 current source.
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

from instruments.abstract_instruments import PowerSupply
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class Keithley6220(SCPIInstrument, PowerSupply):
    """
    The Keithley 6220 is a single channel constant current supply.
    
    Because this is a constant current supply, most features that a regular
    power supply have are not present on the 6220.
    
    Example usage:
    
    >>> import quantities as pq
    >>> import instruments as ik
    >>> ccs = ik.keithley.Keithley6220.open_gpibusb('/dev/ttyUSB0', 10)
    >>> ccs.current = 10 * pq.milliamp # Sets current to 10mA
    >>> ccs.disable() # Turns off the output and sets the current to 0A
    """
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        """
        For most power supplies, this would return a channel specific object.
        However, the 6220 only has a single channel, so this function simply
        returns a tuple containing itself. This is for compatibility reasons
        if a multichannel supply is replaced with the single-channel 6220.
        
        For example, the following commands are the same and both set the 
        current to 10mA:
        
        >>> ccs.channel[0].current = 0.01
        >>> ccs.current = 0.01
        """
        return tuple(self)
        
    @property
    def voltage(self):
        """
        This property is not supported by the Keithley 6220.
        """
        raise NotImplementedError('The Keithley 6220 does not support voltage '
                                  'settings.')
    @voltage.setter
    def voltage(self, newval):
        raise NotImplementedError('The Keithley 6220 does not support voltage '
                                  'settings.')
    
    @property
    def current(self):
        """
        Gets/sets the output current of the source. Value must be between
        -105mA and +105mA.
        
        
        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
        return pq.Quantity(float(self.query(
                        'SOUR:CURR? {}'.format(self._idx)).strip()[:-1]), pq.amp)
    @current.setter
    def current(self, newval):
        newval = assume_units(newval, pq.amp).rescale(pq.amp)
        
        if (newval < -105e-3) or (newval > 105e-3):
            raise ValueError('Current must be betwen -105e-3 and 105e-3') 
        self.sendcmd('SOUR:CURR {}'.format(newval.magnitude))
    
    ## METHODS ##
    
    def disable(self):
        '''
        Set the output current to zero and disable the output.
        '''
        self.sendcmd('SOUR:CLE:IMM')
