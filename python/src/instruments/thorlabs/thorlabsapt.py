#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# thorlabsapt.py: Driver for the Thorlabs APT Controller.
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

from instruments.thorlabs import _abstract
from instruments.thorlabs import _packets

## CLASSES #####################################################################

class ThorLabsAPT(_abstract.ThorLabsInstrument):
    
    def identify(self):
        pkt = _packets.ThorLabsPacket(message_id=0x0223,
                                      param1=0x00,
                                      param2=0x00,
                                      dest=0x50,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)
    
    def go_home(self):
        ptk = _packets.ThorLabsPacket(message_id=0x0443,
                                      param1=0x01,
                                      param2=0x00,
                                      dest=0x50,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)
