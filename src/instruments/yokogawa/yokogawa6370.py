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

        def data(self, bin_format=True):
            cmd = f":TRAC:Y? {self._name}"
            self._parent.sendcmd(cmd)
            data = self._parent.binblockread(data_width=8, fmt="<d")
            self._parent._file.read_raw(1)  # pylint: disable=protected-access
            return data

        def wavelength(self, bin_format=True):
            cmd = f":TRAC:X? {self._name}"
            self._parent.sendcmd(cmd)
            data = self._parent.binblockread(data_width=8, fmt="<d")
            self._parent._file.read_raw(1)  # pylint: disable=protected-access
            return data

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

    active_trace = enum_property(
        ":TRAC:ACTIVE",
        Traces,
        doc="""
        The active trace of the OSA of enum Yokogawa6370.Traces. Determines the
        result of Yokogawa6370.data() and Yokogawa6370.wavelength().""",
    )

    # METHODS #

    def data(self):
        """
        Function to query the active Trace data of the OSA.
        """
        return self.channel[self.active_trace].data()

    def wavelength(self):
        """
        Query the wavelength axis of the active trace.
        """
        return self.channel[self.active_trace].wavelength()

    def start_sweep(self):
        """
        Triggering function for the Yokogawa 6370.

        After changing the sweep mode, the device needs to be triggered before it will update.
        """
        self.sendcmd("*CLS;:init")
