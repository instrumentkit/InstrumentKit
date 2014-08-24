#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for Qubitekk-brand instruments.
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

from cStringIO import StringIO
import quantities as pq

from nose.tools import raises

## TESTS ######################################################################

test_cc1_name = make_name_test(ik.qubitekk.CC1)
    
@raises(IOError)
def test_cc1_unknown_command():
    """
    CC1: Checks that invalid commands are properly turned into exceptions.
    """
    with expected_protocol(ik.qubitekk.CC1,
            [
                "FTN"
            ], [
                "Unknown command"
            ]
    ) as cc1:
        cc1.sendcmd("FTN")

        
