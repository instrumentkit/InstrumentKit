#!/usr/bin/env python
"""
Provides an abstract base class for signal generator instruments
"""

# IMPORTS #####################################################################


import abc

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class SignalGenerator(Instrument, metaclass=abc.ABCMeta):

    """
    Python abstract base class for signal generators (eg microwave sources).

    This ABC is not for function generators, which have their own separate ABC.

    .. seealso::
        `~instruments.FunctionGenerator`
    """

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def channel(self):
        """
        Gets a specific channel object for the SignalGenerator.

        :rtype: A class inherited from `~instruments.SGChannel`
        """
        raise NotImplementedError
