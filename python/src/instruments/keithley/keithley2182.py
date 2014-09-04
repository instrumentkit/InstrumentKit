#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley2182.py: Driver for the Keithley 2182 nano-voltmeter.
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

from flufl.enum import Enum
import quantities as pq

from instruments.generic_scpi import SCPIMultimeter
from instruments.abstract_instruments import Multimeter
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class _Keithley2182Channel(Multimeter):
    """
    Class representing a channel on the Keithley 2182 nano-voltmeter.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `Keithley2182` class.
    """
    
    def __init__(self, parent, idx):
        self._parent = parent
        self._idx = idx + 1
        
    ## PROPERTIES ##
    
    @property
    def mode(self):
        return Keithley2182.Mode[self._parent.query('SENS:FUNC?')]
    @mode.setter
    def mode(self, newval):
        raise NotImplementedError
    
    @property
    def trigger_mode(self):
        raise NotImplementedError
    @trigger_mode.setter
    def trigger_mode(self, newval):
        raise NotImplementedError
        
    @property
    def relative(self):
        raise NotImplementedError
    @relative.setter
    def relative(self, newval):
        raise NotImplementedError
    
    @property
    def input_range(self):
        raise NotImplementedError
    @input_range.setter
    def input_range(self, newval):
        raise NotImplementedError
        
    ## METHODS ##
    
    def measure(self, mode=None):
        """
        #TODO docstring
        """
        if mode is not None:
            self.mode = mode
        self._parent.sendcmd('SENS:CHAN {}'.format(idx))
        value = float(self._parent.query('SENS:DATA:FRES?'))
        unit = self._parent.units
        return value * unit
        

class Keithley2182(SCPIMultimeter):
    """
    The Keithley 2182 is a nano-voltmeter. You can find the full specifications
    list in the `user's guide`_.
    
    Example usage:
    
    >>> import instruments as ik
    >>> import quantities as pq
    >>> meter = ik.keithley.Keithley2182.open_gpibusb('/dev/ttyUSB0', 10)
    >>> print meter.measure(meter.Mode.voltage_dc)
    
    .. _user's guide: http://www.keithley.com/products/dcac/sensitive/lowvoltage/?mn=2182A
    """
    
    def __init__(self, filelike):
        super(Keithley2182, self).__init__(filelike)
        
    ## ENUMS ##
    
    class Mode(Enum):
        voltage_dc = 'VOLT'
        temperature = 'TEMP'
        
    class TriggerMode(Enum):
        immediate = 'IMM'
        external = 'EXT'
        bus = 'BUS'
        timer = 'TIM'
        manual = 'MAN'
        
    ## PROPERTIES ##
    
    @property
    def channel(self):
        """
        Gets a specific Keithley 2182 channel object. The desired channel is
        specified like one would access a list.
        
        Although not default, the 2182 has up to two channels.
        
        For example, the following would print the measurement from channel 1:
        
        >>> meter = ik.keithley.Keithley2182.open_gpibusb('/dev/ttyUSB0', 10)
        >>> print meter.channel[0].measure()
        
        :rtype: `_Keithley2182Channel`
        """
        return ProxyList(self, _Keithley2182Channel, xrange(2))
        
    @property
    def relative(self):
        """
        Gets/sets the relative measurement function of the Keithley 2182.
        
        This is used to enable or disable the relative function for the 
        currently set mode. When enabling, the current reading is used as a 
        baseline which is subtracted from future measurements. 
        
        If relative is already on, the stored value is refreshed with the 
        currently read value.
        
        See the manual for more information.
        
        :type: `bool`
        """
        mode = self.mode
        return self.query('SENS:{}:CHAN1:REF:STAT?'.format(mode.value)) == 'ON'
    @relative.setter
    def relative(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Relative mode must be a boolean.')
        mode = self.mode
        if (self.relative):
            self.sendcmd('SENS:{}:CHAN1:REF:ACQ'.format(mode.value))
        else:
            newval = ('ON' if newval is True else 'OFF')
            self.sendcmd('SENS:{}:CHAN1:REF:STAT {}'.format(mode.value, newval))

    @property
    def input_range(self):
        raise NotImplementedError
    @input_range.setter
    def input_range(self, newval):
        raise NotImplementedError
        
    @property
    def units(self):
        """
        Gets the current measurement units of the instrument.
        
        :rtype: `~quantities.unitquantity.UnitQuantity`
        """
        mode = self.mode
        if mode == Keithley2182.Mode.voltage_dc:
            return pq.ohm
        unit = self.query('UNIT:TEMP?')
        if unit == 'C':
            unit = pq.celsius
        elif unit == 'K':
            unit = pq.kelvin
        elif unit == 'F':
            unit = pq.fahrenheit
        else:
            raise ValueError('Unknown temperature units.') 
        return unit
        
    ## METHODS ##
        
    def fetch(self):
        """
        Transfer readings from instrument memory to the output buffer, and thus 
        to the computer.
        If currently taking a reading, the instrument will wait until it is 
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? command 
        to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not 
        recommended to transfer a large number of data points using GPIB.
        
        :return: Measurement readings from the instrument output buffer.
        :rtype: `list` of `~quantities.quantity.Quantity` elements
        """
        return map(float, self.query('FETC?').split(',')) * self.units
    
    def measure(self, mode=None):
        """
        Perform and transfer a measurement of the desired type.
        
        :param mode: Desired measurement mode. If left at default the 
            measurement will occur with the current mode.
        :type: `Keithley2182.Mode`
        
        :return: Returns a single shot measurement of the specified mode.
        :rtype: `~quantities.quantity.Quantity`
        :units: Volts, Celsius, Kelvin, or Fahrenheit
        """
        if mode is None:
            mode = self.mode
        if mode not in Keithley2182.Mode:
            raise TypeError("Mode must be specified as a Keithley2182.Mode "
                            "value, got {} instead.".format(newval))
        value = float(self.query('MEAS:{}?'.format(mode)))
        unit = self.units
        return value * unit

