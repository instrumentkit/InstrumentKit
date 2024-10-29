#!/usr/bin/env python
"""Tests for the Dressler Cesar 1312 RF generator."""

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol

# CONSTANTS #


ACK = bytes([0x06])
NAK = bytes([0x15])


# TEST CLASS PROPERTIES #


def test_address():
    """Set/get the address of the instrument."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        assert rf.address == 0x01
        rf.address = 5
        assert rf.address == 5

        for addr in [-1, 32]:
            with pytest.raises(ValueError):
                rf.address = addr


def test_retries():
    """Set/get the number of retries."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        assert rf.retries == 3
        rf.retries = 5
        assert rf.retries == 5

        with pytest.raises(ValueError):
            rf.retries = -1


# TEST INSTRUMENT PROPERTIES #


def test_control_mode():
    """Get/set the control model."""
    read_mode = bytes([0x08, 0x9B, 0x93])
    read_mode_answ_front_panel = bytes([0x09, 0x9B, 0x06, 0x94])
    set_mode_host = bytes([0x09, 0x0E, 0x02, 0x05])
    set_mode_answ = bytes([0x09, 0x0E, 0x00, 0x07])
    read_mode_answ_host = bytes([0x09, 0x9B, 0x02, 0x90])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            read_mode,
            ACK,
            set_mode_host,
            ACK,
            read_mode,
            ACK,
        ],
        [
            ACK,
            read_mode_answ_front_panel,
            ACK,
            set_mode_answ,
            ACK,
            read_mode_answ_host,
        ],
        sep="",
    ) as rf:
        assert rf.control_mode == rf.ControlMode.FrontPanel
        rf.control_mode = rf.ControlMode.Host
        assert rf.control_mode == rf.ControlMode.Host


def test_name():
    """Get the supply type and size."""
    cmd_type = bytes([0x08, 0x80, 0x88])
    ascii_type = b"CESAR"
    ans_type = bytes([0x0D, 0x80]) + ascii_type
    ans_type += checksum(ans_type)
    cmd_size = bytes([0x08, 0x81, 0x89])
    ascii_size = b"_1312"
    ans_size = bytes([0x0D, 0x81]) + ascii_size
    ans_size += checksum(ans_size)
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            cmd_type,
            ACK,
            cmd_size,
            ACK,
        ],
        [
            ACK,
            ans_type,
            ACK,
            ans_size,
        ],
        sep="",
    ) as rf:
        assert rf.name == "CESAR_1312"


def test_output_power():
    """Get/set the output power of the RF generator."""
    set_power_1kW = bytes([0x0A, 0x08, 0xE8, 0x03, 0xE9])
    set_power_answ = bytes([0x09, 0x08, 0x00, 0x01])
    read_power = bytes([0x08, 0xA4, 0xAC])
    read_answ = bytes([0x0B, 0xA4, 0xE8, 0x03, 0x06, 0x42])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            set_power_1kW,
            ACK,
            set_power_1kW,
            ACK,
            read_power,
            ACK,
        ],
        [
            ACK,
            set_power_answ,
            ACK,
            set_power_answ,
            ACK,
            read_answ,
        ],
        sep="",
    ) as rf:
        rf.output_power = 1000
        rf.output_power = u.Quantity(1, u.kW)
        assert rf.output_power == u.Quantity(1000, u.W)


def test_regulation_mode():
    """Get/set regulation mode."""
    read_mode = bytes([0x08, 0x9A, 0x92])
    read_answ_load = bytes([0x09, 0x9A, 0x08, 0x9B])
    set_mode_fwd = bytes([0x09, 0x03, 0x06, 0x0C])
    set_mode_answ = bytes([0x09, 0x03, 0x00, 0x0A])
    read_answ_fwd = bytes([0x09, 0x9A, 0x06, 0x95])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            read_mode,
            ACK,
            set_mode_fwd,
            ACK,
            read_mode,
            ACK,
        ],
        [
            ACK,
            read_answ_load,
            ACK,
            set_mode_answ,
            ACK,
            read_answ_fwd,
        ],
        sep="",
    ) as rf:
        assert rf.regulation_mode == rf.RegulationMode.ExternalPower
        rf.regulation_mode = rf.RegulationMode.ForwardPower
        assert rf.regulation_mode == rf.RegulationMode.ForwardPower


def test_reflected_power():
    """Get the reflected power."""
    read_send = bytes([0x08, 0xA6, 0xAE])
    read_answ = bytes([0x0A, 0xA6, 0x01, 0x00, 0xAD])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            read_send,
            ACK,
        ],
        [ACK, read_answ],
        sep="",
    ) as rf:
        assert rf.reflected_power == u.Quantity(1, u.W)


def test_rf():
    """Set/get the RF output state."""
    rf_read = bytes([0x08, 0xA2, 0xAA])
    rf_read_answ_on = bytes([0x0C, 0xA2, 0x20, 0x00, 0x00, 0x00, 0x8E])
    rf_read_answ_off = bytes([0x0C, 0xA2, 0x00, 0x00, 0x00, 0x00, 0xAE])
    rf_on = bytes([0x08, 0x02, 0x0A])
    rf_on_answ = bytes([0x09, 0x02, 0x00, 0x0B])
    rf_off = bytes([0x08, 0x01, 0x09])
    rf_off_answ = bytes([0x09, 0x01, 0x00, 0x08])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            rf_read,
            ACK,
            rf_off,
            ACK,
            rf_on,
            ACK,
            rf_read,
            ACK,
        ],
        [
            ACK,
            rf_read_answ_off,
            ACK,
            rf_off_answ,
            ACK,
            rf_on_answ,
            ACK,
            rf_read_answ_on,
        ],
        sep="",
    ) as rf:
        assert not rf.rf
        rf.rf = False
        rf.rf = True
        assert rf.rf


def test_rf_cmd_invalid():
    """Raise OSError if acknowledgement of cmd fails after retries."""
    rf_read = bytes([0x08, 0xA2, 0xAA])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            rf_read,
            rf_read,
        ],
        [
            NAK,
            NAK,
        ],
        sep="",
    ) as rf:
        rf.retries = 1
        with pytest.raises(OSError):
            rf.rf


def test_rf_reply_invalid():
    """Raise OSError if acknowledgement of reply fails after retries."""
    rf_read = bytes([0x08, 0xA2, 0xAA])
    rf_read_answ_on = bytes([0x0C, 0xA2, 0x20, 0x00, 0x00, 0x00, 0xFF])  # bad checksum
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            rf_read,
            NAK,
            NAK,
        ],
        [
            ACK,
            rf_read_answ_on,
            rf_read_answ_on,
            rf_read_answ_on,
        ],
        sep="",
    ) as rf:
        rf.retries = 2
        with pytest.raises(OSError):
            rf.rf


def test_unknown_command():
    """Raise OSError if an unknown command is sent."""
    pkg_send = bytes([0x08, 0x00, 0x08])
    pkg_rec = bytes([0x09, 0x80, 0x63, 0xEA])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            pkg_send,
            ACK,
        ],
        [
            ACK,
            pkg_rec,
        ],
        sep="",
    ) as rf:
        with pytest.raises(OSError) as err:
            rf.sendcmd(rf._make_pkg(0))
        assert "Command not implemented" in err.value.args[0]


def test_device_returns_no_data():
    """Raise ValueError if device returned no data."""
    pkg_send = bytes([0x08, 0x00, 0x08])
    pkg_rec = bytes([0x08, 0x80, 0x88])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            pkg_send,
            ACK,
        ],
        [
            ACK,
            pkg_rec,
        ],
        sep="",
    ) as rf:
        with pytest.raises(ValueError) as err:
            rf.sendcmd(rf._make_pkg(0))
        assert "No data received from the device" in err.value.args[0]


def test_answer_longer_six_bytes():
    """Ensure that answers with data >6 bytes are handled correctly.

    Note: While the protocol describes this scenario and it is implemented
    into the query, the whole command book does not offer a single command
    where this case occurs. However, this might be different for other
    models.
    """
    pkg_send = bytes([0x08, 0x00, 0x08])
    rec_data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    pkg_rec = bytes([0x0F, 0x00, 0x08]) + rec_data
    pkg_rec += checksum(pkg_rec)
    with expected_protocol(
        ik.dressler.Cesar1312,
        [
            pkg_send,
            ACK,
        ],
        [
            ACK,
            pkg_rec,
        ],
        sep="",
    ) as rf:
        data = rf.query(rf._make_pkg(0))
        assert data == rec_data


# TEST PRIVATE METHODS #


def test_make_pkg():
    """Create a package that can be sent to the instrument."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        # simple query package with command 1
        pkg_exp = bytes([0b00001000, 0x01])
        pkg_exp += rf._calculate_checksum(pkg_exp)

        pkg = rf._make_pkg(1, None)
        assert pkg == pkg_exp

        pkg = rf._make_pkg(1)  # should be same as above
        assert pkg == pkg_exp

        # change address to 3 and send 4 bytes of 1024 to command 2
        pkg_exp = bytes([0b00011100, 0x02, 0x00, 0x04, 0x00, 0x00])
        pkg_exp += rf._calculate_checksum(pkg_exp)

        rf.address = 3
        pkg = rf._make_pkg(2, (1024).to_bytes(4, "little"))

        assert pkg == pkg_exp

        # some long command with lots of data, using the make data pkg
        rf.address = 1
        pkg_exp = bytes(
            [
                0b00001111,
                0x01,
                0x09,
                0x01,
                0x02,
                0x03,
                0x04,
                0x05,
                0x00,
                0x04,
                0x00,
                0x00,
            ]
        )
        data = rf._make_data([1, 1, 1, 1, 1, 4], [1, 2, 3, 4, 5, 1024])
        pkg_exp += rf._calculate_checksum(pkg_exp)

        pkg = rf._make_pkg(1, data)
        assert pkg == pkg_exp


def test_make_pkg_error():
    """Raise error if cmd is too large or data is too long."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        with pytest.raises(ValueError):
            rf._make_pkg(256, None)

        with pytest.raises(ValueError):
            rf._make_pkg(1, (1).to_bytes(256, "little"))


@given(values=st.lists(st.integers(min_value=0, max_value=255), min_size=1))
def test_checksum(values):
    """Assure that exclusive or of all bytes plus checksum is 0."""
    bts = bytes(values)
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        checksum = rf._calculate_checksum(bts)[0]
        for val in bts:
            checksum ^= val
        assert checksum == 0


@given(
    addr=st.integers(min_value=0, max_value=31),
    data_length=st.integers(min_value=0, max_value=255),
)
def test_pack_header(addr, data_length):
    """Pack the header of the package."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        rf.address = addr
        header = rf._pack_header(data_length)
        dl = 7 if data_length > 6 else data_length
        header_exp = (addr << 3) + dl
        assert header == header_exp


@given(hdr_int=st.integers(min_value=0, max_value=255))
def test_unpack_header(hdr_int):
    """Unpack a header to return address and data length."""
    hdr = hdr_int.to_bytes(1)
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
        sep="",
    ) as rf:
        addr, dl = rf._unpack_header(hdr)
        assert addr == hdr_int >> 3
        assert dl == hdr_int & 0b00000111


def checksum(values: bytes) -> bytes:
    """Calculate the checksum of the given values."""
    checksum = 0x00
    for val in values:
        checksum ^= val
    return bytes([checksum])
