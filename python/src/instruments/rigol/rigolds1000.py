#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# rigolds1000.py: Instrument class for Rigol DS-1000 Series oscilloscopes.
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

from instruments.abstract_instruments import (
    Oscilloscope, OscilloscopeChannel, OscilloscopeDataSource
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList

## ENUMS #######################################################################
# TODO: reach some sort of decision about whether enums live inside or outside
#       the classes to which they are related.

class Coupling(Enum):
    ac = "AC"
    dc = "DC"
    ground = "GND"

## FUNCTIONS ###################################################################

# TODO: promote to util_fns.
def bool_property(name, inst_true, inst_false, doc=None):
    def getter(self):
        return self.query(name + "?").strip() == inst_true
    def setter(self, newval):
        self.sendcmd("{} {}".format(name, inst_true if newval else inst_false))
        
    return property(fget=getter, fset=setter, doc=doc)

## CLASSES #####################################################################

class RigolDS1000Series(SCIPInstrument, Oscilloscope):

    class Channel(OscilloscopeChannel):
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1 # Rigols are 1-based.
            
        def sendcmd(self, cmd):
            self._parent.sendcmd(":CHAN{}:{}".format(self._idx, cmd))
            
        def query(self, cmd):
            return self._parent.query(":CHAN{}:{}".format(self._idx, cmd))
        
        @property
        def coupling(self):
            return Coupling[self.query("COUP?")]
        @coupling.setter
        def coupling(self, newval):
            self.sendcmd(Coupling[newval].value)
    
        bw_limit = bool_property("BWL", "ON", "OFF")
        display = bool_property("DISP", "ON", "OFF")
        invert = bool_property("INV", "ON", "OFF")
        
        # TODO: :CHAN<n>:OFFset
        # TODO: :CHAN<n>:PROBe
        # TODO: :CHAN<n>:SCALe
        
        filter = bool_property("FILT", "ON", "OFF")
        
        # TODO: :CHAN<n>:MEMoryDepth
        
        vernier = bool_property("VERN", "ON", "OFF")
    
    class DataSource(OscilloscopeDataSource):
        pass
    
    ## PROPERTIES ##
    
    @property
    def channel(self, idx):
        # Rigol DS1000 series oscilloscopes all have two channels,
        # according to the documentation.
        return ProxyList(self, self.Channel, xrange(2))
        
        
