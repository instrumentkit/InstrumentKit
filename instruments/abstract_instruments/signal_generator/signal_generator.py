#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for signal generator instruments
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc

from future.utils import with_metaclass

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class SignalGenerator(with_metaclass(abc.ABCMeta, Instrument)):

    """
    Python abstract base class for signal generators (eg microwave sources).

    This ABC is not for function generators, which have their own separate ABC.

    .. seealso::
        `~instruments.FunctionGenerator`
    """

    # PROPERTIES #

    @abc.abstractproperty
    def channel(self):
        """
        Gets a specific channel object for the SignalGenerator.

        :rtype: A class inherited from `~instruments.SGChannel`
        """
        raise NotImplementedError
