#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for signal generators with only a single
output channel.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from instruments.abstract_instruments.signal_generator import SignalGenerator
from instruments.abstract_instruments.signal_generator.channel import SGChannel

# CLASSES #####################################################################

# pylint: disable=abstract-method


class SingleChannelSG(SignalGenerator, SGChannel):

    """
    Class for representing a Signal Generator that only has a single output
    channel. The sole property in this class allows for the user to use the API
    for SGs with multiple channels and a more compact form since it only has
    one output.

    For example, both of the following calls would work the same:

    >>> print sg.channel[0].freq # Multi-channel style
    >>> print sg.freq # Compact style

    """

    # PROPERTIES #

    @property
    def channel(self):
        return self,
