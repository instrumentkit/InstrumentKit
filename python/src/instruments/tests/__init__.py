#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Package for InstrumentKit unit tests.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## IMPORTS ####################################################################

import six
import contextlib
from six.moves import StringIO

from nose.tools import nottest, eq_

## FUNCTIONS ##################################################################

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
    # Normalize assertion and playback strings.
    if isinstance(ins_to_host, list):
        ins_to_host = sep.join(ins_to_host) + (sep if ins_to_host else "")
    if isinstance(host_to_ins, list):
        host_to_ins = sep.join(host_to_ins) + (sep if host_to_ins else "")

    stdin = StringIO(ins_to_host)
    stdout = StringIO()
    
    yield ins_class.open_test(stdin, stdout)
    
    assert stdout.getvalue() == host_to_ins, \
"""Expected:

{}

Got:

{}""".format(repr(host_to_ins), repr(stdout.getvalue()))
    
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
    
