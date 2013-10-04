#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# axis_controller.py: Provides base class axis-device controllers.
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

from instruments.abstract_instruments import Instrument

from .axis_collection import AxisCollection
from .axis_list import AxisList
from .axis import Axis
from instruments.util_fns import ProxyList

## CLASSES #####################################################################

class AxisController(Instrument):
    #__metaclass__ = abc.ABCMeta # Needed?
    
    def __init__(self, filelike):
        """
        During init of AxisController, a tuple should be generated containing 
        Axis objects representing physically connected axis-objects. This tuple
        is then in turn fed into an AxisCollection object and stored.
        """
        super(AxisController, self).__init__(filelike)
        axis_list = range(1) # Placeholder. Should be overridden for each
                              # controller's specific implementation needs.
        axis_list = AxisList(self, _Axis, axis_list)
        self._axiscollection = AxisCollection(axis_list)
    
    ## PROPERTIES ##
    
    @property
    def axis(self):
        return self._axiscollection.axis
