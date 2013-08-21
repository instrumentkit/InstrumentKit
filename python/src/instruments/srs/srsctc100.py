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

from flufl.enum import Enum

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList
import sys
## ENUMS #######################################################################



## CLASSES #####################################################################

class SRSCTC100(SCPIInstrument):
    """
    Communicates with a Stanford Research Systems CTC-100 cryogenic temperature
    controller.
    """
                 
    def __init__(self, filelike):
        super(SRSCTC100, self).__init__(filelike)
        self._do_errcheck = True
    
    
    ## DICTIONARIES ##
    _BOOL_NAMES = {
        'On': True,
        'Off': False
    }
    
    # Note that the SRS CTC-100 uses '\xb0' to represent '°'.
    _UNIT_NAMES = {
        '\xb0C': pq.celsius,
        'W':     pq.watt,
        'V':     pq.volt,
        '\xea':  pq.ohm,
        '':      pq.dimensionless
    }
    
    
    ## INNER CLASSES ##
    
    class SensorType(Enum):
        rtd = 'RTD'
        thermistor = 'Thermistor'
        diode = 'Diode'
        rox = 'ROX'
    
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
        
        ## PRIVATE METHODS ##
        def _get(self, prop_name):
            return self._ctc.query("{}.{}?".format(
                self._rem_name,
                prop_name
            )).strip()
            
        def _set(self, prop_name, newval):
            self._ctc.sendcmd('{}.{} = "{}"'.format(self._rem_name, prop_name, newval))
        
        ## DISPLAY AND PROGRAMMING ##
        # These properties control how the channel is identified in scripts
        # and on the front-panel display.
            
        @property
        def name(self):
            return self._chan_name
        @name.setter
        def name(self, newval):
            self._set('name', newval)
            # TODO: check for errors!
            self._chan_name = newval
            self._rem_name = newval.replace(" ", "")
            
        ## BASICS ##
            
        @property
        def value(self):
            # WARNING: Queries all units all the time.
            # TODO: Make an OutputChannel that subclasses this class,
            #       and add a setter for value.
            return pq.Quantity(
                float(self._get('value')),
                self.units
            )
            
        @property
        def units(self):
            # FIXME: does not respect "chan.d/dt" property.
            return self._ctc._channel_units()[self._chan_name]
            # FIXME: the following line doesn't do what I'd expect, and so it's
            #        commented out.
            # return self._ctc._UNIT_NAMES[self._ctc.query('{}.units?'.format(self._rem_name)).strip()]
            
        @property
        def sensor_type(self):
            return self._ctc.SensorType(self._get('sensor'))
            
        ## STATS ##
        # The following properties control and query the statistics of the
        # channel.
   
        @property
        def stats_enabled(self):
            return self._ctc._BOOL_NAMES[self._get('stats')]
        @stats_enabled.setter
        def stats_enabled(self, newval):
            # FIXME: replace with inverse dict.
            self._set('stats', 'On' if newval else 'Off')
            
        @property
        def stats_points(self):
            return int(self._get('points'))
        @stats_points.setter
        def stats_points(self, newval):
            self._set('points', int(newval))
            
        @property
        def average(self):
            return pq.Quantity(
                float(self._get('average')),
                self.units
            )
            
        @property
        def std_dev(self):
            return pq.Quantity(
                float(self._get('SD')),
                self.units
            )
   
    ## PRIVATE METHODS ##
        
    def _channel_names(self):
        """
        Returns the names of valid channels, using the ``getOutput.names``
        command, as documented in the example on page 14 of the
        `CTC-100 manual`_.
        
        Note that ``getOutput`` also lists input channels, confusingly enough.
        
        .. _CTC-100 manual: http://www.thinksrs.com/downloads/PDFs/Manuals/CTC100m.pdf
        """
        # We need to split apart the comma-separated list and make sure that
        # no newlines or other whitespace gets carried along for the ride.
        # Note that we do NOT strip spaces here, as this is done inside
        # the Channel object. Doing things that way allows us to present
        # the actual pretty name to users, but to use the remote-programming
        # name in commands.
        # As a consequence, users of this instrument MUST use spaces
        # matching the pretty name and not the remote-programming name.
        # CG could not think of a good way around this.
        names = [
            name.strip()
            for name in self.query('getOutput.names?').split(',')
        ]
        return names
    
    def _channel_units(self):
        """
        Returns a dictionary from channel names to channel units, using the
        ``getOutput.units`` command. Unknown units and dimensionless quantities
        are presented the same way by the instrument, and so both are reported
        using `pq.dimensionless`.
        """
        unit_strings = [
            unit_str.strip()
            for unit_str in self.query('getOutput.units?').split(',')
        ]
        return {
            chan_name: self._UNIT_NAMES[unit_str]
            for chan_name, unit_str in zip(self._channel_names(), unit_strings)
        }
        
    def _errcheck(self):
        errs = super(SRSCTC100, self).query('geterror?').strip()
        err_code, err_descript = errs.split(',')
        err_code = int(err_code)
        if err_code == 0:
            return
        else:
            raise IOError(err_descript.strip())
   
    ## PROPERTIES ##
    @property
    def channel(self):
        # Note that since the names can change, we need to query channel names
        # each time. This is inefficient, but alas.
        return ProxyList(self, self.Channel, self._channel_names())
        
    ## OVERRIDEN METHODS ##
    
    # We override sendcmd() and query() to do error checking after each command.
    def sendcmd(self, cmd):
        super(SRSCTC100, self).sendcmd(cmd)
        if self._do_errcheck:
            self._errcheck()
        
    def query(self, cmd):
        resp = super(SRSCTC100, self).query(cmd)
        if self._do_errcheck:
            self._errcheck()
        return resp
    
