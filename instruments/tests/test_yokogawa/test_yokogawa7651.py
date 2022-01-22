#!/usr/bin/env python
"""
Unit tests for the Yokogawa 7651 power supply
"""

# IMPORTS #####################################################################


import pytest

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol


# TESTS #######################################################################

# pylint: disable=protected-access

# TEST CHANNEL #


def test_channel_init():
    """Initialize of channel class."""
    with expected_protocol(ik.yokogawa.Yokogawa7651, [], []) as yok:
        assert yok.channel[0]._parent is yok
        assert yok.channel[0]._name == 0


def test_channel_mode():
    """Get / Set mode of the channel."""
    with expected_protocol(
        ik.yokogawa.Yokogawa7651, ["F5;", "E;", "F1;", "E;"], []  # trigger  # trigger
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"Mode is: {yok.channel[0].mode}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the "
            "operation mode."
        )

        # set first current, then voltage mode
        yok.channel[0].mode = yok.Mode.current
        yok.channel[0].mode = yok.Mode.voltage


def test_channel_invalid_mode_set():
    """Set mode to invalid value."""
    with expected_protocol(ik.yokogawa.Yokogawa7651, [], []) as yok:
        wrong_mode = 42
        with pytest.raises(TypeError) as exc_info:
            yok.channel[0].mode = wrong_mode
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "Mode setting must be a `Yokogawa7651.Mode` "
            "value, got {} instead.".format(type(wrong_mode))
        )


def test_channel_voltage():
    """Get / Set voltage of channel."""

    # values to set for test
    value_unitless = 5.0
    value_unitful = u.Quantity(500, u.mV)

    with expected_protocol(
        ik.yokogawa.Yokogawa7651,
        [
            "F1;\nE;",  # set voltage mode
            f"SA{value_unitless};",
            "E;",  # trigger
            "F1;\nE;",  # set voltage mode
            f"SA{value_unitful.to(u.volt).magnitude};",
            "E;",  # trigger
        ],
        [],
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"Voltage is: {yok.channel[0].voltage}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the "
            "output voltage setting."
        )

        # set first current, then voltage mode
        yok.channel[0].voltage = value_unitless
        yok.channel[0].voltage = value_unitful


def test_channel_current():
    """Get / Set current of channel."""

    # values to set for test
    value_unitless = 0.8
    value_unitful = u.Quantity(50, u.mA)

    with expected_protocol(
        ik.yokogawa.Yokogawa7651,
        [
            "F5;\nE;",  # set voltage mode
            f"SA{value_unitless};",
            "E;",  # trigger
            "F5;\nE;",  # set voltage mode
            f"SA{value_unitful.to(u.A).magnitude};",
            "E;",  # trigger
        ],
        [],
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"Current is: {yok.channel[0].current}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the "
            "output current setting."
        )

        # set first current, then current mode
        yok.channel[0].current = value_unitless
        yok.channel[0].current = value_unitful


def test_channel_output():
    """Get / Set output of channel."""
    with expected_protocol(
        ik.yokogawa.Yokogawa7651,
        ["O1;", "E;", "O0;", "E;"],  # turn output on  # turn output off
        [],
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"Output is: {yok.channel[0].output}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the " "output status."
        )

        # set first current, then current mode
        yok.channel[0].output = True
        yok.channel[0].output = False


# CLASS PROPERTIES #


def test_voltage():
    """Get / Set voltage of instrument."""

    # values to set for test
    value_unitless = 5.0
    value_unitful = u.Quantity(500, u.mV)

    with expected_protocol(
        ik.yokogawa.Yokogawa7651,
        [
            "F1;\nE;",  # set voltage mode
            f"SA{value_unitless};",
            "E;",  # trigger
            "F1;\nE;",  # set voltage mode
            f"SA{value_unitful.to(u.volt).magnitude};",
            "E;",  # trigger
        ],
        [],
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"Voltage is: {yok.voltage}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the "
            "output voltage setting."
        )

        # set first current, then voltage mode
        yok.voltage = value_unitless
        yok.voltage = value_unitful


def test_current():
    """Get / Set current of instrument."""

    # values to set for test
    value_unitless = 0.8
    value_unitful = u.Quantity(50, u.mA)

    with expected_protocol(
        ik.yokogawa.Yokogawa7651,
        [
            "F5;\nE;",  # set current mode
            f"SA{value_unitless};",
            "E;",  # trigger
            "F5;\nE;",  # set current mode
            f"SA{value_unitful.to(u.A).magnitude};",
            "E;",  # trigger
        ],
        [],
    ) as yok:
        # query
        with pytest.raises(NotImplementedError) as exc_info:
            print(f"current is: {yok.current}")
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == "This instrument does not support querying the "
            "output current setting."
        )

        # set first current, then current mode
        yok.current = value_unitless
        yok.current = value_unitful
