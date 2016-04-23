#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Tektronix TDS 224 oscilloscope
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
import time

from builtins import range, map
from enum import Enum

import numpy as np
import quantities as pq

from instruments.abstract_instruments import (
    OscilloscopeChannel,
    OscilloscopeDataSource,
    Oscilloscope,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class _TekTDS224DataSource(OscilloscopeDataSource):

    """
    Class representing a data source (channel, math, or ref) on the Tektronix
    TDS 224.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `TekTDS224` class.
    """

    def __init__(self, tek, name):
        super(_TekTDS224DataSource, self).__init__(tek, name)
        self._tek = self._parent

    @property
    def name(self):
        """
        Gets the name of this data source, as identified over SCPI.

        :type: `str`
        """
        return self._name

    def read_waveform(self, bin_format=True):
        """
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the
        oscilloscope, it unpacks the data and scales it accordingly.

        Supports both ASCII and binary waveform transfer. For 2500 data
        points, with a width of 2 bytes, transfer takes approx 2 seconds for
        binary, and 7 seconds for ASCII over Galvant Industries' GPIBUSB
        adapter.

        Function returns a tuple (x,y), where both x and y are numpy arrays.

        :param bool bin_format: If `True`, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.

        :rtype: two item `tuple` of `numpy.ndarray`
        """
        with self:

            if not bin_format:
                self._tek.sendcmd('DAT:ENC ASCI')
                                  # Set the data encoding format to ASCII
                raw = self._tek.query('CURVE?')
                raw = raw.split(',')  # Break up comma delimited string
                raw = map(float, raw)  # Convert each list element to int
                raw = np.array(raw)  # Convert into numpy array
            else:
                self._tek.sendcmd('DAT:ENC RIB')
                                  # Set encoding to signed, big-endian
                data_width = self._tek.data_width
                self._tek.sendcmd('CURVE?')
                raw = self._tek.binblockread(
                    data_width)  # Read in the binary block,
                                                    # data width of 2 bytes

                # pylint: disable=protected-access
                self._tek._file.flush_input()  # Flush input buffer

            yoffs = self._tek.query(
                'WFMP:{}:YOF?'.format(self.name))  # Retrieve Y offset
            ymult = self._tek.query(
                'WFMP:{}:YMU?'.format(self.name))  # Retrieve Y multiply
            yzero = self._tek.query(
                'WFMP:{}:YZE?'.format(self.name))  # Retrieve Y zero

            y = ((raw - float(yoffs)) * float(ymult)) + float(yzero)

            xzero = self._tek.query('WFMP:XZE?')  # Retrieve X zero
            xincr = self._tek.query('WFMP:XIN?')  # Retrieve X incr
            ptcnt = self._tek.query(
                'WFMP:{}:NR_P?'.format(self.name))  # Retrieve number
                                                                  # of data
                                                                  # points

            x = np.arange(float(ptcnt)) * float(xincr) + float(xzero)

            return (x, y)


class _TekTDS224Channel(_TekTDS224DataSource, OscilloscopeChannel):

    """
    Class representing a channel on the Tektronix TDS 224.

    This class inherits from `_TekTDS224DataSource`.

    .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `TekTDS224` class.
    """

    def __init__(self, parent, idx):
        super(_TekTDS224Channel, self).__init__(parent, "CH{}".format(idx + 1))
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekTDS224.Coupling`
        """
        return TekTDS224.Coupling(
            self._tek.query("CH{}:COUPL?".format(self._idx))
        )

    @coupling.setter
    def coupling(self, newval):
        if not isinstance(newval, TekTDS224.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS224.Coupling`"
                            " value, got {} instead.".format(type(newval)))
        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))


class TekTDS224(SCPIInstrument, Oscilloscope):

    """
    The Tektronix TDS224 is a multi-channel oscilloscope with analog
    bandwidths of 100MHz.

    This class inherits from `~instruments.generic_scpi.SCPIInstrument`.

    Example usage:

    >>> import instruments as ik
    >>> tek = ik.tektronix.TekTDS224.open_gpibusb("/dev/ttyUSB0", 1)
    >>> [x, y] = tek.channel[0].read_waveform()
    """

    def __init__(self, filelike):
        super(TekTDS224, self).__init__(filelike)
        self._file.timeout = 3 * pq.second

    # ENUMS #

    class Coupling(Enum):
        """
        Enum containing valid coupling modes for the Tek TDS224
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

        >>> import instruments as ik
        >>> tek = ik.tektronix.TekTDS224.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.channel[0].read_waveform()

        :rtype: `_TekTDS224Channel`
        """
        return ProxyList(self, _TekTDS224Channel, range(4))

    @property
    def ref(self):
        """
        Gets a specific oscilloscope reference channel object. The desired
        channel is specified like one would access a list.

        For instance, this would transfer the waveform from the first channel::

        >>> import instruments as ik
        >>> tek = ik.tektronix.TekTDS224.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.ref[0].read_waveform()

        :rtype: `_TekTDS224DataSource`
        """
        return ProxyList(self,
                         lambda s, idx: _TekTDS224DataSource(
                             s, "REF{}".format(idx + 1)),
                         range(4))

    @property
    def math(self):
        """
        Gets a data source object corresponding to the MATH channel.

        :rtype: `_TekTDS224DataSource`
        """
        return _TekTDS224DataSource(self, "MATH")

    @property
    def data_source(self):
        """
        Gets/sets the the data source for waveform transfer.
        """
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return _TekTDS224Channel(self, int(name[2:]) - 1)
        else:
            return _TekTDS224DataSource(self, name)

    @data_source.setter
    def data_source(self, newval):
        # TODO: clean up type-checking here.
        if not isinstance(newval, str):
            if hasattr(newval, "value"):  # Is an enum with a value.
                newval = newval.value
            elif hasattr(newval, "name"):  # Is a datasource with a name.
                newval = newval.name
        self.sendcmd("DAT:SOU {}".format(newval))
        if not self._testing:
            time.sleep(0.01)  # Let the instrument catch up.

    @property
    def data_width(self):
        """
        Gets/sets the byte-width of the data points being returned by the
        instrument. Valid widths are ``1`` or ``2``.

        :type: `int`
        """
        return int(self.query("DATA:WIDTH?"))

    @data_width.setter
    def data_width(self, newval):
        if int(newval) not in [1, 2]:
            raise ValueError("Only one or two byte-width is supported.")

        self.sendcmd("DATA:WIDTH {}".format(newval))

    @property
    def force_trigger(self):
        raise NotImplementedError
