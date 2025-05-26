#!/usr/bin/env python
"""
Driver for the Sunpower CryoTel GT generation 2 cryocooler.
"""

# IMPORTS #####################################################################

from collections import OrderedDict
from enum import Enum
import warnings

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

    class ThermostatStatus(Enum):
        """
        Thermostat status for the CryoTel GT.

        Off means that the thermostat is open and the cryocooler is shutting down or
        shut down.
        """

        OFF = 0
        ON = 1

    class StopMode(Enum):
        """
        Stop mode for the cryocooler. `HOST` means that the start/stop command can
        be controlled from the host computer. `DIGIO` means that the start/stop command
        can be set from the digital input/output pin 1 on the cryocooler.
        """

        HOST = 0
        DIGIO = 1

    def __init__(self, filelike):
        super().__init__(filelike)

        self._error_codes = OrderedDict(
            {
                1: "Over Current",
                2: "Jumper Error",
                4: "Serial Error",
                8: "Non-volatile Memory Error",
                16: "Watchdog Error",
                32: "Temperature Sensor Error",
            }
        )

        self.terminator = "\r"

    @property
    def at_temperature_band(self):
        """
        Get/set the temperature band of the CryoTel GT in Kelvin.

        Returns the temperature band within the green LED and "At Temperature" pin on
        the I/O connector will be activated.

        If no unit is provided, Kelvin are assumed.

        :return: The current temperature band in Kelvin.
        """
        ret_val = self.query("SET TBAND")
        return float(ret_val) * u.K

    @at_temperature_band.setter
    def at_temperature_band(self, value):
        value = assume_units(value, u.K).to(u.K)
        self.query("SET TBAND", float(value.magnitude))

    @property
    def control_mode(self):
        """
        Get/set the control mode of the CryoTel GT.

        Valid options are `ControlMode.POWER` and `ControlMode.TEMPERATURE`.

        .. note:: The set control mode will be reset after a power cycle unless you also
        call the `save_control_mode()` method.

        :return: The current control mode.
        """
        ret_val = int(float(self.query("SET PID")))
        return self.ControlMode(ret_val)

    @control_mode.setter
    def control_mode(self, value):
        if not isinstance(value, self.ControlMode):
            raise ValueError(
                "Invalid control mode. Use ControlMode.POWER or ControlMode.TEMPERATURE."
            )
        self.query("SET PID", value.value)

    @property
    def errors(self):
        """Get any error codes from the CryoTel GT.

        Only error codes that are currently active will be added to the
        list. If no error codes are active, an empty list is returned.

        :return: List of human readable strings.
        """
        ret_val = int(self.query("ERROR"), 2)
        errors = []
        for errcode, errstr in self._error_codes.items():
            if ret_val & errcode:
                errors.append(errstr)
        return errors

    @property
    def ki(self):
        """Set/get the integral constant of the temperature control loop.

        The default integral constant is 1.0 and will be reset to this value if the
        reset method is called.

        :return: The current integral constant.
        :rtype: float
        """
        ret_val = self.query("SET KI")
        return float(ret_val)

    @ki.setter
    def ki(self, value):
        _ = self.query("SET KI", float(value))

    @property
    def kp(self):
        """Set/get the proportional constant of the temperature control loop.

        The default proportional constant is 50.0 and will be reset to this value if the
        reset method is called.

        :return: The current proportional constant.
        :rtype: float
        """
        ret_val = self.query("SET KP")
        return float(ret_val)

    @kp.setter
    def kp(self, value):
        _ = self.query("SET KP", float(value))

    @property
    def power(self):
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
    def power_max(self):
        """
        Get/set the maximum user defined power in Watts.

        The cooler will automatically limit the power to a safe value if this number
        exceeds the maximum allowable power.

        :return: The maximum user defined power in Watts.
        """
        ret_val = self.query("SET MAX")
        return float(ret_val) * u.W

    @power_max.setter
    def power_max(self, value):
        value = assume_units(value, u.W).to(u.W)
        if value.magnitude < 0 or value.magnitude > 999.99:
            raise ValueError("Maximum power must be between 0 and 999.99 Watts.")
        self.query("SET MAX", float(value.magnitude))

    @property
    def power_min(self):
        """
        Get/set the minimum user defined power in Watts.

        The cooler will automatically limit the power to a safe value if this number
        exceeds the minimum allowable power.

        :return: The minimum user defined power in Watts.
        """
        ret_val = self.query("SET MIN")
        return float(ret_val) * u.W

    @power_min.setter
    def power_min(self, value):
        value = assume_units(value, u.W).to(u.W)
        if value.magnitude < 0 or value.magnitude > 999.99:
            raise ValueError("Minimum power must be between 0 and 999.99 Watts.")
        self.query("SET MIN", float(value.magnitude))

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
        self.query("SET PWOUT", float(value.magnitude))

    @property
    def serial_number(self):
        """
        Get the serial number and revision of the CryoTel GT.

        :return: List of serial number string and revision string.
        """
        return self.query_multiline("SERIAL", 2)

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
    def temperature(self):
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
        self.query("SET TTARGET", float(value.magnitude))

    @property
    def thermostat(self):
        """Get/set the thermostat mode of the CryoTel GT.

        Set this to `True` to enable the thermostat mode, or `False` to disable it.

        :return: The current thermostat mode state.
        :rtype: bool
        """
        ret_val = int(float(self.query("SET TSTATM")))
        return bool(ret_val)

    @thermostat.setter
    def thermostat(self, value):
        if not isinstance(value, bool):
            raise ValueError("Invalid thermostat mode. Use True or False.")
        self.query("SET TSTATM", int(value))

    @property
    def thermostat_status(self):
        """
        Get the current thermostat status of the CryoTel GT.

        Returns `ThermostatStatus.ON` if the thermostat is enabled, and `ThermostatStatus.OFF`
        if it is disabled.

        :return: The current thermostat status.
        :rtype: ThermostatStatus
        """
        ret_val = int(float(self.query("TSTAT")))
        return self.ThermostatStatus(ret_val)

    @property
    def stop(self):
        """
        Get/set the stop state of the CryoTel GT.

        Valid options are `True` (stop) and `False` (start).

        :return: The current stop state.
        """
        ret_val = int(float(self.query("SET SSTOP")))
        return bool(ret_val)

    @stop.setter
    def stop(self, value):
        if not isinstance(value, bool):
            raise ValueError("Invalid stop state. Use True or False.")
        self.query("SET SSTOP", int(value))

    @property
    def stop_mode(self):
        """
        Get/set the stop mode of the CryoTel GT.

        Valid options are `StopMode.HOST` and `StopMode.DIGIO`.

        :return: The current stop mode.
        """
        ret_val = int(float(self.query("SET SSTOPM")))
        return self.StopMode(ret_val)

    @stop_mode.setter
    def stop_mode(self, value):
        if not isinstance(value, self.StopMode):
            raise ValueError("Invalid stop mode. Use StopMode.HOST or StopMode.DIGIO.")
        self.query("SET SSTOPM", value.value)

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
            return self.read().strip()
        else:
            if isinstance(value, float):
                value_to_send = f"{value:.2f}"
            else:
                value_to_send = str(value)
            self.sendcmd(f"{command}={value_to_send}")
            ret_val = self.read().strip()
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
        ret_val = [self.read().strip() for _ in range(num_lines)]
        return ret_val

    def sendcmd(self, command):
        """
        Send a command to the cooler.

        :param command: The command to send to the cooler.
        """
        self._file.sendcmd(command)
        _ = self.read()  # echo
