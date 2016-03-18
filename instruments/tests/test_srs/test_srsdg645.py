#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the SRS DG645
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

test_srsdg645_name = make_name_test(ik.srs.SRSDG645)


def test_srsdg645_output_level():
    """
    SRSDG645: Checks getting/setting unitful ouput level.
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
        unit_eq(ddg.output['AB'].level_amplitude, pq.Quantity(3.2, "V"))
        ddg.output['AB'].level_amplitude = 4.0


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
        assert ddg.output['AB'].polarity == ddg.LevelPolarity.positive
        ddg.output['CD'].polarity = ddg.LevelPolarity.negative


def test_srsdg645_trigger_source():
    with expected_protocol(ik.srs.SRSDG645, "DLAY?2\nDLAY 3,2,60.0\n", "0,42\n") as ddg:
        ref, t = ddg.channel['A'].delay
        assert ref == ddg.Channels.T0
        assert abs((t - pq.Quantity(42, 's')).magnitude) < 1e5
        ddg.channel['B'].delay = (ddg.channel['A'], pq.Quantity(1, "minute"))
