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

    class AcquisitionState(Enum):
        on = 'ON'
        off = 'OFF'
        run = 'RUN'
        stop = 'STOP'

    class StopAfter(Enum):
        run_stop = 'RUNST'
        sequence = 'SEQ'

    class SamplingMode(Enum):
        real_time = "RT"
        equivalent_time_allowed = "ET"
        interpolation_allowed = "IT"

    class Coupling(Enum):
        ac = "AC"
        dc = "DC"
        dc_reject = "DCREJ"
        ground = "GND"

    class HorizontalMode(Enum):
        auto = "AUTO"
        constant = "CONST"
        manual = "MAN"

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
        return ProxyList(self, self.Channel, xrange(4))
        
    @property
    def math(self):
        return ProxyList(self, self.Math, xrange(4))

    @property
    def ref(self):
        raise NotImplementedError


    # For some settings that probably won't be used that often, use 
    # string_property instead of setting up an enum property.
    acquire_enhanced_enob = string_property('ACQ:ENHANCEDE', bookmark_symbol='', doc='Valid values are AUTO and OFF.')
    acquire_enhanced_enob = bool_proprety('ACQ:ENHANCEDE:STATE', '0', '1')
    acquire_interp_8bit = string_property('ACQ:INTERPE', bookmark_symbol='',  doc='Valid values are AUTO, ON and OFF.')
    acquire_magnivu = bool_property('ACQ:MAG', 'ON', 'OFF')
    acquire_mode = enum_property('ACQ:MOD', AcquisitionMode)
    acquire_mode_actual = enum_property('ACQ:MOD:ACT', AcquisitionMode, readonly=True)
    acquire_num_acquisitions = int_property('ACQ:NUMAC', readonly=True, doc="The number of waveform acquisitions that have occurred since starting acquisition with the ACQuire:STATE RUN command")
    acquire_num_avgs = int_property('ACQ:NUMAV', doc="The number of waveform acquisitions to average.")
    acquire_num_envelop = int_property('ACQ:NUME', doc="The number of waveform acquisitions to be enveloped");
    acquire_num_frames = int_property('ACQ:NUMFRAMESACQ', readonly=True, doc="The number of frames acquired when in FastFrame Single Sequence and acquisitions are running.")  
    acquire_num_samples = int_property('ACQ:NUMSAM', doc="The minimum number of acquired samples that make up a waveform database (WfmDB) waveform for single sequence mode and Mask Pass/Fail Completion Test. The default value is 16,000 samples. The range is 5,000 to 2,147,400,000 samples.")
    acquire_sampling_mode = enum_property('ACQ:SAMP', SamplingMode)
    acquire_state = enum_property('ACQ:STATE', AcquisitionState, doc="This command starts or stops acquisitions.")
    acquire_stop_after = enum_property('ACQ:STOPA', StopAfter, doc="This command sets or queries whether the instrument continually acquires acquisitions or acquires a single sequence.")


    horiz_acq_duration = unitful_property('HOR:ACQDURATION', pq.second, readonly=True, doc="The duration of the acquisition.")
    horiz_acq_length = int_property('HOR:ACQLENGTH', readonly=True, doc="The record length.")
    horiz_delay_mode = bool_property('HOR:DEL:MOD', '1', '0')
    horiz_delay_pos = unitful_property('HOR:DEL:POS', pq.percent, doc="The percentage of the waveform that is displayed left of the center graticule.")
    horiz_delay_time = unitful_property('HOR:DEL:TIM', pq.second, doc="The base trigger delay time setting.")
    horiz_interp_ratio = unitless_property('HOR:MAI:INTERPR', readonly=True, doc="The ratio of interpolated points to measured points.")
    horiz_main_pos = unitful_property('HOR:MAI:POS', pq.percent, doc="The percentage of the waveform that is displayed left of the center graticule.")
    horiz_unit = string_property('HOR:MAI:UNI')
    horiz_mode = enum_property('HOR:MODE', HorizontalMode)
    horiz_record_length_lim = int_property('HOR:MODE:AUTO:LIMIT', doc="The recond length limit in samples.")
    horiz_record_length = int_property('HOR:MODE:RECO', doc="The recond length in samples. See `horiz_mode`; manual mode lets you change the record length, while the length is readonly for auto and constant mode.")
    horiz_sample_rate = unitful_property('HOR:MODE:SAMPLER', pq.Hz, doc="The sample rate in samples per second.")
    horiz_scale = unitful_property('HOR:MODE:SCA', pq.second, doc="The horizontal scale in seconds per division. The horizontal scale is readonly when `horiz_mode` is manual.")
    horiz_pos = unitful_property('HOR:POS', pq.percent, doc="The position of the trigger point on the screen, left is 0%, right is 100%.")
    horiz_roll = string_property('HOR:ROLL',  bookmark_symbol='', doc="Valid arguments are AUTO, OFF, and ON.")
    


    ## METHODS ##
    
    def force_trigger(self):
        raise NotImplementedError
        
    # TODO: consider moving the next few methods to Oscilloscope.
    def run(self):
        self.sendcmd(":RUN")
        
    def stop(self):
        self.sendcmd(":STOP")

    
