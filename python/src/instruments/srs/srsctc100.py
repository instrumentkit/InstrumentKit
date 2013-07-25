#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srsctc100.py: Class for communicating with the SRS CTC-100.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from flufl.enum import IntEnum

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList

## ENUMS #######################################################################



## CLASSES #####################################################################

class SRSCTC100(SCPIInstrument):
    """
    Communicates with a Stanford Research Systems CTC-100 cryogenic temperature
    controller.
    """
                 
    def __init__(self, filelike):
        super(SRSCTC100, self).__init__(filelike)
    
    
    ## INNER CLASSES ##
    
    class Channel(object):
        """
        Represents an input or output channel on an SRS CTC-100 cryogenic
        temperature controller.
        """
        
        def __init__(self, ctc, chan_name):
            self._ctc = ctc
            
            # Save the pretty name that we are given.
            self._chan_name = chan_name
            
            # Strip spaces from the name used in remote programming, as
            # specified on page 14 of the manual.
            self._rem_name = chan_name.replace(" ", "")
            
        @property
        def name(self):
            return self._chan_name
        @name.setter
        def name(self, newval):
            self._ctc.sendcmd('{}.Name = "{}"'.format(self._rem_name, newval))
            # TODO: check for errors!
            self._chan_name = newval
            self._rem_name = newval.replace(" ", "")
            
        @property
        def value(self):
            # TODO: Add units to this property. What are the units, anyway?
            # TODO: Make an OutputChannel that subclasses this class,
            #       and add a setter for value.
            return float(self._ctc.query("{}.value?".format(self._chan_name)))
   
   
    ## PRIVATE METHODS ##
    
    def _channel_names(self):
        """
        Returns the names of valid channels, using the ``getOutputNames``
        and ``getInputNames`` commands, as documented in the example on page
        14 of the `CTC-100 manual`_.
        
        .. _CTC-100 manual: http://www.thinksrs.com/downloads/PDFs/Manuals/CTC100m.pdf
        """
        names = []
        for kind in ['getOutputNames?', 'getInputNames?']:
            # We need to split apart the comma-separated list and make sure that
            # no newlines or other whitespace gets carried along for the ride.
            # Note that we do NOT strip spaces here, as this is done inside
            # the Channel object. Doing things that way allows us to present
            # the actual pretty name to users, but to use the remote-programming
            # name in commands.
            # As a consequence, users of this instrument MUST use spaces
            # matching the pretty name and not the remote-programming name.
            # CG could not think of a good way around this.
            names += [
                name.strip()
                for name in self.query(kind).split(',')
            ]
        
        # Get unique names only, since some channels can be both input and
        # output. Since sets don't support multiple inclusion, making a set from
        # the names then going back to a list removes duplicates. That leaves
        # the list in hash-ordering, though, so we should really sort it.
        return sorted(list(set(names)))
   
    ## PROPERTIES ##
    @property
    def channel(self):
        # Note that since the names can change, we need to query channel names
        # each time. This is inefficient, but alas.
        return ProxyList(self, self.Channel, self._channel_names())  
    
