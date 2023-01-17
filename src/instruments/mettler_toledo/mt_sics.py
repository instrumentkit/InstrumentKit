#!/usr/bin/env python
"""
Provides support for the Mettler Toledo balances via Standard Interface Command Set.
"""

import warnings

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units


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

    def clear_tare(self):
        """
        Clear the tare value.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.clear_tare()
        """
        _ = self.query("TAC")

    def reset(self):
        """
        Reset the balance.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.reset()
        """
        _ = self.query("@")

    def tare(self):
        """
        Tare the balance after stable weight is obtained.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.tare()
        """
        _ = self.query("T")

    def tare_immediately(self):
        """
        Tare the balance immediately.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.tare_immediately()
        """
        _ = self.query("TI")

    def zero(self):
        """
        Zero the balance after stable weight is obtained.

        Terminates processes such as zero, tare, calibration and testing etc.
        If the device is in standby mode, it is turned on. This function sets the
        currently read and the tare value to zero.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.zero()
        """
        _ = self.query("Z")

    def zero_immediately(self):
        """
        Zero the balance immediately.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.zero_immediately()
        """
        _ = self.query("ZI")

    def query(self, cmd, size=-1):
        """
        Query the instrument for a response.

        Error checking is performed on the response.

        :param str cmd: The command to send to the instrument.
        :param int size: Number of bytes to read from the instrument.

        :return: The response from the instrument.
        :rtype: str

        :raises: UserWarning if the balance is in dynamic mode.
        """
        self.sendcmd(cmd)

        rval = self.read(size)
        rval = rval.split()

        # error checking
        self._general_error_checking(rval[0])
        self._cmd_error_checking(rval[1])

        # raise warning if balance in dynamic mode
        if rval[1] == "D":
            warnings.warn("Balance in dynamic mode.", UserWarning)

        return rval[2:]

    def _cmd_error_checking(self, value):
        """
        Check for errors in the query response.

        :param value: Command specific error code.
        :return: None

        :raises: OSError if an error in the command occurred.
        """
        if value == "I":
            raise OSError("Internal error (e.g. balance not ready yet).")
        elif value == "L":
            raise OSError("Logical error (e.g. parameter not allowed).")
        elif value == "+":
            raise OSError(
                "Weigh module or balance is in overload range"
                "(weighing range exceeded)."
            )
        elif value == "-":
            raise OSError(
                "Weigh module or balance is in underload range"
                "(e.g. weighing pan is not in place)."
            )

    def _general_error_checking(self, value):
        """
        Check for general errors in the query response.

        :param value:  General error code.

        :return: None

        :raises: OSError if a general error occurred.
        """
        if value == "ES":
            raise OSError("Syntax Error.")
        elif value == "ET":
            raise OSError("Transmission Error.")
        elif value == "EL":
            raise OSError("Logical Error.")

    @property
    def mt_sics(self):
        """
        Get MT-SICS level and MT-SICS versions.

        :return: Level, Version Level 0, Version Level 1, Version Level 2,
            Version Level 3

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.mt_sics
        ['1', '1.0', '1.0', '1.0']
        """
        retval = [it.replace('"', "") for it in self.query("I1")]
        return retval

    @property
    def mt_sics_commands(self):
        """
        Get MT-SICS commands.

        Please refer to manual for information on the commands. Not all of these
        commands are currently implemented in this class!

        :return: List of all implemented MT-SICS levels and commands
        :rtype: list
        """
        timeout = self.timeout
        self.timeout = u.Quantity(0.1, u.s)

        retlist = []
        self.sendcmd("I0")
        while True:
            try:
                lst = self.read().split()
                if lst == []:  # data stream was empty
                    break
                retlist.append(lst)
            except OSError:  # communication timed out
                break
        self.timeout = timeout
        av_cmds = [[it[2], it[3].replace('"', "")] for it in retlist]
        return av_cmds

    @property
    def name(self):
        """Get / Set balance name.

        A maximum of 20 characters can be entered.

        :raises ValueError: If name is longer than 20 characters.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.name = "My Balance"
        >>> inst.name
        'My Balance'
        """
        retval = " ".join(self.query("I10"))
        return retval.replace('"', "")

    @name.setter
    def name(self, value):
        if len(value) > 20:
            raise ValueError("Name must be 20 characters or less.")
        _ = self.query(f'I10 "{value}"')

    @property
    def serial_number(self):
        """
        Get the serial number of the balance.

        :return: The serial number of the balance.
        :rtype: str

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.serial_number
        '123456789'
        """
        return self.query("I4")[0].replace('"', "")

    @property
    def tare_value(self):
        """Get / set the tare value.

        If no unit is given, grams are assumed.

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.tare_value = 1.0
        >>> inst.tare_value
        <Quantity(1.0, 'gram')>
        """
        retval = self.query("TA")
        return u.Quantity(float(retval[0]), retval[1])

    @tare_value.setter
    def tare_value(self, value):
        value = assume_units(value, u.gram)
        value = value.to(u.gram)
        _ = self.query(f"TA {value.magnitude} g")

    @property
    def weight(self):
        """
        Get the stable weight.

        :return: Stable weight
        :rtype: u.Quantity

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.weight
        <Quantity(1.0, 'gram')>
        """
        retval = self.query("S")
        return u.Quantity(float(retval[0]), retval[1])

    @property
    def weight_immediately(self):
        """
        Get the weight immediately, irrespective of balance stability.

        :return: Immediate weight
        :rtype: u.Quantity

        Example usage:
        >>> import instruments as ik
        >>> inst = ik.mettler_toledo.MTSICS.open_serial('/dev/ttyUSB0', 9600)
        >>> inst.weight_immediately
        <Quantity(1.0, 'gram')>
        """
        retval = self.query("SI")
        return u.Quantity(float(retval[0]), retval[1])
