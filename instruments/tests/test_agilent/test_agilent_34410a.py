#!/usr/bin/env python
"""
Module containing tests for Agilent 34410a
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import expected_protocol, iterable_eq, make_name_test, unit_eq
from instruments.units import ureg as u

# TESTS ######################################################################

test_agilent_34410a_name = make_name_test(ik.agilent.Agilent34410a)


def test_agilent34410a_read():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["CONF?", "READ?"],
        ["VOLT +1.000000E+01,+3.000000E-06", "+1.86850000E-03"],
    ) as dmm:
        unit_eq(dmm.read_meter(), +1.86850000e-03 * u.volt)


def test_agilent34410a_data_point_count():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "DATA:POIN?",
        ],
        [
            "+215",
        ],
    ) as dmm:
        assert dmm.data_point_count == 215


def test_agilent34410a_init():
    """Switch device from `idle` to `wait-for-trigger state`."""
    with expected_protocol(ik.agilent.Agilent34410a, ["INIT"], []) as dmm:
        dmm.init()


def test_agilent34410a_abort():
    """Abort all current measurements."""
    with expected_protocol(ik.agilent.Agilent34410a, ["ABOR"], []) as dmm:
        dmm.abort()


def test_agilent34410a_clear_memory():
    """Clear non-volatile memory."""
    with expected_protocol(ik.agilent.Agilent34410a, ["DATA:DEL NVMEM"], []) as dmm:
        dmm.clear_memory()


def test_agilent34410a_r():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["CONF?", "FORM:DATA REAL,64", "R? 1"],
        [
            "VOLT +1.000000E+01,+3.000000E-06",
            # pylint: disable=no-member
            b"#18" + bytes.fromhex("3FF0000000000000"),
        ],
    ) as dmm:
        expected = (u.Quantity(1, u.volt),)
        if numpy:
            expected = numpy.array([1]) * u.volt
        actual = dmm.r(1)
        iterable_eq(actual, expected)


def test_agilent34410a_r_count_zero():
    """Read measurements with count set to zero."""
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["CONF?", "FORM:DATA REAL,64", "R?"],
        [
            "VOLT +1.000000E+01,+3.000000E-06",
            # pylint: disable=no-member
            b"#18" + bytes.fromhex("3FF0000000000000"),
        ],
    ) as dmm:
        expected = (u.Quantity(1, u.volt),)
        if numpy:
            expected = numpy.array([1]) * u.volt
        actual = dmm.r(0)
        iterable_eq(actual, expected)


def test_agilent34410a_r_type_error():
    """Raise TypeError if count is not a integer."""
    wrong_type = "42"
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
        ],
        [
            "VOLT +1.000000E+01,+3.000000E-06",
        ],
    ) as dmm:
        with pytest.raises(TypeError) as err_info:
            dmm.r(wrong_type)
        err_msg = err_info.value.args[0]
        assert err_msg == 'Parameter "count" must be an integer'


def test_agilent34410a_fetch():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["CONF?", "FETC?"],
        ["VOLT +1.000000E+01,+3.000000E-06", "+4.27150000E-03,5.27150000E-03"],
    ) as dmm:
        data = dmm.fetch()
        expected = (4.27150000e-03 * u.volt, 5.27150000e-03 * u.volt)
        if numpy:
            expected = (4.27150000e-03, 5.27150000e-03) * u.volt
        iterable_eq(data, expected)


def test_agilent34410a_read_data():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["CONF?", "FORM:DATA ASC", "DATA:REM? 2"],
        ["VOLT +1.000000E+01,+3.000000E-06", "+4.27150000E-03,5.27150000E-03"],
    ) as dmm:
        data = dmm.read_data(2)
        unit_eq(data[0], 4.27150000e-03 * u.volt)
        unit_eq(data[1], 5.27150000e-03 * u.volt)


def test_agilent34410a_read_data_count_minus_one():
    """Read data for all data points available."""
    sample_count = 100
    with expected_protocol(
        ik.agilent.Agilent34410a,
        ["DATA:POIN?", "CONF?", "FORM:DATA ASC", f"DATA:REM? {sample_count}"],
        [
            f"{sample_count}",
            "VOLT +1.000000E+01,+3.000000E-06",
            "+4.27150000E-03,5.27150000E-03",
        ],
    ) as dmm:
        data = dmm.read_data(-1)
        unit_eq(data[0], 4.27150000e-03 * u.volt)
        unit_eq(data[1], 5.27150000e-03 * u.volt)


def test_agilent34410a_read_data_type_error():
    """Raise Type error if count is not an integer."""
    wrong_type = "42"
    with expected_protocol(ik.agilent.Agilent34410a, [], []) as dmm:
        with pytest.raises(TypeError) as err_info:
            dmm.read_data(wrong_type)
        err_msg = err_info.value.args[0]
        assert err_msg == 'Parameter "sample_count" must be an integer.'


def test_agilent34410a_read_data_nvmem():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "DATA:DATA? NVMEM",
        ],
        ["VOLT +1.000000E+01,+3.000000E-06", "+4.27150000E-03,5.27150000E-03"],
    ) as dmm:
        data = dmm.read_data_nvmem()
        unit_eq(data[0], 4.27150000e-03 * u.volt)
        unit_eq(data[1], 5.27150000e-03 * u.volt)


def test_agilent34410a_read_last_data():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "DATA:LAST?",
        ],
        [
            "+1.73730000E-03 VDC",
        ],
    ) as dmm:
        unit_eq(dmm.read_last_data(), 1.73730000e-03 * u.volt)


def test_agilent34410a_read_last_data_na():
    """Return 9.91e37 if no data are available to read."""
    na_value_str = "9.91000000E+37"
    with expected_protocol(
        ik.agilent.Agilent34410a, ["DATA:LAST?"], [na_value_str]
    ) as dmm:
        assert dmm.read_last_data() == float(na_value_str)
