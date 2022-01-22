#!/usr/bin/env python
"""
Module containing tests for the Rigol DS1000
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import (
    expected_protocol,
    iterable_eq,
    make_name_test,
)

# TESTS ######################################################################

# pylint: disable=protected-access


test_rigolds1000_name = make_name_test(ik.rigol.RigolDS1000Series)


# TEST CHANNEL #


def test_channel_initialization():
    """Ensure correct initialization of channel object."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        channel = osc.channel[0]
        assert channel._parent is osc
        assert channel._idx == 1


def test_channel_coupling():
    """Get / set channel coupling."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN1:COUP?", ":CHAN2:COUP DC"], ["AC"]
    ) as osc:
        assert osc.channel[0].coupling == osc.channel[0].Coupling.ac
        osc.channel[1].coupling = osc.channel[1].Coupling.dc


def test_channel_bw_limit():
    """Get / set instrument bw limit."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN2:BWL?", ":CHAN1:BWL ON"], ["OFF"]
    ) as osc:
        assert not osc.channel[1].bw_limit
        osc.channel[0].bw_limit = True


def test_channel_display():
    """Get / set instrument display."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN2:DISP?", ":CHAN1:DISP ON"], ["OFF"]
    ) as osc:
        assert not osc.channel[1].display
        osc.channel[0].display = True


def test_channel_invert():
    """Get / set instrument invert."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN2:INV?", ":CHAN1:INV ON"], ["OFF"]
    ) as osc:
        assert not osc.channel[1].invert
        osc.channel[0].invert = True


def test_channel_filter():
    """Get / set instrument filter."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN2:FILT?", ":CHAN1:FILT ON"], ["OFF"]
    ) as osc:
        assert not osc.channel[1].filter
        osc.channel[0].filter = True


def test_channel_vernier():
    """Get / set instrument vernier."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":CHAN2:VERN?", ":CHAN1:VERN ON"], ["OFF"]
    ) as osc:
        assert not osc.channel[1].vernier
        osc.channel[0].vernier = True


def test_channel_name():
    """Get channel name - DataSource property."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        assert osc.channel[0].name == "CHAN1"


def test_channel_read_waveform():
    """Read waveform of channel object."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series,
        [":WAV:DATA? CHAN2"],
        [b"#210" + bytes.fromhex("00000001000200030004") + b"0"],
    ) as osc:
        expected = (0, 1, 2, 3, 4)
        if numpy:
            expected = numpy.array(expected)
        iterable_eq(osc.channel[1].read_waveform(), expected)


# TEST MATH #


def test_math_name():
    """Ensure correct naming of math object."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        assert osc.math.name == "MATH"


def test_math_read_waveform():
    """Read waveform of of math object."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series,
        [":WAV:DATA? MATH"],
        [b"#210" + bytes.fromhex("00000001000200030004") + b"0"],
    ) as osc:
        expected = (0, 1, 2, 3, 4)
        if numpy:
            expected = numpy.array(expected)
        iterable_eq(osc.math.read_waveform(), expected)


# TEST REF DATASOURCE #


def test_ref_name():
    """Ensure correct naming of ref object."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        assert osc.ref.name == "REF"


def test_ref_read_waveform_raises_error():
    """Ensure error raising when reading waveform of REF channel."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        with pytest.raises(NotImplementedError):
            osc.ref.read_waveform()


# TEST FURTHER PROPERTIES AND METHODS #


def test_acquire_type():
    """Get / Set acquire type."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":ACQ:TYPE?", ":ACQ:TYPE PEAK"], ["NORM"]
    ) as osc:
        assert osc.acquire_type == osc.AcquisitionType.normal
        osc.acquire_type = osc.AcquisitionType.peak_detect


def test_acquire_averages():
    """Get / Set acquire averages."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":ACQ:AVER?", ":ACQ:AVER 128"], ["16"]
    ) as osc:
        assert osc.acquire_averages == 16
        osc.acquire_averages = 128


def test_acquire_averages_bad_values():
    """Raise error when bad values encountered."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [], []) as osc:
        with pytest.raises(ValueError):
            osc.acquire_averages = 0
        with pytest.raises(ValueError):
            osc.acquire_averages = 1
        with pytest.raises(ValueError):
            osc.acquire_averages = 42
        with pytest.raises(ValueError):
            osc.acquire_averages = 257
        with pytest.raises(ValueError):
            osc.acquire_averages = 512


def test_force_trigger():
    """Force a trigger."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [":FORC"], []) as osc:
        osc.force_trigger()


def test_run():
    """Run the instrument."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [":RUN"], []) as osc:
        osc.run()


def test_stop():
    """Stop the instrument."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [":STOP"], []) as osc:
        osc.stop()


def test_panel_locked():
    """Get / set the panel_locked bool property."""
    with expected_protocol(
        ik.rigol.RigolDS1000Series, [":KEY:LOCK?", ":KEY:LOCK DIS"], ["ENAB"]
    ) as osc:
        assert osc.panel_locked
        osc.panel_locked = False


def test_release_panel():
    """Get / set the panel_locked bool property."""
    with expected_protocol(ik.rigol.RigolDS1000Series, [":KEY:FORC"], []) as osc:
        osc.release_panel()
