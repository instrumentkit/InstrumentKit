#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for SRS-brand instruments.
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
from instruments.tests import expected_protocol, make_name_test, unit_eq

from six.moves import StringIO
import quantities as pq

## TESTS ######################################################################

test_srsdg645_name = make_name_test(ik.srs.SRSDG645)
    
def test_srsdg645_output_level():
    """
    SRSDG645: Checks getting/setting unitful ouput level.
    """
    with expected_protocol(ik.srs.SRSDG645,
            [
                "LAMP? 1",
                "LAMP 1,4.0",
            ], [
                "3.2"
            ]
    ) as ddg:
        unit_eq(ddg.output['AB'].level_amplitude, pq.Quantity(3.2, "V"))
        ddg.output['AB'].level_amplitude = 4.0
        
def test_srsdg645_output_polarity():
    """
    SRSDG645: Checks getting/setting 
    """
    with expected_protocol(
        ik.srs.SRSDG645,
        "LPOL? 1\nLPOL 2,0\n",
        "1\n"
    ) as ddg:
        assert ddg.output['AB'].polarity == ddg.LevelPolarity.positive
        ddg.output['CD'].polarity = ddg.LevelPolarity.negative
    
    
def test_srsdg645_trigger_source():
    with expected_protocol(ik.srs.SRSDG645, "DLAY?2\nDLAY 3,2,60.0\n", "0,42\n") as ddg:
        ref, t = ddg.channel['A'].delay
        assert ref == ddg.Channels.T0
        assert abs((t - pq.Quantity(42, 's')).magnitude) < 1e5
        ddg.channel['B'].delay = (ddg.channel['A'], pq.Quantity(1, "minute"))

