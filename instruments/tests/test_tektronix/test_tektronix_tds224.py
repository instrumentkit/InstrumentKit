#!/usr/bin/env python
"""
Module containing tests for the Tektronix TDS224
"""

# IMPORTS ####################################################################

from enum import Enum
import time

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import (
    expected_protocol,
    iterable_eq,
    make_name_test,
)

# TESTS ######################################################################

# pylint: disable=protected-access,redefined-outer-name


# FIXTURES #


@pytest.fixture(autouse=True)
def mock_time(mocker):
    """Mock time to replace time.sleep."""
    return mocker.patch.object(time, "sleep", return_value=None)


test_tektds224_name = make_name_test(ik.tektronix.TekTDS224)


def test_ref_init():
    """Initialize a reference channel."""
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        assert tek.ref[0]._tek is tek


def test_data_source_name():
    """Get name of data source."""
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        assert tek.math.name == "MATH"


def test_tektds224_data_width():
    with expected_protocol(
        ik.tektronix.TekTDS224, ["DATA:WIDTH?", "DATA:WIDTH 1"], ["2"]
    ) as tek:
        assert tek.data_width == 2
        tek.data_width = 1


@given(width=st.integers().filter(lambda x: x > 2 or x < 1))
def test_tektds224_data_width_value_error(width):
    """Raise value error if data_width is out of range."""
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        with pytest.raises(ValueError) as err_info:
            tek.data_width = width
        err_msg = err_info.value.args[0]
        assert err_msg == "Only one or two byte-width is supported."


def test_tektds224_data_source(mock_time):
    with expected_protocol(
        ik.tektronix.TekTDS224,
        ["DAT:SOU?", "DAT:SOU?", "DAT:SOU MATH"],
        ["MATH", "CH1"],
    ) as tek:
        assert tek.data_source == tek.math
        assert tek.data_source == ik.tektronix.tektds224.TekTDS224.Channel(tek, 0)
        tek.data_source = tek.math

        # assert that time.sleep is called
        mock_time.assert_called()


def test_tektds224_data_source_with_enum():
    """Set data source from an enum."""

    class Channel(Enum):
        """Fake class to init data_source with enum."""

        channel = "MATH"

    with expected_protocol(ik.tektronix.TekTDS224, ["DAT:SOU MATH"], []) as tek:
        tek.data_source = Channel.channel


def test_tektds224_channel():
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        assert tek.channel[0] == ik.tektronix.tektds224.TekTDS224.Channel(tek, 0)


def test_tektds224_channel_coupling():
    with expected_protocol(
        ik.tektronix.TekTDS224, ["CH1:COUPL?", "CH2:COUPL AC"], ["DC"]
    ) as tek:
        assert tek.channel[0].coupling == tek.Coupling.dc
        tek.channel[1].coupling = tek.Coupling.ac


def test_tektds224_channel_coupling_type_error():
    """Raise TypeError if coupling setting is wrong type."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        with pytest.raises(TypeError) as err_info:
            tek.channel[1].coupling = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Coupling setting must be a `TekTDS224.Coupling` "
            f"value,got {type(wrong_type)} instead."
        )


def test_tektds224_data_source_read_waveform():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "DAT:SOU?",
            "DAT:SOU CH2",
            "DAT:ENC RIB",
            "DATA:WIDTH?",
            "CURVE?",
            "WFMP:CH2:YOF?",
            "WFMP:CH2:YMU?",
            "WFMP:CH2:YZE?",
            "WFMP:XZE?",
            "WFMP:XIN?",
            "WFMP:CH2:NR_P?",
            "DAT:SOU CH1",
        ],
        [
            "CH1",
            "2",
            # pylint: disable=no-member
            "#210" + bytes.fromhex("00000001000200030004").decode("utf-8") + "0",
            "1",
            "0",
            "0",
            "1",
            "5",
        ],
    ) as tek:
        data = tuple(range(5))
        if numpy:
            data = numpy.array([0, 1, 2, 3, 4])
        (x, y) = tek.channel[1].read_waveform()
        iterable_eq(x, data)
        iterable_eq(y, data)


@given(values=st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=1))
def test_tektds224_data_source_read_waveform_ascii(values):
    """Read waveform as ASCII"""
    # values
    values_str = ",".join([str(value) for value in values])

    # parameters
    yoffs = 1
    ymult = 1
    yzero = 0
    xzero = 0
    xincr = 1
    ptcnt = len(values)

    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "DAT:SOU?",
            "DAT:SOU CH2",
            "DAT:ENC ASCI",
            "CURVE?",
            "WFMP:CH2:YOF?",
            "WFMP:CH2:YMU?",
            "WFMP:CH2:YZE?",
            "WFMP:XZE?",
            "WFMP:XIN?",
            "WFMP:CH2:NR_P?",
            "DAT:SOU CH1",
        ],
        [
            "CH1",
            values_str,
            f"{yoffs}",
            f"{ymult}",
            f"{yzero}",
            f"{xzero}",
            f"{xincr}",
            f"{ptcnt}",
        ],
    ) as tek:
        if numpy:
            x_expected = numpy.arange(float(ptcnt)) * float(xincr) + float(xzero)
            y_expected = ((numpy.array(values) - float(yoffs)) * float(ymult)) + float(
                yzero
            )
        else:
            x_expected = tuple(
                float(val) * float(xincr) + float(xzero) for val in range(ptcnt)
            )
            y_expected = tuple(
                ((val - float(yoffs)) * float(ymult)) + float(yzero) for val in values
            )
        x_read, y_read = tek.channel[1].read_waveform(bin_format=False)
        iterable_eq(x_read, x_expected)
        iterable_eq(y_read, y_expected)


def test_force_trigger():
    """Raise NotImplementedError when trying to force a trigger."""
    with expected_protocol(ik.tektronix.TekTDS224, [], []) as tek:
        with pytest.raises(NotImplementedError):
            tek.force_trigger()
