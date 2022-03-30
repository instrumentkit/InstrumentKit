#!/usr/bin/env python
#
# hpe3631a.py: Driver for the Glassman FR Series Power Supplies
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
Driver for the Glassman FR Series Power Supplies

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""
# IMPORTS #####################################################################

from struct import unpack
from enum import Enum

from instruments.abstract_instruments import PowerSupply
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class GlassmanFR(PowerSupply, PowerSupply.Channel):

    """
    The GlassmanFR is a single output power supply.

    Because it is a single channel output, this object inherits from both
    PowerSupply and PowerSupply.Channel.

    This class should work for any of the Glassman FR Series power supplies
    and is also likely to work for the EJ, ET, EY and FJ Series which seem
    to share their communication protocols. The code has only been tested
    by the author with an Glassman FR50R6 power supply.

    Before this power supply can be remotely operated, remote communication
    must be enabled and the HV must be on. Please refer to the manual.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.glassman.GlassmanFR.open_serial('/dev/ttyUSB0', 9600)
    >>> psu.voltage = 100 # Sets output voltage to 100V.
    >>> psu.voltage
    array(100.0) * V
    >>> psu.output = True # Turns on the power supply
    >>> psu.voltage_sense < 200 * u.volt
    True

    This code uses default values of `voltage_max`, `current_max` and
    `polarity` that are only valid of the FR50R6 in its positive setting.
    If your power supply differs, reset those values by calling:

    >>> import instruments.units as u
    >>> psu.voltage_max = 40.0 * u.kilovolt
    >>> psu.current_max = 7.5 * u.milliamp
    >>> psu.polarity = -1
    """

    def __init__(self, filelike):
        """
        Initialize the instrument, and set the properties needed for communication.
        """
        super().__init__(filelike)
        self.terminator = "\r"
        self.voltage_max = 50.0 * u.kilovolt
        self.current_max = 6.0 * u.milliamp
        self.polarity = +1
        self._device_timeout = False
        self._voltage = 0.0 * u.volt
        self._current = 0.0 * u.amp

    # ENUMS ##

    class Mode(Enum):
        """
        Enum containing the possible modes of operations of the instrument
        """

        #: Constant voltage mode
        voltage = "0"
        #: Constant current mode
        current = "1"

    class ResponseCode(Enum):
        """
        Enum containing the possible reponse codes returned by the instrument.
        """

        #: A set command expects an acknowledge response (`A`)
        S = "A"
        #: A query command expects a response packet (`R`)
        Q = "R"
        #: A version query expects a different response packet (`B`)
        V = "B"
        #: A configure command expects an acknowledge response (`A`)
        C = "A"

    class ErrorCode(Enum):
        """
        Enum containing the possible error codes returned by the instrument.
        """

        #: Undefined command received (not S, Q, V or C)
        undefined_command = "1"
        #: The checksum calculated by the instrument does not correspond to the one received
        checksum_error = "2"
        #: The command was longer than expected
        extra_bytes = "3"
        #: The digital control byte set was not one of HV On, HV Off or Power supply Reset
        illegal_control = "4"
        #: A send command was sent without a reset byte while the power supply is faulted
        illegal_while_fault = "5"
        #: Command valid, error while executing it
        processing_error = "6"

    # PROPERTIES ##

    @property
    def channel(self):
        """
        Return the channel (which in this case is the entire instrument, since
        there is only 1 channel on the GlassmanFR.)

        :rtype: 'tuple' of length 1 containing a reference back to the parent
            GlassmanFR object.
        """
        return [self]

    @property
    def voltage(self):
        """
        Gets/sets the output voltage setting.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """
        return self.polarity * self._voltage

    @voltage.setter
    def voltage(self, newval):
        self.set_status(voltage=assume_units(newval, u.volt))

    @property
    def current(self):
        """
        Gets/sets the output current setting.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~pint.Quantity`
        """
        return self.polarity * self._current

    @current.setter
    def current(self, newval):
        self.set_status(current=assume_units(newval, u.amp))

    @property
    def voltage_sense(self):
        """
        Gets the output voltage as measured by the sense wires.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `~pint.Quantity`
        """
        return self.get_status()["voltage"]

    @property
    def current_sense(self):
        """
        Gets/sets the output current as measured by the sense wires.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `~pint.Quantity`
        """
        return self.get_status()["current"]

    @property
    def mode(self):
        """
        Gets/sets the mode for the specified channel.

        The constant-voltage/constant-current modes of the power supply
        are selected automatically depending on the load (resistance)
        connected to the power supply. If the load greater than the set
        V/I is connected, a voltage V is applied and the current flowing
        is lower than I. If the load is smaller than V/I, the set current
        I acts as a current limiter and the voltage is lower than V.

        :type: `GlassmanFR.Mode`
        """
        return self.get_status()["mode"]

    @property
    def output(self):
        """
        Gets/sets the output status.

        This is a toggle setting. True will turn on the instrument output
        while False will turn it off.

        :type: `bool`
        """
        return self.get_status()["output"]

    @output.setter
    def output(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Output status mode must be a boolean.")
        self.set_status(output=newval)

    @property
    def fault(self):
        """
        Gets the output status.

        Returns True if the instrument has a fault.

        :type: `bool`
        """
        return self.get_status()["fault"]

    @property
    def version(self):
        """
        The software revision level of the power supply's
        data intereface via the `V` command

        :rtype: `str`
        """
        return self.query("V")

    @property
    def device_timeout(self):
        """
        Gets/sets the timeout instrument side.

        This is a toggle setting. ON will set the timeout to 1.5
        seconds while OFF will disable it.

        :type: `bool`
        """
        return self._device_timeout

    @device_timeout.setter
    def device_timeout(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Device timeout mode must be a boolean.")
        self.query(f"C{int(not newval)}")  # Device acknowledges
        self._device_timeout = newval

    # METHODS ##

    def sendcmd(self, cmd):
        """
        Overrides the default `setcmd` by padding the front of each
        command sent to the instrument with an SOH character and the
        back of it with a checksum.

        :param str cmd: The command message to send to the instrument
        """
        checksum = self._get_checksum(cmd)
        self._file.sendcmd("\x01" + cmd + checksum)  # Add SOH and checksum

    def query(self, cmd, size=-1):
        """
        Overrides the default `query` by padding the front of each
        command sent to the instrument with an SOH character and the
        back of it with a checksum.

        This implementation also automatically check that the checksum
        returned by the instrument is consistent with the message. If
        the message returned is an error, it parses it and raises.

        :param str cmd: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(cmd)
        result = self._file.read(size)
        if result[0] != getattr(self.ResponseCode, cmd[0]).value and result[0] != "E":
            raise ValueError(f"Invalid response code: {result}")
        if result[0] == "A":
            return "Acknowledged"
        if not self._verify_checksum(result):
            raise ValueError(f"Invalid checksum: {result}")
        if result[0] == "E":
            error_name = self.ErrorCode(result[1]).name
            raise ValueError(f"Instrument responded with error: {error_name}")

        return result[1:-2]  # Remove SOH and checksum

    def reset(self):
        """
        Reset device to default status (HV Off, V=0.0, A=0.0)
        """
        self.set_status(reset=True)

    def set_status(self, voltage=None, current=None, output=None, reset=False):
        """
        Sets the requested variables on the instrument.

        This instrument can only set all of its variables simultaneously,
        if some of them are omitted in this function, they will simply be
        kept as what they were set to previously.
        """
        if reset:
            self._voltage = 0.0 * u.volt
            self._current = 0.0 * u.amp
            cmd = format(4, "013d")
        else:
            # The maximum value is encoded as the maximum of three hex characters (4095)
            cmd = ""
            value_max = int(0xFFF)

            # If the voltage is not specified, keep it as is
            voltage = (
                assume_units(voltage, u.volt) if voltage is not None else self.voltage
            )
            ratio = float(voltage.to(u.volt) / self.voltage_max.to(u.volt))
            voltage_int = int(round(value_max * ratio))
            self._voltage = self.voltage_max * float(voltage_int) / value_max
            assert 0.0 * u.volt <= self._voltage <= self.voltage_max
            cmd += format(voltage_int, "03X")

            # If the current is not specified, keep it as is
            current = (
                assume_units(current, u.amp) if current is not None else self.current
            )
            ratio = float(current.to(u.amp) / self.current_max.to(u.amp))
            current_int = int(round(value_max * ratio))
            self._current = self.current_max * float(current_int) / value_max
            assert 0.0 * u.amp <= self._current <= self.current_max
            cmd += format(current_int, "03X")

            # If the output status is not specified, keep it as is
            output = output if output is not None else self.output
            control = f"00{int(output)}{int(not output)}"
            cmd += format(int(control, 2), "07X")

        self.query("S" + cmd)  # Device acknowledges

    def get_status(self):
        """
        Gets and parses the response packet.

        Returns a `dict` with the following keys:
        ``{voltage,current,mode,fault,output}``

        :rtype: `dict`
        """
        return self._parse_response(self.query("Q"))

    def _parse_response(self, response):
        """
        Parse the response packet returned by the power supply.

        Returns a `dict` with the following keys:
        ``{voltage,current,mode,fault,output}``

        :param response: Byte string to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        (voltage, current, monitors) = unpack("@3s3s3x1c2x", bytes(response, "utf-8"))

        try:
            voltage = self._parse_voltage(voltage)
            current = self._parse_current(current)
            mode, fault, output = self._parse_monitors(monitors)
        except:
            raise RuntimeError("Cannot parse response " "packet: {}".format(response))

        return {
            "voltage": voltage,
            "current": current,
            "mode": mode,
            "fault": fault,
            "output": output,
        }

    def _parse_voltage(self, word):
        """
        Converts the three-bytes voltage word returned in the
        response packet to a single voltage quantity.

        :param word: Byte string to be parsed
        :type: `bytes`

        :rtype: `~pint.Quantity`
        """
        value = int(word.decode("utf-8"), 16)
        value_max = int(0x3FF)
        return self.polarity * self.voltage_max * float(value) / value_max

    def _parse_current(self, word):
        """
        Converts the three-bytes current word returned in the
        response packet to a single current quantity.

        :param word: Byte string to be parsed
        :type: `bytes`

        :rtype: `~pint.Quantity`
        """
        value = int(word.decode("utf-8"), 16)
        value_max = int(0x3FF)
        return self.polarity * self.current_max * float(value) / value_max

    def _parse_monitors(self, word):
        """
        Converts the monitors byte returned in the response packet
        to a mode, a fault boolean and an output boolean.

        :param word: Byte to be parsed
        :type: `byte`

        :rtype: `str, bool, bool`
        """
        bits = format(int(word, 16), "04b")
        mode = self.Mode(bits[-1])
        fault = bits[-2] == "1"
        output = bits[-3] == "1"
        return mode, fault, output

    def _verify_checksum(self, word):
        """
        Calculates the modulo 256 checksum of a string of characters
        and compares it to the one returned by the instrument.

        Returns True if they agree, False otherwise.

        :param word: Byte string to be checked
        :type: `str`

        :rtype: `bool`
        """
        data = word[1:-2]
        inst_checksum = word[-2:]
        calc_checksum = self._get_checksum(data)
        return inst_checksum == calc_checksum

    @staticmethod
    def _get_checksum(data):
        """
        Calculates the modulo 256 checksum of a string of characters.
        This checksum, expressed in hexadecimal, is used in every
        communication of this instrument, as a sanity check.

        Returns a string corresponding to the hexademical value
        of the checksum, without the `0x` prefix.

        :param data: Byte string to be checksummed
        :type: `str`

        :rtype: `str`
        """
        chrs = list(data)
        total = 0
        for c in chrs:
            total += ord(c)

        return format(total % 256, "02X")
