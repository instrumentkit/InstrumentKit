#!/usr/bin/env python
"""
Provides support for the Lakeshore Model 336 cryogenic temperature controller.
"""

# IMPORTS #####################################################################

from instruments.generic_scpi import SCPIInstrument
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class Lakeshore336(SCPIInstrument):
    """
    The Lakeshore Model 336 is a multi-sensor cryogenic temperature controller.

    Example usage:

    >>> import instruments as ik
    >>> import instruments.units as u
    >>> import serial
    >>> inst = ik.lakeshore.Lakeshore336.open_serial('/dev/ttyUSB0', baud=57600, bytesize=serial.SEVENBITS, parity=serial.PARITY_ODD, stopbits=serial.STOPBITS_ONE)
    >>> print(inst.sensor[0].temperature)
    >>> print(inst.sensor[1].temperature)
    """

    # INNER CLASSES ##

    class Sensor:
        """
        Class representing a sensor attached to the Lakeshore Model 336.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `Lakeshore336` class.
        """

        def __init__(self, parent, idx):
            _idx_mapper = {0: "A", 1: "B", 2: "C", 3: "D"}
            self._parent = parent
            self._idx = _idx_mapper[idx]

        # PROPERTIES ##

        @property
        def temperature(self):
            """
            Gets the temperature of the specified sensor.

            :units: Kelvin
            :type: `~pint.Quantity`
            """
            value = self._parent.query(f"KRDG?{self._idx}")
            return u.Quantity(float(value), u.kelvin)

    # PROPERTIES ##

    @property
    def sensor(self):
        """
        Gets a specific sensor object. The desired sensor is specified like
        one would access a list.

        For instance, after opening the connection as described in the overview,
        this would query the temperature of the first sensor:

        >>> print(inst.sensor[0].temperature)

        The Lakeshore 336 supports up to 4 sensors (index 0-3).

        :rtype: `~Lakeshore336.Sensor`
        """
        return ProxyList(self, Lakeshore336.Sensor, range(4))
