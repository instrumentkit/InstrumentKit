#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# cc1.py: Class for the Qubitekk Coincidence Counter instrument
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
# CC1 Class contributed by Catherine Holloway
## IMPORTS #####################################################################
from instruments.abstract_instruments import Instrument
from instruments.generic_scpi.scpi_instrument import SCPIInstrument
from instruments.util_fns import ProxyList,assume_units
import quantities as pq

class _CC1Channel():
    def __init__(self, cc1, idx):
        self._cc1 = cc1
        self._idx = idx + 1
        self._chan = "";
        if(self._idx ==1):
            self._chan = "C1"
        if(self._idx ==2):
            self._chan = "C2"
        if(self._idx ==3):
            self._chan = "CO"
        self._count = 0
        
    ## PROPERTIES ##
    
    @property
    def count(self):
        """
        Gets the counts.
        """
        count = self._cc1.query("COUN:"+self._chan+"?")
        if not count is "Unknown command":
            try:
                count = int(count)
                self.count = count
                return self.count
            except ValueError:
                self.count = self.count
        

class CC1(SCPIInstrument):
    """
    The CC1 is a hand-held coincidence counter.
    It has two setting values, the dwell time and the coincidence window. The coincidence window determines the amount of time (in ns) that the two detections may be from each other and still be considered a coincidence. The dwell time is the amount of time that passes before the counter will send the clear signal.
    More information can be found at :
    http://www.qubitekk.com
    """
    def __init__(self, filelike):
        super(CC1, self).__init__(filelike)
        self.terminator = "\n"
        self.end_terminator = "\n"
        self.channel_count = 3

    ### CC SETTINGS ###

    @property
    def window(self):
        """
        The length of the coincidence window between the two signals
        """
        response = self.query("WIND?")
        if not response is "Unknown command":
            response = response[:-3]
            return float(response)*pq.ns
            
    @window.setter
    def window(self, newval):
        newval_mag = assume_units(newval,pq.ns).rescale(pq.ns).magnitude
        if newval_mag < 0:
            raise ValueError("Window is too small.")
        if newval_mag >7:
            raise ValueError("Window is too big")
        self.sendcmd(":WIND {}".format(newval_mag))
    
    @property
    def dwell_time(self):
        """
        The length of time before a clear signal is sent to the counters
        """
        response = self.query("DWEL?")
        if not response is "Unknown command":
            response = response[:-2]
            return float(response)*pq.s
            

    @dwell_time.setter
    def dwell_time(self, newval):
        newval_mag = assume_units(newval,pq.s).rescale(pq.s).magnitude
        if newval_mag < 0:
            raise ValueError("Dwell time cannot be negative.")
        self.sendcmd(":DWEL {}".format(newval_mag))
            
    @property
    def gate_enable(self):
        """
        The Gate mode of the CC
        enabled means the input signals are anded with the gate signal
        disabled means the input signals are not anded with the gate signal
        """
        response = self.query("GATE?")
        if not response is "Unknown command":
            return response

    @gate_enable.setter
    def gate_enable(self, newval):
        """
        Set the gate either enabled (1) or disabled (0)
        """
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid output mode")
        if newval ==0:
            self.sendcmd(":GATE:OFF")
        if newval ==1:
            self.sendcmd(":GATE:ON")

    @property
    def count_enable(self):
        """
        The count mode of the CC
        enabled means the dwell time passes before the counters are cleared
        disabled means the counters are cleared every 0.1 seconds
        """
        response = self.query("COUN?")
        if not response is "Unknown command":
            return response

    @count_enable.setter
    def count_enable(self, newval):
        """
        Set the count either enabled (1) or disabled (0)
        """
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid output mode")
        if newval ==0:
            self.sendcmd(":COUN:OFF")
        if newval ==1:
            self.sendcmd(":COUN:ON")

    ### return values ###
    
    @property
    def channel(self):
        '''
        Gets a specific channel object. The desired channel is specified like 
        one would access a list.
        
        :rtype: `_CC1Channel`
        
        '''
        return ProxyList(self, _CC1Channel, xrange(self.channel_count))
    
    ### functions ###
    def clear_counts(self):
        """
        Clears the current total counts on the counters
        """
        self.query("CLEA")
