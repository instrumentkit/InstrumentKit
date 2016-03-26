#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for signal generator output channels
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc

from future.utils import with_metaclass

# CLASSES #####################################################################


class SGChannel(with_metaclass(abc.ABCMeta, object)):

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

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @frequency.setter
    @abc.abstractmethod
    def frequency(self, newval):
        pass

    @property
    @abc.abstractmethod
    def power(self):
        """
        Gets/sets the output power of the signal generator channel

        :type: `~quantities.quantity.Quantity`
        """
        pass

    @power.setter
    @abc.abstractmethod
    def power(self, newval):
        pass

    @property
    @abc.abstractmethod
    def phase(self):
        """
        Gets/sets the output phase of the signal generator channel

        :type: `~quantities.quantity.Quantity`
        """
        pass

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
        pass

    @output.setter
    @abc.abstractmethod
    def output(self, newval):
        pass
