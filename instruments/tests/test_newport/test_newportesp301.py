#!/usr/bin/env python
"""
Unit tests for the Newport ESP 301 axis controller
"""

# IMPORTS #####################################################################

import time

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol

# TESTS #######################################################################


# pylint: disable=protected-access,too-many-lines


# INSTRUMENT #


def test_init():
    """Initialize a Newport ESP301 instrument."""
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        assert inst._execute_immediately
        assert inst._command_list == []
        assert inst._bulk_query_resp == ""
        assert inst.terminator == "\r"


@given(ax=st.integers(min_value=0, max_value=99))
def test_axis_returns_axis_class(ax):
    """Return axis class with given axis number."""
    with expected_protocol(
        ik.newport.NewportESP301,
        [f"{ax+1}SN?", "TB?"],  # error check query
        ["1", "0,0,0"],
        sep="\r",
    ) as inst:
        axis = inst.axis[ax]
        assert isinstance(axis, ik.newport.NewportESP301.Axis)


def test_newport_cmd(mocker):
    """Send a low level command to some randomly chosen target.

    Execute command immediately (default), but no error check.
    """
    target = "TARG"
    cmd = "COMMAND"
    params = (1, 2, 3)
    # stitch together raw command to send
    raw_cmd = f"{target}{cmd}{','.join(map(str, params))}"
    with expected_protocol(ik.newport.NewportESP301, [raw_cmd], [], sep="\r") as inst:
        execute_spy = mocker.spy(inst, "_execute_cmd")
        resp = inst._newport_cmd(cmd, params=params, target=target, errcheck=False)
        assert resp is None
        execute_spy.assert_called_with(raw_cmd, False)


def test_newport_cmd_add_to_list():
    """Send a low level command to some randomly chosen target.

    Do not execute, just add command to list.
    """
    target = "TARG"
    cmd = "COMMAND"
    params = (1, 2, 3)
    # stitch together raw command to send
    raw_cmd = f"{target}{cmd}{','.join(map(str, params))}"
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        inst._execute_immediately = False
        resp = inst._newport_cmd(cmd, params=params, target=target)
        assert resp is None
        assert inst._command_list == [raw_cmd]


def test_newport_cmd_with_axis():
    """Send a low level command for a given axis."""
    ax = 42
    cmd = "COMMAND"
    params = (1, 2, 3)
    # stitch together raw command to send
    raw_cmd = f"{ax+1}{cmd}{','.join(map(str, params))}"

    with expected_protocol(
        ik.newport.NewportESP301,
        [f"{ax+1}SN?", "TB?", raw_cmd],  # error check query
        ["1", "0,0,0"],
        sep="\r",
    ) as inst:
        axis = inst.axis[ax]
        resp = inst._newport_cmd(cmd, params=params, target=axis, errcheck=False)
        assert resp is None


def test_execute_cmd_query():
    """Execute a query."""
    query = "QUERY?"
    response = "RESPONSE"

    with expected_protocol(
        ik.newport.NewportESP301,
        [query, "TB?"],
        [response, "0,0,0"],  # no error
        sep="\r",
    ) as inst:
        assert inst._execute_cmd(query) == response


def test_execute_cmd_query_error():
    """Raise an error while sending a command to the instrument.

    Only check for the context of the specific error message, since
    timestamp is not frozen.
    """
    cmd = "COMMAND"
    with expected_protocol(
        ik.newport.NewportESP301, [cmd, "TB?"], ["13,0,0"], sep="\r"  # no error
    ) as inst:
        with pytest.raises(ik.newport.errors.NewportError) as err_info:
            inst._execute_cmd(cmd)
        err_msg = err_info.value.args[0]
        assert "GROUP NUMBER MISSING" in err_msg


def test_home(mocker):
    """Search for home.

    Mock `_newport_cmd`, this routine is already tested. Just assert
    that it is called with correct arguments.
    """
    axis = "ax"
    params = 1, 2, 3
    errcheck = False
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        mock_cmd = mocker.patch.object(inst, "_newport_cmd")
        inst._home(axis, params, errcheck)
        mock_cmd.assert_called_with(
            "OR", target=axis, params=[params], errcheck=errcheck
        )


@pytest.mark.parametrize("search_mode", ik.newport.NewportESP301.HomeSearchMode)
def test_search_for_home(mocker, search_mode):
    """Search for home with specific method.

    Mock `_home` routine (already tested) and just assert that called
    with the correct arguments.
    """
    axis = 3
    errcheck = True
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        mock_cmd = mocker.patch.object(inst, "_home")
        inst.search_for_home(axis, search_mode, errcheck)
        mock_cmd.assert_called_with(
            axis=axis, search_mode=search_mode, errcheck=errcheck
        )


def test_reset(mocker):
    """Reset the device.

    Mock `_newport_cmd`, this routine is already tested. Just assert
    that it is called with correct arguments.
    """
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        mock_cmd = mocker.patch.object(inst, "_newport_cmd")
        inst.reset()
        mock_cmd.assert_called_with("RS", errcheck=False)


@given(prg_id=st.integers(min_value=1, max_value=100))
def test_define_program(mocker, prg_id):
    """Define an empty program.

    Mock out the `_newport_cmd` routine. Already tested and not
    required.
    """
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        mock_cmd = mocker.patch.object(inst, "_newport_cmd")
        with inst.define_program(prg_id):
            pass
        calls = (
            mocker.call("XX", target=prg_id),
            mocker.call("EP", target=prg_id),
            mocker.call("QP"),
        )
        mock_cmd.has_calls(calls)


@given(prg_id=st.integers().filter(lambda x: x < 1 or x > 100))
def test_define_program_value_error(prg_id):
    """Raise ValueError when defining program with invalid ID."""
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        with pytest.raises(ValueError) as err_info:
            with inst.define_program(prg_id):
                pass
        err_msg = err_info.value.args[0]
        assert (
            err_msg == "Invalid program ID. Must be an integer from 1 to "
            "100 (inclusive)."
        )


@pytest.mark.parametrize("errcheck", (True, False))
def test_execute_bulk_command(mocker, errcheck):
    """Execute bulk commands.

    Mock out the `_execute_cmd` call and simply assert that calls are
    in correct order.

    We will just do three move commands, one with steps of 1, 10, and
    11.
    """
    ax = 0
    move_commands_sent = "1PA1.0 ; 1PA10.0 ;  ; 1PA11.0 ; "
    resp = "Response"
    with expected_protocol(
        ik.newport.NewportESP301,
        [
            f"{ax+1}SN?",
            "TB?",  # error check query
        ],
        ["1", "0,0,0"],
        sep="\r",
    ) as inst:
        axis = inst.axis[ax]
        mock_exec = mocker.patch.object(inst, "_execute_cmd", return_value=resp)
        with inst.execute_bulk_command(errcheck=errcheck):
            assert not inst._execute_immediately
            # some move commands
            axis.move(1.0)
            axis.move(10.0)
            axis.move(11.0)
        mock_exec.assert_called_with(move_commands_sent, errcheck)
        assert inst._bulk_query_resp == resp
        assert inst._command_list == []
        assert inst._execute_immediately


@given(prg_id=st.integers(min_value=1, max_value=100))
def test_run_program(mocker, prg_id):
    """Run a program.

    Mock out the `_newport_cmd` routine. Already tested and not
    required.
    """
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        mock_cmd = mocker.patch.object(inst, "_newport_cmd")
        inst.run_program(prg_id)
        mock_cmd.assert_called_with("EX", target=prg_id)


@given(prg_id=st.integers().filter(lambda x: x < 1 or x > 100))
def test_run_program_value_error(prg_id):
    """Raise ValueError when defining program with invalid ID."""
    with expected_protocol(ik.newport.NewportESP301, [], [], sep="\r") as inst:
        with pytest.raises(ValueError) as err_info:
            inst.run_program(prg_id)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == "Invalid program ID. Must be an integer from 1 to "
            "100 (inclusive)."
        )


# AXIS #


# commands to send, return when initializing axis zero
ax_init = "1SN?\rTB?", "1\r0,0,0"


def test_axis_init():
    """Initialize a new axis."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        assert axis._controller == inst
        assert axis._axis_id == 1
        assert axis._units == u.Quantity(1, u.count)


def test_axis_init_type_error():
    """Raise TypeError when axis initialized from wrong parent."""
    with pytest.raises(TypeError) as err_info:
        _ = ik.newport.newportesp301.NewportESP301.Axis(42, 0)
    err_msg = err_info.value.args[0]
    assert (
        err_msg == "Axis must be controlled by a Newport ESP-301 motor " "controller."
    )


def test_axis_units_of(mocker):
    """Context manager with reset of units after usage.

    Mock out the getting and setting the units. These two routines are
    tested separately, thus only assert that the correct calls are
    issued.
    """
    get_unit = ik.newport.newportesp301.NewportESP301.Units.millimeter
    set_unit = ik.newport.newportesp301.NewportESP301.Units.inches
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_get = mocker.patch.object(axis, "_get_units", return_value=get_unit)
        mock_set = mocker.patch.object(axis, "_set_units", return_value=None)
        with axis._units_of(set_unit):
            mock_get.assert_called()
            mock_set.assert_called_with(set_unit)
        mock_set.assert_called_with(get_unit)


def test_axis_get_units(mocker):
    """Get units from the axis.

    Mock out the command sending and receiving.
    """
    resp = "2"
    unit = ik.newport.newportesp301.NewportESP301.Units(int(resp))
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=resp)
        assert unit == axis._get_units()
        mock_cmd.assert_called_with("SN?", target=1)


def test_axis_set_units(mocker):
    """Set units for a given axis.

    Mock out the actual command sending for simplicity, but assert it
    has been called.
    """
    unit = ik.newport.newportesp301.NewportESP301.Units.radian  # just pick one
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=None)
        assert axis._set_units(unit) is None
        mock_cmd.assert_called_with("SN", target=1, params=[int(unit)])


def test_axis_id():
    """Get axis ID."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        assert axis.axis_id == 1


@pytest.mark.parametrize("resp", ("0", "1"))
def test_axis_is_motion_done(mocker, resp):
    """Get if motion is done.

    Mock out the command sending, as above.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=resp)
        assert axis.is_motion_done is bool(int(resp))
        mock_cmd.assert_called_with("MD?", target=1)


def test_axis_acceleration(mocker):
    """Set / get axis acceleration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.acceleration = value
        mock_cmd.assert_called_with("AC", target=1, params=[float(value)])
        assert axis.acceleration == u.Quantity(value, axis._units / u.s ** 2)
        mock_cmd.assert_called_with("AC?", target=1)


def test_axis_acceleration_none():
    """Set axis acceleration with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.acceleration = None


def test_axis_deceleration(mocker):
    """Set / get axis deceleration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.deceleration = value
        mock_cmd.assert_called_with("AG", target=1, params=[float(value)])
        assert axis.deceleration == u.Quantity(value, axis._units / u.s ** 2)
        mock_cmd.assert_called_with("AG?", target=1)


def test_axis_deceleration_none():
    """Set axis deceleration with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.deceleration = None


def test_axis_estop_deceleration(mocker):
    """Set / get axis estop deceleration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.estop_deceleration = value
        mock_cmd.assert_called_with("AE", target=1, params=[float(value)])
        assert axis.estop_deceleration == u.Quantity(value, axis._units / u.s ** 2)
        mock_cmd.assert_called_with("AE?", target=1)


def test_axis_jerk(mocker):
    """Set / get axis jerk rate.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.jerk = value
        mock_cmd.assert_called_with("JK", target=1, params=[float(value)])
        assert axis.jerk == u.Quantity(value, axis._units / u.s ** 3)
        mock_cmd.assert_called_with("JK?", target=1)


def test_axis_velocity(mocker):
    """Set / get axis velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.velocity = value
        mock_cmd.assert_called_with("VA", target=1, params=[float(value)])
        assert axis.velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("VA?", target=1)


def test_axis_max_velocity(mocker):
    """Set / get axis maximum velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.max_velocity = value
        mock_cmd.assert_called_with("VU", target=1, params=[float(value)])
        assert axis.max_velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("VU?", target=1)


def test_axis_max_velocity_none():
    """Set axis maximum velocity with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.max_velocity = None


def test_axis_max_base_velocity(mocker):
    """Set / get axis maximum base velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.max_base_velocity = value
        mock_cmd.assert_called_with("VB", target=1, params=[float(value)])
        assert axis.max_base_velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("VB?", target=1)


def test_axis_max_base_velocity_none():
    """Set axis maximum base velocity with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.max_base_velocity = None


def test_axis_jog_high_velocity(mocker):
    """Set / get axis jog high velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.jog_high_velocity = value
        mock_cmd.assert_called_with("JH", target=1, params=[float(value)])
        assert axis.jog_high_velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("JH?", target=1)


def test_axis_jog_high_velocity_none():
    """Set axis jog high velocity with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.jog_high_velocity = None


def test_axis_jog_low_velocity(mocker):
    """Set / get axis jog low velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.jog_low_velocity = value
        mock_cmd.assert_called_with("JW", target=1, params=[float(value)])
        assert axis.jog_low_velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("JW?", target=1)


def test_axis_jog_low_velocity_none():
    """Set axis jog low velocity with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.jog_low_velocity = None


def test_axis_homing_velocity(mocker):
    """Set / get axis homing velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.homing_velocity = value
        mock_cmd.assert_called_with("OH", target=1, params=[float(value)])
        assert axis.homing_velocity == u.Quantity(value, axis._units / u.s)
        mock_cmd.assert_called_with("OH?", target=1)


def test_axis_homing_velocity_none():
    """Set axis homing velocity with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.homing_velocity = None


def test_axis_max_acceleration(mocker):
    """Set / get axis maximum acceleration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.max_acceleration = value
        mock_cmd.assert_called_with("AU", target=1, params=[float(value)])
        assert axis.max_acceleration == u.Quantity(value, axis._units / u.s ** 2)
        mock_cmd.assert_called_with("AU?", target=1)


def test_axis_max_acceleration_none():
    """Set axis maximum acceleration with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.max_acceleration = None


def test_axis_max_deceleration(mocker):
    """Set / get axis maximum deceleration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.max_deceleration = value
        mock_cmd.assert_called_with("AU", target=1, params=[float(value)])
        assert axis.max_deceleration == u.Quantity(value, axis._units / u.s ** 2)
        mock_cmd.assert_called_with("AU?", target=1)


def test_axis_position(mocker):
    """Get axis position.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    retval = "42"
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=retval)
        assert axis.position == u.Quantity(float(retval), axis._units)
        mock_cmd.assert_called_with("TP?", target=1)


def test_axis_desired_position(mocker):
    """Get axis desired position.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    retval = "42"
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=retval)
        assert axis.desired_position == u.Quantity(float(retval), axis._units)
        mock_cmd.assert_called_with("DP?", target=1)


def test_axis_desired_velocity(mocker):
    """Get axis desired velocity.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    retval = "42"
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=retval)
        assert axis.desired_velocity == u.Quantity(float(retval), axis._units / u.s)
        mock_cmd.assert_called_with("DV?", target=1)


def test_axis_home(mocker):
    """Set / get axis home position.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.home = value
        mock_cmd.assert_called_with("DH", target=1, params=[float(value)])
        assert axis.home == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("DH?", target=1)


def test_axis_home_none():
    """Set axis home with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.home = None


def test_axis_units(mocker):
    """Get / set units.

    Mock out `_newport_cmd` since tested elsewhere. Returns u.counts
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value="0")
        assert axis.units == u.counts
        mock_cmd.reset_mock()
        # set units with None
        axis.units = None
        mock_cmd.assert_not_called()
        # set units with um as number (num 3)
        axis.units = 3
        assert axis._units == u.um
        mock_cmd.assert_called_with("SN", target=1, params=[3])
        # set units with millimeters as quantity (num 2)
        axis.units = u.mm
        assert axis._units == u.mm
        mock_cmd.assert_called_with("SN", target=1, params=[2])


def test_axis_encoder_resolution(mocker):
    """Set / get axis encoder resolution.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.encoder_resolution = value
        mock_cmd.assert_called_with("SU", target=1, params=[float(value)])
        assert axis.encoder_resolution == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("SU?", target=1)


def test_axis_encoder_resolution_none():
    """Set axis encoder resolution with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.encoder_resolution = None


def test_axis_full_step_resolution(mocker):
    """Set / get axis full step resolution.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.full_step_resolution = value
        mock_cmd.assert_called_with("FR", target=1, params=[float(value)])
        assert axis.full_step_resolution == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("FR?", target=1)


def test_axis_full_step_resolution_none():
    """Set axis full step resolution with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.full_step_resolution = None


def test_axis_left_limit(mocker):
    """Set / get axis left limit.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.left_limit = value
        mock_cmd.assert_called_with("SL", target=1, params=[float(value)])
        assert axis.left_limit == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("SL?", target=1)


def test_axis_right_limit(mocker):
    """Set / get axis right limit.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.right_limit = value
        mock_cmd.assert_called_with("SR", target=1, params=[float(value)])
        assert axis.right_limit == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("SR?", target=1)


def test_axis_error_threshold(mocker):
    """Set / get axis error threshold.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.error_threshold = value
        mock_cmd.assert_called_with("FE", target=1, params=[float(value)])
        assert axis.error_threshold == u.Quantity(value, axis._units)
        mock_cmd.assert_called_with("FE?", target=1)


def test_axis_error_threshold_none():
    """Set axis error threshold with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.error_threshold = None


def test_axis_current(mocker):
    """Set / get axis current.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.current = value
        mock_cmd.assert_called_with("QI", target=1, params=[float(value)])
        assert axis.current == u.Quantity(value, u.A)
        mock_cmd.assert_called_with("QI?", target=1)


def test_axis_current_none():
    """Set axis current with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.current = None


def test_axis_voltage(mocker):
    """Set / get axis voltage.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.voltage = value
        mock_cmd.assert_called_with("QV", target=1, params=[float(value)])
        assert axis.voltage == u.Quantity(value, u.V)
        mock_cmd.assert_called_with("QV?", target=1)


def test_axis_voltage_none():
    """Set axis voltage with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.voltage = None


def test_axis_motor_type(mocker):
    """Set / get axis motor type.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 1  # DC Servo
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.motor_type = value
        mock_cmd.assert_called_with("QM", target=1, params=[float(value)])
        assert axis.motor_type == value
        mock_cmd.assert_called_with("QM?", target=1)


def test_axis_motor_type_none():
    """Set axis motor type with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.motor_type = None


def test_axis_feedback_configuration(mocker):
    """Set / get axis feedback configuration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "A13\r\n"  # 2 additional characters that will be cancelled
    value = int(value_ret[:-2], 16)
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.feedback_configuration = value
        mock_cmd.assert_called_with("ZB", target=1, params=[float(value)])
        assert axis.feedback_configuration == value
        mock_cmd.assert_called_with("ZB?", target=1)


def test_axis_feedback_configuration_none():
    """Set axis feedback configuration with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.feedback_configuration = None


def test_axis_position_display_resolution(mocker):
    """Set / get axis position display resolution.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.position_display_resolution = value
        mock_cmd.assert_called_with("FP", target=1, params=[float(value)])
        assert axis.position_display_resolution == value
        mock_cmd.assert_called_with("FP?", target=1)


def test_axis_position_display_resolution_none():
    """Set axis position display resolution with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.position_display_resolution = None


def test_axis_trajectory(mocker):
    """Set / get axis trajectory.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.trajectory = value
        mock_cmd.assert_called_with("TJ", target=1, params=[float(value)])
        assert axis.trajectory == value
        mock_cmd.assert_called_with("TJ?", target=1)


def test_axis_trajectory_none():
    """Set axis trajectory with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.trajectory = None


def test_axis_microstep_factor(mocker):
    """Set / get axis microstep factor.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.microstep_factor = value
        mock_cmd.assert_called_with("QS", target=1, params=[float(value)])
        assert axis.microstep_factor == value
        mock_cmd.assert_called_with("QS?", target=1)


def test_axis_microstep_factor_none():
    """Set axis microstep factor with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.microstep_factor = None


@given(fct=st.integers().filter(lambda x: x < 1 or x > 250))
def test_axis_microstep_factor_out_of_range(fct):
    """Raise ValueError when microstep factor is out of range."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError) as err_info:
            axis.microstep_factor = fct
        err_msg = err_info.value.args[0]
        assert err_msg == "Microstep factor must be between 1 and 250"


def test_axis_hardware_limit_configuration(mocker):
    """Set / get axis hardware limit configuration.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "42\r\n"  # add two characters to delete later
    value = int(value_ret[:-2])
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.hardware_limit_configuration = value
        mock_cmd.assert_called_with("ZH", target=1, params=[float(value)])
        assert axis.hardware_limit_configuration == value
        mock_cmd.assert_called_with("ZH?", target=1)


def test_axis_hardware_limit_configuration_none():
    """Set axis hardware limit configuration with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.hardware_limit_configuration = None


def test_axis_acceleration_feed_forward(mocker):
    """Set / get axis acceleration feed forward.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        axis.acceleration_feed_forward = value
        mock_cmd.assert_called_with("AF", target=1, params=[float(value)])
        assert axis.acceleration_feed_forward == value
        mock_cmd.assert_called_with("AF?", target=1)


def test_axis_acceleration_feed_forward_none():
    """Set axis acceleration feed forward with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.acceleration_feed_forward = None


def test_axis_proportional_gain(mocker):
    """Set / get axis proportional gain.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "42\r"
    value = float(value_ret[:-1])
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.proportional_gain = value
        mock_cmd.assert_called_with("KP", target=1, params=[float(value)])
        assert axis.proportional_gain == float(value)
        mock_cmd.assert_called_with("KP?", target=1)


def test_axis_proportional_gain_none():
    """Set axis proportional gain with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.proportional_gain = None


def test_axis_derivative_gain(mocker):
    """Set / get axis derivative gain.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "42"
    value = float(value_ret)
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.derivative_gain = value
        mock_cmd.assert_called_with("KD", target=1, params=[float(value)])
        assert axis.derivative_gain == float(value)
        mock_cmd.assert_called_with("KD?", target=1)


def test_axis_derivative_gain_none():
    """Set axis derivative gain with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.derivative_gain = None


def test_axis_integral_gain(mocker):
    """Set / get axis integral gain.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "42"
    value = float(value_ret)
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.integral_gain = value
        mock_cmd.assert_called_with("KI", target=1, params=[float(value)])
        assert axis.integral_gain == float(value)
        mock_cmd.assert_called_with("KI?", target=1)


def test_axis_integral_gain_none():
    """Set axis integral gain with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.integral_gain = None


def test_axis_integral_saturation_gain(mocker):
    """Set / get axis integral saturation gain.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value_ret = "42"
    value = float(value_ret)
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value_ret)
        axis.integral_saturation_gain = value
        mock_cmd.assert_called_with("KS", target=1, params=[float(value)])
        assert axis.integral_saturation_gain == float(value)
        mock_cmd.assert_called_with("KS?", target=1)


def test_axis_integral_saturation_gain_none():
    """Set axis integral saturation gain with `None` does nothing."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        axis.integral_saturation_gain = None


def test_axis_encoder_position(mocker):
    """Get encoder position.

    Mock out the getting and setting the units. These two routines are
    tested separately, thus only assert that the correct calls are
    issued.
    Also mock out `_newport_cmd`.
    """
    value = 42
    get_unit = ik.newport.newportesp301.NewportESP301.Units.millimeter
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_get = mocker.patch.object(axis, "_get_units", return_value=get_unit)
        mock_set = mocker.patch.object(axis, "_set_units", return_value=None)
        mock_cmd = mocker.patch.object(axis, "_newport_cmd", return_value=value)
        assert axis.encoder_position == u.Quantity(value, u.count)
        mock_get.assert_called()
        mock_set.assert_called_with(get_unit)
        mock_cmd.assert_called_with("TP?", target=1)


# AXIS METHODS #


@pytest.mark.parametrize("mode", ik.newport.newportesp301.NewportESP301.HomeSearchMode)
def test_axis_search_for_home(mocker, mode):
    """Search for home.

    Mock out `search_for_home` of controller since already tested.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_search = mocker.patch.object(axis._controller, "search_for_home")
        axis.search_for_home(search_mode=mode.value)
        mock_search.assert_called_with(axis=1, search_mode=mode.value)


def test_axis_search_for_home_default(mocker):
    """Search for home without a specified search mode.

    Mock out `search_for_home` of controller since already tested.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_search = mocker.patch.object(axis._controller, "search_for_home")
        axis.search_for_home()

        default_mode = axis._controller.HomeSearchMode.zero_position_count.value
        mock_search.assert_called_with(axis=1, search_mode=default_mode)


def test_axis_move_absolute(mocker):
    """Make an absolute move (default) on the axis.

    No wait, no block.
    Mock out `_newport_cmd` since tested elsewhere.
    """
    position = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.move(position)
        mock_cmd.assert_called_with("PA", params=[position], target=1)


def test_axis_move_relative_wait(mocker):
    """Make an relative move on the axis and wait.

    Do a wait but no block.
    Mock out `_newport_cmd` since tested elsewhere.
    """
    position = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.move(position, absolute=False, wait=True)
        calls = (
            mocker.call("PR", params=[position], target=1),
            mocker.call("WP", target=1, params=[float(position)]),
        )
        mock_cmd.assert_has_calls(calls)


def test_axis_move_relative_wait_block(mocker):
    """Make an relative move on the axis and wait.

    Do a wait and lock, go once into while loop.
    Mock out `_newport_cmd`, `time.sleep`, and `is_motion_done` since
    tested elsewhere.
    """
    position = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        mock_cmd.side_effect = [None, None, False, True]
        axis.move(position, absolute=False, wait=True, block=True)
        calls = (
            mocker.call("PR", params=[position], target=1),
            mocker.call("WP", target=1, params=[float(position)]),
            mocker.call("MD?", target=1),
            mocker.call("MD?", target=1),
        )
        mock_cmd.assert_has_calls(calls)


def test_axis_move_to_hardware_limit(mocker):
    """Move to hardware limit.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.move_to_hardware_limit()
        mock_cmd.assert_called_with("MT", target=1)


def test_axis_move_indefinitely(mocker):
    """Move indefinitely

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.move_indefinitely()
        mock_cmd.assert_called_with("MV", target=1)


def test_axis_abort_motion(mocker):
    """Abort motion.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.abort_motion()
        mock_cmd.assert_called_with("AB", target=1)


def test_axis_wait_for_stop(mocker):
    """Wait for stop.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.wait_for_stop()
        mock_cmd.assert_called_with("WS", target=1)


def test_axis_stop_motion(mocker):
    """Stop motion.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.stop_motion()
        mock_cmd.assert_called_with("ST", target=1)


def test_axis_wait_for_position(mocker):
    """Wait for position.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    value = 42
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.wait_for_position(value)
        mock_cmd.assert_called_with("WP", target=1, params=[float(value)])


def test_axis_wait_for_motion_max_wait_zero(mocker):
    """Wait for motion to finish.

    Motion is not stopped (mock that part) but maximum wait time is
    zero.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mocker.patch.object(axis, "_newport_cmd", return_value="0")

        with pytest.raises(IOError) as err_info:
            axis.wait_for_motion(max_wait=0.0)
        err_msg = err_info.value.args[0]
        assert err_msg == "Timed out waiting for motion to finish."


def test_axis_wait_for_motion_max_wait_some_time(mocker):
    """Wait for motion to finish.

    Motion is stopped after several queries that first return `False`.
    Mocking `time.time`, `time.sleep`, and `_newport_cmd`. Using
    generators to create the appropriate times..
    """
    interval = 42.0
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        # patch time and sleep
        mock_time = mocker.patch.object(time, "time", return_value=None)
        mock_time.side_effect = [0.0, 0.0, 0.1]
        mock_sleep = mocker.patch.object(time, "sleep", return_value=None)
        # get axis
        axis = inst.axis[0]
        # patch status
        mock_status = mocker.patch.object(axis, "_newport_cmd", return_value=None)
        mock_status.side_effect = ["0", "0", "1"]
        assert axis.wait_for_motion(poll_interval=interval) is None
        # make sure the routine has called sleep
        mock_sleep.assert_called_with(interval)


def test_axis_enable(mocker):
    """Enable axis.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.enable()
        mock_cmd.assert_called_with("MO", target=1)


def test_axis_disable(mocker):
    """Disable axis.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        axis.disable()
        mock_cmd.assert_called_with("MF", target=1)


def test_axis_setup_axis(mocker):
    """Set up non-newport motor.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    motor_type = 2  # stepper motor
    current = 1
    voltage = 2
    units = ik.newport.newportesp301.NewportESP301.Units.radian
    encoder_resolution = 3.0
    max_velocity = 4
    max_base_velocity = 5
    homing_velocity = 6
    jog_high_velocity = 7
    jog_low_velocity = 8
    max_acceleration = 9
    acceleration = 10
    velocity = 11
    deceleration = 12
    estop_deceleration = 13
    jerk = 14
    error_threshold = 15
    proportional_gain = 16
    derivative_gain = 17
    integral_gain = 18
    integral_saturation_gain = 19
    trajectory = 20
    position_display_resolution = 21
    feedback_configuration = 22
    full_step_resolution = 23
    home = 24
    microstep_factor = 25
    acceleration_feed_forward = 26
    hardware_limit_configuration = 27

    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        mocker.patch.object(axis, "read_setup", return_value=True)
        ax_setup = axis.setup_axis(
            motor_type=motor_type,
            current=current,
            voltage=voltage,
            units=units,
            encoder_resolution=encoder_resolution,
            max_velocity=max_velocity,
            max_base_velocity=max_base_velocity,
            homing_velocity=homing_velocity,
            jog_high_velocity=jog_high_velocity,
            jog_low_velocity=jog_low_velocity,
            max_acceleration=max_acceleration,
            acceleration=acceleration,
            velocity=velocity,
            deceleration=deceleration,
            estop_deceleration=estop_deceleration,
            jerk=jerk,
            error_threshold=error_threshold,
            proportional_gain=proportional_gain,
            derivative_gain=derivative_gain,
            integral_gain=integral_gain,
            integral_saturation_gain=integral_saturation_gain,
            trajectory=trajectory,
            position_display_resolution=position_display_resolution,
            feedback_configuration=feedback_configuration,
            full_step_resolution=full_step_resolution,
            home=home,
            microstep_factor=microstep_factor,
            acceleration_feed_forward=acceleration_feed_forward,
            hardware_limit_configuration=hardware_limit_configuration,
        )
        assert ax_setup

        # assert mandatory calls in any order
        calls_params = (
            mocker.call("QM", target=1, params=[int(motor_type)]),
            mocker.call("ZB", target=1, params=[int(feedback_configuration)]),
            mocker.call("FR", target=1, params=[float(full_step_resolution)]),
            mocker.call("FP", target=1, params=[int(position_display_resolution)]),
            mocker.call("QI", target=1, params=[float(current)]),
            mocker.call("QV", target=1, params=[float(voltage)]),
            mocker.call("SN", target=1, params=[units.value]),
            mocker.call("SU", target=1, params=[float(encoder_resolution)]),
            mocker.call("AU", target=1, params=[float(max_acceleration)]),
            mocker.call("VU", target=1, params=[float(max_velocity)]),
            mocker.call("VB", target=1, params=[float(max_base_velocity)]),
            mocker.call("OH", target=1, params=[float(homing_velocity)]),
            mocker.call("JH", target=1, params=[float(jog_high_velocity)]),
            mocker.call("JW", target=1, params=[float(jog_low_velocity)]),
            mocker.call("AC", target=1, params=[float(acceleration)]),
            mocker.call("VA", target=1, params=[float(velocity)]),
            mocker.call("AG", target=1, params=[float(deceleration)]),
            mocker.call("AE", target=1, params=[float(estop_deceleration)]),
            mocker.call("JK", target=1, params=[float(jerk)]),
            mocker.call("FE", target=1, params=[float(error_threshold)]),
            mocker.call("KP", target=1, params=[float(proportional_gain)]),
            mocker.call("KD", target=1, params=[float(derivative_gain)]),
            mocker.call("KI", target=1, params=[float(integral_gain)]),
            mocker.call("KS", target=1, params=[float(integral_saturation_gain)]),
            mocker.call("DH", target=1, params=[float(home)]),
            mocker.call("QS", target=1, params=[float(microstep_factor)]),
            mocker.call("AF", target=1, params=[float(acceleration_feed_forward)]),
            mocker.call("TJ", target=1, params=[int(trajectory)]),
            mocker.call("ZH", target=1, params=[int(hardware_limit_configuration)]),
        )
        mock_cmd.assert_has_calls(calls_params, any_order=True)

        # assert final calls - in order
        calls_final = (
            mocker.call("UF", target=1),
            mocker.call("QD", target=1),
            mocker.call("SM"),
        )
        mock_cmd.assert_has_calls(calls_final)
        mock_cmd.assert_called_with("SM")


def test_axis_setup_axis_torque(mocker):
    """Set up non-newport motor with torque specifications.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    motor_type = 2  # stepper motor
    current = 1
    voltage = 2
    units = ik.newport.newportesp301.NewportESP301.Units.radian
    encoder_resolution = 3.0
    max_velocity = 4
    max_base_velocity = 5
    homing_velocity = 6
    jog_high_velocity = 7
    jog_low_velocity = 8
    max_acceleration = 9
    acceleration = 10
    velocity = 11
    deceleration = 12
    estop_deceleration = 13
    jerk = 14
    error_threshold = 15
    proportional_gain = 16
    derivative_gain = 17
    integral_gain = 18
    integral_saturation_gain = 19
    trajectory = 20
    position_display_resolution = 21
    feedback_configuration = 22
    full_step_resolution = 23
    home = 24
    microstep_factor = 25
    acceleration_feed_forward = 26
    hardware_limit_configuration = 27
    # special configs
    rmt_time = 42
    rmt_perc = 13

    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        mocker.patch.object(axis, "read_setup", return_value=True)
        axis.setup_axis(
            motor_type=motor_type,
            current=current,
            voltage=voltage,
            units=units,
            encoder_resolution=encoder_resolution,
            max_velocity=max_velocity,
            max_base_velocity=max_base_velocity,
            homing_velocity=homing_velocity,
            jog_high_velocity=jog_high_velocity,
            jog_low_velocity=jog_low_velocity,
            max_acceleration=max_acceleration,
            acceleration=acceleration,
            velocity=velocity,
            deceleration=deceleration,
            estop_deceleration=estop_deceleration,
            jerk=jerk,
            error_threshold=error_threshold,
            proportional_gain=proportional_gain,
            derivative_gain=derivative_gain,
            integral_gain=integral_gain,
            integral_saturation_gain=integral_saturation_gain,
            trajectory=trajectory,
            position_display_resolution=position_display_resolution,
            feedback_configuration=feedback_configuration,
            full_step_resolution=full_step_resolution,
            home=home,
            microstep_factor=microstep_factor,
            acceleration_feed_forward=acceleration_feed_forward,
            hardware_limit_configuration=hardware_limit_configuration,
            reduce_motor_torque_time=rmt_time,
            reduce_motor_torque_percentage=rmt_perc,
        )
        # ensure the torque settings are set
        call_torque = (mocker.call("QR", target=1, params=[rmt_time, rmt_perc]),)

        mock_cmd.assert_has_calls(call_torque)


@given(rmt_time=st.integers().filter(lambda x: x < 0 or x > 60000))
def test_axis_setup_axis_torque_time_out_of_range(mocker, rmt_time):
    """Raise ValueError when time is out of range.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    motor_type = 2  # stepper motor
    current = 1
    voltage = 2
    units = ik.newport.newportesp301.NewportESP301.Units.radian
    encoder_resolution = 3.0
    max_velocity = 4
    max_base_velocity = 5
    homing_velocity = 6
    jog_high_velocity = 7
    jog_low_velocity = 8
    max_acceleration = 9
    acceleration = 10
    velocity = 11
    deceleration = 12
    estop_deceleration = 13
    jerk = 14
    error_threshold = 15
    proportional_gain = 16
    derivative_gain = 17
    integral_gain = 18
    integral_saturation_gain = 19
    trajectory = 20
    position_display_resolution = 21
    feedback_configuration = 22
    full_step_resolution = 23
    home = 24
    microstep_factor = 25
    acceleration_feed_forward = 26
    hardware_limit_configuration = 27
    # special configs
    rmt_perc = 13

    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mocker.patch.object(axis, "_newport_cmd")
        mocker.patch.object(axis, "read_setup", return_value=True)
        with pytest.raises(ValueError) as err_info:
            axis.setup_axis(
                motor_type=motor_type,
                current=current,
                voltage=voltage,
                units=units,
                encoder_resolution=encoder_resolution,
                max_velocity=max_velocity,
                max_base_velocity=max_base_velocity,
                homing_velocity=homing_velocity,
                jog_high_velocity=jog_high_velocity,
                jog_low_velocity=jog_low_velocity,
                max_acceleration=max_acceleration,
                acceleration=acceleration,
                velocity=velocity,
                deceleration=deceleration,
                estop_deceleration=estop_deceleration,
                jerk=jerk,
                error_threshold=error_threshold,
                proportional_gain=proportional_gain,
                derivative_gain=derivative_gain,
                integral_gain=integral_gain,
                integral_saturation_gain=integral_saturation_gain,
                trajectory=trajectory,
                position_display_resolution=position_display_resolution,
                feedback_configuration=feedback_configuration,
                full_step_resolution=full_step_resolution,
                home=home,
                microstep_factor=microstep_factor,
                acceleration_feed_forward=acceleration_feed_forward,
                hardware_limit_configuration=hardware_limit_configuration,
                reduce_motor_torque_time=rmt_time,
                reduce_motor_torque_percentage=rmt_perc,
            )
        err_msg = err_info.value.args[0]
        assert err_msg == "Time must be between 0 and 60000 ms"


@given(rmt_perc=st.integers().filter(lambda x: x < 0 or x > 100))
def test_axis_setup_axis_torque_percentage_out_of_range(mocker, rmt_perc):
    """Raise ValueError when time is out of range.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    motor_type = 2  # stepper motor
    current = 1
    voltage = 2
    units = ik.newport.newportesp301.NewportESP301.Units.radian
    encoder_resolution = 3.0
    max_velocity = 4
    max_base_velocity = 5
    homing_velocity = 6
    jog_high_velocity = 7
    jog_low_velocity = 8
    max_acceleration = 9
    acceleration = 10
    velocity = 11
    deceleration = 12
    estop_deceleration = 13
    jerk = 14
    error_threshold = 15
    proportional_gain = 16
    derivative_gain = 17
    integral_gain = 18
    integral_saturation_gain = 19
    trajectory = 20
    position_display_resolution = 21
    feedback_configuration = 22
    full_step_resolution = 23
    home = 24
    microstep_factor = 25
    acceleration_feed_forward = 26
    hardware_limit_configuration = 27
    # special configs
    rmt_time = 42

    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mocker.patch.object(axis, "_newport_cmd")
        mocker.patch.object(axis, "read_setup", return_value=True)
        with pytest.raises(ValueError) as err_info:
            axis.setup_axis(
                motor_type=motor_type,
                current=current,
                voltage=voltage,
                units=units,
                encoder_resolution=encoder_resolution,
                max_velocity=max_velocity,
                max_base_velocity=max_base_velocity,
                homing_velocity=homing_velocity,
                jog_high_velocity=jog_high_velocity,
                jog_low_velocity=jog_low_velocity,
                max_acceleration=max_acceleration,
                acceleration=acceleration,
                velocity=velocity,
                deceleration=deceleration,
                estop_deceleration=estop_deceleration,
                jerk=jerk,
                error_threshold=error_threshold,
                proportional_gain=proportional_gain,
                derivative_gain=derivative_gain,
                integral_gain=integral_gain,
                integral_saturation_gain=integral_saturation_gain,
                trajectory=trajectory,
                position_display_resolution=position_display_resolution,
                feedback_configuration=feedback_configuration,
                full_step_resolution=full_step_resolution,
                home=home,
                microstep_factor=microstep_factor,
                acceleration_feed_forward=acceleration_feed_forward,
                hardware_limit_configuration=hardware_limit_configuration,
                reduce_motor_torque_time=rmt_time,
                reduce_motor_torque_percentage=rmt_perc,
            )
        err_msg = err_info.value.args[0]
        assert err_msg == r"Percentage must be between 0 and 100%"


def test_axis_read_setup(mocker):
    """Read the axis setup and return it.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    config = {
        "units": u.mm,
        "motor_type": ik.newport.newportesp301.NewportESP301.MotorType.dc_servo,
        "feedback_configuration": 1,  # last 2 removed at return
        "full_step_resolution": u.Quantity(2.0, u.mm),
        "position_display_resolution": 3,
        "current": u.Quantity(4.0, u.A),
        "max_velocity": u.Quantity(5.0, u.mm / u.s),
        "encoder_resolution": u.Quantity(6.0, u.mm),
        "acceleration": u.Quantity(7.0, u.mm / u.s ** 2),
        "deceleration": u.Quantity(8.0, u.mm / u.s ** 2),
        "velocity": u.Quantity(9.0, u.mm / u.s),
        "max_acceleration": u.Quantity(10.0, u.mm / u.s ** 2.0),
        "homing_velocity": u.Quantity(11.0, u.mm / u.s),
        "jog_high_velocity": u.Quantity(12.0, u.mm / u.s),
        "jog_low_velocity": u.Quantity(13.0, u.mm / u.s),
        "estop_deceleration": u.Quantity(14.0, u.mm / u.s ** 2.0),
        "jerk": u.Quantity(14.0, u.mm / u.s ** 3.0),
        "proportional_gain": 15.0,  # last 1 removed at return
        "derivative_gain": 16.0,
        "integral_gain": 17.0,
        "integral_saturation_gain": 18.0,
        "home": u.Quantity(19.0, u.mm),
        "microstep_factor": 20,
        "acceleration_feed_forward": 21.0,
        "trajectory": 22,
        "hardware_limit_configuration": 23,  # last 2 removed
    }

    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        mock_cmd.side_effect = [
            ik.newport.newportesp301.NewportESP301.Units.millimeter.value,
            config["motor_type"].value,
            f"{config['feedback_configuration']}**",  # 2 extra
            config["full_step_resolution"].magnitude,
            config["position_display_resolution"],
            config["current"].magnitude,
            config["max_velocity"].magnitude,
            config["encoder_resolution"].magnitude,
            config["acceleration"].magnitude,
            config["deceleration"].magnitude,
            config["velocity"].magnitude,
            config["max_acceleration"].magnitude,
            config["homing_velocity"].magnitude,
            config["jog_high_velocity"].magnitude,
            config["jog_low_velocity"].magnitude,
            config["estop_deceleration"].magnitude,
            config["jerk"].magnitude,
            f"{config['proportional_gain']}*",  # 1 extra
            config["derivative_gain"],
            config["integral_gain"],
            config["integral_saturation_gain"],
            config["home"].magnitude,
            config["microstep_factor"],
            config["acceleration_feed_forward"],
            config["trajectory"],
            f"{config['hardware_limit_configuration']}**",
        ]
        assert axis.read_setup() == config


def test_axis_get_status(mocker):
    """Get an axis status.

    Mock out `_newport_cmd` since tested elsewhere.
    """
    status = {
        "units": u.mm,
        "position": u.Quantity(1.0, u.mm),
        "desired_position": u.Quantity(2.0, u.mm),
        "desired_velocity": u.Quantity(3.0, u.mm / u.s),
        "is_motion_done": True,
    }
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis, "_newport_cmd")
        mock_cmd.side_effect = [
            "2",
            status["position"].magnitude,
            status["desired_position"].magnitude,
            status["desired_velocity"].magnitude,
            "1",
        ]
        assert axis.get_status() == status


@pytest.mark.parametrize("num", ik.newport.NewportESP301.Axis._unit_dict)
def test_axis_get_pq_unit(num):
    """Get units for specified axis."""
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        assert axis._get_pq_unit(num) == axis._unit_dict[num]


@pytest.mark.parametrize("num", ik.newport.NewportESP301.Axis._unit_dict)
def test_axis_get_unit_num(num):
    """Get unit number from dictionary.

    Skip number 1, since u.count appears twice in dictionary!
    """
    if num == 1:
        num = 0  # u.count twice
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        quant = axis._unit_dict[num]
        print(quant)
        assert axis._get_unit_num(quant) == num


def test_axis_get_unit_num_invalid_unit():
    """Raise KeyError if unit not valid."""
    invalid_unit = u.ly
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(KeyError) as err_info:
            axis._get_unit_num(invalid_unit)
        err_msg = err_info.value.args[0]
        assert err_msg == f"{invalid_unit} is not a valid unit for Newport " f"Axis"


def test_axis_newport_cmd(mocker):
    """Send command to parent class.

    Mock out parent classes `_newport_cmd` and assert call.
    """
    cmd = 123
    some_keyword = "keyword"
    with expected_protocol(
        ik.newport.NewportESP301, [ax_init[0]], [ax_init[1]], sep="\r"
    ) as inst:
        axis = inst.axis[0]
        mock_cmd = mocker.patch.object(axis._controller, "_newport_cmd")
        axis._newport_cmd(cmd, some_keyword=some_keyword)
        mock_cmd.assert_called_with(cmd, some_keyword=some_keyword)
