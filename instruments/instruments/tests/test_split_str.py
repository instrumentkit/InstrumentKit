#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the util_fns.split_unit_str utility function
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

from nose.tools import raises, eq_

from instruments.util_fns import (
    split_unit_str
)

# TEST CASES #################################################################


def test_split_unit_str_magnitude_and_units():
    """
    split_unit_str: Given the input "42 foobars" I expect the output
    to be (42, "foobars").

    This checks that "[val] [units]" works where val is a non-scientific number
    """
    mag, units = split_unit_str("42 foobars")
    eq_(mag, 42)
    eq_(units, "foobars")


def test_split_unit_str_magnitude_and_default_units():
    """
    split_unit_str: Given the input "42" and default_units="foobars"
    I expect output to be (42, "foobars").

    This checks that when given a string without units, the function returns
    default_units as the units.
    """
    mag, units = split_unit_str("42", default_units="foobars")
    eq_(mag, 42)
    eq_(units, "foobars")


def test_split_unit_str_ignore_default_units():
    """
    split_unit_str: Given the input "42 snafus" and default_units="foobars"
    I expect the output to be (42, "snafus").

    This verifies that if the input has units, then any specified default_units
    are ignored.
    """
    mag, units = split_unit_str("42 snafus", default_units="foobars")
    eq_(mag, 42)
    eq_(units, "snafus")


def test_split_unit_str_lookups():
    """
    split_unit_str: Given the input "42 FOO" and a dictionary for our units
    lookup, I expect the output to be (42, "foobars").

    This checks that the unit lookup parameter is correctly called, which can be
    used to map between units as string and their pyquantities equivalent.
    """
    unit_dict = {
        "FOO": "foobars",
        "SNA": "snafus"
    }
    mag, units = split_unit_str("42 FOO", lookup=unit_dict.__getitem__)
    eq_(mag, 42)
    eq_(units, "foobars")


def test_split_unit_str_scientific_notation():
    """
    split_unit_str: Given inputs of scientific notation, I expect the output
    to correctly represent the inputted magnitude.

    This checks that inputs with scientific notation are correctly converted
    to floats.
    """
    # No signs, no units
    mag, units = split_unit_str("123E1")
    eq_(mag, 1230)
    eq_(units, pq.dimensionless)
    # Negative exponential, no units
    mag, units = split_unit_str("123E-1")
    eq_(mag, 12.3)
    eq_(units, pq.dimensionless)
    # Negative magnitude, no units
    mag, units = split_unit_str("-123E1")
    eq_(mag, -1230)
    eq_(units, pq.dimensionless)
    # No signs, with units
    mag, units = split_unit_str("123E1 foobars")
    eq_(mag, 1230)
    eq_(units, "foobars")
    # Signs everywhere, with units
    mag, units = split_unit_str("-123E-1 foobars")
    eq_(mag, -12.3)
    eq_(units, "foobars")
    # Lower case e
    mag, units = split_unit_str("123e1")
    eq_(mag, 1230)
    eq_(units, pq.dimensionless)


@raises(ValueError)
def test_split_unit_str_empty_string():
    """
    split_unit_str: Given an empty string, I expect the function to raise
    a ValueError.
    """
    _ = split_unit_str("")


@raises(ValueError)
def test_split_unit_str_only_exponential():
    """
    split_unit_str: Given a string with only an exponential, I expect the
    function to raise a ValueError.
    """
    _ = split_unit_str("E3")


def test_split_unit_str_magnitude_with_decimal():
    """
    split_unit_str: Given a string with magnitude containing a decimal, I
    expect the function to correctly parse the magnitude.
    """
    # Decimal and units
    mag, units = split_unit_str("123.4 foobars")
    eq_(mag, 123.4)
    eq_(units, "foobars")
    # Decimal, units, and exponential
    mag, units = split_unit_str("123.4E1 foobars")
    eq_(mag, 1234)
    eq_(units, "foobars")


@raises(ValueError)
def test_split_unit_str_only_units():
    """
    split_unit_str: Given a bad string containing only units (ie, no numbers),
    I expect the function to raise a ValueError.
    """
    _ = split_unit_str("foobars")
