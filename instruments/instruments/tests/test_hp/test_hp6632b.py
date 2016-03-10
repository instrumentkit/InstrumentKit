#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the HP 6632b power supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS #######################################################################

test_scpi_multimeter_name = make_name_test(ik.hp.HP6632b)


def test_hp6632b_display_textmode():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DISP:MODE?",
            "DISP:MODE TEXT"
        ], [
            "NORM"
        ]
    ) as psu:
        assert psu.display_textmode is False
        psu.display_textmode = True


def test_hp6632b_display_text():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            'DISP:TEXT "TEST"',
            'DISP:TEXT "TEST AAAAAAAAAA"'
        ],
        []
    ) as psu:
        assert psu.display_text("TEST") == "TEST"
        assert psu.display_text("TEST AAAAAAAAAAAAAAAA") == "TEST AAAAAAAAAA"


def test_hp6632b_output():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP?",
            "OUTP 1"
        ], [
            "0"
        ]
    ) as psu:
        assert psu.output is False
        psu.output = True


def test_hp6632b_voltage():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT?",
            "VOLT {:e}".format(1)
        ], [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.voltage, 10 * pq.volt)
        psu.voltage = 1.0 * pq.volt


def test_hp6632b_voltage_sense():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "MEAS:VOLT?",
        ], [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.voltage_sense, 10 * pq.volt)


def test_hp6632b_overvoltage():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:PROT?",
            "VOLT:PROT {:e}".format(1)
        ], [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.overvoltage, 10 * pq.volt)
        psu.overvoltage = 1.0 * pq.volt


def test_hp6632b_current():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR?",
            "CURR {:e}".format(1)
        ], [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.current, 10 * pq.amp)
        psu.current = 1.0 * pq.amp


def test_hp6632b_current_sense():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "MEAS:CURR?",
        ], [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.current_sense, 10 * pq.amp)


def test_hp6632b_overcurrent():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR:PROT:STAT?",
            "CURR:PROT:STAT 1"
        ], [
            "0"
        ]
    ) as psu:
        assert psu.overcurrent is False
        psu.overcurrent = True


def test_hp6632b_current_sense_range():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:CURR:RANGE?",
            "SENS:CURR:RANGE {:e}".format(1)
        ], [
            "0.05"
        ]
    ) as psu:
        unit_eq(psu.current_sense_range, 0.05 * pq.amp)
        psu.current_sense_range = 1 * pq.amp


def test_hp6632b_output_dfi_source():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:DFI:SOUR?",
            "OUTP:DFI:SOUR QUES"
        ], [
            "OPER"
        ]
    ) as psu:
        assert psu.output_dfi_source == psu.DFISource.operation
        psu.output_dfi_source = psu.DFISource.questionable


def test_hp6632b_output_remote_inhibit():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:RI:MODE?",
            "OUTP:RI:MODE LATC"
        ], [
            "LIVE"
        ]
    ) as psu:
        assert psu.output_remote_inhibit == psu.RemoteInhibit.live
        psu.output_remote_inhibit = psu.RemoteInhibit.latching


def test_hp6632b_digital_function():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DIG:FUNC?",
            "DIG:FUNC DIG"
        ], [
            "RIDF"
        ]
    ) as psu:
        assert psu.digital_function == psu.DigitalFunction.remote_inhibit
        psu.digital_function = psu.DigitalFunction.data


def test_hp6632b_digital_data():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DIG:DATA?",
            "DIG:DATA 1"
        ], [
            "5"
        ]
    ) as psu:
        assert psu.digital_data == 5
        psu.digital_data = 1


def test_hp6632b_sense_sweep_points():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:SWE:POIN?",
            "SENS:SWE:POIN {:e}".format(2048)
        ], [
            "5"
        ]
    ) as psu:
        assert psu.sense_sweep_points == 5
        psu.sense_sweep_points = 2048


def test_hp6632b_sense_sweep_interval():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:SWE:TINT?",
            "SENS:SWE:TINT {:e}".format(1e-05)
        ], [
            "1.56e-05"
        ]
    ) as psu:
        unit_eq(psu.sense_sweep_interval, 1.56e-05 * pq.second)
        psu.sense_sweep_interval = 1e-05 * pq.second


def test_hp6632b_sense_window():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:WIND?",
            "SENS:WIND RECT"
        ], [
            "HANN"
        ]
    ) as psu:
        assert psu.sense_window == psu.SenseWindow.hanning
        psu.sense_window = psu.SenseWindow.rectangular


def test_hp6632b_output_protection_delay():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:PROT:DEL?",
            "OUTP:PROT:DEL {:e}".format(5e-02)
        ], [
            "8e-02"
        ]
    ) as psu:
        unit_eq(psu.output_protection_delay, 8e-02 * pq.second)
        psu.output_protection_delay = 5e-02 * pq.second


def test_hp6632b_voltage_alc_bandwidth():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:ALC:BAND?",
        ], [
            "6e4"
        ]
    ) as psu:
        assert psu.voltage_alc_bandwidth == psu.ALCBandwidth.fast


def test_hp6632b_voltage_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:TRIG?",
            "VOLT:TRIG {:e}".format(1)
        ], [
            "1e+0"
        ]
    ) as psu:
        unit_eq(psu.voltage_trigger, 1 * pq.volt)
        psu.voltage_trigger = 1 * pq.volt


def test_hp6632b_current_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR:TRIG?",
            "CURR:TRIG {:e}".format(0.1)
        ], [
            "1e-01"
        ]
    ) as psu:
        unit_eq(psu.current_trigger, 0.1 * pq.amp)
        psu.current_trigger = 0.1 * pq.amp


def test_hp6632b_init_output_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "INIT:NAME TRAN",
        ],
        []
    ) as psu:
        psu.init_output_trigger()


def test_hp6632b_abort_output_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "ABORT",
        ],
        []
    ) as psu:
        psu.abort_output_trigger()


def test_hp6632b_check_error_queue():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SYST:ERR?",
            "SYST:ERR?",
        ], [
            '-222,"Data out of range"',
            '+0,"No error"'
        ]
    ) as psu:
        err_queue = psu.check_error_queue()
        assert err_queue == [
            psu.ErrorCodes.data_out_of_range
        ], "got {}".format(err_queue)
