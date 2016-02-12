#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Newport ESP 301 axis controller
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import mock
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS #######################################################################


def test_axis_returns_axis_class():
    with expected_protocol(
        ik.newport.NewportESP301,
        [
            "1SN?",
            "TB?"  # error check query
        ],
        [
            "1",
            "0,0,0"
        ],
        sep="\r"
    ) as inst:
        axis = inst.axis[0]
        assert isinstance(axis, ik.newport.NewportESP301Axis) is True
