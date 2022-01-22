#!/usr/bin/env python
"""
Unit tests for the Keithley 6220 constant current supply
"""

# IMPORTS #####################################################################


import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_channel():
    inst = ik.keithley.Keithley6220.open_test()
    assert inst.channel[0] == inst


def test_voltage():
    """Raise NotImplementedError when getting / setting voltage."""
    with expected_protocol(ik.keithley.Keithley6220, [], []) as inst:
        with pytest.raises(NotImplementedError) as err_info:
            _ = inst.voltage
        err_msg = err_info.value.args[0]
        assert err_msg == "The Keithley 6220 does not support voltage " "settings."
        with pytest.raises(NotImplementedError) as err_info:
            inst.voltage = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "The Keithley 6220 does not support voltage " "settings."


def test_current():
    with expected_protocol(
        ik.keithley.Keithley6220,
        ["SOUR:CURR?", f"SOUR:CURR {0.05:e}"],
        [
            "0.1",
        ],
    ) as inst:
        assert inst.current == 100 * u.milliamp
        assert inst.current_min == -105 * u.milliamp
        assert inst.current_max == +105 * u.milliamp
        inst.current = 50 * u.milliamp


def test_disable():
    with expected_protocol(ik.keithley.Keithley6220, ["SOUR:CLE:IMM"], []) as inst:
        inst.disable()
