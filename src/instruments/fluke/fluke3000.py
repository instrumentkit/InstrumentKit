#!/usr/bin/env python
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

import time
from enum import Enum

from instruments.abstract_instruments import Multimeter
from instruments.units import ureg as u

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

    This class has been tested with the 3000 FC Wireless Multimeter and
    the t3000 FC Wireless Temperature Module. They have been operated
    separately and simultaneously. It does not support the Wireless AC/DC
    Voltage Modules as the author did not have them on hand.

    It is important to note that the mode of the multimeter cannot be set
    remotely. If must be set on the device prior to the measurement. If
    the measurement read back from the multimeter is not expressed in the
    expected units, this module will raise an error.

    Example usage:

    >>> import instruments as ik
    >>> mult = ik.fluke.Fluke3000.open_serial("/dev/ttyUSB0", 115200)
    >>> mult.measure(mult.Mode.voltage_dc) # Measures the DC voltage
    array(12.345) * V

    It is crucial not to kill this program in the process of making a measurement,
    as for the Fluke 3000 FC Wireless Multimeter, one has to open continuous
    readout, make a read and close it. If the process is killed, the read out
    may not be closed and the serial cache will be constantly filled with measurements
    that will interfere with any status query. If the multimeter is stuck in
    continuous trigger after a bad kill, simply do:

    >>> mult.reset()
    >>> mult.flush()
    >>> mult.connect()

    Follow the same procedure if you want to add/remove an instrument to/from
    the readout chain as the code will not look for new instruments if some
    have already been connected to the PC3000 dongle.
    """

    def __init__(self, filelike):
        """
        Initialize the instrument, and set the properties needed for communication.
        """
        super().__init__(filelike)
        self.timeout = 3 * u.second
        self.terminator = "\r"
        self.positions = {}
        self.connect()

    # ENUMS ##

    class Module(Enum):
        """
        Enum containing the supported modules serial numbers.
        """

        #: Multimeter
        m3000 = 46333030304643
        #: Temperature module
        t3000 = 54333030304643

    class Mode(Enum):
        """
        Enum containing the supported mode codes.
        """

        #: AC Voltage
        voltage_ac = "01"
        #: DC Voltage
        voltage_dc = "02"
        #: AC Current
        current_ac = "03"
        #: DC Current
        current_dc = "04"
        #: Frequency
        frequency = "05"
        #: Temperature
        temperature = "07"
        #: Resistance
        resistance = "0B"
        #: Capacitance
        capacitance = "0F"

    # PROPERTIES ##

    @property
    def mode(self):
        """
        Gets/sets the measurement mode for the multimeter.

        The measurement mode of the multimeter must be set on the
        device manually and cannot be set remotely. If a multimeter
        is bound to the PC3000, returns its measurement mode by
        making a measurement and checking the units bytes in response.

        :rtype: `Fluke3000.Mode`
        """
        if self.Module.m3000 not in self.positions:
            raise KeyError("No `Fluke3000` FC multimeter is bound")
        port_id = self.positions[self.Module.m3000]
        value = self.query_lines(f"rfemd 0{port_id} 1", 2)[-1]
        self.query(f"rfemd 0{port_id} 2")
        data = value.split("PH=")[-1]
        return self.Mode(self._parse_mode(data))

    @property
    def trigger_mode(self):
        """
        Gets/sets the trigger mode for the multimeter.

        The only supported mode is to trigger the device once when a
        measurement is queried. This device does support continuous
        triggering but it would quickly flood the serial input cache as
        readouts do not overwrite each other and are accumulated.

        :rtype: `str`
        """
        raise AttributeError(
            "The `Fluke3000` only supports single trigger when queried"
        )

    @property
    def relative(self):
        """
        Gets/sets the status of relative measuring mode for the multimeter.

        The `Fluke3000` FC does not support relative measurements.

        :rtype: `bool`
        """
        raise AttributeError(
            "The `Fluke3000` FC does not support relative measurements"
        )

    @property
    def input_range(self):
        """
        Gets/sets the current input range setting of the multimeter.

        The `Fluke3000` FC is an autoranging only multimeter.

        :rtype: `str`
        """
        raise AttributeError("The `Fluke3000` FC is an autoranging only multimeter")

    # METHODS #

    def connect(self):
        """
        Connect to available modules and returns a dictionary
        of the modules found and their port ID.
        """
        self.scan()  # Look for connected devices
        if not self.positions:
            self.reset()  # Reset the PC3000 dongle
            timeout = self.timeout  # Store default timeout
            self.timeout = (
                30 * u.second
            )  # PC 3000 can take a while to bind with wireless devices
            self.query_lines("rfdis", 3)  # Discover available modules and bind them
            self.timeout = timeout  # Restore default timeout
            self.scan()  # Look for connected devices

        if not self.positions:
            raise ValueError("No `Fluke3000` modules available")

    def scan(self):
        """
        Search for available modules and reformat. Returns a dictionary
        of the modules found and their port ID.
        """
        # Loop over possible channels, store device locations
        positions = {}
        for port_id in range(1, 7):
            # Check if a device is connected to port port_id
            output = self.query(f"rfebd 0{port_id} 0")
            if "RFEBD" not in output:
                continue

            # If it is, identify the device
            self.read()
            output = self.query_lines(f"rfgus 0{port_id}", 2)[-1]
            module_id = int(output.split("PH=")[-1])
            if module_id == self.Module.m3000.value:
                positions[self.Module.m3000] = port_id
            elif module_id == self.Module.t3000.value:
                positions[self.Module.t3000] = port_id
            else:
                raise NotImplementedError(f"Module ID {module_id} not implemented")

        self.positions = positions

    def reset(self):
        """
        Resets the device and unbinds all modules.
        """
        self.query_lines("ri", 3)  # Resets the device
        self.query_lines("rfsm 1", 2)  # Turns comms on

    def read_lines(self, nlines=1):
        """
        Function that keeps reading until reaches a termination
        character a set amount of times. This is implemented
        to handle the mutiline output of the PC3000.

        :param nlines: Number of termination characters to reach

        :type nlines: 'int'

        :return: Array of lines read out
        :rtype: Array of `str`

        """
        return [self.read() for _ in range(nlines)]

    def query_lines(self, cmd, nlines=1):
        """
        Function used to send a query to the instrument while allowing
        for the multiline output of the PC3000.

        :param cmd: Command that will be sent to the instrument
        :param nlines: Number of termination characters to reach

        :type cmd: 'str'
        :type nlines: 'int'

        :return: The multiline result from the query
        :rtype: Array of `str`

        """
        self.sendcmd(cmd)
        return self.read_lines(nlines)

    def flush(self):
        """
        Flushes the serial input cache.

        This device outputs a terminator after each output line.
        The serial input cache is flushed by repeatedly reading
        until a terminator is not found.
        """
        timeout = self.timeout
        self.timeout = 0.1 * u.second
        init_time = time.time()
        while time.time() - init_time < 1.0:
            try:
                self.read()
            except OSError:
                break
        self.timeout = timeout

    def measure(self, mode):
        """Instruct the Fluke3000 to perform a one time measurement.

        :param mode: Desired measurement mode.

        :type mode: `Fluke3000.Mode`

        :return: A measurement from the multimeter.
        :rtype: `~pint.Quantity`

        """
        # Check that the mode is supported
        if not isinstance(mode, self.Mode):
            raise ValueError(f"Mode {mode} is not supported")

        # Check that the module associated with this mode is available
        module = self._get_module(mode)
        if module not in self.positions:
            raise ValueError(f"Device necessary to measure {mode} is not available")

        # Query the module
        value = ""
        port_id = self.positions[module]
        init_time = time.time()
        while time.time() - init_time < 3.0:
            # Read out
            if mode == self.Mode.temperature:
                # The temperature module supports single readout
                value = self.query_lines(f"rfemd 0{port_id} 0", 2)[-1]
            else:
                # The multimeter does not support single readout,
                # have to open continuous readout, read, then close it
                value = self.query_lines(f"rfemd 0{port_id} 1", 2)[-1]
                self.query(f"rfemd 0{port_id} 2")

            # Check that value is consistent with the request, break
            if "PH" in value:
                data = value.split("PH=")[-1]
                if self._parse_mode(data) != mode.value:
                    if self.Module.m3000 in self.positions.keys():
                        self.query(f"rfemd 0{self.positions[self.Module.m3000]} 2")
                    self.flush()
                else:
                    break

        # Parse the output
        value = self._parse(value, mode)

        # Return with the appropriate units
        units = UNITS[mode]
        return u.Quantity(value, units)

    def _get_module(self, mode):
        """Gets the module associated with this measurement mode.

        :param mode: Desired measurement mode.

        :type mode: `Fluke3000.Mode`

        :return: A Fluke3000 module.
        :rtype: `Fluke3000.Module`

        """
        if mode == self.Mode.temperature:
            return self.Module.t3000

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
            raise ValueError(
                "Cannot parse a string that does not contain a return value"
            )

        # Isolate the data string from the output
        data = result.split("PH=")[-1]

        # Check that the multimeter is in the right mode (fifth byte)
        if self._parse_mode(data) != mode.value:
            error = (
                f"Mode {mode.name} was requested but the Fluke 3000FC Multimeter is in "
                f"mode {self.Mode(data[8:10]).name} instead. Could not read the requested quantity."
            )
            raise ValueError(error)

        # Extract the value from the first two bytes
        value = self._parse_value(data)

        # Extract the prefactor from the fourth byte
        scale = self._parse_factor(data)

        # Combine and return
        return scale * value

    @staticmethod
    def _parse_mode(data):
        """Parses the measurement mode.

        :param data: Measurement output.

        :type data: `str`

        :return: A Mode string.
        :rtype: `str`

        """
        # The fixth dual hex byte encodes the measurement mode
        return data[8:10]

    @staticmethod
    def _parse_value(data):
        """Parses the measurement value.

        :param data: Measurement output.

        :type data: `str`

        :return: A value.
        :rtype: `float`

        """
        # The second dual hex byte is the most significant byte
        return int(data[2:4] + data[:2], 16)

    @staticmethod
    def _parse_factor(data):
        """Parses the measurement prefactor.

        :param data: Measurement output.

        :type data: `str`

        :return: A prefactor.
        :rtype: `float`

        """
        # Convert the fourth dual hex byte to an 8 bits string
        byte = format(int(data[6:8], 16), "08b")

        # The first bit encodes the sign (0 positive, 1 negative)
        sign = 1 if byte[0] == "0" else -1

        # The second to fourth bits encode the metric prefix
        code = int(byte[1:4], 2)
        if code not in PREFIXES:
            raise ValueError(f"Metric prefix not recognized: {code}")
        prefix = PREFIXES[code]

        # The sixth and seventh bit encode the decimal place
        scale = 10 ** (-int(byte[5:7], 2))

        # Return the combination
        return sign * prefix * scale


# UNITS #######################################################################

UNITS = {
    None: 1,
    Fluke3000.Mode.voltage_ac: u.volt,
    Fluke3000.Mode.voltage_dc: u.volt,
    Fluke3000.Mode.current_ac: u.amp,
    Fluke3000.Mode.current_dc: u.amp,
    Fluke3000.Mode.frequency: u.hertz,
    Fluke3000.Mode.temperature: u.degC,
    Fluke3000.Mode.resistance: u.ohm,
    Fluke3000.Mode.capacitance: u.farad,
}

# METRIC PREFIXES #############################################################

PREFIXES = {
    0: 1e0,  # None
    2: 1e6,  # Mega
    3: 1e3,  # Kilo
    4: 1e-3,  # milli
    5: 1e-6,  # micro
    6: 1e-9,  # nano
}
