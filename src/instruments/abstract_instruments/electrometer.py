#!/usr/bin/env python
"""
Provides an abstract base class for electrometer instruments
"""

# IMPORTS #####################################################################


import abc

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class Electrometer(Instrument, metaclass=abc.ABCMeta):

    """
    Abstract base class for electrometer instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def mode(self):
        """
        Gets/sets the measurement mode for the electrometer. This is an
        abstract method.

        :type: `~enum.Enum`
        """

    @mode.setter
    @abc.abstractmethod
    def mode(self, newval):
        pass

    @property
    @abc.abstractmethod
    def unit(self):
        """
        Gets/sets the measurement mode for the electrometer. This is an
        abstract method.

        :type: `~pint.Unit`
        """

    @property
    @abc.abstractmethod
    def trigger_mode(self):
        """
        Gets/sets the trigger mode for the electrometer. This is an
        abstract method.

        :type: `~enum.Enum`
        """

    @trigger_mode.setter
    @abc.abstractmethod
    def trigger_mode(self, newval):
        pass

    @property
    @abc.abstractmethod
    def input_range(self):
        """
        Gets/sets the input range setting for the electrometer. This is an
        abstract method.

        :type: `~enum.Enum`
        """

    @input_range.setter
    @abc.abstractmethod
    def input_range(self, newval):
        pass

    @property
    @abc.abstractmethod
    def zero_check(self):
        """
        Gets/sets the zero check status for the electrometer. This is an
        abstract method.

        :type: `bool`
        """

    @zero_check.setter
    @abc.abstractmethod
    def zero_check(self, newval):
        pass

    @property
    @abc.abstractmethod
    def zero_correct(self):
        """
        Gets/sets the zero correct status for the electrometer. This is an
        abstract method.

        :type: `bool`
        """

    @zero_correct.setter
    @abc.abstractmethod
    def zero_correct(self, newval):
        pass

    # METHODS #

    @abc.abstractmethod
    def fetch(self):
        """
        Request the latest post-processed readings using the current mode.
        (So does not issue a trigger)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read_measurements(self):
        """
        Trigger and acquire readings using the current mode.
        """
        raise NotImplementedError
