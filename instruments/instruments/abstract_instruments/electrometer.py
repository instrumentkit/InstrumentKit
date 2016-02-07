#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# multimeter.py: Python class for electrometers
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
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
##
##

## IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class Electrometer(with_metaclass(abc.ABCMeta, Instrument)):

    ## PROPERTIES ##

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
        Gets/sets the measurement mode for the multimeter. This is an
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

    ## METHODS ##

    @abc.abstractmethod
    def fetch(self):
        """
        Request the latest post-processed readings using the current mode. 
        (So does not issue a trigger)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read(self):
        """
        Trigger and acquire readings using the current mode.
        """
        raise NotImplementedError
