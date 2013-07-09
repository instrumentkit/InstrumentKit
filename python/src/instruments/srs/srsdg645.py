#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srsdg645.py: Class for communicating with the SRS DG645 DDG.
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

from time import time, sleep

from flufl.enum import IntEnum

from contextlib import contextmanager

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.abstract_instruments.gi_gpib import GPIBWrapper
from instruments.util_fns import assume_units, ProxyList

## ENUMS #######################################################################



## CLASSES #####################################################################

class Channel(object):
    def __init__(self, ddg, chan):
        if not isinstance(ddg, SRSDG645):
            raise TypeError("Don't do that.")

        self._ddg = ddg
        self._chan = chan

    ## PROPERTIES ##

    @property
    def delay(self):
        """
        Gets/sets the delay of this channel.
        Formatted as a two-tuple of the reference and the delay time.
        For example, ``(SRSDG645.Channels.A, pq.Quantity(10, "ps"))``
        indicates a delay of 10 picoseconds from delay channel A.
        """
        resp = self._ddg.query("DLAY?{}".format(int(self._chan))).split(",")
        return (SRSDG645.Channels(int(resp[0])), pq.Quantity(float(resp[1]), "s"))
    @delay.setter
    def delay(self, newval):
        self._ddg.sendcmd("DLAY {},{},{}".format(
            int(self._chan),
            int(newval[0]),
            newval[1].rescale("s").magnitude
        ))

class SRSDG645(SCPIInstrument):
    """
    Communicates with a Stanford Research Systems DG645 digital delay generator,
    using the SCPI commands documented in the `user's guide`_.

    .. _user's guide: http://www.thinksrs.com/downloads/PDFs/Manuals/DG645m.pdf
    """
                 
    def __init__(self, filelike):
        super(SRSDG645, self).__init__(filelike)

        # This instrument requires stripping two characters.
        if isinstance(filelike, GPIBWrapper):
            filelike.strip = 2
    
    ## ENUMS ##
    
    class Channels(IntEnum):
        T0 = 0
        T1 = 1
        A  = 2
        B  = 3
        C  = 4
        D  = 5
        E  = 6
        F  = 7
        G  = 8
        H  = 9

    class DisplayMode(IntEnum):
        trigger_rate          = 0
        trigger_threshold     = 1
        trigger_single_shot   = 2
        trigger_line          = 3
        adv_triggering_enable = 4
        trigger_holdoff       = 5
        prescale_config       = 6
        burst_mode            = 7
        burst_delay           = 8
        burst_count           = 9
        burst_period          = 10
        channel_delay         = 11
        channel_levels        = 12
        channel_polarity      = 13
        burst_T0_config       = 14

    class TriggerSource(IntEnum):
        internal            = 0
        external_rising     = 1
        external_falling    = 2
        ss_external_rising  = 3
        ss_external_falling = 4
        single_shot         = 5
        line                = 6
        
    ## PROPERTIES ##

    @property
    def channel(self):
        return ProxyList(self, Channel, SRSDG645.Channels)

    @property
    def display(self):
        """
        Gets/sets the front-panel display mode for the connected DDG.
        The mode is a tuple of the display mode and the channel.
        
        :type: `tuple` of an `SRSDG645.DisplayMode` and an `SRSDG645.Channels`
        """
        disp_mode, chan = map(int, self.query("DISP?").split(","))
        return (SRSDG645.DisplayMode(disp_mode), SRSDG645.Channels(chan))
    @display.setter
    def display(self, newval):
        # TODO: check types here.
        self.sendcmd("DISP {0},{1}".format(*map(int, newval)))
    
    @property
    def enable_adv_triggering(self):
        """
        Gets/sets whether advanced triggering is enabled.
        
        :type: `bool`
        """
        return bool(int(self.query("ADVT?")))
    @enable_adv_triggering.setter
    def enable_adv_triggering(self, newval):
        self.sendcmd("ADVT {}".format(1 if newval else 0))

    @property
    def trigger_rate(self):
        """
        Gets/sets the rate of the internal trigger.

        :type: `~quantities.Quantity` or `float`
        :units: As passed or Hz if not specified.
        """
        return pq.Quantity(float(self.query("TRAT?")), pq.Hz)
    @trigger_rate.setter
    def trigger_rate(self, newval):
        newval = assume_units(newval, pq.Hz)
        self.sendcmd("TRAT {}".format(newval.rescale(pq.Hz).magnitude))

    @property
    def trigger_source(self):
        """
        Gets/sets the source for the trigger.

        :type: SRSDG645.TriggerSource
        """
        return SRSDG645.TriggerSource(int(self.query("TSRC?")))
    @trigger_source.setter
    def trigger_source(self, newval):
        self.sendcmd("TSRC {}".format(int(newval)))

    @property
    def holdoff(self):
        """
        Gets/sets the trigger holdoff time.

        :type: `~quantities.Quantity` or `float`
        :units: As passed, or s if not specified.
        """
        return pq.Quantity(float(self.query("HOLD?")), pq.s)
    @holdoff.setter
    def holdoff(self, newval):
        self.sendcmd("HOLD {}".format(newval.rescale(pq.s).magnitude))
        
