#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Tektronix DPO 70000 oscilloscope series
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc
import time

from builtins import range
from enum import Enum

import quantities as pq

from instruments.abstract_instruments import (
    Oscilloscope, OscilloscopeChannel, OscilloscopeDataSource
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import (
    enum_property, string_property, int_property, unitful_property,
    unitless_property, bool_property, ProxyList
)

# CLASSES #####################################################################


class TekDPO70000(SCPIInstrument, Oscilloscope):

    """
    The Tektronix DPO70000 series  is a multi-channel oscilloscope with analog
    bandwidths ranging up to 33GHz.

    This class inherits from `~instruments.generic_scpi.SCPIInstrument`.

    Example usage:

    >>> import instruments as ik
    >>> tek = ik.tektronix.TekDPO70000.open_tcpip("192.168.0.2", 8888)
    >>> [x, y] = tek.channel[0].read_waveform()
    """

    # CONSTANTS #

    # The number of horizontal and vertical divisions.
    HOR_DIVS = 10
    VERT_DIVS = 10

    # ENUMS #

    class AcquisitionMode(Enum):

        """
        Enum containing valid acquisition modes for the Tektronix 70000 series
        oscilloscopes.
        """
        sample = "SAM"
        peak_detect = "PEAK"
        hi_res = "HIR"
        average = "AVE"
        waveform_db = "WFMDB"
        envelope = "ENV"

    class AcquisitionState(Enum):

        """
        Enum containing valid acquisition states for the Tektronix 70000 series
        oscilloscopes.
        """
        on = 'ON'
        off = 'OFF'
        run = 'RUN'
        stop = 'STOP'

    class StopAfter(Enum):

        """
        Enum containing valid stop condition modes for the Tektronix 70000
        series oscilloscopes.
        """
        run_stop = 'RUNST'
        sequence = 'SEQ'

    class SamplingMode(Enum):

        """
        Enum containing valid sampling modes for the Tektronix 70000
        series oscilloscopes.
        """
        real_time = "RT"
        equivalent_time_allowed = "ET"
        interpolation_allowed = "IT"

    class HorizontalMode(Enum):

        """
        Enum containing valid horizontal scan modes for the Tektronix 70000
        series oscilloscopes.
        """
        auto = "AUTO"
        constant = "CONST"
        manual = "MAN"

    class WaveformEncoding(Enum):

        """
        Enum containing valid waveform encoding modes for the Tektronix 70000
        series oscilloscopes.
        """
        # NOTE: For some reason, it uses the full names here instead of
        # returning the mneonics listed in the manual.
        ascii = "ASCII"
        binary = "BINARY"

    class BinaryFormat(Enum):

        """
        Enum containing valid binary formats for the Tektronix 70000
        series oscilloscopes (int, unsigned-int, floating-point).
        """
        int = "RI"
        uint = "RP"
        float = "FP"  # Single-precision!

    class ByteOrder(Enum):

        """
        Enum containing valid byte order (big-/little-endian) for the
        Tektronix 70000 series oscilloscopes.
        """
        little_endian = "LSB"
        big_endian = "MSB"

    class TriggerState(Enum):

        """
        Enum containing valid trigger states for the Tektronix 70000
        series oscilloscopes.
        """
        armed = "ARMED"
        auto = "AUTO"
        dpo = "DPO"
        partial = "PARTIAL"
        ready = "READY"

    # STATIC METHODS #

    @staticmethod
    def _dtype(binary_format, byte_order, n_bytes):
        return "{}{}{}".format({
            TekDPO70000.ByteOrder.big_endian: ">",
            TekDPO70000.ByteOrder.little_endian: "<"
        }[byte_order], {
            TekDPO70000.BinaryFormat.int: "i",
            TekDPO70000.BinaryFormat.uint: "u",
            TekDPO70000.BinaryFormat.float: "f"
        }[binary_format], n_bytes)

    # CLASSES #

    class DataSource(OscilloscopeDataSource):

        """
        Class representing a data source (channel, math, or ref) on the
        Tektronix DPO 70000.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `TekDPO70000` class.
        """

        def __init__(self, parent, name):
            super(TekDPO70000.DataSource, self).__init__(parent, name)

        @property
        def name(self):
            return self._name

        @abc.abstractmethod
        def _scale_raw_data(self, data):
            """
            Takes the int16 data and figures out how to make it unitful.
            """

        # pylint: disable=protected-access
        def read_waveform(self, bin_format=True):
            # We want to get the data back in binary, as it's just too much
            # otherwise.
            with self:
                self._parent.select_fastest_encoding()
                n_bytes = self._parent.outgoing_n_bytes
                dtype = self._parent._dtype(
                    self._parent.outgoing_binary_format,
                    self._parent.outgoing_byte_order,
                    n_bytes
                )
                self._parent.sendcmd("CURV?")
                raw = self._parent.binblockread(n_bytes, fmt=dtype)
                # Clear the queue by trying to read.
                # FIXME: this is a hack-y way of doing so.
                if hasattr(self._parent._file, 'flush_input'):
                    self._parent._file.flush_input()
                else:
                    self._parent._file.read()

                return self._scale_raw_data(raw)

        def __enter__(self):
            self._old_dsrc = self._parent.data_source
            if self._old_dsrc != self:
                # Set the new data source, and let __exit__ cleanup.
                self._parent.data_source = self
            else:
                # There's nothing to do or undo in this case.
                self._old_dsrc = None

        def __exit__(self, type, value, traceback):
            if self._old_dsrc is not None:
                self._parent.data_source = self._old_dsrc

    class Math(DataSource):

        """
        Class representing a math channel on the Tektronix DPO 70000.

        This class inherits from `TekDPO70000.DataSource`.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `TekDPO70000` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # 1-based.

            # Initialize as a data source with name MATH{}.
            super(TekDPO70000.Math, self).__init__(
                parent,
                "MATH{}".format(self._idx)
            )

        def sendcmd(self, cmd):
            """
            Wraps commands sent from property factories in this class with
            identifiers for the specified math channel.

            :param str cmd: Command to send to the instrument
            """
            self._parent.sendcmd("MATH{}:{}".format(self._idx, cmd))

        def query(self, cmd, size=-1):
            """
            Wraps queries sent from property factories in this class with
            identifiers for the specified math channel.

            :param str cmd: Query command to send to the instrument
            :param int size: Number of characters to read from the response.
                Default value reads until a termination character is found.
            :return: The query response
            :rtype: `str`
            """
            return self._parent.query("MATH{}:{}".format(self._idx, cmd), size)

        class FilterMode(Enum):
            """
            Enum containing valid filter modes for a math channel on the
            TekDPO70000 series oscilloscope.
            """
            centered = "CENT"
            shifted = "SHIF"

        class Mag(Enum):
            """
            Enum containing valid amplitude units for a math channel on the
            TekDPO70000 series oscilloscope.
            """
            linear = "LINEA"
            db = "DB"
            dbm = "DBM"

        class Phase(Enum):
            """
            Enum containing valid phase units for a math channel on the
            TekDPO70000 series oscilloscope.
            """
            degrees = "DEG"
            radians = "RAD"
            group_delay = "GROUPD"

        class SpectralWindow(Enum):
            """
            Enum containing valid spectral windows for a math channel on the
            TekDPO70000 series oscilloscope.
            """
            rectangular = "RECTANG"
            hamming = "HAMM"
            hanning = "HANN"
            kaiser_besse = "KAISERB"
            blackman_harris = "BLACKMANH"
            flattop2 = "FLATTOP2"
            gaussian = "GAUSS"
            tek_exponential = "TEKEXP"

        define = string_property(
            "DEF",
            doc="""
            A text string specifying the math to do, ex. CH1+CH2
            """
        )

        filter_mode = enum_property(
            "FILT:MOD",
            FilterMode
        )

        filter_risetime = unitful_property(
            "FILT:RIS",
            pq.second
        )

        label = string_property(
            "LAB:NAM",
            doc="""
            Just a human readable label for the channel.
            """
        )

        label_xpos = unitless_property(
            "LAB:XPOS",
            doc="""
            The x position, in divisions, to place the label.
            """
        )

        label_ypos = unitless_property(
            "LAB:YPOS",
            doc="""The y position, in divisions, to place the label.
            """
        )

        num_avg = unitless_property(
            "NUMAV",
            doc="""
            The number of acquisistions over which exponential averaging is
            performed.
            """
        )

        spectral_center = unitful_property(
            "SPEC:CENTER",
            pq.Hz,
            doc="""
            The desired frequency of the spectral analyzer output data span
            in Hz.
            """
        )

        spectral_gatepos = unitful_property(
            "SPEC:GATEPOS",
            pq.second,
            doc="""
            The gate position. Units are represented in seconds, with respect
            to trigger position.
            """
        )

        spectral_gatewidth = unitful_property(
            "SPEC:GATEWIDTH",
            pq.second,
            doc="""
            The time across the 10-division screen in seconds.
            """
        )

        spectral_lock = bool_property(
            "SPEC:LOCK",
            inst_true="ON",
            inst_false="OFF"
        )

        spectral_mag = unitful_property(
            "SPEC:MAG",
            Mag,
            doc="""
            Whether the spectral magnitude is linear, db, or dbm.
            """
        )

        spectral_phase = unitful_property(
            "SPEC:PHASE",
            Mag,
            doc="""
            Whether the spectral phase is degrees, radians, or group delay.
            """
        )

        spectral_reflevel = unitless_property(
            "SPEC:REFL",
            doc="""
            The value that represents the topmost display screen graticule.
            The units depend on spectral_mag.
            """
        )

        spectral_reflevel_offset = unitless_property(
            "SPEC:REFLEVELO"
        )

        spectral_resolution_bandwidth = unitful_property(
            "SPEC:RESB",
            pq.Hz,
            doc="""
            The desired resolution bandwidth value. Units are represented in
            Hertz.
            """
        )

        spectral_span = unitful_property(
            "SPEC:SPAN",
            pq.Hz,
            doc="""
            Specifies the frequency span of the output data vector from the
            spectral analyzer.
            """
        )

        spectral_suppress = unitless_property(
            "SPEC:SUPP",
            doc="""
            The magnitude level that data with magnitude values below this
            value are displayed as zero phase.
            """
        )

        spectral_unwrap = bool_property(
            "SPEC:UNWR",
            inst_true="ON",
            inst_false="OFF",
            doc="""
            Enables or disables phase wrapping.
            """
        )

        spectral_window = enum_property(
            "SPEC:WIN",
            SpectralWindow
        )

        threshhold = unitful_property(
            "THRESH",
            pq.volt,
            doc="""
            The math threshhold in volts
            """
        )

        unit_string = string_property(
            "UNITS",
            doc="""
            Just a label for the units...doesn"t actually change anything.
            """
        )

        autoscale = bool_property(
            "VERT:AUTOSC",
            inst_true="ON",
            inst_false="OFF",
            doc="""
            Enables or disables the auto-scaling of new math waveforms.
            """
        )

        position = unitless_property(
            "VERT:POS",
            doc="""
            The vertical position, in divisions from the center graticule.
            """
        )

        scale = unitful_property(
            "VERT:SCALE",
            pq.volt,
            doc="""
            The scale in volts per division. The range is from
            ``100e-36`` to ``100e+36``.
            """
        )

        def _scale_raw_data(self, data):
            # TODO: incorperate the unit_string somehow
            return self.scale * (
                (TekDPO70000.VERT_DIVS / 2) *
                data.astype(float) / (2**15) - self.position
            )

    class Channel(DataSource, OscilloscopeChannel):

        """
        Class representing a channel on the Tektronix DPO 70000.

        This class inherits from `TekDPO70000.DataSource`.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `TekDPO70000` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # 1-based.

            # Initialize as a data source with name CH{}.
            super(TekDPO70000.Channel, self).__init__(
                self._parent,
                "CH{}".format(self._idx)
            )

        def sendcmd(self, cmd):
            """
            Wraps commands sent from property factories in this class with
            identifiers for the specified channel.

            :param str cmd: Command to send to the instrument
            """
            self._parent.sendcmd("CH{}:{}".format(self._idx, cmd))

        def query(self, cmd, size=-1):
            """
            Wraps queries sent from property factories in this class with
            identifiers for the specified channel.

            :param str cmd: Query command to send to the instrument
            :param int size: Number of characters to read from the response.
                Default value reads until a termination character is found.
            :return: The query response
            :rtype: `str`
            """
            return self._parent.query("CH{}:{}".format(self._idx, cmd), size)

        class Coupling(Enum):
            """
            Enum containing valid coupling modes for the oscilloscope channel
            """
            ac = "AC"
            dc = "DC"
            dc_reject = "DCREJ"
            ground = "GND"

        coupling = enum_property(
            "COUP",
            Coupling,
            doc="""
            Gets/sets the coupling for the specified channel.

            Example usage:

            >>> import instruments as ik
            >>> inst = ik.tektronix.TekDPO70000.open_tcpip("192.168.0.1", 8080)
            >>> channel = inst.channel[0]
            >>> channel.coupling = channel.Coupling.ac
            """
        )

        bandwidth = unitful_property(
            'BAN',
            pq.Hz
        )

        deskew = unitful_property(
            'DESK',
            pq.second
        )

        termination = unitful_property(
            'TERM',
            pq.ohm
        )

        label = string_property(
            'LAB:NAM',
            doc="""
            Just a human readable label for the channel.
            """
        )

        label_xpos = unitless_property(
            'LAB:XPOS',
            doc="""
            The x position, in divisions, to place the label.
            """
        )

        label_ypos = unitless_property(
            'LAB:YPOS',
            doc="""
            The y position, in divisions, to place the label.
            """
        )

        offset = unitful_property(
            'OFFS',
            pq.volt,
            doc="""
            The vertical offset in units of volts. Voltage is given by
            ``offset+scale*(5*raw/2^15 - position)``.
            """
        )

        position = unitless_property(
            'POS',
            doc="""
            The vertical position, in divisions from the center graticule,
            ranging from ``-8`` to ``8``. Voltage is given by
            ``offset+scale*(5*raw/2^15 - position)``.
            """
        )

        scale = unitful_property(
            'SCALE',
            pq.volt,
            doc="""
            Vertical channel scale in units volts/division. Voltage is given
            by ``offset+scale*(5*raw/2^15 - position)``.
            """
        )

        def _scale_raw_data(self, data):
            return self.scale * (
                (TekDPO70000.VERT_DIVS / 2) *
                data.astype(float) / (2**15) - self.position
            ) + self.offset

    # PROPERTIES ##

    @property
    def channel(self):
        return ProxyList(self, self.Channel, range(4))

    @property
    def math(self):
        return ProxyList(self, self.Math, range(4))

    @property
    def ref(self):
        raise NotImplementedError

    # For some settings that probably won't be used that often, use
    # string_property instead of setting up an enum property.
    acquire_enhanced_enob = string_property(
        'ACQ:ENHANCEDE',
        bookmark_symbol='',
        doc="""
        Valid values are AUTO and OFF.
        """
    )

    acquire_enhanced_state = bool_property(
        'ACQ:ENHANCEDE:STATE',
        inst_false='0',  # TODO: double check that these are correct
        inst_true='1'
    )

    acquire_interp_8bit = string_property(
        'ACQ:INTERPE',
        bookmark_symbol='',
        doc="""
        Valid values are AUTO, ON and OFF.
        """
    )

    acquire_magnivu = bool_property(
        'ACQ:MAG',
        inst_true='ON',
        inst_false='OFF'
    )

    acquire_mode = enum_property(
        'ACQ:MOD',
        AcquisitionMode
    )

    acquire_mode_actual = enum_property(
        'ACQ:MOD:ACT',
        AcquisitionMode,
        readonly=True
    )

    acquire_num_acquisitions = int_property(
        'ACQ:NUMAC',
        readonly=True,
        doc="""
        The number of waveform acquisitions that have occurred since starting
        acquisition with the ACQuire:STATE RUN command
        """
    )

    acquire_num_avgs = int_property(
        'ACQ:NUMAV',
        doc="""
        The number of waveform acquisitions to average.
        """
    )

    acquire_num_envelop = int_property(
        'ACQ:NUME',
        doc="""
        The number of waveform acquisitions to be enveloped
        """
    )

    acquire_num_frames = int_property(
        'ACQ:NUMFRAMESACQ',
        readonly=True,
        doc="""
        The number of frames acquired when in FastFrame Single Sequence and
        acquisitions are running.
        """
    )

    acquire_num_samples = int_property(
        'ACQ:NUMSAM',
        doc="""
        The minimum number of acquired samples that make up a waveform
        database (WfmDB) waveform for single sequence mode and Mask Pass/Fail
        Completion Test. The default value is 16,000 samples. The range is
        5,000 to 2,147,400,000 samples.
        """
    )

    acquire_sampling_mode = enum_property(
        'ACQ:SAMP',
        SamplingMode
    )

    acquire_state = enum_property(
        'ACQ:STATE',
        AcquisitionState,
        doc="""
        This command starts or stops acquisitions.
        """
    )

    acquire_stop_after = enum_property(
        'ACQ:STOPA',
        StopAfter,
        doc="""
        This command sets or queries whether the instrument continually
        acquires acquisitions or acquires a single sequence.
        """
    )

    data_framestart = int_property('DAT:FRAMESTAR')

    data_framestop = int_property('DAT:FRAMESTOP')

    data_start = int_property(
        'DAT:STAR',
        doc="""
        The first data point that will be transferred, which ranges from 1 to
        the record length.
        """
    )

    # TODO: Look into the following troublesome datasheet note: "When using the
    # CURVe command, DATa:STOP is ignored and WFMInpre:NR_Pt is used."
    data_stop = int_property(
        'DAT:STOP',
        doc="""
        The last data point that will be transferred.
        """
    )

    data_sync_sources = bool_property(
        'DAT:SYNCSOU',
        inst_true='ON',
        inst_false='OFF'
    )

    @property
    def data_source(self):
        """
        Gets/sets the data source for the oscilloscope. This will return
        the actual Channel/Math/DataSource object as if it was accessed
        through the usual `TekDPO70000.channel`, `TekDPO70000.math`, or
        `TekDPO70000.ref` properties.

        :type: `TekDPO70000.Channel` or `TekDPO70000.Math`
        """
        val = self.query('DAT:SOU?')
        if val[0:2] == 'CH':
            out = self.channel[int(val[2]) - 1]
        elif val[0:2] == 'MA':
            out = self.math[int(val[4]) - 1]
        elif val[0:2] == 'RE':
            out = self.ref[int(val[3]) - 1]
        else:
            raise NotImplementedError
        return out

    @data_source.setter
    def data_source(self, newval):
        if not isinstance(newval, self.DataSource):
            raise TypeError(
                "{} is not a valid data source.".format(type(newval)))
        self.sendcmd("DAT:SOU {}".format(newval.name))

        # Some Tek scopes require this after the DAT:SOU command, or else
        # they will stop responding.
        if not self._testing:
            time.sleep(0.02)

    horiz_acq_duration = unitful_property(
        'HOR:ACQDURATION',
        pq.second,
        readonly=True,
        doc="""
        The duration of the acquisition.
        """
    )

    horiz_acq_length = int_property(
        'HOR:ACQLENGTH',
        readonly=True,
        doc="""
        The record length.
        """
    )

    horiz_delay_mode = bool_property(
        'HOR:DEL:MOD',
        inst_true='1',
        inst_false='0'
    )

    horiz_delay_pos = unitful_property(
        'HOR:DEL:POS',
        pq.percent,
        doc="""
        The percentage of the waveform that is displayed left of the center
        graticule.
        """
    )

    horiz_delay_time = unitful_property(
        'HOR:DEL:TIM',
        pq.second,
        doc="""
        The base trigger delay time setting.
        """
    )

    horiz_interp_ratio = unitless_property(
        'HOR:MAI:INTERPR',
        readonly=True,
        doc="""
        The ratio of interpolated points to measured points.
        """
    )

    horiz_main_pos = unitful_property(
        'HOR:MAI:POS',
        pq.percent,
        doc="""
        The percentage of the waveform that is displayed left of the center
        graticule.
        """
    )

    horiz_unit = string_property('HOR:MAI:UNI')

    horiz_mode = enum_property(
        'HOR:MODE',
        HorizontalMode
    )

    horiz_record_length_lim = int_property(
        'HOR:MODE:AUTO:LIMIT',
        doc="""
        The recond length limit in samples.
        """
    )

    horiz_record_length = int_property(
        'HOR:MODE:RECO',
        doc="""
        The recond length in samples. See `horiz_mode`; manual mode lets you
        change the record length, while the length is readonly for auto and
        constant mode.
        """
    )

    horiz_sample_rate = unitful_property(
        'HOR:MODE:SAMPLER',
        pq.Hz,
        doc="""
        The sample rate in samples per second.
        """
    )

    horiz_scale = unitful_property(
        'HOR:MODE:SCA',
        pq.second,
        doc="""
        The horizontal scale in seconds per division. The horizontal scale is
        readonly when `horiz_mode` is manual.
        """
    )

    horiz_pos = unitful_property(
        'HOR:POS',
        pq.percent,
        doc="""
        The position of the trigger point on the screen, left is 0%, right
        is 100%.
        """
    )

    horiz_roll = string_property(
        'HOR:ROLL',
        bookmark_symbol='',
        doc="""
        Valid arguments are AUTO, OFF, and ON.
        """
    )

    trigger_state = enum_property(
        'TRIG:STATE',
        TriggerState
    )

    # Waveform Transfer Properties
    outgoing_waveform_encoding = enum_property(
        'WFMO:ENC',
        WaveformEncoding,
        doc="""
        Controls the encoding used for outgoing waveforms (instrument → host).
        """
    )

    outgoing_binary_format = enum_property(
        "WFMO:BN_F",
        BinaryFormat,
        doc="""
        Controls the data type of samples when transferring waveforms from
        the instrument to the host using binary encoding.
        """
    )

    outgoing_byte_order = enum_property(
        "WFMO:BYT_O",
        ByteOrder,
        doc="""
        Controls whether binary data is returned in little or big endian.
        """
    )

    outgoing_n_bytes = int_property(
        "WFMO:BYT_N",
        valid_set=set((1, 2, 4, 8)),
        doc="""
        The number of bytes per sample used in representing outgoing
        waveforms in binary encodings.

        Must be either 1, 2, 4 or 8.
        """
    )

    # METHODS #

    def select_fastest_encoding(self):
        """
        Sets the encoding for data returned by this instrument to be the
        fastest encoding method consistent with the current data source.
        """
        self.sendcmd("DAT:ENC FAS")

    def force_trigger(self):
        """
        Forces a trigger event to happen for the oscilloscope.
        """
        self.sendcmd('TRIG FORC')

    # TODO: consider moving the next few methods to Oscilloscope.
    def run(self):
        """
        Enables the trigger for the oscilloscope.
        """
        self.sendcmd(":RUN")

    def stop(self):
        """
        Disables the trigger for the oscilloscope.
        """
        self.sendcmd(":STOP")
