#!/usr/bin/env python
"""
Module containing tests for the SRS DG645
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.abstract_instruments.comm import GPIBCommunicator
from instruments.units import ureg as u
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

# pylint: disable=no-member,protected-access

test_srsdg645_name = make_name_test(ik.srs.SRSDG645)


# CHANNELS #


def test_srsdg645_channel_init():
    """
    _SRSDG645Channel: Ensure correct errors are raised during
    initialization if not coming from a DG class.
    """
    with pytest.raises(TypeError):
        ik.srs.srsdg645.SRSDG645.Channel(42, 0)


def test_srsdg645_channel_init_channel_value():
    """
    _SRSDG645Channel: Ensure the correct channel value is used when
    passing on a SRSDG645.Channels instance as the `chan` value.
    """
    ddg = ik.srs.SRSDG645.open_test()  # test connection
    chan = ik.srs.srsdg645.SRSDG645.Channels.B  # select a channel manually
    assert ik.srs.srsdg645.SRSDG645.Channel(ddg, chan)._chan == 3


def test_srsdg645_channel_delay():
    """
    SRSDG645: Get / set delay.
    """
    with expected_protocol(
        ik.srs.SRSDG645,
        ["DLAY?2", "DLAY 3,2,60", "DLAY 5,4,10"],
        ["0,42"],
    ) as ddg:
        ref, t = ddg.channel["A"].delay
        assert ref == ddg.Channels.T0
        assert abs((t - u.Quantity(42, "s")).magnitude) < 1e5
        ddg.channel["B"].delay = (ddg.channel["A"], u.Quantity(1, "minute"))
        ddg.channel["D"].delay = (ddg.channel["C"], 10)


# DG645 #


def test_srsdg645_init_gpib(mocker):
    """Initialize SRSDG645 with GPIB Communicator."""
    mock_gpib = mocker.MagicMock()
    comm = GPIBCommunicator(mock_gpib, 1)
    ik.srs.SRSDG645(comm)
    assert comm.strip == 2


def test_srsdg645_output_level():
    """
    SRSDG645: Checks getting/setting unitful output level.
    """
    with expected_protocol(
        ik.srs.SRSDG645,
        [
            "LAMP? 1",
            "LAMP 1,4.0",
        ],
        ["3.2"],
    ) as ddg:
        unit_eq(ddg.output["AB"].level_amplitude, u.Quantity(3.2, "V"))
        ddg.output["AB"].level_amplitude = 4.0


def test_srsdg645_output_offset():
    """
    SRSDG645: Checks getting/setting unitful output offset.
    """
    with expected_protocol(
        ik.srs.SRSDG645,
        [
            "LOFF? 1",
            "LOFF 1,2.0",
        ],
        ["1.2"],
    ) as ddg:
        unit_eq(ddg.output["AB"].level_offset, u.Quantity(1.2, "V"))
        ddg.output["AB"].level_offset = 2.0


def test_srsdg645_output_polarity():
    """
    SRSDG645: Checks getting/setting
    """
    with expected_protocol(ik.srs.SRSDG645, ["LPOL? 1", "LPOL 2,0"], ["1"]) as ddg:
        assert ddg.output["AB"].polarity == ddg.LevelPolarity.positive
        ddg.output["CD"].polarity = ddg.LevelPolarity.negative


def test_srsdg645_output_polarity_raise_type_error():
    """
    SRSDG645: Polarity setter with wrong input - raise type error.
    """
    with expected_protocol(ik.srs.SRSDG645, [], []) as ddg:
        with pytest.raises(TypeError):
            ddg.output["AB"].polarity = 1


def test_srsdg645_display():
    """
    SRSDG645: Set / get display mode.
    """
    with expected_protocol(ik.srs.SRSDG645, ["DISP?", "DISP 0,0"], ["12,3"]) as ddg:
        assert ddg.display == (ddg.DisplayMode.channel_levels, ddg.Channels.B)
        ddg.display = (ddg.DisplayMode.trigger_rate, ddg.Channels.T0)


def test_srsdg645_enable_adv_triggering():
    """
    SRSDG645: Set / get if advanced triggering is enabled.
    """
    with expected_protocol(ik.srs.SRSDG645, ["ADVT?", "ADVT 1"], ["0"]) as ddg:
        assert not ddg.enable_adv_triggering
        ddg.enable_adv_triggering = True


def test_srsdg645_trigger_rate():
    """
    SRSDG645: Set / get trigger rate.
    """
    with expected_protocol(
        ik.srs.SRSDG645, ["TRAT?", "TRAT 10000", "TRAT 1000"], ["+1000.000000"]
    ) as ddg:
        assert ddg.trigger_rate == u.Quantity(1000, u.Hz)
        ddg.trigger_rate = 10000
        ddg.trigger_rate = u.Quantity(1000, u.Hz)  # unitful send


def test_srsdg645_trigger_source():
    """
    SRSDG645: Set / get trigger source.
    """
    with expected_protocol(ik.srs.SRSDG645, ["TSRC?", "TSRC 1"], ["0"]) as ddg:
        assert ddg.trigger_source == ddg.TriggerSource.internal
        ddg.trigger_source = ddg.TriggerSource.external_rising


def test_srsdg645_holdoff():
    """
    SRSDG645: Set / get hold off.
    """
    with expected_protocol(
        ik.srs.SRSDG645, ["HOLD?", "HOLD 0", "HOLD 0.01"], ["+0.001001000000"]
    ) as ddg:
        assert u.Quantity(1001, u.us) == ddg.holdoff
        ddg.holdoff = 0
        ddg.holdoff = u.Quantity(10, u.ms)  # unitful hold off


def test_srsdg645_enable_burst_mode():
    """
    SRSDG645: Checks getting/setting of enabling burst mode.
    """
    with expected_protocol(ik.srs.SRSDG645, ["BURM?", "BURM 1"], ["0"]) as ddg:
        assert ddg.enable_burst_mode is False
        ddg.enable_burst_mode = True


def test_srsdg645_enable_burst_t0_first():
    """
    SRSDG645: Checks getting/setting of enabling T0 output on first
    in burst mode.
    """
    with expected_protocol(ik.srs.SRSDG645, ["BURT?", "BURT 1"], ["0"]) as ddg:
        assert ddg.enable_burst_t0_first is False
        ddg.enable_burst_t0_first = True


def test_srsdg645_burst_count():
    """
    SRSDG645: Checks getting/setting of enabling T0 output on first
    in burst mode.
    """
    with expected_protocol(ik.srs.SRSDG645, ["BURC?", "BURC 42"], ["10"]) as ddg:
        assert ddg.burst_count == 10
        ddg.burst_count = 42


def test_srsdg645_burst_period():
    """
    SRSDG645: Checks getting/setting of enabling T0 output on first
    in burst mode.
    """
    with expected_protocol(
        ik.srs.SRSDG645, ["BURP?", "BURP 13", "BURP 0.1"], ["100E-9"]
    ) as ddg:
        unit_eq(ddg.burst_period, u.Quantity(100, "ns").to(u.sec))
        ddg.burst_period = u.Quantity(13, "s")
        ddg.burst_period = 0.1


def test_srsdg645_burst_delay():
    """
    SRSDG645: Checks getting/setting of enabling T0 output on first
    in burst mode.
    """
    with expected_protocol(
        ik.srs.SRSDG645, ["BURD?", "BURD 42", "BURD 0.1"], ["0"]
    ) as ddg:
        unit_eq(ddg.burst_delay, u.Quantity(0, "s"))
        ddg.burst_delay = u.Quantity(42, "s")
        ddg.burst_delay = 0.1
