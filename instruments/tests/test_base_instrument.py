#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the base Instrument class
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from builtins import bytes

# pylint: disable=unused-import
from nose.tools import raises
import quantities as pq

import numpy as np

import instruments as ik
from instruments.tests import expected_protocol

# TESTS ######################################################################


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
