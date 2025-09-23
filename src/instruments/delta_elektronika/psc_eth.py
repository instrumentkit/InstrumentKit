"""Support for Delta Elektronika DC power supplies with PSC-ETH-2 interface."""

# IMPORTS #####################################################################

from enum import IntEnum
from typing import Tuple, Union

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units, unitful_property

# CLASSES #####################################################################


class PscEth(Instrument):
    """Communicate with a Delta Elektronica one channel power supply via the
    PSC-ETH-2 ethernet interface.

    For communication, make sure the device is set to "ethernet" mode.

    Example:
        >>> import instruments as ik
        >>> from instruments import units as u
        >>> i = ik.delta_elektronika.PscEth.open_tcpip("192.168.127.100", port=8462)
        >>> print(i.name)
    """

    def __init__(self, filelike):
        super().__init__(filelike)

    class LimitStatus(IntEnum):
        """Enum class for the limit status."""

        OFF = 0
        ON = 1

    # CLASS PROPERTIES #

    @property
    def name(self) -> str:
        return self.query("*IDN?")

    @property
    def current_limit(self) -> tuple["PscEth.LimitStatus", u.Quantity]:
        """Get the current limit status.

        :return: A tuple of the current limit status and the current limit value.
        :rtype: `tuple` of (`PscEth.LimitStatus`, `~pint.Quantity`)
        """
        resp = self.query("SYST:LIM:CUR?")
        val, status = resp.split(",")
        ls = self.LimitStatus.OFF if "off" in status.lower() else self.LimitStatus.ON
        return ls, assume_units(float(val), u.A)

    @property
    def voltage_limit(self) -> tuple["PscEth.LimitStatus", u.Quantity]:
        """Get the voltage limit status.

        :return: A tuple of the voltage limit status and the voltage limit value.
        :rtype: `tuple` of (`PscEth.LimitStatus`, `~pint.Quantity`)
        """
        resp = self.query("SYST:LIM:VOL?")
        val, status = resp.split(",")
        ls = self.LimitStatus.OFF if "off" in status.lower() else self.LimitStatus.ON
        return ls, assume_units(float(val), u.V)

    current = unitful_property(
        "SOUR:CURR",
        u.A,
        format_code="{:.15f}",
        doc="""
        Set/get the output current.

        Note: There is no bound checking of the value specified.

        :newval: The output current to set.
        :uval: `float` (assumes milliamps) or `~pint.Quantity`
        """,
    )

    current_max = unitful_property(
        "SOUR:CURR:MAX",
        u.A,
        format_code="{:.15f}",
        doc="""
        Set/get the maximum output current.

        Note: This value should generally not be used. It sets the maximum
        capable current of the power supply, which is fixed by the hardware.
        If you set this to other values, you will get strange measurement results.

        :newval: The maximum output current to set.
        :uval: `float` (assumes milliamps) or `~pint.Quantity`
        """,
    )

    current_measure = unitful_property(
        "MEAS:CURR?",
        u.A,
        format_code="{:.15f}",
        readonly=True,
        doc="""
        Get the measured output current.

        :rtype: `~pint.Quantity`
        """,
    )

    current_stepsize = unitful_property(
        "SOUR:CUR:STE",
        u.A,
        format_code="{:.15f}",
        readonly=True,
        doc="""
        Get the output current step size.

        :rtype: `~pint.Quantity`
        """,
    )

    voltage = unitful_property(
        "SOUR:VOL",
        u.V,
        format_code="{:.15f}",
        doc="""
        Set/get the output voltage.

        Note: There is no bound checking of the value specified.

        :newval: The output voltage to set.
        :uval: `float` (assumes volts) or `~pint.Quantity`
        """,
    )

    voltage_max = unitful_property(
        "SOUR:VOLT:MAX",
        u.V,
        format_code="{:.15f}",
        doc="""
        Set/get the maximum output voltage.

        Note: This value should generally not be used. It sets the maximum
        capable voltage of the power supply, which is fixed by the hardware.
        If you set this to other values, you will get strange measurement results.

        :newval: The maximum output voltage to set.
        :uval: `float` (assumes volts) or `~pint.Quantity`
        """,
    )

    voltage_measure = unitful_property(
        "MEAS:VOLT?",
        u.V,
        format_code="{:.15f}",
        readonly=True,
        doc="""
        Get the measured output voltage.

        :rtype: `~pint.Quantity`
        """,
    )

    voltage_stepsize = unitful_property(
        "SOUR:VOL:STE",
        u.V,
        format_code="{:.15f}",
        readonly=True,
        doc="""
        Get the output voltage step size.

        :rtype: `~pint.Quantity`
        """,
    )

    def recall(self) -> None:
        """Recall the settings from non-volatile memory."""
        self.sendcmd("*RCL")

    def reset(self) -> None:
        """Reset the instrument to default settings."""
        self.sendcmd("*RST")

    def save(self) -> None:
        """Save the current settings to non-volatile memory."""
        self.sendcmd("*SAV")

    def set_current_limit(
        self, stat: "PscEth.LimitStatus", val: Union[float, u.Quantity] = 0
    ) -> None:
        """Set the current limit.

        :param stat: The limit status to set.
        :type stat: `PscEth.LimitStatus`
        :param val: The current limit value to set. Only requiered when turning it on.
        :type val: `float` (assumes milliamps) or `~pint.Quantity`
        """
        if not isinstance(stat, PscEth.LimitStatus):
            raise TypeError("stat must be of type PscEth.LimitStatus")
        val = assume_units(val, u.A).to(u.A).magnitude
        cmd = f"SYST:LIM:CUR {val:.15f},{stat.name}"
        print(cmd)
        self.sendcmd(cmd)

    def set_voltage_limit(
        self, stat: "PscEth.LimitStatus", val: Union[float, u.Quantity] = 0
    ) -> None:
        """Set the voltage limit.

        :param stat: The limit status to set.
        :type stat: `PscEth.LimitStatus`
        :param val: The voltage limit value to set. Only requiered when turning it on.
        :type val: `float` (assumes volts) or `~pint.Quantity`
        """
        if not isinstance(stat, PscEth.LimitStatus):
            raise TypeError("stat must be of type PscEth.LimitStatus")
        val = assume_units(val, u.V).to(u.V).magnitude
        cmd = f"SYST:LIM:VOL {val:.15f},{stat.name}"
        print(cmd)
        self.sendcmd(cmd)
