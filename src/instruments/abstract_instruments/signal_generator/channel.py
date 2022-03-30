#!/usr/bin/env python
"""
Provides an abstract base class for signal generator output channels
"""

# IMPORTS #####################################################################

import abc

# CLASSES #####################################################################


class SGChannel(metaclass=abc.ABCMeta):

    """
    Python abstract base class representing a single channel for a signal
    generator.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `~instruments.SignalGenerator` class.
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def frequency(self):
        """
        Gets/sets the output frequency of the signal generator channel

        :type: `~pint.Quantity`
        """

    @frequency.setter
    @abc.abstractmethod
    def frequency(self, newval):
        pass

    @property
    @abc.abstractmethod
    def power(self):
        """
        Gets/sets the output power of the signal generator channel

        :type: `~pint.Quantity`
        """

    @power.setter
    @abc.abstractmethod
    def power(self, newval):
        pass

    @property
    @abc.abstractmethod
    def phase(self):
        """
        Gets/sets the output phase of the signal generator channel

        :type: `~pint.Quantity`
        """

    @phase.setter
    @abc.abstractmethod
    def phase(self, newval):
        pass

    @property
    @abc.abstractmethod
    def output(self):
        """
        Gets/sets the output status of the signal generator channel

        :type: `bool`
        """

    @output.setter
    @abc.abstractmethod
    def output(self, newval):
        pass
