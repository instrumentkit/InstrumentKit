#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# holzworth_hs9000.py: Instrument class for Holzworth HS-9000 series
#     multi-channel synthesizers.
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

# FIXME: so much documentation missing!

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units, ProxyList
from instruments.units import dBm

import quantities as pq
import re

## FUNCTIONS ###################################################################

# TODO: promote the following to util_fns in case another module needs it.
def split_unit_str(s):
    """
    Given a string of the form "12 C" or "14.7 GHz", returns a tuple of the
    numeric part and the unit part, irrespective of how many (if any) whitespace
    characters appear between.
    """
    # Borrowed from:
    # http://stackoverflow.com/questions/430079/how-to-split-strings-into-text-and-number
    match = re.match(r"([0-9\.]+)\s*([a-z]+)", s.strip(), re.I)
    if match:
        val, units = match.groups()
        return float(val), units
    else:
        try:
            return float(s), pq.dimensionless
        except ValueError:
            raise ValueError("Could not split '{}' into value and units.".format(repr(s)))
            
def _bounded_property(base_name, allowed_units, default_units, doc=""):
    
    def getter(self):
        return pq.Quantity(*split_unit_str(self._query("{}?".format(base_name))))
    
    def min_getter(self):
        return pq.Quantity(*split_unit_str(self._query("{}:MIN?".format(base_name))))
    
    def max_getter(self):
        return pq.Quantity(*split_unit_str(self._query("{}:MAX?".format(base_name))))
    
    def setter(self, newval):
        newval = assume_units(newval, default_units)
        
        if newval > max_getter(self) or newval < min_getter(self):
            raise ValueError("Value outside allowed bounds for this channel.")
        
        if newval.units not in allowed_units:
            newval = newval.rescale(default_units)
            
        self._sendcmd("{} {}".format(base_name, newval))
        
    return property(getter, setter, doc=doc), property(min_getter), property(max_getter)
    

## CLASSES #####################################################################

class HolzworthHS9000(Instrument):
    """
    Communicates with a `Holzworth HS-9000 series`_ multi-channel frequency
    synthesizer. 
    
    .. _Holzworth HS-9000 series: http://www.holzworth.com/synthesizers-multi.htm
    """
    
    ## INNER CLASSES ##
    
    class Channel(object):
        # TODO: docstring!
        
        def __init__(self, hs, idx_chan):
            self._hs = hs
            self._idx = idx_chan
            
            # We unpacked the channel index from the string of the form "CH1",
            # in order to make the API more Pythonic, but now we need to put
            # it back.
            self._ch_name = "CH{}".format(idx_chan)
           
        ## PRIVATE METHODS ##
            
        def _sendcmd(self, cmd):
            self._hs.sendcmd("{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))
            
        def _query(self, cmd):
            return self._hs.query("{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))
            
        
        ## STATE METHODS ##
            
        def reset(self):
            self._sendcmd("*RST")
            
        def recall_state(self):
            self._sendcmd("*RCL")
            
        def save_state(self):
            self._sendcmd("*SAV")
            
        ## PROPERTIES ##
        
        @property
        def temperature(self):
            val, units = split_unit_str(self._query("TEMP?"))
            units = "deg{}".format(units)
            return pq.Quantity(val, units)
            
        frequency, frequency_min, frequency_max = _bounded_property(
            "FREQ", [pq.Hz, pq.kHz, pq.MHz, pq.GHz], pq.GHz
        )
        power, power_min, power_max = _bounded_property(
            "PWR", [dBm], dBm
        )
        phase, phase_min, phase_max = _bounded_property(
            "PHASE", [pq.degree], pq.degree
        )
        
        @property
        def power_on(self):
            return bool(self._query("PWR:RF?"))
        @power_on.setter
        def power_on(self, newval):
            self._sendcmd("PWR:RF {}".format("ON" if newval else "OFF"))
                
    ## PROXY LIST ##
    
    def _channel_idxs(self):
        # The command :ATTACH? returns a string of the form ":CH1:CH2" to
        # indicate what channels are attached to the internal USB bus.
        return [
            int(ch_name.replace("CH", "")) - 1
            for ch_name in self.query(":ATTACH?").split(":")
            if ch_name
        ]
        
    @property
    def channel(self):
        return ProxyList(self, self.Channel, self._channel_idxs())
        
    ## OTHER PROPERTIES ##
    
    @property
    def name(self):
        # This is a weird one; the HS-9000 associates the :IDN? command
        # with each individual channel, though we want it to be a synthesizer-
        # wide property. To solve this, we assume that CH1 is always a channel
        # and ask its name.
        return self.channel[0]._query("IDN?")
    
    @property
    def ready(self):
        return "Ready" in self.query(":COMM:READY?")
        
        
