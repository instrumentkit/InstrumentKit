#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Thorlabs SC10
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises
import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, unit_eq

# TESTS ######################################################################


def test_sc10_name():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "id?"
        ],
        [
            "id?",
            "bloopbloop",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.name == "bloopbloop"


def test_sc10_enable():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "ens?",
            "ens=1"
        ],
        [
            "ens?",
            "0",
            ">ens=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.enable is False
        sc.enable = True


@raises(TypeError)
def test_sc10_enable_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.enable = 10


def test_sc10_repeat():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "rep?",
            "rep=10"
        ],
        [
            "rep?",
            "20",
            ">rep=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.repeat == 20
        sc.repeat = 10


@raises(ValueError)
def test_sc10_repeat_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.repeat = -1


def test_sc10_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "mode?",
            "mode=2"
        ],
        [
            "mode?",
            "1",
            ">mode=2",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.mode == ik.thorlabs.SC10.Mode.manual
        sc.mode = ik.thorlabs.SC10.Mode.auto


@raises(ValueError)
def test_sc10_mode_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.mode = "blo"


def test_sc10_trigger():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "trig?",
            "trig=1"
        ],
        [
            "trig?",
            "0",
            ">trig=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.trigger == 0
        sc.trigger = 1


def test_sc10_out_trigger():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "xto?",
            "xto=1"
        ],
        [
            "xto?",
            "0",
            ">xto=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.out_trigger == 0
        sc.out_trigger = 1


def test_sc10_open_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "open?",
            "open=10"
        ],
        [
            "open?",
            "20",
            ">open=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        unit_eq(sc.open_time, pq.Quantity(20, "ms"))
        sc.open_time = 10


def test_sc10_shut_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "shut?",
            "shut=10"
        ],
        [
            "shut?",
            "20",
            ">shut=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        unit_eq(sc.shut_time, pq.Quantity(20, "ms"))
        sc.shut_time = 10.0


def test_sc10_baud_rate():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "baud?",
            "baud=1"
        ],
        [
            "baud?",
            "0",
            ">baud=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.baud_rate == 9600
        sc.baud_rate = 115200


@raises(ValueError)
def test_sc10_baud_rate_error():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.baud_rate = 115201


def test_sc10_closed():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "closed?"
        ],
        [
            "closed?",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.closed


def test_sc10_interlock():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "interlock?"
        ],
        [
            "interlock?",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.interlock


def test_sc10_default():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "default"
        ],
        [
            "default",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.default()


def test_sc10_save():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "savp"
        ],
        [
            "savp",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.save()


def test_sc10_save_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "save"
        ],
        [
            "save",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.save_mode()


def test_sc10_restore():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "resp"
        ],
        [
            "resp",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.restore()
