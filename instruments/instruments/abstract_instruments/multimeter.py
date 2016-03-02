#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# multimeter.py: Python class for multimeters
#
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
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
#

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class Multimeter(with_metaclass(abc.ABCMeta, Instrument)):

    # PROPERTIES ##

    @property
    @abc.abstractmethod
    def mode(self):
        """
        Gets/sets the measurement mode for the multimeter. This is an
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
    def trigger_mode(self):
        """
        Gets/sets the trigger mode for the multimeter. This is an
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
    def relative(self):
        """
        Gets/sets the status of relative measuring mode for the multimeter.
        This is an abstract method.

        :type: `bool`
        """
        pass

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

        :type: `~quantities.quantity.Quantity` or `~enum.Enum`
        """
        pass

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
        pass
