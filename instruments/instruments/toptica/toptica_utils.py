#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Contains common utility functions for Toptica-brand instruments
"""

from __future__ import absolute_import
from datetime import datetime


def convert_toptica_boolean(response):
    """
    Converts the toptica boolean expression to a boolean
    :param response: response string
    :type response: str
    :return: the converted boolean
    :rtype: bool
    """
    if response.find('Error: -3') > -1:
        return None
    elif response.find('f') > -1:
        return False
    elif response.find('t') > -1:
        return True
    else:
        raise ValueError("cannot convert: " + str(response) + " to boolean")


def convert_toptica_datetime(response):
    """
    Converts the toptical date format to a python time date
    :param response: the string from the topmode
    :type response: str
    :return: the converted date
    :rtype: 'datetime.datetime'
    """
    if response.find('""') >= 0:
        return None
    else:
        return datetime.strptime(response, '%b %d %Y %I:%M%p')
