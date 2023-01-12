#!/usr/bin/env python
"""
Provides support for the Mettler Toledo balances via Standard Interface Command Set.
"""

from enum import IntEnum, Enum

from instruments.units import ureg as u

from instruments.abstract_instruments import Instrument


class MTSICS(Instrument):
    """
    Instrument class to communicate with Mettler Toledo balances using the MT-SICS
    Standared Interface Command Set.

    Example usage:
    >>> import instruments as ik
    >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
    >>> inst.weight_stable
    <Quantity(120.2, 'gram')>
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        self.terminator = "\r\n"

    def query(self, cmd, size=-1):
        """
        Query the instrument for a response.

        :param str cmd: The command to send to the instrument.
        :param int size: Number of bytes to read from the instrument.

        :return: The response from the instrument.
        :rtype: str

        :raises: IOError
            Command understood but cannot be executed at the moment.
        :raises: IOError
            Balance in over- or underrange mode.
        """
        self.sendcmd(cmd)

        rval = self.read(size)
        rval = rval.split()
        if rval[1] == "I":
            raise OSError("Command understood but cannot be executed at the moment.")
        elif rval[1] == "+":
            raise OSError("Balance in overrange mode.")
        elif rval[1] == "-":
            raise OSError("Balance in underrange mode.")
        return rval[1:]

    def reset(self):
        """
        Reset the balance.
        """
        self.sendcmd("@")

    def zero(self):
        """
        Zero the balance.
        """
        self.sendcmd("Z")

    def zero_immediately(self):
        """
        Zero the balance immediately.
        """
        self.sendcmd("ZI")

    @property
    def mt_sics(self):
        """
        Get MT-SICS level and MT-SICS versions.

        :return: Level, Version Level 0, Version Level 1, Version Level 2, Version Level 3
        """
        retval = [it.replace('"', "") for it in self.query("I1")[1:]]
        return retval

    @property
    def serial_number(self):
        """
        Get the serial number of the balance.

        :return: The serial number of the balance.
        :rtype: str
        """
        return self.query("I4")[1].replace('"', "")

    @property
    def weight(self):
        """
        Get the stable weight.

        :return: Stable weight
        :rtype: u.Quantity
        """
        retval = self.query("S")
        return u.Quantity(float(retval[1]), retval[2])

    @property
    def weight_immediately(self):
        """
        Get the weight immediately, irrespective of balance stability.

        :return: Immediate weight
        :rtype: u.Quantity
        """
        retval = self.query("SI")
        return u.Quantity(float(retval[1]), retval[2])
