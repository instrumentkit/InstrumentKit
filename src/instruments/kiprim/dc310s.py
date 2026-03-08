#!/usr/bin/env python
"""
Driver for the Kiprim DC310S single-output power supply.
"""

# IMPORTS #####################################################################

from instruments.abstract_instruments import PowerSupply
from instruments.units import ureg as u
from instruments.util_fns import bounded_unitful_property, unitful_property

# FUNCTIONS ###################################################################


def _parse_output_state(reply):
    """
    Normalize the DC310S output-state reply into a boolean value.

    The DC310S has been observed to report either ``ON``/``OFF`` or ``1``/``0``
    depending on firmware and transport state.
    """

    reply = reply.strip().upper()
    if reply in {"1", "ON"}:
        return True
    if reply in {"0", "OFF"}:
        return False
    raise ValueError(f"Unexpected output-state reply: {reply}")


# CLASSES #####################################################################


class DC310S(PowerSupply, PowerSupply.Channel):
    """
    The Kiprim DC310S is a single-output programmable DC power supply.

    Because the supply has one programmable output, this object inherits from
    both `~instruments.abstract_instruments.power_supply.PowerSupply` and
    `~instruments.abstract_instruments.power_supply.PowerSupply.Channel`.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.kiprim.DC310S.open_serial("COM8", baud=115200, timeout=0.5)
    >>> psu.voltage = 5 * ik.units.volt
    >>> psu.current = 0.25 * ik.units.ampere
    >>> psu.output = True
    >>> psu.voltage_sense
    <Quantity(5.0, 'volt')>
    """

    voltage, voltage_min, voltage_max = bounded_unitful_property(
        "VOLT",
        u.volt,
        format_code="{:.3f}",
        input_decoration=str.strip,
        valid_range=(0 * u.volt, 30 * u.volt),
        doc="""
        Gets/sets the programmed output voltage.

        The DC310S product documentation specifies a programmable output range
        of 0 V to 30 V.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
    )

    current, current_min, current_max = bounded_unitful_property(
        "CURR",
        u.amp,
        format_code="{:.3f}",
        input_decoration=str.strip,
        valid_range=(0 * u.amp, 10 * u.amp),
        doc="""
        Gets/sets the programmed output current limit.

        The DC310S product documentation specifies a programmable output range
        of 0 A to 10 A.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
    )

    voltage_sense = unitful_property(
        "MEAS:VOLT",
        u.volt,
        readonly=True,
        input_decoration=str.strip,
        doc="""
        Gets the measured output voltage.

        :units: :math:`\\text{V}`
        :rtype: `~pint.Quantity`
        """,
    )

    current_sense = unitful_property(
        "MEAS:CURR",
        u.amp,
        readonly=True,
        input_decoration=str.strip,
        doc="""
        Gets the measured output current.

        :units: :math:`\\text{A}`
        :rtype: `~pint.Quantity`
        """,
    )

    power_sense = unitful_property(
        "MEAS:POW",
        u.watt,
        readonly=True,
        input_decoration=str.strip,
        doc="""
        Gets the measured output power.

        :units: :math:`\\text{W}`
        :rtype: `~pint.Quantity`
        """,
    )

    @property
    def output(self):
        """
        Gets/sets the output state.

        :type: `bool`
        """

        return _parse_output_state(self.query("OUTP?"))

    @output.setter
    def output(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Output state must be specified with a boolean value.")
        self.sendcmd(f"OUTP {'ON' if newval else 'OFF'}")

    @property
    def name(self):
        """
        Gets the instrument name as reported by ``*IDN?``.

        :rtype: `str`
        """

        idn_string = self.query("*IDN?")
        idn_parts = [part.strip() for part in idn_string.split(",")]
        if len(idn_parts) >= 2:
            return " ".join(idn_parts[:2])
        return idn_string.strip()

    @property
    def mode(self):
        """
        Unimplemented.
        """

        raise NotImplementedError("The DC310S does not expose a stable mode query.")

    @mode.setter
    def mode(self, newval):
        """
        Unimplemented.
        """

        raise NotImplementedError("The DC310S does not expose a stable mode query.")

    @property
    def channel(self):
        """
        Return the single output channel.

        :rtype: `tuple`
        """

        return (self,)
