#!/usr/bin/python
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
    return 1 if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID" else 0
