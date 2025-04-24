#!/usr/bin/env python
"""
Driver for the Sunpower CryoTel GT generation 2 cryocooler.
"""

# IMPORTS #####################################################################

import warnings

from enum import Enum

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class CryoTelGT(Instrument):
    """
    The Sunpower CyroTel GT is a cryocooler.

    This driver is for the GT generation 2. According to the Sunpower website,
    this means for cryocoolers purchased after May 2012.

    Caution: Do not use this driver to established a closed loop control of the
    cryocooler, as this may cause malfunction and potentially damage to the
    device (see the manual for details). You can use this driver however to adjust
    the setpoint temperature and read the current temperature.

    For communications, the default baudrate is 4800, 8 data bits, 1 stop bit,
    and no flow control.

    Example usage:
        >>> import instruments as ik
        >>> inst = ik.sunpower.CryoTelGT.open_serial("/dev/ttyACM0", 4800)
        >>> inst.temperature_current
        82.0 Kelvin
        >>> inst.temperature_set
        77.0 Kelvin
    """

    class ControlMode(Enum):
        """
        Control modes for the Cryocooler.
        """

        POWER = 0
        TEMPERATURE = 2

    def __init__(self, filelike):
        super().__init__(filelike)

        self._error_codes = {
            1: "Over Current",
            2: "Jumper Error",
            4: "Serial Error",
            8: "Non-volatile Memory Error",
            16: "Watchdog Error",
            32: "Temperature Sensor Error",
        }

        self.terminator = "\r"  # FIXME: Unclear if this is correct

    @property
    def control_mode(self):
        """
        Get/set the control mode of the CryoTel GT.

        Valid options are `ControlMode.POWER` and `ControlMode.TEMPERATURE`.

        .. note:: The set control mode will be reset after a power cycle unless you also
        call the `save_control_mode()` method.

        :return: The current control mode.
        """
        ret_val = int(self.query("SET PID"))
        return self.ControlMode(ret_val)

    @control_mode.setter
    def control_mode(self, value):
        if not isinstance(value, self.ControlMode):
            raise ValueError(
                "Invalid control mode. Use ControlMode.POWER or ControlMode.TEMPERATURE."
            )
        self.query("SET PID", value.value)

    @property
    def power_current(self):
        """
        Get the current power in Watts.

        :return: The current power in Watts.
        """
        ret_val = self.query("P")
        return float(ret_val) * u.W

    @property
    def power_current_and_limits(self):
        """
        Get the current power and power limits in Watts.

        :return: Three u.Quantity objects representing the maximum allowable power at the
            current temperature, the minimum allowable power at the current temperature,
            and the current power.
        """
        ret_vals = self.query_multiline("E", 3)
        max_power = float(ret_vals[0]) * u.W
        min_power = float(ret_vals[1]) * u.W
        current_power = float(ret_vals[2]) * u.W
        return max_power, min_power, current_power

    @property
    def power_set(self):
        """
        Get/set the setpoint power in Watts.

        This setpoint is used when the control mode is set to `ControlMode.POWER`.
        Setting the power is unitful. If no unit is given, it is assumed
        to be in Watts.

        While any number from 0 to 999.99 can be set, the controller will only command
        a power that will not damage the cryocooler.

        :return: The setpoint power in Watts.

        :raises ValueError: If the power is set to a value outside the allowed range.
        """
        ret_val = self.query("SET PWOUT")
        return float(ret_val) * u.W

    @power_set.setter
    def power_set(self, value):
        value = assume_units(value, u.W).to(u.W)
        if value.magnitude < 0 or value.magnitude > 999.99:
            raise ValueError("Power setpoint must be between 0 and 999.99 Watts.")
        self.query("SET PWOUT", value.magnitude)

    @property
    def serial_number(self):
        """
        Get the serial number of the CryoTel GT.

        :return: The serial number as a string.
        """
        return self.query("SERIAL")

    @property
    def state(self):
        """
        Get a list of most of the control parameters and their values.

        Note: This is the direct list from the CryoTel GT controller. See the manual for
        the meaning of the parameters.

        :return: A list of strings representing the control parameters and their values.
        """
        return self.query_multiline("STATE", 14)

    @property
    def temperature_current(self):
        """
        Get the current temperature in Kelvin.

        :return: The current temperature in Kelvin.
        """
        ret_val = self.query("TC")
        return float(ret_val) * u.K

    @property
    def temperature_set(self):
        """
        Get/set the setpoint temperature in Kelvin.

        This setpoint is used when the control mode is set to `ControlMode.TEMPERATURE`.
        Setting the temperature is unitful. If no unit is given, it is assumed
        to be in Kelvin.

        :return: The setpoint temperature in Kelvin.
        """
        ret_val = self.query("SET TTARGET")
        return float(ret_val) * u.K

    @temperature_set.setter
    def temperature_set(self, value):
        value = assume_units(value, u.K).to(u.K)
        self.query("SET TTARGET", value.magnitude)

    # CryoCooler Methods

    def reset(self):
        """
        Reset the CryoTel GT to factory defaults.
        """
        _ = self.query_multiline("RESET=F", 2)

    def save_control_mode(self):
        """
        Save the current control mode as the default control mode.
        """
        _ = self.query("SAVE PID")

    # Driver methods

    def query(self, command, value=None):
        """
        Send a query to the cooler and return the response if no value is given.

        When setting a variable, the CryoTel GT will generally return the value
        that was set. This is checked for accuracy and a warning is raised if the
        return value is not the same as the set value.

        For an actual query where we expect a result, the result is returned unchanged.

        :param command: The command to send to the cooler.
        :param value: The value to be set. If not given or None, it is assumed that
            you want to query the cryocooler.

        :return: The response from the cooler or None.
        """
        if value is None:
            self.sendcmd(command)
            return self.read()
        else:
            if isinstance(value, float):
                value_to_send = f"{value:.2f}"
            else:
                value_to_send = str(value)
            self.sendcmd(f"{command}={value_to_send}")
            ret_val = self.read()
            if float(ret_val) != value:
                warnings.warn(
                    f"Set value {value} does not match returned value {ret_val}."
                )

    def query_multiline(self, command, num_lines):
        """
        Send a query to the cooler and return the response.

        This is used for commands that return multiple lines of data.

        :param command: The command to send to the cooler.
        :param num_lines: The number of lines to read from the cooler.

        :return: The response from the cooler as a list of lines.
        """
        self.sendcmd(command)
        ret_val = [self.read() for _ in range(num_lines)]
        return ret_val
