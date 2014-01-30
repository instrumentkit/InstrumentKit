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

from instruments.generic_scpi import SCPIInstrument
from instruments.abstract_instruments import Multimeter
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class Keithley2182(SCPIInstrument, Multimeter):
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
    
    def Mode(Enum):
        voltage_dc = 'VOLT'
        temperature = 'TEMP'
        
    def TriggerMode(Enum):
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
        """
        raise NotImplementedError
    
    @property
    def mode(self):
        """
        Gets/sets the measurement mode of the Keithley 2182. In comparison 
        to a multimeter, the 2182 only has two measurement modes: DC voltage 
        and temperature.
        
        Example use:
        
        >>> import instruments as ik
        >>> meter = ik.keithley.Keithley2182.open_gpibusb('/dev/ttyUSB0', 10)
        >>> meter.mode = meter.Mode.voltage_dc
        
        :type: `Keithley2182.Mode`
        """
        return Keithley2182.Mode[self.query('CONF?')]
    @mode.setter
    def mode(self, newval):
        if isinstance(newval, str):
            newval = Keithley2182.Mode[newval.upper()]
        if newval not in Keithley2182.Mode:
            raise TypeError("Mode must be specified as a Keithley2182.Mode "
                            "value, got {} instead.".format(newval))
        self.sendcmd('CONF:{}'.format(newval.value))
        
    @property
    def trigger_mode(self):
        """
        Gets/sets the trigger mode of the Keithley 2182.
        
        There are five different trigger sources for the 2182. These are
        ``immediate, external, bus, timer, manual``.
        
        :type: `Keithley2182.TriggerMode`
        """
        return Keithley2182.TriggerMode[self.query('TRIG:SOUR?')]
    @trigger_mode.setter
    def trigger_mode(self, newval):
        if isinstance(newval, str):
            newval = Keithley2182.TriggerMode[newval.upper()]
        if newval not in Keithley2182.TriggerMode:
            raise TypeError("Mode must be specified as a "
                            "Keithley2182.TriggerMode value, got {} "
                            "instead.".format(newval))
        self.sendcmd('CONF:{}'.format(newval.value))
        
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
    
    @property
    def trigger_count(self):
        """
        Gets/sets the number of triggers that the 2182 will accept 
        before returning to an "idle" trigger state.
        
        Note that if the sample count parameter has been changed, the number of 
        readings taken will be a multiplication of sample count and trigger 
        count (see `~Keithley2182.sample_count`).
        
        Number of triggers before returning to an "idle" trigger state. When 
        setting this, enter use an integer between ``[1,9999]`` or the string
        ``INF``.
        
        :type: `int` or `str`
        
        .. seealso::
            `Keithley2182.sample_count`
        """
        value = self.query('TRIG:COUN?')
        if value == 'INF':
            return value
        else:
            return int(value)
    @trigger_count.setter
    def trigger_count(self, newval):
        if isinstance(newval, str):
            newval = newval.upper()
            if newval == 'INFINITY':
                newval = 'INF'
            if newval != 'INF':
                raise ValueError('Valid trigger count value is "INFinity" '
                    'when specified as a string.')
        elif isinstance(newval, int):
            if newval < 1 or newval > 9999:
                raise ValueError('Trigger count must be a between '
                    '1 and 9999.')
            newval = str(newval)
        else:
            raise TypeError('Trigger count must be a string or an integer.')
        self.sendcmd('TRIG:COUN {}'.format(newval))
    
    @property    
    def trigger_delay(self):
        """
        Gets/sets the time delay which the instrument will use 
        following receiving a trigger event before starting the measurement.
        
        Time between receiving a trigger event and the instrument 
        taking the reading. Values range from 0s to ~3600s, in ~20us 
        increments.
        
        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units seconds.
        :type: `~quantities.quantity.Quantity` with units seconds
        """
        return float(self.query('TRIG:DEL?')) * pq.second
    @trigger_delay.setter
    def trigger_delay(self, newval):
        if isinstance(newval, str):
            newval = newval.upper()
            if newval == 'AUTO':
                self.sendcmd('TRIG:DEL:AUTO 1')
                return
        newval = float(assume_units(newval, pq.second).rescale(pq.second).magnitude)        
        if (newval < 0) or (newval >  999999.999):
            raise ValueError('The trigger delay needs to be between 0 '
                'and 1,000,000 seconds.')
        self.sendcmd('TRIG:DEL {}'.format(newval))
    
    @property    
    def sample_count(self):
        """
        This command sets the number of readings (samples) that the meter will 
        take per trigger.
        
        Note that if the sample count parameter has been changed, the number of 
        readings taken will be a multiplication of sample count and trigger 
        count (see function `~Keithley2182.trigger_count`).
            
        :type: `int`
        
        .. seealso::
            `Keithley2182.trigger_count`
        """
        return int(self.query('SAMP:COUN?'))
    @sample_count.setter
    def sample_count(self, newval):
        if isinstance(newval, int):
            if newval < 1 or newval > 1024:
                raise ValueError('Trigger count must be an integer, '
                    '1 to 1024.')
        else:
            raise TypeError('Trigger count must be an integer.')
        
        self.sendcmd('SAMP:COUN {}'.format(newval))
        
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
        :rtype: `list` of `float`
        """
        return map(float, self.query('FETC?').split(','))
    
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
        if isinstance(mode, str):
            newval = Keithley2182.Mode[mode.upper()]
        if mode not in Keithley2182.Mode:
            raise TypeError("Mode must be specified as a Keithley2182.Mode "
                            "value, got {} instead.".format(newval))
        value = float(self.query('MEAS:{}?'.format(mode)))
        if mode == Keithley2182.Mode.voltage_dc:
            return value * pq.volt
        else:
            unit = self.query('UNIT:TEMP?')
            if unit == 'C':
                unit = pq.celsius
            elif unit == 'K':
                unit = pq.kelvin
            elif unit == 'F':
                unit = pq.fahrenheit
            else:
                raise ValueError('Unknown temperature units.')
            return value * unit

