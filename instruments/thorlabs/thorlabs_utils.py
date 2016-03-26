#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# thorlabs_utils.py: Utility functions for Thorlabs-brand instruments.
#
# © 2016 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#
"""
Contains common utility functions for Thorlabs-brand instruments
"""


def check_cmd(response):
    """
    Checks the for the two common Thorlabs error messages; CMD_NOT_DEFINED and
    CMD_ARG_INVALID

    :param response: the response from the device
    :return: 1 if not found, 0 otherwise
    :rtype: int
    """
    if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID":
        return 1
    else:
        return 0
