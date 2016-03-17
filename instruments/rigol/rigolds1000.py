#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for Rigol DS-1000 series oscilloscopes.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

from enum import Enum

from instruments.abstract_instruments import (
    Oscilloscope, OscilloscopeChannel, OscilloscopeDataSource
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList, bool_property, enum_property

# CLASSES #####################################################################


class RigolDS1000Series(SCPIInstrument, Oscilloscope):

    """
    The Rigol DS1000-series is a popular budget oriented oscilloscope
    that has featured wide adoption across hobbyist circles.

    .. warning:: This instrument is not complete, and probably not even
        functional!
    """

    # ENUMS #

    class AcquisitionType(Enum):
        """
        Enum containing valid acquisition types for the Rigol DS1000
        """
        normal = "NORM"
        average = "AVER"
        peak_detect = "PEAK"

    class Coupling(Enum):
        """
        Enum containing valid coupling modes for the Rigol DS1000
        """
        ac = "AC"
        dc = "DC"
        ground = "GND"

    # INNER CLASSES #

    class DataSource(OscilloscopeDataSource):
        """
        Class representing a data source (channel, math, or ref) on the
        Rigol DS1000

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `RigolDS1000Series` class.
        """

        def __init__(self, parent, name):
            super(RigolDS1000Series.DataSource, self).__init__(parent, name)

        @property
        def name(self):
            return self._name

        def read_waveform(self, bin_format=True):
            # TODO: add DIG, FFT.
            if self.name not in ["CHAN1", "CHAN2", "DIG", "MATH", "FFT"]:
                raise NotImplementedError("Rigol DS1000 series does not "
                                          "supportreading waveforms from "
                                          "{}.".format(self.name))
            self._parent.sendcmd(":WAV:DATA? {}".format(self.name))
            data = self._parent.binblockread(2)  # TODO: check width
            return data

    class Channel(DataSource, OscilloscopeChannel):
        """
        Class representing a channel on the Rigol DS1000.

        This class inherits from `~RigolDS1000Series.DataSource`.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `RigolDS1000Series` class.
        """
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # Rigols are 1-based.

            # Initialize as a data source with name CHAN{}.
            super(RigolDS1000Series.Channel, self).__init__(
                self._parent, "CHAN{}".format(self._idx))

        def sendcmd(self, cmd):
            """
            Passes a command from the `Channel` class to the parent
            `RigolDS1000Series`, appending the required channel identification.

            :param str cmd: The command string to send to the instrument
            """
            self._parent.sendcmd(":CHAN{}:{}".format(self._idx, cmd))

        def query(self, cmd):
            """
            Passes a command from the `Channel` class to the parent
            `RigolDS1000Series`, appending the required channel identification.

            :param str cmd: The command string to send to the instrument
            :return: The result as returned by the instrument
            :rtype: `str`
            """
            return self._parent.query(":CHAN{}:{}".format(self._idx, cmd))

        coupling = enum_property("COUP", lambda: RigolDS1000Series.Coupling)

        bw_limit = bool_property("BWL", "ON", "OFF")
        display = bool_property("DISP", "ON", "OFF")
        invert = bool_property("INV", "ON", "OFF")

        # TODO: :CHAN<n>:OFFset
        # TODO: :CHAN<n>:PROBe
        # TODO: :CHAN<n>:SCALe

        filter = bool_property("FILT", "ON", "OFF")

        # TODO: :CHAN<n>:MEMoryDepth

        vernier = bool_property("VERN", "ON", "OFF")

    # PROPERTIES #

    @property
    def channel(self):
        # Rigol DS1000 series oscilloscopes all have two channels,
        # according to the documentation.
        return ProxyList(self, self.Channel, range(2))

    @property
    def math(self):
        return self.DataSource(parent=self, name="MATH")

    @property
    def ref(self):
        return self.DataSource(parent=self, name="REF")

    acquire_type = enum_property(":ACQ:TYPE", AcquisitionType)
    # TODO: implement :ACQ:MODE. This is confusing in the documentation,
    # though.

    @property
    def acquire_averages(self):
        """
        Gets/sets the number of averages the oscilloscope should take per
        acquisition.

        :type: `int`
        """
        return int(self.query(":ACQ:AVER?"))

    @acquire_averages.setter
    def acquire_averages(self, newval):
        if newval not in [2**i for i in range(1, 9)]:
            raise ValueError(
                "Number of averages {} not supported by instrument; "
                "must be a power of 2 from 2 to 256.".format(newval)
            )
        self.sendcmd(":ACQ:AVER {}".format(newval))

    # TODO: implement :ACQ:SAMP in a meaningful way. This should probably be
    #       under Channel, and needs to be unitful.
    # TODO: I don't understand :ACQ:MEMD yet.

    # METHODS ##

    def force_trigger(self):
        self.sendcmd(":FORC")

    # TODO: consider moving the next few methods to Oscilloscope.
    def run(self):
        """
        Starts running the oscilloscope trigger.
        """
        self.sendcmd(":RUN")

    def stop(self):
        """
        Stops running the oscilloscope trigger.
        """
        self.sendcmd(":STOP")

    # TODO: unitful timebase!

    # FRONT-PANEL KEY EMULATION METHODS ##
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
        self.sendcmd(":KEY:FORC")
