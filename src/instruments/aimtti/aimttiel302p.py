#!/usr/bin/env python
"""
Provides support for the Aim-TTI EL302P power supply
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.abstract_instruments import PowerSupply
from instruments.units import ureg as u
from instruments.util_fns import (
    bounded_unitful_property,
    enum_property,
    unitful_property,
)

# CLASSES #####################################################################


class AimTTiEL302P(PowerSupply, PowerSupply.Channel):
    """
    The Aim-TTI EL302P is a single output power supply.

    Because it is a single channel output, this object inherits from both
    PowerSupply and PowerSupply.Channel.

    Before this power supply can be remotely operated, remote communication
    must be enabled and the unit must be on. Please refer to the manual.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.aimtti.AimTTiEL302P.open_serial('/dev/ttyUSB0', 9600)
    >>> psu.voltage = 10 # Sets output voltage to 10V.
    >>> psu.voltage
    array(10.0) * V
    >>> psu.output = True # Turns on the power supply
    """

    # ENUMS ##

    class Mode(Enum):
        """
        Enum containing the possible modes of operations of the instrument.
        """

        #: Constant voltage mode
        voltage = "M CV"
        #: Constant current mode
        current = "M CC"

    class Error(Enum):
        """
        Enum containing the possible error codes returned by the instrument.
        """

        #: No errors
        error_none = "ERR 0"
        #: Command not recognized
        error_not_recognized = "ERR 1"
        #: Command value outside instrument limits
        error_outside_limits = "ERR 2"

    # PROPERTIES ##

    voltage, voltage_min, voltage_max = bounded_unitful_property(
        "V",
        u.volt,
        valid_range=(0.0 * u.volt, 30.0 * u.volt),
        doc="""
        Gets/sets the output voltage of the source. Value must be between
        0V and 30V.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
        input_decoration=lambda x: float(x[2:]),
        format_code="{}",
    )

    voltage_sense = unitful_property(
        command="VO",
        units=u.volt,
        doc="""
        Gets the actual output voltage measured by the power supply.

        :units: :math:`\\text{V}`
        :rtype: `~pint.Quantity`
        """,
        input_decoration=lambda x: float(x[2:]),
        readonly=True,
    )

    current, current_min, current_max = bounded_unitful_property(
        "I",
        u.amp,
        valid_range=(0.01 * u.amp, 2.0 * u.amp),
        doc="""
        Gets/sets the output current of the source. Value must be between
        0.01A and 2A.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
        input_decoration=lambda x: float(x[2:]),
        format_code="{}",
    )

    current_sense = unitful_property(
        command="IO",
        units=u.amp,
        doc="""
        Gets the actual output current measured by the power supply.

        :units: :math:`\\text{A}`
        :rtype: `~pint.Quantity`
        """,
        input_decoration=lambda x: float(x[2:]),
        readonly=True,
    )

    @property
    def output(self):
        return self.query("OUT?") == "OUT ON"

    @output.setter
    def output(self, newval):
        value = "ON" if newval is True else "OFF"
        self.sendcmd(f"{value}")

    mode = enum_property(
        "M",
        Mode,
        doc="""
        Gets output mode status.
        """,
        readonly=True,
    )

    error = enum_property(
        "ERR",
        Error,
        doc="""
        Gets the value in the error register.
        """,
        readonly=True,
    )

    @property
    def name(self):
        """
        Gets the name of the connected instrument.

        :rtype: `str`
        """
        idn_string = self.query("*IDN?")
        idn_list = idn_string.split(",")
        return " ".join(idn_list[:2])

    def reset(self):
        """
        Resets the instrument to the default power-up settings
        (1.00V, 1.00A, output off).
        """
        self.sendcmd("*RST")

    @property
    def channel(self):
        """
        Return the channel (which in this case is the entire instrument, since
        there is only 1 channel on the EL302P.)

        :rtype: 'tuple' of length 1 containing a reference back to the parent
            EL302P object.
        """
        return (self,)
