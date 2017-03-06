# -*- coding: utf-8 -*-
"""
Contains unit tests for `instruments.cryomagnetics.cryomagnetics_4g`
"""
# IMPORTS #####################################################################

import quantities as pq

from instruments.cryomagnetics import Cryomagnetics4G
from instruments.tests import expected_protocol

# TEST CASES ##################################################################


def test_units():
    with expected_protocol(
        Cryomagnetics4G,
        [
            "UNITS?",
        ],
        [
            "A"
        ]
    ) as inst:
        assert inst.unit == inst.UNITS["A"]


def test_unit_setter():
    with expected_protocol(
        Cryomagnetics4G,
        [
            "UNITS A",
            "UNITS?"
        ],
        [
            "",
            "A"
        ]
    ) as inst:
        inst.unit = "A"
        assert inst.unit == inst.UNITS["A"]


def test_current():
    with expected_protocol(
        Cryomagnetics4G,
        [
            "UNITS A",
            "IOUT?"
        ],
        [
            "",
            "10.0A"
        ]
    ) as inst:
        assert inst.current == 10.0 * pq.A
