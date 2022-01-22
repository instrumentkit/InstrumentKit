#!/usr/bin/env python
"""
Module containing custom units used by various instruments.
"""

# IMPORTS #####################################################################

import pint

# UNITS #######################################################################

ureg = pint.get_application_registry()
ureg.define("percent = []")
ureg.define("centibelmilliwatt = 1e-3 watt; logbase: 10; logfactor: 100 = cBm")
