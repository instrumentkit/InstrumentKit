#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# power_supply.py: Python ABC for power supplies
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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

## IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class PowerSupplyChannel(with_metaclass(abc.ABCMeta, object)):
    
    ## PROPERTIES ##

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
    
    ## PROPERTIES ##
    
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
