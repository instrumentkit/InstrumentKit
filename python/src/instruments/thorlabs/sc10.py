#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# file_communicator.py: Treats a file on the filesystem as a communicator
#     (aka wrapper).
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
# SC10 Class contributed by Catherine Holloway
## IMPORTS #####################################################################
from instruments.abstract_instruments import Instrument
import quantities as pq
from flufl.enum import IntEnum

class SC10mode(IntEnum):
    manual = 1
    auto = 2
    single = 3
    repeat = 4
    external = 5

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

    @property
    def identity(self):
        """
        gets the name and version number of the device
        """
        response = self.check_command("id?")
        if response is "CMD_NOT_DEFINED":
            self.identity()          
        else:
            return response

    ### LCC SETTINGS ###

    @property
    def enable(self):
        """
        The shutter enable status, 0 for disabled, 1 if enabled
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
        The repeat count for repeat mode. 
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
            raise ValueError("Invalid value for repeat count, must be between 1 and 99")        

    @property
    def mode(self):
        """
        The output mode of the SC10
        mode 1 Manual Mode
        mode 2 Auto Mode
        mode 3 Single Mode
        mode 4 Repeat Mode
        mode 5 External Gate Mode
        """
        response = self.check_command("mode?")
        if not response is "CMD_NOT_DEFINED":
            _mode = int(response)
            return (response)
    @mode.setter
    def mode(self, newval):
        if newval >0  and newval < 6:
            self.sendcmd("mode={}".format(newval))
            self.read()
        else:
            raise ValueError("Not a valid operation mode")
    
    @property
    def trigger(self):
        """
        0 for internal trigger, 1 for external trigger
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
        0 trigger out follows shutter output, 1 trigger out follows controller output
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
        The amount of time that the shutter is open, in ms
        """
        response = self.check_command("open?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @open_time.setter
    def open_time(self, newval):
        if newval < 0:
            raise ValueError("Time cannot be negative")
        if newval >999999:
            raise ValueError("Duration is too long")
        self.sendcmd("open={}".format(newval))
        self.read()
    @property
    def shut_time(self):
        """
        The amount of time that the shutter is closed, in ms
        """
        response = self.check_command("shut?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @shut_time.setter
    def shut_time(self, newval):
        if newval < 0:
            raise ValueError("Time cannot be negative")
        if newval >999999:
            raise ValueError("Duration is too long")
        self.sendcmd("shut={}".format(newval))
        self.read()
    @property
    def baud_rate(self):
        """
        Gets the baud rate: 0 for 9600, 1 for 115200
        """
        response = self.check_command("baud?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @baud_rate.setter
    def baud_rate(self, newval):
        if newval != 0 and newval !=1:
            raise ValueError("invalid baud rate mode")
        else:
            self.sendcmd("baud={}".format(newval))
            self.read()   
    @property
    def closed(self):
        """
        1 if the shutter is closed, 0 if the shutter is open
        """
        response = self.check_command("closed?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @property
    def interlock(self):
        """
        1 if the interlock is tripped, 0 otherwise
        """
        response = self.check_command("interlock?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)

    ### SC10 Methods ###
    def default(self):
        """
        restores factory settings
        returns 1 if successful
        """
        response = self.check_command("default")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save(self):
        """
        stores the parameters in static memory
        returns 1 if successful
        """
        response = self.check_command("savp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save_mode(self):
        """
        stores output trigger mode and baud rate in memory
        """
        response = self.check_command("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def restore(self):
        """
        loads the settings from memory
        """
        response = self.check_command("resp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0
