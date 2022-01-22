#!/usr/bin/env python
"""
Module containing tests for the SRS CTC-100
"""

# IMPORTS ####################################################################

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
)
from instruments.units import ureg as u

# TESTS ######################################################################


# pylint: disable=protected-access


# SETUP #


# Create one channel name for every possible unit for parametrized testing
ch_units = list(ik.srs.SRSCTC100._UNIT_NAMES.keys())
ch_names = [f"CH {it}" for it in range(len(ch_units))]
ch_name_unit_dict = dict(zip(ch_names, ch_units))


# string that is returned when initializing channels:
ch_names_query = "getOutput.names?"
ch_names_str = ",".join(ch_names)


# CHANNELS #


@pytest.mark.parametrize("channel", ch_names)
def test_srsctc100_channel_init(channel):
    """Initialize a channel."""
    with expected_protocol(ik.srs.SRSCTC100, [ch_names_query], [ch_names_str]) as inst:
        with inst._error_checking_disabled():
            ch = inst.channel[channel]
            assert ch._ctc is inst
            assert ch._chan_name == channel
            assert ch._rem_name == channel.replace(" ", "")


def test_srsctc100_channel_name():
    """Get / set the channel name."""
    old_name = ch_names[0]
    new_name = "New channel"
    with expected_protocol(
        ik.srs.SRSCTC100,
        [ch_names_query, f"{old_name.replace(' ', '')}.name = \"{new_name}\""],
        [ch_names_str],
    ) as inst:
        with inst._error_checking_disabled():
            ch = inst.channel[ch_names[0]]
            # assert old name is set
            assert ch.name == ch_names[0]
            # set a new name
            ch.name = new_name
            assert ch.name == new_name
            assert ch._rem_name == new_name.replace(" ", "")


@pytest.mark.parametrize("channel", ch_names)
def test_srsctc100_channel_get(channel):
    """Query a given channel.

    Ensure proper functionality for all available channels.
    """
    cmd = "COMMAND"
    answ = "ANSWER"
    with expected_protocol(
        ik.srs.SRSCTC100,
        [ch_names_query, f"{channel.replace(' ', '')}.{cmd}?"],
        [ch_names_str, answ],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel]._get(cmd) == answ


@pytest.mark.parametrize("channel", ch_names)
def test_srsctc100_channel_set(channel):
    """Send a command to a given channel.

    Ensure proper functionality for all available channels.
    """
    cmd = "COMMAND"
    newval = "NEWVAL"
    with expected_protocol(
        ik.srs.SRSCTC100,
        [ch_names_query, f"{channel.replace(' ', '')}.{cmd} = \"{newval}\""],
        [ch_names_str],
    ) as inst:
        with inst._error_checking_disabled():
            inst.channel[channel]._set(cmd, newval)


def test_srsctc100_channel_value():
    """Get value and unit from a given channel."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_units[0]]
    value = 42

    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.value?",
            "getOutput.units?",
            ch_names_query,
        ],
        [
            ch_names_str,
            f"{value}",
            ",".join(ch_units),
            ch_names_str,
        ],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel].value == u.Quantity(value, unit)


def test_srsctc100_channel_units_single():
    """Get unit for one given channel."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_units[0]]
    with expected_protocol(
        ik.srs.SRSCTC100,
        [ch_names_query, "getOutput.units?", ch_names_query],
        [
            ch_names_str,
            ",".join(ch_units),
            ch_names_str,
        ],
    ) as inst:
        with inst._error_checking_disabled():
            ch = inst.channel[channel]
            assert ch.units == unit


@pytest.mark.parametrize("sensor", ik.srs.SRSCTC100.SensorType)
def test_srsctc100_channel_sensor_type(sensor):
    """Get type of sensor attached to specified channel."""
    channel = ch_names[0]
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.sensor?",
        ],
        [ch_names_str, f"{sensor.value}"],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel].sensor_type == sensor


@pytest.mark.parametrize("newval", (True, False))
def test_srsctc100_channel_stats_enabled(newval):
    """Get / set enabling statistics for specified channel."""
    channel = ch_names[0]
    value_inst = "On" if newval else "Off"
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.stats = \"{value_inst}\"",
            f"{channel.replace(' ', '')}.stats?",
        ],
        [ch_names_str, f"{value_inst}"],
    ) as inst:
        with inst._error_checking_disabled():
            ch = inst.channel[channel]
            ch.stats_enabled = newval
            assert ch.stats_enabled == newval


@given(points=st.integers(min_value=2, max_value=6000))
def test_srsctc100_channel_stats_points(points):
    """Get / set stats points in valid range."""
    channel = ch_names[0]
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.points = \"{points}\"",
            f"{channel.replace(' ', '')}.points?",
        ],
        [ch_names_str, f"{points}"],
    ) as inst:
        with inst._error_checking_disabled():
            ch = inst.channel[channel]
            ch.stats_points = points
            assert ch.stats_points == points


def test_srsctc100_channel_average():
    """Get average measurement for given channel, unitful."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_units[0]]
    value = 42
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.average?",
            "getOutput.units?",
            ch_names_query,
        ],
        [
            ch_names_str,
            f"{value}",
            ",".join(ch_units),
            ch_names_str,
        ],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel].average == u.Quantity(value, unit)


def test_srsctc100_channel_std_dev():
    """Get standard deviation for given channel, unitful."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_units[0]]
    value = 42
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            f"{channel.replace(' ', '')}.SD?",
            "getOutput.units?",
            ch_names_query,
        ],
        [
            ch_names_str,
            f"{value}",
            ",".join(ch_units),
            ch_names_str,
        ],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel].std_dev == u.Quantity(value, unit)


@pytest.mark.parametrize("channel", ch_names)
def test_get_log_point(channel):
    """Get a log point and include a unit query."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_name_unit_dict[channel]]
    values = (13, 42)
    which = "first"
    values_out = (
        u.Quantity(float(values[0]), u.ms),
        u.Quantity(float(values[1]), unit),
    )
    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            "getOutput.units?",
            ch_names_query,
            f"getLog.xy {channel}, {which}",
        ],
        [ch_names_str, ",".join(ch_units), ch_names_str, f"{values[0]},{values[1]}"],
    ) as inst:
        with inst._error_checking_disabled():
            assert inst.channel[channel].get_log_point(which=which) == values_out


def test_get_log_point_with_unit():
    """Get a log point and include a unit query."""
    channel = ch_names[0]
    unit = ik.srs.SRSCTC100._UNIT_NAMES[ch_units[0]]
    values = (13, 42)
    which = "first"
    values_out = (
        u.Quantity(float(values[0]), u.ms),
        u.Quantity(float(values[1]), unit),
    )
    with expected_protocol(
        ik.srs.SRSCTC100,
        [ch_names_query, f"getLog.xy {channel}, {which}"],
        [ch_names_str, f"{values[0]},{values[1]}"],
    ) as inst:
        with inst._error_checking_disabled():
            assert (
                inst.channel[channel].get_log_point(which=which, units=unit)
                == values_out
            )


@pytest.mark.parametrize("channel", ch_names)
def test_channel_get_log(channel):
    """Get the full log of a channel.

    Leave error checking activated, because it is run at the end.
    """
    # make some data
    times = [0, 1, 2, 3]
    values = [1.3, 2.4, 3.5, 4.6]

    # variables
    units = ik.srs.SRSCTC100._UNIT_NAMES[ch_name_unit_dict[channel]]
    n_points = len(values)

    # strings for error checking, sending and receiving
    err_check_send = "geterror?"
    err_check_reci = "0,NO ERROR"

    # stich together strings to read all the values
    str_log_next_send = "\n".join(
        [f"getLog.xy {channel}, next" for it in range(1, n_points)]
    )
    str_log_next_reci = "\n".join(
        [f"{times[it]},{values[it]}" for it in range(1, n_points)]
    )

    # make data to compare with
    if numpy:
        ts = u.Quantity(numpy.empty((n_points,)), u.ms)
        temps = u.Quantity(numpy.empty((n_points,)), units)
    else:
        ts = [u.Quantity(0, u.ms)] * n_points
        temps = [u.Quantity(0, units)] * n_points
    for it, time in enumerate(times):
        ts[it] = u.Quantity(time, u.ms)
        temps[it] = u.Quantity(values[it], units)

    if not numpy:
        ts = tuple(ts)
        temps = tuple(temps)

    with expected_protocol(
        ik.srs.SRSCTC100,
        [
            ch_names_query,
            err_check_send,
            "getOutput.units?",
            err_check_send,
            ch_names_query,
            err_check_send,
            f"getLog.xy? {channel}",
            err_check_send,
            f"getLog.xy {channel}, first",  # query first point
            str_log_next_send,
            err_check_send,
        ],
        [
            ch_names_str,
            err_check_reci,
            ",".join(ch_units),
            err_check_reci,
            ch_names_str,
            err_check_reci,
            f"{n_points}",
            err_check_reci,
            f"{times[0]},{values[0]}",
            str_log_next_reci,
            err_check_reci,
        ],
    ) as inst:
        ch = inst.channel[channel]
        ts_read, temps_read = ch.get_log()
        # assert the data is correct
        iterable_eq(ts, ts_read)
        iterable_eq(temps, temps_read)


# INSTRUMENT #


def test_srsctc100_init():
    """Initialize the SRS CTC-100 instrument."""
    with expected_protocol(ik.srs.SRSCTC100, [], []) as inst:
        assert inst._do_errcheck


def test_srsctc100_channel_names():
    """Get current channel names from instrument."""
    with expected_protocol(ik.srs.SRSCTC100, [ch_names_query], [ch_names_str]) as inst:
        with inst._error_checking_disabled():
            assert inst._channel_names() == ch_names


def test_srsctc100_channel_units_all():
    """Get units for all channels."""
    with expected_protocol(
        ik.srs.SRSCTC100,
        ["getOutput.units?", ch_names_query],
        [",".join(ch_units), ch_names_str],
    ) as inst:
        with inst._error_checking_disabled():
            # create a unit dictionary to compare the return to
            unit_dict = {
                chan_name: ik.srs.SRSCTC100._UNIT_NAMES[unit_str]
                for chan_name, unit_str in zip(ch_names, ch_units)
            }
            assert inst.channel_units() == unit_dict


def test_srsctc100_errcheck():
    """Error check - no error returned."""
    with expected_protocol(ik.srs.SRSCTC100, ["geterror?"], ["0,NO ERROR"]) as inst:
        assert inst.errcheck() == 0


def test_srsctc100_errcheck_error_raised():
    """Error check - error raises."""
    with expected_protocol(ik.srs.SRSCTC100, ["geterror?"], ["42,THE ANSWER"]) as inst:
        with pytest.raises(IOError) as exc_info:
            inst.errcheck()
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "THE ANSWER"


def test_srsctc100_error_checking_disabled_context():
    """Context dialogue to disable error checking."""
    with expected_protocol(ik.srs.SRSCTC100, [], []) as inst:
        # by default, error checking enabled
        with inst._error_checking_disabled():
            assert not inst._do_errcheck

        # default enabled again
        assert inst._do_errcheck


@given(figures=st.integers(min_value=0, max_value=6))
def test_srsctc100_display_figures(figures):
    """Get / set significant figures of display."""
    with expected_protocol(
        ik.srs.SRSCTC100,
        [f"system.display.figures = {figures}", "system.display.figures?"],
        [f"{figures}"],
    ) as inst:
        with inst._error_checking_disabled():
            inst.display_figures = figures
            assert inst.display_figures == figures


@given(figures=st.integers().filter(lambda x: x < 0 or x > 6))
def test_srsctc100_display_figures_value_error(figures):
    """Raise ValueError when setting an invalid number of figures."""
    with expected_protocol(ik.srs.SRSCTC100, [], []) as inst:
        with inst._error_checking_disabled():
            with pytest.raises(ValueError) as exc_info:
                inst.display_figures = figures
            exc_msg = exc_info.value.args[0]
            assert (
                exc_msg == "Number of display figures must be an "
                "integer from 0 to 6, inclusive."
            )


@pytest.mark.parametrize("newval", (True, False))
def test_srsctc100_error_check_toggle(newval):
    """Get / set error check bool."""
    with expected_protocol(ik.srs.SRSCTC100, [], []) as inst:
        inst.error_check_toggle = newval
        assert inst.error_check_toggle == newval


def test_srsctc100_error_check_toggle_type_error():
    """Raise type error when error check toggle set with non-bool."""
    newval = 42
    with expected_protocol(ik.srs.SRSCTC100, [], []) as inst:
        with pytest.raises(TypeError):
            inst.error_check_toggle = newval


def test_srsctc100_sendcmd():
    """Send a command and error check."""
    cmd = "COMMAND"
    with expected_protocol(
        ik.srs.SRSCTC100, [cmd, "geterror?"], ["0,NO ERROR"]
    ) as inst:
        inst.sendcmd("COMMAND")


def test_srsctc100_query():
    """Send a query and error check."""
    cmd = "COMMAND"
    answ = "ANSWER"
    with expected_protocol(
        ik.srs.SRSCTC100, [cmd, "geterror?"], [answ, "0,NO ERROR"]
    ) as inst:
        assert inst.query("COMMAND") == answ


def test_srsctc100_clear_log():
    """Clear the log."""
    with expected_protocol(ik.srs.SRSCTC100, ["System.Log.Clear yes"], []) as inst:
        with inst._error_checking_disabled():
            inst.clear_log()
