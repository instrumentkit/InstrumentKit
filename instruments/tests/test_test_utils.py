"""
Module containing tests for test-related utility functions
"""

from hypothesis import (
    given,
    strategies as st,
)
import pytest

from instruments.optional_dep_finder import numpy
from instruments.tests import iterable_eq
from instruments.units import ureg as u


# TESTS #######################################################################


@given(a=st.lists(st.floats()))
def test_iterable_eq_passes_basic(a):
    """
    Test that two identical lists and tuples always pass
    """
    b = a[:]
    iterable_eq(a, b)
    iterable_eq(tuple(a), tuple(b))


@pytest.mark.parametrize("b", [(0, 1, 2), (0,)])
def test_iterable_eq_fails(b):
    """
    Test failure on equal and mismatched lengths
    """
    a = (1, 2, 3)
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


def test_iterable_eq_fails_type_mismatch():
    """
    Test failure on type mismatch
    """
    a = [1, 2, 3]
    with pytest.raises(AssertionError):
        iterable_eq(a, tuple(a))


def test_iterable_eq_passes_sequence_quantity():
    """
    Test passes on equal sequences with unitful values
    """
    a = (1 * u.V, 2 * u.A)
    iterable_eq(a, a[:])


def test_iterable_eq_fails_sequence_quantity():
    """
    Test failure on unitful sequences with wrong units, and wrong magnitudes
    """
    a = (1 * u.V, 2 * u.A)
    b = (1 * u.A, 2 * u.A)  # Different units
    with pytest.raises(AssertionError):
        iterable_eq(a, b)

    b = (1 * u.V, 3 * u.A)  # Different magnitude
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


def test_iterable_eq_passes_singular_quantity():
    """
    Test passes on singular unitful quantity
    """
    iterable_eq(1 * u.V, 1 * u.V)


def test_iterable_eq_fails_singular_quantity():
    """
    Test failure on singular unitful quantity with wrong units
    """
    a = 1 * u.V
    b = 1 * u.A
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


@pytest.mark.skipif(numpy is None, reason="Only run if numpy installed")
def test_iterable_eq_passes_two_numpy_array():
    """
    Test pases for two identical numpy arrays
    """
    a = numpy.array([1, 2, 3])
    iterable_eq(a, a.copy())


@pytest.mark.skipif(numpy is None, reason="Only run if numpy installed")
def test_iterable_eq_fails_one_numpy_array_equal_values():
    """
    Test failure for one is numpy array, other is not
    """
    a = numpy.array([1, 2, 3])
    b = (1, 2, 3)
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


@pytest.mark.skipif(numpy is None, reason="Only run if numpy installed")
@pytest.mark.parametrize("b", [(1, 6, 3), (1, 2)])
def test_iterable_eq_fails_one_numpy_array(b):
    """
    Test that different value and different length
    comparisons against numpy arrays fail
    """
    a = numpy.array([1, 2, 3])
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


@pytest.mark.skipif(numpy is None, reason="Only run if numpy installed")
@pytest.mark.parametrize("b", [(1, 6, 3), (1, 2)])
def test_iterable_eq_fails_two_numpy_array(b):
    """
    Test that different value and different length
    comparisons against numpy arrays fail
    """
    a = numpy.array([1, 2, 3])
    b = numpy.array(b)
    with pytest.raises(AssertionError):
        iterable_eq(a, b)


@pytest.mark.skipif(numpy is None, reason="Only run if numpy installed")
def test_iterable_eq_passes_two_numpy_array_quantities():
    """
    Test that two unitful quantities with numpy array data
    will equal data will pass
    """
    values = [1, 2, 3]
    a = numpy.array(values) * u.V
    b = numpy.array(a) * u.V
    iterable_eq(a, b)
