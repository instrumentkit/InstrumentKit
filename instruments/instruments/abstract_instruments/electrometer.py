#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for electrometer instruments
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc
from future.utils import with_metaclass

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class Electrometer(with_metaclass(abc.ABCMeta, Instrument)):

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
        pass

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

        :type: `~quantities.UnitQuantity`
        """
        pass

    @property
    @abc.abstractmethod
    def trigger_mode(self):
        """
        Gets/sets the trigger mode for the electrometer. This is an
        abstract method.

        :type: `~enum.Enum`
        """
        pass

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
        pass

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
        pass

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
        pass

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
