#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the base Instrument class
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from builtins import bytes

from nose.tools import raises
import mock

import numpy as np

import instruments as ik
from instruments.tests import expected_protocol

# TESTS ######################################################################

# pylint: disable=no-member,protected-access


def test_instrument_binblockread():
    with expected_protocol(
        ik.Instrument,
        [],
        [
            b"#210" + bytes.fromhex("00000001000200030004") + b"0",
        ],
        sep="\n"
    ) as inst:
        np.testing.assert_array_equal(inst.binblockread(2), [0, 1, 2, 3, 4])


def test_instrument_binblockread_two_reads():
    inst = ik.Instrument.open_test()
    data = bytes.fromhex("00000001000200030004")
    inst._file.read_raw = mock.MagicMock(
        side_effect=[b"#", b"2", b"10", data[:6], data[6:]]
    )

    np.testing.assert_array_equal(inst.binblockread(2), [0, 1, 2, 3, 4])

    calls_expected = [1, 1, 2, 10, 4]
    calls_actual = [call[0][0] for call in inst._file.read_raw.call_args_list]
    np.testing.assert_array_equal(calls_expected, calls_actual)


@raises(IOError)
def test_instrument_binblockread_too_many_reads():
    inst = ik.Instrument.open_test()
    data = bytes.fromhex("00000001000200030004")
    inst._file.read_raw = mock.MagicMock(
        side_effect=[b"#", b"2", b"10", data[:6], b"", b"", b""]
    )

    _ = inst.binblockread(2)


@raises(IOError)
def test_instrument_binblockread_bad_block_start():
    inst = ik.Instrument.open_test()
    inst._file.read_raw = mock.MagicMock(return_value=b"@")

    _ = inst.binblockread(2)
