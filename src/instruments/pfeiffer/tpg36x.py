#!/usr/bin/env python
"""
Driver for the Pfeiffer TPG36x vacumm gauge controller.
"""

# IMPORTS #####################################################################

from enum import Enum, IntEnum

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class TPG36x(Instrument):
    """
    The Pfeiffer TPG361/2 is a vacuum gauge controller with one/two channels.

    By default, the two channel version is intialized. If you have the one channel
    version (TPG361), set the `number_channels` property to 1.

    Example usage:

        TODO:

    """

    def __init__(self, filelike):
        super().__init__(filelike)

        self._number_channels = 2

        self._defined_cmd = {
            "ETX": 3,
            "ENQ": 5,
            "ACK": 6,
            "NAK": 21,
        }

        self.terminator = "\r\n"

    class EthernetMode(Enum):
        """Enum go get/set the ethernet mode of the device when configuring."""

        DHCP = 0
        STATIC = 1

    class Language(Enum):
        """Enum to get/set the language of the device."""

        ENGLISH = 0
        GERMAN = 1
        FRENCH = 2

    class Unit(Enum):
        """Enum for the pressure units (example)."""

        MBAR = 0
        TORR = 1
        PASCAL = 2

    class Channel:
        """
        Class representing a sensor attached to the TPG 362.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TPG36x` class.
        """

        def __init__(self, parent, chan):
            if not isinstance(parent, TPG36x):
                raise TypeError("Don't do that.")
            self._chan = chan
            self._parent = parent

        @property
        def pressure(self):
            """
            The pressure measured by the channel, returned as a pint.Quantity
            with the correct units attached (based on instrument settings).

            This routine also does error checking on the pressure reading and raises
            an IOError with adequate message if, e.g., no sensor is connected to the
            channel.

            :return: Pressure on given channel.
            :rtype: `u.Quantity`
            """
            status_msgs = {
                0: "OK",
                1: "Underrange",
                2: "Overrange",
                3: "Sensor error",
                4: "Sensor off",
                5: "No sensor",
                6: "Identification error",
            }

            raw_str = self._parent.query(f"PR{self._chan + 1}")  # ex: "0,+1.7377E+00"
            status_str, val_str = raw_str.split(",")
            status = int(status_str)
            val = float(val_str)
            current_unit = self._parent.unit

            if status != 0:
                raise OSError(status_msgs.get(status, "Unknown error"))

            return val * u.Quantity(current_unit.name.lower())

    @property
    def channel(self):
        """
        Gets a specific channel object.

        Note that the channel number is pythonic, i.e., the first channel is 0.

        :rtype: `TPG36x.Channel`
        """
        return ProxyList(self, self.Channel, range(self._number_channels))

    @property
    def ethernet_configuration(self):
        """
        Get / set the ethernet configuration of the TPG36x.

        :return: List of the current configuration:
            0. Configuration enum `TPG36x.EthernetMode`
            1. IP address as string
            2. Subnet mask as string
            3. Gateway as string
        """
        return_list = self.query("ETH").split(",")
        return_list[0] = self.EthernetMode(int(return_list[0]))
        return return_list

    @ethernet_configuration.setter
    def ethernet_configuration(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise ValueError("The ethernet configuration must be a list of 4 elements.")
        if not isinstance(value[0], self.EthernetMode):
            raise ValueError("The first element must be an EthernetMode.")
        self.sendcmd(f"ETH,{value[0].value},{value[1]},{value[2]},{value[3]}")

    @property
    def language(self):
        """
        Get the language of the TPG36x.

        :rtype: `TPG36x.Language`
        """
        val = int(self.query("LNG"))
        return self.Language(val)

    @language.setter
    def language(self, value):
        """
        Set the language of the TPG36x.

        :param value: The language to set.
        :type value: `TPG36x.Language`
        """
        self.sendcmd(f"LNG,{value.value}")

    @property
    def mac_address(self):
        """
        Get the MAC address of the TPG36x.

        :return: MAC address of the TPG36x.
        :rtype: str
        """
        return self.query("MAC")

    @property
    def name(self):
        """
        Get the name from the TPG36x.

        :rtype: str
        """
        return self.query("AYT").split(",")[0]

    @property
    def number_channels(self):
        """
        The number of channels on the TPG36x.

        :rtype: int
        """
        return self._number_channels

    @number_channels.setter
    def number_channels(self, value):
        if value not in (1, 2):
            raise ValueError("The TPG36x only supports 1 or 2 channels.")
        self._number_channels = value

    @property
    def pressure(self):
        """
        The pressure measured by the first channel.

        To select the channel, get a channel first and then call the pressure
        method on it.

        :rtype: `pint.Quantity`
        """
        return self.channel[0].pressure

    @property
    def unit(self):
        """
        Get or set the unit of the TPG36x (global to the instrument).

        :return: The current unit.
        :rtype: `TPG36x.Unit`
        """
        val = self.query("UNI")
        val = int(val)
        return self.Unit(val)

    @unit.setter
    def unit(self, new_unit):
        if isinstance(new_unit, str):
            new_unit = self.Unit[new_unit.upper()]
        cmd_val = new_unit.value
        self.sendcmd(f"UNI,{cmd_val}")

    def query(self, cmd):
        """
        Query the TPG36x with the enquire command.

        :return: The response from the TPG36x.
        """
        self.sendcmd(cmd)
        self.write(chr(self._defined_cmd["ENQ"]))
        return self.read()

    def _ack_expected(self, msg=""):
        return [chr(self._defined_cmd["ACK"])]
