from __future__ import absolute_import

from io import BytesIO

from enum import Enum
from nose.tools import raises, eq_
import mock
import quantities as pq

from instruments.util_fns import (
    rproperty, bool_property, enum_property, int_property, string_property,
    unitful_property, unitless_property, bounded_unitful_property
)

class MockInstrument(object):

    """
    Mock class that admits sendcmd/query but little else such that property
    factories can be tested by deriving from the class.
    """

    def __init__(self, responses=None):
        self._buf = BytesIO()
        self._responses = responses if responses is not None else {}

    @property
    def value(self):
        return self._buf.getvalue()

    def sendcmd(self, cmd):
        self._buf.write("{}\n".format(cmd))

    def query(self, cmd):
        self.sendcmd(cmd)
        return self._responses[cmd.strip()]