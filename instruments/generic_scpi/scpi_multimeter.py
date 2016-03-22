#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for SCPI compliant multimeters
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from enum import Enum

import quantities as pq

from instruments.abstract_instruments import Multimeter
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, enum_property, unitful_property

# CONSTANTS ###################################################################

VALID_FRES_NAMES = ['4res', '4 res', 'four res', 'f res']

UNITS_CAPACITANCE = ['cap']
UNITS_VOLTAGE = ['volt:dc', 'volt:ac', 'diod']
UNITS_CURRENT = ['curr:dc', 'curr:ac']
UNITS_RESISTANCE = ['res', 'fres'] + VALID_FRES_NAMES
UNITS_FREQUENCY = ['freq']
UNITS_TIME = ['per']
UNITS_TEMPERATURE = ['temp']

# CLASSES #####################################################################


class SCPIMultimeter(SCPIInstrument, Multimeter):

    """
    This class is used for communicating with generic SCPI-compliant
    multimeters.

    Example usage:

    >>> import instruments as ik
    >>> inst = ik.generic_scpi.SCPIMultimeter.open_tcpip("192.168.1.1")
    >>> print(inst.measure(inst.Mode.resistance))
    """

    def __init__(self, filelike):
        super(SCPIMultimeter, self).__init__(filelike)

    # ENUMS ##

    class Mode(Enum):

        """
        Enum of valid measurement modes for (most) SCPI compliant multimeters
        """
        capacitance = "CAP"
        continuity = "CONT"
        current_ac = "CURR:AC"
        current_dc = "CURR:DC"
        diode = "DIOD"
        frequency = "FREQ"
        fourpt_resistance = "FRES"
        period = "PER"
        resistance = "RES"
        temperature = "TEMP"
        voltage_ac = "VOLT:AC"
        voltage_dc = "VOLT:DC"

    class TriggerMode(Enum):

        """
        Valid trigger sources for most SCPI Multimeters.

        "Immediate": This is a continuous trigger. This means the trigger
        signal is always present.

        "External": External TTL pulse on the back of the instrument. It
        is active low.

        "Bus": Causes the instrument to trigger when a ``*TRG`` command is
        sent by software. This means calling the trigger() function.
        """
        immediate = "IMM"
        external = "EXT"
        bus = "BUS"

    class InputRange(Enum):

        """
        Valid device range parameters outside of directly specifying the range.
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"
        automatic = "AUTO"

    class Resolution(Enum):

        """
        Valid measurement resolution parameters outside of directly the
        resolution.
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"

    class TriggerCount(Enum):

        """
        Valid trigger count parameters outside of directly the value.
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"
        infinity = "INF"

    class SampleCount(Enum):

        """
        Valid sample count parameters outside of directly the value.
        """
        minimum = "MIN"
        maximum = "MAX"
        default = "DEF"

    class SampleSource(Enum):

        """
        Valid sample source parameters.

        #. "immediate": The trigger delay time is inserted between successive
            samples. After the first measurement is completed, the instrument
            waits the time specified by the trigger delay and then performs the
            next sample.
        #. "timer": Successive samples start one sample interval after the
            START of the previous sample.
        """
        immediate = "IMM"
        timer = "TIM"

    # PROPERTIES ##

    # pylint: disable=unnecessary-lambda
    mode = enum_property(
        name="CONF",
        enum=Mode,
        doc="""
        Gets/sets the current measurement mode for the multimeter.

        Example usage:

        >>> dmm.mode = dmm.Mode.voltage_dc

        :type: `~SCPIMultimeter.Mode`
        """,
        input_decoration=lambda x: SCPIMultimeter._mode_parse(x),
        set_fmt="{}:{}"
    )

    trigger_mode = enum_property(
        name="TRIG:SOUR",
        enum=TriggerMode,
        doc="""
            Gets/sets the SCPI Multimeter trigger mode.

            Example usage:

            >>> dmm.trigger_mode = dmm.TriggerMode.external

            :type: `~SCPIMultimeter.TriggerMode`
        """)

    @property
    def input_range(self):
        """
        Gets/sets the device input range for the device range for the currently
        set multimeter mode.

        Example usages:

        >>> dmm.input_range = dmm.InputRange.automatic
        >>> dmm.input_range = 1 * pq.millivolt

        :units: As appropriate for the current mode setting.
        :type: `~quantities.Quantity`, or `~SCPIMultimeter.InputRange`
        """
        value = self.query('CONF?')
        mode = self.Mode(self._mode_parse(value))
        value = value.split(" ")[1].split(",")[0]  # Extract device range
        try:
            return float(value) * UNITS[mode]
        except ValueError:
            return self.InputRange(value.strip())

    @input_range.setter
    def input_range(self, newval):
        current = self.query("CONF?")
        mode = self.Mode(self._mode_parse(current))
        units = UNITS[mode]
        if isinstance(newval, self.InputRange):
            newval = newval.value
        else:
            newval = assume_units(newval, units).rescale(units).magnitude
        self.sendcmd("CONF:{} {}".format(mode.value, newval))

    @property
    def resolution(self):
        """
        Gets/sets the measurement resolution for the multimeter. When
        specified as a float it is assumed that the user is providing an
        appropriate value.

        Example usage:

        >>> dmm.resolution = 3e-06
        >>> dmm.resolution = dmm.Resolution.maximum

        :type: `int`, `float` or `~SCPIMultimeter.Resolution`
        """
        value = self.query('CONF?')
        value = value.split(" ")[1].split(",")[1]  # Extract resolution
        try:
            return float(value)
        except ValueError:
            return self.Resolution(value.strip())

    @resolution.setter
    def resolution(self, newval):
        current = self.query("CONF?")
        mode = self.Mode(self._mode_parse(current))
        input_range = current.split(" ")[1].split(",")[0]
        if isinstance(newval, self.Resolution):
            newval = newval.value
        elif not isinstance(newval, (float, int)):
            raise TypeError("Resolution must be specified as an int, float, "
                            "or SCPIMultimeter.Resolution value.")
        self.sendcmd("CONF:{} {},{}".format(mode.value, input_range, newval))

    @property
    def trigger_count(self):
        """
        Gets/sets the number of triggers that the multimeter will accept before
        returning to an "idle" trigger state.

        Note that if the sample_count propery has been changed, the number
        of readings taken total will be a multiplication of sample count and
        trigger count (see property `SCPIMulimeter.sample_count`).

        If specified as a `~SCPIMultimeter.TriggerCount` value, the following
        options apply:

        #. "minimum": 1 trigger
        #. "maximum": Maximum value as per instrument manual
        #. "default": Instrument default as per instrument manual
        #. "infinity": Continuous. Typically when the buffer is filled in this
            case, the older data points are overwritten.

        Note that when using triggered measurements, it is recommended that you
        disable autorange by either explicitly disabling it or specifying your
        desired range.

        :type: `int` or `~SCPIMultimeter.TriggerCount`
        """
        value = self.query('TRIG:COUN?')
        try:
            return int(value)
        except ValueError:
            return self.TriggerCount(value.strip())

    @trigger_count.setter
    def trigger_count(self, newval):
        if isinstance(newval, self.TriggerCount):
            newval = newval.value
        elif not isinstance(newval, int):
            raise TypeError("Trigger count must be specified as an int "
                            "or SCPIMultimeter.TriggerCount value.")
        self.sendcmd("TRIG:COUN {}".format(newval))

    @property
    def sample_count(self):
        """
        Gets/sets the number of readings (samples) that the multimeter will
        take per trigger event.

        The time between each measurement is defined with the sample_timer
        property.

        Note that if the trigger_count propery has been changed, the number
        of readings taken total will be a multiplication of sample count and
        trigger count (see property `SCPIMulimeter.trigger_count`).

        If specified as a `~SCPIMultimeter.SampleCount` value, the following
        options apply:

        #. "minimum": 1 sample per trigger
        #. "maximum": Maximum value as per instrument manual
        #. "default": Instrument default as per instrument manual

        Note that when using triggered measurements, it is recommended that you
        disable autorange by either explicitly disabling it or specifying your
        desired range.

        :type: `int` or `~SCPIMultimeter.SampleCount`
        """
        value = self.query('SAMP:COUN?')
        try:
            return int(value)
        except ValueError:
            return self.SampleCount(value.strip())

    @sample_count.setter
    def sample_count(self, newval):
        if isinstance(newval, self.SampleCount):
            newval = newval.value
        elif not isinstance(newval, int):
            raise TypeError("Sample count must be specified as an int "
                            "or SCPIMultimeter.SampleCount value.")
        self.sendcmd("SAMP:COUN {}".format(newval))

    trigger_delay = unitful_property(
        name="TRIG:DEL",
        units=pq.second,
        doc="""
        Gets/sets the time delay which the multimeter will use following
        receiving a trigger event before starting the measurement.

        :units: As specified, or assumed to be of units seconds otherwise.
        :type: `~quantities.Quantity`
        """
    )

    sample_source = enum_property(
        name="SAMP:SOUR",
        enum=SampleSource,
        doc="""
        Gets/sets the multimeter sample source. This determines whether the
        trigger delay or the sample timer is used to dtermine sample timing when
        the sample count is greater than 1.

        In both cases, the first sample is taken one trigger delay time period
        after the trigger event. After that, it depends on which mode is used.

        :type: `SCPIMultimeter.SampleSource`
        """
    )

    sample_timer = unitful_property(
        name="SAMP:TIM",
        units=pq.second,
        doc="""
        Gets/sets the sample interval when the sample counter is greater than
        one and when the sample source is set to timer (see
        `SCPIMultimeter.sample_source`).

        This command does not effect the delay between the trigger occuring and
        the start of the first sample. This trigger delay is set with the
        `~SCPIMultimeter.trigger_delay` property.

        :units: As specified, or assumed to be of units seconds otherwise.
        :type: `~quantities.Quantity`
        """
    )

    @property
    def relative(self):
        raise NotImplementedError

    @relative.setter
    def relative(self, newval):
        raise NotImplementedError

    # METHODS ##

    def measure(self, mode=None):
        """
        Instruct the multimeter to perform a one time measurement. The
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are
        directly sent to the instrument's output buffer.

        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units. If no appropriate units exist,
        (for example, continuity), then return type is `float`.

        :param mode: Desired measurement mode. If set to `None`, will default
            to the current mode.
        :type mode: `~SCPIMultimeter.Mode`
        """
        if mode is None:
            mode = self.mode
        if not isinstance(mode, SCPIMultimeter.Mode):
            raise TypeError("Mode must be specified as a SCPIMultimeter.Mode "
                            "value, got {} instead.".format(type(mode)))
        # pylint: disable=no-member
        value = float(self.query('MEAS:{}?'.format(mode.value)))
        return value * UNITS[mode]

    # INTERNAL FUNCTIONS ##

    @staticmethod
    def _mode_parse(val):
        """
        When given a string of the form

        "VOLT +1.00000000E+01,+3.00000000E-06"

        this function will return just the first component representing the mode
        the multimeter is currently in.

        :param str val: Input string to be parsed.

        :rtype: `str`
        """
        val = val.split(" ")[0]
        if val == "VOLT":
            val = "VOLT:DC"
        return val

# UNITS #######################################################################

UNITS = {
    SCPIMultimeter.Mode.capacitance: pq.farad,
    SCPIMultimeter.Mode.voltage_dc:  pq.volt,
    SCPIMultimeter.Mode.voltage_ac:  pq.volt,
    SCPIMultimeter.Mode.diode:       pq.volt,
    SCPIMultimeter.Mode.current_ac:  pq.amp,
    SCPIMultimeter.Mode.current_dc:  pq.amp,
    SCPIMultimeter.Mode.resistance:  pq.ohm,
    SCPIMultimeter.Mode.fourpt_resistance: pq.ohm,
    SCPIMultimeter.Mode.frequency:   pq.hertz,
    SCPIMultimeter.Mode.period:      pq.second,
    SCPIMultimeter.Mode.temperature: pq.kelvin,
    SCPIMultimeter.Mode.continuity:  1,
}
