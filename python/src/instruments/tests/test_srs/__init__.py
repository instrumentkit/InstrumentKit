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

import instruments as ik
import cStringIO as StringIO
import quantities as pq

## SETUP ######################################################################

def test_srsdg645_name():
    with ik.tests.expected_protocol(ik.srs.SRSDG645, "*IDN?\n", "Name") as ddg:
        assert ddg.name == "Name"
    
def test_srsdg645_trigger_source():
    with ik.tests.expected_protocol(ik.srs.SRSDG645, "DLAY?2\nDLAY 3,2,60.0\n", "0,42") as ddg:
        ref, t = ddg.channel['A'].delay
        assert ref == ddg.Channels.T0
        assert abs((t - pq.Quantity(42, 's')).magnitude) < 1e5
        ddg.channel['B'].delay = (ddg.channel['A'], pq.Quantity(1, "minute"))

