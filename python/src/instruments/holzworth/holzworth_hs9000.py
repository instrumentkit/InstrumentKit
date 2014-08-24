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
from instruments.abstract_instruments.signal_generator import (
    SignalGenerator, 
    SGChannel
)
from instruments.util_fns import assume_units, ProxyList, split_unit_str
from instruments.units import dBm

import quantities as pq
import re

## FUNCTIONS ###################################################################
            
# TODO: elevate this to util_fns, generalize enough to capture fixed limits
#       rather than just :MIN, :MAX style SCPI limits, so that it can be used
#       for instruments like the Qubitekk CC1.
#       While doing that, rename to bounded_unitful_property for parity
#       with unitful_property, and write some bloody unit tests for it.
def _bounded_property(base_name, allowed_units, default_units, doc=""):
    
    def getter(self):
        return pq.Quantity(*split_unit_str(
            self._query("{}?".format(base_name)),
            default_units
        ))
    
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
            
        self._sendcmd("{}:{}".format(base_name, newval))
        
    return property(getter, setter, doc=doc), property(min_getter), property(max_getter)
    

## CLASSES #####################################################################

class HolzworthHS9000(SignalGenerator):
    """
    Communicates with a `Holzworth HS-9000 series`_ multi-channel frequency
    synthesizer. 
    
    .. _Holzworth HS-9000 series: http://www.holzworth.com/synthesizers-multi.htm
    """
    
    ## INNER CLASSES ##
    
    class Channel(SGChannel):
        # TODO: docstring!
        
        def __init__(self, hs, idx_chan):
            self._hs = hs
            self._idx = idx_chan
            
            # We unpacked the channel index from the string of the form "CH1",
            # in order to make the API more Pythonic, but now we need to put
            # it back.
            # Some channel names, like "REF", are special and are preserved
            # as strs.
            self._ch_name = (
                idx_chan if isinstance(idx_chan, str)
                else "CH{}".format(idx_chan + 1)
            )
                      
        ## PRIVATE METHODS ##
            
        def _sendcmd(self, cmd):
            self._hs.sendcmd(":{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))
            
        def _query(self, cmd):
            return self._hs.query(":{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))
            
        
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
            
        freq, freq_min, freq_max = _bounded_property(
            "FREQ", [pq.Hz, pq.kHz, pq.MHz, pq.GHz], pq.GHz
        )
        power, power_min, power_max = _bounded_property(
            "PWR", [dBm], dBm
        )
        phase, phase_min, phase_max = _bounded_property(
            "PHASE", [pq.degree], pq.degree
        )
        
        @property
        def output(self):
            return (self._query("PWR:RF?").strip() == 'ON')
        @output.setter
        def output(self, newval):
            self._sendcmd("PWR:RF:{}".format("ON" if newval else "OFF"))
                
    ## PROXY LIST ##
    
    def _channel_idxs(self):
        # The command :ATTACH? returns a string of the form ":CH1:CH2" to
        # indicate what channels are attached to the internal USB bus.
        # We convert what channel names we can to integers, and leave the
        # rest as strings.
        return [
            (
                int(ch_name.replace("CH", "")) - 1
                if ch_name.startswith('CH') else
                ch_name.strip()
            )
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
        
        
