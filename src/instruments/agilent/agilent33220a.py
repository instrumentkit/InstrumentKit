#!/usr/bin/env python
"""
Provides support for the Agilent 33220a function generator.
"""

# IMPORTS #####################################################################

from enum import Enum


from instruments.generic_scpi import SCPIFunctionGenerator
from instruments.units import ureg as u
from instruments.util_fns import (
    enum_property,
    int_property,
    bool_property,
    assume_units,
)


# CLASSES #####################################################################


class Agilent33220a(SCPIFunctionGenerator):

    """
    The `Agilent/Keysight 33220a`_ is a 20MHz function/arbitrary waveform
    generator. This model has been replaced by the Keysight 33500 series
    waveform generators. This class may or may not work with these newer
    models.

    Example usage:

    >>> import instruments as ik
    >>> import instruments.units as u
    >>> inst = ik.agilent.Agilent33220a.open_gpibusb('/dev/ttyUSB0', 1)
    >>> inst.function = inst.Function.sinusoid
    >>> inst.frequency = 1 * u.kHz
    >>> inst.output = True

    .. _Agilent/Keysight 33220a: http://www.keysight.com/en/pd-127539-pn-33220A

    """

    # ENUMS #

    class Function(Enum):

        """
        Enum containing valid functions for the Agilent/Keysight 33220a
        """

        sinusoid = "SIN"
        square = "SQU"
        ramp = "RAMP"
        pulse = "PULS"
        noise = "NOIS"
        dc = "DC"
        user = "USER"

    class LoadResistance(Enum):

        """
        Enum containing valid load resistance for the Agilent/Keysight 33220a
        """

        minimum = "MIN"
        maximum = "MAX"
        high_impedance = "INF"

    class OutputPolarity(Enum):

        """
        Enum containg valid output polarity modes for the
        Agilent/Keysight 33220a
        """

        normal = "NORM"
        inverted = "INV"

    # PROPERTIES #

    function = enum_property(
        command="FUNC",
        enum=Function,
        doc="""
        Gets/sets the output function of the function generator

        :type: `Agilent33220a.Function`
        """,
        set_fmt="{}:{}",
    )

    duty_cycle = int_property(
        command="FUNC:SQU:DCYC",
        doc="""
        Gets/sets the duty cycle of a square wave.

        Duty cycle represents the amount of time that the square wave is at a
        high level.

        :type: `int`
        """,
        valid_set=range(101),
    )

    ramp_symmetry = int_property(
        command="FUNC:RAMP:SYMM",
        doc="""
        Gets/sets the ramp symmetry for ramp waves.

        Symmetry represents the amount of time per cycle that the ramp wave is
        rising (unless polarity is inverted).

        :type: `int`
        """,
        valid_set=range(101),
    )

    output = bool_property(
        command="OUTP",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the output enable status of the front panel output connector.

        The value `True` corresponds to the output being on, while `False` is
        the output being off.

        :type: `bool`
        """,
    )

    output_sync = bool_property(
        command="OUTP:SYNC",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the enabled status of the front panel sync connector.

        :type: `bool`
        """,
    )

    output_polarity = enum_property(
        command="OUTP:POL",
        enum=OutputPolarity,
        doc="""
        Gets/sets the polarity of the waveform relative to the offset voltage.

        :type: `~Agilent33220a.OutputPolarity`
        """,
    )

    @property
    def load_resistance(self):
        """
        Gets/sets the desired output termination load (ie, the impedance of the
        load attached to the front panel output connector).

        The instrument has a fixed series output impedance of 50ohms. This
        function allows the instrument to compensate of the voltage divider
        and accurately report the voltage across the attached load.

        :units: As specified (if a `~pint.Quantity`) or assumed
            to be of units :math:`\\Omega` (ohm).
        :type: `~pint.Quantity` or `Agilent33220a.LoadResistance`
        """
        value = self.query("OUTP:LOAD?")
        try:
            return int(value) * u.ohm
        except ValueError:
            return self.LoadResistance(value.strip())

    @load_resistance.setter
    def load_resistance(self, newval):
        if isinstance(newval, self.LoadResistance):
            newval = newval.value
        else:
            newval = assume_units(newval, u.ohm).to(u.ohm).magnitude
            if (newval < 0) or (newval > 10000):
                raise ValueError("Load resistance must be between 0 and 10,000")
        self.sendcmd(f"OUTP:LOAD {newval}")

    @property
    def phase(self):
        raise NotImplementedError

    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
