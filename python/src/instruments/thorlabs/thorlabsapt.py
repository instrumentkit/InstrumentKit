#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# thorlabsapt.py: Driver for the Thorlabs APT Controller.
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

from instruments.thorlabs import _abstract
from instruments.thorlabs import _packets
from instruments.thorlabs import _cmds

from instruments.util_fns import ProxyList

from flufl.enum import IntEnum

import quantities as pq

import struct

## LOGGING #####################################################################

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

## CLASSES #####################################################################

class ThorLabsAPT(_abstract.ThorLabsInstrument):
    
    class APTChannel(object):
        def __init__(self, apt, idx_chan):
            self._apt = apt
            # APT is 1-based, but we want the Python representation to be
            # 0-based.
            self._idx_chan = idx_chan + 1
            
        @property
        def enabled(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOD_REQ_CHANENABLESTATE,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            resp = self._apt.querypacket(pkt)
            return not bool(resp._param2 - 1)
        @enabled.setter
        def enabled(self, newval):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_SET_POSCONTROLMODE,
                                          param1=self._idx_chan,
                                          param2=0x01 if newval else 0x02,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            self._apt.sendpacket(pkt)
    
    _channel_type = APTChannel
    
    def __init__(self, filelike):
        super(ThorLabsAPT, self).__init__(filelike)
        self._dest = 0x50
        
        # Provide defaults in case an exception occurs below.
        self._serial_number = None
        self._model_number = None
        self._hw_type = None
        self._fw_version = None
        self._notes = ""
        self._hw_version = None
        self._mod_state = None
        self._n_channels = 0
        
        # Perform a HW_REQ_INFO to figure out the model number, serial number,
        # etc.
        try:
            req_packet = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.HW_REQ_INFO,
                param1=0x00,
                param2=0x00,
                dest=self._dest,
                source=0x01,
                data=None
                )
            hw_info = self.querypacket(req_packet)
            
            self._serial_number = str(hw_info._data[0:4]).encode('hex')
            self._model_number  = str(hw_info._data[4:12]).replace('\x00', '').strip()
            
            # TODO: decode this field
            self._hw_type       = str(hw_info._data[12:14]).encode('hex') 
            
            self._fw_version    = str(hw_info._data[14:18]).encode('hex')
            self._notes         = str(hw_info._data[18:66]).replace('\x00', '').strip()
            
            # TODO: decode the following fields.
            self._hw_version    = str(hw_info._data[78:80]).encode('hex')
            self._mod_state     = str(hw_info._data[80:82]).encode('hex')
            self._n_channels    = str(hw_info._data[82:84]).encode('hex')
        except Exception as e:
            logger.error("Exception occured while fetching hardware info: {}".format(e))
    
    @property
    def serial_number(self):
        return serial_number
    
    @property
    def model_number(self):
        return self._model_number
        
    @property
    def name(self):
        return (self._hw_type, self._hw_version, self._serial_number, 
                self._fw_version, self._mode_state, self._n_channels)
                
    @property
    def channel(self):
        return ProxyList(self, self._channel_type, xrange(self._n_channels))
    
    def identify(self):
        """
        Causes a light on the APT instrument to blink, so that it can be
        identified.
        """
        pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOD_IDENTIFY,
                                      param1=0x00,
                                      param2=0x00,
                                      dest=self._dest,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)
    
class APTPiezoStage(ThorLabsAPT):
    
    class PiezoChannel(ThorLabsAPT.APTChannel):
        ## PIEZO COMMANDS ##
    
        @property
        def is_position_control_closed(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_REQ_POSCONTROLMODE,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            resp = self._apt.querypacket(pkt)
            return bool((resp._param2 - 1) & 1)
            
        def change_position_control_mode(self, closed, smooth=True):
            mode = 1 + (int(closed) | int(smooth) << 1)
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_SET_POSCONTROLMODE,
                                          param1=self._idx_chan,
                                          param2=mode,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            self._apt.sendpacket(pkt)
        
        @property
        def output_position(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_REQ_OUTPUTPOS,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            resp = self._apt.querypacket(pkt)
            chan, pos = struct.unpack('<HH', resp._data)
            return pos
        
        @output_position.setter
        def output_position(self, pos):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_SET_OUTPUTPOS,
                                          param1=None,
                                          param2=None,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=struct.pack('<HH', self._idx_chan, pos))
            self._apt.sendpacket(pkt)
            
        @property
        def max_travel(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_REQ_MAXTRAVEL,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            resp = self._apt.querypacket(pkt)
            
            # Not all APT piezo devices support querying the maximum travel
            # distance. Those that do not simply ignore the PZ_REQ_MAXTRAVEL
            # packet, so that the response is empty.
            if resp is None:
                return NotImplemented
            
            chan, int_maxtrav = struct.unpack('<HH', resp._data)
            return int_maxtrav * pq.Quantity(100, 'nm')
    
    _channel_type = PiezoChannel
    
    
class APTMotorController(ThorLabsAPT):
    
    class MotorChannel(ThorLabsAPT.APTChannel):
        ## MOTOR COMMANDS ##
        
        @property
        def position(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_REQ_POSCOUNTER,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            response = self._apt.querypacket(pkt)
            chan, pos = struct.unpack('<Hl', response._data)
            return pq.Quantity(pos, 'counts')
            
        @property
        def position_encoder(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_REQ_ENCCOUNTER,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            response = self._apt.querypacket(pkt)
            chan, pos = struct.unpack('<Hl', response._data)
            return pq.Quantity(pos, 'counts')
        
        def go_home(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_MOVE_HOME,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            self._apt.sendpacket(pkt)
            
        def move(self, pos, absolute=True):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_MOVE_ABSOLUTE if absolute else _cmds.ThorLabsCommands.MOT_MOVE_RELATIVE,
                                          param1=None,
                                          param2=None,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=struct.pack('<Hl', self._idx_chan, pos))
                                          
            response = self._apt.querypacket(pkt)
            if response._message_id != _cmds.ThorLabsCommands.MOT_MOVE_COMPLETED:
                raise IOError("Move might not have completed, got {} instead.".format(_cmds.ThorLabsCommands(response._message_id)))
            
    _channel_type = MotorChannel
            
