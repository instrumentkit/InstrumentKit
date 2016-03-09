#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# cc1.py: Class for the Qubitekk Coincidence Counter instrument
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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
# CC1 Class contributed by Catherine Holloway.
##

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

import quantities as pq
from enum import IntEnum, Enum

from instruments.generic_scpi.scpi_instrument import SCPIInstrument
from instruments.util_fns import ProxyList, assume_units, split_unit_str, \
    bool_property, enum_property


def qubitekk_check_unknown(response):
    """
    Check whether the command was understood by the CC1
    :param response: the string received from the device
    :type response: str
    :return: True if the command was understood
    """
    if "Unknown command" == response.strip():
        return False
    else:
        return True


class TriggerModeInt(Enum):
    continuous = "0"
    start_stop = "1"


class TriggerMode(Enum):
    continuous = "MODE CONT"
    start_stop = "MODE STOP"


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

    _sep = ":"
    _bool = ("ON", "OFF")
    _trig_bool = TriggerMode

    def __init__(self, filelike):
        super(CC1, self).__init__(filelike)
        self.terminator = "\n"
        self.channel_count = 3
        self._firmware = None

    gate = bool_property("GATE", inst_true=_bool[0], inst_false=_bool[1],
                             set_fmt=":{}"+_sep+"{}")
    subtract = bool_property("SUBT", inst_true=_bool[0], inst_false=_bool[1],
                                 set_fmt=":{}"+_sep+"{}")
    trigger = enum_property("TRIG", enum=_trig_bool,
                                set_fmt=":{}"+_sep+"{}")
    # INNER CLASSES ##

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

            
        # PROPERTIES ##
        
        @property
        def count(self):
            """
            Gets the counts of this channel.
            
            :rtype: `int`
            """
            count = self._cc1.query("COUN:{0}?".format(self._chan))
            try:
                count = int(count)
            except ValueError:
                count = None
                while count is None:
                    # try to read again
                    try:
                        count = int(self._file.read(-1))
                    except ValueError:
                        count = None
            self._count = count
            return self._count



    # PROPERTIES #
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
        Get the delay value (in nanoseconds) on Channel 1. N may be 0, 2, 4, 6, 8, 10, 12, or 14ns.
        :rtype: quantities.ns
        :return: the delay value
        """
        return pq.Quantity(*split_unit_str(self.query("DELA?"), "ns"))

    @delay.setter
    def delay(self, new_val):
        """
        Set the delay value (in nanoseconds) on Channel 1. N may be 0, 2, 4, 6, 8, 10, 12, or 14ns.
        """
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
        if self.firmware.find("v2.001") >= 0:
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
        # the firmware is assumed not to change while the device is active
        # firmware is stored locally as it will be gotten often
        if self._firmware is None:
            while self._firmware is None:
                self._firmware = self.query("FIRM?")
                if self._firmware.find("Unknown") >= 0:
                    self._firmware = None
        return self._firmware



    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        For instance, this would print the counts of the first channel::

        >>> cc = ik.qubitekk.CC1.open_serial('COM8', 19200, timeout=1)
        >>> print cc.channel[0].count

        :rtype: `CC1.Channel`
        """

        return ProxyList(self, CC1.Channel, range(self.channel_count))


    # METHODS #
    def clear_counts(self):
        """
        Clears the current total counts on the counters.
        """
        self.sendcmd("CLEA")


class CC1v2001(CC1):
    """
    Use this class for older versions of the CC1 firmware
    """
    _sep = " "
    _bool = ("1", "0")
    _trig_bool = TriggerModeInt

    def __init__(self, filelike):
        super(CC1v2001, self).__init__(filelike)

    gate = bool_property("GATE", inst_true=_bool[0], inst_false=_bool[1],
                             set_fmt=":{}"+_sep+"{}")
    subtract = bool_property("SUBT", inst_true=_bool[0], inst_false=_bool[1],
                                 set_fmt=":{}"+_sep+"{}")
    trigger = enum_property("TRIG", enum=_trig_bool, set_fmt=":{}"+_sep+"{}")
