#!/usr/bin/env python
"""
Module containing tests for the Agilis Controller
"""

# IMPORTS #####################################################################

import time

import pytest

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


# pylint: disable=protected-access


# FIXTURES #


@pytest.fixture(autouse=True)
def mock_time(mocker):
    """Mock `time.sleep` for and set to zero as autouse fixture."""
    return mocker.patch.object(time, "sleep", return_value=None)


# CONTROLLER TESTS #


def test_aguc2_enable_remote_mode():
    """
    Check enabling of remote mode.
    """
    with expected_protocol(ik.newport.AGUC2, ["MR", "ML"], [], sep="\r\n") as agl:
        agl.enable_remote_mode = True
        assert agl.enable_remote_mode is True
        agl.enable_remote_mode = False
        assert agl.enable_remote_mode is False


def test_aguc2_error_previous_command_no_error():
    """Test return of an error value (`No Error`) from previous command."""
    with expected_protocol(ik.newport.AGUC2, ["TE"], ["TE0"], sep="\r\n") as agl:
        assert agl.error_previous_command == "No error"


def test_aguc2_error_previous_command():
    """
    Check the call error of previous command routine. Note that the test will
    return "Error code must be given as an integer." will be returned because
    no actual error code is fed to the error message checker.
    """
    with expected_protocol(ik.newport.AGUC2, ["TE"], [], sep="\r\n") as agl:
        assert agl.error_previous_command == "Error code query failed."


def test_aguc2_firmware_version():
    """
    Check firmware version
    AG-UC2 v2.2.1
    """
    with expected_protocol(
        ik.newport.AGUC2, ["VE"], ["AG-UC2 v2.2.1"], sep="\r\n"
    ) as agl:
        assert agl.firmware_version == "AG-UC2 v2.2.1"


def test_aguc2_limit_status():
    """
    Check the limit status routine.
    """
    with expected_protocol(
        ik.newport.AGUC2, ["MR", "PH"], ["PH0"], sep="\r\n"  # initialize remote mode
    ) as agl:
        assert agl.limit_status == "PH0"


def test_aguc2_sleep_time():
    """
    Check setting, getting the sleep time.
    """
    with expected_protocol(ik.newport.AGUC2, [], [], sep="\r\n") as agl:
        agl.sleep_time = 3
        assert agl.sleep_time == 3
        with pytest.raises(ValueError):
            agl.sleep_time = -3.14


def test_aguc2_reset_controller():
    """
    Check reset controller function.
    """
    with expected_protocol(ik.newport.AGUC2, ["RS"], [], sep="\r\n") as agl:
        agl.reset_controller()
        assert agl.enable_remote_mode is False


def test_aguc2_ag_sendcmd():
    """
    Check agilis sendcommand wrapper.
    """
    with expected_protocol(
        ik.newport.AGUC2, ["MR"], [], sep="\r\n"  # some command, here remote mode
    ) as agl:
        agl.ag_sendcmd("MR")


def test_aguc2_ag_query():
    """
    Check agilis query wrapper.
    """
    with expected_protocol(
        ik.newport.AGUC2, ["VE"], ["AG-UC2 v2.2.1"], sep="\r\n"
    ) as agl:
        assert agl.ag_query("VE") == "AG-UC2 v2.2.1"


def test_aguc2_ag_query_io_error(mocker):
    """Respond with `Query timed out.` if IOError occurs."""
    # mock the query to raise an IOError
    io_error_mock = mocker.Mock()
    io_error_mock.side_effect = IOError
    mocker.patch.object(ik.newport.AGUC2, "query", io_error_mock)

    with expected_protocol(ik.newport.AGUC2, [], [], sep="\r\n") as agl:
        assert agl.ag_query("VE") == "Query timed out."


# AXIS TESTS #


@pytest.mark.parametrize("axis", ik.newport.AGUC2.Axes)
def test_aguc2_axis_init_enum(axis):
    """Initialize an axis externally with an enum."""
    with expected_protocol(ik.newport.AGUC2, [], [], sep="\r\n") as agl:
        ax = ik.newport.agilis.AGUC2.Axis(agl, axis)
        assert ax._ax == axis.value


def test_aguc2_axis_init_wrong_type():
    """Raise TypeError when not initialized from AGUC2 parent class."""
    with pytest.raises(TypeError) as err_info:
        ik.newport.agilis.AGUC2.Axis(42, ik.newport.AGUC2.Axes.X)
    err_msg = err_info.value.args[0]
    assert err_msg == "Don't do that."


@pytest.mark.parametrize("axis", ik.newport.AGUC2.Axes)
@pytest.mark.parametrize("still", (True, False))
def test_aguc2_axis_am_i_still(axis, still):
    """Check if axis is still or not."""
    with expected_protocol(
        ik.newport.AGUC2,
        [
            "MR",  # initialize remote mode
            f"{axis.value} TS",
        ],
        [f"{axis.value}TS {int(not still)}"],
        sep="\r\n",
    ) as agl:
        assert agl.axis[axis].am_i_still() == still


def test_aguc2_axis_am_i_still_io_error():
    """Raise IOError if max retries achieved."""
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 TS", "2 TS", "2 TS", "2 TS"],  # initialize remote mode
        [],
        sep="\r\n",
    ) as agl:
        with pytest.raises(IOError):
            agl.axis["X"].am_i_still(max_retries=1)
        with pytest.raises(IOError):
            agl.axis["Y"].am_i_still(max_retries=3)


@pytest.mark.parametrize("axis", ik.newport.AGUC2.Axes)
def test_aguc2_axis_axis_status_not_moving(axis):
    """Check status of axis and return axis not moving."""
    with expected_protocol(
        ik.newport.AGUC2,
        [
            "MR",  # initialize remote mode
            f"{axis.value} TS",
        ],
        [f"{axis.value}TS0"],
        sep="\r\n",
    ) as agl:
        assert agl.axis[axis].axis_status == "Ready (not moving)."


def test_aguc2_axis_axis_status():
    """
    Check the status of the axis. Note that the test will return
    "Status code query failed." since no instrument is connected.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 TS", "2 TS"],  # initialize remote mode
        [],
        sep="\r\n",
    ) as agl:
        assert agl.axis["X"].axis_status == "Status code query failed."
        assert agl.axis["Y"].axis_status == "Status code query failed."


def test_aguc2_axis_jog():
    """Get / set jog function."""
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 JA 3", "1 JA?", "2 JA -4", "2 JA?"],  # initialize remote mode
        ["1JA3", "2JA-4"],
        sep="\r\n",
    ) as agl:
        agl.axis["X"].jog = 3
        assert agl.axis["X"].jog == 3
        agl.axis["Y"].jog = -4
        assert agl.axis["Y"].jog == -4
        with pytest.raises(ValueError):
            agl.axis["X"].jog = -5
        with pytest.raises(ValueError):
            agl.axis["Y"].jog = 5


def test_aguc2_axis_number_of_steps():
    """
    Check the number of steps function.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        [
            "MR",  # initialize remote mode
            "1 TP",
        ],
        ["1TP0"],
        sep="\r\n",
    ) as agl:
        assert agl.axis["X"].number_of_steps == 0


def test_aguc2_axis_move_relative():
    """
    Check the move relative function.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 PR 1000", "1 PR?", "2 PR -340", "2 PR?"],  # initialize remote mode
        ["1PR1000", "2PR-340"],
        sep="\r\n",
    ) as agl:
        agl.axis["X"].move_relative = 1000
        assert agl.axis["X"].move_relative == 1000
        agl.axis["Y"].move_relative = -340
        assert agl.axis["Y"].move_relative == -340
        with pytest.raises(ValueError):
            agl.axis["X"].move_relative = 2147483648
        with pytest.raises(ValueError):
            agl.axis["Y"].move_relative = -2147483649


def test_aguc2_axis_move_to_limit():
    """
    Check for move to limit function.
    This function is UNTESTED to work, here simply command sending is checked
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "2 MA 3", "2 MA?"],  # initialize remote mode
        ["2MA42"],
        sep="\r\n",
    ) as agl:
        agl.axis["Y"].move_to_limit = 3
        assert agl.axis["Y"].move_to_limit == 42
        with pytest.raises(ValueError):
            agl.axis["Y"].move_to_limit = -5
        with pytest.raises(ValueError):
            agl.axis["X"].move_to_limit = 5


def test_aguc2_axis_step_amplitude():
    """
    Check for step amplitude function
    """
    with expected_protocol(
        ik.newport.AGUC2,
        [
            "MR",  # initialize remote mode
            "1 SU-?",
            "1 SU+?",
            "1 SU -35",
            "1 SU 47",
            "1 SU -23",
            "1 SU 13",
        ],
        ["1SU-35", "1SU+35"],
        sep="\r\n",
    ) as agl:
        assert agl.axis["X"].step_amplitude == (-35, 35)
        agl.axis["X"].step_amplitude = -35
        agl.axis["X"].step_amplitude = 47
        agl.axis["X"].step_amplitude = (-23, 13)
        with pytest.raises(ValueError):
            agl.axis["X"].step_amplitude = 0
        with pytest.raises(ValueError):
            agl.axis["Y"].step_amplitude = -51
        with pytest.raises(ValueError):
            agl.axis["Y"].step_amplitude = 51


def test_aguc2_axis_step_delay():
    """
    Check the step delay function.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "2 DL?", "1 DL 1000", "1 DL 200"],  # initialize remote mode
        ["2DL0"],
        sep="\r\n",
    ) as agl:
        assert agl.axis["Y"].step_delay == 0
        agl.axis["X"].step_delay = 1000
        agl.axis["X"].step_delay = 200
        with pytest.raises(ValueError):
            agl.axis["X"].step_delay = -1
        with pytest.raises(ValueError):
            agl.axis["Y"].step_delay = 2000001


def test_aguc2_axis_stop():
    """
    Check the stop function.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 ST", "2 ST"],  # initialize remote mode
        [],
        sep="\r\n",
    ) as agl:
        agl.axis["X"].stop()
        agl.axis["Y"].stop()


def test_aguc2_axis_zero_position():
    """
    Check the stop function.
    """
    with expected_protocol(
        ik.newport.AGUC2,
        ["MR", "1 ZP", "2 ZP"],  # initialize remote mode
        [],
        sep="\r\n",
    ) as agl:
        agl.axis["X"].zero_position()
        agl.axis["Y"].zero_position()


# FUNCTION TESTS #


def test_agilis_error_message():
    # regular error messages
    assert ik.newport.agilis.agilis_error_message(0) == "No error"
    assert (
        ik.newport.agilis.agilis_error_message(-6) == "Not allowed in " "current state"
    )
    # out of range integers
    assert ik.newport.agilis.agilis_error_message(1) == "An unknown error " "occurred."
    assert ik.newport.agilis.agilis_error_message(-7) == "An unknown error " "occurred."
    # non-integers
    assert (
        ik.newport.agilis.agilis_error_message(-7.5) == "Error code is "
        "not an integer."
    )
    assert (
        ik.newport.agilis.agilis_error_message("TE0") == "Error code is "
        "not an integer."
    )


def test_agilis_status_message():
    # regular status messages
    assert ik.newport.agilis.agilis_status_message(0) == "Ready (not moving)."
    assert (
        ik.newport.agilis.agilis_status_message(3)
        == "Moving to limit (currently executing "
        "`measure_current_position`, `move_to_limit`, or "
        "`move_absolute` command)."
    )
    # out of range integers
    assert (
        ik.newport.agilis.agilis_status_message(4) == "An unknown " "status occurred."
    )
    assert (
        ik.newport.agilis.agilis_status_message(-1) == "An unknown " "status occurred."
    )
    # non integers
    assert (
        ik.newport.agilis.agilis_status_message(3.14) == "Status code is "
        "not an integer."
    )
    assert (
        ik.newport.agilis.agilis_status_message("1TS0") == "Status code "
        "is not an "
        "integer."
    )
