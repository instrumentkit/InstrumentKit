#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the SRS DG645
"""

# IMPORTS ####################################################################


import instruments.units as u

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

test_srsdg645_name = make_name_test(ik.srs.SRSDG645)


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
            [
                "3.2"
            ]
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
            [
                "1.2"
            ]
    ) as ddg:
        unit_eq(ddg.output["AB"].level_offset, u.Quantity(1.2, "V"))
        ddg.output["AB"].level_offset = 2.0


def test_srsdg645_output_polarity():
    """
    SRSDG645: Checks getting/setting
    """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "LPOL? 1",
                "LPOL 2,0"
            ],
            [
                "1"
            ]
    ) as ddg:
        assert ddg.output["AB"].polarity == ddg.LevelPolarity.positive
        ddg.output["CD"].polarity = ddg.LevelPolarity.negative


def test_srsdg645_trigger_source():
    with expected_protocol(ik.srs.SRSDG645, "DLAY?2\nDLAY 3,2,60.0\n", "0,42\n") as ddg:
        ref, t = ddg.channel["A"].delay
        assert ref == ddg.Channels.T0
        assert abs((t - u.Quantity(42, "s")).magnitude) < 1e5
        ddg.channel["B"].delay = (ddg.channel["A"], u.Quantity(1, "minute"))


def test_srsdg645_enable_burst_mode():
    """
    SRSDG645: Checks getting/setting of enabling burst mode.
    """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "BURM?",
                "BURM 1"
            ],
            [
                "0"
            ]
    ) as ddg:
        assert ddg.enable_burst_mode is False
        ddg.enable_burst_mode = True


def test_srsdg645_enable_burst_t0_first():
    """
        SRSDG645: Checks getting/setting of enabling T0 output on first
        in burst mode.
        """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "BURT?",
                "BURT 1"
            ],
            [
                "0"
            ]
    ) as ddg:
        assert ddg.enable_burst_t0_first is False
        ddg.enable_burst_t0_first = True


def test_srsdg645_burst_count():
    """
        SRSDG645: Checks getting/setting of enabling T0 output on first
        in burst mode.
        """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "BURC?",
                "BURC 42"
            ],
            [
                "10"
            ]
    ) as ddg:
        assert ddg.burst_count == 10
        ddg.burst_count = 42


def test_srsdg645_burst_period():
    """
        SRSDG645: Checks getting/setting of enabling T0 output on first
        in burst mode.
        """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "BURP?",
                "BURP 13"
            ],
            [
                "100E-9"
            ]
    ) as ddg:
        unit_eq(ddg.burst_period, u.Quantity(100, "ns").rescale(u.s))
        ddg.burst_period = u.Quantity(13, "s")


def test_srsdg645_burst_delay():
    """
        SRSDG645: Checks getting/setting of enabling T0 output on first
        in burst mode.
        """
    with expected_protocol(
            ik.srs.SRSDG645,
            [
                "BURD?",
                "BURD 42"
            ],
            [
                "0"
            ]
    ) as ddg:
        unit_eq(ddg.burst_delay, u.Quantity(0, "s"))
        ddg.burst_delay = u.Quantity(42, "s")
