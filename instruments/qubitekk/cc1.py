#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Qubitekk CC1 Coincidence Counter instrument.

CC1 Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range, map

from enum import Enum
import quantities as pq

from instruments.generic_scpi.scpi_instrument import SCPIInstrument
from instruments.util_fns import (
    ProxyList, assume_units, split_unit_str
)

# CLASSES #####################################################################


class CC1(SCPIInstrument):

    """
    The CC1 is a hand-held coincidence counter.

    It has two setting values, the dwell time and the coincidence window. The
    coincidence window determines the amount of time (in ns) that the two
    detections may be from each other and still be considered a coincidence.
    The dwell time is the amount of time that passes before the counter will
    send the clear signal.

    More information can be found at :
    http://www.qubitekk.com
    """

    def __init__(self, filelike):
        super(CC1, self).__init__(filelike)
        self.terminator = "\n"
        self._channel_count = 3
        self._firmware = None
        self._ack_on = False
        self.sendcmd(":ACKN OF")
        # a readline is required because if the firmware is prior to 2.2,
        # the cc1 will respond with 'Unknown Command'. After
        # 2.2, it will either respond by acknowledging the command (turning
        # acknowledgements off does not take place until after the current
        # exchange has been completed), or not acknowledging it (if the
        # acknowledgements are off). The try/except block is required to
        # handle the case in which acknowledgements are off.
        try:
            self.read(-1)
        except OSError:
            pass
        _ = self.firmware  # prime the firmware

        if self.firmware[0] >= 2 and self.firmware[1] > 1:
            self._bool = ("ON", "OFF")
            self._set_fmt = ":{}:{}"
            self.TriggerMode = self._TriggerModeNew

        else:
            self._bool = ("1", "0")
            self._set_fmt = ":{} {}"
            self.TriggerMode = self._TriggerModeOld

    def _ack_expected(self, msg=""):
        return msg if self._ack_on and self.firmware[0] >= 2 and \
                      self.firmware[1] > 1 else None

    # ENUMS #

    class _TriggerModeNew(Enum):
        """
        Enum containing valid trigger modes for the CC1
        """
        continuous = "MODE CONT"
        start_stop = "MODE STOP"

    class _TriggerModeOld(Enum):
        """
        Enum containing valid trigger modes for the CC1
        """
        continuous = "0"
        start_stop = "1"

    # INNER CLASSES #

    class Channel(object):

        """
        Class representing a channel on the Qubitekk CC1.
        """

        __CHANNEL_NAMES = {
            1: 'C1',
            2: 'C2',
            3: 'CO'
        }

        def __init__(self, cc1, idx):
            self._cc1 = cc1
            # Use zero-based indexing for the external API, but one-based
            # for talking to the instrument.
            self._idx = idx + 1
            self._chan = self.__CHANNEL_NAMES[self._idx]
            self._count = 0

        # PROPERTIES #

        @property
        def count(self):
            """
            Gets the counts of this channel.

            :rtype: `int`
            """
            count = self._cc1.query("COUN:{0}?".format(self._chan))
            # FIXME: Does this property actually work? The try block seems
            # wrong.
            try:
                count = int(count)
            except ValueError:  # pragma: no cover
                count = None
                while count is None:
                    # try to read again
                    try:
                        count = int(self._cc1.read(-1))
                    except ValueError:
                        count = None
            self._count = count
            return self._count

    # PROPERTIES #

    @property
    def acknowledge(self):
        """
        Gets/sets the acknowledge message state. If True, the CC1 will echo
        back every command sent, then print the response (either Unable to
        comply, Unknown command or the response to a query). If False,
        the CC1 will only print the response.

        :units: None
        :type: boolean
        """
        return self._ack_on

    @acknowledge.setter
    def acknowledge(self, new_val):
        if self.firmware[0] >= 2 and self.firmware[1] > 1:
            if self._ack_on and not new_val:
                self.sendcmd(":ACKN OF")
                self._ack_on = False
            elif not self._ack_on and new_val:
                self.sendcmd(":ACKN ON")
                self._ack_on = True
        else:
            raise NotImplementedError("Acknowledge message not implemented in "
                                      "this version.")

    @property
    def gate(self):
        """
        Gets/sets the gate enable status

        :type: `bool`
        """
        return self.query("GATE?").strip() == self._bool[0]

    @gate.setter
    def gate(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Bool properties must be specified with a "
                            "boolean value")
        self.sendcmd(
            self._set_fmt.format("GATE", self._bool[0] if newval else self._bool[1])
        )

    @property
    def subtract(self):
        """
        Gets/sets the subtract enable status

        :type: `bool`
        """
        return self.query("SUBT?").strip() == self._bool[0]

    @subtract.setter
    def subtract(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Bool properties must be specified with a "
                            "boolean value")
        self.sendcmd(
            self._set_fmt.format("SUBT", self._bool[0] if newval else self._bool[1])
        )

    @property
    def trigger_mode(self):
        """
        Gets/sets the trigger mode setting for the CC1. This can be set to
        ``continuous`` or ``start/stop`` modes.

        :type: `CC1.TriggerMode`
        """
        return self.TriggerMode(self.query("TRIG?").strip())

    @trigger_mode.setter
    def trigger_mode(self, newval):
        try:  # First assume newval is Enum.value
            newval = self.TriggerMode[newval]
        except KeyError:  # Check if newval is Enum.name instead
            try:
                newval = self.TriggerMode(newval)
            except ValueError:
                raise ValueError("Enum property new value not in enum.")
        self.sendcmd(self._set_fmt.format("TRIG", self.TriggerMode(newval).value))

    @property
    def window(self):
        """
        Gets/sets the length of the coincidence window between the two signals.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units nanoseconds.
        :type: `~quantities.Quantity`
        """
        return pq.Quantity(*split_unit_str(self.query("WIND?"), "ns"))

    @window.setter
    def window(self, new_val):
        new_val_mag = int(assume_units(new_val, pq.ns).rescale(pq.ns).magnitude)
        if new_val_mag < 0 or new_val_mag > 7:
            raise ValueError("Window is out of range.")
        # window must be an integer!
        self.sendcmd(":WIND {}".format(new_val_mag))

    @property
    def delay(self):
        """
        Get/sets the delay value (in nanoseconds) on Channel 1.

        When setting, ``N`` may be ``0, 2, 4, 6, 8, 10, 12, or 14ns``.

        :rtype: quantities.ns
        :return: the delay value
        """
        return pq.Quantity(*split_unit_str(self.query("DELA?"), "ns"))

    @delay.setter
    def delay(self, new_val):
        new_val = assume_units(new_val, pq.ns).rescale(pq.ns)
        if new_val < 0*pq.ns or new_val > 14*pq.ns:
            raise ValueError("New delay value is out of bounds.")
        if new_val.magnitude % 2 != 0:
            raise ValueError("New magnitude must be an even number")
        self.sendcmd(":DELA "+str(int(new_val.magnitude)))

    @property
    def dwell_time(self):
        """
        Gets/sets the length of time before a clear signal is sent to the
        counters.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units seconds.
        :type: `~quantities.Quantity`
        """
        # the older versions of the firmware erroneously report the units of the
        # dwell time as being seconds rather than ms
        dwell_time = pq.Quantity(*split_unit_str(self.query("DWEL?"), "s"))
        if self.firmware[0] <= 2 and self.firmware[1] <= 1:
            return dwell_time/1000.0
        else:
            return dwell_time

    @dwell_time.setter
    def dwell_time(self, new_val):
        new_val_mag = assume_units(new_val, pq.s).rescale(pq.s).magnitude
        if new_val_mag < 0:
            raise ValueError("Dwell time cannot be negative.")
        self.sendcmd(":DWEL {}".format(new_val_mag))

    @property
    def firmware(self):
        """
        Gets the firmware version

        :rtype: `tuple`(Major:`int`, Minor:`int`, Patch`int`)
        """
        # the firmware is assumed not to change while the device is active
        # firmware is stored locally as it will be gotten often
        # pylint: disable=no-member
        if self._firmware is None:
            while self._firmware is None:
                self._firmware = self.query("FIRM?")
                if self._firmware.find("Unknown") >= 0:
                    self._firmware = None
                else:
                    value = self._firmware.replace("Firmware v", "").split(".")
                    if len(value) < 3:
                        for _ in range(3-len(value)):
                            value.append(0)
                    value = tuple(map(int, value))
                    self._firmware = value
        return self._firmware

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        For instance, this would print the counts of the first channel::

        >>> cc = ik.qubitekk.CC1.open_serial('COM8', 19200, timeout=1)
        >>> print(cc.channel[0].count)

        :rtype: `CC1.Channel`
        """
        return ProxyList(self, CC1.Channel, range(self._channel_count))

    # METHODS #

    def clear_counts(self):
        """
        Clears the current total counts on the counters.
        """
        self.sendcmd("CLEA")
