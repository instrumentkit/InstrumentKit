#!/usr/bin/env python
"""
Provides support for the Lakeshore 370 AC resistance bridge.
"""

# IMPORTS #####################################################################

from instruments.generic_scpi import SCPIInstrument
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class Lakeshore370(SCPIInstrument):

    """
    The Lakeshore 370 is a multichannel AC resistance bridge for use in low
    temperature dilution refridgerator setups.

    Example usage:

    >>> import instruments as ik
    >>> bridge = ik.lakeshore.Lakeshore370.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print(bridge.channel[0].resistance)
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        # Disable termination characters and enable EOI
        self.sendcmd("IEEE 3,0")

    # INNER CLASSES ##

    class Channel:

        """
        Class representing a sensor attached to the Lakeshore 370.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `Lakeshore370` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1

        # PROPERTIES ##

        @property
        def resistance(self):
            """
            Gets the resistance of the specified sensor.

            :units: Ohm
            :rtype: `~pint.Quantity`
            """
            value = self._parent.query(f"RDGR? {self._idx}")
            return u.Quantity(float(value), u.ohm)

    # PROPERTIES ##

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        For instance, this would query the resistance of the first channel::

        >>> import instruments as ik
        >>> bridge = ik.lakeshore.Lakeshore370.open_serial("COM5")
        >>> print(bridge.channel[0].resistance)

        The Lakeshore 370 supports up to 16 channels (index 0-15).

        :rtype: `~Lakeshore370.Channel`
        """
        return ProxyList(self, Lakeshore370.Channel, range(16))
