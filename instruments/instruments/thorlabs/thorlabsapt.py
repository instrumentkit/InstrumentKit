#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the Thorlabs APT Controller.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import re
import struct
import logging

from builtins import range
import quantities as pq

from instruments.thorlabs import _abstract, _packets, _cmds

# LOGGING #####################################################################

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# CLASSES #####################################################################


class ThorLabsAPT(_abstract.ThorLabsInstrument):

    """
    Generic ThorLabs APT hardware device controller. Communicates using the
    ThorLabs APT communications protocol, whose documentation is found in the
    thorlabs source folder.
    """

    class APTChannel(object):

        """
        Represents a channel within the hardware device. One device can have
        many channels, each labeled by an index.
        """

        def __init__(self, apt, idx_chan):
            self._apt = apt
            # APT is 1-based, but we want the Python representation to be
            # 0-based.
            self._idx_chan = idx_chan + 1

        @property
        def enabled(self):
            """
            Gets/sets the enabled status for the specified APT channel

            :type: `bool`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOD_REQ_CHANENABLESTATE,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOD_GET_CHANENABLESTATE)
            return not bool(resp.parameters[1] - 1)

        @enabled.setter
        def enabled(self, newval):
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOD_SET_CHANENABLESTATE,
                param1=self._idx_chan,
                param2=0x01 if newval else 0x02,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            self._apt.sendpacket(pkt)

    _channel_type = APTChannel

    def __init__(self, filelike):
        super(ThorLabsAPT, self).__init__(filelike)
        self._dest = 0x50  # Generic USB device; make this configurable later.

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
            hw_info = self.querypacket(
                req_packet, expect=_cmds.ThorLabsCommands.HW_GET_INFO)

            self._serial_number = str(hw_info.data[0:4]).encode('hex')
            self._model_number = str(
                hw_info.data[4:12]).replace('\x00', '').strip()

            hw_type_int = struct.unpack('<H', str(hw_info.data[12:14]))[0]
            if hw_type_int == 45:
                self._hw_type = 'Multi-channel controller motherboard'
            elif hw_type_int == 44:
                self._hw_type = 'Brushless DC controller'
            else:
                self._hw_type = 'Unknown type: {}'.format(hw_type_int)

            # Note that the fourth byte is padding, so we strip out the first
            # three bytes and format them.
            # pylint: disable=invalid-format-index
            self._fw_version = "{0[0]}.{0[1]}.{0[2]}".format(
                str(hw_info.data[14:18]).encode('hex')
            )
            self._notes = str(hw_info.data[18:66]).replace('\x00', '').strip()

            self._hw_version = struct.unpack(
                '<H', str(hw_info.data[78:80]))[0]
            self._mod_state = struct.unpack(
                '<H', str(hw_info.data[80:82]))[0]
            self._n_channels = struct.unpack(
                '<H', str(hw_info.data[82:84]))[0]
        except IOError as e:
            logger.error("Exception occured while fetching hardware info: %s", e)

        # Create a tuple of channels of length _n_channel_type
        if self._n_channels > 0:
            self._channel = tuple(self._channel_type(self, chan_idx)
                                  for chan_idx in range(self._n_channels))

    @property
    def serial_number(self):
        """
        Gets the serial number for the APT controller

        :type: `str`
        """
        return self._serial_number

    @property
    def model_number(self):
        """
        Gets the model number for the APT controller

        :type: `str`
        """
        return self._model_number

    @property
    def name(self):
        """
        Gets the name of the APT controller. This is a human readable string
        containing the model, serial number, hardware version, and firmware
        version.

        :type: `str`
        """
        return "ThorLabs APT Instrument model {model}, serial {serial} " \
               "(HW version {hw_ver}, FW version {fw_ver})".format(
                   hw_ver=self._hw_version,
                   serial=self.serial_number,
                   fw_ver=self._fw_version,
                   model=self.model_number
               )

    @property
    def channel(self):
        """
        Gets the list of channel objects attached to the APT controller.

        A specific channel object can then be accessed like one would access
        a list.

        :type: `tuple` of `APTChannel`
        """
        return self._channel

    @property
    def n_channels(self):
        """
        Gets/sets the number of channels attached to the APT controller

        :type: `int`
        """
        return self._n_channels

    @n_channels.setter
    def n_channels(self, nch):
        # Change the number of channels so as not to modify those instances
        # already existing:
        # If we add more channels, append them to the list,
        # If we remove channels, remove them from the end of the list.
        if nch > self._n_channels:
            self._channel = self._channel + \
                list(self._channel_type(self, chan_idx)
                     for chan_idx in range(self._n_channels, nch))
        elif nch < self._n_channels:
            self._channel = self._channel[:nch]
        self._n_channels = nch

    def identify(self):
        """
        Causes a light on the APT instrument to blink, so that it can be
        identified.
        """
        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.MOD_IDENTIFY,
            param1=0x00,
            param2=0x00,
            dest=self._dest,
            source=0x01,
            data=None
        )
        self.sendpacket(pkt)

    @property
    def destination(self):
        """
        Gets the destination for the APT controller

        :type: `int`
        """
        return self._dest


class APTPiezoDevice(ThorLabsAPT):

    """
    Generic ThorLabs APT piezo device, superclass of more specific piezo
    devices.
    """

    class PiezoDeviceChannel(ThorLabsAPT.APTChannel):
        """
        Represents a channel within the hardware device. One device can have
        many channels, each labeled by an index.

        This class represents piezo stage channels.
        """
        # PIEZO COMMANDS #

        @property
        def max_travel(self):
            """
            Gets the maximum travel for the specified piezo channel.

            :type: `~quantities.Quantity`
            :units: Nanometers
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_REQ_MAXTRAVEL,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            resp = self._apt.querypacket(pkt)

            # Not all APT piezo devices support querying the maximum travel
            # distance. Those that do not simply ignore the PZ_REQ_MAXTRAVEL
            # packet, so that the response is empty.
            if resp is None:
                return NotImplemented

            # chan, int_maxtrav
            _, int_maxtrav = struct.unpack('<HH', resp.data)
            return int_maxtrav * pq.Quantity(100, 'nm')

    @property
    def led_intensity(self):
        """
        Gets/sets the output intensity of the LED display.

        :type: `float` between 0 and 1.
        """
        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.PZ_REQ_TPZ_DISPSETTINGS,
            param1=0x01,
            param2=0x00,
            dest=self._dest,
            source=0x01,
            data=None
        )
        resp = self.querypacket(pkt)
        return float(struct.unpack('<H', resp.data)[0]) / 255

    @led_intensity.setter
    def led_intensity(self, intensity):
        # pylint: disable=round-builtin
        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.PZ_SET_TPZ_DISPSETTINGS,
            param1=None,
            param2=None,
            dest=self._dest,
            source=0x01,
            data=struct.pack('<H', int(round(255 * intensity)))
        )
        self.sendpacket(pkt)

    _channel_type = PiezoDeviceChannel


class APTPiezoStage(APTPiezoDevice):

    """
    Class representing a Thorlabs APT piezo stage
    """

    class PiezoChannel(APTPiezoDevice.PiezoDeviceChannel):
        """
        Class representing a single piezo channel within a piezo stage
        on the Thorlabs APT controller.
        """

        # PIEZO COMMANDS #

        @property
        def position_control_closed(self):
            """
            Gets the status if the position control is closed or not.

            `True` means that the position control is closed, `False` otherwise

            :tyep: `bool`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_REQ_POSCONTROLMODE,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZ_GET_POSCONTROLMODE)
            return bool((resp.parameters[1] - 1) & 1)

        def change_position_control_mode(self, closed, smooth=True):
            """
            Changes the position control mode of the piezo channel

            :param bool closed: `True` for closed, `False` for open
            :param bool smooth: `True` for smooth, `False` for otherwise.
                Default is `True`.
            """
            mode = 1 + (int(closed) | int(smooth) << 1)
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_SET_POSCONTROLMODE,
                param1=self._idx_chan,
                param2=mode,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            self._apt.sendpacket(pkt)

        @property
        def output_position(self):
            """
            Gets/sets the output position for the piezo channel.

            :type: `str`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_REQ_OUTPUTPOS,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZ_GET_OUTPUTPOS)
            # chan, pos
            _, pos = struct.unpack('<HH', resp.data)
            return pos

        @output_position.setter
        def output_position(self, pos):
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_SET_OUTPUTPOS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack('<HH', self._idx_chan, pos)
            )
            self._apt.sendpacket(pkt)

    _channel_type = PiezoChannel


class APTStrainGaugeReader(APTPiezoDevice):

    """
    Class representing a Thorlabs APT strain gauge reader.

    .. warning:: This is not currently implemented
    """

    class StrainGaugeChannel(APTPiezoDevice.PiezoDeviceChannel):
        """
        Class representing a single strain gauge channel attached to a
        `APTStrainGaugeReader` on the Thorlabs APT controller.

        .. warning:: This is not currently implemented
        """
        # STRAIN GAUGE COMMANDS #

        pass

    _channel_type = StrainGaugeChannel


class APTMotorController(ThorLabsAPT):

    """
    Class representing a Thorlabs APT motor controller
    """

    class MotorChannel(ThorLabsAPT.APTChannel):

        """
        Class representing a single motor attached to a Thorlabs APT motor
        controller (`APTMotorController`).
        """

        # INSTANCE VARIABLES #

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
        #: factors, so as to produce quantities of dimension "ct/s" and
        #: "ct/s**2"
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
                'FW103':  (pq.Quantity(25600 / 360, 'ct/deg'),) * 3,
                'NR360':  (pq.Quantity(25600 / 5.4546, 'ct/deg'),) * 3
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

        # UNIT CONVERSION METHODS #

        def set_scale(self, motor_model):
            """
            Sets the scale factors for this motor channel, based on the model
            of the attached motor and the specifications of the driver of which
            this is a channel.

            :param str motor_model: Name of the model of the attached motor,
                as indicated in the APT protocol documentation (page 14, v9).
            """
            for driver_re, motor_dict in self.__SCALE_FACTORS_BY_MODEL.items():
                if driver_re.match(self._apt.model_number) is not None:
                    if motor_model in motor_dict:
                        self.scale_factors = motor_dict[motor_model]
                        return
                    else:
                        break
            # If we've made it down here, emit a warning that we didn't find the
            # model.
            logger.warning("Scale factors for controller %s and motor %s are "
                           "unknown", self._apt.model_number, motor_model)

        # MOTOR COMMANDS #

        @property
        def status_bits(self):
            """
            Gets the status bits for the specified motor channel.

            :type: `dict`
            """
            # NOTE: the difference between MOT_REQ_STATUSUPDATE and
            # MOT_REQ_DCSTATUSUPDATE confuses me
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_REQ_STATUSUPDATE,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            # The documentation claims there are 14 data bytes, but it seems
            # there are sometimes some extra random ones...
            resp_data = self._apt.querypacket(pkt).data[:14]
            # ch_ident, position, enc_count, status_bits
            _, _, _, status_bits = struct.unpack(
                '<HLLL', resp_data)

            status_dict = dict(
                (key, (status_bits & bit_mask > 0))
                for key, bit_mask in self.__STATUS_BIT_MASK.items()
            )

            return status_dict

        @property
        def position(self):
            """
            Gets the current position of the specified motor channel

            :type: `~quantities.Quantity`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_REQ_POSCOUNTER,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            response = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOT_GET_POSCOUNTER)
            # chan, pos
            _, pos = struct.unpack('<Hl', response.data)
            return pq.Quantity(pos, 'counts') / self.scale_factors[0]

        @property
        def position_encoder(self):
            """
            Gets the position of the encoder of the specified motor channel

            :type: `~quantities.Quantity`
            :units: Encoder ``counts``
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_REQ_ENCCOUNTER,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            response = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOT_GET_ENCCOUNTER)
            # chan, pos
            _, pos = struct.unpack('<Hl', response.data)
            return pq.Quantity(pos, 'counts')

        def go_home(self):
            """
            Instructs the specified motor channel to return to its home
            position
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_MOVE_HOME,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None
            )
            self._apt.sendpacket(pkt)

        def move(self, pos, absolute=True):
            """
            Instructs the specified motor channel to move to a specific
            location. The provided position can be either an absolute or
            relative position.

            :param pos: The position to move to. Provided value will be
                converted to encoder counts.
            :type pos: `~quantities.Quantity`
            :units pos: As specified, or assumed to of units encoder counts

            :param bool absolute: Specify if the position is a relative or
                absolute position. ``True`` means absolute, while ``False``
                is for a relative move.
            """
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
                        raise ValueError("Provided units are not compatible "
                                         "with current motor scale factor.")

            # Now that we have our position as an integer number of encoder
            # counts, we're good to move.
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_MOVE_ABSOLUTE if absolute
                else _cmds.ThorLabsCommands.MOT_MOVE_RELATIVE,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack('<Hl', self._idx_chan, pos_ec)
            )

            _ = self._apt.querypacket(
                pkt,
                expect=_cmds.ThorLabsCommands.MOT_MOVE_COMPLETED
            )

    _channel_type = MotorChannel

    # CONTROLLER PROPERTIES AND METHODS #
