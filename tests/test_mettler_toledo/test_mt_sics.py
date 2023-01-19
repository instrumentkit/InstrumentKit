#!/usr/bin/env python
"""
Tests for the Mettler Toledo Standard Interface Command Set (SICS).
"""

# IMPORTS #####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol


# TESTS #######################################################################


def test_clear_tare():
    """Clear the tare value."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["TAC"], ["TAC A"], "\r\n"
    ) as inst:
        inst.clear_tare()


def test_reset():
    """Reset the balance."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["@"], ['@ A "123456789"'], "\r\n"
    ) as inst:
        inst.reset()


def test_tare():
    """Tare the balance."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["T"], ["T A 2.486 g"], "\r\n"
    ) as inst:
        inst.tare()


def test_tare_immediately():
    """Tare the balance immediately."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["TI"], ["TI A 1.234 g"], "\r\n"
    ) as inst:
        inst.tare(immediately=True)


def test_zero():
    """Zero the balance."""
    with expected_protocol(ik.mettler_toledo.MTSICS, ["Z"], ["Z A"], "\r\n") as inst:
        inst.zero()


def test_zero_immidiately():
    """Zero the balance immediately."""
    with expected_protocol(ik.mettler_toledo.MTSICS, ["ZI"], ["ZI A"], "\r\n") as inst:
        inst.zero(immediately=True)


@pytest.mark.parametrize("err", ["I", "L", "+", "-"])
def test_command_error_checking(err):
    """Raise OSError if command encounters an error."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["S"], [f"S {err}"], "\r\n"
    ) as inst:
        with pytest.raises(OSError):
            inst.weight


@pytest.mark.parametrize("err", ["ES", "ET", "EL"])
def test_general_error_checking(err):
    """Raise OSError if general error encountered."""
    with expected_protocol(ik.mettler_toledo.MTSICS, ["S"], [f"{err}"], "\r\n") as inst:
        with pytest.raises(OSError):
            inst.weight


# PROPERTIES #


def test_mt_sics():
    """Get MT-SICS level and MT-SICS versions."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["I1"], ["I1 A 01 2.00 2.00 2.00 1.0"], "\r\n"
    ) as inst:
        assert inst.mt_sics == ["01", "2.00", "2.00", "2.00", "1.0"]


def test_mt_sics_commands():
    """Get all available MT-SICS implemented commands."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["I0"], ['0 B 0 "I0"\r\nI0 B 1 "D"'], "\r\n"
    ) as inst:
        assert inst.mt_sics_commands == [["0", "I0"], ["1", "D"]]


def test_mt_sics_commands_timeout(mocker):
    """Ensure that timeout error is caught appropriately."""
    inst_class = ik.mettler_toledo.MTSICS
    # mock reading raises timeout error
    os_error_mock = mocker.Mock()
    os_error_mock.side_effect = OSError
    mocker.patch.object(inst_class, "read", os_error_mock)

    with expected_protocol(inst_class, ["I0"], [], "\r\n") as inst:
        timeout = inst.timeout
        assert inst.mt_sics_commands == []
        assert inst.timeout == timeout


def test_name():
    """Get / Set balance name."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS,
        ['I10 "My Balance"', "I10"],
        ['I10 A "Balance"', 'I10 A "My Balance"'],
        "\r\n",
    ) as inst:
        inst.name = "My Balance"
        assert inst.name == "My Balance"


def test_name_too_long():
    """Raise ValueError if name is too long."""
    with expected_protocol(ik.mettler_toledo.MTSICS, [], [], "\r\n") as inst:
        with pytest.raises(ValueError):
            inst.name = "My Balance is too long"


def test_serial_number():
    """Get the serial number of the instrument."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["I4"], ["I4 A 0123456789"], "\r\n"
    ) as inst:
        assert inst.serial_number == "0123456789"


def test_tare_value():
    """Set / get the tare value."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS,
        ["TA 2.486 g", "TA"],
        ["TA A 2.486 g", "TA A 2.486 g"],
        "\r\n",
    ) as inst:
        inst.tare_value = u.Quantity(2.486, u.gram)
        assert inst.tare_value == u.Quantity(2.486, u.gram)


def test_weight():
    """Get the stable weight."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["S"], ["S A 1.234 g"], "\r\n"
    ) as inst:
        assert inst.weight == u.Quantity(1.234, u.gram)


def test_weigth_immediately():
    """Get the immediate weight."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["SI"], ["S D 1.234 g"], "\r\n"
    ) as inst:
        assert inst.weight_immediately == u.Quantity(1.234, u.gram)


def test_weight_immediately_dynamic_mode():
    """Raise UserWarning if balance is in dynamic mode."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["SI"], ["S D 1.234 g"], "\r\n"
    ) as inst:
        with pytest.warns(UserWarning):
            _ = inst.weight_immediately
