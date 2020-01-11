#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Fluke 3000 FC multimeter
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

# TESTS ######################################################################

# Empty initialization sequence (scan function) that does not uncover
# any available Fluke 3000 FC device.
none_sequence = [
    "rfebd 01 0",
    "rfebd 02 0",
    "rfebd 03 0",
    "rfebd 04 0",
    "rfebd 05 0",
    "rfebd 06 0"
]
none_response = [
    "CR:Ack=2",
    "CR:Ack=2",
    "CR:Ack=2",
    "CR:Ack=2",
    "CR:Ack=2",
    "CR:Ack=2"
]

# Default initialization sequence (scan function) that binds a multimeter
# to port 1 and a temperature module to port 2.
init_sequence = [
    "rfebd 01 0",   # 1
    "rfgus 01",     # 2
    "rfebd 02 0",   # 3
    "rfgus 02",     # 4
    "rfebd 03 0",   # 5
    "rfebd 04 0",   # 6
    "rfebd 05 0",   # 7
    "rfebd 06 0"    # 8
]
init_response = [
    "CR:Ack=0:RFEBD",   # 1.1
    "ME:R:S#=01:DCC=012:PH=64",  # 1.2
    "CR:Ack=0:RFGUS",   # 2.1
    "ME:R:S#=01:DCC=004:PH=46333030304643",  # 2.2
    "CR:Ack=0:RFEBD",   # 3.1
    "ME:R:S#=01:DCC=012:PH=64",  # 3.2
    "CR:Ack=0:RFGUS",   # 4.1
    "ME:R:S#=02:DCC=004:PH=54333030304643",  # 4.2
    "CR:Ack=2",  # 5
    "CR:Ack=2",  # 6
    "CR:Ack=2",  # 7
    "CR:Ack=2"   # 8
]


def test_mode():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence +
        [
            "rfemd 01 1",   # 1
            "rfemd 01 2"    # 2
        ],
        init_response +
        [
            "CR:Ack=0:RFEMD",   # 1.1
            "ME:R:S#=01:DCC=010:PH=00000006020C0600",   # 1.2
            "CR:Ack=0:RFEMD"    # 2
        ],
        "\r"
    ) as inst:
        assert inst.mode == inst.Mode.voltage_dc


def test_connect():
    with expected_protocol(
        ik.fluke.Fluke3000,
        none_sequence +
        [
            "ri",   # 1
            "rfsm 1",   # 2
            "rfdis",    # 3
        ] +
        init_sequence,
        none_response +
        [
            "CR:Ack=0:RI",  # 1.1
            "SI:PON=Power On",  # 1.2
            "RE:O",  # 1.3
            "CR:Ack=0:RFSM:Radio On Master",    # 2.1
            "RE:M",  # 2.2
            "CR:Ack=0:RFDIS",   # 3.1
            "ME:S",  # 3.2
            "ME:D:010200000000",  # 3.3
        ] +
        init_response,
        "\r"
    ) as inst:
        assert inst.positions[ik.fluke.Fluke3000.Module.m3000] == 1
        assert inst.positions[ik.fluke.Fluke3000.Module.t3000] == 2


def test_scan():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence,
        init_response,
        "\r"
    ) as inst:
        assert inst.positions[ik.fluke.Fluke3000.Module.m3000] == 1
        assert inst.positions[ik.fluke.Fluke3000.Module.t3000] == 2


def test_reset():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence +
        [
            "ri",   # 1
            "rfsm 1"   # 2
        ],
        init_response +
        [
            "CR:Ack=0:RI",  # 1.1
            "SI:PON=Power On",  # 1.2
            "RE:O",  # 1.3
            "CR:Ack=0:RFSM:Radio On Master",    # 2.1
            "RE:M"  # 2.2
        ],
        "\r"
    ) as inst:
        inst.reset()


def test_measure():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence +
        [
            "rfemd 01 1",   # 1
            "rfemd 01 2",   # 2
            "rfemd 02 0"    # 3
        ],
        init_response +
        [
            "CR:Ack=0:RFEMD",   # 1.1
            "ME:R:S#=01:DCC=010:PH=FD010006020C0600",   # 1.2
            "CR:Ack=0:RFEMD",   # 2
            "CR:Ack=0:RFEMD",   # 3.1
            "ME:R:S#=02:DCC=010:PH=FD00C08207220000"    # 3.2
        ],
        "\r"
    ) as inst:
        assert inst.measure(inst.Mode.voltage_dc) == 0.509 * pq.volt
        assert inst.measure(inst.Mode.temperature) == -25.3 * pq.celsius
