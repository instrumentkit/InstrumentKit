#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# sc10.py: Class for the thorlabs sc10 Shutter Controller
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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
# SC10 Class contributed by Catherine Holloway
#
## IMPORTS #####################################################################

import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class SC10(Instrument):
    """
    The SC10 is a shutter controller, to be used with the Thorlabs SH05 and SH1.
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/8600/SC10-Manual.pdf
    """
    def __init__(self, filelike):
        super(SC10, self).__init__(filelike)
        self.terminator = '\r'
        self.end_terminator = '>'
        
    ## ENUMS ##
    
    class Mode(IntEnum):
        manual = 1
        auto = 2
        single = 3
        repeat = 4
        external = 5
        
    ## PROPERTIES ##

    @property
    def name(self):
        """
        Gets the name and version number of the device.
        """
        response = self.check_command("id?")
        if response is "CMD_NOT_DEFINED":
            self.name()          
        else:
            return response

    @property
    def enable(self):
        """
        Gets/sets the shutter enable status, 0 for disabled, 1 if enabled
        
        :type: `int`
        """
        response = self.check_command("ens?")
        if not response is "CMD_NOT_DEFINED":
            return response
    @enable.setter
    def enable(self, newval):
        if newval == 0 or newval ==1:
            self.sendcmd("ens={}".format(newval))
            self.read()
        else:
            raise ValueError("Invalid value for enable, must be 0 or 1")        

    @property
    def repeat(self):
        """
        Gets/sets the repeat count for repeat mode. Valid range is [1,99]
        inclusive.
        
        :type: `int`
        """
        response = self.check_command("rep?")
        if not response is "CMD_NOT_DEFINED":
            return response
    @repeat.setter
    def repeat(self, newval):
        if newval >0 or newval <100:
            self.sendcmd("rep={}".format(newval))
            self.read()
        else:
            raise ValueError("Invalid value for repeat count, must be "
                             "between 1 and 99")        

    @property
    def mode(self):
        """
        Gets/sets the output mode of the SC10.

        :type: `SC10.Mode`
        """
        response = self.check_command("mode?")
        if not response is "CMD_NOT_DEFINED":
            return SC10.Mode[int(response)]
    @mode.setter
    def mode(self, newval):
        if (newval.enum is not SC10.Mode):
            raise TypeError("Mode setting must be a `SC10.Mode` value, "
                "got {} instead.".format(type(newval)))
        
        self.sendcmd("mode={}".format(newval.value))
        self.read()        
    
    @property
    def trigger(self):
        """
        Gets/sets the trigger source.
        
        0 for internal trigger, 1 for external trigger
        
        :type: `int`
        """
        response = self.check_command("trig?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @trigger.setter
    def trigger(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for trigger mode")
        self.sendcmd("trig={}".format(newval))
        self.read()
    
    @property
    def out_trigger(self):
        """
        Gets/sets the out trigger source.
        
        0 trigger out follows shutter output, 1 trigger out follows 
        controller output
        
        :type: `int`
        """
        response = self.check_command("xto?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @out_trigger.setter
    def out_trigger(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for output trigger mode")
        self.sendcmd("xto={}".format(newval))
        self.read()

    ###I'm not sure how to handle checking for the number of digits yet.
    @property
    def open_time(self):
        """
        Gets/sets the amount of time that the shutter is open, in ms
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units milliseconds.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("open?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @open_time.setter
    def open_time(self, newval):
        newval = int(assume_units(newval, pq.ms).rescale(pq.ms).magnitude)
        if newval < 0:
            raise ValueError("Shutter open time cannot be negative")
        if newval >999999:
            raise ValueError("Shutter open duration is too long")
        self.sendcmd("open={}".format(newval))
        self.read()
    
    @property
    def shut_time(self):
        """
        Gets/sets the amount of time that the shutter is closed, in ms
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units milliseconds.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("shut?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @shut_time.setter
    def shut_time(self, newval):
        newval = int(assume_units(newval, pq.ms).rescale(pq.ms).magnitude)
        if newval < 0:
            raise ValueError("Time cannot be negative")
        if newval >999999:
            raise ValueError("Duration is too long")
        self.sendcmd("shut={}".format(newval))
        self.read()
    
    @property
    def baud_rate(self):
        """
        Gets/sets the instrument baud rate.
        
        Valid baud rates are 9600 and 115200.
        
        :type: `int`
        """
        response = self.check_command("baud?")
        if not response is "CMD_NOT_DEFINED":
            return 115200 if response else 9600 
    @baud_rate.setter
    def baud_rate(self, newval):
        if newval != 9600 and newval !=115200:
            raise ValueError("Invalid baud rate mode")
        else:
            self.sendcmd("baud={}".format(0 if newval == 9600 else 1))
            self.read()
    
    @property
    def closed(self):
        """
        Gets the shutter closed status.
        
        `True` represents the shutter is closed, and `False` for the shutter is
        open.
        
        :rtype: `bool`
        """
        response = self.check_command("closed?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) is 1 else False
    
    @property
    def interlock(self):
        """
        Gets the interlock tripped status.
        
        Returns `True` if the interlock is tripped, and `False` otherwise.
        
        :rtype: `bool`
        """
        response = self.check_command("interlock?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) is 1 else False

    ## Methods ##
    
    def check_command(self,command):
        """
        Checks for the \"Command error CMD_NOT_DEFINED\" error, which can sometimes occur if there were
        incorrect terminators on the previous command. If the command is successful, it returns the value,
        if not, it returns CMD_NOT_DEFINED
        check_command will also clear out the query string
        """
        response = self.query(command)
        #This device will echo the commands sent, so another line must be read to catch the response.
        response = self.read()
        cmd_find = response.find("CMD_NOT_DEFINED")
        if cmd_find ==-1:
            error_find = response.find("CMD_ARG_INVALID")
            if error_find ==-1:
                output_str = response.replace(command,"")
                output_str = output_str.replace(self.terminator,"")
                output_str = output_str.replace(self.end_terminator,"")
            else:
                output_str = "CMD_ARG_INVALID"
        else:
            output_str = "CMD_NOT_DEFINED"
        return output_str
        
    def default(self):
        """
        Restores instrument to factory settings.
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("default")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save(self):
        """
        Stores the parameters in static memory
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("savp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save_mode(self):
        """
        Stores output trigger mode and baud rate settings in memory.
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def restore(self):
        """
        Loads the settings from memory.
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("resp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0
