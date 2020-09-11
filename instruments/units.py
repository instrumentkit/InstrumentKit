#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing custom units used by various instruments.
"""

# IMPORTS #####################################################################

# pylint: disable=unused-wildcard-import, wildcard-import


from pint import _DEFAULT_REGISTRY as ureg

# UNITS #######################################################################

ureg.define("percent = []")
ureg.define("centibelmilliwatt = 1e-3 watt; logbase: 10; logfactor: 100 = cBm")
