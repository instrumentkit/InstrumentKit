# -*- coding: utf-8 -*-
"""
Tests the Cryomagnetics LM 510 liquid cryogen level meter
"""
# IMPORTS #####################################################################
from __future__ import absolute_import

import quantities as pq
from nose.tools import eq_

from instruments.cryomagnetics import CryomagneticsLM510
from instruments.tests import expected_protocol

# TEST CASES ##################################################################


def test_default_channel():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "CHAN?"
        ],
        [
            "1"
        ]
    ) as inst:
        assert inst.default_channel == 1


def test_default_channel_setter():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "CHAN 1",
            "CHAN?"
        ],
        [
            "",
            "1"
        ]
    ) as inst:
        inst.default_channel = 1
        eq_(1, inst.default_channel)


def test_status_byte():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "*STB?"
        ],
        [
            chr(1)
        ]
    ) as inst:
        eq_(
            chr(1).encode('ascii'),
            inst.status_byte
        )


def test_channel_1_data_ready():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "*STB?"
        ],
        [
            chr(17)
        ]
    ) as inst:
        assert inst.channel[0].data_ready is True


def test_channel_2_data_ready():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "*STB?"
        ],
        [
            chr(4)
        ]
    ) as inst:
        assert inst.channel[1].data_ready is True


def test_channel_1_measurement_data_selector():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "MEAS? 1"
        ],
        [
            "5.42 cm"
        ]
    ) as inst:
        eq_(
            5.42 * pq.cm,
            inst.channel[0].measurement
        )


def test_channel_2_measurement_data_selector():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "MEAS? 2"
        ],
        [
            "102.321 cm"
        ]
    ) as inst:
        eq_(
            102.321 * pq.cm,
            inst.channel[1].measurement
        )


def test_reset():
    with expected_protocol(
        CryomagneticsLM510,
        [
            "*RST"
        ],
        [
            ""
        ]
    ) as inst:
        inst.reset()
