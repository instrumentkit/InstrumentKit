#!/usr/bin/env python
"""
Module containing InstrumentKit unit tests

This file hosts a few utility functions to assist with creating and running
unit tests.
"""

# IMPORTS ####################################################################


import contextlib
from io import BytesIO
from unittest import mock

import pytest

from instruments.optional_dep_finder import numpy
from instruments.units import ureg as u

# FUNCTIONS ##################################################################


@contextlib.contextmanager
def expected_protocol(ins_class, host_to_ins, ins_to_host, sep="\n", repeat=1):
    """
    Given an instrument class, expected output from the host and expected input
    from the instrument, asserts that the protocol in a context block proceeds
    according to that expectation.

    For an example of how to write tests using this context manager, see
    the ``make_name_test`` function below.

    :param ins_class: Instrument class to use for the protocol assertion.
    :type ins_class: `~instruments.Instrument`
    :param host_to_ins: Data to be sent by the host to the instrument;
        this is checked against the actual data sent by the instrument class
        during the execution of this context manager.
    :type host_to_ins: ``str`` or ``list``; if ``list``, each line is
        concatenated with the separator given by ``sep``.
    :param ins_to_host: Data to be sent by the instrument; this is played
        back during the execution of this context manager, and should
        be used to assert correct behaviour within the context.
    :type ins_to_host: ``str`` or ``list``; if ``list``, each line is
        concatenated with the separator given by ``sep``.
    :param str sep: Character to be inserted after each string in both
        host_to_ins and ins_to_host parameters. This is typically the
        termination character you would like to have inserted.
    :param int repeat: The number of times the host_to_ins and
        ins_to_host data sets should be duplicated. Typically the default
        value of 1 is sufficient, but increasing this is useful when
        testing multiple calls in the same test that should have the same
        command transactions.
    """
    if isinstance(sep, bytes):
        sep = sep.decode("utf-8")

    # Normalize assertion and playback strings.
    if isinstance(ins_to_host, list):
        ins_to_host = [
            item.encode("utf-8") if isinstance(item, str) else item
            for item in ins_to_host
        ]
        ins_to_host = sep.encode("utf-8").join(ins_to_host) + (
            sep.encode("utf-8") if ins_to_host else b""
        )
    elif isinstance(ins_to_host, str):
        ins_to_host = ins_to_host.encode("utf-8")
    ins_to_host *= repeat

    if isinstance(host_to_ins, list):
        host_to_ins = [
            item.encode("utf-8") if isinstance(item, str) else item
            for item in host_to_ins
        ]
        host_to_ins = sep.encode("utf-8").join(host_to_ins) + (
            sep.encode("utf-8") if host_to_ins else b""
        )
    elif isinstance(host_to_ins, str):
        host_to_ins = host_to_ins.encode("utf-8")
    host_to_ins *= repeat

    stdin = BytesIO(ins_to_host)
    stdout = BytesIO()

    yield ins_class.open_test(stdin, stdout)

    assert (
        stdout.getvalue() == host_to_ins
    ), """Expected:

{}

Got:

{}""".format(
        repr(host_to_ins), repr(stdout.getvalue())
    )

    # current = stdin.tell()
    # stdin.seek(0, 2)
    # end = stdin.tell()
    #
    # assert current == end, \
    #     """Only read {} bytes out of {}""".format(current, end)


def unit_eq(a, b):
    """
    Asserts that two unitful quantites ``a`` and ``b``
    are equal up to a small numerical threshold.
    """
    assert a.magnitude == pytest.approx(b.magnitude)
    assert a.units == b.units, f"{a} and {b} have different units"


def make_name_test(ins_class, name_cmd="*IDN?"):
    """
    Given an instrument class, produces a test which asserts that the instrument
    correctly reports its name in response to a standard command.
    """

    def test():
        with expected_protocol(ins_class, name_cmd + "\n", "NAME\n") as ins:
            assert ins.name == "NAME"

    return test


def iterable_eq(a, b):
    """
    Asserts that the contents of two iterables are the same.
    """
    if numpy and (isinstance(a, numpy.ndarray) or isinstance(b, numpy.ndarray)):
        # pylint: disable=unidiomatic-typecheck
        assert type(a) == type(
            b
        ), f"Expected two numpy arrays, got {type(a)}, {type(b)}"
        assert len(a) == len(
            b
        ), f"Length of iterables is not the same, got {len(a)} and {len(b)}"
        assert (a == b).all()
    elif isinstance(a, u.Quantity) and isinstance(b, u.Quantity):
        unit_eq(a, b)
    else:
        assert a == b
