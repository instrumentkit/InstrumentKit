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

    class Channel:
        """
        Class representing a sensor attached to the TPG 362.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TPG36x` class.
        """

        def __init__(self, parent, chan):
            if not isinstance(parent, TPG36x):
                raise TypeError("Don't do that.")

            self._parent = parent

        @property
        def pressure(self):
            """
            The pressure measured by the channel.

            :rtype: `pint.Quantity`
            """
            # TODO: Implement this!
            pass

    @property
    def channel(self):
        """
        Gets a specific channel object.

        Note that the channel number is pythonic, i.e., the first channel is 0.

        :rtype: `TPG36x.Channel`
        """
        return ProxyList(self, self.Channel, TPG36x.Channels)

    @property
    def name(self):
        """
        Get the name from the TPG36x.

        :rtype: str
        """
        # TODO: Implement this.
        pass

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
