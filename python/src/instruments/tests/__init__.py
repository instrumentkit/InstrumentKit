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

import contextlib
import cStringIO as StringIO

from nose.tools import nottest, eq_

## FUNCTIONS ##################################################################

@contextlib.contextmanager
def expected_protocol(ins_class, host_to_ins, ins_to_host):
    """
    Given an instrument class, expected output from the host and expected input
    from the instrument, asserts that the protocol in a context block proceeds
    according to that expectation.
    
    For an example of how to write tests using this context manager, see
    the ``make_name_test`` function below.
    """
    stdin = StringIO.StringIO(ins_to_host)
    stdout = StringIO.StringIO()
    
    yield ins_class.open_test(stdin, stdout)
    
    assert stdout.getvalue() == host_to_ins, \
"""Expected:

{}

Got:

{}""".format(repr(host_to_ins), repr(stdout.getvalue()))
    
@nottest
def unit_eq(a, b, msg=None, thresh=1e-5):
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
            assert ins.name == "NAME"
    return test
    
