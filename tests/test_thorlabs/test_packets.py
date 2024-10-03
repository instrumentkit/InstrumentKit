#!/usr/bin/env python
"""
Module containing tests for the ThorLabsPacket class.
"""

# IMPORTS ####################################################################


import struct

import pytest

from instruments.thorlabs import _packets


# TESTS ######################################################################


# pylint: disable=protected-access,redefined-outer-name


# variable to parametrize parameters or data: param1, param2, data, has_data
params_or_data = (
    (0x00, 0x00, None, False),
    (None, None, struct.pack("<HH", 0x00, 0x01), True),
)


@pytest.mark.parametrize("params_or_data", params_or_data)
def test_init(params_or_data):
    """Initialize a Thorlabs packet without data."""
    message_id = 0x0000
    param1 = params_or_data[0]
    param2 = params_or_data[1]
    dest = 0x50
    source = 0x01
    data = params_or_data[2]
    pkt = _packets.ThorLabsPacket(
        message_id=message_id,
        param1=param1,
        param2=param2,
        dest=dest,
        source=source,
        data=data,
    )
    # assert that variables are set correctly
    assert pkt._message_id == message_id
    assert pkt._param1 == param1
    assert pkt._param2 == param2
    assert pkt._data == data
    assert pkt._dest == dest
    assert pkt._source == source
    assert pkt._has_data is params_or_data[3]


def test_init_no_params_no_data():
    """Raise ValueError if package initialized without parameters or data."""
    message_id = 0x0000
    param1 = None
    param2 = None
    dest = 0x50
    source = 0x01
    data = None
    with pytest.raises(ValueError) as err_info:
        _ = _packets.ThorLabsPacket(
            message_id=message_id,
            param1=param1,
            param2=param2,
            dest=dest,
            source=source,
            data=data,
        )
    err_msg = err_info.value.args[0]
    assert err_msg == "Must specify either parameters or data."


def test_init_params_and_data():
    """Raise ValueError if package initialized with parameters and data."""
    message_id = 0x0000
    param1 = 0x00
    param2 = 0x00
    dest = 0x50
    source = 0x01
    data = struct.pack("<HH", 0x00, 0x01)
    with pytest.raises(ValueError) as err_info:
        _ = _packets.ThorLabsPacket(
            message_id=message_id,
            param1=param1,
            param2=param2,
            dest=dest,
            source=source,
            data=data,
        )
    err_msg = err_info.value.args[0]
    assert (
        err_msg == "A ThorLabs packet can either have parameters or "
        "data, but not both."
    )


@pytest.mark.parametrize("params_or_data", params_or_data)
def test_string(params_or_data):
    """Return a string of the class."""
    message_id = 0x0000
    param1 = params_or_data[0]
    param2 = params_or_data[1]
    dest = 0x50
    source = 0x01
    data = params_or_data[2]
    pkt = _packets.ThorLabsPacket(
        message_id=message_id,
        param1=param1,
        param2=param2,
        dest=dest,
        source=source,
        data=data,
    )
    string_expected = """
ThorLabs APT packet:
    Message ID      {}
    Parameter 1     {}
    Parameter 2     {}
    Destination     {}
    Source          {}
    Data            {}
""".format(
        f"0x{message_id:x}",
        f"0x{param1:x}" if not params_or_data[3] else "None",
        f"0x{param2:x}" if not params_or_data[3] else "None",
        f"0x{dest:x}",
        f"0x{source:x}",
        f"{data}" if params_or_data[3] else "None",
    )
    assert pkt.__str__() == string_expected


def test_message_id():
    """Get / set message ID."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    pkt.message_id = 0x002A
    assert pkt.message_id == 0x002A


def test_parameters():
    """Get / set both parameters."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    pkt.parameters = (0x0D, 0x2A)
    assert pkt.parameters == (0x0D, 0x2A)


def test_destination():
    """Get / set destination."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    pkt.destination = 0x2A
    assert pkt.destination == 0x2A


def test_source():
    """Get / set source."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    pkt.source = 0x2A
    assert pkt.source == 0x2A


def test_data():
    """Get / set data."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=None, param2=None, dest=0x50, source=0x01, data=0x00
    )
    data = struct.pack("<H", 0x2A)
    pkt.data = data
    assert pkt.data == data


@pytest.mark.parametrize("params_or_data", params_or_data)
def test_pack_with_data(params_or_data):
    """Pack a package with data."""
    message_id = 0x0000
    param1 = params_or_data[0]
    param2 = params_or_data[1]
    dest = 0x50
    source = 0x01
    data = params_or_data[2]
    pkt = _packets.ThorLabsPacket(
        message_id=message_id,
        param1=param1,
        param2=param2,
        dest=dest,
        source=source,
        data=data,
    )

    if params_or_data[3]:
        message_header = struct.Struct("<HHBB")
        pkt_expected = (
            message_header.pack(message_id, len(data), 0x80 | dest, source) + data
        )
    else:
        message_header = struct.Struct("<HBBBB")
        pkt_expected = message_header.pack(message_id, param1, param2, dest, source)
    assert pkt.pack() == pkt_expected


@pytest.mark.parametrize("params_or_data", params_or_data)
def test_unpack(params_or_data):
    """Unpack data - the reverse operation of packing it!"""
    message_id = 0x0000
    param1 = params_or_data[0]
    param2 = params_or_data[1]
    dest = 0x50
    source = 0x01
    data = params_or_data[2]
    pkt = _packets.ThorLabsPacket(
        message_id=message_id,
        param1=param1,
        param2=param2,
        dest=dest,
        source=source,
        data=data,
    )
    packed_package = pkt.pack()
    unpacked_package = pkt.unpack(packed_package)
    assert unpacked_package.message_id == message_id
    assert unpacked_package.parameters == (param1, param2)
    assert unpacked_package.data == data
    assert unpacked_package.destination == dest
    assert unpacked_package.source == source


def test_unpack_empty_packet():
    """Raise ValueError if trying to unpack empty string."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    with pytest.raises(ValueError) as err_info:
        pkt.unpack("")
    err_msg = err_info.value.args[0]
    assert err_msg == "Expected a packet, got an empty string instead."


def test_unpack_too_short():
    """Raise ValueError if trying to unpack to short value."""
    pkt = _packets.ThorLabsPacket(
        message_id=0x000, param1=0x01, param2=0x02, dest=0x50, source=0x01, data=None
    )
    too_short_package = struct.pack("<HH", 0x01, 0x02)
    with pytest.raises(ValueError) as err_info:
        pkt.unpack(too_short_package)
    err_msg = err_info.value.args[0]
    assert err_msg == "Packet must be at least 6 bytes long."
