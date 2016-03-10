#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the HP 6624a power supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import mock
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################

# pylint: disable=protected-access


def test_channel_returns_inner_class():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
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


def test_channel_voltage():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "VSET? 1",
            "VSET 1,{:.1f}".format(5)
        ],
        [
            "2"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].voltage == 2 * pq.V
        hp.channel[0].voltage = 5 * pq.V


def test_channel_current():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "ISET? 1",
            "ISET 1,{:.1f}".format(5)
        ],
        [
            "2"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].current == 2 * pq.amp
        hp.channel[0].current = 5 * pq.amp


def test_channel_voltage_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "VOUT? 1"
        ],
        [
            "2"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].voltage_sense == 2 * pq.V


def test_channel_current_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "IOUT? 1",
        ],
        [
            "2"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].current_sense == 2 * pq.A


def test_channel_overvoltage():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "OVSET? 1",
            "OVSET 1,{:.1f}".format(5)
        ],
        [
            "2"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].overvoltage == 2 * pq.V
        hp.channel[0].overvoltage = 5 * pq.V


def test_channel_overcurrent():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "OVP? 1",
            "OVP 1,1"
        ],
        [
            "1"
        ],
        sep="\n"
    ) as hp:
        assert hp.channel[0].overcurrent is True
        hp.channel[0].overcurrent = True


def test_channel_output():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "OUT? 1",
            "OUT 1,1"
        ],
        [
            "1"
        ],
        sep="\n"
    ) as hp:
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

            "VSET 1,{:.1f}".format(5),
            "VSET 2,{:.1f}".format(5),
            "VSET 3,{:.1f}".format(5),
            "VSET 4,{:.1f}".format(5),

            "VSET 1,{:.1f}".format(1),
            "VSET 2,{:.1f}".format(2),
            "VSET 3,{:.1f}".format(3),
            "VSET 4,{:.1f}".format(4)
        ],
        [
            "2",
            "3",
            "4",
            "5"
        ],
        sep="\n"
    ) as hp:
        assert sorted(hp.voltage) == sorted((2, 3, 4, 5) * pq.V)
        hp.voltage = 5 * pq.V
        hp.voltage = (1 * pq.V, 2 * pq.V, 3 * pq.V, 4 * pq.V)


@raises(ValueError)
def test_all_voltage_wrong_length():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
        hp.voltage = (1 * pq.volt, 2 * pq.volt)


def test_all_current():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "ISET? 1",
            "ISET? 2",
            "ISET? 3",
            "ISET? 4",

            "ISET 1,{:.1f}".format(5),
            "ISET 2,{:.1f}".format(5),
            "ISET 3,{:.1f}".format(5),
            "ISET 4,{:.1f}".format(5),

            "ISET 1,{:.1f}".format(1),
            "ISET 2,{:.1f}".format(2),
            "ISET 3,{:.1f}".format(3),
            "ISET 4,{:.1f}".format(4)
        ],
        [
            "2",
            "3",
            "4",
            "5"
        ],
        sep="\n"
    ) as hp:
        assert sorted(hp.current) == sorted((2, 3, 4, 5) * pq.A)
        hp.current = 5 * pq.A
        hp.current = (1 * pq.A, 2 * pq.A, 3 * pq.A, 4 * pq.A)


@raises(ValueError)
def test_all_current_wrong_length():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
        hp.current = (1 * pq.amp, 2 * pq.amp)


def test_all_voltage_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "VOUT? 1",
            "VOUT? 2",
            "VOUT? 3",
            "VOUT? 4"
        ],
        [
            "2",
            "3",
            "4",
            "5"
        ],
        sep="\n"
    ) as hp:
        assert sorted(hp.voltage_sense) == sorted((2, 3, 4, 5) * pq.V)


def test_all_current_sense():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "IOUT? 1",
            "IOUT? 2",
            "IOUT? 3",
            "IOUT? 4"
        ],
        [
            "2",
            "3",
            "4",
            "5"
        ],
        sep="\n"
    ) as hp:
        assert sorted(hp.current_sense) == sorted((2, 3, 4, 5) * pq.A)


def test_clear():
    with expected_protocol(
        ik.hp.HP6624a,
        [
            "CLR"
        ],
        [],
        sep="\n"
    ) as hp:
        hp.clear()


def test_channel_count():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
        assert hp.channel_count == 4
        hp.channel_count = 3


@raises(TypeError)
def test_channel_count_wrong_type():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
        hp.channel_count = "foobar"


@raises(ValueError)
def test_channel_count_too_small():
    with expected_protocol(
        ik.hp.HP6624a,
        [],
        [],
        sep="\n"
    ) as hp:
        hp.channel_count = 0
