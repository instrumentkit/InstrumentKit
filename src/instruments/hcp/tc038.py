#!/usr/bin/env python
"""
Provides support for the TC038 AC crystal oven by HC Photonics.
"""


# IMPORTS #####################################################################


from instruments.units import ureg as u

from instruments.abstract_instruments.instrument import Instrument
from instruments.util_fns import assume_units

import serial

# CLASSES #####################################################################


class TC038(Instrument):
    """
    Communication with the HCP TC038 oven.

    This is the older version with an AC power supply and AC heater.

    It has parity or framing errors from time to time. Handle them in your
    application.
    """

    registers = {'temperature': "D0002",
                 'setpoint': "D0120",
                 }

    def __init__(self, *args, **kwargs):
        """
        Initialize the TC038 is a crystal oven.

        Example usage:

        >>> import instruments as ik
        >>> import instruments.units as u
        >>> inst = ik.hcp.TC038.open_visa('TCPIP0:192.168.0.35')
        >>> inst.setpoint = 45.3
        >>> print(inst.temperature)
        """
        super().__init__(*args, **kwargs)
        self.addr = 1

    @classmethod
    def open_serial(cls, *args, **kwargs):
        """Configure the serial connection."""
        inst = super().open_serial(*args, **kwargs)
        inst._file._conn.parity = serial.PARITY_EVEN
        inst._file._terminator = "\r"
        return inst

    def sendcmd(self, command):
        """
        Send "command" to the oven with "commandData".

        Parameters
        ----------
        command : string, optional
            Command to be sent. Three chars indicating the type, and data for
            the command, if necessary.
        """
        # 010 is CPU (01) and time to wait (0), which are fix
        super().sendcmd(chr(2) + f"{self.addr:02}" + "010"
                        + command + chr(3))

    def query(self, command):
        """
        Send a command to the oven and read its response.

        Parameters
        ----------
        command : string, optional
            Command to be sent. Three chars indicating the type, and data for
            the command, if necessary.

        Returns
        -------
        string
            response of the system.
        """
        return super().query(chr(2) + f"{self.addr:02}" + "010"
                             + command + chr(3))

    def set_monitored_quantity(self, quantity='temperature'):
        """
        Configure the oven to monitor a certain `quantity`.

        `quantity` may be any key of `registers`. Default is the current
        temperature in °C.
        """
        # WRS in order to setup to monitor a word
        # monitor 1 to 16 words
        # monitor the word in the given register
        # Additional registers are added with a separating space or comma.
        self.query(command="WRS" + "01" + self.registers[quantity])

    @property
    def setpoint(self):
        """Read and return the current setpoint in °C."""
        got = self.query(command="WRD" + "D0120" + ",01")
        # WRD: read words
        # start with register D0003
        # read a single word, separated by space or comma
        return self._data_to_temp(got)

    @setpoint.setter
    def setpoint(self, value):
        """Set the setpoint to a temperature in °C."""
        number = assume_units(value, u.degC).to(u.degC).magnitude
        commandData = f"D0120,01,{int(round(number * 10)):04X}"
        # Temperature without decimal sign in hex representation
        got = self.query(command="WWR" + commandData)
        assert got[5:7] == "OK", "A communication error occurred."

    @property
    def temperature(self):
        """Read and return the current temperature in °C."""
        got = self.query(command="WRD" + "D0002" + ",01")
        return self._data_to_temp(got)

    @property
    def monitored_value(self):
        """
        Read and return the monitored value.

        Per default it's the current temperature in °C.
        """
        # returns the monitored words
        got = self.query(command="WRM")
        return self._data_to_temp(got)

    @property
    def information(self):
        """Read the device information."""
        # TODO laut Manual INF6
        return self.query("INF")[7:-1]

    @staticmethod
    def _data_to_temp(data):
        """Convert the returned hex value "data" to a temperature in °C."""
        return u.Quantity(int(data[7:11], 16) / 10, u.degC)
        # get the hex number, convert to int and shift the decimal sign
