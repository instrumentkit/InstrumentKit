#!/usr/bin/env python
"""
Provides support for the Oxford ITC 503 temperature controller.
"""

# IMPORTS #####################################################################

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class OxfordITC503(Instrument):

    """
    The Oxford ITC503 is a multi-sensor temperature controller.

    Example usage::

    >>> import instruments as ik
    >>> itc = ik.oxford.OxfordITC503.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print(itc.sensor[0].temperature)
    >>> print(itc.sensor[1].temperature)
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        self.terminator = "\r"
        self.sendcmd("C3")  # Enable remote commands

    # INNER CLASSES #

    class Sensor:

        """
        Class representing a probe sensor on the Oxford ITC 503.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `OxfordITC503` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1

        # PROPERTIES #

        @property
        def temperature(self):
            """
            Read the temperature of the attached probe to the specified channel.

            :units: Kelvin
            :type: `~pint.Quantity`
            """
            value = float(self._parent.query(f"R{self._idx}")[1:])
            return u.Quantity(value, u.kelvin)

    # PROPERTIES #

    @property
    def sensor(self):
        """
        Gets a specific sensor object. The desired sensor is specified like
        one would access a list.

        For instance, this would query the temperature of the first sensor::

        >>> itc = ik.oxford.OxfordITC503.open_gpibusb('/dev/ttyUSB0', 1)
        >>> print(itc.sensor[0].temperature)

        :type: `OxfordITC503.Sensor`
        """
        return ProxyList(self, OxfordITC503.Sensor, range(3))
