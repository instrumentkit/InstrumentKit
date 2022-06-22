#!/usr/bin/env python
"""
Provides support for the Yokogawa 6370 optical spectrum analyzer.
"""

# IMPORTS #####################################################################


from enum import IntEnum, Enum

from instruments.units import ureg as u

from instruments.abstract_instruments import OpticalSpectrumAnalyzer
from instruments.util_fns import (
    enum_property,
    unitful_property,
    unitless_property,
    bounded_unitful_property,
    ProxyList,
    string_property,
)


# CLASSES #####################################################################


class Yokogawa6370(OpticalSpectrumAnalyzer):

    """
    The Yokogawa 6370 is a optical spectrum analyzer.
    Example usage:
    >>> import instruments as ik
    >>> import instruments.units as u
    >>> inst = ik.yokogawa.Yokogawa6370.open_visa('TCPIP0:192.168.0.35')
    >>> inst.start_wl = 1030e-9 * u.m
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set data Format to binary
        self.sendcmd(":FORMat:DATA REAL,64")  # TODO: Find out where we want this

    # INNER CLASSES #

    class Channel(OpticalSpectrumAnalyzer.Channel):

        """
        Class representing the channels on the Yokogawa 6370.
        This class inherits from `OpticalSpectrumAnalyzer.Channel`.
        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `Yokogawa6370` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._name = idx

        # METHODS #

        def _data(self, axis, limits=None, bin_format=True):
            """Get data of `axis`."""
            if limits is None:
                cmd = f":TRAC:{axis}? {self._name}"
            elif isinstance(limits, (tuple, list)) and len(limits) >= 2:
                cmd = f":TRAC:{axis}? {self._name},{limits[0]+1},{limits[1]+1}"
            else:
                raise AssertionError(
                    "limits has to be an list or tuple with at least two members"
                )
            self._parent.sendcmd(cmd)
            data = self._parent.binblockread(data_width=8, fmt="<d")
            self._parent._file.read_raw(1)  # pylint: disable=protected-access
            return data

        def data(self, limits=None, bin_format=True):
            """
            Return the trace's level data.

            :param limits: Range of samples to transfer. (0 to 50000)
            """
            return self._data("Y", limits=limits, bin_format=bin_format)

        def wavelength(self, limits=None, bin_format=True):
            """
            Return the trace's wavelength data.

            :param limits: Range of samples to transfer. (0 to 50000)
            """
            return self._data("X", limits=limits, bin_format=bin_format)

    # ENUMS #

    class SweepModes(IntEnum):
        """
        Enum containing valid output modes for the Yokogawa 6370
        """

        SINGLE = 1
        REPEAT = 2
        AUTO = 3

    class Traces(Enum):
        """
        Enum containing valid Traces for the Yokogawa 6370
        """

        A = "TRA"
        B = "TRB"
        C = "TRC"
        D = "TRD"
        E = "TRE"
        F = "TRF"
        G = "TRG"

    # PROPERTIES #

    # General

    id = string_property(
        "*IDN",
        doc="""
            Get the identification of the device.
            Output: 'Manufacturer,Product,SerialNumber,FirmwareVersion'
            Sample: 'YOKOGAWA,AQ6370D,90Y403996,02.08'
            """,
        readonly=True,
    )

    status = unitless_property(
        "*STB", doc="""The status byte of the device.""", readonly=True
    )

    operation_event = unitless_property(
        ":status:operation:event",
        doc="""
            All changes after the last readout. Readout clears the operation_event
            Bit 4: Autosweep
            Bit 3: Calibration/Alignment
            Bit 2: Copy/File
            Bit 1: Program
            Bit 0: Sweep finished.
        """,
        readonly=True,
    )

    @property
    def channel(self):
        """
        Gets the specific channel object.
        This channel is accessed as a list in the following manner::
        >>> import instruments as ik
        >>> osa = ik.yokogawa.Yokogawa6370.open_gpibusb('/dev/ttyUSB0')
        >>> dat = osa.channel["A"].data # Gets the data of channel 0
        :rtype: `list`[`~Yokogawa6370.Channel`]
        """
        return ProxyList(self, Yokogawa6370.Channel, Yokogawa6370.Traces)

    # Sweep

    start_wl, start_wl_min, start_wl_max = bounded_unitful_property(
        ":SENS:WAV:STAR",
        u.meter,
        doc="""
        The start wavelength in m.
        """,
        valid_range=(600e-9, 1700e-9),
    )

    stop_wl, stop_wl_min, stop_wl_max = bounded_unitful_property(
        ":SENS:WAV:STOP",
        u.meter,
        doc="""
        The stop wavelength in m.
        """,
        valid_range=(600e-9, 1700e-9),
    )

    bandwidth = unitful_property(
        ":SENS:BAND:RES",
        u.meter,
        doc="""
        The bandwidth in m.
        """,
    )

    span = unitful_property(
        ":SENS:WAV:SPAN",
        u.meter,
        doc="""
        A floating point property that controls the wavelength span in m.
        """,
    )

    center_wl = unitful_property(
        ":SENS:WAV:CENT",
        u.meter,
        doc="""
         A floating point property that controls the center wavelength m.
        """,
    )

    points = unitless_property(
        ":SENS:SWE:POIN",
        doc="""
        An integer property that controls the number of points in a trace.
        """,
    )

    sweep_mode = enum_property(
        ":INIT:SMOD",
        SweepModes,
        input_decoration=int,
        doc="""
        A property to control the Sweep Mode as one of Yokogawa6370.SweepMode.
        Effective only after a self.start_sweep().""",
    )

    # Analysis

    # Traces

    active_trace = enum_property(
        ":TRAC:ACTIVE",
        Traces,
        doc="""
        The active trace of the OSA of enum Yokogawa6370.Traces. Determines the
        result of Yokogawa6370.data() and Yokogawa6370.wavelength().""",
    )

    # METHODS #

    def data(self, limits=None):
        """
        Function to query the active Trace data of the OSA.
        """
        return self.channel[self.active_trace].data(limits=limits)

    def wavelength(self, limits=None):
        """
        Query the wavelength axis of the active trace.
        """
        return self.channel[self.active_trace].wavelength(limits=limits)

    def analysis(self):
        """Get the analysis data."""
        return [float(x) for x in self.query(":CALC:DATA?").split(",")]

    def start_sweep(self):
        """
        Triggering function for the Yokogawa 6370.
        After changing the sweep mode, the device needs to be triggered before
        it will update.
        """
        self.sendcmd("*CLS;:init")

    def abort(self):
        """Abort a running sweep or calibration etc."""
        self.sendcmd(":ABORT")

    def clear(self):
        """Clear status registers."""
        self.sendcmd("*CLS")
