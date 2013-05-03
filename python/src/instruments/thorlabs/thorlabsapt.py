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
from instruments.thorlabs._cmds import ThorLabsCommands

## CLASSES #####################################################################

class ThorLabsAPT(_abstract.ThorLabsInstrument):
    
    def __init__(self, filelike):
        super(ThorLabsAPT, self).__init__(filelike)
        self._dest = 0x50
        
        # Perform a HW_REQ_INFO to figure out the model number, serial number,
        # etc.
        req_packet = _packets.ThorLabsPacket(
            message_id=ThorlabsCommands.HW_REQ_INFO,
            param1=0x00,
            param2=0x00,
            dest=self._dest,
            source=0x01,
            data=None
            )
        hw_info = self.querypacket(req_packet)
        
        self._serial_number = str(hw_info.data[0:4]).encode('hex')
        self._model_number  = str(hw_info.data[4:12])
        
        # TODO: decode this field
        self._hw_type       = str(hw_info.data[12:14]).encode('hex') 
        
        self._fw_version    = str(hw_info.data[14:18]).encode('hex')
        self._notes         = str(hw_info.data[18:66])
        
        # TODO: decode the following fields.
        self._hw_version    = str(hw_info.data[78:80]).encode('hex')
        self._mod_state     = str(hw_info.data[80:82]).encode('hex')
        self._n_channels    = str(hw_info.data[82:84]).encode('hex')
    
    @property
    def model_number(self):
        return self._model_number
        
    @property
    def name(self):
        return (self._hw_type, self._hw_version, self._serial_number, 
                self._fw_version, self._mode_state, self._n_channels)
    
    def identify(self):
        pkt = _packets.ThorLabsPacket(message_id=ThorLabsCommands.MOD_IDENTIFY,
                                      param1=0x00,
                                      param2=0x00,
                                      dest=self._dest,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)
    
    def go_home(self):
        pkt = _packets.ThorLabsPacket(message_id=ThorLabsCommands.MOT_MOVE_HOME,
                                      param1=0x01,
                                      param2=0x00,
                                      dest=self._dest,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)
    
