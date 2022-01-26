#!/usr/bin/env python
"""
Tests for the Tektronix TDS 5xx series oscilloscope.
"""


# IMPORTS #####################################################################


from datetime import datetime
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
)


# TESTS #######################################################################


# pylint: disable=protected-access


test_tektds5xx_name = make_name_test(ik.tektronix.TekTDS5xx)


# MEASUREMENT #


@pytest.mark.parametrize("msr", [it for it in range(3)])
def test_measurement_init(msr):
    """Initialize a new measurement."""
    meas_categories = [
        "enabled",
        "type",
        "units",
        "src1",
        "src2",
        "edge1",
        "edge2",
        "dir",
    ]
    meas_return = '0;UNDEFINED;"V",CH1,CH2,RISE,RISE,FORWARDS'
    data_expected = dict(zip(meas_categories, meas_return.split(";")))
    with expected_protocol(
        ik.tektronix.TekTDS5xx, [f"MEASU:MEAS{msr+1}?"], [meas_return]
    ) as inst:
        measurement = inst.measurement[msr]
        assert measurement._tek is inst
        assert measurement._id == msr + 1
        assert measurement._data == data_expected


@pytest.mark.parametrize("msr", [it for it in range(3)])
@given(value=st.floats(allow_nan=False))
def test_measurement_read_enabled_true(msr, value):
    """Read a new measurement value since enabled is true."""
    enabled = 1
    # initialization dictionary
    meas_categories = [
        "enabled",
        "type",
        "units",
        "src1",
        "src2",
        "edge1",
        "edge2",
        "dir",
    ]
    meas_return = f'{enabled};UNDEFINED;"V",CH1,CH2,RISE,RISE,FORWARDS'
    data_expected = dict(zip(meas_categories, meas_return.split(";")))

    # extended dictionary
    data_expected["value"] = value

    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"MEASU:MEAS{msr+1}?", f"MEASU:MEAS{msr+1}:VAL?"],
        [meas_return, f"{value}"],
    ) as inst:
        measurement = inst.measurement[msr]
        assert measurement.read() == data_expected


def test_measurement_read_enabled_false():
    """Do not read a new measurement value since enabled is false."""
    msr = 0
    enabled = 0
    # initialization dictionary
    meas_categories = [
        "enabled",
        "type",
        "units",
        "src1",
        "src2",
        "edge1",
        "edge2",
        "dir",
    ]
    meas_return = f'{enabled};UNDEFINED;"V",CH1,CH2,RISE,RISE,FORWARDS'
    data_expected = dict(zip(meas_categories, meas_return.split(";")))
    with expected_protocol(
        ik.tektronix.TekTDS5xx, [f"MEASU:MEAS{msr+1}?"], [meas_return]
    ) as inst:
        measurement = inst.measurement[msr]
        assert measurement.read() == data_expected


# DATA SOURCE #


@given(values=st.lists(st.integers(min_value=-32768, max_value=32767), min_size=1))
def test_data_source_read_waveform_binary(values):
    """Read waveform from data source as binary."""
    # constants - to not overkill it with hypothesis
    channel_no = 0
    data_width = 2
    yoffs = 1.0
    ymult = 1.0
    yzero = 0.3
    xincr = 0.001
    # make values to compare with
    ptcnt = len(values)
    values_arr = values
    if numpy:
        values_arr = numpy.array(values)
    values_packed = b"".join(struct.pack(">h", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()

    # calculations
    if numpy:
        x_calc = numpy.arange(float(ptcnt)) * xincr
        y_calc = ((values_arr - yoffs) * ymult) + yzero
    else:
        x_calc = tuple(float(val) * float(xincr) for val in range(ptcnt))
        y_calc = tuple(((val - yoffs) * float(ymult)) + float(yzero) for val in values)

    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [
            "DAT:SOU?",
            "DAT:ENC RIB",
            "DATA:WIDTH?",
            "CURVE?",
            f"WFMP:CH{channel_no+1}:YOF?",
            f"WFMP:CH{channel_no+1}:YMU?",
            f"WFMP:CH{channel_no+1}:YZE?",
            f"WFMP:CH{channel_no+1}:XIN?",
            f"WFMP:CH{channel_no+1}:NR_P?",
        ],
        [
            f"CH{channel_no+1}",
            f"{data_width}",
            b"#" + values_len_of_len + values_len + values_packed,
            f"{yoffs}",
            f"{ymult}",
            f"{yzero}",
            f"{xincr}",
            f"{ptcnt}",
        ],
    ) as inst:
        channel = inst.channel[channel_no]
        x_read, y_read = channel.read_waveform(bin_format=True)
        iterable_eq(x_read, x_calc)
        iterable_eq(y_read, y_calc)


@given(values=st.lists(st.floats(min_value=0), min_size=1))
def test_data_source_read_waveform_ascii(values):
    """Read waveform from data source as ASCII."""
    # constants - to not overkill it with hypothesis
    channel_no = 0
    yoffs = 1.0
    ymult = 1.0
    yzero = 0.3
    xincr = 0.001
    # make values to compare with
    values_str = ",".join([str(value) for value in values])
    values_arr = values
    if numpy:
        values_arr = numpy.array(values)

    # calculations
    ptcnt = len(values)
    if numpy:
        x_calc = numpy.arange(float(ptcnt)) * xincr
        y_calc = ((values_arr - yoffs) * ymult) + yzero
    else:
        x_calc = tuple(float(val) * float(xincr) for val in range(ptcnt))
        y_calc = tuple(((val - yoffs) * float(ymult)) + float(yzero) for val in values)

    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [
            "DAT:SOU?",
            "DAT:ENC ASCI",
            "CURVE?",
            f"WFMP:CH{channel_no+1}:YOF?",
            f"WFMP:CH{channel_no+1}:YMU?",
            f"WFMP:CH{channel_no+1}:YZE?",
            f"WFMP:CH{channel_no+1}:XIN?",
            f"WFMP:CH{channel_no+1}:NR_P?",
        ],
        [
            f"CH{channel_no+1}",
            values_str,
            f"{yoffs}",
            f"{ymult}",
            f"{yzero}",
            f"{xincr}",
            f"{ptcnt}",
        ],
    ) as inst:
        channel = inst.channel[channel_no]
        x_read, y_read = channel.read_waveform(bin_format=False)
        iterable_eq(x_read, x_calc)
        iterable_eq(y_read, y_calc)


# CHANNEL #


@pytest.mark.parametrize("channel", [it for it in range(4)])
def test_channel_init(channel):
    """Initialize a new channel."""
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        assert inst.channel[channel]._parent is inst
        assert inst.channel[channel]._idx == channel + 1


@pytest.mark.parametrize("coupl", ik.tektronix.TekTDS5xx.Coupling)
def test_channel_coupling(coupl):
    """Get / set channel coupling."""
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"CH{channel+1}:COUPL {coupl.value}", f"CH{channel+1}:COUPL?"],
        [f"{coupl.value}"],
    ) as inst:
        inst.channel[channel].coupling = coupl
        assert inst.channel[channel].coupling == coupl


def test_channel_coupling_type_error():
    """Raise type error if channel coupling is set with wrong type."""
    wrong_type = 42
    channel = 0
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.channel[channel].coupling = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Coupling setting must be a `TekTDS5xx.Coupling` "
            f"value, got {type(wrong_type)} instead."
        )


@pytest.mark.parametrize("bandw", ik.tektronix.TekTDS5xx.Bandwidth)
def test_channel_bandwidth(bandw):
    """Get / set channel bandwidth."""
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"CH{channel+1}:BAND {bandw.value}", f"CH{channel+1}:BAND?"],
        [f"{bandw.value}"],
    ) as inst:
        inst.channel[channel].bandwidth = bandw
        assert inst.channel[channel].bandwidth == bandw


def test_channel_bandwidth_type_error():
    """Raise type error if channel bandwidth is set with wrong type."""
    wrong_type = 42
    channel = 0
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.channel[channel].bandwidth = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Bandwidth setting must be a "
            f"`TekTDS5xx.Bandwidth` value, got "
            f"{type(wrong_type)} instead."
        )


@pytest.mark.parametrize("imped", ik.tektronix.TekTDS5xx.Impedance)
def test_channel_impedance(imped):
    """Get / set channel impedance."""
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"CH{channel+1}:IMP {imped.value}", f"CH{channel+1}:IMP?"],
        [f"{imped.value}"],
    ) as inst:
        inst.channel[channel].impedance = imped
        assert inst.channel[channel].impedance == imped


def test_channel_impedance_type_error():
    """Raise type error if channel impedance is set with wrong type."""
    wrong_type = 42
    channel = 0
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.channel[channel].impedance = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Impedance setting must be a "
            f"`TekTDS5xx.Impedance` value, got "
            f"{type(wrong_type)} instead."
        )


@given(value=st.floats(min_value=0, exclude_min=True))
def test_channel_probe(value):
    """Get connected probe value."""
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx, [f"CH{channel+1}:PRO?"], [f"{value}"]
    ) as inst:
        value_expected = round(1 / value, 0)
        assert inst.channel[channel].probe == value_expected


@given(value=st.floats(min_value=0))
def test_channel_scale(value):
    """Get / set scale setting."""
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [
            f"CH{channel + 1}:SCA {value:.3E}",
            f"CH{channel + 1}:SCA?",
            f"CH{channel + 1}:SCA?",
        ],
        [f"{value}", f"{value}"],
    ) as inst:
        inst.channel[channel].scale = value
        print(f"\n>>>{value}")
        assert inst.channel[channel].scale == value


def test_channel_scale_value_error():
    """Raise ValueError if scale was not set properly."""
    scale_set = 42
    scale_rec = 13
    channel = 0
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"CH{channel + 1}:SCA {scale_set:.3E}", f"CH{channel + 1}:SCA?"],
        [f"{scale_rec}"],
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.channel[channel].scale = scale_set
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Tried to set CH{channel+1} Scale to {scale_set} "
            f"but got {float(scale_rec)} instead"
        )


# INSTRUMENT #


@given(states=st.lists(st.integers(min_value=0, max_value=1), min_size=11, max_size=11))
def test_sources(states):
    """Get list of all active sources."""
    active_sources = []
    with expected_protocol(
        ik.tektronix.TekTDS5xx, ["SEL?"], [";".join([str(state) for state in states])]
    ) as inst:
        # create active_sources
        for idx in range(4):
            if states[idx]:
                active_sources.append(
                    ik.tektronix.tektds5xx.TekTDS5xx.Channel(inst, idx)
                )
        for idx in range(4, 7):
            if states[idx]:
                active_sources.append(
                    ik.tektronix.tektds5xx.TekTDS5xx.DataSource(inst, f"MATH{idx - 3}")
                )
        for idx in range(7, 11):
            if states[idx]:
                active_sources.append(
                    ik.tektronix.tektds5xx.TekTDS5xx.DataSource(inst, f"REF{idx - 6}")
                )
        # read active sources
        active_read = inst.sources

        assert active_read == active_sources


@pytest.mark.parametrize("channel", [it for it in range(4)])
def test_data_source_channel(channel):
    """Get / set channel data source for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"DAT:SOU CH{channel+1}", f"DAT:SOU CH{channel+1}", "DAT:SOU?"],
        [f"CH{channel+1}"],
    ) as inst:
        # set as Source enum
        inst.data_source = ik.tektronix.TekTDS5xx.Source[f"CH{channel + 1}"]
        # set as channel object
        data_source = inst.channel[channel]
        inst.data_source = data_source
        assert inst.data_source == data_source


@pytest.mark.parametrize("channel", [it for it in range(3)])
def test_data_source_math(channel):
    """Get / set math data source for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"DAT:SOU MATH{channel+1}", f"DAT:SOU MATH{channel+1}", "DAT:SOU?"],
        [f"MATH{channel+1}"],
    ) as inst:
        # set as Source enum
        inst.data_source = ik.tektronix.TekTDS5xx.Source[f"Math{channel + 1}"]
        # set as channel object
        data_source = inst.math[channel]
        inst.data_source = data_source
        assert inst.data_source == data_source


@pytest.mark.parametrize("channel", [it for it in range(3)])
def test_data_source_ref(channel):
    """Get / set ref data source for waveform transfer."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"DAT:SOU REF{channel+1}", f"DAT:SOU REF{channel+1}", "DAT:SOU?"],
        [f"REF{channel+1}"],
    ) as inst:
        # set as Source enum
        inst.data_source = ik.tektronix.TekTDS5xx.Source[f"Ref{channel + 1}"]
        # set as channel object
        data_source = inst.ref[channel]
        inst.data_source = data_source
        assert inst.data_source == data_source


def test_data_source_raise_type_error():
    """Raise TypeError when setting data source with wrong type."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.data_source = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Source setting must be a `TekTDS5xx.Source` "
            f"value, got {type(wrong_type)} instead."
        )


@pytest.mark.parametrize("width", (1, 2))
def test_data_width(width):
    """Get / set data width."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx, [f"DATA:WIDTH {width}", "DATA:WIDTH?"], [f"{width}"]
    ) as inst:
        inst.data_width = width
        assert inst.data_width == width


@given(width=st.integers().filter(lambda x: x < 1 or x > 2))
def test_data_width_value_error(width):
    """Raise ValueError when setting a wrong data width."""
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.data_width = width
        err_msg = err_info.value.args[0]
        assert err_msg == "Only one or two byte-width is supported."


def test_force_trigger():
    """Raise NotImplementedError when forcing a trigger."""
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(NotImplementedError):
            inst.force_trigger()


@given(value=st.floats(min_value=0))
def test_horizontal_scale(value):
    """Get / set horizontal scale."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"HOR:MAI:SCA {value:.3E}", "HOR:MAI:SCA?", "HOR:MAI:SCA?"],
        [f"{value}", f"{value}"],
    ) as inst:
        inst.horizontal_scale = value
        assert inst.horizontal_scale == value


def test_horizontal_scale_value_error():
    """Raise ValueError if setting horizontal scale does not work."""
    set_value = 42
    get_value = 13
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"HOR:MAI:SCA {set_value:.3E}", "HOR:MAI:SCA?"],
        [
            f"{get_value}",
        ],
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.horizontal_scale = set_value
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Tried to set Horizontal Scale to {set_value} "
            f"but got {float(get_value)} instead"
        )


@given(value=st.floats(min_value=0))
def test_trigger_level(value):
    """Get / set trigger level."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"TRIG:MAI:LEV {value:.3E}", "TRIG:MAI:LEV?", "TRIG:MAI:LEV?"],
        [f"{value}", f"{value}"],
    ) as inst:
        inst.trigger_level = value
        assert inst.trigger_level == value


def test_trigger_level_value_error():
    """Raise ValueError if setting trigger level does not work."""
    set_value = 42
    get_value = 13
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"TRIG:MAI:LEV {set_value:.3E}", "TRIG:MAI:LEV?"],
        [f"{get_value}"],
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.trigger_level = set_value
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Tried to set trigger level to {set_value} "
            f"but got {float(get_value)} instead"
        )


@pytest.mark.parametrize("coupl", ik.tektronix.TekTDS5xx.Coupling)
def test_trigger_coupling(coupl):
    """Get / set trigger coupling."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"TRIG:MAI:EDGE:COUP {coupl.value}", "TRIG:MAI:EDGE:COUP?"],
        [f"{coupl.value}"],
    ) as inst:
        inst.trigger_coupling = coupl
        assert inst.trigger_coupling == coupl


def test_trigger_coupling_type_error():
    """Raise type error when coupling is not a `Coupling` enum."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.trigger_coupling = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Coupling setting must be a `TekTDS5xx.Coupling` "
            f"value, got {type(wrong_type)} instead."
        )


@pytest.mark.parametrize("edge", ik.tektronix.TekTDS5xx.Edge)
def test_trigger_slope(edge):
    """Get / set trigger slope."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"TRIG:MAI:EDGE:SLO {edge.value}", "TRIG:MAI:EDGE:SLO?"],
        [f"{edge.value}"],
    ) as inst:
        inst.trigger_slope = edge
        assert inst.trigger_slope == edge


def test_trigger_slope_type_error():
    """Raise type error when edge is not an `Edge` enum."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.trigger_slope = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Edge setting must be a `TekTDS5xx.Edge` "
            f"value, got {type(wrong_type)} instead."
        )


@pytest.mark.parametrize("source", ik.tektronix.TekTDS5xx.Trigger)
def test_trigger_source(source):
    """Get / set trigger source."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"TRIG:MAI:EDGE:SOU {source.value}", "TRIG:MAI:EDGE:SOU?"],
        [f"{source.value}"],
    ) as inst:
        inst.trigger_source = source
        assert inst.trigger_source == source


def test_trigger_source_type_error():
    """Raise type error when source is not an `source` enum."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.trigger_source = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Trigger source setting must be a "
            f"`TekTDS5xx.Trigger` value, got "
            f"{type(wrong_type)} instead."
        )


@given(dt=st.datetimes(min_value=datetime(1000, 1, 1)))
def test_clock(dt):
    """Get / set oscilloscope clock."""
    # create a date and time
    dt_fmt_receive = '"%Y-%m-%d";"%H:%M:%S"'
    dt_fmt_send = 'DATE "%Y-%m-%d";:TIME "%H:%M:%S"'
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [dt.strftime(dt_fmt_send), "DATE?;:TIME?"],
        [dt.strftime(dt_fmt_receive)],
    ) as inst:
        inst.clock = dt
        assert inst.clock == dt.replace(microsecond=0)


def test_clock_value_error():
    """Raise ValueError when not set with datetime object."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.clock = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Expected datetime.datetime but got "
            f"{type(wrong_type)} instead"
        )


@pytest.mark.parametrize("newval", (True, False))
def test_display_clock(newval):
    """Get / set if clock is displayed on screen."""
    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [f"DISPLAY:CLOCK {int(newval)}", "DISPLAY:CLOCK?"],
        [f"{int(newval)}"],
    ) as inst:
        inst.display_clock = newval
        assert inst.display_clock == newval


def test_display_clock_value_error():
    """Raise ValueError when display_clock is called w/o a bool."""
    wrong_type = 42
    with expected_protocol(ik.tektronix.TekTDS5xx, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.display_clock = wrong_type
        err_msg = err_info.value.args[0]
        assert err_msg == f"Expected bool but got {type(wrong_type)} instead"


@given(data=st.binary(min_size=1, max_size=2147483647))
def test_get_hardcopy(mocker, data):
    """Transfer data in binary from the instrument.

    Data is at least 1 byte long, then we need to add 8 for the
    color table.
    Fake the header of the data such that in byte 18:30 are 4 factorial
    packed as '<iihh' that multiplied together result in the length of
    the total data. Limit maximum size of binary such that we don't have
    to factor the length and such that it simply fits into 4 bytes
    unsigned.
    Take some random data, then stick a header to it. Unchecked entries
    in header are filled with zeros.
    Mocking out sleep to do nothing.
    """
    # mock out time
    mocker.patch.object(time, "sleep", return_value=None)

    # make data
    length_data = (len(data) - 8) * 8  # subtract header and color table
    # make a fake header
    header = struct.pack("<ddhiihhddd", 0, 0, 0, length_data, 1, 1, 1, 0, 0, 0)
    # stick header and data together
    data_expected = header + data

    with expected_protocol(
        ik.tektronix.TekTDS5xx,
        [
            "HARDC:PORT GPI;HARDC:LAY PORT;:HARDC:FORM BMP",
            "HARDC START",
        ],
        [header + data],
    ) as inst:
        data_read = inst.get_hardcopy()
        assert data_read == data_expected
