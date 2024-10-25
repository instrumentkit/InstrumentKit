#!/usr/bin/env python
"""Tests for the Dressler Cesar 1312 RF generator."""

from hypothesis import HealthCheck, given, settings, strategies as st
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
    ) as rf:
        assert rf.retries == 3
        rf.retries = 5
        assert rf.retries == 5

        with pytest.raises(ValueError):
            rf.retries = -1


# TEST INSTRUMENT PROPERTIES #


def test_rf():
    """Set/get the RF output state."""
    RF_ON = bytes([0x08, 0x02, 0x0A])
    RF_ON_ANSW = bytes([0x09, 0x02, 0x00, 0x0B])
    RF_OFF = bytes([0x08, 0x01, 0x09])
    RF_OFF_ANSW = bytes([0x09, 0x01, 0x00, 0x08])
    with expected_protocol(
        ik.dressler.Cesar1312,
        [RF_ON, ACK, RF_OFF, ACK],
        [
            ACK,
            RF_ON_ANSW,
            ACK,
            RF_OFF_ANSW,
        ],
        sep="",
    ) as rf:
        # TODO: assert rf.rf == False
        rf.rf = True
        rf.rf = False
        # TODO: assert rf.rf == True


# TEST PRIVATE METHODS #


def test_make_pkg():
    """Create a package that can be sent to the instrument."""
    with expected_protocol(
        ik.dressler.Cesar1312,
        [],
        [],
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
    ) as rf:
        rf.address = addr
        header = rf._pack_header(addr, data_length)
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
    ) as rf:
        addr, dl = rf._unpack_header(hdr)
        assert addr == hdr_int >> 3
        assert dl == hdr_int & 0b00000111
