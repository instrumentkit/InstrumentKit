#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for power supply instruments
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc

from future.utils import with_metaclass

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class PowerSupplyChannel(with_metaclass(abc.ABCMeta, object)):

    """
    Abstract base class for power supply output channels.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def mode(self):
        """
        Gets/sets the output mode for the power supply channel. This is an
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
    def voltage(self):
        """
        Gets/sets the output voltage for the power supply channel. This is an
        abstract method.

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @voltage.setter
    @abc.abstractmethod
    def voltage(self, newval):
        pass

    @property
    @abc.abstractmethod
    def current(self):
        """
        Gets/sets the output current for the power supply channel. This is an
        abstract method.

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @current.setter
    @abc.abstractmethod
    def current(self, newval):
        pass

    @property
    @abc.abstractmethod
    def output(self):
        """
        Gets/sets the output status for the power supply channel. This is an
        abstract method.

        :type: `bool`
        """
        pass

    @output.setter
    @abc.abstractmethod
    def output(self, newval):
        pass


class PowerSupply(with_metaclass(abc.ABCMeta, Instrument)):

    """
    Abstract base class for power supply instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def channel(self):
        """
        Gets a channel object for the power supply. This should use
        `~instruments.util_fns.ProxyList` to achieve this.

        This is an abstract method.

        :rtype: `PowerSupplyChannel`
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def voltage(self):
        """
        Gets/sets the output voltage for all channel on the power supply.
        This is an abstract method.

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @voltage.setter
    @abc.abstractmethod
    def voltage(self, newval):
        pass

    @property
    @abc.abstractmethod
    def current(self):
        """
        Gets/sets the output current for all channel on the power supply.
        This is an abstract method.

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @current.setter
    @abc.abstractmethod
    def current(self, newval):
        pass
