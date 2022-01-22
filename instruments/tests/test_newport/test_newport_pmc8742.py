#!/usr/bin/env python
"""
Tests for the Newport Picomotor Controller 8742.
"""

# IMPORTS #####################################################################

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol

# pylint: disable=protected-access


# INSTRUMENT #


def test_init():
    """Initialize a new Picomotor PMC8742 instrument."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        assert inst.terminator == "\r\n"
        assert not inst.multiple_controllers


def test_controller_address():
    """Set and get controller address."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["SA2", "SA?"], ["2"], sep="\r\n"
    ) as inst:
        inst.controller_address = 2
        assert inst.controller_address == 2


def test_controller_configuration():
    """Set and get controller configuration."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        ["ZZ11", "ZZ11", "ZZ11", "ZZ?"],
        ["11"],
        sep="\r\n",
    ) as inst:
        inst.controller_configuration = 3
        inst.controller_configuration = 0b11
        inst.controller_configuration = "11"
        assert inst.controller_configuration == "11"


def test_dhcp_mode():
    """Set and get DHCP mode."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        ["IPMODE0", "IPMODE1", "IPMODE?"],
        ["1"],
        sep="\r\n",
    ) as inst:
        inst.dhcp_mode = False
        inst.dhcp_mode = True
        assert inst.dhcp_mode


def test_error_code():
    """Get error code."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["TE?"], ["0"], sep="\r\n"
    ) as inst:
        assert inst.error_code == 0


def test_error_code_and_message():
    """Get error code and message as tuple."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        ["TB?"],
        ["0, NO ERROR DETECTED"],
        sep="\r\n",
    ) as inst:
        err_expected = (0, "NO ERROR DETECTED")
        err_received = inst.error_code_and_message
        assert err_received == err_expected
        assert isinstance(err_received, tuple)


def test_firmware_version():
    """Get firmware version."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["VE?"], ["0123456789"], sep="\r\n"
    ) as inst:
        assert inst.firmware_version == "0123456789"


def test_gateway():
    """Set / get gateway."""
    ip_addr = "192.168.1.1"
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"GATEWAY {ip_addr}", "GATEWAY?"],
        [f"{ip_addr}"],
        sep="\r\n",
    ) as inst:
        inst.gateway = ip_addr
        assert inst.gateway == ip_addr


def test_hostname():
    """Set / get hostname."""
    host = "192.168.1.1"
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"HOSTNAME {host}", "HOSTNAME?"],
        [f"{host}"],
        sep="\r\n",
    ) as inst:
        inst.hostname = host
        assert inst.hostname == host


def test_ip_address():
    """Set / get ip address."""
    ip_addr = "192.168.1.1"
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"IPADDR {ip_addr}", "IPADDR?"],
        [f"{ip_addr}"],
        sep="\r\n",
    ) as inst:
        inst.ip_address = ip_addr
        assert inst.ip_address == ip_addr


def test_mac_address():
    """Set / get mac address."""
    mac_addr = "5827809, 8087"
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["MACADDR?"], [f"{mac_addr}"], sep="\r\n"
    ) as inst:
        assert inst.mac_address == mac_addr


def test_name():
    """Get name of the current instrument."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["*IDN?"], ["NAME"], sep="\r\n"
    ) as inst:
        assert inst.name == "NAME"


def test_netmask():
    """Set / get netmask."""
    ip_addr = "192.168.1.1"
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"NETMASK {ip_addr}", "NETMASK?"],
        [f"{ip_addr}"],
        sep="\r\n",
    ) as inst:
        inst.netmask = ip_addr
        assert inst.netmask == ip_addr


def test_scan_controller():
    """Scan connected controllers."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["SC?"], ["11"], sep="\r\n"
    ) as inst:
        assert inst.scan_controllers == "11"


def test_scan_done():
    """Query if a controller scan is completed."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["SD?", "SD?"], ["1", "0"], sep="\r\n"
    ) as inst:
        assert inst.scan_done
        assert not inst.scan_done


def test_abort_motion():
    """Abort all motion."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["AB"], [], sep="\r\n"
    ) as inst:
        inst.abort_motion()


def test_motor_check():
    """Check the connected motors."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["MC"], [], sep="\r\n"
    ) as inst:
        inst.motor_check()


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_scan(mode):
    """Scan address configuration of motors for default and other modes."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["SC2", f"SC{mode}"], [], sep="\r\n"
    ) as inst:
        inst.scan()
        inst.scan(mode)


def test_purge():
    """Purge the memory."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["XX"], [], sep="\r\n"
    ) as inst:
        inst.purge()


@pytest.mark.parametrize("mode", [0, 1])
def test_recall_parameters(mode):
    """Recall parameters, by default the factory set values."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["*RCL0", f"*RCL{mode}"], [], sep="\r\n"
    ) as inst:
        inst.recall_parameters()
        inst.recall_parameters(mode)


def test_reset():
    """Soft reset of the controller."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["*RST"], [], sep="\r\n"
    ) as inst:
        inst.reset()


def test_save_settings():
    """Save settings of the controller."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["SM"], [], sep="\r\n"
    ) as inst:
        inst.save_settings()


def test_query_bad_header():
    """Ensure stripping of bad header if present, see comment in query."""
    retval = b"\xff\xfd\x03\xff\xfb\x01192.168.2.161"
    val_expected = "192.168.2.161"
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["IPADDR?"], [retval], sep="\r\n"
    ) as inst:
        assert inst.ip_address == val_expected


# AXIS SPECIFIC COMMANDS - CONTROLLER COMMANDS PER AXIS TESTED ABOVE #


@given(ax=st.integers(min_value=0, max_value=3))
def test_axis_returns(ax):
    """Return axis with given axis number testing all valid axes."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[ax]
        assert isinstance(axis, ik.newport.PicoMotorController8742.Axis)
        assert axis._parent == inst
        assert axis._idx == ax + 1
        assert axis._address == ""


def test_axis_returns_type_error():
    """Raise TypeError if parent class is not PicoMotorController8742."""
    with pytest.raises(TypeError):
        _ = ik.newport.PicoMotorController8742.Axis(0, 0)


@given(ax=st.integers(min_value=4))
def test_axis_return_index_error(ax):
    """Raise IndexError if axis out of bounds and in one controller mode."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        with pytest.raises(IndexError):
            _ = inst.axis[ax]


@given(val=st.integers(min_value=1, max_value=200000))
def test_axis_acceleration(val):
    """Set / get axis acceleration unitful and without units."""
    val_unit = u.Quantity(val, u.s ** -2)
    val_unit_other = val_unit.to(u.min ** -2)
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1AC{val}", f"1AC{val}", "1AC?"],
        [f"{val}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.acceleration = val
        axis.acceleration = val_unit_other
        assert axis.acceleration == val_unit


@given(val=st.integers().filter(lambda x: not 1 <= x <= 200000))
def test_axis_acceleration_value_error(val):
    """Raise ValueError if acceleration out of range."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.acceleration = val


@given(val=st.integers(min_value=-2147483648, max_value=2147483647))
def test_axis_home_position(val):
    """Set / get axis home position."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1DH{val}", "1DH?"],
        [f"{val}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.home_position = val
        assert axis.home_position == val


@pytest.mark.parametrize("val", [-2147483649, 2147483648])
def test_axis_home_position_value_error(val):
    """Raise ValueError if home position out of range."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.home_position = val


@pytest.mark.parametrize("val", ["0", "1"])
def test_axis_is_stopped(val):
    """Query if axis is stopped."""
    exp_result = True if val == "1" else False
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["1MD?"], [f"{val}"], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        assert axis.is_stopped == exp_result


@pytest.mark.parametrize("val", ik.newport.PicoMotorController8742.Axis.MotorType)
def test_axis_motor_type(val):
    """Set / get motor type."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1QM{val.value}", "1QM?"],
        [f"{val.value}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.motor_type = val
        assert axis.motor_type == val


def test_axis_motor_type_wrong_type():
    """Raise TypeError if not appropriate motor type."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(TypeError):
            axis.motor_type = 2


@given(val=st.integers(min_value=-2147483648, max_value=2147483647))
def test_axis_move_absolute(val):
    """Set / get axis move absolute."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1PA{val}", "1PA?"],
        [f"{val}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.move_absolute = val
        assert axis.move_absolute == val


@pytest.mark.parametrize("val", [-2147483649, 2147483648])
def test_axis_move_absolute_value_error(val):
    """Raise ValueError if move absolute out of range."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.move_absolute = val


@given(val=st.integers(min_value=-2147483648, max_value=2147483647))
def test_axis_move_relative(val):
    """Set / get axis move relative."""
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1PR{val}", "1PR?"],
        [f"{val}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.move_relative = val
        assert axis.move_relative == val


@pytest.mark.parametrize("val", [-2147483649, 2147483648])
def test_axis_move_relative_value_error(val):
    """Raise ValueError if move relative out of range."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.move_relative = val


def test_axis_position():
    """Query position of an axis."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["1TP?"], ["42"], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        assert axis.position == 42


@given(val=st.integers(min_value=1, max_value=2000))
def test_axis_velocity(val):
    """Set / get axis velocity, unitful and unitless."""
    val_unit = u.Quantity(val, 1 / u.s)
    val_unit_other = val_unit.to(1 / u.hour)
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"1QM?", f"1VA{val}", f"1QM?", f"1VA{val}", "1VA?"],
        ["3", "3", f"{val}"],
        sep="\r\n",
    ) as inst:
        axis = inst.axis[0]
        axis.velocity = val
        axis.velocity = val_unit_other
        assert axis.velocity == val_unit


@given(val=st.integers().filter(lambda x: not 1 <= x <= 2000))
@pytest.mark.parametrize("motor", [0, 1, 3])
def test_axis_velocity_value_error_regular(val, motor):
    """Raise ValueError if velocity is out of range for non-tiny motor."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["1QM?"], [f"{motor}"], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.velocity = val


@given(val=st.integers().filter(lambda x: not 1 <= x <= 1750))
def test_axis_velocity_value_error_tiny(val):
    """Raise ValueError if velocity is out of range for tiny motor."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, ["1QM?"], ["2"], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        with pytest.raises(ValueError):
            axis.velocity = val


@pytest.mark.parametrize("direction", ["+", "-"])
def test_axis_move_indefinite(direction):
    """Move axis indefinitely."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [f"1MV{direction}"], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        axis.move_indefinite(direction)


def test_axis_stop():
    """Stop axis."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [f"1ST"], [], sep="\r\n"
    ) as inst:
        axis = inst.axis[0]
        axis.stop()


# SOME ADDITIONAL TESTS FOR MAIN / SECONDARY CONTROLLER SETUP #


def test_multi_controllers():
    """Enable and disable multiple controllers."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        inst.multiple_controllers = True
        assert inst.multiple_controllers
        inst.multiple_controllers = False
        assert not inst.multiple_controllers


@given(ax=st.integers(min_value=0, max_value=31 * 4 - 1))
def test_axis_return_multi(ax):
    """Return axis properly for multi-controller setup."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        inst.multiple_controllers = True
        axis = inst.axis[ax]
        assert isinstance(axis, ik.newport.PicoMotorController8742.Axis)
        assert axis._parent == inst
        assert axis._idx == ax % 4 + 1
        assert axis._address == f"{ax // 4 + 1}>"


@given(ax=st.integers(min_value=124))
def test_axis_return_multi_index_error(ax):
    """Raise IndexError if axis out of bounds and in multi controller mode."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [], [], sep="\r\n"
    ) as inst:
        inst.multiple_controllers = True
        with pytest.raises(IndexError):
            _ = inst.axis[ax]


@given(ax=st.integers(min_value=0, max_value=31 * 4 - 1))
def test_axis_sendcmd_multi(ax):
    """Send correct command in multiple axis mode."""
    address = ax // 4 + 1
    axis = ax % 4 + 1
    with expected_protocol(
        ik.newport.PicoMotorController8742, [f"{address}>{axis}CMD"], [], sep="\r\n"
    ) as inst:
        inst.multiple_controllers = True
        axis = inst.axis[ax]
        axis.sendcmd("CMD")


@given(ax=st.integers(min_value=0, max_value=31 * 4 - 1))
def test_axis_query_multi(ax):
    """Query command in multiple axis mode and strip address routing."""
    address = ax // 4 + 1
    axis = ax % 4 + 1
    answer_expected = f"{axis}ANSWER"
    with expected_protocol(
        ik.newport.PicoMotorController8742,
        [f"{address}>{axis}CMD"],
        [f"{address}>{answer_expected}"],
        sep="\r\n",
    ) as inst:
        inst.multiple_controllers = True
        axis = inst.axis[ax]
        assert axis.query("CMD") == answer_expected


def test_axis_query_multi_io_error():
    """Raise IOError if query response from wrong controller."""
    with expected_protocol(
        ik.newport.PicoMotorController8742, [f"1>1CMD"], [f"4>1ANSWER"], sep="\r\n"
    ) as inst:
        inst.multiple_controllers = True
        axis = inst.axis[0]
        with pytest.raises(IOError):
            axis.query("CMD")
