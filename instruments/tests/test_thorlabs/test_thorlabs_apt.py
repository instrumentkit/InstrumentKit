#!/usr/bin/env python
"""
Module containing tests for the Thorlabs TC200
"""

# IMPORTS ####################################################################

# pylint: disable=unused-import,too-many-lines


import struct
import warnings

from hypothesis import given, strategies as st
import pytest
from instruments.units import ureg as u

import instruments as ik
from instruments.thorlabs._packets import ThorLabsPacket, hw_info_data
from instruments.thorlabs._cmds import ThorLabsCommands
from instruments.tests import expected_protocol

# TESTS ######################################################################

# pylint: disable=protected-access,unused-argument


hw_types_setup = (
    (45, "Multi-channel controller motherboard"),
    (44, "Brushless DC controller"),
    (3, "Unknown type: 3"),
)


@pytest.mark.parametrize("hw_type", hw_types_setup)
def test_apt_hw_info(hw_type):
    with expected_protocol(
        ik.thorlabs.ThorLabsAPT,
        [
            ThorLabsPacket(
                message_id=ThorLabsCommands.HW_REQ_INFO,
                param1=0x00,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack()
        ],
        [
            ThorLabsPacket(
                message_id=ThorLabsCommands.HW_GET_INFO,
                dest=0x01,
                source=0x50,
                data=hw_info_data.pack(
                    # Serial number
                    b"\x01\x02\x03\x04",
                    # Model number
                    b"ABC-123",
                    # HW type
                    hw_type[0],
                    # FW version,
                    0xA1,
                    0xA2,
                    0xA3,
                    # Notes
                    b"abcdefg",
                    # HW version
                    42,
                    # Mod state
                    43,
                    # Number of channels
                    2,
                ),
            ).pack()
        ],
        sep="",
    ) as apt:
        # Check internal representations.
        # NB: we shouldn't do this in some sense, but these fields
        #     act as an API to the APT subclasses.
        assert apt._hw_type == hw_type[1]
        assert apt._fw_version == "a1.a2.a3"
        assert apt._notes == "abcdefg"
        assert apt._hw_version == 42
        assert apt._mod_state == 43

        # Check external API.
        assert apt.serial_number == "01020304"
        assert apt.model_number == "ABC-123"
        assert apt.name == (
            "ThorLabs APT Instrument model ABC-123, "
            "serial 01020304 (HW version 42, FW version a1.a2.a3)"
        )


def test_apt_hw_info_io_error(mocker):
    inst_class = ik.thorlabs.ThorLabsAPT

    # mock querying a packet and raise an IOError
    io_error_mock = mocker.Mock()
    io_error_mock.side_effect = IOError
    mocker.patch.object(inst_class, "querypacket", io_error_mock)

    with expected_protocol(inst_class, [], [], sep="") as apt:
        # IOError was raised, assert that defaults are still present
        assert apt._serial_number is None
        assert apt._model_number is None
        assert apt._hw_type is None
        assert apt._fw_version is None
        assert apt._notes == ""
        assert apt._hw_version is None
        assert apt._mod_state is None
        assert apt._n_channels == 0
        assert apt._channel == ()


# FIXTURES FOR APT TEST SUITE #


@pytest.fixture
def init_kdc101():
    """Return the send, receive value to initialize a KIM101 unit."""
    stdin = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_REQ_INFO,
        param1=0x00,
        param2=0x00,
        dest=0x50,
        source=0x01,
        data=None,
    ).pack()
    stdout = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_GET_INFO,
        dest=0x01,
        source=0x50,
        data=hw_info_data.pack(
            # Serial number
            b"\x01\x02\x03\x04",
            # Model number
            b"KDC101",
            # HW type
            16,
            # FW version,
            0xA1,
            0xA2,
            0xA3,
            # Notes
            b"abcdefg",
            # HW version
            42,
            # Mod state
            43,
            # Number of channels
            1,
        ),
    ).pack()
    return stdin, stdout


@pytest.fixture
def init_kim101():
    """Return the send, receive value to initialize a KIM101 unit."""
    stdin = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_REQ_INFO,
        param1=0x00,
        param2=0x00,
        dest=0x50,
        source=0x01,
        data=None,
    ).pack()
    stdout = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_GET_INFO,
        dest=0x01,
        source=0x50,
        data=hw_info_data.pack(
            # Serial number
            b"\x01\x02\x03\x04",
            # Model number
            b"KIM101",
            # HW type
            16,
            # FW version,
            0xA1,
            0xA2,
            0xA3,
            # Notes
            b"abcdefg",
            # HW version
            42,
            # Mod state
            43,
            # Number of channels
            4,
        ),
    ).pack()
    return stdin, stdout


@pytest.fixture
def init_tim101():
    """Return the send, receive value to initialize a TIM101 unit.

    Currently only used to test failure modes.
    """
    stdin = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_REQ_INFO,
        param1=0x00,
        param2=0x00,
        dest=0x50,
        source=0x01,
        data=None,
    ).pack()
    stdout = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_GET_INFO,
        dest=0x01,
        source=0x50,
        data=hw_info_data.pack(
            # Serial number
            b"\x01\x02\x03\x04",
            # Model number
            b"TIM101",
            # HW type
            16,
            # FW version,
            0xA1,
            0xA2,
            0xA3,
            # Notes
            b"abcdefg",
            # HW version
            42,
            # Mod state
            43,
            # Number of channels
            4,
        ),
    ).pack()
    return stdin, stdout


@pytest.fixture
def init_ksg101():
    """Return the send, receive value to initialize a KSG101 unit."""
    stdin = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_REQ_INFO,
        param1=0x00,
        param2=0x00,
        dest=0x50,
        source=0x01,
        data=None,
    ).pack()
    stdout = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_GET_INFO,
        dest=0x01,
        source=0x50,
        data=hw_info_data.pack(
            # Serial number
            b"\x01\x02\x03\x04",
            # Model number
            b"KSG101",
            # HW type
            3,
            # FW version,
            0xA1,
            0xA2,
            0xA3,
            # Notes
            b"abcdefg",
            # HW version
            42,
            # Mod state
            43,
            # Number of channels
            1,
        ),
    ).pack()
    return stdin, stdout


@pytest.fixture
def init_kpz001():
    """Return the send, receive value to initialize a KPZ001 unit."""
    stdin = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_REQ_INFO,
        param1=0x00,
        param2=0x00,
        dest=0x50,
        source=0x01,
        data=None,
    ).pack()
    stdout = ThorLabsPacket(
        message_id=ThorLabsCommands.HW_GET_INFO,
        dest=0x01,
        source=0x50,
        data=hw_info_data.pack(
            # Serial number
            b"\x01\x02\x03\x04",
            # Model number
            b"KPZ101",
            # HW type
            3,
            # FW version,
            0xA1,
            0xA2,
            0xA3,
            # Notes
            b"abcdefg",
            # HW version
            42,
            # Mod state
            43,
            # Number of channels
            1,
        ),
    ).pack()
    return stdin, stdout


# pylint: disable=redefined-outer-name


# TESTS FOR APT PIEZO INERTIA ACTUATOR CLASS (APT_PIA) #


# CHANNELS #


def test_apt_pia_channel_drive_op_parameters(init_kim101):
    """Test the drive op parameters for the APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # receive a package
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x07,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # send a packet
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HHHll", 0x07, 0x01, 100, 1000, 10000),
            ).pack(),
        ],
        [
            init_kim101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                dest=0x01,
                source=0x50,
                data=struct.pack("<HHHll", 0x07, 0x01, 90, 500, 5000),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].drive_op_parameters == [
            u.Quantity(90, u.V),
            u.Quantity(500, 1 / u.s),
            u.Quantity(5000, 1 / u.s ** 2),
        ]
        apt.channel[0].drive_op_parameters = [
            u.Quantity(100, u.V),
            u.Quantity(1000, 1 / u.s),
            u.Quantity(10000, 1 / u.s ** 2),
        ]


def test_apt_pia_channel_drive_op_parameters_exceptions(init_kim101):
    """Raise exceptions in drive op parameters: APT Piezo Inertia Actuator."""
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator, [init_kim101[0]], [init_kim101[1]], sep=""
    ) as apt:
        # wrong type of parameters
        with pytest.raises(TypeError):
            apt.channel[0].drive_op_parameters = 42

        # wrong list length
        with pytest.raises(ValueError):
            apt.channel[0].drive_op_parameters = [42, 42]

        # parameters out of range
        with pytest.raises(ValueError):
            apt.channel[0].drive_op_parameters = [1, 1000, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].drive_op_parameters = [100, 2500, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].drive_op_parameters = [100, 1000, 100001]


def test_apt_pia_channel_enabled_single(init_kim101):
    """Enable a single channel for the APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2B,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # disable all channels
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x00),
            ).pack(),
        ],
        [
            init_kim101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                param1=None,
                param2=None,
                dest=0x01,
                source=0x50,
                data=struct.pack("<HH", 0x2B, 0x01),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].enabled_single
        apt.channel[0].enabled_single = False


def test_apt_pia_channel_enabled_single_wrong_controller(init_tim101):
    """Raise TypeError when called with from non-KIM controller."""
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator, [init_tim101[0]], [init_tim101[1]], sep=""
    ) as apt:
        with pytest.raises(TypeError):
            assert apt.channel[0].enabled_single
        with pytest.raises(TypeError):
            apt.channel[0].enabled_single = True


def test_apt_pia_channel_jog_parameters(init_kim101):
    """Test the jog parameters for the APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # receive a package
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2D,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # send a packet
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HHHllll", 0x2D, 0x01, 2, 100, 100, 1000, 10000),
            ).pack(),
        ],
        [
            init_kim101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                dest=0x01,
                source=0x50,
                data=struct.pack("<HHHllll", 0x2D, 0x01, 1, 500, 1000, 400, 5000),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].jog_parameters == [
            1,
            500,
            1000,
            u.Quantity(400, 1 / u.s),
            u.Quantity(5000, 1 / u.s ** 2),
        ]
        apt.channel[0].jog_parameters = [
            2,
            100,
            100,
            u.Quantity(1000, 1 / u.s),
            u.Quantity(10000, 1 / u.s ** 2),
        ]

        # invalid setter
        with pytest.raises(TypeError):
            apt.channel[0].jog_parameters = 3.14
        # list out of range
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [42, 42]
        # invalid parameters
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [0, 100, 100, 1000, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [2, 0, 100, 1000, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [2, 100, 2500, 1000, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [2, 100, 100, 2500, 10000]
        with pytest.raises(ValueError):
            apt.channel[0].jog_parameters = [2, 100, 100, 1000, 100001]


def test_apt_pia_channel_jog_parameters_invalid_controller(init_tim101):
    """Throw error when trying to set jog parameters for wrong controller."""
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator, [init_tim101[0]], [init_tim101[1]], sep=""
    ) as apt:
        with pytest.raises(TypeError):
            assert apt.channel[0].jog_parameters == [2, 100, 100, 1000, 1000]
        with pytest.raises(TypeError):
            apt.channel[0].jog_parameters = [2, 100, 100, 1000, 1000]


def test_apt_pia_channel_position_count(init_kim101):
    """Get / Set position count for APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # receive a package
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x05,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # send a packet
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HHll", 0x05, 0x03, 100, 0x00),
            ).pack(),
        ],
        [
            init_kim101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                dest=0x01,
                source=0x50,
                data=struct.pack("<HHll", 0x05, 0x01, 0, 0),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].position_count == 0
        apt.channel[2].position_count = 100


def test_apt_pia_channel_move_abs(init_kim101):
    """Absolute movement of APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_MOVE_ABSOLUTE,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, 100),
            ).pack(),
        ],
        [init_kim101[1]],
        sep="",
    ) as apt:
        apt.channel[0].move_abs(100)


def test_apt_pia_channel_move_jog(init_kim101):
    """Jog forward and reverse with APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # forward
                message_id=ThorLabsCommands.PZMOT_MOVE_JOG,
                param1=0x01,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # reverse
                message_id=ThorLabsCommands.PZMOT_MOVE_JOG,
                param1=0x01,
                param2=0x02,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kim101[1]],
        sep="",
    ) as apt:
        apt.channel[0].move_jog()
        apt.channel[0].move_jog("rev")


def test_apt_pia_channel_move_jog_stop(init_kim101):
    """Jog forward and reverse with APT Piezo Inertia Actuator.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # no direction -> stop
                message_id=ThorLabsCommands.PZMOT_MOVE_JOG,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kim101[1]],
        sep="",
    ) as apt:
        apt.channel[0].move_jog_stop()


# CONTROLLER #


def test_apt_pia_enabled_multi(init_kim101):
    """Multi-channel enabling APT Piezo Inertia Actuator KIM101.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator,
        [
            init_kim101[0],
            ThorLabsPacket(  # all off
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2B,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # read channel 0 & 1
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2B,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # read channel 2 & 3
                message_id=ThorLabsCommands.PZMOT_REQ_PARAMS,
                param1=0x2B,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # send off
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x00),
            ).pack(),
            ThorLabsPacket(  # send ch 0 & 1
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x05),
            ).pack(),
            ThorLabsPacket(  # send ch 2 & 3
                message_id=ThorLabsCommands.PZMOT_SET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x06),
            ).pack(),
        ],
        [
            init_kim101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x00),
            ).pack(),
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x05),
            ).pack(),
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZMOT_GET_PARAMS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x2B, 0x06),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.enabled_multi == 0
        assert apt.enabled_multi == 1
        assert apt.enabled_multi == 2
        apt.enabled_multi = 0
        apt.enabled_multi = 1
        apt.enabled_multi = 2

        # Invalid controller chosen
        with pytest.raises(ValueError):
            apt.enabled_multi = 42


def test_apt_pia_enabled_multi_wrong_controller(init_tim101):
    """Multi-channel enabling APT Piezo Inertia Actuator TIM101.

    Tested with KIM101 driver connected to PIM1 mirror mount.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator, [init_tim101[0]], [init_tim101[1]], sep=""
    ) as apt:
        with pytest.raises(TypeError):
            apt.enabled_multi = 42
        with pytest.raises(TypeError):
            assert apt.enabled_multi == 1


def test_apt_pia_enabled_type_error(init_kim101):
    """Raise Type Error and give feedback when trying to use enabled.

    Implemented at parent class level and KIM101 should respond to it,
    however, it does not. Enabling channels is implmented. Unclear if
    this is an error in the manual.
    """
    with expected_protocol(
        ik.thorlabs.APTPiezoInertiaActuator, [init_kim101[0]], [init_kim101[1]], sep=""
    ) as apt:
        with pytest.raises(TypeError):
            assert apt.channel[0].enabled


# APT PIEZO STAGE (APT_PS) #


def test_apt_ps_max_travel_no_response(init_kpz001):
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.PZ_REQ_MAXTRAVEL,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kpz001[1]],
        sep="",
    ) as apt:
        assert apt.channel[0].max_travel == NotImplemented


def test_apt_ps_led_intensity(init_kpz001):
    """Get / set LED intensity between zero and 1."""
    led_intensity = 0.73
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(  # set state
                message_id=ThorLabsCommands.PZ_SET_TPZ_DISPSETTINGS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<H", int(round(255 * led_intensity))),
            ).pack(),
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.PZ_REQ_TPZ_DISPSETTINGS,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kpz001[1],
            ThorLabsPacket(  # get state
                message_id=ThorLabsCommands.PZ_GET_TPZ_DISPSETTINGS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<H", int(round(255 * led_intensity))),
            ).pack(),
        ],
        sep="",
    ) as apt:
        apt.led_intensity = led_intensity
        assert apt.led_intensity == pytest.approx(led_intensity, 1.0 / 255)


def test_apt_ps_led_intensity_no_response(init_kpz001):
    """No response when setting the display."""
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.PZ_REQ_TPZ_DISPSETTINGS,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kpz001[1]],
        sep="",
    ) as apt:
        assert apt.led_intensity == NotImplemented


@pytest.mark.parametrize("value", (0x01, 0x02, 0x03, 0x04))
def test_apt_ps_position_control_closed(init_kpz001, value):
    """Get the status if the position control is closed or not."""
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_REQ_POSCONTROLMODE,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kpz001[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_GET_POSCONTROLMODE,
                param1=0x01,
                param2=value,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].position_control_closed == bool(value - 1 & 1)


@pytest.mark.parametrize("closed", (True, False))
@pytest.mark.parametrize("smooth", (True, False))
def test_apt_ps_change_position_control_mode(init_kpz001, closed, smooth):
    """Set the position control mode."""
    mode = 1 + (int(closed) | int(smooth) << 1)
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_SET_POSCONTROLMODE,
                param1=0x01,
                param2=mode,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kpz001[1]],
        sep="",
    ) as apt:
        apt.channel[0].change_position_control_mode(closed, smooth=smooth)


@given(position=st.integers(min_value=0, max_value=32767))
def test_apt_ps_output_position(init_kpz001, position):
    """Get / set output position for piezo channel."""
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_kpz001[0],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_SET_OUTPUTPOS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x01, position),
            ).pack(),
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_REQ_OUTPUTPOS,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kpz001[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_GET_OUTPUTPOS,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x01, position),
            ).pack(),
        ],
        sep="",
    ) as apt:
        apt.channel[0].output_position = position
        assert apt.channel[0].output_position == position


# APT STRAIN GAUGE READER (APT SGR) #


def test_apt_sgr_max_travel(init_ksg101):
    value = 10000
    with expected_protocol(
        ik.thorlabs.APTPiezoStage,
        [
            init_ksg101[0],
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.PZ_REQ_MAXTRAVEL,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_ksg101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.PZ_GET_MAXTRAVEL,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HH", 0x01, value),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].max_travel == value * u.Quantity(100, "nm")


# APT MOTOR CONTROLLER (APT_MC) #


def test_apt_mc_motion_timeout(init_kdc101):
    """Set and get motion timeout."""
    with expected_protocol(
        ik.thorlabs.APTMotorController, [init_kdc101[0]], [init_kdc101[1]], sep=""
    ) as apt:
        apt.channel[0].motion_timeout = u.Quantity(100, u.s)
        assert apt.channel[0].motion_timeout == u.Quantity(100, u.s)


def test_apt_mc_enabled(init_kdc101):
    """Enable the channel and read status back."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # read state
                message_id=ThorLabsCommands.MOD_REQ_CHANENABLESTATE,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # write state
                message_id=ThorLabsCommands.MOD_SET_CHANENABLESTATE,
                param1=0x01,
                param2=0x01,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(  # return False
                message_id=ThorLabsCommands.MOD_GET_CHANENABLESTATE,
                param1=0x01,
                param2=0x02,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert not apt.channel[0].enabled
        apt.channel[0].enabled = True


def test_apt_mc_set_scale(init_kdc101, mocker):
    """Set the scale using the depreciated set scale routine.

    Assert that a warning was raised.
    """
    mock_warning = mocker.patch.object(warnings, "warn")
    with expected_protocol(
        ik.thorlabs.APTMotorController, [init_kdc101[0]], [init_kdc101[1]], sep=""
    ) as apt:
        apt.channel[0].set_scale("PRM1-Z8")
        mock_warning.assert_called_with(
            "The set_scale method has been deprecated in favor "
            "of the motor_model property.",
            DeprecationWarning,
        )


def test_apt_mc_motor_model(init_kdc101):
    """Set / Get the motor model."""
    with expected_protocol(
        ik.thorlabs.APTMotorController, [init_kdc101[0]], [init_kdc101[1]], sep=""
    ) as apt:
        apt.channel[0].motor_model = "PRM1-Z8"
        assert apt.channel[0].motor_model == "PRM1-Z8"


def test_apt_mc_motor_model_invalid_model(init_kdc101):
    """Try setting an invalid motor model."""
    with expected_protocol(
        ik.thorlabs.APTMotorController, [init_kdc101[0]], [init_kdc101[1]], sep=""
    ) as apt:
        apt.scale_factors = 42  # set to some value
        apt.channel[0].motor_model = "INVALID"
        assert apt.scale_factors == 42  # assert it hasn't changed


apt_mc_channel_status_bit_mask = {
    "CW_HARD_LIM": 0x00000001,
    "CCW_HARD_LIM": 0x00000002,
    "CW_SOFT_LIM": 0x00000004,
    "CCW_SOFT_LIM": 0x00000008,
    "CW_MOVE_IN_MOTION": 0x00000010,
    "CCW_MOVE_IN_MOTION": 0x00000020,
    "CW_JOG_IN_MOTION": 0x00000040,
    "CCW_JOG_IN_MOTION": 0x00000080,
    "MOTOR_CONNECTED": 0x00000100,
    "HOMING_IN_MOTION": 0x00000200,
    "HOMING_COMPLETE": 0x00000400,
    "INTERLOCK_STATE": 0x00001000,
}


@pytest.mark.parametrize("status_bits", apt_mc_channel_status_bit_mask.values())
def test_apt_mc_status_bits(init_kdc101, status_bits):
    """Get status bits."""
    status_dict_expected = {
        key: (status_bits & bit_mask > 0)
        for key, bit_mask in apt_mc_channel_status_bit_mask.items()
    }

    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # read position
                message_id=ThorLabsCommands.MOT_REQ_STATUSUPDATE,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.MOT_GET_POSCOUNTER,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<HLLL", 0x01, 0x01, 0x01, status_bits),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].status_bits == status_dict_expected


def test_apt_mc_position(init_kdc101):
    """Get unitful position of controller."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # read position
                message_id=ThorLabsCommands.MOT_REQ_POSCOUNTER,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.MOT_GET_POSCOUNTER,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, -20000),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert (
            apt.channel[0].position
            == u.Quantity(-20000, "counts") / apt.channel[0].scale_factors[0]
        )


def test_apt_mc_position_encoder(init_kdc101):
    """Get unitful position of encoder, in counts."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # read position
                message_id=ThorLabsCommands.MOT_REQ_ENCCOUNTER,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(
                message_id=ThorLabsCommands.MOT_GET_ENCCOUNTER,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, -20000),
            ).pack(),
        ],
        sep="",
    ) as apt:
        assert apt.channel[0].position_encoder == u.Quantity(-20000, "counts")


def test_apt_mc_go_home(init_kdc101):
    """Homing routine."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # read position
                message_id=ThorLabsCommands.MOT_MOVE_HOME,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(  # homing complete package
                message_id=ThorLabsCommands.MOT_MOVE_HOMED,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        sep="",
    ) as apt:
        apt.channel[0].go_home()


def test_apt_mc_move(init_kdc101):
    """Move the stage."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # encoder count, absolute move
                message_id=ThorLabsCommands.MOT_MOVE_ABSOLUTE,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, 1000),
            ).pack(),
            ThorLabsPacket(  # encoder count, relative move
                message_id=ThorLabsCommands.MOT_MOVE_RELATIVE,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, -1000),
            ).pack(),
            ThorLabsPacket(  # encoder count, absolute move
                message_id=ThorLabsCommands.MOT_MOVE_ABSOLUTE,
                param1=None,
                param2=None,
                dest=0x50,
                source=0x01,
                data=struct.pack("<Hl", 0x01, 1919),
            ).pack(),
        ],
        [
            init_kdc101[1],
            ThorLabsPacket(  # move complete message
                message_id=ThorLabsCommands.MOT_MOVE_COMPLETED,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # move complete message
                message_id=ThorLabsCommands.MOT_MOVE_COMPLETED,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
            ThorLabsPacket(  # move complete message
                message_id=ThorLabsCommands.MOT_MOVE_COMPLETED,
                param1=0x01,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        sep="",
    ) as apt:
        apt.channel[0].move(1000)
        apt.channel[0].move(u.Quantity(-1000, "counts"), absolute=False)

        # unitful motion: requires motor to be initialized
        apt.channel[0].motor_model = "PRM1-Z8"
        apt.channel[0].move(u.Quantity(1, u.deg))

        # raise error if units are wrong
        with pytest.raises(ValueError):
            apt.channel[0].move(u.Quantity(5, u.mm))


# CONTROLLER #


def test_apt_mc_identify(init_kdc101):
    """Identify the controller by blinking its LEDs."""
    with expected_protocol(
        ik.thorlabs.APTMotorController,
        [
            init_kdc101[0],
            ThorLabsPacket(  # write state
                message_id=ThorLabsCommands.MOD_IDENTIFY,
                param1=0x00,
                param2=0x00,
                dest=0x50,
                source=0x01,
                data=None,
            ).pack(),
        ],
        [init_kdc101[1]],
        sep="",
    ) as apt:
        apt.identify()


@pytest.mark.parametrize("n_ch", (0, 1, 2))
def test_apt_mc_n_channels(init_kdc101, n_ch):
    """Get / Set the number of channels."""
    with expected_protocol(
        ik.thorlabs.APTMotorController, [init_kdc101[0]], [init_kdc101[1]], sep=""
    ) as apt:
        # print(type(apt._channel))
        apt.n_channels = n_ch
        assert apt.n_channels == n_ch
