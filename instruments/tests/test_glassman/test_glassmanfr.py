#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Glassman FR power supply
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from builtins import round

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################

def set_defaults(inst):
    """
    Sets default values for the voltage and current range of the Glassman FR
    to be used to test the voltage and current property getters/setters.
    """
    inst.voltage_max = 50.0 * pq.kilovolt
    inst.current_max = 6.0 * pq.milliamp
    inst.polarity = +1


def test_channel():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [],
        [],
        "\r"
    ) as inst:
        assert len(inst.channel) == 1
        assert inst.channel[0] == inst


def test_voltage():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q51",
            "\x01S3330000000001CD"
        ],
        [
            "R00000000000040",
            "A"
        ],
        "\r"
    ) as inst:
        set_defaults(inst)
        inst.voltage = 10.0 * pq.kilovolt
        assert inst.voltage == 10.0 * pq.kilovolt


def test_current():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q51",
            "\x01S0003330000001CD"
        ],
        [
            "R00000000000040",
            "A"
        ],
        "\r"
    ) as inst:
        set_defaults(inst)
        inst.current = 1.2 * pq.milliamp
        assert inst.current == 1.2 * pq.milliamp


def test_voltage_sense():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q51"
        ],
        [
            "R10A00000010053"
        ],
        "\r"
    ) as inst:
        set_defaults(inst)
        assert round(inst.voltage_sense) == 13.0 * pq.kilovolt


def test_current_sense():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q51"
        ],
        [
            "R0001550001004C"
        ],
        "\r"
    ) as inst:
        set_defaults(inst)
        assert inst.current_sense == 2.0 * pq.milliamp


def test_mode():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q51",
            "\x01Q51"
        ],
        [
            "R00000000000040",
            "R00000000010041"
        ],
        "\r"
    ) as inst:
        assert inst.mode == inst.Mode.voltage
        assert inst.mode == inst.Mode.current


def test_output():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01S0000000000001C4",
            "\x01Q51",
            "\x01S0000000000002C5",
            "\x01Q51"
        ],
        [
            "A",
            "R00000000000040",
            "A",
            "R00000000040044"
        ],
        "\r"
    ) as inst:
        inst.output = False
        assert not inst.output
        inst.output = True
        assert inst.output


def test_version():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01V56"
        ],
        [
            "B1465"
        ],
        "\r"
    ) as inst:
        assert inst.version == "14"


def test_device_timeout():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01C073",
            "\x01C174"
        ],
        [
            "A",
            "A"
        ],
        "\r"
    ) as inst:
        inst.device_timeout = True
        assert inst.device_timeout
        inst.device_timeout = False
        assert not inst.device_timeout


def test_sendcmd():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01123ABC5C"
        ],
        [],
        "\r"
    ) as inst:
        inst.sendcmd("123ABC")


def test_query():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01Q123ABCAD"
        ],
        [
            "R123ABC5C"
        ],
        "\r"
    ) as inst:
        inst.query("Q123ABC")


def test_reset():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01S0000000000004C7"
        ],
        [
            "A"
        ],
        "\r"
    ) as inst:
        inst.reset()


def test_set_status():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        [
            "\x01S3333330000002D7",
            "\x01Q51"
        ],
        [
            "A",
            "R00000000040044"
        ],
        "\r"
    ) as inst:
        set_defaults(inst)
        inst.set_status(voltage=10*pq.kilovolt, current=1.2*pq.milliamp, output=True)
        assert inst.output
        assert inst.voltage == 10 * pq.kilovolt
        assert inst.current == 1.2 * pq.milliamp
