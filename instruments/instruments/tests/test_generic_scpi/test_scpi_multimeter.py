#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for generic SCPI multimeter instruments
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

test_scpi_multimeter_name = make_name_test(ik.generic_scpi.SCPIMultimeter)


def test_scpi_multimeter_mode():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?",
            "CONF:CURR:AC"
        ], [
            "FRES +1.000000E+01,+3.000000E-06"
        ]
    ) as dmm:
        assert dmm.mode == dmm.Mode.fourpt_resistance
        dmm.mode = dmm.Mode.current_ac


def test_scpi_multimeter_trigger_mode():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "TRIG:SOUR?",
            "TRIG:SOUR EXT"
        ], [
            "BUS"
        ]
    ) as dmm:
        assert dmm.trigger_mode == dmm.TriggerMode.bus
        dmm.trigger_mode = dmm.TriggerMode.external


def test_scpi_multimeter_input_range():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?",  # 1
            "CONF?",  # 2
            "CONF?",  # 3.1
            "CONF:FRES MIN",  # 3.2
            "CONF?",  # 4.1
            "CONF:CURR:DC 1.0"  # 4.2
        ], [
            "CURR:AC +1.000000E+01,+3.000000E-06",  # 1
            "CURR:AC AUTO,+3.000000E-06",  # 2
            "FRES +1.000000E+01,+3.000000E-06",  # 3
            "CURR:DC +1.000000E+01,+3.000000E-06"  # 4
        ]
    ) as dmm:
        unit_eq(dmm.input_range, 1e1 * pq.amp)
        assert dmm.input_range == dmm.InputRange.automatic
        dmm.input_range = dmm.InputRange.minimum
        dmm.input_range = 1 * pq.amp


def test_scpi_multimeter_resolution():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?",  # 1
            "CONF?",  # 2
            "CONF?",  # 3.1
            "CONF:FRES +1.000000E+01,MIN",  # 3.2
            "CONF?",  # 4.1
            "CONF:CURR:DC +1.000000E+01,3e-06"  # 4.2
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",  # 1
            "VOLT +1.000000E+01,MAX",  # 2
            "FRES +1.000000E+01,+3.000000E-06",  # 3
            "CURR:DC +1.000000E+01,+3.000000E-06"  # 4
        ]
    ) as dmm:
        assert dmm.resolution == 3e-06
        assert dmm.resolution == dmm.Resolution.maximum
        dmm.resolution = dmm.Resolution.minimum
        dmm.resolution = 3e-06


def test_scpi_multimeter_trigger_count():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "TRIG:COUN?",
            "TRIG:COUN?",
            "TRIG:COUN MIN",
            "TRIG:COUN 10"
        ], [
            "+10",
            "INF",
        ]
    ) as dmm:
        assert dmm.trigger_count == 10
        assert dmm.trigger_count == dmm.TriggerCount.infinity
        dmm.trigger_count = dmm.TriggerCount.minimum
        dmm.trigger_count = 10


def test_scpi_multimeter_sample_count():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "SAMP:COUN?",
            "SAMP:COUN?",
            "SAMP:COUN MIN",
            "SAMP:COUN 10"
        ], [
            "+10",
            "MAX",
        ]
    ) as dmm:
        assert dmm.sample_count == 10
        assert dmm.sample_count == dmm.SampleCount.maximum
        dmm.sample_count = dmm.SampleCount.minimum
        dmm.sample_count = 10


def test_scpi_multimeter_trigger_delay():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "TRIG:DEL?",
            "TRIG:DEL {:e}".format(1),
        ], [
            "+1",
        ]
    ) as dmm:
        unit_eq(dmm.trigger_delay, 1 * pq.second)
        dmm.trigger_delay = 1000 * pq.millisecond


def test_scpi_multimeter_sample_source():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "SAMP:SOUR?",
            "SAMP:SOUR TIM",
        ], [
            "IMM",
        ]
    ) as dmm:
        assert dmm.sample_source == dmm.SampleSource.immediate
        dmm.sample_source = dmm.SampleSource.timer


def test_scpi_multimeter_sample_timer():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "SAMP:TIM?",
            "SAMP:TIM {:e}".format(1),
        ], [
            "+1",
        ]
    ) as dmm:
        unit_eq(dmm.sample_timer, 1 * pq.second)
        dmm.sample_timer = 1000 * pq.millisecond


def test_scpi_multimeter_measure():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "MEAS:VOLT:DC?",
        ], [
            "+4.23450000E-03",
        ]
    ) as dmm:
        unit_eq(dmm.measure(dmm.Mode.voltage_dc), 4.2345e-03 * pq.volt)
