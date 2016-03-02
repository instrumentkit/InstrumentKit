#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# channel.py: Python ABC for Signal Generators output channels
#
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

# CLASSES #####################################################################


class SGChannel(with_metaclass(abc.ABCMeta, object)):

    """
    Python abstract base class representing a single channel for a signal
    generator.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `~instruments.SignalGenerator` class.
    """

    # PROPERTIES ##

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
