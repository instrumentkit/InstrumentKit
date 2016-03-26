#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing common code for testing the property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from __future__ import unicode_literals

from io import StringIO

# CLASSES ####################################################################

# pylint: disable=missing-docstring


class MockInstrument(object):

    """
    Mock class that admits sendcmd/query but little else such that property
    factories can be tested by deriving from the class.
    """

    def __init__(self, responses=None):
        self._buf = StringIO()
        self._responses = responses if responses is not None else {}

    @property
    def value(self):
        return self._buf.getvalue()

    def sendcmd(self, cmd):
        self._buf.write("{}\n".format(cmd))

    def query(self, cmd):
        self.sendcmd(cmd)
        return self._responses[cmd.strip()]
