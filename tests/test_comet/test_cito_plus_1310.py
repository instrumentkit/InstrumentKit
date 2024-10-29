#!/usr/bin/env python
"""Test the Comet Cito Plus 1310 instrument."""

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.comet.cito_plus_1310 import _crc16 as crc16
from instruments.units import ureg as u
from tests import expected_protocol


def add_checksum(data: bytes) -> bytes:
    """Add a CRC-16 checksum to the data."""
    checksum = crc16(data)
    return data + checksum.to_bytes(2, "little")


# TEST CLASS PROPERTIES #


def test_name():
    """Get the instrument label as string."""
    label_exp = "Comet Cito Plus 1310"
    lbl_bytes = label_exp.encode("utf_8")

    cmd = bytes([0x0A, 0x41, 0x00, 0x0A, 0x00, 0x01])
    cmd = add_checksum(cmd)
    answ = bytes([0x0A, 0x41, len(lbl_bytes)]) + lbl_bytes
    answ = add_checksum(answ)

    with expected_protocol(
        ik.comet.CitoPlus1310,
        [cmd],
        [answ],
        sep="",
    ) as cito:
        assert cito.name == label_exp


def test_forward_power():
    """Read forward power from instrument."""
    cmd = bytes([0x0A, 0x41, 0x1F, 0x56, 0x00, 0x01])
    cmd = add_checksum(cmd)
    answ = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x03, 0xE8])  # 1000 W
    answ = add_checksum(answ)
    with expected_protocol(
        ik.comet.CitoPlus1310,
        [cmd],
        [answ],
        sep="",
    ) as cito:
        assert cito.forward_power == 1000 * u.W


def test_output_power():
    """Get/set output power."""
    cmd_set_1kW = bytes([0x0A, 0x42, 0x04, 0xB6, 0x00, 0x0F, 0x42, 0x40])
    cmd_set_1kW = add_checksum(cmd_set_1kW)
    cmd_query = bytes([0x0A, 0x41, 0x04, 0xB6, 0x00, 0x01])
    cmd_query = add_checksum(cmd_query)
    answ_1kW = bytes([0x0A, 0x41, 0x04, 0x00, 0x0F, 0x42, 0x40])
    answ_1kW = add_checksum(answ_1kW)
    with expected_protocol(
        ik.comet.CitoPlus1310,
        [
            cmd_set_1kW,
            cmd_query,
        ],
        [
            cmd_set_1kW,
            answ_1kW,
        ],
        sep="",
    ) as cito:
        cito.output_power = 1 * u.kW
        assert cito.output_power == 1 * u.kW


def test_reflected_power():
    """Read reflected power from instrument."""
    cmd = bytes([0x0A, 0x41, 0x1F, 0x55, 0x00, 0x01])
    cmd = add_checksum(cmd)
    answ = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x03, 0xE8])  # 1000 W
    answ = add_checksum(answ)
    with expected_protocol(
        ik.comet.CitoPlus1310,
        [cmd],
        [answ],
        sep="",
    ) as cito:
        assert cito.reflected_power == 1000 * u.W


def test_regulation_mode():
    """Set/get the regulation mode."""
    cmd_forward_power = bytes([0x0A, 0x42, 0x04, 0xB1, 0x00, 0x00, 0x00, 0x00])
    cmd_forward_power = add_checksum(cmd_forward_power)
    cmd_load_power = bytes([0x0A, 0x42, 0x04, 0xB1, 0x00, 0x00, 0x00, 0x01])
    cmd_load_power = add_checksum(cmd_load_power)
    cmd_read_mode = bytes([0x0A, 0x41, 0x04, 0xB1, 0x00, 0x01])
    cmd_read_mode = add_checksum(cmd_read_mode)
    answ_forward_power = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x00, 0x00])
    answ_forward_power = add_checksum(answ_forward_power)
    answ_load_power = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x00, 0x01])
    answ_load_power = add_checksum(answ_load_power)

    with expected_protocol(
        ik.comet.CitoPlus1310,
        [
            cmd_forward_power,
            cmd_read_mode,
            cmd_load_power,
            cmd_read_mode,
        ],
        [
            cmd_forward_power,
            answ_forward_power,
            cmd_load_power,
            answ_load_power,
        ],
        sep="",
    ) as cito:
        cito.regulation_mode = cito.RegulationMode.ForwardPower
        assert cito.regulation_mode == cito.RegulationMode.ForwardPower
        cito.regulation_mode = cito.RegulationMode.LoadPower
        assert cito.regulation_mode == cito.RegulationMode.LoadPower


def test_rf():
    """Set/get the RF state."""
    cmd_rf_on = bytes([0x0A, 0x42, 0x03, 0xE9, 0x00, 0x00, 0x00, 0x01])
    cmd_rf_on = add_checksum(cmd_rf_on)
    cmd_rf_off = bytes([0x0A, 0x42, 0x03, 0xE9, 0x00, 0x00, 0x00, 0x00])
    cmd_rf_off = add_checksum(cmd_rf_off)
    query_rf = bytes([0x0A, 0x41, 0x1F, 0x40, 0x00, 0x01])
    query_rf = add_checksum(query_rf)
    answ_rf_on = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x00, 0x00])
    answ_rf_on = add_checksum(answ_rf_on)
    answ_rf_off = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x00, 0x01])
    answ_rf_off = add_checksum(answ_rf_off)
    with expected_protocol(
        ik.comet.CitoPlus1310,
        [
            cmd_rf_on,
            query_rf,
            cmd_rf_off,
            query_rf,
        ],
        [
            cmd_rf_on,
            answ_rf_on,
            cmd_rf_off,
            answ_rf_off,
        ],
        sep="",
    ) as rf:
        rf.rf = True
        assert rf.rf
        rf.rf = False
        assert not rf.rf


def test_checksum_error_return_package():
    """Raise an OSError if the checksum of returned package is invalid."""
    query_rf = bytes([0x0A, 0x41, 0x1F, 0x40, 0x00, 0x01])
    query_rf = add_checksum(query_rf)
    answ_rf_on = bytes([0x0A, 0x41, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    with expected_protocol(
        ik.comet.CitoPlus1310,
        [query_rf],
        [answ_rf_on],
        sep="",
    ) as rf:
        with pytest.raises(OSError) as err:
            _ = rf.rf
        assert "CRC-16 checksum of returned package does not match" in err.value.args[0]


def test_unknown_parameter():
    """Raise an excpetion if illegal function code used."""
    cmd = bytes([0x0A, 0x41, 0x00, 0x00])
    cmd = add_checksum(cmd)
    answ = bytes([0x0A, 0xC1, 0x01])
    answ = add_checksum(answ)
    with expected_protocol(
        ik.comet.CitoPlus1310,
        [cmd],
        [answ],
        sep="",
    ) as cito:
        with pytest.raises(OSError) as err:
            cito.query(cmd)
        assert "Unknown parameter or illegal function code" in err.value.args[0]


def test_write_answer_package_no_match():
    """Raise exception if answer package of a write command does not match."""
    cmd_rf_on = bytes([0x0A, 0x42, 0x03, 0xE9, 0x00, 0x00, 0x00, 0x01])
    cmd_rf_on = add_checksum(cmd_rf_on)
    wrong_return = bytes([0x0A, 0x42, 0x04, 0xE9, 0x00, 0x00, 0x00, 0x01])
    wrong_return = add_checksum(wrong_return)

    with expected_protocol(
        ik.comet.CitoPlus1310,
        [cmd_rf_on],
        [wrong_return],
        sep="",
    ) as rf:
        with pytest.raises(OSError) as err:
            rf.rf = True
        assert "Received package does not match sent package" in err.value.args[0]


### TEST CHECKSUM FUNCTION ###


@pytest.mark.parametrize(
    "inp_out", [[bytes([0x00]), 0x0000], [bytes([0x31, 0xAE]), 0x2C94]]
)
def test_crc16(inp_out):
    """Test CRC16 calculation with some hand-calculated examples."""
    input, expected = inp_out
    assert crc16(input) == expected
