#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for Tektronix-brand instruments.
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

import cStringIO as StringIO
import quantities as pq
import numpy as np

## TESTS ######################################################################

test_tektds224_name = make_name_test(ik.tektronix.TekTDS224)
    
def test_tektds224_data_width():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        "DATA:WIDTH?\nDATA:WIDTH 1\n",
        "2\n"
    ) as tek:
        assert tek.data_width == 2
        tek.data_width = 1
        
def test_tektds224_data_source():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        "DAT:SOU?\nDAT:SOU MATH\n",
        "CH1\n"
    ) as tek:
        assert tek.data_source == ik.tektronix.tektds224._TekTDS224Channel(tek,
                                                                           0
                                                                           )
        tek.data_source = tek.math
    
def test_tektds224_channel():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        "",
        ""
    ) as tek:
        assert tek.channel[0] == ik.tektronix.tektds224._TekTDS224Channel(tek,0)
        
def test_tektds224_channel_coupling():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        "CH1:COUPL?\nCH2:COUPL AC\n",
        "DC\n"
    ) as tek:
        assert tek.channel[0].coupling == tek.Coupling.dc
        tek.channel[1].coupling = tek.Coupling.ac
        
def test_tektds224_data_source_read_waveform():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        ("DAT:SOU?\nDAT:SOU CH1\nDAT:ENC RIB\nDATA:WIDTH?\nCURVE?\n"
        "WFMP:CH1:YOF?\nWFMP:CH1:YMU?\nWFMP:CH1:YZE?\nWFMP:XZE?\nWFMP:XIN?\n"
        "WFMP:CH1:NR_P?\nDAT:SOU CH1\n"),
        "CH1\n2\n#210"+"00000001000200030004".decode("hex")+"0\n1\n0\n0\n1\n5\n"
    ) as tek:
        data = np.array([0,1,2,3,4])
        (x,y) = tek.channel[0].read_waveform()
        assert (x == data).all()
        assert (y == data).all()

