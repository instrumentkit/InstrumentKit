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
        self.timeout = 1 * pq.second
        self.terminator = "\r"
        self._null = False
        self.positions = {}
        self.connect()

    # ENUMS ##
    
    class Module(Enum):

        """
        Enum containing the supported module codes
        """
        #: Temperature module
        t3000 = "t3000"
    
    class Mode(Enum):

        """
        Enum containing the supported mode codes
        """
        #: Temperature
        temperature = "rfemd"
        
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
        self.scan()
        if not self.positions:
            self.reset()                # Resets the PC3000 dongle
            self.query("rfdis")         # Discovers connected modules
            time.sleep(10)              # Wait for modules to connect
            self.scan()
            
        if not self.positions:
            raise ValueError("No Fluke3000 modules available")  
            
    def reset(self):
        """
        Resets the device and unbinds all modules
        """
        self.query("ri") # Resets the device
        self.query("rfsm 1") # Turns comms on
                
    def scan(self):
        """
        Search for available modules and returns
        a dictionary of the modules found and their location
        """
        # Loop over possible channels, store device locations
        positions = {}
        for port_id in range(1, 7):
            # Check if a device is connected to port port_id
            output = self.query("rfebd 0{} 1".format(port_id))
            if "PH" not in output:
                break
            
            # If it is, identify the device
            module_id = int(output.split("PH=")[-1])
            if module_id == 64:
                positions[self.Module.t3000] = port_id
            else:
                error = "Module ID {} not implemented".format(module_id)
                raise NotImplementedError(error)
                
        self.positions = positions
        
    def query(self, cmd):
        """
        Function used to send a command to the instrument while allowing
        for multiline output (multiple termination characters)

        :param str cmd: Command that will be sent to the instrument
        :return: The result from the query
        :rtype: `str`
        """
        # First send the command
        self.sendcmd(cmd)
        time.sleep(0.1)
    
        # While there is something to readout, keep going
        result = ""
        while True:
            try:
                result += self.read()
            except:
                break
            
        return result      

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
        module = self._get_module(mode)
        if module not in self.positions.keys():
            raise ValueError("Device necessary to measure {} is not available".format(mode))

        port_id = self.positions[module]
        value = None
        init_time = time.time()
        while not value and time.time() - init_time < float(self.timeout):
            value = self.query("{} 0{} 0".format(mode.value, port_id))
            value = self._parse(value, mode)

        if not value:
            raise ValueError("Failed to read out Fluke3000 with mode {}".format(mode))

        units = UNITS[mode]
        return value * units
        
    def _parse(self, result, mode):
        """Parses the module output depending on the measurement made

        :param result: Output of the query. 
        :param mode: Desired measurement mode. 
      
        :type result: `string`  
        :type mode: `Fluke3000.Mode`

        :return: A measurement from the multimeter.
        :rtype: `float`

        """
        # Loop over possible channels, store device locations
        value = None
        if mode == self.Mode.temperature:
            if "PH" not in result:
                return value
        
            data = result.split('PH=')[-1]
            least = int(data[:2], 16)
            most = int(data[2:4], 16)
            sign = 1 if data[6:8] == '02' else -1
            return sign*float(most*255+least)/10        
        else:
            raise NotImplementedError("Mode {} not implemented".format(mode))

        return value

    def _get_module(self, mode):
        if mode == self.Mode.temperature:
            return self.Module.t3000
        else:
            raise ValueError("No module associated with mode {}".format(mode))
        
# UNITS #######################################################################

UNITS = {
    None: 1,
    Fluke3000.Mode.temperature: pq.celsius
}
