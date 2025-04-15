#!/usr/bin/env python
"""
Driver for the Pfeiffer TPG36x vacumm gauge controller.
"""

# IMPORTS #####################################################################

from enum import Enum

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
        >>> import instruments as ik
        >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
        >>> ch = inst.channel[0]
        >>> ch.pressure
        0.02 * u.mbar
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

        STATIC = 0
        DHCP = 1

    class Language(Enum):
        """Enum to get/set the language of the device."""

        ENGLISH = 0
        GERMAN = 1
        FRENCH = 2

    class Unit(Enum):
        """Enum for the pressure units."""

        MBAR = 0
        TORR = 1
        PASCAL = 2
        MICRON = 3
        HPASCAL = 4
        VOLT = 5

    class Channel:
        """
        Class representing a sensor attached to the TPG 362.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TPG36x` class.
        """

        class SensorStatus(Enum):
            """Enum to get the status of the sensor."""

            CANNOT_TURN_ON_OFF = 0
            OFF = 1
            ON = 2

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

            Example:
                >>> import instruments as ik
                >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
                >>> ch = inst.channel[0]
                >>> ch.pressure
                0.02 * u.mbar
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

            if status != 0:
                raise OSError(status_msgs.get(status, "Unknown error"))

            current_unit = self._parent.unit

            return val * u.Quantity(current_unit.name.lower())

        @property
        def status(self):
            """
            Get/set the status of a channel (sensor).

            :return: The status of the sensor.
            :rtype: `TPG36x.Channel.SensorStatus`

            Example:
                >>> import instruments as ik
                >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
                >>> ch = inst.channel[0]
                >>> ch.status
                SensorStatus.ON
            """
            val = self._parent.query("SEN")
            val = int(val.split(",")[self._chan])
            return self.SensorStatus(val)

        @status.setter
        def status(self, value):
            if not isinstance(value, self.SensorStatus):
                raise ValueError("The status must be a SensorStatus enum.")
            if value == self.SensorStatus.CANNOT_TURN_ON_OFF:
                raise ValueError("You cannot set the status to this value.")
            status_to_send = [0 for _ in range(self._parent.number_channels)]
            status_to_send[self._chan] = value.value
            status_to_send_str = ",".join([str(x) for x in status_to_send])
            self._parent.sendcmd(f"SEN,{status_to_send_str}")

    @property
    def channel(self):
        """
        Gets a specific channel object.

        Note that the channel number is pythonic, i.e., the first channel is 0.

        :rtype: `TPG36x.Channel`

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> ch = inst.channel[0]
        """
        return ProxyList(self, self.Channel, range(self._number_channels))

    @property
    def ethernet_configuration(self):
        """
        Get / set the ethernet configuration of the TPG36x.

        .. note:: If you set the configuration to DHCP, you can simply send
            `TPG36x.EthernetMode.DHCP` as the sole value. To set it to static,
            you must provide a list of 4 elements: `[EthernetMode, IP, Subnet, Gateway]`.
            The types are as follows: `TPG36x.EthernetMode`, `str`, `str`, `str`.

        :return: List of the current configuration:
            0. Configuration enum `TPG36x.EthernetMode`
            1. IP address as string
            2. Subnet mask as string
            3. Gateway as string

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.ethernet_configuration = [inst.EthernetMode.STATIC, "192.168.1.42", "255.255.255.0", "192.168.1.1"]
           >>> inst.ethernet_configuration
            [inst.EthernetMode.STATIC, "192.168.1.42", "255.255.255.0", "192.168.1.1"]
        """
        return_list = self.query("ETH").split(",")
        return_list[0] = self.EthernetMode(int(return_list[0]))
        return return_list

    @ethernet_configuration.setter
    def ethernet_configuration(self, value):
        if not isinstance(value, list) or len(value) != 4:  # check for correct format
            if value == self.EthernetMode.DHCP:  # DHCP is a special case
                value = [self.EthernetMode.DHCP, "0.0.0.0", "0.0.0.0", "0.0.0.0"]
            else:
                raise ValueError(
                    "The ethernet configuration must be a list of 4 elements."
                )
        if not isinstance(value[0], self.EthernetMode):  # check for correct type
            raise ValueError("The first element must be an EthernetMode.")

        for addr in value[1:]:
            try:
                addr = addr.split(".")
                if len(addr) != 4:
                    raise ValueError(
                        f"Address {addr} must have 4 parts, not {len(addr)}"
                    )
                for part in addr:
                    if not 0 <= int(part) <= 255:
                        raise ValueError(
                            f"Each part of the address {addr} must be between 0 and 255."
                        )
            except (ValueError, AttributeError):
                raise ValueError(
                    f"The address {addr} must be a string of 4 numbers separated by dots."
                )
        self.sendcmd(f"ETH,{value[0].value},{value[1]},{value[2]},{value[3]}")

    @property
    def language(self):
        """
        Get/set the language of the TPG36x.

        :rtype: `TPG36x.Language`

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.language
            Language.ENGLISH
        """
        val = int(self.query("LNG"))
        return self.Language(val)

    @language.setter
    def language(self, value):
        self.sendcmd(f"LNG,{value.value}")

    @property
    def mac_address(self):
        """
        Get the MAC address of the TPG36x.

        :return: MAC address of the TPG36x.
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.mac_address
            "00:1A:2B:3C:4D:5E"
        """
        return self.query("MAC")

    @property
    def name(self):
        """
        Get the name from the TPG36x.

        :rtype: str

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.name
            "TPG 362"
        """
        return self.query("AYT").split(",")[0]

    @property
    def number_channels(self):
        """
        The number of channels on the TPG36x.

        This defaults to two channels. Set this to 1 if you have a one gauge
        instrument, i.e., a TPG361.

        :rtype: int

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.number_channels
            2
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

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.pressure
            0.02 * u.mbar
        """
        return self.channel[0].pressure

    @property
    def unit(self):
        """
        Get/set the unit of the TPG36x (global to the instrument).

        :return: The current unit.
        :rtype: `TPG36x.Unit`

        Example:
            >>> import instruments as ik
            >>> inst = ik.pfeiffer.TPG36x.open_serial("/dev/ttyUSB0", 9600)
            >>> inst.unit
            Unit.MBAR
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
