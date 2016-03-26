#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing Tektronix instruments
"""

from __future__ import absolute_import

from .tekdpo4104 import (
    TekDPO4104,
    _TekDPO4104Channel,
    _TekDPO4104DataSource,
)
from .tekdpo70000 import TekDPO70000
from .tekawg2000 import TekAWG2000
from .tektds224 import TekTDS224
from .tektds5xx import TekTDS5xx
