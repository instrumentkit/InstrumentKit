#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the MingHe low-cost function generator.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import range, map
from enum import IntEnum, Enum

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import convert_temperature
from instruments.util_fns import enum_property, unitful_property, int_property

# CLASSES #####################################################################


class MHS5200(Instrument):
    """
    The MHS5200 is a low-cost, 2 channel function generator.

    There is no user manual, but Al Williams has reverse-engineered the
    communications protocol:
    https://github.com/wd5gnr/mhs5200a/blob/master/MHS5200AProtocol.pdf
    """
    def __init__(self, filelike):
        super(MHS5200, self).__init__(filelike)

    

