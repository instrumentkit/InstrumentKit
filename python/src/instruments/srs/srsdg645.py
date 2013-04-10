#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srsdg645.py: Class for communicating with the SRS DG645 DDG.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the GPIBUSB adapter project.
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

## ENUMS #######################################################################

class SRSDG645Channels(IntEnum):
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

class SRSDG645DisplayMode(IntEnum):
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

## CLASSES #####################################################################

class SRSDG645(SCPIInstrument):
    """
    Communicates with a Stanford Research Systems DG645 digital delay generator,
    using the SCPI commands documented in the `user's guide`_.

    .. _user's guide: http://www.thinksrs.com/downloads/PDFs/Manuals/DG645m.pdf
    """
                 
    # No __init__ needed.


    @property
    def display(self):
        """
        Gets/sets the front-panel display mode for the connected DDG.
        The mode is a tuple of the display mode and the channel.
        
        :type: `tuple` of an `SRSDG645DisplayMode` and an `SRSDG645Channels`
        """
        disp_mode, chan = map(int(self.query("DISP?").split(",")))
        return (SRSDG645DisplayMode(disp_mode), SRSDG645Channel(chan))
    @display.setter
    def display(self, newval):
        # TODO: check types here.
        self.sendcmd("DISP {0},{1}", *newval)
    
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
    
