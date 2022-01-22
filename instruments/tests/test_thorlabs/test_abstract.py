#!/usr/bin/env python
"""
Module containing tests for the abstract ThorlabsInstrument class.
"""

# IMPORTS ####################################################################


import struct
import time

import pytest

import instruments as ik
from instruments.thorlabs import _packets
from instruments.tests import expected_protocol


# TESTS ######################################################################


example_packet = _packets.ThorLabsPacket(
    message_id=0x0000, param1=0x00, param2=0x00, dest=0x50, source=0x01, data=None
)


example_packet_with_data = _packets.ThorLabsPacket(
    message_id=0x0000,
    param1=None,
    param2=None,
    dest=0x50,
    source=0x01,
    data=struct.pack("<HH", 0, 1),
)


# pylint: disable=protected-access


def test_init():
    """Initialize the instrument and set terminator."""
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument, [], [], sep=""
    ) as inst:
        assert inst.terminator == ""


def test_send_packet():
    """Send a packet using write_raw."""
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument, [example_packet.pack()], [], sep=""
    ) as inst:
        inst.sendpacket(example_packet)


def test_query_packet(mocker):
    """Query the simple example packet without data.

    For simplicity, the query and response packet are the same.
    """
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument,
        [example_packet.pack()],
        [example_packet.pack()],
        sep="",
    ) as inst:
        read_raw_spy = mocker.spy(inst._file, "read_raw")
        packet_return = inst.querypacket(example_packet)
        assert packet_return.message_id == example_packet.message_id
        assert packet_return.parameters == example_packet.parameters
        assert packet_return.destination == example_packet.destination
        assert packet_return.source == example_packet.source
        assert packet_return.data == example_packet.data
        # assert read_raw is called with proper length
        read_raw_spy.assert_called_with(6)


def test_query_packet_with_data(mocker):
    """Query the simple example packet with data."""
    data_length = 4
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument,
        [example_packet.pack()],
        [example_packet_with_data.pack()],
        sep="",
    ) as inst:
        read_raw_spy = mocker.spy(inst._file, "read_raw")
        packet_return = inst.querypacket(example_packet, expect_data_len=data_length)
        assert packet_return.data == example_packet_with_data.data
        # assert read_raw is called with proper length
        read_raw_spy.assert_called_with(data_length + 6)


def test_query_packet_expect_none_no_respnse():
    """Query a packet but no response, none expected."""
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument, [example_packet.pack()], [], sep=""
    ) as inst:
        assert inst.querypacket(example_packet, expect=None) is None


def test_query_packet_expect_but_no_respnse():
    """Raise IO error when expecting a package but none returned."""
    expect = 0x0000
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument, [example_packet.pack()], [], sep=""
    ) as inst:
        with pytest.raises(IOError) as err_info:
            inst.querypacket(example_packet, expect=expect)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Expected packet {expect}, got nothing instead."


def test_query_packet_wrong_package_received():
    """Raise IOError if an unexpected package is received."""
    expect = 0x002A
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument,
        [example_packet.pack()],
        [example_packet.pack()],
        sep="",
    ) as inst:
        with pytest.raises(IOError) as err_info:
            inst.querypacket(example_packet, expect=expect)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"APT returned message ID "
            f"{example_packet.message_id}, expected {expect}"
        )


def test_query_packet_no_response_with_timeout(mocker):
    """Query a packet but no response, timeout is set."""
    with expected_protocol(
        ik.thorlabs._abstract.ThorLabsInstrument, [example_packet.pack()], [], sep=""
    ) as inst:
        time_spy = mocker.spy(time, "time")
        assert inst.querypacket(example_packet, timeout=0) is None
        # timeout set to zero, assert `time.time()`  called twice
        assert time_spy.call_count == 2
