#!/usr/bin/env python
"""
Provides an abstract base class for multimeter instruments
"""

# IMPORTS #####################################################################


import abc

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class Multimeter(Instrument, metaclass=abc.ABCMeta):

    """
    Abstract base class for multimeter instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def mode(self):
        """
        Gets/sets the measurement mode for the multimeter. This is an
        abstract method.

        :type: `~enum.Enum`
        """

    @mode.setter
    @abc.abstractmethod
    def mode(self, newval):
        pass

    @property
    @abc.abstractmethod
    def trigger_mode(self):
        """
        Gets/sets the trigger mode for the multimeter. This is an
        abstract method.

        :type: `~enum.Enum`
        """

    @trigger_mode.setter
    @abc.abstractmethod
    def trigger_mode(self, newval):
        pass

    @property
    @abc.abstractmethod
    def relative(self):
        """
        Gets/sets the status of relative measuring mode for the multimeter.
        This is an abstract method.

        :type: `bool`
        """

    @relative.setter
    @abc.abstractmethod
    def relative(self, newval):
        pass

    @property
    @abc.abstractmethod
    def input_range(self):
        """
        Gets/sets the current input range setting of the multimeter.
        This is an abstract method.

        :type: `~pint.Quantity` or `~enum.Enum`
        """

    @input_range.setter
    @abc.abstractmethod
    def input_range(self, newval):
        pass

    # METHODS ##

    @abc.abstractmethod
    def measure(self, mode):
        """
        Perform a measurement as specified by mode parameter.
        """
