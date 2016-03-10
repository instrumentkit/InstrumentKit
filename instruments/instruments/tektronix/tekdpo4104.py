#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Tektronix DPO 4104 oscilloscope
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from time import sleep
from builtins import range, map

from enum import Enum
import numpy as np

from instruments.abstract_instruments import (
    OscilloscopeChannel,
    OscilloscopeDataSource,
    Oscilloscope,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList

# FUNCTIONS ###################################################################


def _parent_property(prop_name, doc=""):

    def getter(self):  # pylint: disable=missing-docstring
        with self:
            # pylint: disable=protected-access
            return getattr(self._tek, prop_name)

    # pylint: disable=missing-docstring,unused-argument
    def setter(self, newval):
        with self:
            # pylint: disable=protected-access
            setattr(self._tek, prop_name, doc)

    return property(getter, setter, doc=doc)

# CLASSES #####################################################################


class _TekDPO4104DataSource(OscilloscopeDataSource):

    """
    Class representing a data source (channel, math, or ref) on the Tektronix
    DPO 4104.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `TekDPO4104` class.
    """

    def __init__(self, tek, name):
        super(_TekDPO4104DataSource, self).__init__(tek, name)
        self._tek = self._parent

    @property
    def name(self):
        """
        Gets the name of this data source, as identified over SCPI.

        :type: `str`
        """
        return self._name

    def __enter__(self):
        self._old_dsrc = self._tek.data_source
        if self._old_dsrc != self:
            # Set the new data source, and let __exit__ cleanup.
            self._tek.data_source = self
        else:
            # There"s nothing to do or undo in this case.
            self._old_dsrc = None

    def __exit__(self, type, value, traceback):
        if self._old_dsrc is not None:
            self._tek.data_source = self._old_dsrc

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return other.name == self.name

    def read_waveform(self, bin_format=True):
        """
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the
        oscilloscope, it unpacks the data and scales it accordingly.
        Supports both ASCII and binary waveform transfer.

        Function returns a tuple (x,y), where both x and y are numpy arrays.

        :param bool bin_format: If `True`, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.
        """

        # Set the acquisition channel
        with self:

            # TODO: move this out somewhere more appropriate.
            old_dat_stop = self._tek.query("DAT:STOP?")
            self._tek.sendcmd("DAT:STOP {}".format(10**7))

            if not bin_format:
                # Set data encoding format to ASCII
                self._tek.sendcmd("DAT:ENC ASCI")
                sleep(0.02)  # Work around issue with 2.48 firmware.
                raw = self._tek.query("CURVE?")
                raw = raw.split(",")  # Break up comma delimited string
                raw = map(float, raw)  # Convert each list element to int
                raw = np.array(raw)  # Convert into numpy array
            else:
                # Set encoding to signed, big-endian
                self._tek.sendcmd("DAT:ENC RIB")
                sleep(0.02)  # Work around issue with 2.48 firmware.
                data_width = self._tek.data_width
                self._tek.sendcmd("CURVE?")
                # Read in the binary block, data width of 2 bytes.
                raw = self._tek.binblockread(data_width)

            yoffs = self._tek.y_offset  # Retrieve Y offset
            ymult = self._tek.query("WFMP:YMU?")  # Retrieve Y multiplier
            yzero = self._tek.query("WFMP:YZE?")  # Retrieve Y zero

            y = ((raw - yoffs) * float(ymult)) + float(yzero)

            xzero = self._tek.query("WFMP:XZE?")  # Retrieve X zero
            xincr = self._tek.query("WFMP:XIN?")  # Retrieve X incr
            # Retrieve number of data points
            ptcnt = self._tek.query("WFMP:NR_P?")

            x = np.arange(float(ptcnt)) * float(xincr) + float(xzero)

            self._tek.sendcmd("DAT:STOP {}".format(old_dat_stop))

            return x, y

    y_offset = _parent_property("y_offset")


class _TekDPO4104Channel(_TekDPO4104DataSource, OscilloscopeChannel):

    """
    Class representing a channel on the Tektronix DPO 4104.

    This class inherits from `_TekDPO4104DataSource`.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `TekDPO4104` class.
    """

    def __init__(self, parent, idx):
        super(_TekDPO4104Channel, self).__init__(
            parent, "CH{}".format(idx + 1))
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekDPO4104.Coupling`
        """
        return TekDPO4104.Coupling(
            self._tek.query("CH{}:COUPL?".format(self._idx))
        )

    @coupling.setter
    def coupling(self, newval):
        if not isinstance(newval, TekDPO4104.Coupling):
            raise TypeError("Coupling setting must be a `TekDPO4104.Coupling`"
                            " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))


class TekDPO4104(SCPIInstrument, Oscilloscope):

    """
    The Tektronix DPO4104 is a multi-channel oscilloscope with analog
    bandwidths ranging from 100MHz to 1GHz.

    This class inherits from `~instruments.generic_scpi.SCPIInstrument`.

    Example usage:

    >>> import instruments as ik
    >>> tek = ik.tektronix.TekDPO4104.open_tcpip("192.168.0.2", 8888)
    >>> [x, y] = tek.channel[0].read_waveform()
    """

    # ENUMS #

    class Coupling(Enum):
        """
        Enum containing valid coupling modes for the channels on the
        Tektronix DPO 4104
        """
        ac = "AC"
        dc = "DC"
        ground = "GND"

    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets a specific oscilloscope channel object. The desired channel is
        specified like one would access a list.

        For instance, this would transfer the waveform from the first channel::

        >>> tek = ik.tektronix.TekDPO4104.open_tcpip("192.168.0.2", 8888)
        >>> [x, y] = tek.channel[0].read_waveform()

        :rtype: `_TekDPO4104Channel`
        """
        return ProxyList(self, _TekDPO4104Channel, range(4))

    @property
    def ref(self):
        """
        Gets a specific oscilloscope reference channel object. The desired
        channel is specified like one would access a list.

        For instance, this would transfer the waveform from the first channel::

        >>> import instruments as ik
        >>> tek = ik.tektronix.TekDPO4104.open_tcpip("192.168.0.2", 8888)
        >>> [x, y] = tek.ref[0].read_waveform()

        :rtype: `_TekDPO4104DataSource`
        """
        return ProxyList(
            self,
            lambda s, idx: _TekDPO4104DataSource(s, "REF{}".format(idx + 1)),
            range(4)
        )

    @property
    def math(self):
        """
        Gets a data source object corresponding to the MATH channel.

        :rtype: `_TekDPO4104DataSource`
        """
        return _TekDPO4104DataSource(self, "MATH")

    @property
    def data_source(self):
        """
        Gets/sets the the data source for waveform transfer.
        """
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return _TekDPO4104Channel(self, int(name[2:]) - 1)
        else:
            return _TekDPO4104DataSource(self, name)

    @data_source.setter
    def data_source(self, newval):
        # TODO: clean up type-checking here.
        if not isinstance(newval, str):
            if hasattr(newval, "value"):  # Is an enum with a value.
                newval = newval.value
            elif hasattr(newval, "name"):  # Is a datasource with a name.
                newval = newval.name
        self.sendcmd("DAT:SOU {}".format(newval))
        sleep(0.01)  # Let the instrument catch up.

    @property
    def aquisition_length(self):
        """
        Gets/sets the aquisition length of the oscilloscope

        :type: `int`
        """
        return int(self.query("HOR:RECO?"))

    @aquisition_length.setter
    def aquisition_length(self, newval):
        self.sendcmd("HOR:RECO {}".format(newval))

    @property
    def aquisition_running(self):
        """
        Gets/sets the aquisition state of the attached instrument.
        This property is `True` if the aquisition is running,
        and is `False` otherwise.

        :type: `bool`
        """
        return bool(int(self.query("ACQ:STATE?").strip()))

    @aquisition_running.setter
    def aquisition_running(self, newval):
        self.sendcmd("ACQ:STATE {}".format(1 if newval else 0))

    @property
    def aquisition_continuous(self):
        """
        Gets/sets whether the aquisition is continuous ("run/stop mode")
        or whether aquisiton halts after the next sequence ("single mode").

        :type: `bool`
        """
        return self.query("ACQ:STOPA?").strip().startswith("RUNST")

    @aquisition_continuous.setter
    def aquisition_continuous(self, newval):
        self.sendcmd("ACQ:STOPA {}".format("RUNST" if newval else "SEQ"))

    @property
    def data_width(self):
        """
        Gets/sets the data width (number of bytes wide per data point)
        for waveforms transfered to/from the oscilloscope.

        Valid widths are 1 or 2.

        :type: `int`
        """
        return int(self.query("DATA:WIDTH?"))

    @data_width.setter
    def data_width(self, newval):
        if int(newval) not in [1, 2]:
            raise ValueError("Only one or two byte-width is supported.")

        self.sendcmd("DATA:WIDTH {}".format(newval))

    # TODO: convert to read in unitful quantities.
    @property
    def y_offset(self):
        """
        Gets/sets the Y offset of the currently selected data source.
        """
        yoffs = float(self.query("WFMP:YOF?"))
        return yoffs

    @y_offset.setter
    def y_offset(self, newval):
        self.sendcmd("WFMP:YOF {}".format(newval))

    # METHODS #

    def force_trigger(self):
        """
        Forces a trigger event to occur on the attached oscilloscope.
        Note that this is distinct from the standard SCPI ``*TRG``
        functionality.
        """
        self.sendcmd("TRIG FORCE")
