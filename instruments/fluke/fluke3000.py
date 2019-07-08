#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# fluke3000.py: Driver for the Fluke 3000 FC Industrial System
#
# © 2019 Francois Drielsma (francois.drielsma@gmail.com).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#
"""
Driver for the Fluke 3000 FC Industrial System

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
import time
from builtins import range

from enum import Enum, IntEnum

import quantities as pq

from instruments.abstract_instruments import Multimeter
from instruments.util_fns import assume_units, bool_property, enum_property

# CLASSES #####################################################################


class Fluke3000(Multimeter):

    """The `Fluke3000` is an ecosystem of devices produced by Fluke that may be
    connected simultaneously to a Fluke PC3000 wireless adapter which exposes
    a serial port to the computer to send and receive commands.

    The `Fluke3000` ecosystem supports the following instruments:
     - Fluke 3000 FC Series Wireless Multimeter
     - Fluke v3000 FC Wireless AC Voltage Module
     - Fluke v3001 FC Wireless DC Voltage Module
     - Fluke t3000 FC Wireless Temperature Module

    `Fluke3000` is a USB instrument that communicates through a serial port
    via the PC3000 dongle. The commands used to communicate to the dongle
    do not follow the SCPI standard.
    
    When the device is reset, it searches for available wireless modules
    and binds them to the PC3000 dongle. At each initialization, this class
    checks what device has been bound and saves their module number.
    
    This class is a work in progress, it currently only supports the t3000
    FC Wireless Temperature Module as it is the only instrument available
    to the author. It also only supports single readout.
    """

    def __init__(self, filelike):
        """
        Initialise the instrument, and set the required eos, eoi needed for
        communication.
        """
        super(Fluke3000, self).__init__(filelike)
        self.timeout = 15 * pq.second
        self.terminator = "\r"
        self._null = False
        self.positions = {}
        self.connect()

    # ENUMS ##
    
    class Module(Enum):

        """
        Enum containing the supported module codes
        """
        #: Multimeter
        m3000 = 46333030304643
        #: Temperature module
        t3000 = 54333030304643
    
    class Mode(Enum):

        """
        Enum containing the supported mode codes
        """
        #: AC Voltage
        voltage_ac  = "01"
        #: DC Voltage
        voltage_dc  = "02"
        #: AC Current
        current_ac  = "03"
        #: DC Current
        current_dc  = "04"
        #: Frequency
        frequency   = "05"
        #: Temperature
        temperature = "07"
        #: Resistance
        resistance  = "0B"
        #: Capacitance
        capacitance = "0F"
        
    class TriggerMode(IntEnum):

        """
        Enum with valid trigger modes.
        """
        internal = 1
        external = 2
        single = 3
        hold = 4

    # PROPERTIES ##

    mode = enum_property(
        "",
        Mode,
        doc="""Set the measurement mode.

        :type: `Fluke3000.Mode`
        """,
        writeonly=True,
        set_fmt="{}{}")
        
    module = enum_property(
        "",
        Module,
        doc="""Set the measurement module.

        :type: `Fluke3000.Module`
        """,
        writeonly=True,
        set_fmt="{}{}")    
        
    trigger_mode = enum_property(
        "T",
        TriggerMode,
        doc="""Set the trigger mode.

        Note that using `HP3456a.measure()` will override the `trigger_mode` to
        `HP3456a.TriggerMode.single`.

        :type: `HP3456a.TriggerMode`

        """,
        writeonly=True,
        set_fmt="{}{}")
        
    @property
    def input_range(self):
        """Set the input range to be used.

        The `HP3456a` has separate ranges for `~quantities.ohm` and for
        `~quantities.volt`. The range value sent to the instrument depends on
        the unit set on the input range value. `auto` selects auto ranging.

        :type: `~quantities.Quantity`
        """
        raise NotImplementedError

    @input_range.setter
    def input_range(self, value):
        if isinstance(value, str):
            if value.lower() == "auto":
                self.sendcmd("R1W")
            else:
                raise ValueError("Only 'auto' is acceptable when specifying "
                                 "the input range as a string.")

        elif isinstance(value, pq.quantity.Quantity):
            if value.units == pq.volt:
                valid = HP3456a.ValidRange.voltage.value
                value = value.rescale(pq.volt)
            elif value.units == pq.ohm:
                valid = HP3456a.ValidRange.resistance.value
                value = value.rescale(pq.ohm)
            else:
                raise ValueError("Value {} not quantity.volt or quantity.ohm"
                                 "".format(value))

            value = float(value)
            if value not in valid:
                raise ValueError("Value {} outside valid ranges "
                                 "{}".format(value, valid))
            value = valid.index(value) + 2
            self.sendcmd("R{}W".format(value))
        else:
            raise TypeError("Range setting must be specified as a float, int, "
                            "or the string 'auto', got {}".format(type(value)))

    @property
    def relative(self):
        """
        Enable or disable `HP3456a.MathMode.Null` on the instrument.

        :type: `bool`
        """
        return self._null

    @relative.setter
    def relative(self, value):
        if value is True:
            self._null = True
            self.sendcmd("M{}".format(HP3456a.MathMode.null.value))
        elif value is False:
            self._null = False
            self.sendcmd("M{}".format(HP3456a.MathMode.off.value))
        else:
            raise TypeError("Relative setting must be specified as a bool, "
                            "got {}".format(type(value)))

    # METHODS ##
        
    def connect(self):
        """
        Connect to available modules and returns
        a dictionary of the modules found and their location
        """
        self.flush()                    # Flush serial
        self.scan()                     # Look for connected devices
        if not self.positions:
            self.reset()                # Resets the PC3000 dongle
            self.query("rfdis", 3)      # Discovers connected modules
            self.scan()                 # Look for connected devices
            
        if not self.positions:
            raise ValueError("No Fluke3000 modules available")

        self.timeout = 3 * pq.second

    def flush(self):
        timeout = self.timeout
        self.timeout = 0.1 * pq.second
        init_time = time.time()
        while time.time() - init_time < timeout:
            try:
                self.read()
            except:
                break
        self.timeout = timeout
        
    def reset(self):
        """
        Resets the device and unbinds all modules
        """
        self.query("ri", 3)             # Resets the device
        self.query("rfsm 1", 2)         # Turns comms on
                
    def scan(self):
        """
        Search for available modules and returns
        a dictionary of the modules found and their location
        """
        # Loop over possible channels, store device locations
        positions = {}
        for port_id in range(1, 7):
            # Check if a device is connected to port port_id
            output = self.query("rfebd 0{} 0".format(port_id))[0]
            if "RFEBD" not in output:
                continue
            
            # If it is, identify the device
            self.read()
            output = self.query('rfgus 0{}'.format(port_id), 2)[-1]
            module_id = int(output.split("PH=")[-1])
            if module_id == self.Module.m3000.value:
                positions[self.Module.m3000] = port_id
            elif module_id == self.Module.t3000.value:
                positions[self.Module.t3000] = port_id
            else:
                error = "Module ID {} not implemented".format(module_id)
                raise NotImplementedError(error)

            # Reset device readout    
            self.query('rfemd 0{} 2'.format(port_id))

        self.flush()
        self.positions = positions

    def read_lines(self, nlines=1):
        """
        Function that keeps reading until reaches a termination
        character a set amount of times. This is implemented
        to handle the mutiline output of the PC3000

        :param nlines: Number of termination characters to reach

        :type: 'int'

        :return: Array of lines read out
        :rtype: Array of `str`

        """
        lines = []
        i = 0
        while i < nlines:
            try:
                lines.append(self.read())
                i += 1
            except :
                continue

        return lines

    def query(self, cmd, nlines=1):
        """
        Function used to send a command to the instrument while allowing
        for multiline output (multiple termination characters)

        :param cmd: Command that will be sent to the instrument
        :param nlines: Number of termination characters to reach

        :type cmd: 'str'
        :type nlines: 'int'

        :return: The multiline result from the query
        :rtype: Array of `str`

        """
        self.sendcmd(cmd)
        return self.read_lines(nlines)
    
    def measure(self, mode):
        """Instruct the Fluke3000 to perform a one time measurement. 

        Example usage:

        >>> dmm = ik.fluke.Fluke3000.open_serial("/dev/ttyUSB0")
        >>> print dmm.measure(dmm.Mode.temperature)

        :param mode: Desired measurement mode.

        :type mode: `Fluke3000.Mode`

        :return: A measurement from the multimeter.
        :rtype: `~quantities.quantity.Quantity`

        """
        # Check that the mode is supported
        if not isinstance(mode, self.Mode):
            raise ValueError("Mode {} is not supported".format(mode))

        # Check that the module associated with this mode is available
        module = self._get_module(mode)
        if module not in self.positions.keys():
            raise ValueError("Device necessary to measure {} is not available".format(mode))

        # Query the module
        value = ''
        port_id = self.positions[module]
        init_time = time.time()
        while time.time() - init_time < self.timeout:
            # Read out
            if mode == self.Mode.temperature:
                # The temperature module supports single readout
                value = self.query("rfemd 0{} 0".format(port_id), 2)[1]
            else:
                # The multimeter does not support single readout,
                # have to open continuous readout, read, then close it
                value = self.query("rfemd 0{} 1".format(port_id), 2)[1]
                self.query("rfemd 0{} 2".format(port_id))

            # Check that value is consistent with the request, break
            if "PH" in value:
                data = value.split("PH=")[-1]
                if self._parse_mode(data) != mode.value:
                    self.flush()
                else:
                    break

        # Parse the output
        try:
            value = self._parse(value, mode)
        except:
            raise ValueError("Failed to read out Fluke3000 with mode {}".format(mode))

        # Return with the appropriate units
        units = UNITS[mode]
        return value * units
        
    def _get_module(self, mode):
        """Gets the module associated with this measurement mode.

        :param mode: Desired measurement mode.

        :type mode: `Fluke3000.Mode`

        :return: A Fluke3000 module.
        :rtype: `Fluke3000.Module`

        """
        if mode == self.Mode.temperature:
            return self.Module.t3000
        else:
            return self.Module.m3000

    def _parse(self, result, mode):
        """Parses the module output.

        :param result: Output of the query. 
        :param mode: Desired measurement mode. 
      
        :type result: `string`  
        :type mode: `Fluke3000.Mode`

        :return: A measurement from the multimeter.
        :rtype: `Quantity`

        """
        # Check that a value is contained
        if "PH" not in result:
            raise ValueError("Cannot parse a string that does not contain a return value")

        # Isolate the data string from the output
        data = result.split('PH=')[-1]

        # Check that the multimeter is in the right mode (fifth byte)
        if self._parse_mode(data) != mode.value:
            error =  "Mode {} was requested but the Fluke 3000FC Multimeter is in ".format(mode.name)
            error += "mode {} instead, could not read the requested quantity.".format(self.Mode(data[8:10]).name)
            raise ValueError(error)

        # Extract the value from the first two bytes
        value = self._parse_factor(data)

        # Extract the prefactor from the fourth byte
        try:
            scale = self._parse_factor(data)
        except:
            raise ValueError("Could not parse the prefactor byte")

        # Combine and return
        return scale*value

    def _parse_mode(self, data):
        """Parses the measurement mode.

        :param data: Measurement output.

        :type data: `str`

        :return: A Mode string.
        :rtype: `str`

        """
        # The fixth dual hex byte encodes the measurement mode
        return data[8:10]

    def _parse_value(self, data):
        """Parses the measurement value.

        :param data: Measurement output.

        :type data: `str`

        :return: A value.
        :rtype: `float`

        """
        # The second dual hex byte is the most significant byte
        return int(data[2:4]+data[:2], 16)

    def _parse_factor(self, data):
        """Parses the measurement prefactor.

        :param data: Measurement output.

        :type data: `str`

        :return: A prefactor.
        :rtype: `float`

        """
        # Convert the fourth dual hex byte to an 8 bits string
        byte = '{0:08b}'.format(int(data[6:8], 16))

        # The first bit encodes the sign (0 positive, 1 negative)
        sign = 1 if byte[0] == '0' else -1

        # The second to fourth bits encode the metric prefix
        code = int(byte[1:4], 2)
        if code not in PREFIXES.keys():
            raise ValueError("Metric prefix not recognized: {}".format(code))
        prefix = PREFIXES[code]

        # The sixth and seventh bit encode the decimal place
        scale = 10**(-int(byte[5:7], 2))

        # Return the combination
        return sign*prefix*scale

# UNITS #######################################################################

UNITS = {
    None: 1,
    Fluke3000.Mode.voltage_ac:  pq.volt,
    Fluke3000.Mode.voltage_dc:  pq.volt,
    Fluke3000.Mode.current_ac:  pq.amp,
    Fluke3000.Mode.current_dc:  pq.amp,
    Fluke3000.Mode.frequency:   pq.hertz,
    Fluke3000.Mode.temperature: pq.celsius,
    Fluke3000.Mode.resistance:  pq.ohm,
    Fluke3000.Mode.capacitance: pq.farad
}

# METRIC PREFIXES #############################################################

PREFIXES = {
    0: 1e0,     # None
    2: 1e6,     # Mega
    3: 1e3,     # Kilo
    4: 1e-3,    # milli
    5: 1e-6,    # micro
    6: 1e-9     # nano
}

