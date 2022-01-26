#!/usr/bin/env python
"""
Provides support for the Tektronix TDS 224 oscilloscope
"""

# IMPORTS #####################################################################

import time

from enum import Enum

from instruments.abstract_instruments import Oscilloscope
from instruments.generic_scpi import SCPIInstrument
from instruments.optional_dep_finder import numpy
from instruments.util_fns import ProxyList
from instruments.units import ureg as u


# CLASSES #####################################################################


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
        super().__init__(filelike)
        self._file.timeout = 3 * u.second

    class DataSource(Oscilloscope.DataSource):
        """
        Class representing a data source (channel, math, or ref) on the Tektronix
        TDS 224.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TekTDS224` class.
        """

        def __init__(self, tek, name):
            super().__init__(tek, name)
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

            :rtype: `tuple`[`tuple`[`float`, ...], `tuple`[`float`, ...]]
                or if numpy is installed, `tuple`[`numpy.array`, `numpy.array`]
            """
            with self:

                if not bin_format:
                    self._tek.sendcmd("DAT:ENC ASCI")
                    # Set the data encoding format to ASCII
                    raw = self._tek.query("CURVE?")
                    raw = raw.split(",")  # Break up comma delimited string
                    if numpy:
                        raw = numpy.array(raw, dtype=numpy.float)  # Convert to ndarray
                    else:
                        raw = tuple(map(float, raw))
                else:
                    self._tek.sendcmd("DAT:ENC RIB")
                    # Set encoding to signed, big-endian
                    data_width = self._tek.data_width
                    self._tek.sendcmd("CURVE?")
                    raw = self._tek.binblockread(
                        data_width
                    )  # Read in the binary block,
                    # data width of 2 bytes

                    # pylint: disable=protected-access
                    self._tek._file.flush_input()  # Flush input buffer

                yoffs = self._tek.query(f"WFMP:{self.name}:YOF?")  # Retrieve Y offset
                ymult = self._tek.query(f"WFMP:{self.name}:YMU?")  # Retrieve Y multiply
                yzero = self._tek.query(f"WFMP:{self.name}:YZE?")  # Retrieve Y zero

                xzero = self._tek.query("WFMP:XZE?")  # Retrieve X zero
                xincr = self._tek.query("WFMP:XIN?")  # Retrieve X incr
                ptcnt = self._tek.query(
                    f"WFMP:{self.name}:NR_P?"
                )  # Retrieve number of data points

                if numpy:
                    x = numpy.arange(float(ptcnt)) * float(xincr) + float(xzero)
                    y = ((raw - float(yoffs)) * float(ymult)) + float(yzero)
                else:
                    x = tuple(
                        float(val) * float(xincr) + float(xzero)
                        for val in range(int(ptcnt))
                    )
                    y = tuple(
                        ((x - float(yoffs)) * float(ymult)) + float(yzero) for x in raw
                    )

                return x, y

    class Channel(DataSource, Oscilloscope.Channel):
        """
        Class representing a channel on the Tektronix TDS 224.

        This class inherits from `TekTDS224.DataSource`.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TekTDS224` class.
        """

        def __init__(self, parent, idx):
            super().__init__(parent, f"CH{idx + 1}")
            self._idx = idx + 1

        @property
        def coupling(self):
            """
            Gets/sets the coupling setting for this channel.

            :type: `TekTDS224.Coupling`
            """
            return TekTDS224.Coupling(self._tek.query(f"CH{self._idx}:COUPL?"))

        @coupling.setter
        def coupling(self, newval):
            if not isinstance(newval, TekTDS224.Coupling):
                raise TypeError(
                    f"Coupling setting must be a `TekTDS224.Coupling` value,"
                    f"got {type(newval)} instead."
                )
            self._tek.sendcmd(f"CH{self._idx}:COUPL {newval.value}")

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

        :rtype: `TekTDS224.Channel`
        """
        return ProxyList(self, self.Channel, range(4))

    @property
    def ref(self):
        """
        Gets a specific oscilloscope reference channel object. The desired
        channel is specified like one would access a list.

        For instance, this would transfer the waveform from the first channel::

        >>> import instruments as ik
        >>> tek = ik.tektronix.TekTDS224.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.ref[0].read_waveform()

        :rtype: `TekTDS224.DataSource`
        """
        return ProxyList(
            self, lambda s, idx: self.DataSource(s, f"REF{idx + 1}"), range(4)
        )

    @property
    def math(self):
        """
        Gets a data source object corresponding to the MATH channel.

        :rtype: `TekTDS224.DataSource`
        """
        return self.DataSource(self, "MATH")

    @property
    def data_source(self):
        """
        Gets/sets the the data source for waveform transfer.
        """
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return self.Channel(self, int(name[2:]) - 1)

        return self.DataSource(self, name)

    @data_source.setter
    def data_source(self, newval):
        # TODO: clean up type-checking here.
        if not isinstance(newval, str):
            if hasattr(newval, "value"):  # Is an enum with a value.
                newval = newval.value
            elif hasattr(newval, "name"):  # Is a datasource with a name.
                newval = newval.name
        self.sendcmd(f"DAT:SOU {newval}")
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

        self.sendcmd(f"DATA:WIDTH {newval}")

    def force_trigger(self):
        raise NotImplementedError
