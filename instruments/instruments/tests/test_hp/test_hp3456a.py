#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the HP 3456a digital voltmeter
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS #######################################################################


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
            "HO0T4SO1",
        ], [
            "+000.1055E+0,+000.1043E+0,+000.1005E+0,+000.1014E+0"
        ],
        sep="\r"
    ) as dmm:
        v = dmm.fetch(dmm.Mode.resistance_2wire)
        np.testing.assert_array_equal(
            v, [0.1055, 0.1043, 0.1005, 0.1014] * pq.ohm)


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
        ], [
            "-000.0000E+0"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.delay == 0


def test_hp3456a_lower():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REL",
        ], [
            "+099.3000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.lower == +099.3000E-3


def test_hp3456a_upper():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REU",
        ], [
            "+105.5000E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.upper == +105.5000E-3


def test_hp3456a_ryz():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "RER",
            "REY",
            "REZ"
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


def test_hp3456a_measure():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "S1F1W1STNT3",
            "S0F4W1STNT3",
            "S0F1W1STNT3"
        ], [
            "+00.00000E-3",
            "+000.1010E+0",
            "+000.0002E-3"
        ],
        sep="\r"
    ) as dmm:
        assert dmm.measure(dmm.Mode.ratio_dcv_dcv) == 0
        assert dmm.measure(dmm.Mode.resistance_2wire) == +000.1010E+0 * pq.ohm
        assert dmm.measure(dmm.Mode.dcv) == +000.0002E-3 * pq.volt


def test_hp3456a_input_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "R2W",
        ], [
            ""
        ],
        sep="\r"
    ) as dmm:
        dmm.input_range = 10 ** -1 * pq.volt


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
