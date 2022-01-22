#!/usr/bin/env python
"""
Module containing tests for the Qubitekk MC1
"""

# IMPORTS ####################################################################


import pytest

from instruments.units import ureg as u
import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


def test_mc1_increment():
    with expected_protocol(ik.qubitekk.MC1, [], [], sep="\r") as mc:
        assert mc.increment == 1 * u.ms
        mc.increment = 3 * u.ms
        assert mc.increment == 3 * u.ms


def test_mc1_lower_limit():
    with expected_protocol(ik.qubitekk.MC1, [], [], sep="\r") as mc:
        assert mc.lower_limit == -300 * u.ms
        mc.lower_limit = -400 * u.ms
        assert mc.lower_limit == -400 * u.ms


def test_mc1_upper_limit():
    with expected_protocol(ik.qubitekk.MC1, [], [], sep="\r") as mc:
        assert mc.upper_limit == 300 * u.ms
        mc.upper_limit = 400 * u.ms
        assert mc.upper_limit == 400 * u.ms


def test_mc1_setting():
    with expected_protocol(
        ik.qubitekk.MC1, ["OUTP?", ":OUTP 0"], ["1"], sep="\r"
    ) as mc:
        assert mc.setting == 1
        mc.setting = 0


def test_mc1_internal_position():
    with expected_protocol(
        ik.qubitekk.MC1, ["POSI?", "STEP?"], ["-100", "1"], sep="\r"
    ) as mc:
        assert mc.internal_position == -100 * u.ms


def test_mc1_metric_position():
    with expected_protocol(ik.qubitekk.MC1, ["METR?"], ["-3.14159"], sep="\r") as mc:
        assert mc.metric_position == -3.14159 * u.mm


def test_mc1_direction():
    with expected_protocol(ik.qubitekk.MC1, ["DIRE?"], ["-100"], sep="\r") as mc:
        assert mc.direction == -100 * u.ms


def test_mc1_firmware():
    with expected_protocol(ik.qubitekk.MC1, ["FIRM?"], ["1.0.1"], sep="\r") as mc:
        assert mc.firmware == (1, 0, 1)


def test_mc1_firmware_no_patch_info():
    with expected_protocol(ik.qubitekk.MC1, ["FIRM?"], ["1.0"], sep="\r") as mc:
        assert mc.firmware == (1, 0, 0)


def test_mc1_inertia():
    with expected_protocol(ik.qubitekk.MC1, ["INER?"], ["20"], sep="\r") as mc:
        assert mc.inertia == 20 * u.ms


def test_mc1_step():
    with expected_protocol(ik.qubitekk.MC1, ["STEP?"], ["20"], sep="\r") as mc:
        assert mc.step_size == 20 * u.ms


def test_mc1_motor():
    with expected_protocol(ik.qubitekk.MC1, ["MOTO?"], ["Radio"], sep="\r") as mc:
        assert mc.controller == mc.MotorType.radio


def test_mc1_move_timeout():
    with expected_protocol(
        ik.qubitekk.MC1, ["TIME?", "STEP?"], ["200", "1"], sep="\r"
    ) as mc:
        assert mc.move_timeout == 200 * u.ms


def test_mc1_is_centering():
    with expected_protocol(ik.qubitekk.MC1, ["CENT?"], ["1"], sep="\r") as mc:
        assert mc.is_centering() is True


def test_mc1_is_centering_false():
    with expected_protocol(ik.qubitekk.MC1, ["CENT?"], ["0"], sep="\r") as mc:
        assert mc.is_centering() is False


def test_mc1_center():
    with expected_protocol(ik.qubitekk.MC1, [":CENT"], [""], sep="\r") as mc:
        mc.center()


def test_mc1_reset():
    with expected_protocol(ik.qubitekk.MC1, [":RESE"], [""], sep="\r") as mc:
        mc.reset()


def test_mc1_move():
    with expected_protocol(
        ik.qubitekk.MC1, ["STEP?", ":MOVE 0"], ["1"], sep="\r"
    ) as mc:
        mc.move(0)


def test_mc1_move_value_error():
    with pytest.raises(ValueError) as exc_info, expected_protocol(
        ik.qubitekk.MC1, [], [], sep="\r"
    ) as mc:
        mc.move(-1000)
    exc_msg = exc_info.value.args[0]
    assert exc_msg == "Location out of range"
