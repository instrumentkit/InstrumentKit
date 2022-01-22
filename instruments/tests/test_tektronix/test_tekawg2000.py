#!/usr/bin/env python
"""
Unit tests for the Tektronix AGG2000 arbitrary wave generators.
"""

# IMPORTS #####################################################################

from hypothesis import (
    given,
    strategies as st,
)
import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import expected_protocol, make_name_test
from instruments.units import ureg as u


# TESTS #######################################################################

# pylint: disable=protected-access


test_tekawg2000_name = make_name_test(ik.tektronix.TekAWG2000)


# CHANNEL #


channels_to_try = range(2)
channels_to_try_id = [f"CH{it}" for it in channels_to_try]


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
def test_channel_init(channel):
    """Channel initialization."""
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        assert inst.channel[channel]._tek is inst
        assert inst.channel[channel]._name == f"CH{channel + 1}"
        assert inst.channel[channel]._old_dsrc is None


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
def test_channel_name(channel):
    """Get the name of the channel."""
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        assert inst.channel[channel].name == f"CH{channel + 1}"


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
@given(
    val_read=st.floats(min_value=0.02, max_value=2),
    val_unitless=st.floats(min_value=0.02, max_value=2),
    val_millivolt=st.floats(min_value=0.02, max_value=2000),
)
def test_channel_amplitude(channel, val_read, val_unitless, val_millivolt):
    """Get / set amplitude."""
    val_read = u.Quantity(val_read, u.V)
    val_unitful = u.Quantity(val_millivolt, u.mV)
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [
            f"FG:CH{channel+1}:AMPL?",
            f"FG:CH{channel+1}:AMPL {val_unitless}",
            f"FG:CH{channel+1}:AMPL {val_unitful.to(u.V).magnitude}",
        ],
        [f"{val_read.magnitude}"],
    ) as inst:
        assert inst.channel[channel].amplitude == val_read
        inst.channel[channel].amplitude = val_unitless
        inst.channel[channel].amplitude = val_unitful


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
@given(
    val_read=st.floats(min_value=0.02, max_value=2),
    val_unitless=st.floats(min_value=0.02, max_value=2),
    val_millivolt=st.floats(min_value=0.02, max_value=2000),
)
def test_channel_offset(channel, val_read, val_unitless, val_millivolt):
    """Get / set offset."""
    val_read = u.Quantity(val_read, u.V)
    val_unitful = u.Quantity(val_millivolt, u.mV)
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [
            f"FG:CH{channel+1}:OFFS?",
            f"FG:CH{channel+1}:OFFS {val_unitless}",
            f"FG:CH{channel+1}:OFFS {val_unitful.to(u.V).magnitude}",
        ],
        [f"{val_read.magnitude}"],
    ) as inst:
        assert inst.channel[channel].offset == val_read
        inst.channel[channel].offset = val_unitless
        inst.channel[channel].offset = val_unitful


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
@given(
    val_read=st.floats(min_value=1, max_value=200000),
    val_unitless=st.floats(min_value=1, max_value=200000),
    val_kilohertz=st.floats(min_value=1, max_value=200),
)
def test_channel_frequency(channel, val_read, val_unitless, val_kilohertz):
    """Get / set offset."""
    val_read = u.Quantity(val_read, u.Hz)
    val_unitful = u.Quantity(val_kilohertz, u.kHz)
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [
            f"FG:FREQ?",
            f"FG:FREQ {val_unitless}HZ",
            f"FG:FREQ {val_unitful.to(u.Hz).magnitude}HZ",
        ],
        [f"{val_read.magnitude}"],
    ) as inst:
        assert inst.channel[channel].frequency == val_read
        inst.channel[channel].frequency = val_unitless
        inst.channel[channel].frequency = val_unitful


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
@given(polarity=st.sampled_from(ik.tektronix.TekAWG2000.Polarity))
def test_channel_polarity(channel, polarity):
    """Get / set polarity."""
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [f"FG:CH{channel+1}:POL?", f"FG:CH{channel+1}:POL {polarity.value}"],
        [f"{polarity.value}"],
    ) as inst:
        assert inst.channel[channel].polarity == polarity
        inst.channel[channel].polarity = polarity


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
def test_channel_polarity_type_mismatch(channel):
    """Raise a TypeError if a wrong type is selected as the polarity."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        with pytest.raises(TypeError) as exc_info:
            inst.channel[channel].polarity = wrong_type
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Polarity settings must be a `TekAWG2000.Polarity` "
            f"value, got {type(wrong_type)} instead."
        )


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
@given(shape=st.sampled_from(ik.tektronix.TekAWG2000.Shape))
def test_channel_shape(channel, shape):
    """Get / set shape."""
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [f"FG:CH{channel+1}:SHAP?", f"FG:CH{channel+1}:SHAP {shape.value}"],
        [f"{shape.value}, 0"],  # pulse duty cycle
    ) as inst:
        assert inst.channel[channel].shape == shape
        inst.channel[channel].shape = shape


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_id)
def test_channel_shape_type_mismatch(channel):
    """Raise a TypeError if a wrong type is selected as the shape."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        with pytest.raises(TypeError) as exc_info:
            inst.channel[channel].shape = wrong_type
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Shape settings must be a `TekAWG2000.Shape` "
            f"value, got {type(wrong_type)} instead."
        )


# INSTRUMENT #


def test_waveform_name():
    """Get / set the waveform name."""
    file_name = "test_file"
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        ["DATA:DEST?", f'DATA:DEST "{file_name}"'],
        [f"{file_name}"],
    ) as inst:
        assert inst.waveform_name == file_name
        inst.waveform_name = file_name


def test_waveform_name_type_mismatch():
    """Raise a TypeError when something else than a string is given."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        with pytest.raises(TypeError) as exc_info:
            inst.waveform_name = wrong_type
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Waveform name must be specified as a string."


@pytest.mark.skipif(numpy is None, reason="Numpy required for this test")
@given(
    yzero=st.floats(min_value=-5, max_value=5),
    ymult=st.floats(min_value=0.00001),
    xincr=st.floats(min_value=5e-8, max_value=1e-1),
    waveform=st.lists(st.floats(min_value=0, max_value=1), min_size=1),
)
def test_upload_waveform(yzero, ymult, xincr, waveform):
    """Upload a waveform from the PC to the instrument."""
    # prep waveform
    waveform = numpy.array(waveform)
    waveform_send = waveform * (2 ** 12 - 1)
    waveform_send = waveform_send.astype("<u2").tobytes()
    wfm_header_2 = str(len(waveform_send))
    wfm_header_1 = len(wfm_header_2)
    bin_str = f"#{wfm_header_1}{wfm_header_2}{waveform_send}"
    with expected_protocol(
        ik.tektronix.TekAWG2000,
        [
            f"WFMP:YZERO {yzero}",
            f"WFMP:YMULT {ymult}",
            f"WFMP:XINCR {xincr}",
            f"CURVE {bin_str}",
        ],
        [],
    ) as inst:
        inst.upload_waveform(yzero, ymult, xincr, waveform)


@pytest.mark.skipif(numpy is None, reason="Numpy required for this test")
@given(
    yzero=st.floats(min_value=-5, max_value=5),
    ymult=st.floats(min_value=0.00001),
    xincr=st.floats(min_value=5e-8, max_value=1e-1),
    waveform=st.lists(st.floats(min_value=0, max_value=1), min_size=1),
)
def test_upload_waveform_type_mismatch(yzero, ymult, xincr, waveform):
    """Raise type error when types for method mismatched."""
    wrong_type_yzero = "42"
    wrong_type_ymult = "42"
    wrong_type_xincr = "42"
    waveform_ndarray = numpy.array(waveform)
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        # wrong yzero type
        with pytest.raises(TypeError) as exc_info:
            inst.upload_waveform(wrong_type_yzero, ymult, xincr, waveform_ndarray)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "yzero must be specified as a float or int"
        # wrong ymult type
        with pytest.raises(TypeError) as exc_info:
            inst.upload_waveform(yzero, wrong_type_ymult, xincr, waveform_ndarray)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "ymult must be specified as a float or int"
        # wrong xincr type
        with pytest.raises(TypeError) as exc_info:
            inst.upload_waveform(yzero, ymult, wrong_type_xincr, waveform_ndarray)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "xincr must be specified as a float or int"
        # wrong waveform type
        with pytest.raises(TypeError) as exc_info:
            inst.upload_waveform(yzero, ymult, xincr, waveform)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "waveform must be specified as a numpy array"


@pytest.mark.skipif(numpy is None, reason="Numpy required for this test")
@given(
    yzero=st.floats(min_value=-5, max_value=5),
    ymult=st.floats(min_value=0.00001),
    xincr=st.floats(min_value=5e-8, max_value=1e-1),
    waveform=st.lists(st.floats(min_value=0, max_value=1), min_size=1),
)
def test_upload_waveform_wrong_max(yzero, ymult, xincr, waveform):
    """Raise ValueError when waveform maximum is too large."""
    waveform_wrong_max = numpy.array(waveform)
    waveform_wrong_max[0] = 42.0
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        with pytest.raises(ValueError) as exc_info:
            inst.upload_waveform(yzero, ymult, xincr, waveform_wrong_max)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "The max value for an element in waveform is 1."


@pytest.mark.skipif(numpy is not None, reason="Numpy missing is required for this test")
def test_upload_waveform_missing_numpy_raises_exception():
    with expected_protocol(ik.tektronix.TekAWG2000, [], []) as inst:
        with pytest.raises(ImportError):
            inst.upload_waveform(0, 0, 0, [0])
