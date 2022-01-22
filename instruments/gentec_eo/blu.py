"""Support for Gentec-EO Blu devices."""


# IMPORTS #####################################################################

from enum import Enum
from time import sleep

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class Blu(Instrument):
    """Communicate with Gentec-eo BLU power / energy meter interfaces.

    These instruments communicate via USB or via bluetooth. The
    bluetooth sender / receiver that is provided with the instrument is
    simply emulating a COM port. This routine cannot pair the device
    with bluetooth, but once it is paired, it can communicate with the
    port. Alternatively, you can plug the device into the computer using
    a USB cable.

    .. warning:: If commands are issued too fast, the device will not
        answer. Experimentally, a 1 ms delay should be enough to get the
        device into answering mode. Keep this in mind when issuing many
        commands at once. No wait time included in this class.

    .. note:: The instrument also has a possiblity to read a continuous
        data stream. This is currently not implemented here since it
        would have to be threaded out.

    Example:
        >>> import instruments as ik
        >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
        >>> inst.current_value
        3.004 W
    """

    def __init__(self, filelike):
        super().__init__(filelike)

        # use a terminator for blu, even though none required
        self.terminator = "\r\n"

        # define the power mode
        self._power_mode = None

        # acknowledgement message
        self._ack_message = "ACK"

    def _ack_expected(self, msg=""):
        """Set up acknowledgement checking."""
        return self._ack_message

    # ENUMS #

    class Scale(Enum):
        """Available scales for Blu devices.

        The following list maps available scales of the Blu devices
        to the respective indexes. All scales are either in watts or
        joules, depending if power or energy mode is activated.
        Furthermore, the maximum value that can be measured determines
        the name of the scale to be set. Prefixes are given in the
        `enum` class while the unit is omitted since it depends on the
        mode the head is in.
        """

        max1pico = "00"
        max3pico = "01"
        max10pico = "02"
        max30pico = "03"
        max100pico = "04"
        max300pico = "05"
        max1nano = "06"
        max3nano = "07"
        max10nano = "08"
        max30nano = "09"
        max100nano = "10"
        max300nano = "11"
        max1micro = "12"
        max3micro = "13"
        max10micro = "14"
        max30micro = "15"
        max100micro = "16"
        max300micro = "17"
        max1milli = "18"
        max3milli = "19"
        max10milli = "20"
        max30milli = "21"
        max100milli = "22"
        max300milli = "23"
        max1 = "24"
        max3 = "25"
        max10 = "26"
        max30 = "27"
        max100 = "28"
        max300 = "29"
        max1kilo = "30"
        max3kilo = "31"
        max10kilo = "32"
        max30kilo = "33"
        max100kilo = "34"
        max300kilo = "35"
        max1Mega = "36"
        max3Mega = "37"
        max10Mega = "38"
        max30Mega = "39"
        max100Mega = "40"
        max300Mega = "41"

    # PROPERTIES #

    @property
    def anticipation(self):
        """Get / Set anticipation.

        This command is used to enable or disable the anticipation
        processing when the device is reading from a wattmeter. The
        anticipation is a software-based acceleration algorithm that
        provides faster readings using the detector’s calibration.

        :return: Is anticipation enabled or not.
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.anticipation
            True
            >>> inst.anticipation = False
        """
        return self._value_query("*GAN", tp=int) == 1

    @anticipation.setter
    def anticipation(self, newval):
        sendval = 1 if newval else 0
        self.sendcmd(f"*ANT{sendval}")

    @property
    def auto_scale(self):
        """Get / Set auto scale on the device.

        :return: Status of auto scale enabled feature.
        :rtype: bool

        :raises ValueError: The command was not acknowledged by the
            device.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.auto_scale
            True
            >>> inst.auto_scale = False
        """
        resp = self._value_query("*GAS", tp=int)
        return resp == 1

    @auto_scale.setter
    def auto_scale(self, newval):
        sendval = 1 if newval else 0
        self.sendcmd(f"*SAS{sendval}")

    @property
    def available_scales(self):
        """Get available scales from connected device.

        :return: Scales currently available on device.
        :rtype: :class:`Blu.Scale`

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.available_scales
            [<Scale.max100milli: '22'>, <Scale.max300milli: '23'>,
            <Scale.max1: '24'>, <Scale.max3: '25'>, <Scale.max10: '26'>,
            <Scale.max30: '27'>, <Scale.max100: '28'>]
        """
        # set no terminator and a 1 second timeout
        _terminator = self.terminator
        self.terminator = ""
        _timeout = self.timeout
        self.timeout = u.Quantity(1, u.s)

        try:
            # get the response
            resp = self._no_ack_query("*DVS").split("\r\n")
        finally:
            # set back terminator and 3 second timeout
            self.terminator = _terminator
            self.timeout = _timeout

        # prepare return
        retlist = []  # init return list of enums
        for line in resp:
            if len(line) > 0:  # account for empty lines
                index = line[line.find("[") + 1 : line.find("]")]
                retlist.append(self.Scale(index))
        return retlist

    @property
    def battery_state(self):
        """Get the charge state of the battery.

        :return: Charge state of battery
        :rtype: u.percent

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.battery_state
            array(100.) * %
        """
        resp = self._no_ack_query("*QSO").rstrip()
        resp = float(resp[resp.find("=") + 1 : len(resp)])
        return u.Quantity(resp, u.percent)

    @property
    def current_value(self):
        """Get the currently measured value (unitful).

        :return: Currently measured value
        :rtype: u.Quantity

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.current_value
            3.004 W
        """
        if self._power_mode is None:
            _ = self.measure_mode  # determine the power mode
            sleep(0.01)

        unit = u.W if self._power_mode else u.J
        return u.Quantity(float(self._no_ack_query("*CVU")), unit)

    @property
    def head_type(self):
        """Get the head type information.

        :return: Type of instrument head.
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.head_type
            'NIG : 104552, Wattmeter, V1.95'
        """
        return self._no_ack_query("*GFW")

    @property
    def measure_mode(self):
        """Get the current measurement mode.

        Potential return values are 'power', which inidcates power mode
        in W and 'sse', indicating single shot energy mode in J.

        :return: 'power' if in power mode, 'sse' if in single shot
            energy mode.
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.measure_mode
            'power'
        """
        resp = self._value_query("*GMD", tp=int)
        if resp == 0:
            self._power_mode = True
            return "power"
        else:
            self._power_mode = False
            return "sse"

    @property
    def new_value_ready(self):
        """Get status if a new value is ready.

        This command is used to check whether a new value is available
        from the device. Though optional, its use is recommended when
        used with single pulse operation.

        :return: Is a new value ready?
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.new_value_ready
            False
        """
        resp = self._no_ack_query("*NVU")
        return False if resp.find("Not") > -1 else True

    @property
    def scale(self):
        """Get / Set measurement scale.

        The measurement scales are chosen from the the `Scale` enum
        class. Scales are either in watts or joules, depending on what
        state the power meter is currently in.

        .. note:: Setting a scale manually will automatically turn of
            auto scale.

        :return: Scale that is currently set.
        :rtype: :class:`Blu.Scale`

        :raises ValueError: The command was not acknowledged by the
            device. A scale that is not available might have been
            selected. Use `available_scales` to display scales that
            are possible on your device.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.scale = inst.Scale.max3
            >>> inst.scale
            <Scale.max3: '25'>
        """
        return self.Scale(self._value_query("*GCR"))

    @scale.setter
    def scale(self, newval):
        self.sendcmd(f"*SCS{newval.value}")

    @property
    def single_shot_energy_mode(self):
        """Get / Set single shot energy mode.

        :return: Is single shot energy mode turned on?
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.single_shot_energy_mode
            False
            >>> inst.single_shot_energy_mode = True
        """
        val = self._value_query("*GSE", tp=int) == 1
        self._power_mode = False if val else True
        return val

    @single_shot_energy_mode.setter
    def single_shot_energy_mode(self, newval):
        sendval = 1 if newval else 0  # set send value
        self._power_mode = False if newval else True  # set power mode
        self.sendcmd(f"*SSE{sendval}")

    @property
    def trigger_level(self):
        """Get / Set trigger level when in energy mode.

        The trigger level must be between 0.001 and 0.998.

        :return: Trigger level (absolute) with respect to the currently
            set scale
        :rtype: float

        :raise ValueError: Trigger level out of range.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.trigger_level = 0.153
            >>> inst.trigger_level
            0.153

        """
        level = self._no_ack_query("*GTL")
        # get the percent
        retval = float(level[level.find(":") + 1 : level.find("%")]) / 100
        return retval

    @trigger_level.setter
    def trigger_level(self, newval):
        if newval < 0.001 or newval > 0.99:
            raise ValueError(
                "Trigger level {} is out of range. It must be "
                "between 0.001 and 0.998.".format(newval)
            )

        newval = newval * 100.0
        if newval >= 10:
            newval = str(round(newval, 1)).zfill(4)
        else:
            newval = str(round(newval, 2)).zfill(4)

        self.sendcmd(f"*STL{newval}")

    @property
    def usb_state(self):
        """Get status if USB cable is connected.

        :return: Is a USB cable connected?
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.usb_state
            True
        """
        return self._value_query("*USB", tp=int) == 1

    @property
    def user_multiplier(self):
        """Get / Set user multiplier.

        :return: User multiplier
        :rtype: u.Quantity

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.user_multiplier = 10
            >>> inst.user_multiplier
            10.0
        """
        return self._value_query("*GUM", tp=float)

    @user_multiplier.setter
    def user_multiplier(self, newval):
        sendval = _format_eight(newval)  # sendval: 8 characters long
        self.sendcmd(f"*MUL{sendval}")

    @property
    def user_offset(self):
        """Get / Set user offset.

        The user offset can be set unitful in watts or joules and set
        to the device.

        :return: User offset
        :rtype: u.Quantity

        :raises ValueError: Unit not supported or value for offset is
            out of range.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.user_offset = 10
            >>> inst.user_offset
            array(10.) * W
        """
        if self._power_mode is None:
            _ = self.measure_mode  # determine the power mode
            sleep(0.01)

        if self._power_mode:
            return assume_units(self._value_query("*GUO", tp=float), u.W)
        else:
            return assume_units(self._value_query("*GUO", tp=float), u.J)

    @user_offset.setter
    def user_offset(self, newval):
        # if unitful, try to rescale and grab magnitude
        if isinstance(newval, u.Quantity):
            if newval.is_compatible_with(u.W):
                newval = newval.to(u.W).magnitude
            elif newval.is_compatible_with(u.J):
                newval = newval.to(u.J).magnitude
            else:
                raise ValueError(
                    "Value must be given in watts, " "joules, or unitless."
                )
        sendval = _format_eight(newval)  # sendval: 8 characters long
        self.sendcmd(f"*OFF{sendval}")

    @property
    def version(self):
        """Get device information.

        :return: Version and device type
        :rtype: str

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.version
            'Blu firmware Version 1.95'
        """
        return self._no_ack_query("*VER")

    @property
    def wavelength(self):
        """Get / Set the wavelength.

        The wavelength can be set unitful. Specifying zero as a
        wavelength or providing an out-of-bound value as a parameter
        restores the default settings, typically 1064nm. If no units
        are provided, nm are assumed.

        :return: Wavelength in nm
        :rtype: u.Quantity

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.wavelength = u.Quantity(527, u.nm)
            >>> inst.wavelength
            array(527) * nm
        """
        return u.Quantity(self._value_query("*GWL", tp=int), u.nm)

    @wavelength.setter
    def wavelength(self, newval):
        val = round(assume_units(newval, u.nm).to(u.nm).magnitude)
        if val >= 1000000 or val < 0:  # can only send 5 digits
            val = 0  # out of bound anyway
        val = str(int(val)).zfill(5)
        self.sendcmd(f"*PWC{val}")

    @property
    def zero_offset(self):
        """Get / Set zero offset.

        Gets the status if zero offset is enabled. When set to `True`,
        the device will read the current level immediately for around
        three seconds and then set the baseline to the averaged value.
        If activated and set to `True` again, a new value for the
        baseline will be established.

        :return: Is zero offset enabled?
        :rtype: bool

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.zero_offset
            True
            >>> inst.zero_offset = False
        """
        return self._value_query("*GZO", tp=int) == 1

    @zero_offset.setter
    def zero_offset(self, newval):
        if newval:
            self.sendcmd("*SOU")
        else:
            self.sendcmd("*COU")

    # METHODS #

    def confirm_connection(self):
        """Confirm a connection to the device.

        Turns of bluetooth searching by confirming a connection.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.confirm_connection()
        """
        self.sendcmd("*RDY")

    def disconnect(self):
        """Disconnect the device.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.disconnect()
        """
        self.sendcmd("*BTD")

    def scale_down(self):
        """Set scale to next lower level.

        Sets the power meter to the next lower scale. If already at
        the lowest possible scale, no change will be made.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.scale_down()
        """
        self.sendcmd("*SSD")

    def scale_up(self):
        """Set scale to next higher level.

        Sets the power meter to the next higher scale. If already at
        the highest possible scale, no change will be made.

        Example:
            >>> import instruments as ik
            >>> inst = ik.gentec_eo.Blu.open_serial('/dev/ttyACM0')
            >>> inst.scale_up()
        """
        self.sendcmd("*SSU")

    # PRIVATE METHODS #

    def _no_ack_query(self, cmd, size=-1):
        """Query a value and don't expect an ACK message."""
        self._ack_message = None
        try:
            value = self.query(cmd, size=size)
        finally:
            self._ack_message = "ACK"
        return value

    def _value_query(self, cmd, tp=str):
        """Query one specific value and return it.

        :param cmd: Command to send to self._no_ack_query.
        :type cmd: str
        :param tp: Type of the value to be returned, default: str
        :type tp: type

        :return: Single value of query.
        :rtype: tp (selected type)

        :raises ValueError: Conversion of response into given type was
            unsuccessful.
        """
        resp = self._no_ack_query(cmd).rstrip()  # strip \r\n
        resp = resp.split(":")[1]  # strip header off
        resp = resp.replace(" ", "")  # strip white space
        if isinstance(resp, tp):
            return resp
        else:
            return tp(resp)


def _format_eight(value):
    """Formats a value to eight characters total.

    :param value: value to be formatted, > -1e100 and < 1e100
    :type value: int,float

    :return: Value formatted to 8 characters
    :rtype: str
    """
    if len(str(value)) > 8:
        if value < 0:
            value = f"{value:.2g}".zfill(8)  # make space for -
        else:
            value = f"{value:.3g}".zfill(8)
    else:
        value = str(value).zfill(8)
    return value
