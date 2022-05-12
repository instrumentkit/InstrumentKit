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

    def __init__(self, *args, **kwargs):
        """
        The TC038 is a crystal oven.

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
            Command to be sent, three chars. The default is "WRM".
        commandData : string, optional
            Additional data for the command. The default is "".
        """
        super().sendcmd(chr(2) + f"{self.addr:02}" + "010"
                        + command + chr(3))
        # 010 is CPU (01) and time to wait (0), which are fix

    def query(self, command):
        """
        Send a command to the oven and read its response.

        Parameters
        ----------
        command : string, optional
            Command to be sent, three chars. The default is "WRM".
        commandData : string, optional
            Additional data for the command. The default is "".

        Returns
        -------
        string
            response of the system.

        """
        return super().query(chr(2) + f"{self.addr:02}" + "010"
                             + command + chr(3))

    def monitorTemperature(self):
        """Configure the oven to monitor the current temperature."""
        self.query(command="WRS" + "01" + "D0002")
        # WRS in order to setup to monitor a word
        # monitor 1 word
        # monitor the word in register D0002

    @property
    def setpoint(self):
        """Read and return the current setpoint in °C."""
        got = self.query(command="WRD" + "D0120" + ",01")
        # WRD: read words
        # start with register D0003
        # read a single word, separated by space or comma
        return self.dataToTemp(got)

    @property
    def temperature(self):
        """Read and return the current temperature in °C."""
        got = self.query(command="WRD" + "D0002" + ",01")
        return self.dataToTemp(got)

    def getMonitored(self):
        """Read and return the monitored value.
        Normally it's the current temperature in °C."""
        # returns the monitored words
        got = self.query(command="WRM")
        return self.dataToTemp(got)

    @setpoint.setter
    def setpoint(self, value):
        """Set the setpoint to a temperature in °C."""
        number = assume_units(value, u.degC).to(u.degC).magnitude
        commandData = f"D0120,01,{int(round(number * 10)):04X}"
        # Temperature without decimal sign in hex representation
        got = self.query(command="WWR" + commandData)
        return got[5:7]

    def dataToTemp(self, data):
        """Convert the returned hex value "data" to a temperature in °C."""
        return u.Quantity(int(data[7:11], 16) / 10, u.degC)
        # get the hex number, convert to int and shift the decimal sign
