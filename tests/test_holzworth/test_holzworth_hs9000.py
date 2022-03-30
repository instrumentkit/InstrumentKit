#!/usr/bin/env python
"""
Unit tests for the Holzworth HS9000
"""

# IMPORTS #####################################################################


from instruments.units import ureg as u

import instruments as ik
from tests import expected_protocol
from .. import mock

# TEST CLASSES ################################################################

# pylint: disable=protected-access


def test_hs9000_name():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:IDN?"],
        [":CH1:CH2:FOO", "Foobar name"],
        sep="\n",
    ) as hs:
        assert hs.name == "Foobar name"


def test_channel_idx_list():
    with expected_protocol(
        ik.holzworth.HS9000,
        [
            ":ATTACH?",
        ],
        [":CH1:CH2:FOO"],
        sep="\n",
    ) as hs:
        assert hs._channel_idxs() == [0, 1, "FOO"]


def test_channel_returns_inner_class():
    with expected_protocol(
        ik.holzworth.HS9000,
        [
            ":ATTACH?",
        ],
        [":CH1:CH2:FOO"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert isinstance(channel, hs.Channel) is True
        assert channel._ch_name == "CH1"


def test_channel_sendcmd():
    channel = ik.holzworth.HS9000.Channel(mock.MagicMock(), 0)

    channel.sendcmd("FOO")

    channel._hs.sendcmd.assert_called_with(":CH1:FOO")


def test_channel_query():
    channel = ik.holzworth.HS9000.Channel(mock.MagicMock(), 0)
    channel._hs.query.return_value = "FOO"

    value = channel.query("BAR")

    channel._hs.query.assert_called_with(":CH1:BAR")
    assert value == "FOO"


def test_channel_reset():
    channel = ik.holzworth.HS9000.Channel(mock.MagicMock(), 0)
    channel.reset()

    channel._hs.sendcmd.assert_called_with(":CH1:*RST")


def test_channel_recall_state():
    channel = ik.holzworth.HS9000.Channel(mock.MagicMock(), 0)
    channel.recall_state()

    channel._hs.sendcmd.assert_called_with(":CH1:*RCL")


def test_channel_save_state():
    channel = ik.holzworth.HS9000.Channel(mock.MagicMock(), 0)
    channel.save_state()

    channel._hs.sendcmd.assert_called_with(":CH1:*SAV")


def test_channel_temperature():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:TEMP?"],
        [":CH1:CH2:FOO", "10 C"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert channel.temperature == u.Quantity(10, u.degC)


def test_channel_frequency_getter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:FREQ?", ":CH1:FREQ:MIN?", ":CH1:FREQ:MAX?"],
        [":CH1:CH2:FOO", "1000 MHz", "100 MHz", "10 GHz"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert channel.frequency == 1 * u.GHz
        assert channel.frequency_min == 100 * u.MHz
        assert channel.frequency_max == 10 * u.GHz


def test_channel_frequency_setter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:FREQ:MIN?", ":CH1:FREQ:MAX?", f":CH1:FREQ {1:e}"],
        [":CH1:CH2:FOO", "100 MHz", "10 GHz"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        channel.frequency = 1 * u.GHz


def test_channel_power_getter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:PWR?", ":CH1:PWR:MIN?", ":CH1:PWR:MAX?"],
        [":CH1:CH2:FOO", "0", "-100", "20"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert channel.power == u.Quantity(0, u.dBm)
        assert channel.power_min == u.Quantity(-100, u.dBm)
        assert channel.power_max == u.Quantity(20, u.dBm)


def test_channel_power_setter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:PWR:MIN?", ":CH1:PWR:MAX?", f":CH1:PWR {0:e}"],
        [":CH1:CH2:FOO", "-100", "20"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        channel.power = u.Quantity(0, u.dBm)


def test_channel_phase_getter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:PHASE?", ":CH1:PHASE:MIN?", ":CH1:PHASE:MAX?"],
        [":CH1:CH2:FOO", "0", "-180", "+180"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert channel.phase == 0 * u.degree
        assert channel.phase_min == -180 * u.degree
        assert channel.phase_max == 180 * u.degree


def test_channel_phase_setter():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:PHASE:MIN?", ":CH1:PHASE:MAX?", f":CH1:PHASE {0:e}"],
        [":CH1:CH2:FOO", "-180", "+180"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        channel.phase = 0 * u.degree


def test_channel_output():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":ATTACH?", ":CH1:PWR:RF?", ":CH1:PWR:RF:ON", ":CH1:PWR:RF:OFF"],
        [":CH1:CH2:FOO", "OFF"],
        sep="\n",
    ) as hs:
        channel = hs.channel[0]
        assert channel.output is False
        channel.output = True
        channel.output = False


def test_hs9000_is_ready():
    with expected_protocol(
        ik.holzworth.HS9000,
        [":COMM:READY?", ":COMM:READY?"],
        ["Ready", "DANGER DANGER"],
        sep="\n",
    ) as hs:
        assert hs.ready is True
        assert hs.ready is False
