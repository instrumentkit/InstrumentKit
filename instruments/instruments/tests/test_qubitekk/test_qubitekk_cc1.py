#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Qubitekk CC1
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol, make_name_test

# TESTS ######################################################################

test_cc1_name = make_name_test(ik.qubitekk.CC1)


@raises(IOError)
def test_cc1_unknown_command():
    """
    CC1: Checks that invalid commands are properly turned into exceptions.
    """
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "FTN"
        ],
        [
            "Unknown command"
        ]
    ) as cc1:
        cc1.sendcmd("FTN")
