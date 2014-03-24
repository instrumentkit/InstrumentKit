#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tekdpo70000.py: Driver for the Tektronix DPO 70000 oscilloscope series.
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

from flufl.enum import Enum

from instruments.abstract_instruments import (
    Oscilloscope, OscilloscopeChannel, OscilloscopeDataSource
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import *


## CLASSES #####################################################################

class TekDPO70000Series(SCPIInstrument, Oscilloscope):

    ## CONSTANTS ##

    # The number of horizontal and vertical divisions.
    HOR_DIVS = 10
    VERT_DIVS = 10

    ## ENUMS ##

    class AcquisitionMode(Enum):
        sample = "SAM"
        peak_detect = "PEAK"
        hi_res = "HIR"
        average = "AVE"
        waveform_db = "WFMDB"
        envelope = "ENV"

    class Coupling(Enum):
        ac = "AC"
        dc = "DC"
        dc_reject = "DCREJ"
        ground = "GND"

    ## CLASSES ##

    class DataSource(OscilloscopeDataSource):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
        @property
        def name(self):
            return self._name

        @abs.abstract_property
        def _scale_raw_data(self, data):
            '''
            Takes the int16 data and figures out how to make it unitful.
            '''
            
        def read_waveform(self):
            # TODO: DO
            pass
    
    class Math(DataSource):
        """
        Represents a single math channel on the oscilliscope.
        """
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1 # 1-based.
            
            # Initialize as a data source with name MATH{}.
            super(TekDPO70000Series.Channel, self).__init__(self._parent, "MATH{}".format(self._idx))
            
        def sendcmd(self, cmd):
            self._parent.sendcmd("MATH{}:{}".format(self._idx, cmd))
            
        def query(self, cmd):
            return self._parent.query("MATH{}:{}".format(self._idx, cmd))
        
        class FilterMode(Enum):
            centered = "CENT"
            shifted = "SHIF"

        class Mag(Enum):
            linear = "LINEA"
            db = "DB"
            dbm = "DBM"

        class Phase(Enum):
            degrees = "DEG"
            radians = "RAD"
            group_delay = "GROUPD"

        class SpectralWindow(Enum):
            rectangular = "RECTANG"
            hamming = "HAMM"
            hanning = "HANN"
            kaiser_besse = "KAISERB"
            blackman_harris = "BLACKMANH"
            flattop2 = "FLATTOP2"
            gaussian = "GAUSS"
            tek_exponential = "TEKEXP"

        define = string_property("DEF", doc="A text string specifying the math to do, ex. CH1+CH2")
        filter_mode = enum_property("FILT:MOD", FilterMode)
        filter_risetime = unitful_property("FILT:RIS", pq.second)

        label = string_property('LAB:NAM', doc="Just a human readable label for the channel.")
        label_xpos = unitless_property('LAB:XPOS', doc="The x position, in divisions, to place the label.")
        label_ypos = unitless_property('LAB:YPOS', doc="The y position, in divisions, to place the label.")

        num_avg = unitless_property('NUMAV', doc="The number of acquisistions over which exponential averaging is performed.")

        spectral_center = unitful_property('SPEC:CENTER', pq.Hz, doc="The desired frequency of the spectral analyzer output data span in Hz.")
        spectral_gatepos = unitful_property('SPEC:GATEPOS', pq.second, doc="The gate position. Units are represented in seconds, with respect to trigger position.")
        spectral_gatewidth = unitful_property('SPEC:GATEWIDTH', pq.second, doc="The time across the 10-division screen in seconds.")
        spectral_lock = bool_property('SPEC:LOCK', 'ON', 'OFF')
        spectral_mag = unitful_property('SPEC:MAG', Mag, doc="Whether the spectral magnitude is linear, db, or dbm.")
        spectral_mag = unitful_property('SPEC:PHASE', Mag, doc="Whether the spectral phase is degrees, radians, or group delay.")
        spectral_reflevel = unitless_property('SPEC:REFL', doc="The value that represents the topmost display screen graticule. The units depend on spectral_mag.")
        spectral_reflevel_offset = unitless_property('SPEC:REFLEVELO')
        spectral_resolution_bandwidth = unitful_property('SPEC:RESB', pq.Hz, doc="The desired resolution bandwidth value. Units are represented in Hertz.")
        spectral_span = unitlful_property('SPEC:SPAN', pq.Hz, doc="Specifies the frequency span of the output data vector from the spectral analyzer.")
        spectral_suppress = unitless_property('SPEC:SUPP', doc="The magnitude level that data with magnitude values below this value are displayed as zero phase.")    
        spectral_unwrap = bool_property('SPEC:UNWR', 'ON', 'OFF', doc="Enables or disables phase wrapping.")
        spectral_window = enum_property('SPEC:WIN', SpectralWindow)

        threshhold = unitful_property('THRESH', pq.volt, doc="The math threshhold in volts")
        unit_string = string_property('UNITS', doc="Just a label for the units...doesn't actually change anything.")
        
        autoscale = bool_property('VERT:AUTOSC', 'ON', 'OFF', doc="Enables or disables the auto-scaling of new math waveforms.")
        position = unitless_property('VERT:POS', doc="The vertical position, in divisions from the center graticule.")
        scale = unitful_property('VERT:SCALE', pq.volt, doc="The scale in volts per division. The range is from 100e-36 to 100e+36.")

        def _scale_raw_data(self, data):
            # TODO: incorperate the unit_string somehow
            return self.scale*(
                ((TekDPO70000Series.VERT_DIVS/2)*float(data)/(2^15)
                - self.position
            )

    class Channel(DataSource, OscilloscopeChannel):
        """
        Represents a single physical channel on the oscilliscope.
        """
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1 # 1-based.
            
            # Initialize as a data source with name CH{}.
            super(TekDPO70000Series.Channel, self).__init__(self._parent, "CH{}".format(self._idx))
            
        def sendcmd(self, cmd):
            self._parent.sendcmd("CH{}:{}".format(self._idx, cmd))
            
        def query(self, cmd):
            return self._parent.query("CH{}:{}".format(self._idx, cmd))
        
        coupling = enum_property("COUP", Coupling)
        bandwidth = unitful_property('BAN', pq.Hz)
        deskew = unitful_property('DESK', pq.second)
        termination = unitful_property('TERM', pq.ohm)

        label = string_property('LAB:NAM', doc="Just a human readable label for the channel.")
        label_xpos = unitless_property('LAB:XPOS', doc="The x position, in divisions, to place the label.")
        label_ypos = unitless_property('LAB:YPOS', doc="The y position, in divisions, to place the label.")

        offset = unitful_property('OFFS', pq.volt, doc="The vertical offset in units of volts. Voltage is given by offset+scale*(5*raw/2^15 - position).")
        position = unitless_property('POS', doc="The vertical position, in divisions from the center graticule, ranging from -8 to 8. Voltage is given by offset+scale*(5*raw/2^15 - position).")
        scale = unitful_property('SCALE', pq.volt, doc="Vertical channel scale in units volts/division. Voltage is given by offset+scale*(5*raw/2^15 - position).")
        
        def _scale_raw_data(self, data):
            return self.scale*(
                ((TekDPO70000Series.VERT_DIVS/2)*float(data)/(2^15)
                - self.position
            ) + self.offset
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        # Support four channels
        return ProxyList(self, self.Channel, xrange(4))
        
    @property
    def math(self):
        return DataSource("MATH")
    @property
    def ref(self):
        return DataSource("REF")
        
    acquire_type = enum_property(":ACQ:TYPE", AcquisitionMode)
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
    
