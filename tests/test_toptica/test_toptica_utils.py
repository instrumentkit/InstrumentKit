#!/usr/bin/env python
"""
Module containing tests for Topical util functions
"""

# IMPORTS #####################################################################

import datetime

import pytest

from instruments.toptica import toptica_utils

# TESTS #######################################################################


def test_convert_boolean():
    assert toptica_utils.convert_toptica_boolean("bloof") is False
    assert toptica_utils.convert_toptica_boolean("boot") is True
    assert toptica_utils.convert_toptica_boolean("Error: -3") is None


def test_convert_boolean_value():
    with pytest.raises(ValueError):
        toptica_utils.convert_toptica_boolean("blo")


def test_convert_toptica_datetime():
    blo = datetime.datetime.now()
    blo_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    assert toptica_utils.convert_toptica_datetime('""\r') is None
    blo2 = toptica_utils.convert_toptica_datetime(blo_str)
    diff = blo - blo2
    assert diff.seconds < 60
