#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the SRS 830 lock-in amplifier
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_frequency_source():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FMOD?",
            "FMOD 0"
        ],
        [
            "1",
        ]
    ) as inst:
        assert inst.frequency_source == inst.FreqSource.internal
        inst.frequency_source = inst.FreqSource.external


def test_frequency():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FREQ?",
            "FREQ {:e}".format(1000)
        ],
        [
            "12.34",
        ]
    ) as inst:
        assert inst.frequency == 12.34 * pq.Hz
        inst.frequency = 1 * pq.kHz


def test_phase():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "PHAS?",
            "PHAS {:e}".format(10)
        ],
        [
            "-45",
        ]
    ) as inst:
        assert inst.phase == -45 * pq.degrees
        inst.phase = 10 * pq.degrees


def test_amplitude():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SLVL?",
            "SLVL {:e}".format(1)
        ],
        [
            "0.1",
        ]
    ) as inst:
        assert inst.amplitude == 0.1 * pq.V
        inst.amplitude = 1 * pq.V


def test_input_shield_ground():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "IGND?",
            "IGND 1"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.input_shield_ground is False
        inst.input_shield_ground = True


def test_coupling():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "ICPL?",
            "ICPL 0"
        ],
        [
            "1",
        ]
    ) as inst:
        assert inst.coupling == inst.Coupling.dc
        inst.coupling = inst.Coupling.ac


def test_sample_rate():  # sends index of VALID_SAMPLE_RATES
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SRAT?",
            "SRAT?",
            "SRAT {:d}".format(5),
            "SRAT 14"
        ],
        [
            "8",
            "14"
        ]
    ) as inst:
        assert inst.sample_rate == 16 * pq.Hz
        assert inst.sample_rate == "trigger"
        inst.sample_rate = 2
        inst.sample_rate = "trigger"  # pylint: disable=redefined-variable-type


@raises(ValueError)
def test_sample_rate_invalid():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.sample_rate = "foobar"


def test_buffer_mode():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SEND?",
            "SEND 1"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.buffer_mode == inst.BufferMode.one_shot
        inst.buffer_mode = inst.BufferMode.loop


def test_num_data_points():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SPTS?"
        ],
        [
            "5",
        ]
    ) as inst:
        assert inst.num_data_points == 5


def test_data_transfer():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FAST?",
            "FAST 2"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.data_transfer is False
        inst.data_transfer = True


def test_auto_offset():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "AOFF 1",
            "AOFF 1"
        ],
        []
    ) as inst:
        inst.auto_offset(inst.Mode.x)
        inst.auto_offset("x")


@raises(ValueError)
def test_auto_offset_invalid():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "AOFF 1",
        ],
        []
    ) as inst:
        inst.auto_offset(inst.Mode.theta)


def test_auto_phase():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "APHS"
        ],
        []
    ) as inst:
        inst.auto_phase()


def test_init():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "REST",
            "SRAT 5",
            "SEND 1"
        ],
        []
    ) as inst:
        inst.init(sample_rate=2, buffer_mode=inst.BufferMode.loop)


def test_start_data_transfer():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FAST 2",
            "STRD"
        ],
        []
    ) as inst:
        inst.start_data_transfer()


def test_take_measurement():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "REST",
            "SRAT 4",
            "SEND 0",
            "FAST 2",
            "STRD",
            "PAUS",
            "SPTS?",
            "SPTS?",
            "TRCA?1,0,2",
            "SPTS?",
            "TRCA?2,0,2"
        ],
        [
            "2",
            "2",
            "1.234,5.678",
            "2",
            "0.456,5.321"
        ]
    ) as inst:
        resp = inst.take_measurement(sample_rate=1, num_samples=2)
        np.testing.assert_array_equal(resp, [[1.234, 5.678], [0.456, 5.321]])


@raises(ValueError)
def test_take_measurement_invalid_num_samples():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        _ = inst.take_measurement(sample_rate=1, num_samples=16384)


def test_set_offset_expand():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "OEXP 1,0,0"
        ],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.x, offset=0, expand=1)


def test_set_offset_expand_mode_as_str():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "OEXP 1,0,0"
        ],
        []
    ) as inst:
        inst.set_offset_expand(mode="x", offset=0, expand=1)


@raises(ValueError)
def test_set_offset_expand_invalid_mode():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.theta, offset=0, expand=1)


@raises(ValueError)
def test_set_offset_expand_invalid_offset():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.x, offset=106, expand=1)


@raises(ValueError)
def test_set_offset_expand_invalid_expand():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.x, offset=0, expand=5)


@raises(TypeError)
def test_set_offset_expand_invalid_type_offset():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.x, offset="derp", expand=1)


@raises(TypeError)
def test_set_offset_expand_invalid_type_expand():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_offset_expand(mode=inst.Mode.x, offset=0, expand="derp")


def test_start_scan():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "STRD"
        ],
        []
    ) as inst:
        inst.start_scan()


def test_pause():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "PAUS"
        ],
        []
    ) as inst:
        inst.pause()


def test_data_snap():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SNAP? 1,2"
        ],
        [
            "1.234,9.876"
        ]
    ) as inst:
        data = inst.data_snap(mode1=inst.Mode.x, mode2=inst.Mode.y)
        expected = [1.234, 9.876]
        np.testing.assert_array_equal(data, expected)


def test_data_snap_mode_as_str():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SNAP? 1,2"
        ],
        [
            "1.234,9.876"
        ]
    ) as inst:
        data = inst.data_snap(mode1='x', mode2='y')
        expected = [1.234, 9.876]
        np.testing.assert_array_equal(data, expected)


@raises(ValueError)
def test_data_snap_invalid_snap_mode1():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        _ = inst.data_snap(mode1=inst.Mode.xnoise, mode2=inst.Mode.y)


@raises(ValueError)
def test_data_snap_invalid_snap_mode2():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        _ = inst.data_snap(mode1=inst.Mode.x, mode2=inst.Mode.ynoise)


@raises(ValueError)
def test_data_snap_identical_modes():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        _ = inst.data_snap(mode1=inst.Mode.x, mode2=inst.Mode.x)


def test_read_data_buffer():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SPTS?",
            "TRCA?1,0,2"
        ],
        [
            "2",
            "1.234,9.876"
        ]
    ) as inst:
        data = inst.read_data_buffer(channel=inst.Mode.ch1)
        expected = [1.234, 9.876]
        np.testing.assert_array_equal(data, expected)


def test_read_data_buffer_mode_as_str():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SPTS?",
            "TRCA?1,0,2"
        ],
        [
            "2",
            "1.234,9.876"
        ]
    ) as inst:
        data = inst.read_data_buffer(channel="ch1")
        expected = [1.234, 9.876]
        np.testing.assert_array_equal(data, expected)


@raises(ValueError)
def test_read_data_buffer_invalid_mode():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        _ = inst.read_data_buffer(channel=inst.Mode.x)


def test_clear_data_buffer():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "REST"
        ],
        []
    ) as inst:
        inst.clear_data_buffer()


def test_set_channel_display():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "DDEF 1,0,0"
        ],
        []
    ) as inst:
        inst.set_channel_display(
            channel=inst.Mode.ch1,
            display=inst.Mode.x,
            ratio=inst.Mode.none
        )


def test_set_channel_display_params_as_str():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "DDEF 1,0,0"
        ],
        []
    ) as inst:
        inst.set_channel_display(
            channel="ch1",
            display="x",
            ratio="none"
        )


@raises(ValueError)
def test_set_channel_display_invalid_channel():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_channel_display(
            channel=inst.Mode.x,
            display=inst.Mode.x,
            ratio=inst.Mode.none
        )


@raises(ValueError)
def test_set_channel_display_invalid_display():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_channel_display(
            channel=inst.Mode.ch1,
            display=inst.Mode.y,  # y is only valid for ch2, not ch1!
            ratio=inst.Mode.none
        )


@raises(ValueError)
def test_set_channel_display_invalid_ratio():
    with expected_protocol(
        ik.srs.SRS830,
        [],
        []
    ) as inst:
        inst.set_channel_display(
            channel=inst.Mode.ch1,
            display=inst.Mode.x,
            ratio=inst.Mode.xnoise
        )
