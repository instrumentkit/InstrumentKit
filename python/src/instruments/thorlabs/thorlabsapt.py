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

from flufl.enum import IntEnum

import quantities as pq

import re
import struct

## LOGGING #####################################################################

import logging
from instruments.util_fns import NullHandler

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

## CLASSES #####################################################################

class ThorLabsAPT(_abstract.ThorLabsInstrument):
    '''
    Generic ThorLabs APT hardware device controller. Communicates using the 
    ThorLabs APT communications protocol, whose documentation is found in the
    thorlabs source folder.
    '''
    
    class APTChannel(object):
        '''
        Represents a channel within the hardware device. One device can have 
        many channels, each labeled by an index.
        '''
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
            resp = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.MOD_GET_CHANENABLESTATE)
            return not bool(resp._param2 - 1)
        @enabled.setter
        def enabled(self, newval):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOD_SET_CHANENABLESTATE,
                                          param1=self._idx_chan,
                                          param2=0x01 if newval else 0x02,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            self._apt.sendpacket(pkt)
    
    _channel_type = APTChannel
    
    def __init__(self, filelike):
        super(ThorLabsAPT, self).__init__(filelike)
        self._dest = 0x50 # Generic USB device; make this configurable later.
        
        # Provide defaults in case an exception occurs below.
        self._serial_number = None
        self._model_number = None
        self._hw_type = None
        self._fw_version = None
        self._notes = ""
        self._hw_version = None
        self._mod_state = None
        self._n_channels = 0
        self._channel = ()
        
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
            hw_info = self.querypacket(req_packet, expect=_cmds.ThorLabsCommands.HW_GET_INFO)
            
            self._serial_number = str(hw_info._data[0:4]).encode('hex')
            self._model_number  = str(hw_info._data[4:12]).replace('\x00', '').strip()
            
            hw_type_int = struct.unpack('<H', str(hw_info._data[12:14]))[0]
            if hw_type_int == 45:
                self._hw_type = 'Multi-channel controller motherboard'
            elif hw_type_int == 44:
                self._hw_type = 'Brushless DC controller'
            else:
                self._hw_type = 'Unknown type: {}'.format(hw_type_int)
            
            # Note that the fourth byte is padding, so we strip out the first
            # three bytes and format them.
            self._fw_version    = "{0[0]}.{0[1]}.{0[2]}".format(
                str(hw_info._data[14:18]).encode('hex')
            )
            self._notes         = str(hw_info._data[18:66]).replace('\x00', '').strip()
            
            self._hw_version    = struct.unpack('<H', str(hw_info._data[78:80]))[0]
            self._mod_state     = struct.unpack('<H', str(hw_info._data[80:82]))[0]
            self._n_channels    = struct.unpack('<H', str(hw_info._data[82:84]))[0]
        except Exception as e:
            logger.error("Exception occured while fetching hardware info: {}".format(e))

        # Create a tuple of channels of length _n_channel_type
        if self._n_channels > 0:
            self._channel = list(self._channel_type(self, chan_idx) for chan_idx in xrange(self._n_channels) )
    
    @property
    def serial_number(self):
        return self._serial_number
    
    @property
    def model_number(self):
        return self._model_number
        
    @property
    def name(self):
        return "ThorLabs APT Instrument model {model}, serial {serial} (HW version {hw_ver}, FW version {fw_ver})".format(
            hw_ver=self._hw_version, serial=self.serial_number, 
            fw_ver=self._fw_version, model=self.model_number
        )
                
    @property
    def channel(self):
        return self._channel
        
    @property
    def n_channels(self):
        return self._n_channels
        
    @n_channels.setter
    def n_channels(self, nch):
        # Change the number of channels so as not to modify those instances already existing:
        # If we add more channels, append them to the list,
        # If we remove channels, remove them from the end of the list.
        if nch > self._n_channels:
            self._channel = self._channel + \
                list( self._channel_type(self, chan_idx) for chan_idx in xrange(self._n_channels, nch) )
        elif nch < self._n_channels:
            self._channel = self._channel[:nch]
        self._n_channels = nch
    
    def identify(self):
        '''
        Causes a light on the APT instrument to blink, so that it can be
        identified.
        '''
        pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOD_IDENTIFY,
                                      param1=0x00,
                                      param2=0x00,
                                      dest=self._dest,
                                      source=0x01,
                                      data=None)
        self.sendpacket(pkt)

class APTPiezoDevice(ThorLabsAPT):
    '''
    Generic ThorLabs APT piezo device, superclass of more specific piezo devices.
    '''
    
    class PiezoDeviceChannel(ThorLabsAPT.APTChannel):
        ## PIEZO COMMANDS ##
    
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
            
    @property
    def led_intensity(self):
        '''
        The output intensity of the LED display.
        
        :type: `float` between 0 and 1.
        '''
        pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_REQ_TPZ_DISPSETTINGS,
                                      param1=0x01,
                                      param2=0x00,
                                      dest=self._dest,
                                      source=0x01,
                                      data=None)
        resp = self.querypacket(pkt)
        return float(struct.unpack('<H', resp._data)[0])/255
    
    @led_intensity.setter
    def led_intensity(self, intensity):
        '''
        The output intensity of the LED display.
        
        :param float intensity: Ranges from 0 to 1.
        '''
        pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_SET_TPZ_DISPSETTINGS,
                                      param1=None,
                                      param2=None,
                                      dest=self._dest,
                                      source=0x01,
                                      data=struct.pack('<H', int(round(255*intensity))))
        self.sendpacket(pkt)
    
    _channel_type = PiezoDeviceChannel
        
class APTPiezoStage(APTPiezoDevice):
    
    class PiezoChannel(APTPiezoDevice.PiezoDeviceChannel):
        ## PIEZO COMMANDS ##
    
        @property
        def is_position_control_closed(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.PZ_REQ_POSCONTROLMODE,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            resp = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.PZ_GET_POSCONTROLMODE)
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
            resp = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.PZ_GET_OUTPUTPOS)
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
            
    _channel_type = PiezoChannel

class APTStrainGaugeReader(APTPiezoDevice):
    
    class StrainGaugeChannel(APTPiezoDevice.PiezoDeviceChannel):
        ## STRAIN GAUGE COMMANDS ##
    
        pass
        
    
    _channel_type = StrainGaugeChannel
    
class APTMotorController(ThorLabsAPT):

    class MotorChannel(ThorLabsAPT.APTChannel):
    
        ## INSTANCE VARIABLES ##
        
        #: Sets the scale between the encoder counts and physical units
        #: for the position, velocity and acceleration parameters of this
        #: channel. By default, set to dimensionless, indicating that the proper
        #: scale is not known.
        #:
        #: In keeping with the APT protocol documentation, the scale factor
        #: is multiplied by the physical quantity to get the encoder count,
        #: such that scale factors should have units similar to microsteps/mm,
        #: in the example of a linear motor.
        #:
        #: Encoder counts are represented by the quantities package unit
        #: "ct", which is considered dimensionally equivalent to dimensionless.
        #: Finally, note that the "/s" and "/s**2" are not included in scale
        #: factors, so as to produce quantities of dimension "ct/s" and "ct/s**2"
        #: from dimensionful input.
        #: 
        #: For more details, see the APT protocol documentation.
        scale_factors = (pq.Quantity(1, 'dimensionless'), ) * 3
        
        __SCALE_FACTORS_BY_MODEL = {
            re.compile('TST001|BSC00.|BSC10.|MST601'): {
                # Note that for these drivers, the scale factors are identical
                # for position, velcoity and acceleration. This is not true for
                # all drivers!
                'DRV001': (pq.Quantity(51200, 'ct/mm'),) * 3,
                'DRV013': (pq.Quantity(25600, 'ct/mm'),) * 3,
                'DRV014': (pq.Quantity(25600, 'ct/mm'),) * 3,
                'DRV113': (pq.Quantity(20480, 'ct/mm'),) * 3,
                'DRV114': (pq.Quantity(20480, 'ct/mm'),) * 3,
                'FW103':  (pq.Quantity(25600/360, 'ct/deg'),) * 3,
                'NR360':  (pq.Quantity(25600/5.4546, 'ct/deg'),) * 3
            },
            # TODO: add other tables here.
        }
        
        __STATUS_BIT_MASK = {
            'CW_HARD_LIM':          0x00000001,
            'CCW_HARD_LIM':         0x00000002,
            'CW_SOFT_LIM':          0x00000004,
            'CCW_SOFT_LIM':         0x00000008,
            'CW_MOVE_IN_MOTION':    0x00000010,
            'CCW_MOVE_IN_MOTION':   0x00000020,
            'CW_JOG_IN_MOTION':     0x00000040,
            'CCW_JOG_IN_MOTION':    0x00000080,
            'MOTOR_CONNECTED':      0x00000100,
            'HOMING_IN_MOTION':     0x00000200,
            'HOMING_COMPLETE':      0x00000400,
            'INTERLOCK_STATE':      0x00001000
        }
    
        ## UNIT CONVERSION METHODS ##
        
        def set_scale(self, motor_model):
            """
            Sets the scale factors for this motor channel, based on the model
            of the attached motor and the specifications of the driver of which
            this is a channel.
            
            :param str motor_model: Name of the model of the attached motor,
                as indicated in the APT protocol documentation (page 14, v9).
            """
            for driver_re, motor_dict in self.__SCALE_FACTORS_BY_MODEL.iteritems():
                if driver_re.match(self._apt.model_number) is not None:
                    if motor_model in motor_dict:
                        self.scale_factors = motor_dict[motor_model]
                        return
                    else:
                        break
            # If we've made it down here, emit a warning that we didn't find the
            # model.
            logger.warning(
                "Scale factors for controller {} and motor {} are unknown".format(
                    self._apt.model_number, motor_model
                )
            )
    
        ## MOTOR COMMANDS ##
        
        @property
        def status_bits(self):
            # NOTE: the difference between MOT_REQ_STATUSUPDATE and MOT_REQ_DCSTATUSUPDATE confuses me
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_REQ_STATUSUPDATE,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            # The documentation claims there are 14 data bytes, but it seems there are sometimes
            # some extra random ones...
            resp_data = self._apt.querypacket(pkt)._data[:14]
            ch_ident, position, enc_count, status_bits = struct.unpack('<HLLL', resp_data)
            
            status_dict = dict(
                (key, (status_bits & bit_mask > 0))
                for key, bit_mask in self.__STATUS_BIT_MASK.iteritems()
            )
            
            return status_dict
        
        @property
        def position(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_REQ_POSCOUNTER,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            response = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.MOT_GET_POSCOUNTER)
            chan, pos = struct.unpack('<Hl', response._data)
            return pq.Quantity(pos, 'counts') / self.scale_factors[0]
            
        @property
        def position_encoder(self):
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_REQ_ENCCOUNTER,
                                          param1=self._idx_chan,
                                          param2=0x00,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=None)
            response = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.MOT_GET_ENCCOUNTER)
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
            # Handle units as follows:
            # 1. Treat raw numbers as encoder counts.
            # 2. If units are provided (as a Quantity), check if they're encoder
            #    counts. If they aren't, apply scale factor.
            if not isinstance(pos, pq.Quantity):
                pos_ec = int(pos)
            else:
                if pos.units == pq.counts:
                    pos_ec = int(pos.magnitude)
                else:
                    scaled_pos = (pos * self.scale_factors[0])
                    # Force a unit error.
                    try:
                        pos_ec = int(scaled_pos.rescale(pq.counts).magnitude)
                    except:
                        raise ValueError("Provided units are not compatible with current motor scale factor.")
            
            # Now that we have our position as an integer number of encoder
            # counts, we're good to move.
            pkt = _packets.ThorLabsPacket(message_id=_cmds.ThorLabsCommands.MOT_MOVE_ABSOLUTE if absolute else _cmds.ThorLabsCommands.MOT_MOVE_RELATIVE,
                                          param1=None,
                                          param2=None,
                                          dest=self._apt._dest,
                                          source=0x01,
                                          data=struct.pack('<Hl', self._idx_chan, pos_ec))
                                          
            response = self._apt.querypacket(pkt, expect=_cmds.ThorLabsCommands.MOT_MOVE_COMPLETED)
            
    _channel_type = MotorChannel
    
    ## CONTROLLER PROPERTIES AND METHODS ##
    
            
