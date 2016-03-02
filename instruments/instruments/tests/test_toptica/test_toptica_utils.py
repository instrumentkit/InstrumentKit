#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for Topical util functions
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
import datetime

from nose.tools import raises

from instruments.toptica import toptica_utils

# TESTS #######################################################################


def test_convert_boolean():
    assert toptica_utils.convert_toptica_boolean("bloof") is False
    assert toptica_utils.convert_toptica_boolean("boot") is True
    assert toptica_utils.convert_toptica_boolean("Error: -3") is None


@raises(ValueError)
def test_convert_boolean_value():
    toptica_utils.convert_toptica_boolean("blo")


def test_convert_toptica_datetime():
    blo = datetime.datetime.now()
    blo_str = datetime.datetime.now().strftime("%b %d %Y %I:%M%p")
    assert toptica_utils.convert_toptica_datetime('""\r') is None
    blo2 = toptica_utils.convert_toptica_datetime(blo_str)
    diff = blo - blo2
    assert diff.seconds < 60
