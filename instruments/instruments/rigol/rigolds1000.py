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

from flufl.enum import Enum

from instruments.abstract_instruments import (
    Oscilloscope, OscilloscopeChannel, OscilloscopeDataSource
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList, bool_property, enum_property

## ENUMS #######################################################################
# TODO: reach some sort of decision about whether enums live inside or outside
#       the classes to which they are related.

class AcquisitionType(Enum):
    normal = "NORM"
    average = "AVER"
    peak_detect = "PEAK"

class Coupling(Enum):
    ac = "AC"
    dc = "DC"
    ground = "GND"

## FUNCTIONS ###################################################################


## CLASSES #####################################################################

class RigolDS1000Series(SCPIInstrument, Oscilloscope):

    class DataSource(OscilloscopeDataSource):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
        @property
        def name(self):
            return self._name
            
        def read_waveform(self):
            # TODO: add DIG, FFT.
            if self.name not in ["CHAN1", "CHAN2", "DIG", "MATH", "FFT"]:
                raise NotImplementedError("Rigol DS1000 series does not support reading waveforms from {}.".format(self.name))
            self._parent.sendcmd(":WAV:DATA? {}".format(self.name))
            data = self._parent.binblockread(2) # TODO: check width
            return data
    

    class Channel(DataSource, OscilloscopeChannel):
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1 # Rigols are 1-based.
            
            # Initialize as a data source with name CHAN{}.
            super(RigolDS1000Series.Channel, self).__init__(self._parent, "CHAN{}".format(self._idx))
            
        def sendcmd(self, cmd):
            self._parent.sendcmd(":CHAN{}:{}".format(self._idx, cmd))
            
        def query(self, cmd):
            return self._parent.query(":CHAN{}:{}".format(self._idx, cmd))
        
        coupling = enum_property("COUP", Coupling)
    
        bw_limit = bool_property("BWL", "ON", "OFF")
        display = bool_property("DISP", "ON", "OFF")
        invert = bool_property("INV", "ON", "OFF")
        
        # TODO: :CHAN<n>:OFFset
        # TODO: :CHAN<n>:PROBe
        # TODO: :CHAN<n>:SCALe
        
        filter = bool_property("FILT", "ON", "OFF")
        
        # TODO: :CHAN<n>:MEMoryDepth
        
        vernier = bool_property("VERN", "ON", "OFF")
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        # Rigol DS1000 series oscilloscopes all have two channels,
        # according to the documentation.
        return ProxyList(self, self.Channel, xrange(2))
        
    @property
    def math(self):
        return DataSource("MATH")
    @property
    def ref(self):
        return DataSource("REF")
        
    acquire_type = enum_property(":ACQ:TYPE", AcquisitionType)
    # TODO: implement :ACQ:MODE. This is confusing in the documentation, though.
    
    @property
    def acquire_averages(self):
        return int(self.query(":ACQ:AVER?"))
    @acquire_averages.setter
    def acquire_averages(self, newval):
        if newval not in [2**i for i in xrange(1,9)]:
            raise ValueError(
                "Number of averages {} not supported by instrument; "
                "must be a power of 2 from 2 to 256.".format(newval)
            )
        self.sendcmd(":ACQ:AVER {}".format(newval))
    
    # TODO: implement :ACQ:SAMP in a meaningful way. This should probably be
    #       under Channel, and needs to be unitful.
    # TODO: I don't understand :ACQ:MEMD yet.
        
    ## METHODS ##
    
    def force_trigger(self):
        self.sendcmd(":FORC")
        
    # TODO: consider moving the next few methods to Oscilloscope.
    def run(self):
        self.sendcmd(":RUN")
        
    def stop(self):
        self.sendcmd(":STOP")
        
    # TODO: unitful timebase!
    
    ## FRONT-PANEL KEY EMULATION METHODS ##
    # These methods correspond one-to-one with physical keys on the front
    # (local) control panel, except for release_panel, which enables the local
    # panel and disables any remote lockouts, and for panel_locked.
    #
    # Many of the :KEY: commands are not yet implemented as methods.
    
    panel_locked = bool_property(":KEY:LOCK", "ON", "OFF")
    
    def release_panel(self):
        # TODO: better name?
        # NOTE: method may be redundant with the panel_locked property.
        """
        Releases any lockout of the local control panel.
        """
        self.sendcmf(":KEY:FORC")
        
    
