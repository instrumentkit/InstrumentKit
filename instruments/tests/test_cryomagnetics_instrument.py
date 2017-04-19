# -*- coding: utf-8 -*-
"""
Test the cryomagnetics instrument base class
"""

# IMPORTS #####################################################################
from __future__ import absolute_import

import mock
from nose.tools import eq_, raises

from instruments.abstract_instruments import CryomagneticsInstrument
from instruments.abstract_instruments.comm import LoopbackCommunicator
from instruments.abstract_instruments.comm import CryomagneticsSerialCommunicator

# DEFAULT TESTING VARIABLES ###################################################

default_port = '/dev/ttyUSB0'
default_baud = 19200
default_vid = 1000
default_pid = 1000
default_serial_number = 'a1'
default_timeout = 10
default_write_timeout = 10

# TEST CASES ##################################################################

# pylint: disable=protected-access


def test_init():
    filelike = LoopbackCommunicator()
    instrument = CryomagneticsInstrument(filelike)
    assert isinstance(instrument, CryomagneticsInstrument) is True


@mock.patch('instruments.abstract_instruments.comm.serial_manager'
            '.new_serial_connection', return_value=LoopbackCommunicator())
def test_open_serial_happy_path(mock_new_serial_connection):
    port = default_port
    baud = default_baud
    CryomagneticsInstrument.open_serial(port=port, baud=baud)

    eq_(
        mock.call(
            port, baud=baud, timeout=3, write_timeout=3,
            communicator_type=CryomagneticsSerialCommunicator
        ),
        mock_new_serial_connection.call_args
    )


@raises(ValueError)
def test_open_serial_no_port_no_vid():
    port = None
    vid = None

    CryomagneticsInstrument.open_serial(port=port, vid=vid)


@raises(ValueError)
def test_open_serial_both_port_and_vid():
    port = default_port
    vid = default_vid

    CryomagneticsInstrument.open_serial(port=port, vid=vid)


@raises(ValueError)
def test_open_vid_no_pid():
    vid = default_vid
    pid = None

    CryomagneticsInstrument.open_serial(vid=vid, pid=pid)


@raises(ValueError)
def test_open_pid_no_vid():
    vid = None
    pid = default_pid

    CryomagneticsInstrument.open_serial(vid=vid, pid=pid)
