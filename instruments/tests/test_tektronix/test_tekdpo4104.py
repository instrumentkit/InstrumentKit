#!/usr/bin/env python
"""
Tests for the Tektronix DPO 4104 oscilloscope.
"""

# IMPORTS #####################################################################

from enum import Enum
import struct

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
)


# TESTS #######################################################################

# pylint: disable=protected-access


test_tekdpo4104_name = make_name_test(ik.tektronix.TekDPO4104)


# INSTRUMENT #


def test_data_source():
    """Get / set data source for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU CH1",  # set a string
            "DAT:SOU?",
            "DAT:SOU REF2",  # set value of an enum
            "DAT:SOU?",
            "DAT:SOU MATH",  # set a math channel
            "DAT:SOU?",
        ],
        ["CH1", "REF2", "MATH"],
    ) as inst:
        # Channel as string
        inst.data_source = "CH1"
        assert inst.data_source == ik.tektronix.tekdpo4104.TekDPO4104.Channel(inst, 0)

        # Reference channel as enum
        class RefChannel(Enum):
            """Temporary reference channel enum."""

            channel = "REF2"

        channel = RefChannel.channel.value
        inst.data_source = RefChannel.channel
        assert inst.data_source == ik.tektronix.tekdpo4104.TekDPO4104.DataSource(
            inst, channel
        )

        # Set a math channel
        math_ch = inst.math
        inst.data_source = math_ch
        assert inst.data_source == ik.tektronix.tekdpo4104.TekDPO4104.DataSource(
            inst, math_ch.name
        )


h_record_lengths_possible = (1000, 10000, 100000, 1000000, 10000000)


@pytest.mark.parametrize("aqu_length", h_record_lengths_possible)
def test_aquisition_length(aqu_length):
    """Get / set acquisition length with valid values."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [f"HOR:RECO {aqu_length}", "HOR:RECO?"],
        [f"{aqu_length}"],
    ) as inst:
        inst.aquisition_length = aqu_length
        assert inst.aquisition_length == aqu_length


def test_aquisition_running():
    """Get / set status of aquisition running."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        ["ACQ:STATE?", "ACQ:STATE 0", "ACQ:STATE?", "ACQ:STATE 1"],
        ["1", "0"],
    ) as inst:
        assert inst.aquisition_running
        inst.aquisition_running = False
        assert not inst.aquisition_running
        inst.aquisition_running = True


def test_aquisition_continuous():
    """Get / set status of aquisition continuous."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        ["ACQ:STOPA?", "ACQ:STOPA SEQ", "ACQ:STOPA?", "ACQ:STOPA RUNST"],
        ["RUNST", "SEQ"],
    ) as inst:
        assert inst.aquisition_continuous
        inst.aquisition_continuous = False
        assert not inst.aquisition_continuous
        inst.aquisition_continuous = True


@pytest.mark.parametrize("data_width", (1, 2))
def test_data_width(data_width):
    """Get / set data width with valid values."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            f"DATA:WIDTH {data_width}",
            "DATA:WIDTH?",
        ],
        [f"{data_width}"],
    ) as inst:
        inst.data_width = data_width
        assert inst.data_width == data_width


def test_data_width_out_of_range():
    """Raise Value Error if input value is out of range."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        with pytest.raises(ValueError) as exc_info:
            inst.data_width = 42
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Only one or two byte-width is supported."


@given(offset=st.floats(min_value=-100, max_value=100))
def test_y_offset(offset):
    """Get / set Y offset of currently selected data source."""
    with expected_protocol(
        ik.tektronix.TekDPO4104, [f"WFMP:YOF {offset}", "WFMP:YOF?"], [f"{offset}"]
    ) as inst:
        inst.y_offset = offset
        assert inst.y_offset == offset


def test_force_trigger():
    """Force a trigger event to occur."""
    with expected_protocol(ik.tektronix.TekDPO4104, ["TRIG FORCE"], []) as inst:
        inst.force_trigger()


# CHANNELS #


channels_to_try = range(4)
channels_to_try_ids = [f"CH{it}" for it in channels_to_try]


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_ids)
def test_channel_init(channel):
    """Initialize a channel."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        assert inst.channel[channel]._idx == channel + 1


@pytest.mark.parametrize("channel", channels_to_try, ids=channels_to_try_ids)
@pytest.mark.parametrize("coupling", ik.tektronix.TekDPO4104.Coupling)
def test_channel_coupling(channel, coupling):
    """Initialize a channel."""
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [f"CH{channel + 1}:COUPL {coupling.value}", f"CH{channel + 1}:COUPL?"],
        [f"{coupling.value}"],
    ) as inst:
        inst.channel[channel].coupling = coupling
        assert inst.channel[channel].coupling == coupling


def test_channel_coupling_invalid_value():
    """Raise Type Error when trying to set coupling with wrong value."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        wrong_type = "DC"
        with pytest.raises(TypeError) as exc_info:
            inst.channel[0].coupling = wrong_type
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Coupling setting must be a `TekDPO4104.Coupling`"
            f" value, got {type(wrong_type)} instead."
        )


# DATA SOURCE #


reference_sources_to_try = range(4)
reference_sources_to_try_ids = [f"REF{it}" for it in reference_sources_to_try]


@pytest.mark.parametrize(
    "ref", reference_sources_to_try, ids=reference_sources_to_try_ids
)
def test_data_source_ref_initialize(ref):
    """Initialize a ref data source."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        ref_source = inst.ref[ref]

        # test instance
        assert isinstance(ref_source, ik.tektronix.tekdpo4104.TekDPO4104.DataSource)

        # test for parent
        assert ref_source._tek is inst


def test_data_source_math_initialize():
    """Initialize a ref data source."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        math_source = inst.math

        # test instance
        assert isinstance(math_source, ik.tektronix.tekdpo4104.TekDPO4104.DataSource)

        # test for parent
        assert math_source._tek is inst


def test_data_source_name():
    """Get the name of the data source."""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        assert inst.math.name == "MATH"


def test_data_source_equality_not_implemented():
    """Raise NotImplemented when comparing different types"""
    with expected_protocol(ik.tektronix.TekDPO4104, [], []) as inst:
        assert inst.math.__eq__(42) == NotImplemented


@given(
    values=st.lists(st.integers(min_value=-32768, max_value=32767), min_size=1),
    ymult=st.integers(min_value=1, max_value=65536),
    yzero=st.floats(min_value=-100, max_value=100),
    xzero=st.floats(min_value=-10, max_value=10),
    xincr=st.floats(min_value=1e-6, max_value=1),
)
def test_data_source_read_waveform_bin(values, ymult, yzero, xzero, xincr):
    """Read the waveform of a data trace in bin format."""
    old_dat_source = 3
    old_dat_stop = 100  # "previous" setting
    # new values
    channel = 0
    data_width = 2  # use format '>h' for decoding
    yoffs = 0  # already tested with hypothesis
    # values packing
    ptcnt = len(values)
    values_packed = b"".join(struct.pack(">h", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU?",  # old data source
            f"DAT:SOU CH{channel+1}",
            "DAT:STOP?",
            f"DAT:STOP {10**7}",
            "DAT:ENC RIB",  # set encoding
            "DATA:WIDTH?",  # query data width
            "CURVE?",  # get the data (in bin format)
            "WFMP:YOF?",  # query yoffs
            "WFMP:YMU?",  # query ymult
            "WFMP:YZE?",  # query yzero
            "WFMP:XZE?",  # query x zero
            "WFMP:XIN?",  # retrieve x increments
            "WFMP:NR_P?",  # retrieve number of points
            f"DAT:STOP {old_dat_stop}",
            f"DAT:SOU CH{old_dat_source + 1}",  # set back old data source
        ],
        [
            f"CH{old_dat_source+1}",
            f"{old_dat_stop}",
            f"{data_width}",
            b"#" + values_len_of_len + values_len + values_packed,
            f"{yoffs}",
            f"{ymult}",
            f"{yzero}",
            f"{xzero}",
            f"{xincr}",
            f"{ptcnt}",
        ],
    ) as inst:
        x_read, y_read = inst.channel[channel].read_waveform()
        if numpy:
            x_calc = numpy.arange(ptcnt) * xincr + xzero
            y_calc = ((numpy.array(values) - yoffs) * ymult) + yzero
        else:
            x_calc = tuple(float(val) * xincr + xzero for val in range(ptcnt))
            y_calc = tuple(((float(val) - yoffs) * ymult) + yzero for val in values)
        iterable_eq(x_read, x_calc)
        iterable_eq(y_read, y_calc)


@given(
    values=st.lists(st.integers(min_value=-32768, max_value=32767), min_size=1),
    ymult=st.integers(min_value=1, max_value=65536),
    yzero=st.floats(min_value=-100, max_value=100),
    xzero=st.floats(min_value=-10, max_value=10),
    xincr=st.floats(min_value=1e-9, max_value=1),
)
def test_data_source_read_waveform_ascii(values, ymult, yzero, xzero, xincr):
    """Read waveform back in ASCII format."""
    old_dat_source = 3
    old_dat_stop = 100  # "previous" setting
    # new values
    channel = 0
    yoffs = 0  # already tested with hypothesis
    # transform values to strings
    values_str = ",".join([str(value) for value in values])
    # calculated values
    ptcnt = len(values)
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU?",  # old data source
            f"DAT:SOU CH{channel + 1}",
            "DAT:STOP?",
            f"DAT:STOP {10**7}",
            "DAT:ENC ASCI",  # set encoding
            "CURVE?",  # get the data (in bin format)
            "WFMP:YOF?",
            "WFMP:YMU?",  # query y-offset
            "WFMP:YZE?",  # query y zero
            "WFMP:XZE?",  # query x zero
            "WFMP:XIN?",  # retrieve x increments
            "WFMP:NR_P?",  # retrieve number of points
            f"DAT:STOP {old_dat_stop}",
            f"DAT:SOU CH{old_dat_source + 1}",  # set back old data source
        ],
        [
            f"CH{old_dat_source + 1}",
            f"{old_dat_stop}",
            f"{values_str}",
            f"{yoffs}",
            f"{ymult}",
            f"{yzero}",
            f"{xzero}",
            f"{xincr}",
            f"{ptcnt}",
        ],
    ) as inst:
        # get the values from the instrument
        x_read, y_read = inst.channel[channel].read_waveform(bin_format=False)

        # manually calculate the values
        if numpy:
            raw = numpy.array(values_str.split(","), dtype=numpy.float)
            x_calc = numpy.arange(ptcnt) * xincr + xzero
            y_calc = (raw - yoffs) * ymult + yzero
        else:
            x_calc = tuple(float(val) * xincr + xzero for val in range(ptcnt))
            y_calc = tuple(((float(val) - yoffs) * ymult) + yzero for val in values)

        # assert arrays are equal
        iterable_eq(x_read, x_calc)
        iterable_eq(y_read, y_calc)


@given(offset=st.floats(min_value=-100, max_value=100))
def test_data_source_y_offset_get(offset):
    """Get y-offset from parent property."""
    old_dat_source = 2
    channel = 0
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU?",  # old data source
            f"DAT:SOU CH{channel + 1}",
            "WFMP:YOF?",
            f"DAT:SOU CH{old_dat_source + 1}",  # set back old data source
        ],
        [f"CH{old_dat_source + 1}", f"{offset}"],
    ) as inst:
        assert inst.channel[channel].y_offset == offset


@given(offset=st.floats(min_value=-100, max_value=100))
def test_data_source_y_offset_set(offset):
    """Set y-offset from parent property."""
    old_dat_source = 2
    channel = 0
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU?",  # old data source
            f"DAT:SOU CH{channel + 1}",
            f"WFMP:YOF {offset}",
            f"DAT:SOU CH{old_dat_source + 1}",  # set back old data source
        ],
        [
            f"CH{old_dat_source + 1}",
        ],
    ) as inst:
        inst.channel[channel].y_offset = offset


def test_data_source_y_offset_set_old_data_source_same():
    """Set y-offset from parent property, old data source same.

    Test one case of setting a data source where the old data source
    and the new one is the same. Use y_offset for this test.
    """
    offset = 0
    old_dat_source = 0
    channel = 0
    with expected_protocol(
        ik.tektronix.TekDPO4104,
        [
            "DAT:SOU?",  # old data source
            f"WFMP:YOF {offset}",
        ],
        [
            f"CH{old_dat_source + 1}",
        ],
    ) as inst:
        inst.channel[channel].y_offset = offset
