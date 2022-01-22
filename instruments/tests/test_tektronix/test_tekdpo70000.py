#!/usr/bin/env python
"""
Tests for the Tektronix DPO 70000 oscilloscope.
"""

# IMPORTS #####################################################################

import struct
import time

from hypothesis import (
    given,
    strategies as st,
)
import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import (
    expected_protocol,
    iterable_eq,
    make_name_test,
    unit_eq,
)
from instruments.units import ureg as u


# TESTS #######################################################################

# pylint: disable=too-many-lines,protected-access


test_tekdpo70000_name = make_name_test(ik.tektronix.TekDPO70000)


# STATIC METHOD #


@pytest.mark.parametrize("binary_format", ik.tektronix.TekDPO70000.BinaryFormat)
@pytest.mark.parametrize("byte_order", ik.tektronix.TekDPO70000.ByteOrder)
@pytest.mark.parametrize("n_bytes", (1, 2, 4, 8))
def test_dtype(binary_format, byte_order, n_bytes):
    """Return the formatted format name, depending on settings."""
    binary_format_dict = {
        ik.tektronix.TekDPO70000.BinaryFormat.int: "i",
        ik.tektronix.TekDPO70000.BinaryFormat.uint: "u",
        ik.tektronix.TekDPO70000.BinaryFormat.float: "f",
    }
    byte_order_dict = {
        ik.tektronix.TekDPO70000.ByteOrder.big_endian: ">",
        ik.tektronix.TekDPO70000.ByteOrder.little_endian: "<",
    }
    value_expected = (
        f"{byte_order_dict[byte_order]}"
        f"{n_bytes}"
        f"{binary_format_dict[binary_format]}"
    )
    with expected_protocol(ik.tektronix.TekDPO70000, [], []) as inst:
        assert inst._dtype(binary_format, byte_order, n_bytes) == value_expected


# DATA SOURCE - TESTED WITH CHANNELS #


def test_data_source_name():
    """Query the name of a data source."""
    channel = 0
    with expected_protocol(ik.tektronix.TekDPO70000, [], []) as inst:
        assert inst.channel[channel].name == f"CH{channel+1}"


@pytest.mark.parametrize("channel", [it for it in range(4)])
@given(
    values=st.lists(
        st.integers(min_value=-2147483648, max_value=2147483647), min_size=1
    )
)
def test_data_source_read_waveform(channel, values):
    """Read waveform from data source, binary format only!"""
    # select one set to test for:
    binary_format = ik.tektronix.TekDPO70000.BinaryFormat.int  # go w/ values
    byte_order = ik.tektronix.TekDPO70000.ByteOrder.big_endian
    n_bytes = 4
    # get the dtype
    dtype_set = ik.tektronix.TekDPO70000._dtype(binary_format, byte_order, n_bytes=None)

    # pack the values
    values_packed = b"".join(struct.pack(dtype_set, value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    # scale the values
    scale = 1.0
    position = 0.0
    offset = 0.0
    scaled_values = [
        scale
        * ((ik.tektronix.TekDPO70000.VERT_DIVS / 2) * float(v) / (2 ** 15) - position)
        + offset
        for v in values
    ]
    if numpy:
        values = numpy.array(values)
        scaled_values = (
            scale
            * (
                (ik.tektronix.TekDPO70000.VERT_DIVS / 2)
                * values.astype(float)
                / (2 ** 15)
                - position
            )
            + offset
        )

    # run through the instrument
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            "DAT:SOU?",  # query data source
            "DAT:ENC FAS",  # fastest encoding
            "WFMO:BYT_N?",  # get n_bytes
            "WFMO:BN_F?",  # outgoing binary format
            "WFMO:BYT_O?",  # outgoing byte order
            "CURV?",  # query data
            f"CH{channel + 1}:SCALE?",  # scale raw data
            f"CH{channel + 1}:POS?",
            f"CH{channel + 1}:OFFS?",
        ],
        [
            f"CH{channel+1}",
            f"{n_bytes}",
            f"{binary_format.value}",
            f"{byte_order.value}",
            b"#" + values_len_of_len + values_len + values_packed,
            f"{scale}",
            f"{position}",
            f"{offset}",
        ],
    ) as inst:
        # query waveform
        actual_waveform = inst.channel[channel].read_waveform()
        expected_waveform = tuple(v * u.V for v in scaled_values)
        if numpy:
            expected_waveform = scaled_values * u.V
        iterable_eq(actual_waveform, expected_waveform)


def test_data_source_read_waveform_with_old_data_source():
    """Read waveform from data, old data source present!"""
    channel = 0  # multiple channels already tested above
    # select one set to test for:
    binary_format = ik.tektronix.TekDPO70000.BinaryFormat.int  # go w/ values
    byte_order = ik.tektronix.TekDPO70000.ByteOrder.big_endian
    n_bytes = 4
    # get the dtype
    dtype_set = ik.tektronix.TekDPO70000._dtype(binary_format, byte_order, n_bytes=None)

    # pack the values
    values = range(10)
    if numpy:
        values = numpy.arange(10)
    values_packed = b"".join(struct.pack(dtype_set, value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    # scale the values
    scale = 1.0
    position = 0.0
    offset = 0.0
    scaled_values = [
        scale
        * ((ik.tektronix.TekDPO70000.VERT_DIVS / 2) * float(v) / (2 ** 15) - position)
        + offset
        for v in values
    ]
    if numpy:
        scaled_values = (
            scale
            * (
                (ik.tektronix.TekDPO70000.VERT_DIVS / 2)
                * values.astype(float)
                / (2 ** 15)
                - position
            )
            + offset
        )

    # old data source to set manually - ensure it is set back later
    old_dsrc = "MATH1"

    # run through the instrument
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            "DAT:SOU?",  # query data source
            f"DAT:SOU CH{channel + 1}",  # set current data source
            "DAT:ENC FAS",  # fastest encoding
            "WFMO:BYT_N?",  # get n_bytes
            "WFMO:BN_F?",  # outgoing binary format
            "WFMO:BYT_O?",  # outgoing byte order
            "CURV?",  # query data
            f"CH{channel + 1}:SCALE?",  # scale raw data
            f"CH{channel + 1}:POS?",
            f"CH{channel + 1}:OFFS?",
            f"DAT:SOU {old_dsrc}",
        ],
        [
            old_dsrc,
            f"{n_bytes}",
            f"{binary_format.value}",
            f"{byte_order.value}",
            b"#" + values_len_of_len + values_len + values_packed,
            f"{scale}",
            f"{position}",
            f"{offset}",
        ],
    ) as inst:
        # query waveform
        actual_waveform = inst.channel[channel].read_waveform()
        expected_waveform = tuple(v * u.V for v in scaled_values)
        if numpy:
            expected_waveform = scaled_values * u.V
        iterable_eq(actual_waveform, expected_waveform)


# MATH #


@pytest.mark.parametrize("math", [it for it in range(4)])
def test_math_init(math):
    """Initialize a math channel."""
    with expected_protocol(ik.tektronix.TekDPO70000, [], []) as inst:
        assert inst.math[math]._parent is inst
        assert inst.math[math]._idx == math + 1


@pytest.mark.parametrize("math", [it for it in range(4)])
def test_math_sendcmd(math):
    """Send a command from a math channel."""
    cmd = "TEST"
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"MATH{math+1}:{cmd}"], []
    ) as inst:
        inst.math[math].sendcmd(cmd)


@pytest.mark.parametrize("math", [it for it in range(4)])
def test_math_query(math):
    """Query from a math channel."""
    cmd = "TEST"
    answ = "ANSWER"
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"MATH{math+1}:{cmd}"], [answ]
    ) as inst:
        assert inst.math[math].query(cmd) == answ


@given(
    value=st.text(
        alphabet=st.characters(blacklist_characters="\n", blacklist_categories=("Cs",))
    )
)
def test_math_define(value):
    """Get / set a string operation from the Math mode."""
    math = 0
    cmd = "DEF"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f'MATH{math+1}:{cmd} "{value}"', f"MATH{math+1}:{cmd}?"],
        [f'"{value}"'],
    ) as inst:
        inst.math[math].define = value
        assert inst.math[math].define == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.Math.FilterMode)
def test_math_filter_mode(value):
    """Get / set filter mode."""
    math = 0
    cmd = "FILT:MOD"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value.value}", f"MATH{math + 1}:{cmd}?"],
        [f"{value.value}"],
    ) as inst:
        inst.math[math].filter_mode = value
        assert inst.math[math].filter_mode == value


@given(value=st.floats(min_value=0))
def test_math_filter_risetime(value):
    """Get / set filter risetime."""
    math = 0
    cmd = "FILT:RIS"
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].filter_risetime = value
        inst.math[math].filter_risetime = value_unitful
        unit_eq(inst.math[math].filter_risetime, value_unitful)


@given(
    value=st.text(
        alphabet=st.characters(blacklist_characters="\n", blacklist_categories=("Cs",))
    )
)
def test_math_label(value):
    """Get / set a label for the math channel."""
    math = 0
    cmd = "LAB:NAM"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f'MATH{math+1}:{cmd} "{value}"', f"MATH{math+1}:{cmd}?"],
        [f'"{value}"'],
    ) as inst:
        inst.math[math].label = value
        assert inst.math[math].label == value


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.HOR_DIVS,
        max_value=ik.tektronix.TekDPO70000.HOR_DIVS,
    )
)
def test_math_label_xpos(value):
    """Get / set x position for label."""
    math = 0
    cmd = "LAB:XPOS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].label_xpos = value
        assert inst.math[math].label_xpos == value


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.VERT_DIVS,
        max_value=ik.tektronix.TekDPO70000.VERT_DIVS,
    )
)
def test_math_label_ypos(value):
    """Get / set y position for label."""
    math = 0
    cmd = "LAB:YPOS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].label_ypos = value
        assert inst.math[math].label_ypos == value


@given(value=st.integers(min_value=0))
def test_math_num_avg(value):
    """Get / set number of averages."""
    math = 0
    cmd = "NUMAV"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].num_avg = value
        assert inst.math[math].num_avg == pytest.approx(value)


@given(value=st.floats(min_value=0))
def test_math_spectral_center(value):
    """Get / set spectral center."""
    math = 0
    cmd = "SPEC:CENTER"
    value_unitful = u.Quantity(value, u.Hz)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_center = value
        inst.math[math].spectral_center = value_unitful
        unit_eq(inst.math[math].spectral_center, value_unitful)


@given(value=st.floats(allow_nan=False))
def test_math_spectral_gatepos(value):
    """Get / set gate position."""
    math = 0
    cmd = "SPEC:GATEPOS"
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_gatepos = value
        inst.math[math].spectral_gatepos = value_unitful
        unit_eq(inst.math[math].spectral_gatepos, value_unitful)


@given(value=st.floats(allow_nan=False))
def test_math_spectral_gatewidth(value):
    """Get / set gate width."""
    math = 0
    cmd = "SPEC:GATEWIDTH"
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_gatewidth = value
        inst.math[math].spectral_gatewidth = value_unitful
        unit_eq(inst.math[math].spectral_gatewidth, value_unitful)


@pytest.mark.parametrize("value", [True, False])
def test_math_spectral_lock(value):
    """Get / set spectral lock."""
    math = 0
    cmd = "SPEC:LOCK"
    value_io = "ON" if value else "OFF"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value_io}", f"MATH{math + 1}:{cmd}?"],
        [f"{value_io}"],
    ) as inst:
        inst.math[math].spectral_lock = value
        assert inst.math[math].spectral_lock == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.Math.Mag)
def test_math_spectral_mag(value):
    """Get / set spectral magnitude scaling."""
    math = 0
    cmd = "SPEC:MAG"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value.value}", f"MATH{math + 1}:{cmd}?"],
        [f"{value.value}"],
    ) as inst:
        inst.math[math].spectral_mag = value
        assert inst.math[math].spectral_mag == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.Math.Phase)
def test_math_spectral_phase(value):
    """Get / set spectral phase unit."""
    math = 0
    cmd = "SPEC:PHASE"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value.value}", f"MATH{math + 1}:{cmd}?"],
        [f"{value.value}"],
    ) as inst:
        inst.math[math].spectral_phase = value
        assert inst.math[math].spectral_phase == value


@given(value=st.floats(allow_nan=False))
def test_math_spectral_reflevel(value):
    """Get / set spectral reference level."""
    math = 0
    cmd = "SPEC:REFL"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_reflevel = value
        assert inst.math[math].spectral_reflevel == value


@given(value=st.floats(allow_nan=False))
def test_math_spectral_reflevel_offset(value):
    """Get / set spectral reference level offset."""
    math = 0
    cmd = "SPEC:REFLEVELO"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_reflevel_offset = value
        assert inst.math[math].spectral_reflevel_offset == value


@given(value=st.floats(min_value=0))
def test_math_spectral_resolution_bandwidth(value):
    """Get / set spectral resolution bandwidth."""
    math = 0
    cmd = "SPEC:RESB"
    value_unitful = u.Quantity(value, u.Hz)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_resolution_bandwidth = value
        inst.math[math].spectral_resolution_bandwidth = value_unitful
        unit_eq(inst.math[math].spectral_resolution_bandwidth, value_unitful)


@given(value=st.floats(min_value=0))
def test_math_spectral_span(value):
    """Get / set frequency span of output data vector."""
    math = 0
    cmd = "SPEC:SPAN"
    value_unitful = u.Quantity(value, u.Hz)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_span = value
        inst.math[math].spectral_span = value_unitful
        unit_eq(inst.math[math].spectral_span, value_unitful)


@given(value=st.floats(allow_nan=False))
def test_math_spectral_suppress(value):
    """Get / set spectral suppression value."""
    math = 0
    cmd = "SPEC:SUPP"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].spectral_suppress = value
        assert inst.math[math].spectral_suppress == value


@pytest.mark.parametrize("value", [True, False])
def test_math_spectral_unwrap(value):
    """Get / set phase wrapping."""
    math = 0
    cmd = "SPEC:UNWR"
    value_io = "ON" if value else "OFF"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value_io}", f"MATH{math + 1}:{cmd}?"],
        [f"{value_io}"],
    ) as inst:
        inst.math[math].spectral_unwrap = value
        assert inst.math[math].spectral_unwrap == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.Math.SpectralWindow)
def test_math_spectral_window(value):
    """Get / set spectral window."""
    math = 0
    cmd = "SPEC:WIN"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value.value}", f"MATH{math + 1}:{cmd}?"],
        [f"{value.value}"],
    ) as inst:
        inst.math[math].spectral_window = value
        assert inst.math[math].spectral_window == value


@given(value=st.floats(min_value=0))
def test_math_threshold(value):
    """Get / set threshold of math channel."""
    math = 0
    cmd = "THRESH"
    value_unitful = u.Quantity(value, u.V)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].threshhold = value
        inst.math[math].threshhold = value_unitful
        unit_eq(inst.math[math].threshhold, value_unitful)


@given(
    value=st.text(
        alphabet=st.characters(blacklist_characters="\n", blacklist_categories=("Cs",))
    )
)
def test_math_units(value):
    """Get / set a label for the units."""
    math = 0
    cmd = "UNITS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f'MATH{math+1}:{cmd} "{value}"', f"MATH{math+1}:{cmd}?"],
        [f'"{value}"'],
    ) as inst:
        inst.math[math].unit_string = value
        assert inst.math[math].unit_string == value


@pytest.mark.parametrize("value", [True, False])
def test_math_autoscale(value):
    """Get / set if autoscale is enabled."""
    math = 0
    cmd = "VERT:AUTOSC"
    value_io = "ON" if value else "OFF"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value_io}", f"MATH{math + 1}:{cmd}?"],
        [f"{value_io}"],
    ) as inst:
        inst.math[math].autoscale = value
        assert inst.math[math].autoscale == value


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.VERT_DIVS / 2,
        max_value=ik.tektronix.TekDPO70000.VERT_DIVS / 2,
    )
)
def test_math_position(value):
    """Get / set spectral vertical position from center."""
    math = 0
    cmd = "VERT:POS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:{cmd} {value:e}", f"MATH{math + 1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.math[math].position = value
        assert inst.math[math].position == value


@given(value=st.floats(min_value=0))
def test_math_scale(value):
    """Get / set scale in volts per division."""
    math = 0
    cmd = "VERT:SCALE"
    value_unitful = u.Quantity(value, u.V)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd} {value:e}",
            f"MATH{math + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.math[math].scale = value
        inst.math[math].scale = value_unitful
        unit_eq(inst.math[math].scale, value_unitful)


@given(
    values=st.lists(st.floats(min_value=-2147483648, max_value=2147483647), min_size=1)
)
def test_math_scale_raw_data(values):
    """Return scaled raw data according to current settings."""
    math = 0
    scale = 1.0 * u.V
    position = -2.3
    expected_value = tuple(
        scale
        * ((ik.tektronix.TekDPO70000.VERT_DIVS / 2) * float(v) / (2 ** 15) - position)
        for v in values
    )
    if numpy:
        values = numpy.array(values)
        expected_value = scale * (
            (ik.tektronix.TekDPO70000.VERT_DIVS / 2) * values.astype(float) / (2 ** 15)
            - position
        )

    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"MATH{math + 1}:VERT:SCALE?", f"MATH{math + 1}:VERT:POS?"],
        [f"{scale}", f"{position}"],
    ) as inst:
        iterable_eq(inst.math[math]._scale_raw_data(values), expected_value)


# CHANNEL #


@pytest.mark.parametrize("channel", [it for it in range(4)])
def test_channel_init(channel):
    """Initialize a channel."""
    with expected_protocol(ik.tektronix.TekDPO70000, [], []) as inst:
        assert inst.channel[channel]._parent is inst
        assert inst.channel[channel]._idx == channel + 1


@pytest.mark.parametrize("channel", [it for it in range(4)])
def test_channel_sendcmd(channel):
    """Send a command from a channel."""
    cmd = "TEST"
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"CH{channel+1}:{cmd}"], []
    ) as inst:
        inst.channel[channel].sendcmd(cmd)


@pytest.mark.parametrize("channel", [it for it in range(4)])
def test_channel_query(channel):
    """Send a query from a channel."""
    cmd = "TEST"
    answ = "ANSWER"
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"CH{channel+1}:{cmd}"], [answ]
    ) as inst:
        assert inst.channel[channel].query(cmd) == answ


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.Channel.Coupling)
def test_channel_coupling(value):
    """Get / set channel coupling."""
    channel = 0
    cmd = "COUP"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"CH{channel+1}:{cmd} {value.value}", f"CH{channel+1}:{cmd}?"],
        [f"{value.value}"],
    ) as inst:
        inst.channel[channel].coupling = value
        assert inst.channel[channel].coupling == value


@given(value=st.floats(min_value=0, max_value=30e9))
def test_channel_bandwidth(value):
    """Get / set bandwidth of a channel.

    Test unitful and unitless setting.
    """
    channel = 0
    cmd = "BAN"
    value_unitful = u.Quantity(value, u.Hz)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].bandwidth = value
        inst.channel[channel].bandwidth = value_unitful
        unit_eq(inst.channel[channel].bandwidth, value_unitful)


@given(value=st.floats(min_value=-25e-9, max_value=25e-9))
def test_channel_deskew(value):
    """Get / set deskew time.

    Test unitful and unitless setting.
    """
    channel = 0
    cmd = "DESK"
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].deskew = value
        inst.channel[channel].deskew = value_unitful
        unit_eq(inst.channel[channel].deskew, value_unitful)


@pytest.mark.parametrize("value", [50, 1000000])
def test_channel_termination(value):
    """Get / set termination of channel.

    Valid values are 50 Ohm or 1 MOhm. Try setting unitful and
    unitless.
    """
    channel = 0
    cmd = "TERM"
    value_unitful = u.Quantity(value, u.ohm)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].termination = value
        inst.channel[channel].termination = value_unitful
        unit_eq(inst.channel[channel].termination, value_unitful)


@given(
    value=st.text(
        alphabet=st.characters(blacklist_characters="\n", blacklist_categories=("Cs",))
    )
)
def test_channel_label(value):
    """Get / set human readable label for channel."""
    channel = 0
    cmd = "LAB:NAM"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f'CH{channel+1}:{cmd} "{value}"', f"CH{channel+1}:{cmd}?"],
        [f'"{value}"'],
    ) as inst:
        inst.channel[channel].label = value
        assert inst.channel[channel].label == value


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.HOR_DIVS,
        max_value=ik.tektronix.TekDPO70000.HOR_DIVS,
    )
)
def test_channel_label_xpos(value):
    """Get / set x position for label."""
    channel = 0
    cmd = "LAB:XPOS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"CH{channel+1}:{cmd} {value:e}", f"CH{channel+1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].label_xpos = value
        assert inst.channel[channel].label_xpos == value


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.VERT_DIVS,
        max_value=ik.tektronix.TekDPO70000.VERT_DIVS,
    )
)
def test_channel_label_ypos(value):
    """Get / set y position for label."""
    channel = 0
    cmd = "LAB:YPOS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"CH{channel+1}:{cmd} {value:e}", f"CH{channel+1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].label_ypos = value
        assert inst.channel[channel].label_ypos == value


@given(value=st.floats(allow_nan=False))
def test_channel_offset(value):
    """Get / set offset, unitful in V and unitless."""
    channel = 0
    cmd = "OFFS"
    value_unitful = u.Quantity(value, u.V)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].offset = value
        inst.channel[channel].offset = value_unitful
        unit_eq(inst.channel[channel].offset, value_unitful)


@given(
    value=st.floats(
        min_value=-ik.tektronix.TekDPO70000.VERT_DIVS,
        max_value=ik.tektronix.TekDPO70000.VERT_DIVS,
    )
)
def test_channel_position(value):
    """Get / set vertical position."""
    channel = 0
    cmd = "POS"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"CH{channel+1}:{cmd} {value:e}", f"CH{channel+1}:{cmd}?"],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].position = value
        assert inst.channel[channel].position == value


@given(value=st.floats(min_value=0))
def test_channel_scale(value):
    """Get / set scale."""
    channel = 0
    cmd = "SCALE"
    value_unitful = u.Quantity(value, u.V)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd} {value:e}",
            f"CH{channel + 1}:{cmd}?",
        ],
        [f"{value}"],
    ) as inst:
        inst.channel[channel].scale = value
        inst.channel[channel].scale = value_unitful
        unit_eq(inst.channel[channel].scale, value_unitful)


@given(
    values=st.lists(st.floats(min_value=-2147483648, max_value=2147483647), min_size=1)
)
def test_channel_scale_raw_data(values):
    """Return scaled raw data according to current settings."""
    channel = 0
    scale = u.Quantity(1.0, u.V)
    position = -1.0
    offset = u.Quantity(0.0, u.V)
    expected_value = tuple(
        scale
        * ((ik.tektronix.TekDPO70000.VERT_DIVS / 2) * float(v) / (2 ** 15) - position)
        for v in values
    )
    if numpy:
        values = numpy.array(values)
        expected_value = (
            scale
            * (
                (ik.tektronix.TekDPO70000.VERT_DIVS / 2)
                * values.astype(float)
                / (2 ** 15)
                - position
            )
            + offset
        )
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"CH{channel + 1}:SCALE?", f"CH{channel + 1}:POS?", f"CH{channel + 1}:OFFS?"],
        [f"{scale}", f"{position}", f"{offset}"],
    ) as inst:
        actual_data = inst.channel[channel]._scale_raw_data(values)
        iterable_eq(actual_data, expected_value)


# INSTRUMENT #


@pytest.mark.parametrize("value", ["AUTO", "OFF"])
def test_acquire_enhanced_enob(value):
    """Get / set enhanced effective number of bits."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:ENHANCEDE {value}", "ACQ:ENHANCEDE?"],
        [f"{value}"],
    ) as inst:
        inst.acquire_enhanced_enob = value
        assert inst.acquire_enhanced_enob == value


@pytest.mark.parametrize("value", [True, False])
def test_acquire_enhanced_state(value):
    """Get / set state of enhanced effective number of bits."""
    value_io = "1" if value else "0"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:ENHANCEDE:STATE {value_io}", "ACQ:ENHANCEDE:STATE?"],
        [f"{value_io}"],
    ) as inst:
        inst.acquire_enhanced_state = value
        assert inst.acquire_enhanced_state == value


@pytest.mark.parametrize("value", ["AUTO", "ON", "OFF"])
def test_acquire_interp_8bit(value):
    """Get / set interpolation method of instrument."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"ACQ:INTERPE {value}", "ACQ:INTERPE?"], [f"{value}"]
    ) as inst:
        inst.acquire_interp_8bit = value
        assert inst.acquire_interp_8bit == value


@pytest.mark.parametrize("value", [True, False])
def test_acquire_magnivu(value):
    """Get / set MagniVu feature."""
    value_io = "ON" if value else "OFF"
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"ACQ:MAG {value_io}", "ACQ:MAG?"], [f"{value_io}"]
    ) as inst:
        inst.acquire_magnivu = value
        assert inst.acquire_magnivu == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.AcquisitionMode)
def test_acquire_mode(value):
    """Get / set acquisition mode."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:MOD {value.value}", "ACQ:MOD?"],
        [f"{value.value}"],
    ) as inst:
        inst.acquire_mode = value
        assert inst.acquire_mode == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.AcquisitionMode)
def test_acquire_mode_actual(value):
    """Get actually used acquisition mode (query only)."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["ACQ:MOD:ACT?"], [f"{value.value}"]
    ) as inst:
        assert inst.acquire_mode_actual == value


@given(value=st.integers(min_value=0, max_value=2 ** 30 - 1))
def test_acquire_num_acquisitions(value):
    """Get number of waveform acquisitions since start (query only)."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["ACQ:NUMAC?"], [f"{value}"]
    ) as inst:
        assert inst.acquire_num_acquisitions == value


@given(value=st.integers(min_value=0))
def test_acquire_num_avgs(value):
    """Get / set number of waveform acquisitions to average."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"ACQ:NUMAV {value}", "ACQ:NUMAV?"], [f"{value}"]
    ) as inst:
        inst.acquire_num_avgs = value
        assert inst.acquire_num_avgs == value


@given(value=st.integers(min_value=0))
def test_acquire_num_envelop(value):
    """Get / set number of waveform acquisitions to envelope."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"ACQ:NUME {value}", "ACQ:NUME?"], [f"{value}"]
    ) as inst:
        inst.acquire_num_envelop = value
        assert inst.acquire_num_envelop == value


@given(value=st.integers(min_value=0))
def test_acquire_num_frames(value):
    """Get / set number of frames in FastFrame Single Sequence mode.

    Query only.
    """
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["ACQ:NUMFRAMESACQ?"], [f"{value}"]
    ) as inst:
        assert inst.acquire_num_frames == value


@given(value=st.integers(min_value=5000, max_value=2147400000))
def test_acquire_num_samples(value):
    """Get / set number of acquired samples to make up waveform database."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"ACQ:NUMSAM {value}", "ACQ:NUMSAM?"], [f"{value}"]
    ) as inst:
        inst.acquire_num_samples = value
        assert inst.acquire_num_samples == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.SamplingMode)
def test_acquire_sampling_mode(value):
    """Get / set sampling mode."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:SAMP {value.value}", "ACQ:SAMP?"],
        [f"{value.value}"],
    ) as inst:
        inst.acquire_sampling_mode = value
        assert inst.acquire_sampling_mode == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.AcquisitionState)
def test_acquire_state(value):
    """Get / set acquisition state."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:STATE {value.value}", "ACQ:STATE?"],
        [f"{value.value}"],
    ) as inst:
        inst.acquire_state = value
        assert inst.acquire_state == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.StopAfter)
def test_acquire_stop_after(value):
    """Get / set whether acquisition is continuous."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"ACQ:STOPA {value.value}", "ACQ:STOPA?"],
        [f"{value.value}"],
    ) as inst:
        inst.acquire_stop_after = value
        assert inst.acquire_stop_after == value


@given(value=st.integers(min_value=0))
def test_data_framestart(value):
    """Get / set start frame for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"DAT:FRAMESTAR {value}", "DAT:FRAMESTAR?"],
        [f"{value}"],
    ) as inst:
        inst.data_framestart = value
        assert inst.data_framestart == value


@given(value=st.integers(min_value=0))
def test_data_framestop(value):
    """Get / set stop frame for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"DAT:FRAMESTOP {value}", "DAT:FRAMESTOP?"],
        [f"{value}"],
    ) as inst:
        inst.data_framestop = value
        assert inst.data_framestop == value


@given(value=st.integers(min_value=0))
def test_data_start(value):
    """Get / set start data point for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"DAT:STAR {value}", "DAT:STAR?"], [f"{value}"]
    ) as inst:
        inst.data_start = value
        assert inst.data_start == value


@given(value=st.integers(min_value=0))
def test_data_stop(value):
    """Get / set stop data point for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"DAT:STOP {value}", "DAT:STOP?"], [f"{value}"]
    ) as inst:
        inst.data_stop = value
        assert inst.data_stop == value


@pytest.mark.parametrize("value", [True, False])
def test_data_sync_sources(value):
    """Get / set if data sync sources are on or off."""
    value_io = "ON" if value else "OFF"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"DAT:SYNCSOU {value_io}", "DAT:SYNCSOU?"],
        [f"{value_io}"],
    ) as inst:
        inst.data_sync_sources = value
        assert inst.data_sync_sources == value


valid_channel_range = [it for it in range(4)]


@pytest.mark.parametrize("no", valid_channel_range)
def test_data_source_channel(no):
    """Get / set channel as data source."""
    channel_name = f"CH{no + 1}"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"DAT:SOU {channel_name}", f"DAT:SOU?"],
        [channel_name],
    ) as inst:
        channel = inst.channel[no]
        inst.data_source = channel
        assert inst.data_source == channel


valid_math_range = [it for it in range(4)]


@pytest.mark.parametrize("no", valid_math_range)
def test_data_source_math(no, mocker):
    """Get / set math as data source."""
    math_name = f"MATH{no + 1}"

    # patch call to time.sleep with mock
    mock_time = mocker.patch.object(time, "sleep", return_value=None)

    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"DAT:SOU {math_name}", f"DAT:SOU?"], [math_name]
    ) as inst:
        math = inst.math[no]
        inst.data_source = math
        assert inst.data_source == math

        # assert that time.sleep has been called
        mock_time.assert_called()


def test_data_source_ref_not_implemented_error():
    """Get / set a reference channel raises a NotImplemented error."""
    ref_name = "REF1"  # example, range not important
    with expected_protocol(ik.tektronix.TekDPO70000, [f"DAT:SOU?"], [ref_name]) as inst:
        # getter
        with pytest.raises(NotImplementedError):
            print(inst.data_source)
        # setter
        with pytest.raises(NotImplementedError):
            inst.data_source = inst.ref[0]


def test_data_source_not_implemented_error():
    """Get a data source that is currently not implemented."""
    ds_name = "HHG29"  # example, range not important
    with expected_protocol(ik.tektronix.TekDPO70000, [f"DAT:SOU?"], [ds_name]) as inst:
        with pytest.raises(NotImplementedError):
            print(inst.data_source)


def test_data_source_invalid_type():
    """Raise TypeError when a wrong type is set for data source."""
    invalid_data_source = 42
    with expected_protocol(ik.tektronix.TekDPO70000, [], []) as inst:
        with pytest.raises(TypeError) as exc_info:
            inst.data_source = invalid_data_source
        exc_msg = exc_info.value.args[0]
        assert exc_msg == f"{type(invalid_data_source)} is not a valid data " f"source."


@given(value=st.floats(min_value=0, max_value=1000))
def test_horiz_acq_duration(value):
    """Get horizontal acquisition duration (query only)."""
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["HOR:ACQDURATION?"], [f"{value}"]
    ) as inst:
        unit_eq(inst.horiz_acq_duration, value_unitful)


@given(value=st.integers(min_value=0))
def test_horiz_acq_length(value):
    """Get horizontal acquisition length (query only)."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["HOR:ACQLENGTH?"], [f"{value}"]
    ) as inst:
        assert inst.horiz_acq_length == value


@pytest.mark.parametrize("value", [True, False])
def test_horiz_delay_mode(value):
    """Get / set state of horizontal delay mode."""
    value_io = "1" if value else "0"
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:DEL:MOD {value_io}", "HOR:DEL:MOD?"],
        [f"{value_io}"],
    ) as inst:
        inst.horiz_delay_mode = value
        assert inst.horiz_delay_mode == value


@given(value=st.floats(min_value=0, max_value=100))
def test_horiz_delay_pos(value):
    """Get / set horizontal time base if delay mode is on.

    Test setting unitful and without units."""
    value_unitful = u.Quantity(value, u.percent)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:DEL:POS {value:e}", f"HOR:DEL:POS {value:e}", "HOR:DEL:POS?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_delay_pos = value
        inst.horiz_delay_pos = value_unitful
        unit_eq(inst.horiz_delay_pos, value_unitful)


@given(value=st.floats(min_value=0))
def test_horiz_delay_time(value):
    """Get / set horizontal delay time."""
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:DEL:TIM {value:e}", f"HOR:DEL:TIM {value:e}", "HOR:DEL:TIM?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_delay_time = value
        inst.horiz_delay_time = value_unitful
        unit_eq(inst.horiz_delay_time, value_unitful)


@given(value=st.floats(min_value=0))
def test_horiz_interp_ratio(value):
    """Get horizontal interpolation ratio (query only)."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, ["HOR:MAI:INTERPR?"], [f"{value}"]
    ) as inst:
        assert inst.horiz_interp_ratio == value


@given(value=st.floats(min_value=0))
def test_horiz_main_pos(value):
    """Get / set horizontal main position.

    Test setting unitful and without units."""
    value_unitful = u.Quantity(value, u.percent)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:MAI:POS {value:e}", f"HOR:MAI:POS {value:e}", "HOR:MAI:POS?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_main_pos = value
        inst.horiz_main_pos = value_unitful
        unit_eq(inst.horiz_main_pos, value_unitful)


def test_horiz_unit():
    """Get / set horizontal unit string."""
    unit_string = "LUM"  # as example in manual
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f'HOR:MAI:UNI "{unit_string}"', "HOR:MAI:UNI?"],
        [f'"{unit_string}"'],
    ) as inst:
        inst.horiz_unit = unit_string
        assert inst.horiz_unit == unit_string


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.HorizontalMode)
def test_horiz_mode(value):
    """Get / set horizontal mode."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:MODE {value.value}", "HOR:MODE?"],
        [f"{value.value}"],
    ) as inst:
        inst.horiz_mode = value
        assert inst.horiz_mode == value


@given(value=st.integers(min_value=0))
def test_horiz_record_length_lim(value):
    """Get / set horizontal record length limit."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:MODE:AUTO:LIMIT {value}", "HOR:MODE:AUTO:LIMIT?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_record_length_lim = value
        assert inst.horiz_record_length_lim == value


@given(value=st.integers(min_value=0))
def test_horiz_record_length(value):
    """Get / set horizontal record length."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:MODE:RECO {value}", "HOR:MODE:RECO?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_record_length = value
        assert inst.horiz_record_length == value


@given(value=st.floats(min_value=0, max_value=30e9))
def test_horiz_sample_rate(value):
    """Get / set horizontal sampling rate.

    Set with and without units."""
    value_unitful = u.Quantity(value, u.Hz)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [
            f"HOR:MODE:SAMPLER {value:e}",
            f"HOR:MODE:SAMPLER {value:e}",
            f"HOR:MODE:SAMPLER?",
        ],
        [f"{value}"],
    ) as inst:
        inst.horiz_sample_rate = value_unitful
        inst.horiz_sample_rate = value
        unit_eq(inst.horiz_sample_rate, value_unitful)


@given(value=st.floats(min_value=0))
def test_horiz_scale(value):
    """Get / set horizontal scale in seconds per division.

    Set with and without units."""
    value_unitful = u.Quantity(value, u.s)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:MODE:SCA {value:e}", f"HOR:MODE:SCA {value:e}", f"HOR:MODE:SCA?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_scale = value_unitful
        inst.horiz_scale = value
        unit_eq(inst.horiz_scale, value_unitful)


@given(value=st.floats(min_value=0))
def test_horiz_pos(value):
    """Get / set position of trigger point on the screen.

    Set with and without units.
    """
    value_unitful = u.Quantity(value, u.percent)
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"HOR:POS {value:e}", f"HOR:POS {value:e}", f"HOR:POS?"],
        [f"{value}"],
    ) as inst:
        inst.horiz_pos = value_unitful
        inst.horiz_pos = value
        unit_eq(inst.horiz_pos, value_unitful)


@pytest.mark.parametrize("value", ["AUTO", "OFF", "ON"])
def test_horiz_roll(value):
    """Get / set roll mode status."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"HOR:ROLL {value}", f"HOR:ROLL?"], [f"{value}"]
    ) as inst:
        inst.horiz_roll = value
        assert inst.horiz_roll == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.TriggerState)
def test_trigger_state(value):
    """Get / set the trigger state."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"TRIG:STATE {value.value}", "TRIG:STATE?"],
        [f"{value.value}"],
    ) as inst:
        inst.trigger_state = value
        assert inst.trigger_state == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.WaveformEncoding)
def test_outgoing_waveform_encoding(value):
    """Get / set the encoding used for outgoing waveforms."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"WFMO:ENC {value.value}", "WFMO:ENC?"],
        [f"{value.value}"],
    ) as inst:
        inst.outgoing_waveform_encoding = value
        assert inst.outgoing_waveform_encoding == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.BinaryFormat)
def test_outgoing_byte_format(value):
    """Get / set the binary format for outgoing waveforms."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"WFMO:BN_F {value.value}", "WFMO:BN_F?"],
        [f"{value.value}"],
    ) as inst:
        inst.outgoing_binary_format = value
        assert inst.outgoing_binary_format == value


@pytest.mark.parametrize("value", ik.tektronix.TekDPO70000.ByteOrder)
def test_outgoing_byte_order(value):
    """Get / set the binary data endianness for outgoing waveforms."""
    with expected_protocol(
        ik.tektronix.TekDPO70000,
        [f"WFMO:BYT_O {value.value}", "WFMO:BYT_O?"],
        [f"{value.value}"],
    ) as inst:
        inst.outgoing_byte_order = value
        assert inst.outgoing_byte_order == value


@pytest.mark.parametrize("value", (1, 2, 4, 8))
def test_outgoing_n_bytes(value):
    """Get / set the number of bytes sampled in waveforms binary encoding."""
    with expected_protocol(
        ik.tektronix.TekDPO70000, [f"WFMO:BYT_N {value}", "WFMO:BYT_N?"], [f"{value}"]
    ) as inst:
        inst.outgoing_n_bytes = value
        assert inst.outgoing_n_bytes == value


# METHODS #


def test_select_fastest_encoding():
    """Sets encoding to fastest methods."""
    with expected_protocol(ik.tektronix.TekDPO70000, ["DAT:ENC FAS"], []) as inst:
        inst.select_fastest_encoding()


def test_force_trigger():
    """Force a trivver event."""
    with expected_protocol(ik.tektronix.TekDPO70000, ["TRIG FORC"], []) as inst:
        inst.force_trigger()


def test_run():
    """Enables the trigger for the oscilloscope."""
    with expected_protocol(ik.tektronix.TekDPO70000, [":RUN"], []) as inst:
        inst.run()


def test_stop():
    """Disables the trigger for the oscilloscope."""
    with expected_protocol(ik.tektronix.TekDPO70000, [":STOP"], []) as inst:
        inst.stop()
