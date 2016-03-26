#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# hp3456a.py: Driver for the HP3456a Digital Voltmeter.
#
# © 2014 Willem Dijkstra (wpd@xs4all.nl).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Driver for the HP3456a Digital Voltmeter

Originally contributed and copyright held by Willem Dijkstra (wpd@xs4all.nl)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
import time
from builtins import range

from enum import Enum, IntEnum

import quantities as pq

from instruments.abstract_instruments import Multimeter
from instruments.util_fns import assume_units, bool_property, enum_property

# CLASSES #####################################################################


class HP3456a(Multimeter):

    """The `HP3456a` is a 6 1/2 digit bench multimeter.

    It supports DCV, ACV, ACV + DCV, 2 wire Ohms, 4 wire Ohms, DCV/DCV Ratio,
    ACV/DCV Ratio, Offset compensated 2 wire Ohms and Offset compensated 4 wire
    Ohms measurements.

    Measurements can be further extended using a system math mode that allows
    for pass/fail, statistics, dB/dBm, null, scale and percentage readings.

    `HP3456a` is a HPIB / pre-448.2 instrument.
    """

    def __init__(self, filelike):
        """
        Initialise the instrument, and set the required eos, eoi needed for
        communication.
        """
        super(HP3456a, self).__init__(filelike)
        self.timeout = 15 * pq.second
        self.terminator = "\r"
        self.sendcmd("HO0T4SO1")
        self._null = False

    # ENUMS ##

    class MathMode(IntEnum):

        """
        Enum with the supported math modes
        """
        off = 0
        pass_fail = 1
        statistic = 2
        null = 3
        dbm = 4
        thermistor_f = 5
        thermistor_c = 6
        scale = 7
        percent = 8
        db = 9

    class Mode(Enum):

        """
        Enum containing the supported mode codes
        """
        #: DC voltage
        dcv = "S0F1"
        #: AC voltage
        acv = "S0F2"
        #: RMS of DC + AC voltage
        acvdcv = "S0F3"
        #: 2 wire resistance
        resistance_2wire = "S0F4"
        #: 4 wire resistance
        resistance_4wire = "S0F5"
        #: ratio DC / DC voltage
        ratio_dcv_dcv = "S1F1"
        #: ratio AC / DC voltage
        ratio_acv_dcv = "S1F2"
        #: ratio (AC + DC) / DC voltage
        ratio_acvdcv_dcv = "S1F3"
        #: offset compensated 2 wire resistance
        oc_resistence_2wire = "S1F4"
        #: offset compensated 4 wire resistance
        oc_resistence_4wire = "S1F5"

    class Register(Enum):

        """
        Enum with the register names for all `HP3456a` internal registers.
        """
        number_of_readings = "N"
        number_of_digits = "G"
        nplc = "I"
        delay = "D"
        mean = "M"
        variance = "V"
        count = "C"
        lower = "L"
        r = "R"
        upper = "U"
        y = "Y"
        z = "Z"

    class TriggerMode(IntEnum):

        """
        Enum with valid trigger modes.
        """
        internal = 1
        external = 2
        single = 3
        hold = 4

    class ValidRange(Enum):

        """
        Enum with the valid ranges for voltage, resistance, and number of
        powerline cycles to integrate over.

        """
        voltage = (1e-1, 1e0, 1e1, 1e2, 1e3)
        resistance = (1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9)
        nplc = (1e-1, 1e0, 1e1, 1e2)

    # PROPERTIES ##

    mode = enum_property(
        "",
        Mode,
        doc="""Set the measurement mode.

        :type: `HP3456a.Mode`
        """,
        writeonly=True,
        set_fmt="{}{}")

    autozero = bool_property(
        "Z",
        inst_true="1",
        inst_false="0",
        doc="""Set the autozero mode.

        This is used to compensate for offsets in the dc
        input amplifier circuit of the multimeter. If set, the amplifier"s input
        circuit is shorted to ground prior to actual measurement in order to
        take an offset reading. This offset is then used to compensate for
        drift in the next measurement. When disabled, one offset reading
        is taken immediately and stored into memory to be used for all
        successive measurements onwards. Disabling autozero increases the
        `HP3456a`"s measurement speed, and also makes the instrument more
        suitable for high impendance measurements since no input switching is
        done.""",
        writeonly=True,
        set_fmt="{}{}")

    filter = bool_property(
        "FL",
        inst_true="1",
        inst_false="0",
        doc="""Set the analog filter mode.

        The `HP3456a` has a 3 pole active filter with
        greater than 60dB attenuation at frequencies of 50Hz and higher. The
        filter is applied between the input terminals and input amplifier. When
        in ACV or ACV+DCV functions the filter is applied to the output of the
        ac converter and input amplifier. In these modes select the filter for
        measurements below 400Hz.""",
        writeonly=True,
        set_fmt="{}{}")

    math_mode = enum_property(
        "M",
        MathMode,
        doc="""Set the math mode.

        The `HP3456a` has a number of different math modes that
        can change measurement output, or can provide additional
        statistics. Interaction with these modes is done via the
        `HP3456a.Register`.

        :type: `HP3456a.MathMode`
        """,
        writeonly=True,
        set_fmt="{}{}")

    trigger_mode = enum_property(
        "T",
        TriggerMode,
        doc="""Set the trigger mode.

        Note that using `HP3456a.measure()` will override the `trigger_mode` to
        `HP3456a.TriggerMode.single`.

        :type: `HP3456a.TriggerMode`

        """,
        writeonly=True,
        set_fmt="{}{}")

    @property
    def number_of_readings(self):
        """Get/set the number of readings done per trigger/measurement cycle
        using `HP3456a.Register.number_of_readings`.

        :type: `float`
        :rtype: `float`

        """
        return self._register_read(HP3456a.Register.number_of_readings)

    @number_of_readings.setter
    def number_of_readings(self, value):
        self._register_write(HP3456a.Register.number_of_readings, value)

    @property
    def number_of_digits(self):
        """Get/set the number of digits used in measurements using
        `HP3456a.Register.number_of_digits`.

        Set to higher values to increase accuracy at the cost of measurement
        speed.

        :type: `int`
        """
        return int(self._register_read(HP3456a.Register.number_of_digits))

    @number_of_digits.setter
    def number_of_digits(self, newval):
        newval = int(newval)
        if newval not in range(3, 7):
            raise ValueError("Valid number_of_digits are: "
                             "{}".format(list(range(3, 7))))

        self._register_write(HP3456a.Register.number_of_digits, newval)

    @property
    def nplc(self):
        """Get/set the number of powerline cycles to integrate per measurement
        using `HP3456a.Register.nplc`.

        Setting higher values increases accuracy at the cost of a longer
        measurement time. The implicit assumption is that the input reading is
        stable over the number of powerline cycles to integrate.

        :type: `int`
        """
        return int(self._register_read(HP3456a.Register.nplc))

    @nplc.setter
    def nplc(self, newval):
        newval = int(newval)
        valid = HP3456a.ValidRange["nplc"].value
        if newval in valid:
            self._register_write(HP3456a.Register.nplc, newval)
        else:
            raise ValueError("Valid nplc settings are: "
                             "{}".format(valid))

    @property
    def delay(self):
        """Get/set the delay that is waited after a trigger for the input to
        settle using `HP3456a.Register.delay`.

        :type: As specified, assumed to be `~quantaties.Quantity.s` otherwise
        :rtype: `~quantaties.Quantity.s`

        """
        return self._register_read(HP3456a.Register.delay) * pq.s

    @delay.setter
    def delay(self, value):
        delay = assume_units(value, pq.s).rescale(pq.s).magnitude
        self._register_write(HP3456a.Register.delay, delay)

    @property
    def mean(self):
        """
        Get the mean over `HP3456a.Register.count` measurements from
        `HP3456a.Register.mean` when in `HP3456a.MathMode.statistic`.

        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.mean)

    @property
    def variance(self):
        """
        Get the variance over `HP3456a.Register.count` measurements from
        `HP3456a.Register.variance` when in `HP3456a.MathMode.statistic`.

        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.variance)

    @property
    def count(self):
        """
        Get the number of measurements taken from `HP3456a.Register.count` when
        in `HP3456a.MathMode.statistic`.

        :rtype: `int`
        """
        return int(self._register_read(HP3456a.Register.count))

    @property
    def lower(self):
        """
        Get/set the value in `HP3456a.Register.lower`, which indicates the
        lowest value measurement made while in `HP3456a.MathMode.statistic`, or
        the lowest value preset for `HP3456a.MathMode.pass_fail`.

        :type: `float`
        """
        return self._register_read(HP3456a.Register.lower)

    @lower.setter
    def lower(self, value):
        self._register_write(HP3456a.Register.lower, value)

    @property
    def upper(self):
        """
        Get/set the value in `HP3456a.Register.upper`, which indicates the
        highest value measurement made while in `HP3456a.MathMode.statistic`,
        or the highest value preset for `HP3456a.MathMode.pass_fail`.

        :type: `float`
        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.upper)

    @upper.setter
    def upper(self, value):
        return self._register_write(HP3456a.Register.upper, value)

    @property
    def r(self):
        """
        Get/set the value in `HP3456a.Register.r`, which indicates the resistor
        value used while in `HP3456a.MathMode.dbm` or the number of recalled
        readings in reading storage mode.

        :type: `float`
        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.r)

    @r.setter
    def r(self, value):
        self._register_write(HP3456a.Register.r, value)

    @property
    def y(self):
        """
        Get/set the value in `HP3456a.Register.y` to be used in calculations
        when in `HP3456a.MathMode.scale` or `HP3456a.MathMode.percent`.

        :type: `float`
        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.y)

    @y.setter
    def y(self, value):
        self._register_write(HP3456a.Register.y, value)

    @property
    def z(self):
        """
        Get/set the value in `HP3456a.Register.z` to be used in calculations
        when in `HP3456a.MathMode.scale` or the first reading when in
        `HP3456a.MathMode.statistic`.

        :type: `float`
        :rtype: `float`
        """
        return self._register_read(HP3456a.Register.z)

    @z.setter
    def z(self, value):
        self._register_write(HP3456a.Register.z, value)

    @property
    def input_range(self):
        """Set the input range to be used.

        The `HP3456a` has separate ranges for `~quantities.ohm` and for
        `~quantities.volt`. The range value sent to the instrument depends on
        the unit set on the input range value. `auto` selects auto ranging.

        :type: `~quantities.Quantity`
        """
        raise NotImplementedError

    @input_range.setter
    def input_range(self, value):
        if isinstance(value, str):
            if value.lower() == "auto":
                self.sendcmd("R1W")
            else:
                raise ValueError("Only 'auto' is acceptable when specifying "
                                 "the input range as a string.")

        elif isinstance(value, pq.quantity.Quantity):
            if value.units == pq.volt:
                valid = HP3456a.ValidRange.voltage.value
                value = value.rescale(pq.volt)
            elif value.units == pq.ohm:
                valid = HP3456a.ValidRange.resistance.value
                value = value.rescale(pq.ohm)
            else:
                raise ValueError("Value {} not quantity.volt or quantity.ohm"
                                 "".format(value))

            value = float(value)
            if value not in valid:
                raise ValueError("Value {} outside valid ranges "
                                 "{}".format(value, valid))
            value = valid.index(value) + 2
            self.sendcmd("R{}W".format(value))
        else:
            raise TypeError("Range setting must be specified as a float, int, "
                            "or the string 'auto', got {}".format(type(value)))

    @property
    def relative(self):
        """
        Enable or disable `HP3456a.MathMode.Null` on the instrument.

        :type: `bool`
        """
        return self._null

    @relative.setter
    def relative(self, value):
        if value is True:
            self._null = True
            self.sendcmd("M{}".format(HP3456a.MathMode.null.value))
        elif value is False:
            self._null = False
            self.sendcmd("M{}".format(HP3456a.MathMode.off.value))
        else:
            raise TypeError("Relative setting must be specified as a bool, "
                            "got {}".format(type(value)))

    # METHODS ##

    def auto_range(self):
        """
        Set input range to auto. The `HP3456a` should upscale when a reading
        is at 120% and downscale when it below 11% full scale. Note that auto
        ranging can increase the measurement time.
        """
        self.input_range = "auto"

    def fetch(self, mode=None):
        """Retrieve n measurements after the HP3456a has been instructed to
        perform a series of similar measurements. Typically the mode, range,
        nplc, analog filter, autozero is set along with the number of
        measurements to take. The series is then started at the trigger
        command.

        Example usage:

        >>> dmm.number_of_digits = 6
        >>> dmm.auto_range()
        >>> dmm.nplc = 1
        >>> dmm.mode = dmm.Mode.resistance_2wire
        >>> n = 100
        >>> dmm.number_of_readings = n
        >>> dmm.trigger()
        >>> time.sleep(n * 0.04)
        >>> v = dmm.fetch(dmm.Mode.resistance_2wire)
        >>> print len(v)
        10

        :param mode: Desired measurement mode. If not specified, the previous
            set mode will be used, but no measurement unit will be returned.

        :type mode: `HP3456a.Mode`

        :return: A series of measurements from the multimeter.
        :rtype: `~quantities.quantity.Quantity`
        """
        if mode is not None:
            units = UNITS[mode]
        else:
            units = 1

        value = self.query("", size=-1)
        values = [float(x) * units for x in value.split(",")]
        return values

    def measure(self, mode=None):
        """Instruct the HP3456a to perform a one time measurement. The
        measurement will use the current set registers for the measurement
        (number_of_readings, number_of_digits, nplc, delay, mean, lower, upper,
        y and z) and will immediately take place.

        Note that using `HP3456a.measure()` will override the `trigger_mode` to
        `HP3456a.TriggerMode.single`

        Example usage:

        >>> dmm = ik.hp.HP3456a.open_gpibusb("/dev/ttyUSB0", 22)
        >>> dmm.number_of_digits = 6
        >>> dmm.nplc = 1
        >>> print dmm.measure(dmm.Mode.resistance_2wire)

        :param mode: Desired measurement mode. If not specified, the previous
            set mode will be used, but no measurement unit will be
            returned.

        :type mode: `HP3456a.Mode`

        :return: A measurement from the multimeter.
        :rtype: `~quantities.quantity.Quantity`

        """
        if mode is not None:
            modevalue = mode.value
            units = UNITS[mode]
        else:
            modevalue = ""
            units = 1

        self.sendcmd("{}W1STNT3".format(modevalue))

        value = self.query("", size=-1)
        return float(value) * units

    def _register_read(self, name):
        """
        Read a register on the HP3456a.

        :param name: The name of the register to read from
        :type name: `HP3456a.Register`
        :rtype: `float`
        """
        try:
            name = HP3456a.Register[name]
        except KeyError:
            pass
        if not isinstance(name, HP3456a.Register):
            raise TypeError("register must be specified as a "
                            "HP3456a.Register, got {} "
                            "instead.".format(name))
        self.sendcmd("RE{}".format(name.value))
        if not self._testing:  # pragma: no cover
            time.sleep(.1)
        return float(self.query("", size=-1))

    def _register_write(self, name, value):
        """
        Write a register on the HP3456a.

        :param name: The name of the register to write to
        :type name: `HP3456a.Register`
        :type value: `float`
        """
        try:
            name = HP3456a.Register[name]
        except KeyError:
            pass
        if not isinstance(name, HP3456a.Register):
            raise TypeError("register must be specified as a "
                            "HP3456a.Register, got {} "
                            "instead.".format(name))
        if name in [
                HP3456a.Register.mean,
                HP3456a.Register.variance,
                HP3456a.Register.count
        ]:
            raise ValueError("register {} is read only".format(name))
        self.sendcmd("W{}ST{}".format(value, name.value))
        if not self._testing:  # pragma: no cover
            time.sleep(.1)

    def trigger(self):
        """
        Signal a single manual trigger event to the `HP3456a`.
        """
        self.sendcmd("T3")

# UNITS #######################################################################

UNITS = {
    None: 1,
    HP3456a.Mode.dcv: pq.volt,
    HP3456a.Mode.acv: pq.volt,
    HP3456a.Mode.acvdcv: pq.volt,
    HP3456a.Mode.resistance_2wire: pq.ohm,
    HP3456a.Mode.resistance_4wire: pq.ohm,
    HP3456a.Mode.ratio_dcv_dcv: 1,
    HP3456a.Mode.ratio_acv_dcv: 1,
    HP3456a.Mode.ratio_acvdcv_dcv: 1,
    HP3456a.Mode.oc_resistence_2wire: pq.ohm,
    HP3456a.Mode.oc_resistence_4wire: pq.ohm,
}
