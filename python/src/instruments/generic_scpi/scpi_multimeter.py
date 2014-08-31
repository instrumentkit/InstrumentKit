#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# scpimultimeter.py: Python class for SCPI complient multimeters
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

from flufl.enum import Enum
from flufl.enum._enum import EnumValue

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Multimeter
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import enum_property

## CONSTANTS ###################################################################

VALID_FRES_NAMES = ['4res','4 res','four res','f res']

UNITS_CAPACITANCE = ['cap']
UNITS_VOLTAGE = ['volt:dc','volt:ac','diod']
UNITS_CURRENT = ['curr:dc','curr:ac']
UNITS_RESISTANCE = ['res','fres'] + VALID_FRES_NAMES
UNITS_FREQUENCY = ['freq']
UNITS_TIME = ['per']
UNITS_TEMPERATURE = ['temp']
    
## CLASSES #####################################################################

class SCPIMultimeter(Multimeter, SCPIInstrument):

    ## ENUMS ##
    
    class Mode(Enum):
        capacitance = "CAP"
        continuity = "CONT"
        current_ac = "CURR:AC"
        current_dc = "CURR:DC"
        diode = "DIOD"
        frequency = "FREQ"
        fourpt_resistance = "FRES"
        period = "PER"
        resistance = "RES"
        temperature = "TEMP"
        voltage_ac = "VOLT:AC"
        voltage_dc = "VOLT:DC"
    
    class TriggerSource(Enum):
        """
        Valid trigger sources for most SCPI Multimeters.
        
        "Immediate": This is a continuous trigger. This means the trigger 
        signal is always present.
        
        "External": External TTL pulse on the back of the instrument. It 
        is active low.
        
        "Bus": Causes the instrument to trigger when a ``*TRG`` command is 
        sent by software. This means calling the trigger() function.
        """
        immediate = "IMM"
        external = "EXT"
        bus = "BUS"
        
    class DeviceRange(Enum):
        """
        Valid device range parameters outside of directly specifying the range.
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"
        automatic = "AUTO"
        
    class Resolution(Enum):
        """
        
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"
    
    ## PROPERTIES ##
    
    mode = enum_property(
        name="CONF",
        enum=Mode,
        doc="""
        Gets/sets the current measurement mode for the multimeter.
        
        Example usage:
        
        >>> dmm.mode = dmm.Mode.voltage_dc
        
        :type: `~SCPIMultimeter.Mode`
        """,
        #input_decoration = _mode_parse, # FIXME: Can't get this line to work
        set_fmt="{}:{}"
    )
    
    trigger_source = enum_property(
        name="TRIG:SOUR",
        enum=TriggerSource,
        doc="""
            Gets/sets the SCPI Multimeter trigger source.
            
            Example usage:
            
            >>> dmm.trigger_source = dmm.TriggerSource.external
            
            :type: `~SCPIMultimeter.Trigger`
        """)
        
    @property
    def device_range(self):
        """
        Gets/sets the device range for the device range for the currently
        set multimeter mode.
        
        Example usages:
        
        >>> dmm.device_range = dmm.DeviceRange.automatic
        >>> dmm.device_range = 1 * pq.millivolt
        
        :units: As appropriate for the current mode setting.
        :type: `~quantities.Quantity`, or `~SCPIMultimeter.DeviceRange`
        """
        value = self.query('CONF?')
        value = value.split(" ")[1].split(",")[0] # Extract device range
        try:
            return float(value) * UNITS[self.mode]
        except:
            return self.DeviceRange[value.strip()]
    @device_range.setter
    def device_range(self, newval):
        mode = self.mode
        units = UNITS[mode]
        if isinstance(newval, EnumValue) and (newval.enum is self.DeviceRange):
            newval = newval.value
        else:
            newval = assume_units(newval, units).rescale(units).magnitude
        #self.sendcmd("CONF {},{}".format(mode.value, newval))
        self._configure(device_range=newval)
    
    @property
    def resolution(self):
        """
        Gets/sets the measurement resolution for the multimeter. When 
        specified as a float it is assumed that the user is providing an
        appropriate value.
        
        Example usage:
        
        >>> dmm.resolution = 4.5
        >>> dmm.resolution = dmm.Resolution.maximum
        
        :type: `int`, `float` or `~SCPIMultimeter.Resolution`
        """
        value = self.query('CONF?')
        value = value.split(" ")[1].split(",")[1] # Extract device range
        try:
            return float(value)
        except:
            return self.Resolution[value.strip()]
    @resolution.setter
    def resolution(self, newval):
        if isinstance(newval, EnumValue) and (newval.enum is self.Resolution):
            newval = newval.value
        elif not isinstance(newval, float) and not isinstance(newval, int):
            raise TypeError("Resolution must be specified as an int, float, "
                            "or SCPIMultimeter.Resolution value.")
        self._configure(resolution=newval)
    
    ## METHODS ##
    
    def measure(self, mode=None):
        """
        Instruct the multimeter to perform a one time measurement. The 
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are 
        directly sent to the instrument's output buffer.
        
        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units. If no appropriate units exist,
        (for example, continuity), then return type is `float`.
        
        :param mode: Desired measurement mode. If set to `None`, will default 
            to the current mode.
        :type mode: `~SCPIMultimeter.Mode`
        """
        
        # Default to the current mode.
        if mode is None:
            mode = self.mode
            
        # Throw an error if the mode isn't an enum.
        if mode.enum is not SCPIMultimeter.Mode:
            raise TypeError("Mode must be specified as a SCPIMultimeter.Mode "
                            "value, got {} instead.".format(type(newval)))
        
        # Unpack the value from the enumeration.
        mode = mode._value.lower()
        # mode = VALID_MODES_SHORT[VALID_MODES.index(mode)]
        
        # Apply the mode and obtain the measurement.
        self.mode = mode
        value = float(self.query('MEAS:{}?'.format(mode)))
        
        # Put the measurement into the correct units.
        return value * UNITS[mode]
        
    ## INTERNAL FUNCTIONS ##

    def _mode_parse(self, val):
        """
        When given a string of the form
        
        "VOLT +1.00000000E+01,+3.00000000E-06"
        
        this function will return just the first component representing the mode
        the multimeter is currently in.
        
        :param str val: Input string to be parsed.
        
        :rtype: `str`
        """
        val = val.split(" ")[0]
        if val == "VOLT":
            val = "VOLT:DC"
        return val
        
    def _configure(self, device_range=None, resolution=None):
        """
        Internally used by two properties to construct the string for setting the
        device range or resolution.
        
        Assumes device_range and resolution are properly formatted if not an 
        EnumValue.
        """
        #pass
        if device_range is not None:
            self.sendcmd("CONF:{} {}".format(self.mode.value, device_range))
        elif resolution is not None:
            mode = self.mode
            device_range = self.device_range
            if isinstance(newval, EnumValue):
                device_range = device_range.value
            self.sendcmd("CONF:{} {},{}".format(mode.value, 
                                                device_range,
                                                resolution))
                                                
## UNITS #######################################################################

UNITS = {
    SCPIMultimeter.Mode.capacitance: pq.farad,
    SCPIMultimeter.Mode.voltage_dc:  pq.volt,
    SCPIMultimeter.Mode.voltage_ac:  pq.volt,
    SCPIMultimeter.Mode.diode:       pq.volt,
    SCPIMultimeter.Mode.current_ac:  pq.amp,
    SCPIMultimeter.Mode.current_dc:  pq.amp,
    SCPIMultimeter.Mode.resistance:  pq.ohm,
    SCPIMultimeter.Mode.fourpt_resistance: pq.ohm,
    SCPIMultimeter.Mode.frequency:   pq.hertz,
    SCPIMultimeter.Mode.period:      pq.second,
    SCPIMultimeter.Mode.temperature: pq.kelvin,
    SCPIMultimeter.Mode.continuity:  1,
}
            
        
