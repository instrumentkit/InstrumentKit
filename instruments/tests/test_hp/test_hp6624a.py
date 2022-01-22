#!/usr/bin/env python
"""
Unit tests for the HP 6624a power supply
"""

# IMPORTS #####################################################################

import pytest

import instruments as ik
from instruments.tests import (
    expected_protocol,
    iterable_eq,
)
from instruments.units import ureg as u
from .. import mock

# TESTS #######################################################################

# pylint: disable=protected-access


def test_channel_returns_inner_class():
    with expected_protocol(ik.hp.HP6624a, [], [], sep="\n") as hp:
        channel = hp.channel[0]
        assert isinstance(channel, hp.Channel) is True
        assert channel._idx == 1


def test_channel_sendcmd():
    channel = ik.hp.HP6624a.Channel(mock.MagicMock(), 0)

    channel.sendcmd("FOO")

    channel._hp.sendcmd.assert_called_with("FOO 1")


def test_channel_sendcmd_2():
    channel = ik.hp.HP6624a.Channel(mock.MagicMock(), 0)

    channel.sendcmd("FOO 5")

    channel._hp.sendcmd.assert_called_with("FOO 1,5")


def test_channel_query():
    channel = ik.hp.HP6624a.Channel(mock.MagicMock(), 0)
    channel._hp.query.return_value = "FOO"

    value = channel.query("BAR?")

    channel._hp.query.assert_called_with("BAR? 1")
    assert value == "FOO"


def test_mode():
    """Raise NotImplementedError when mode is called."""
    with expected_protocol(ik.hp.HP6624a, [], [], sep="\n") as hp:
        channel = hp.channel[0]
        with pytest.raises(NotImplementedError):
            _ = channel.mode
        with pytest.raises(NotImplementedError):
            channel.mode = 42


def test_channel_voltage():
    with expected_protocol(
        ik.hp.HP6624a, ["VSET? 1", f"VSET 1,{5:.1f}"], ["2"], sep="\n"
    ) as hp:
        assert hp.channel[0].voltage == 2 * u.V
        hp.channel[0].voltage = 5 * u.V


def test_channel_current():
    with expected_protocol(
        ik.hp.HP6624a, ["ISET? 1", f"ISET 1,{5:.1f}"], ["2"], sep="\n"
    ) as hp:
        assert hp.channel[0].current == 2 * u.amp
        hp.channel[0].current = 5 * u.amp


def test_channel_voltage_sense():
    with expected_protocol(ik.hp.HP6624a, ["VOUT? 1"], ["2"], sep="\n") as hp:
        assert hp.channel[0].voltage_sense == 2 * u.V


def test_channel_current_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "IOUT? 1",
        ],
        ["2"],
        sep="\n",
    ) as hp:
        assert hp.channel[0].current_sense == 2 * u.A


def test_channel_overvoltage():
    with expected_protocol(
        ik.hp.HP6624a, ["OVSET? 1", f"OVSET 1,{5:.1f}"], ["2"], sep="\n"
    ) as hp:
        assert hp.channel[0].overvoltage == 2 * u.V
        hp.channel[0].overvoltage = 5 * u.V


def test_channel_overcurrent():
    with expected_protocol(ik.hp.HP6624a, ["OVP? 1", "OVP 1,1"], ["1"], sep="\n") as hp:
        assert hp.channel[0].overcurrent is True
        hp.channel[0].overcurrent = True


def test_channel_output():
    with expected_protocol(ik.hp.HP6624a, ["OUT? 1", "OUT 1,1"], ["1"], sep="\n") as hp:
        assert hp.channel[0].output is True
        hp.channel[0].output = True


def test_channel_reset():
    channel = ik.hp.HP6624a.Channel(mock.MagicMock(), 0)
    channel.reset()

    calls = [mock.call("OVRST 1"), mock.call("OCRST 1")]
    channel._hp.sendcmd.assert_has_calls(calls)


def test_all_voltage():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "VSET? 1",
            "VSET? 2",
            "VSET? 3",
            "VSET? 4",
            f"VSET 1,{5:.1f}",
            f"VSET 2,{5:.1f}",
            f"VSET 3,{5:.1f}",
            f"VSET 4,{5:.1f}",
            f"VSET 1,{1:.1f}",
            f"VSET 2,{2:.1f}",
            f"VSET 3,{3:.1f}",
            f"VSET 4,{4:.1f}",
        ],
        ["2", "3", "4", "5"],
        sep="\n",
    ) as hp:
        expected = (2 * u.V, 3 * u.V, 4 * u.V, 5 * u.V)
        iterable_eq(hp.voltage, expected)
        hp.voltage = 5 * u.V
        hp.voltage = (1 * u.V, 2 * u.V, 3 * u.V, 4 * u.V)


def test_all_voltage_wrong_length():
    with pytest.raises(ValueError), expected_protocol(
        ik.hp.HP6624a, [], [], sep="\n"
    ) as hp:
        hp.voltage = (1 * u.volt, 2 * u.volt)


def test_all_current():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "ISET? 1",
            "ISET? 2",
            "ISET? 3",
            "ISET? 4",
            f"ISET 1,{5:.1f}",
            f"ISET 2,{5:.1f}",
            f"ISET 3,{5:.1f}",
            f"ISET 4,{5:.1f}",
            f"ISET 1,{1:.1f}",
            f"ISET 2,{2:.1f}",
            f"ISET 3,{3:.1f}",
            f"ISET 4,{4:.1f}",
        ],
        ["2", "3", "4", "5"],
        sep="\n",
    ) as hp:
        expected = (2 * u.A, 3 * u.A, 4 * u.A, 5 * u.A)
        iterable_eq(hp.current, expected)
        hp.current = 5 * u.A
        hp.current = (1 * u.A, 2 * u.A, 3 * u.A, 4 * u.A)


def test_all_current_wrong_length():
    with pytest.raises(ValueError), expected_protocol(
        ik.hp.HP6624a, [], [], sep="\n"
    ) as hp:
        hp.current = (1 * u.amp, 2 * u.amp)


def test_all_voltage_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        ["VOUT? 1", "VOUT? 2", "VOUT? 3", "VOUT? 4"],
        ["2", "3", "4", "5"],
        sep="\n",
    ) as hp:
        expected = (2 * u.V, 3 * u.V, 4 * u.V, 5 * u.V)
        iterable_eq(hp.voltage_sense, expected)


def test_all_current_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        ["IOUT? 1", "IOUT? 2", "IOUT? 3", "IOUT? 4"],
        ["2", "3", "4", "5"],
        sep="\n",
    ) as hp:
        expected = (2 * u.A, 3 * u.A, 4 * u.A, 5 * u.A)
        iterable_eq(hp.current_sense, expected)


def test_clear():
    with expected_protocol(ik.hp.HP6624a, ["CLR"], [], sep="\n") as hp:
        hp.clear()


def test_channel_count():
    with expected_protocol(ik.hp.HP6624a, [], [], sep="\n") as hp:
        assert hp.channel_count == 4
        hp.channel_count = 3


def test_channel_count_wrong_type():
    with pytest.raises(TypeError), expected_protocol(
        ik.hp.HP6624a, [], [], sep="\n"
    ) as hp:
        hp.channel_count = "foobar"


def test_channel_count_too_small():
    with pytest.raises(ValueError), expected_protocol(
        ik.hp.HP6624a, [], [], sep="\n"
    ) as hp:
        hp.channel_count = 0
