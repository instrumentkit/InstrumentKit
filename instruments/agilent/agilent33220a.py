#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Agilent 33220a function generator.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

from enum import Enum

import quantities as pq

from instruments.generic_scpi import SCPIFunctionGenerator
from instruments.util_fns import (
    enum_property, int_property, bool_property, assume_units
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
    >>> import quantities as pq
    >>> inst = ik.agilent.Agilent33220a.open_gpibusb('/dev/ttyUSB0', 1)
    >>> inst.function = inst.Function.sinusoid
    >>> inst.frequency = 1 * pq.kHz
    >>> inst.output = True

    .. _Agilent/Keysight 33220a: http://www.keysight.com/en/pd-127539-pn-33220A

    """

    def __init__(self, filelike):
        super(Agilent33220a, self).__init__(filelike)

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

    @property
    def frequency(self):
        return super(Agilent33220a, self).frequency

    @frequency.setter
    def frequency(self, newval):
        super(Agilent33220a, self).frequency = newval

    function = enum_property(
        name="FUNC",
        enum=Function,
        doc="""
        Gets/sets the output function of the function generator

        :type: `Agilent33220a.Function`
        """,
        set_fmt="{}:{}"
    )

    duty_cycle = int_property(
        name="FUNC:SQU:DCYC",
        doc="""
        Gets/sets the duty cycle of a square wave.

        Duty cycle represents the amount of time that the square wave is at a
        high level.

        :type: `int`
        """,
        valid_set=range(101)
    )

    ramp_symmetry = int_property(
        name="FUNC:RAMP:SYMM",
        doc="""
        Gets/sets the ramp symmetry for ramp waves.

        Symmetry represents the amount of time per cycle that the ramp wave is
        rising (unless polarity is inverted).

        :type: `int`
        """,
        valid_set=range(101)
    )

    output = bool_property(
        name="OUTP",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the output enable status of the front panel output connector.

        The value `True` corresponds to the output being on, while `False` is
        the output being off.

        :type: `bool`
        """
    )

    output_sync = bool_property(
        name="OUTP:SYNC",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the enabled status of the front panel sync connector.

        :type: `bool`
        """
    )

    output_polarity = enum_property(
        name="OUTP:POL",
        enum=OutputPolarity,
        doc="""
        Gets/sets the polarity of the waveform relative to the offset voltage.

        :type: `~Agilent33220a.OutputPolarity`
        """
    )

    @property
    def load_resistance(self):
        """
        Gets/sets the desired output termination load (ie, the impedance of the
        load attached to the front panel output connector).

        The instrument has a fixed series output impedance of 50ohms. This
        function allows the instrument to compensate of the voltage divider
        and accurately report the voltage across the attached load.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units :math:`\\Omega` (ohm).
        :type: `~quantities.quantity.Quantity` or `Agilent33220a.LoadResistance`
        """
        value = self.query("OUTP:LOAD?")
        try:
            return int(value) * pq.ohm
        except ValueError:
            return self.LoadResistance(value.strip())

    @load_resistance.setter
    def load_resistance(self, newval):
        if isinstance(newval, self.LoadResistance):
            newval = newval.value
        elif isinstance(newval, int):
            if (newval < 0) or (newval > 10000):
                raise ValueError(
                    "Load resistance must be between 0 and 10,000")
            newval = assume_units(newval, pq.ohm).rescale(pq.ohm).magnitude
        else:
            raise TypeError("Not a valid load resistance type.")
        self.sendcmd("OUTP:LOAD {}".format(newval))

    @property
    def phase(self):
        raise NotImplementedError

    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
