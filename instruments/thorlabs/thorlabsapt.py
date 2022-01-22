#!/usr/bin/env python
"""
Provides the support for the Thorlabs APT Controller.
"""

# IMPORTS #####################################################################


import re
import struct
import logging
import codecs
import warnings

from instruments.thorlabs import _abstract, _packets, _cmds
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# LOGGING #####################################################################

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# CLASSES #####################################################################

# pylint: disable=too-many-lines


class ThorLabsAPT(_abstract.ThorLabsInstrument):

    """
    Generic ThorLabs APT hardware device controller. Communicates using the
    ThorLabs APT communications protocol, whose documentation is found in the
    thorlabs source folder.
    """

    class APTChannel:

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

            :raises TypeError: If controller is not supported
            """
            if self._apt.model_number[0:3] == "KIM":
                raise TypeError(
                    "For KIM controllers, use the "
                    "`enabled_single` function to enable "
                    "one axis. For KIM101 controllers, "
                    "multiple axes can be enabled using "
                    "the `enabled_multi` function from the "
                    "controller level."
                )

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOD_REQ_CHANENABLESTATE,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOD_GET_CHANENABLESTATE
            )
            return not bool(resp.parameters[1] - 1)

        @enabled.setter
        def enabled(self, newval):
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOD_SET_CHANENABLESTATE,
                param1=self._idx_chan,
                param2=0x01 if newval else 0x02,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            self._apt.sendpacket(pkt)

    _channel_type = APTChannel

    def __init__(self, filelike):
        super().__init__(filelike)
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
                data=None,
            )
            hw_info = self.querypacket(
                req_packet,
                expect=_cmds.ThorLabsCommands.HW_GET_INFO,
                expect_data_len=84,
            )

            self._serial_number = codecs.encode(hw_info.data[0:4], "hex").decode(
                "ascii"
            )
            self._model_number = (
                hw_info.data[4:12].decode("ascii").replace("\x00", "").strip()
            )

            hw_type_int = struct.unpack("<H", hw_info.data[12:14])[0]
            if hw_type_int == 45:
                self._hw_type = "Multi-channel controller motherboard"
            elif hw_type_int == 44:
                self._hw_type = "Brushless DC controller"
            else:
                self._hw_type = f"Unknown type: {hw_type_int}"

            # Note that the fourth byte is padding, so we strip out the first
            # three bytes and format them.
            # pylint: disable=invalid-format-index
            self._fw_version = "{0[0]:x}.{0[1]:x}.{0[2]:x}".format(hw_info.data[14:18])
            self._notes = (
                hw_info.data[18:66].replace(b"\x00", b"").decode("ascii").strip()
            )

            self._hw_version = struct.unpack("<H", hw_info.data[78:80])[0]
            self._mod_state = struct.unpack("<H", hw_info.data[80:82])[0]
            self._n_channels = struct.unpack("<H", hw_info.data[82:84])[0]
        except OSError as e:
            logger.error("Exception occured while fetching hardware info: %s", e)

        # Create a tuple of channels of length _n_channel_type
        if self._n_channels > 0:
            self._channel = tuple(
                self._channel_type(self, chan_idx)
                for chan_idx in range(self._n_channels)
            )

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
        return (
            "ThorLabs APT Instrument model {model}, serial {serial} "
            "(HW version {hw_ver}, FW version {fw_ver})".format(
                hw_ver=self._hw_version,
                serial=self.serial_number,
                fw_ver=self._fw_version,
                model=self.model_number,
            )
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
            self._channel = list(self._channel) + list(
                self._channel_type(self, chan_idx)
                for chan_idx in range(self._n_channels, nch)
            )
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
            data=None,
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

            :type: `~pint.Quantity`
            :units: Nanometers
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_REQ_MAXTRAVEL,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            resp = self._apt.querypacket(pkt, expect_data_len=4)

            # Not all APT piezo devices support querying the maximum travel
            # distance. Those that do not simply ignore the PZ_REQ_MAXTRAVEL
            # packet, so that the response is empty.
            if resp is None:
                return NotImplemented

            # chan, int_maxtrav
            _, int_maxtrav = struct.unpack("<HH", resp.data)
            return int_maxtrav * u.Quantity(100, "nm")

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
            data=None,
        )
        resp = self.querypacket(pkt, expect_data_len=2)

        # Not all APT piezo devices support querying the LED intenstiy
        # distance, e.g., TIM, KIM. Those that do not simply ignore the
        # PZ_REQ_TPZ_DISPSETTINGS packet, so that the response is empty.
        # Setting will be ignored as well.
        if resp is None:
            return NotImplemented
        else:
            return float(struct.unpack("<H", resp.data)[0]) / 255

    @led_intensity.setter
    def led_intensity(self, intensity):
        # pylint: disable=round-builtin
        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.PZ_SET_TPZ_DISPSETTINGS,
            param1=None,
            param2=None,
            dest=self._dest,
            source=0x01,
            data=struct.pack("<H", int(round(255 * intensity))),
        )
        self.sendpacket(pkt)

    _channel_type = PiezoDeviceChannel


class APTPiezoInertiaActuator(APTPiezoDevice):

    """Represent a Thorlabs APT piezo inertia actuator.

    Currently only the KIM piezo inertia actuator is implemented.
    Some routines will work with the TIM actuator as well. Routines
    that are specific for the KIM101 controller will raise a TypeError
    if not implemented for this controller. Unfortunately, handling all
    these controller specific functions is fairly messy, but necessary.

    Example for a KIM101 controller:
        >>> import instruments as ik
        >>> import instruments.units as u
        >>> # call the controller
        >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
        >>> # set first channel to enabled
        >>> ch = kim.channel[0]
        >>> ch.enabled_single = True
        >>> # define and set drive parameters
        >>> max_volts = u.Quantity(110, u.V)
        >>> step_rate = u.Quantity(1000, 1/u.s)
        >>> acceleration = u.Quantity(10000, 1/u.s**2)
        >>> ch.drive_op_parameters = [max_volts, step_rate, acceleration]
        >>> # aboslute move to 1000 steps
        >>> ch.move_abs(1000)
    """

    class PiezoChannel(APTPiezoDevice.PiezoDeviceChannel):
        """
        Class representing a single piezo channel within a piezo stage
        on the Thorlabs APT controller.
        """

        # PROPERTIES #

        @property
        def drive_op_parameters(self):
            """Get / Set various drive parameters for move motion.

            Defines the speed and acceleration of moves initiated in
            the following ways:
            - by clicking in the position display
            - via the top panel controls when ‘Go To Position’ mode is
            selected (in the Set_TIM_JogParameters (09) or
            Set_KCubeMMIParams (15) sub‐messages).
            - via software using the MoveVelocity, MoveAbsoluteStepsEx
            or MoveRelativeStepsEx methods.

            :setter: The setter must be be given as a list of 3
                entries. The three entries are:
                -  Maximum Voltage:
                The maximum piezo drive voltage, in the range 85V
                to 125V. Unitful, if no unit given, V are assumed.
                - Step Rate:
                The piezo motor moves by ramping up the drive
                voltage to the value set in the MaxVoltage parameter
                and then dropping quickly to zero, then repeating.
                One cycle is termed a step. This parameter specifies
                the velocity to move when a command is initiated.
                The step rate is specified in steps/sec, in the range 1
                to 2,000. Unitful, if no unit given, 1 / sec assumed.
                - Step Acceleration:
                This parameter specifies the acceleration up to the
                step rate, in the range 1 to 100,000 cycles/sec/sec.
                Unitful, if no unit given, 1/sec**2 assumed.

            :return: List with the drive parameters, unitful.

            :raises TypeError: The setter was not a list or tuple.
            :raises ValueError: The setter was not given a tuple with
                three values.
            :raises ValueError: One of the parameters was out of range.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # change the step rate to 2000 /s
                >>> drive_params = ch.drive_op_parameters
                >>> drive_params[1] = 2000
                >>> ch.drive_op_parameters = drive_params
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x07,
                param2=self._idx_chan,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )

            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZMOT_GET_PARAMS, expect_data_len=14
            )

            # unpack
            ret_val = struct.unpack("<HHHll", resp.data)
            ret_val = [ret_val[2], ret_val[3], ret_val[4]]

            # set units and formats
            ret_val = [
                u.Quantity(int(ret_val[0]), u.V),
                u.Quantity(int(ret_val[1]), 1 / u.s),
                u.Quantity(int(ret_val[2]), 1 / u.s ** 2),
            ]
            return ret_val

        @drive_op_parameters.setter
        def drive_op_parameters(self, params):
            if not isinstance(params, tuple) and not isinstance(params, list):
                raise TypeError("Parameters must be given as list or tuple.")
            if len(params) != 3:
                raise ValueError("Parameters must be a list or tuple with " "length 3.")

            # ensure units
            volt = int(assume_units(params[0], u.V).to(u.V).magnitude)
            rate = int(assume_units(params[1], 1 / u.s).to(1 / u.s).magnitude)
            accl = int(assume_units(params[2], 1 / u.s ** 2).to(1 / u.s ** 2).magnitude)

            # check parameters
            if volt < 85 or volt > 125:
                raise ValueError(
                    "The voltage ({} V) is out of range. It must "
                    "be between 85 V and 125 V.".format(volt)
                )
            if rate < 1 or rate > 2000:
                raise ValueError(
                    "The step rate ({} /s) is out of range. It "
                    "must be between 1 /s and 2,000 /s.".format(rate)
                )

            if accl < 1 or accl > 100000:
                raise ValueError(
                    "The acceleration ({} /s/s) is out of range. "
                    "It must be between 1 /s/s and 100,000 /s/s.".format(accl)
                )

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<HHHll", 0x07, self._idx_chan, volt, rate, accl),
            )
            self._apt.sendpacket(pkt)

        @property
        def enabled_single(self):
            """Get / Set single axis enabled.

            .. note:: Enabling multi channels for KIM101 is defined in
            the controller class.

            :return: Axis status enabled.
            :rtype: bool

            :raises TypeError: Invalid controller for this command.

            Example for a KIM101 controller:
                >>> import instruments as ik
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # enable channel 0
                >>> ch.enabled_single = True
            """
            if self._apt.model_number[0:3] != "KIM":
                raise (
                    "This command is only valid with KIM001 and "
                    "KIM101 controllers. Your controller is a {}.".format(
                        self._apt.model_number
                    )
                )

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2B,
                param2=self._idx_chan,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )

            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZMOT_GET_PARAMS, expect_data_len=4
            )

            ret_val = struct.unpack("<HH", resp.data)[1] == self._idx_chan

            return ret_val

        @enabled_single.setter
        def enabled_single(self, newval):
            if self._apt.model_number[0:3] != "KIM":
                raise TypeError(
                    "This command is only valid with "
                    "KIM001 and KIM101 controllers. Your "
                    "controller is a {}.".format(self._apt.model_number)
                )

            param = self._idx_chan if newval else 0x00
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<HH", 0x2B, param),
            )
            self._apt.sendpacket(pkt)

        @property
        def jog_parameters(self):
            """Get / Set the jog parameters.

            Define the speed and acceleration of moves initiated in the
            following ways:
            - By clicking the jog buttons on the GUI panel
            - By moving the joystick on the unit when ‘Jog Mode’ is
            selected.
            - via software using the MoveJog method.

            It differs from the normal motor jog message in that there
            are two jog step sizes, one for forward and one for reverse.
            The reason for this is that due to the inherent nature of
            the PIA actuators going further in one direction as
            compared with another this will allow the user to
            potentially make adjustments to get fore and aft movement
            the same or similar.

            :setter: The setter must be be given as a list of 5
                entries. The three entries are:
                - Jog Mode (1 for continuus, i.e., until stop command
                is issued, or 2 jog by the number of steps defined)
                - Jog Step Size Forward: Range 1 - 2000
                - Jog Step Size Backward: Range 1 - 2000
                The piezo motor moves by ramping up the drive
                voltage to the value set in the MaxVoltage parameter
                and then dropping quickly to zero, then repeating.
                One cycle is termed a step. This parameter specifies
                the velocity to move when a command is initiated.
                The step rate is specified in steps/sec, in the range 1
                to 2,000. Unitful, if no unit given, 1 / sec assumed.
                - Jog Step Acceleration:
                This parameter specifies the acceleration up to the
                step rate, in the range 1 to 100,000 cycles/sec/sec.
                Unitful, if no unit given, 1/sec**2 assumed.

            :return: List with the jog parameters.

            :raises TypeError: The setter was not a list or tuple.
            :raises ValueError: The setter was not given a tuple with
                three values.
            :raises ValueError: One of the parameters was out of range.
            :raises TypeError: Invalid controller for this command.

            Example for a KIM101 controller:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # set jog parameters
                >>> mode = 2  # only move by set step size
                >>> step = 100  # step size
                >>> rate = u.Quantity(1000, 1/u.s)  # step rate
                >>> # if no quantity given, SI units assumed
                >>> accl = 10000
                >>> ch.jog_parameters = [mode, step, step, rate, accl]
                >>> ch.jog_parameters
                [2, 100, 100, array(1000) * 1/s, array(10000) * 1/s**2]
            """
            if self._apt.model_number[0:3] != "KIM":
                raise TypeError(
                    "This command is only valid with "
                    "KIM001 and KIM101 controllers. Your "
                    "controller is a {}.".format(self._apt.model_number)
                )

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2D,
                param2=self._idx_chan,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )

            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZMOT_GET_PARAMS, expect_data_len=22
            )

            # unpack response
            ret_val = struct.unpack("<HHHllll", resp.data)
            ret_val = [ret_val[2], ret_val[3], ret_val[4], ret_val[5], ret_val[6]]

            # assign the appropriate units, forms
            ret_val = [
                int(ret_val[0]),
                int(ret_val[1]),
                int(ret_val[2]),
                u.Quantity(int(ret_val[3]), 1 / u.s),
                u.Quantity(int(ret_val[4]), 1 / u.s ** 2),
            ]

            return ret_val

        @jog_parameters.setter
        def jog_parameters(self, params):
            if self._apt.model_number[0:3] != "KIM":
                raise TypeError(
                    "This command is only valid with "
                    "KIM001 and KIM101 controllers. Your "
                    "controller is a {}.".format(self._apt.model_number)
                )

            if not isinstance(params, tuple) and not isinstance(params, list):
                raise TypeError("Parameters must be given as list or tuple.")
            if len(params) != 5:
                raise ValueError("Parameters must be a list or tuple with " "length 5.")

            # ensure units
            mode = int(params[0])
            steps_fwd = int(params[1])
            steps_bkw = int(params[2])
            rate = int(assume_units(params[3], 1 / u.s).to(1 / u.s).magnitude)
            accl = int(assume_units(params[4], 1 / u.s ** 2).to(1 / u.s ** 2).magnitude)

            # check parameters
            if mode != 1 and mode != 2:
                raise ValueError(
                    "The mode ({}) must be either set to 1 "
                    "(continuus) or 2 (steps).".format(mode)
                )
            if steps_fwd < 1 or steps_fwd > 2000:
                raise ValueError(
                    "The steps forward ({}) are out of range. It "
                    "must be between 1 and 2,000.".format(steps_fwd)
                )
            if steps_bkw < 1 or steps_bkw > 2000:
                raise ValueError(
                    "The steps backward ({}) are out of range. "
                    "It must be between 1 and 2,000.".format(steps_bkw)
                )
            if rate < 1 or rate > 2000:
                raise ValueError(
                    "The step rate ({} /s) is out of range. It "
                    "must be between 1 /s and 2,000 /s.".format(rate)
                )
            if accl < 1 or accl > 100000:
                raise ValueError(
                    "The acceleration ({} /s/s) is out of range. "
                    "It must be between 1 /s/s and 100,000 /s/s.".format(accl)
                )

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack(
                    "<HHHllll",
                    0x2D,
                    self._idx_chan,
                    mode,
                    steps_fwd,
                    steps_bkw,
                    rate,
                    accl,
                ),
            )
            self._apt.sendpacket(pkt)

        @property
        def position_count(self):
            """Get/Set the position count of a given channel.

            :setter pos: Position (steps) of axis.
            :type pos: int

            :return: Position (steps) of axis.
            :rtype: int

            Example:
                >>> import instruments as ik
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # set position count to zero
                >>> ch.position_count = 0
                >>> ch.position_count
                0
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x05,
                param2=self._idx_chan,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )

            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZMOT_GET_PARAMS, expect_data_len=12
            )

            ret_val = int(struct.unpack("<HHll", resp.data)[2])

            return ret_val

        @position_count.setter
        def position_count(self, pos):
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<HHll", 0x05, self._idx_chan, pos, 0x00),
            )
            self._apt.sendpacket(pkt)

        # METHODS #

        def move_abs(self, pos):
            """
            Moves the axis to a position specified as the number of
            steps away from the zero position.

            To set the moving parameters, use the setter for
            `drive_op_parameters`.

            :param pos: Position to move to, in steps.
            :type pos: int

            Example:
                >>> import instruments as ik
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # move to 314 steps
                >>> ch.move_abs(314)
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_MOVE_ABSOLUTE,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<Hl", self._idx_chan, pos),
            )
            self._apt.sendpacket(pkt)

        def move_jog(self, direction="fwd"):
            """
            Jogs the axis in forward or backward direction by the number
            of steps that are stored in the controller.

            To set the moving parameters, use the setter for
            `jog_parameters`.

            :param str direction: Direction of jog. 'fwd' for forward,
                'rev' for backward. 'fwd' if invalid argument given

            Example:
                >>> import instruments as ik
                >>> # call the controller
                >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # grab channel 0
                >>> ch = kim.channel[0]
                >>> # set jog parameters
                >>> params = ch.jog_parameters
                >>> params[0] = 2  # move by number of steps
                >>> params[1] = 100  # step size forward
                >>> params[2] = 200  # step size reverse
                >>> ch.jog_parameters = params  # set parameters
                >>> # jog forward (default)
                >>> ch.move_jog()
                >>> # jog reverse
                >>> ch.move_jog('rev')
            """
            if direction == "rev":
                param2 = 0x02
            else:
                param2 = 0x01

            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_MOVE_JOG,
                param1=self._idx_chan,
                param2=param2,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            self._apt.sendpacket(pkt)

        def move_jog_stop(self):
            """Stops the current motor movement.

            Stop a jog command. The regular motor move stop command does
            not work for jogging. This command somehow does...

            .. note:: This information is quite empirical. It would
                only be really needed if jogging parameters are set to
                continuous. The safer method is to set the step range.
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZMOT_MOVE_JOG,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )

            self._apt.sendpacket(pkt)

    _channel_type = PiezoChannel

    # PROPERTIES #

    @property
    def enabled_multi(self):
        """Enable / Query mulitple channel mode.

        For KIM101 controller, where multiple axes can be selected
        simultaneously (i. e., for a mirror mount).

        :setter mode: Channel pair to be activated.
            0:  All channels deactivated
            1:  First channel pair activated (channel 0 & 1)
            2:  Second channel pair activated (channel 2 & 3)
        :type mode: int

        :return: The selected mode:
            0 - multi-channel selection disabled
            1 - Channel 0 & 1 enabled
            2 - Channel 2 & 3 enabled
        :rtype: int

        :raises ValueError: No valid channel pair selected
        :raises TypeError: Invalid controller for this command.

        Example:
            >>> import instruments as ik
            >>> kim = ik.thorlabs.APTPiezoInertiaActuator.open_serial("/dev/ttyUSB0", baud=115200)
            >>> # activate the first two channels
            >>> kim.enabled_multi = 1
            >>> # read back
            >>> kim.enabled_multi
            1
        """
        if self.model_number != "KIM101":
            raise TypeError(
                "This command is only valid with "
                "a KIM101 controller. Your "
                "controller is a {}.".format(self.model_number)
            )

        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.PZMOT_REQ_PARAMS,
            param1=0x2B,
            param2=0x00,
            dest=self.destination,
            source=0x01,
            data=None,
        )

        resp = self.querypacket(
            pkt, expect=_cmds.ThorLabsCommands.PZMOT_GET_PARAMS, expect_data_len=4
        )

        ret_val = int(struct.unpack("<HH", resp.data)[1])

        if ret_val == 5:
            return 1
        elif ret_val == 6:
            return 2
        else:
            return 0

    @enabled_multi.setter
    def enabled_multi(self, mode):
        if self.model_number != "KIM101":
            raise TypeError(
                "This command is only valid with "
                "a KIM101 controller. Your "
                "controller is a {}.".format(self.model_number)
            )

        if mode == 0:
            param = 0x00
        elif mode == 1:
            param = 0x05
        elif mode == 2:
            param = 0x06
        else:
            raise ValueError(
                "Please select a valid mode: 0 - all "
                "disabled, 1 - Channel 1 & 2 enabled, "
                "2 - Channel 3 & 4 enabled."
            )

        pkt = _packets.ThorLabsPacket(
            message_id=_cmds.ThorLabsCommands.PZMOT_SET_PARAMS,
            param1=None,
            param2=None,
            dest=self.destination,
            source=0x01,
            data=struct.pack("<HH", 0x2B, param),
        )

        self.sendpacket(pkt)


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

            :type: `bool`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_REQ_POSCONTROLMODE,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZ_GET_POSCONTROLMODE
            )
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
                data=None,
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
                data=None,
            )
            resp = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.PZ_GET_OUTPUTPOS, expect_data_len=4
            )
            # chan, pos
            _, pos = struct.unpack("<HH", resp.data)
            return pos

        @output_position.setter
        def output_position(self, pos):
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.PZ_SET_OUTPUTPOS,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<HH", self._idx_chan, pos),
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

    _channel_type = StrainGaugeChannel


class APTMotorController(ThorLabsAPT):

    """
    Class representing a Thorlabs APT motor controller.

    .. note:: A motor model must be selected in order to use unitful
        distances.

    Example:
        >>> import instruments as ik
        >>> import instruments.units as u

        >>> # load the controller, a KDC101 cube
        >>> kdc = ik.thorlabs.APTMotorController.open_serial("/dev/ttyUSB0", baud=115200)
        >>> # assign a channel to `ch`
        >>> ch = kdc.channel[0]
        >>> # select the stage that is connected to the controller
        >>> ch.motor_model = 'PRM1-Z8'  # a rotation stage

        >>> # home the stage
        >>> ch.go_home()
        >>> # move to 52 degrees absolute position
        >>> ch.move(u.Quantity(52, u.deg))
        >>> # move 10 degrees back from current position
        >>> ch.move(u.Quantity(-10, u.deg), absolute=False)
    """

    class MotorChannel(ThorLabsAPT.APTChannel):

        """
        Class representing a single motor attached to a Thorlabs APT motor
        controller (`APTMotorController`).
        """

        # INSTANCE VARIABLES #

        _motor_model = None

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
        scale_factors = (u.Quantity(1, "dimensionless"),) * 3

        _motion_timeout = u.Quantity(10, "second")

        __SCALE_FACTORS_BY_MODEL = {
            # TODO: add other tables here.
            re.compile("TST001|BSC00.|BSC10.|MST601"): {
                # Note that for these drivers, the scale factors are identical
                # for position, velcoity and acceleration. This is not true for
                # all drivers!
                "DRV001": (u.Quantity(51200, "count/mm"),) * 3,
                "DRV013": (u.Quantity(25600, "count/mm"),) * 3,
                "DRV014": (u.Quantity(25600, "count/mm"),) * 3,
                "DRV113": (u.Quantity(20480, "count/mm"),) * 3,
                "DRV114": (u.Quantity(20480, "count/mm"),) * 3,
                "FW103": (u.Quantity(25600 / 360, "count/deg"),) * 3,
                "NR360": (u.Quantity(25600 / 5.4546, "count/deg"),) * 3,
            },
            re.compile("TDC001|KDC101"): {
                "MTS25-Z8": (
                    1 / u.Quantity(34304, "mm/count"),
                    NotImplemented,
                    NotImplemented,
                ),
                "MTS50-Z8": (
                    1 / u.Quantity(34304, "mm/count"),
                    NotImplemented,
                    NotImplemented,
                ),
                # TODO: Z8xx and Z6xx models. Need to add regex support to motor models, too.
                "PRM1-Z8": (
                    u.Quantity(1919.64, "count/deg"),
                    NotImplemented,
                    NotImplemented,
                ),
            },
        }

        __STATUS_BIT_MASK = {
            "CW_HARD_LIM": 0x00000001,
            "CCW_HARD_LIM": 0x00000002,
            "CW_SOFT_LIM": 0x00000004,
            "CCW_SOFT_LIM": 0x00000008,
            "CW_MOVE_IN_MOTION": 0x00000010,
            "CCW_MOVE_IN_MOTION": 0x00000020,
            "CW_JOG_IN_MOTION": 0x00000040,
            "CCW_JOG_IN_MOTION": 0x00000080,
            "MOTOR_CONNECTED": 0x00000100,
            "HOMING_IN_MOTION": 0x00000200,
            "HOMING_COMPLETE": 0x00000400,
            "INTERLOCK_STATE": 0x00001000,
        }

        # IK-SPECIFIC PROPERTIES #
        # These properties don't correspond to any particular functionality
        # of the underlying device, but control how we interact with it.

        @property
        def motion_timeout(self):
            """
            Gets/sets the motor channel motion timeout.

            :units: Seconds
            :type: `~pint.Quantity`
            """
            return self._motion_timeout

        @motion_timeout.setter
        def motion_timeout(self, newval):
            self._motion_timeout = assume_units(newval, u.second)

        # UNIT CONVERSION METHODS #

        def _set_scale(self, motor_model):
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
            logger.warning(
                "Scale factors for controller %s and motor %s are " "unknown",
                self._apt.model_number,
                motor_model,
            )

        # We copy the docstring below, so it's OK for this method
        # to not have a docstring of its own.
        # pylint: disable=missing-docstring
        def set_scale(self, motor_model):
            warnings.warn(
                "The set_scale method has been deprecated in favor "
                "of the motor_model property.",
                DeprecationWarning,
            )
            return self._set_scale(motor_model)

        set_scale.__doc__ = _set_scale.__doc__

        @property
        def motor_model(self):
            """
            Gets or sets the model name of the attached motor.
            Note that the scale factors for this motor channel are based on the model
            of the attached motor and the specifications of the driver of which
            this is a channel, such that setting a new motor model will update
            the scale factors accordingly.

            :type: `str` or `None`
            """
            return self._motor_model

        @motor_model.setter
        def motor_model(self, newval):
            self._set_scale(newval)
            self._motor_model = newval

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
                data=None,
            )
            # The documentation claims there are 14 data bytes, but it seems
            # there are sometimes some extra random ones...
            resp_data = self._apt.querypacket(
                pkt,
                expect=_cmds.ThorLabsCommands.MOT_GET_POSCOUNTER,
                expect_data_len=14,
            ).data[:14]
            # ch_ident, position, enc_count, status_bits
            _, _, _, status_bits = struct.unpack("<HLLL", resp_data)

            status_dict = {
                key: (status_bits & bit_mask > 0)
                for key, bit_mask in self.__STATUS_BIT_MASK.items()
            }

            return status_dict

        @property
        def position(self):
            """
            Gets the current position of the specified motor channel

            :type: `~pint.Quantity`
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_REQ_POSCOUNTER,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            response = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOT_GET_POSCOUNTER, expect_data_len=6
            )
            # chan, pos
            _, pos = struct.unpack("<Hl", response.data)
            return u.Quantity(pos, "counts") / self.scale_factors[0]

        @property
        def position_encoder(self):
            """
            Gets the position of the encoder of the specified motor channel

            :type: `~pint.Quantity`
            :units: Encoder ``counts``
            """
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_REQ_ENCCOUNTER,
                param1=self._idx_chan,
                param2=0x00,
                dest=self._apt.destination,
                source=0x01,
                data=None,
            )
            response = self._apt.querypacket(
                pkt, expect=_cmds.ThorLabsCommands.MOT_GET_ENCCOUNTER, expect_data_len=6
            )
            # chan, pos
            _, pos = struct.unpack("<Hl", response.data)
            return u.Quantity(pos, "counts")

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
                data=None,
            )
            _ = self._apt.querypacket(
                pkt,
                expect=_cmds.ThorLabsCommands.MOT_MOVE_HOMED,
                timeout=self.motion_timeout,
            )

        def move(self, pos, absolute=True):
            """
            Instructs the specified motor channel to move to a specific
            location. The provided position can be either an absolute or
            relative position.

            :param pos: The position to move to. Provided value will be
                converted to encoder counts.
            :type pos: `~pint.Quantity`
            :units pos: As specified, or assumed to of units encoder counts

            :param bool absolute: Specify if the position is a relative or
                absolute position. ``True`` means absolute, while ``False``
                is for a relative move.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u

                >>> # load the controller, a KDC101 cube
                >>> kdc = ik.thorlabs.APTMotorController.open_serial("/dev/ttyUSB0", baud=115200)
                >>> # assign a channel to `ch`
                >>> ch = kdc.channel[0]
                >>> # select the stage that is connected to the controller
                >>> ch.motor_model = 'PRM1-Z8'  # a rotation stage

                >>> # move to 32 degrees absolute position
                >>> ch.move(u.Quantity(32, u.deg))

                >>> # move 10 degrees forward from current position
                >>> ch.move(u.Quantity(10, u.deg), absolute=False)
            """
            # Handle units as follows:
            # 1. Treat raw numbers as encoder counts.
            # 2. If units are provided (as a Quantity), check if they're encoder
            #    counts. If they aren't, apply scale factor.
            if not isinstance(pos, u.Quantity):
                pos_ec = int(pos)
            else:
                if pos.units == u.counts:
                    pos_ec = int(pos.magnitude)
                else:
                    scaled_pos = pos * self.scale_factors[0]
                    # Force a unit error.
                    try:
                        pos_ec = int(scaled_pos.to(u.counts).magnitude)
                    except:
                        raise ValueError(
                            "Provided units are not compatible "
                            "with current motor scale factor."
                        )

            # Now that we have our position as an integer number of encoder
            # counts, we're good to move.
            pkt = _packets.ThorLabsPacket(
                message_id=_cmds.ThorLabsCommands.MOT_MOVE_ABSOLUTE
                if absolute
                else _cmds.ThorLabsCommands.MOT_MOVE_RELATIVE,
                param1=None,
                param2=None,
                dest=self._apt.destination,
                source=0x01,
                data=struct.pack("<Hl", self._idx_chan, pos_ec),
            )

            _ = self._apt.querypacket(
                pkt,
                expect=_cmds.ThorLabsCommands.MOT_MOVE_COMPLETED,
                timeout=self.motion_timeout,
            )

    _channel_type = MotorChannel

    # CONTROLLER PROPERTIES AND METHODS #
