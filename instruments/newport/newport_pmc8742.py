#!/usr/bin/env python
"""
Provides support for the Newport Pico Motor Controller 8742

Note that the class is currently only tested with one controller connected,
however, a main controller / secondary controller setup has also been
implemented already. Commands are as described in the Picomotor manual.

If a connection via TCP/IP is opened, the standard port that these devices
listen to is 23.

If you have only one controller connected, everything should work out of
the box. Please only use axiss 0 through 3.

If you have multiple controllers connected (up to 31), you need to set the
addresses of each controller. This can be done with this this class. See,
e.g., routines for `controller_address`, `scan_controller`, and `scan`.
Also make sure that you set `multiple_controllers` to `True`. This is
used for internal handling of the class only and does not communicate with
the instruments.
If you run with multiple controllers, the axiss are as following:
Ch 0 - 3 -> Motors 1 - 4 on controller with address 1
Ch 4 - 7 -> Motors 1 - 4 on controller with address 2
Ch i - i+4 -> Motors 1 - 4 on controller with address i / 4 + 1 (with i%4 = 0)

All network commands only work with the main controller (this should make
sense).

If in multiple controller mode, you can always send controller specific
commands by sending them to one individual axis of that controller.
Any axis works!
"""

# IMPORTS #

from enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units, ProxyList

# pylint: disable=too-many-lines


class PicoMotorController8742(Instrument):
    """Newport Picomotor Controller 8742 Communications Class

    Use this class to communicate with the picomotor controller 8742.
    Single-controller and multi-controller setup can be used.

    Device can be talked to via TCP/IP or over USB.
    FixMe: InstrumentKit currently does not communicate correctly via USB!

    Example for TCP/IP controller in single controller mode:
        >>> import instruments as ik
        >>> ip = "192.168.1.2"
        >>> port = 23   # this is the default port
        >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
        >>> motor1 = inst.axis[0]
        >>> motor1.move_relative = 100

    Example for communications via USB:
        >>> import instruments as ik
        >>> pid = 0x4000
        >>> vid = 0x104d
        >>> ik.newport.PicoMotorController8742.open_usb(pid=pid, vid=vid)
        >>> motor3 = inst.axis[2]
        >>> motor3.move_absolute = -200

    Example for multicontrollers with controller addresses 1 and 2:
        >>> import instruments as ik
        >>> ip = "192.168.1.2"
        >>> port = 23   # this is the default port
        >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
        >>> inst.multiple_controllers = True
        >>> contr1mot1 = inst.axis[0]
        >>> contr2mot1 = inst.axis[4]
        >>> contr1mot1.move_absolute = 200
        >>> contr2mot1.move_relative = -212
    """

    def __init__(self, filelike):
        """Initialize the PicoMotorController class."""
        super().__init__(filelike)

        # terminator
        self.terminator = "\r\n"

        # setup
        self._multiple_controllers = False

    # INNER CLASSES #

    class Axis:
        """PicoMotorController8742 Axis class for individual motors."""

        def __init__(self, parent, idx):
            """Initialize the axis with the parent and the number.

            :raises IndexError: Axis accessed looks like a main / secondary
                setup, but the flag for `multiple_controllers` is not set
                appropriately. See introduction.
            """
            if not isinstance(parent, PicoMotorController8742):
                raise TypeError("Don't do that.")

            if idx > 3 and not parent.multiple_controllers:
                raise IndexError(
                    "You requested an axis that is only "
                    "available in multi controller mode, "
                    "however, have not enabled it. See "
                    "`multi_controllers` routine."
                )

            # set controller
            self._parent = parent
            self._idx = idx % 4 + 1

            # set _address:
            if self._parent.multiple_controllers:
                self._address = f"{idx // 4 + 1}>"
            else:
                self._address = ""

        # ENUMS #

        class MotorType(IntEnum):
            """IntEnum Class containing valid MotorTypes

            Use this enum to set the motor type. You can select that no or an
            unkown motor are connected. See also `motor_check` command to set
            these values per controller automatically.
            """

            none = 0
            unknown = 1
            tiny = 2
            standard = 3

        # PROPERTIES #

        @property
        def acceleration(self):
            """Get / set acceleration of axis in steps / sec^2.

            Valid values are between 1 and 200,000 (steps) 1 / sec^2 with the
            default as 100,000 (steps) 1 / sec^2. If quantity is not unitful,
            it is assumed that 1 / sec^2 is chosen.

            :return: Acceleration in 1 / sec^2
            :rtype: u.Quantity(int)

            :raises ValueError: Limit is out of bound.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.acceleration = u.Quantity(500, 1/u.s**-2)
            """
            return assume_units(int(self.query("AC?")), u.s ** -2)

        @acceleration.setter
        def acceleration(self, value):
            value = int(assume_units(value, u.s ** -2).to(u.s ** -2).magnitude)
            if not 1 <= value <= 200000:
                raise ValueError(
                    f"Acceleration must be between 1 and "
                    f"200,000 s^-2 but is {value}."
                )
            self.sendcmd(f"AC{value}")

        @property
        def home_position(self):
            """Get / set home position

            The home position of the device is used, e.g., when moving
            to a specific position instead of a relative move. Valid values
            are between -2147483648 and 2147483647.

            :return: Home position.
            :rtype: int

            :raises ValueError: Set value is out of range.

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.home_position = 444
            """
            return int(self.query("DH?"))

        @home_position.setter
        def home_position(self, value):
            if not -2147483648 <= value <= 2147483647:
                raise ValueError(
                    f"Home position must be between -2147483648 "
                    f"and 2147483647, but is {value}."
                )
            self.sendcmd(f"DH{int(value)}")

        @property
        def is_stopped(self):
            """Get if an axis is stopped (not moving).

            :return: Is the axis stopped?
            :rtype: bool

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.is_stopped
                True
            """
            return bool(int(self.query("MD?")))

        @property
        def motor_type(self):
            """Set / get the type of motor connected to the axis.

            Use a `MotorType` IntEnum to set this motor type.

            :return: Motor type set.
            :rtype: MotorType

            :raises TypeError: Set motor type is not of type `MotorType`.

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.motor_type = ax.MotorType.tiny
            """
            retval = int(self.query("QM?"))
            return self.MotorType(retval)

        @motor_type.setter
        def motor_type(self, value):
            if not isinstance(value, self.MotorType):
                raise TypeError(
                    f"Set motor type must be of type `MotorType` "
                    f"but is of type {type(value)}."
                )
            self.sendcmd(f"QM{value.value}")

        @property
        def move_absolute(self):
            """Get / set the absolute target position of a motor.

            Set with absolute position in steps. Valid values between
            -2147483648 and +2147483647.
            See also: `home_position`.

            :return: Absolute motion target position.
            :rtype: int

            :raises ValueError: Requested position out of range.

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.move_absolute = 100
            """
            return int(self.query("PA?"))

        @move_absolute.setter
        def move_absolute(self, value):
            if not -2147483648 <= value <= 2147483647:
                raise ValueError(
                    f"Set position must be between -2147483648 "
                    f"and 2147483647, but is {value}."
                )
            self.sendcmd(f"PA{int(value)}")

        @property
        def move_relative(self):
            """Get / set the relative target position of a motor.

            Set with relative motion in steps. Valid values between
            -2147483648 and +2147483647.
            See also: `home_position`.

            :return: Relative motion target position.
            :rtype: int

            :raises ValueError: Requested motion out of range.

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.move_relative = 100
            """
            return int(self.query("PR?"))

        @move_relative.setter
        def move_relative(self, value):
            if not -2147483648 <= value <= 2147483647:
                raise ValueError(
                    f"Set motion must be between -2147483648 "
                    f"and 2147483647, but is {value}."
                )
            self.sendcmd(f"PR{int(value)}")

        @property
        def position(self):
            """Queries current, actual position of motor.

            Positions are with respect to the home position.

            :return: Current position in steps.
            :rtype: int

            Example:
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.position
                123
            """
            return int(self.query("TP?"))

        @property
        def velocity(self):
            """Get / set velocty of the connected motor (unitful).

            Velocity is given in (steps) per second (1/s).
            If a `MotorType.tiny` motor is connected, the maximum velocity
            allowed is 1750 /s, otherwise 2000 /s.
            If no units are given, 1/s are assumed.

            :return: Velocity in 1/s
            :rtype: u.Quantity(int)

            :raises ValueError: Set value is out of the allowed range.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.velocity = u.Quantity(500, 1/u.s)
            """
            retval = int(self.query("VA?"))
            return u.Quantity(retval, 1 / u.s)

        @velocity.setter
        def velocity(self, value):
            if self.motor_type == self.MotorType.tiny:
                max_velocity = 1750
            else:
                max_velocity = 2000

            value = int(assume_units(value, 1 / u.s).to(1 / u.s).magnitude)
            if not 0 < value <= max_velocity:
                raise ValueError(
                    f"The maximum allowed velocity for the set "
                    f"motor is {max_velocity}. The requested "
                    f"velocity of {value} is out of range."
                )
            self.sendcmd(f"VA{value}")

        # METHODS #

        def move_indefinite(self, direction):
            """Move the motor indefinitely in the specific direction.

            To stop motion, issue `stop_motion` or `abort_motion` command.
            Direction is defined as a string of either "+" or "-".

            :param direction: Direction in which to move the motor, "+" or "-"
            :type direction: str

            Example:
                >>> from time import sleep
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.move_indefinite("+")
                >>> sleep(1)   # wait a second
                >>> ax.stop()
            """
            if direction in ["+", "-"]:
                self.sendcmd(f"MV{direction}")

        def stop(self):
            """Stops the specific axis if in motion.

            Example:
                >>> from time import sleep
                >>> import instruments as ik
                >>> ip = "192.168.1.2"
                >>> port = 23   # this is the default port
                >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
                >>> ax = inst.axis[0]
                >>> ax.move_indefinite("+")
                >>> sleep(1)   # wait a second
                >>> ax.stop()
            """
            self.sendcmd("ST")

        # CONTROLLER SPECIFIC PROPERTIES #

        @property
        def controller_address(self):
            """Get / set the controller address.

            Valid address values are between 1 and 31. For setting up multiple
            instruments, see `multiple_controllers`.

            :return: Address of this device if secondary, otherwise `None`
            :rtype: int
            """
            retval = int(self.query("SA?", axs=False))
            return retval

        @controller_address.setter
        def controller_address(self, newval):
            self.sendcmd(f"SA{int(newval)}", axs=False)

        @property
        def controller_configuration(self):
            """Get / set configuration of some of the controller’s features.

            Configuration is given as a bit mask. If changed, please save
            the settings afterwards if you would like to do so. See
            `save_settings`.

            The bitmask to be set can be either given as a number, or as a
            string of the mask itself. The following values are equivalent:
            3, 0b11, "11"

            Bit 0:
                Value 0: Perform auto motor detection. Check and set motor
                    type automatically when commanded to move.
                Value 1: Do not perform auto motor detection on move.
            Bit 1:
                Value 0: Do not scan for motors connected to controllers upon
                    reboot (Performs ‘MC’ command upon power-up, reset or
                    reboot).
                Value 1: Scan for motors connected to controller upon power-up
                    or reset.

            :return: Bitmask of the controller configuration.
            :rtype: str, binary configuration
            """
            return self.query("ZZ?", axs=False)

        @controller_configuration.setter
        def controller_configuration(self, value):
            if isinstance(value, str):
                self.sendcmd(f"ZZ{value}", axs=False)
            else:
                self.sendcmd(f"ZZ{str(bin(value))[2:]}", axs=False)

        @property
        def error_code(self):
            """Get error code only.

            Error code0 means no error detected.

            :return: Error code.
            :rtype: int
            """
            return int(self.query("TE?", axs=False))

        @property
        def error_code_and_message(self):
            """Get error code and message.

            :return: Error code, error message
            :rtype: int, str
            """
            retval = self.query("TB?", axs=False)
            err_code, err_msg = retval.split(",")
            err_code = int(err_code)
            err_msg = err_msg.strip()
            return err_code, err_msg

        @property
        def firmware_version(self):
            """Get the controller firmware version."""
            return self.query("VE?", axs=False)

        @property
        def name(self):
            """Get the name of the controller."""
            return self.query("*IDN?", axs=False)

        # CONTROLLER SPECIFIC METHODS #

        def abort_motion(self):
            """Instantaneously stops any motion in progress."""
            self.sendcmd("AB", axs=False)

        def motor_check(self):
            """Check what motors are connected and set parameters.

            Use the save command `save_settings` if you want to save the
            configuration to the non-volatile memory.
            """
            self.sendcmd("MC", axs=False)

        def purge(self):
            """Purge the non-volatile memory of the controller.

            Perform a hard reset and reset all the saved variables. The
            following variables are reset to factory settings:
            1. Hostname
            2. IP Mode
            3. IP Address
            4. Subnet mask address
            5. Gateway address
            6. Configuration register
            7. Motor type
            8. Desired Velocity
            9. Desired Acceleration
            """
            self.sendcmd("XX", axs=False)

        def recall_parameters(self, value=0):
            """Recall parameter set.

            This command restores the controller working parameters from values
            saved in its non-volatile memory. It is useful when, for example,
            the user has been exploring and changing parameters (e.g., velocity)
            but then chooses to reload from previously stored, qualified
            settings. Note that “*RCL 0” command just restores the working
            parameters to factory default settings. It does not change the
            settings saved in EEPROM.

            :param value: 0 -> Recall factory default,
                1 -> Recall last saved settings
            :type int:
            """
            self.sendcmd(f"*RCL{1 if value else 0}", axs=False)

        def reset(self):
            """Reset the controller.

            Perform a soft reset. Saved variables are not deleted! For a
            hard reset, see the `purge` command.

            ..note:: It might take up to 30 seconds to re-establish
            communications via TCP/IP
            """
            self.sendcmd("*RST", axs=False)

        def save_settings(self):
            """Save user settings.

            This command saves the controller settings in its non-volatile memory.
            The controller restores or reloads these settings to working registers
            automatically after system reset or it reboots. The purge
            command is used to clear non-volatile memory and restore to factory
            settings. Note that the SM saves parameters for all motors.

            Saves the following variables:
            1. Controller address
            2. Hostname
            3. IP Mode
            4. IP Address
            5. Subnet mask address
            6. Gateway address
            7. Configuration register
            8. Motor type
            9. Desired Velocity
            10. Desired Acceleration
            """
            self.sendcmd("SM", axs=False)

        # SEND AND QUERY #

        def sendcmd(self, cmd, axs=True):
            """Send a command to an axis object.

            :param cmd: Command
            :type cmd: str
            :param axs: Send axis address along? Not used for controller
                commands. Defaults to `True`
            :type axs: bool
            """
            if axs:
                command = f"{self._address}{self._idx}{cmd}"
            else:
                command = f"{self._address}{cmd}"
            self._parent.sendcmd(command)

        def query(self, cmd, size=-1, axs=True):
            """Query for an axis object.

            :param cmd: Command
            :type cmd: str
            :param size: bytes to read, defaults to "until terminator" (-1)
            :type size: int
            :param axs: Send axis address along? Not used for controller
                commands. Defaults to `True`
            :type axs: bool

            :raises IOError: The wrong axis answered.
            """
            if axs:
                command = f"{self._address}{self._idx}{cmd}"
            else:
                command = f"{self._address}{cmd}"

            retval = self._parent.query(command, size=size)

            if retval[: len(self._address)] != self._address:
                raise OSError(
                    f"Expected to hear back from secondary "
                    f"controller {self._address}, instead "
                    f"controller {retval[:len(self._address)]} "
                    f"answered."
                )

            return retval[len(self._address) :]

    @property
    def axis(self):
        """Return an axis object.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> ax = inst.axis[0]
        """
        return ProxyList(self, self.Axis, range(31 * 4))

    @property
    def controller_address(self):
        """Get / set the controller address.

        Valid address values are between 1 and 31. For setting up multiple
        instruments, see `multiple_controllers`.

        :return: Address of this device if secondary, otherwise `None`
        :rtype: int

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.controller_address = 13
        """
        return self.axis[0].controller_address

    @controller_address.setter
    def controller_address(self, newval):
        self.axis[0].controller_address = newval

    @property
    def controller_configuration(self):
        """Get / set configuration of some of the controller’s features.

        Configuration is given as a bit mask. If changed, please save
        the settings afterwards if you would like to do so. See
        `save_settings`.

        Bit 0:
            Value 0: Perform auto motor detection. Check and set motor
                type automatically when commanded to move.
            Value 1: Do not perform auto motor detection on move.
        Bit 1:
            Value 0: Do not scan for motors connected to controllers upon
                reboot (Performs ‘MC’ command upon power-up, reset or
                reboot).
            Value 1: Scan for motors connected to controller upon power-up
                or reset.

        :return: Bitmask of the controller configuration.
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.controller_configuration = "11"
        """
        return self.axis[0].controller_configuration

    @controller_configuration.setter
    def controller_configuration(self, value):
        self.axis[0].controller_configuration = value

    @property
    def dhcp_mode(self):
        """Get / set if device is in DHCP mode.

        If not in DHCP mode, a static IP address, gateway, and netmask
        must be set.

        :return: Status if DHCP mode is enabled
        :rtype: `bool`

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.dhcp_mode = True
        """
        return bool(self.query("IPMODE?"))

    @dhcp_mode.setter
    def dhcp_mode(self, newval):
        nn = 1 if newval else 0
        self.sendcmd(f"IPMODE{nn}")

    @property
    def error_code(self):
        """Get error code only.

        Error code0 means no error detected.

        :return: Error code.
        :rtype: int

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.error_code
            0
        """
        return self.axis[0].error_code

    @property
    def error_code_and_message(self):
        """Get error code and message.

        :return: Error code, error message
        :rtype: int, str

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.error_code
            (0, 'NO ERROR DETECTED')
        """
        return self.axis[0].error_code_and_message

    @property
    def firmware_version(self):
        """Get the controller firmware version.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.firmware_version
            '8742 Version 2.2 08/01/13'
        """
        return self.axis[0].firmware_version

    @property
    def gateway(self):
        """Get / set the gateway of the instrument.

        :return: Gateway address
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.gateway = "192.168.1.1"
        """
        return self.query("GATEWAY?")

    @gateway.setter
    def gateway(self, value):
        self.sendcmd(f"GATEWAY {value}")

    @property
    def hostname(self):
        """Get / set the hostname of the instrument.

        :return: Hostname
        :rtype: `str`

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.hostname = "asdf"
        """
        return self.query("HOSTNAME?")

    @hostname.setter
    def hostname(self, value):
        self.sendcmd(f"HOSTNAME {value}")

    @property
    def ip_address(self):
        """Get / set the IP address of the instrument.

        :return: IP address
        :rtype: `str`

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.ip_address = "192.168.1.2"
        """
        return self.query("IPADDR?")

    @ip_address.setter
    def ip_address(self, value):
        self.sendcmd(f"IPADDR {value}")

    @property
    def mac_address(self):
        """Get the MAC address of the instrument.

        :return: MAC address
        :rtype: `str`

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.mac_address
            '5827809, 8087'
        """
        return self.query("MACADDR?")

    @property
    def multiple_controllers(self):
        """Get / set if multiple controllers are used.

        By default, this is initialized as `False`. Set to `True` if you
        have a main controller / secondary controller via RS-485 network
        set up.

        Instrument commands will always be sent to main controller.
        Axis specific commands will be set to the axis chosen, see
        `axis` description.

        :return: Status if multiple controllers are activated
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.multiple_controllers = True
        """
        return self._multiple_controllers

    @multiple_controllers.setter
    def multiple_controllers(self, newval):
        self._multiple_controllers = True if newval else False

    @property
    def name(self):
        """Get the name of the controller.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.name
            'New_Focus 8742 v2.2 08/01/13 13991'
        """
        return self.axis[0].name

    @property
    def netmask(self):
        """Get / set the Netmask of the instrument.

        :return: Netmask
        :rtype: `str`

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.netmask = "255.255.255.0"
        """
        return self.query("NETMASK?")

    @netmask.setter
    def netmask(self, value):
        self.sendcmd(f"NETMASK {value}")

    @property
    def scan_controllers(self):
        """RS-485 controller address map query of all controllers.

        32 bit string that represents the following:
            Bit:    Value: (True: 1, False: 0)
            0       Address conflict?
            1:      Controller with address 1 exists?
                ...
            31:      Controller with address 31 exists

        Bits 1—31 are one-to-one mapped to controller addresses 1—31. The
        bit value is set to 1 only when there are no conflicts with that
        address. For example, if the master controller determines that there
        are unique controllers at addresses 1,2, and 7 and more than one
        controller at address 23, this query will return 135. The binary
        representation of 135 is 10000111. Bit #0 = 1 implies that the scan
        found at lease one address conflict during last scan. Bit #1,2, 7 = 1
        implies that the scan found controllers with addresses 1,2, and 7
        that do not conflict with any other controller.

        :return: Binary representation of controller configuration bitmask.
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.scan_controllers
            "10000111"
        """
        return self.query("SC?")

    @property
    def scan_done(self):
        """Queries if a controller scan is done or not.

        :return: Controller scan done?
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.scan_done
            True
        """
        return bool(int(self.query("SD?")))

    # METHODS #

    def abort_motion(self):
        """Instantaneously stop any motion in progress.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.abort_motion()
        """
        self.axis[0].abort_motion()

    def motor_check(self):
        """Check what motors are connected and set parameters.

        Use the save command `save_settings` if you want to save the
        configuration to the non-volatile memory.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.motor_check()
        """
        self.axis[0].motor_check()

    def scan(self, value=2):
        """Initialize and set controller addresses automatically.

        Scans the RS-485 network for connected controllers and set the
        addresses automatically. Three possible scan modes can be
        selected:
        Mode 0:
            Primary controller scans the network but does not resolve
            any address conflicts.
        Mode 1:
            Primary controller scans the network and resolves address
            conflicts, if any. This option preserves the non-conflicting
            addresses and reassigns the conflicting addresses starting
            with the lowest available address.
        Mode 2 (default):
            Primary controller reassigns the addresses of all
            controllers on the network in a sequential order starting
            with master controller set to address 1.

        See also: `scan_controllers` property.

        :param value: Scan mode.
        :type: int

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.scan(2)
        """
        self.sendcmd(f"SC{value}")

    def purge(self):
        """Purge the non-volatile memory of the controller.

        Perform a hard reset and reset all the saved variables. The
        following variables are reset to factory settings:
        1. Hostname
        2. IP Mode
        3. IP Address
        4. Subnet mask address
        5. Gateway address
        6. Configuration register
        7. Motor type
        8. Desired Velocity
        9. Desired Acceleration

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.purge()
        """
        self.axis[0].purge()

    def recall_parameters(self, value=0):
        """Recall parameter set.

        This command restores the controller working parameters from values
        saved in its non-volatile memory. It is useful when, for example,
        the user has been exploring and changing parameters (e.g., velocity)
        but then chooses to reload from previously stored, qualified
        settings. Note that “*RCL 0” command just restores the working
        parameters to factory default settings. It does not change the
        settings saved in EEPROM.

        :param value: 0 -> Recall factory default,
            1 -> Recall last saved settings
        :type value: int

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.recall_parameters(1)
        """
        self.axis[0].recall_parameters(value)

    def reset(self):
        """Reset the controller.

        Perform a soft reset. Saved variables are not deleted! For a
        hard reset, see the `purge` command.

        ..note:: It might take up to 30 seconds to re-establish
        communications via TCP/IP

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.reset()
        """
        self.axis[0].reset()

    def save_settings(self):
        """Save user settings.

        This command saves the controller settings in its non-volatile memory.
        The controller restores or reloads these settings to working registers
        automatically after system reset or it reboots. The purge
        command is used to clear non-volatile memory and restore to factory
        settings. Note that the SM saves parameters for all motors.

        Saves the following variables:
        1. Controller address
        2. Hostname
        3. IP Mode
        4. IP Address
        5. Subnet mask address
        6. Gateway address
        7. Configuration register
        8. Motor type
        9. Desired Velocity
        10. Desired Acceleration

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> ip = "192.168.1.2"
            >>> port = 23   # this is the default port
            >>> inst = ik.newport.PicoMotorController8742.open_tcpip(ip, port)
            >>> inst.save_settings()
        """
        self.axis[0].save_settings()

    # QUERY #

    def query(self, cmd, size=-1):
        """Query's the device and returns ASCII string.

        Must be queried as a raw string with terminator line ending. This is
        currently not implemented in instrument and therefore must be called
        directly from file.

        Sometimes, the instrument sends an undecodable 6 byte header along
        (usually for the first query). We'll catch it with a try statement.
        The 6 byte header was also remarked in this matlab script:
        https://github.com/cnanders/matlab-newfocus-model-8742
        """
        self.sendcmd(cmd)
        retval = self.read_raw(size=size)
        try:
            retval = retval.decode("utf-8")
        except UnicodeDecodeError:
            retval = retval[6:].decode("utf-8")

        return retval
