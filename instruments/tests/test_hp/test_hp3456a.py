#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the HP 3456a digital voltmeter
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################

# pylint: disable=protected-access


def test_hp3456a_trigger_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "T4",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.trigger_mode = dmm.TriggerMode.hold


@raises(ValueError)
def test_hp3456a_number_of_digits():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W6STG",
            "REG"
        ], [
            "+06.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        dmm.number_of_digits = 7


def test_hp3456a_number_of_digits_invalid():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W6STG",
            "REG"
        ], [
            "+06.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        dmm.number_of_digits = 6
        assert dmm.number_of_digits == 6


def test_hp3456a_auto_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "R1W",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.auto_range()


def test_hp3456a_number_of_readings():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W10STN",
            "REN"
        ], [
            "+10.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        dmm.number_of_readings = 10
        assert dmm.number_of_readings == 10


def test_hp3456a_nplc():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W1STI",
            "REI"
        ], [
            "+1.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        dmm.nplc = 1
        assert dmm.nplc == 1


@raises(ValueError)
def test_hp3456a_nplc_invalid():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W1STI",
            "REI"
        ], [
            "+1.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        dmm.nplc = 0


def test_hp3456a_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "S0F4",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.mode = dmm.Mode.resistance_2wire


def test_hp3456a_math_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "M2",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.math_mode = dmm.MathMode.statistic


def test_hp3456a_trigger():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "T3",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.trigger()


def test_hp3456a_fetch():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1"
        ],
        [
            "+000.1055E+0,+000.1043E+0,+000.1005E+0,+000.1014E+0",
            "+000.1055E+0,+000.1043E+0,+000.1005E+0,+000.1014E+0"
        ],
        sep="\r"
    ) as dmm:
        v = dmm.fetch(dmm.Mode.resistance_2wire)
        np.testing.assert_array_equal(
            v, [0.1055, 0.1043, 0.1005, 0.1014] * pq.ohm
        )
        assert v[0].units == pq.ohm
        v = dmm.fetch()
        np.testing.assert_array_equal(
            v, [0.1055, 0.1043, 0.1005, 0.1014] * pq.ohm
        )
        assert isinstance(v[0], float)


def test_hp3456a_variance():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REV",
        ], [
            "+04.93111E-6"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.variance == +04.93111E-6


def test_hp3456a_count():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REC",
        ], [
            "+10.00000E+0"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.count == +10


def test_hp3456a_mean():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REM",
        ], [
            "+102.1000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.mean == +102.1000E-3


def test_hp3456a_delay():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "RED",
            "W1.0STD"
        ], [
            "-000.0000E+0"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.delay == 0
        dmm.delay = 1 * pq.sec


def test_hp3456a_lower():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REL",
            "W0.0993STL"
        ], [
            "+099.3000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.lower == +099.3000E-3
        dmm.lower = +099.3000E-3


def test_hp3456a_upper():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REU",
            "W0.1055STU"
        ], [
            "+105.5000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.upper == +105.5000E-3
        dmm.upper = +105.5000E-3


def test_hp3456a_ryz():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "RER",
            "REY",
            "REZ",
            "W600.0STR",
            "W1.0STY",
            "W0.1055STZ"
        ], [
            "+0600.000E+0",
            "+1.000000E+0",
            "+105.5000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.r == +0600.000E+0
        assert dmm.y == +1.000000E+0
        assert dmm.z == +105.5000E-3
        dmm.r = +0600.000E+0
        dmm.y = +1.000000E+0
        dmm.z = +105.5000E-3


def test_hp3456a_measure():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "S1F1W1STNT3",
            "S0F4W1STNT3",
            "S0F1W1STNT3",
            "W1STNT3"
        ],
        [
            "+00.00000E-3",
            "+000.1010E+0",
            "+000.0002E-3",
            "+000.0002E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.measure(dmm.Mode.ratio_dcv_dcv) == 0
        assert dmm.measure(dmm.Mode.resistance_2wire) == +000.1010E+0 * pq.ohm
        assert dmm.measure(dmm.Mode.dcv) == +000.0002E-3 * pq.volt
        assert dmm.measure() == +000.0002E-3


def test_hp3456a_input_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "R2W",
            "R3W"
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.input_range = 10 ** -1 * pq.volt
        dmm.input_range = 1e3 * pq.ohm


@raises(ValueError)
def test_hp3456a_input_range_invalid_str():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm.input_range = "derp"


@raises(ValueError)
def test_hp3456a_input_range_invalid_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm.input_range = 1 * pq.ohm


@raises(TypeError)
def test_hp3456a_input_range_bad_type():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm.input_range = True


@raises(ValueError)
def test_hp3456a_input_range_bad_units():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm.input_range = 1 * pq.amp


def test_hp3456a_relative():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "M0",
            "M3",
        ], [
            "",
        ],
        sep="\r"
    ) as dmm:
        dmm.relative = False
        dmm.relative = True
        assert dmm.relative is True


@raises(TypeError)
def test_hp3456a_relative_bad_type():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm.relative = "derp"


def test_hp3456a_auto_zero():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "Z0",
            "Z1",
        ], [
            "",
        ],
        sep="\r"
    ) as dmm:
        dmm.autozero = False
        dmm.autozero = True


def test_hp3456a_filter():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "FL0",
            "FL1",
        ], [
            "",
        ],
        sep="\r"
    ) as dmm:
        dmm.filter = False
        dmm.filter = True


@raises(TypeError)
def test_hp3456a_register_read_bad_name():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm._register_read("foobar")


@raises(TypeError)
def test_hp3456a_register_write_bad_name():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm._register_write("foobar", 1)


@raises(ValueError)
def test_hp3456a_register_write_bad_register():
    with expected_protocol(
        ik.hp.HP3456a,
        [],
        [],
        sep="\r"
    ) as dmm:
        dmm._register_write(dmm.Register.mean, 1)
