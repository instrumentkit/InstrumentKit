#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Thorlabs util functions
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import instruments as ik

# TESTS ######################################################################


def test_check_cmd():
    assert ik.thorlabs.thorlabs_utils.check_cmd("blo") == 1
    assert ik.thorlabs.thorlabs_utils.check_cmd("CMD_NOT_DEFINED") == 0
    assert ik.thorlabs.thorlabs_utils.check_cmd("CMD_ARG_INVALID") == 0
