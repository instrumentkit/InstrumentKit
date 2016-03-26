#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing InstrumentKit unit tests

This file hosts a few utility functions to assist with creating and running
unit tests.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
from io import BytesIO

from builtins import bytes, str

from nose.tools import nottest, eq_

# FUNCTIONS ##################################################################


@contextlib.contextmanager
def expected_protocol(ins_class, host_to_ins, ins_to_host, sep="\n"):
    """
    Given an instrument class, expected output from the host and expected input
    from the instrument, asserts that the protocol in a context block proceeds
    according to that expectation.

    For an example of how to write tests using this context manager, see
    the ``make_name_test`` function below.

    :param type ins_class: Instrument class to use for the protocol assertion.
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
    """
    if isinstance(sep, bytes):
        sep = sep.encode("utf-8")

    # Normalize assertion and playback strings.
    if isinstance(ins_to_host, list):
        ins_to_host = [
            item.encode("utf-8") if isinstance(item, str) else item
            for item in ins_to_host
        ]
        ins_to_host = sep.encode("utf-8").join(ins_to_host) + \
                      (sep.encode("utf-8") if ins_to_host else b"")
    elif isinstance(ins_to_host, str):
        ins_to_host = ins_to_host.encode("utf-8")

    if isinstance(host_to_ins, list):
        host_to_ins = [
            item.encode("utf-8") if isinstance(item, str) else item
            for item in host_to_ins
        ]
        host_to_ins = sep.encode("utf-8").join(host_to_ins) + \
                      (sep.encode("utf-8") if host_to_ins else b"")
    elif isinstance(host_to_ins, str):
        host_to_ins = host_to_ins.encode("utf-8")

    stdin = BytesIO(ins_to_host)
    stdout = BytesIO()

    yield ins_class.open_test(stdin, stdout)

    assert stdout.getvalue() == host_to_ins, \
        """Expected:

{}

Got:

{}""".format(repr(host_to_ins), repr(stdout.getvalue()))

    # current = stdin.tell()
    # stdin.seek(0, 2)
    # end = stdin.tell()
    #
    # assert current == end, \
    #     """Only read {} bytes out of {}""".format(current, end)


@nottest
def unit_eq(a, b, msg=None, thresh=1e-5):
    """
    Asserts that two unitful quantites ``a`` and ``b``
    are equal up to a small numerical threshold.
    """
    assert abs((a - b).magnitude) <= thresh, "{} - {} = {}.{}".format(
        a, b, a - b,
        "\n" + msg if msg is not None else ""
    )
    assert a.units == b.units, "{} and {} have different units".format(a, b)


@nottest
def make_name_test(ins_class, name_cmd="*IDN?"):
    """
    Given an instrument class, produces a test which asserts that the instrument
    correctly reports its name in response to a standard command.
    """
    def test():
        with expected_protocol(ins_class, name_cmd + "\n", "NAME\n") as ins:
            eq_(ins.name, "NAME")
    return test
