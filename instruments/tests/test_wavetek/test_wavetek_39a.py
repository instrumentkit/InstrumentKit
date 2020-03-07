#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for Wavetek 39A
"""

# IMPORTS ####################################################################


import instruments.units as u

import instruments as ik
from instruments.tests import expected_protocol, make_name_test

# TESTS ######################################################################


def test_wavetek39a_amplitude():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "AMPUNIT VPP",
                "AMPL 2.0",
                "AMPUNIT VPP",
                "AMPL 4.0",
                "AMPUNIT VPP",
                "AMPL 2.0",
                "AMPUNIT VRMS",
                "AMPL 3.0",
                "AMPUNIT DBM",
                "AMPL 1.5"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.amplitude = 2 * u.V
        fg.amplitude = 4 * u.V
        fg.amplitude = (2 * u.V, fg.VoltageMode.peak_to_peak)
        fg.amplitude = (3.0 * u.V, fg.VoltageMode.rms)
        fg.amplitude = (1.5 * u.V, fg.VoltageMode.dBm)


def test_wavetek39a_frequency():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "WAVFREQ 1.005000e+02"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.frequency = 100.5 * u.Hz

        
def test_wavetek39a_period():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "WAVPER 1.200000e-02"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.period = 12 * u.ms
        

def test_wavetek39a_function():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "WAVE SINE",
                "WAVE SQUARE",
                "WAVE TRIANG",
                "WAVE DC",
                "WAVE POSRMP",
                "WAVE NEGRMP",
                "WAVE COSINE",
                "WAVE HAVSIN",
                "WAVE HAVCOS",
                "WAVE SINC",
                "WAVE PULSE",
                "WAVE PULSTRN",
                "WAVE ARB",
                "WAVE SEQ"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.function = fg.Function.sinusoid
        fg.function = fg.Function.square
        fg.function = fg.Function.triangle
        fg.function = fg.Function.dc
        fg.function = fg.Function.positive_ramp
        fg.function = fg.Function.negative_ramp
        fg.function = fg.Function.cosine
        fg.function = fg.Function.haversine
        fg.function = fg.Function.havercosine
        fg.function = fg.Function.sinc
        fg.function = fg.Function.pulse
        fg.function = fg.Function.pulse_train
        fg.function = fg.Function.arbitrary
        fg.function = fg.Function.sequence
        

def test_wavetek39a_offset():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "DCOFFS 4.321000e-01"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.offset = 0.4321 * u.V


def test_wavetek39a_output():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "OUTPUT ON"
                "OUTPUT OFF"
                "OUTPUT NORMAL"
                "OUTPUT INVERT"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.output = True
        fg.output = False
        fg.output_mode = fg.OutputMode.normal
        fg.output_mode = fg.OutputMode.invert


def test_wavetek39a_zload():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "ZLOAD 50"
                "ZLOAD 600"
                "ZLOAD OPEN"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.zload = fg.ZLoad.Z50
        fg.zload = fg.ZLoad.Z600
        fg.zload = fg.ZLoad.OPEN

        
def test_wavetek39a_mode():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "MODE CONT"
                "MODE GATE"
                "MODE TRIG"
                "MODE SWEEP"
                "MODE TONE"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.mode = fg.Mode.cont
        fg.mode = fg.Mode.gate
        fg.mode = fg.Mode.trig
        fg.mode = fg.Mode.sweep
        fg.mode = fg.Mode.tone

        
def test_wavetek39a_syncout():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "SYNCOUT ON"
                "SYNCOUT OFF"
                "SYNCOUT AUTO"
                "SYNCOUT WFMSYNC"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.syncout = True
        fg.syncout = False
        fg.syncout_mode = fg.SyncOutMode.auto
        fg.syncout_mode = fg.SyncOutMode.waveform_sync

        
def test_wavetek39a_trigger():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "TRIGIN INT",
                "TRIGIN EXT",
                "TRIGIN MAN",
                "TRIGIN POS",
                "TRIGIN NEG",
                "TRIGPER 1.000000e-03",
            ], [
            ],
            sep = ""
    ) as fg:
        fg.trigger_input = fg.TriggerInput.internal
        fg.trigger_input = fg.TriggerInput.external
        fg.trigger_input = fg.TriggerInput.manual
        fg.trigger_input_edge = fg.TriggerInputEdge.positive
        fg.trigger_input_edge = fg.TriggerInputEdge.negative
        fg.trigger_period = 1 * u.ms

        
def test_wavetek39a_filter():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "FILTER AUTO",
                "FILTER EL10",
                "FILTER EL16",
                "FILTER BESS",
                "FILTER NONE"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.filter = fg.Filter.auto
        fg.filter = fg.Filter.elliptic10
        fg.filter = fg.Filter.elliptic16
        fg.filter = fg.Filter.Bessel
        fg.filter = fg.Filter.none

def test_wavetek39a_local():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "BEEP"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.beep()


def test_wavetek39a_local():
    with expected_protocol(
            ik.wavetek.Wavetek39A,
            [
                "LOCAL"
            ], [
            ],
            sep = ""
    ) as fg:
        fg.local()

