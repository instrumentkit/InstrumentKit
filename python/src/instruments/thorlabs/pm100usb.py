#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# pm100usb.py: Driver class for the PM100USB power meter.
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

from instruments.generic_scpi import SCPIInstrument
from flufl.enum import IntEnum

import quantities as pq
from collections import namedtuple

## LOGGING #####################################################################

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

## CLASSES #####################################################################

class PM100USB(SCPIInstrument):
    """
    Instrument class for the `ThorLabs PM100USB`_ power meter.
    Note that as this is an SCPI-compliant instrument, the properties and
    methods of :class:`~instruments.generic_scpi.SCPIInstrument` may be used
    as well.
    
    .. _ThorLabs PM100USB: http://www.thorlabs.com/thorproduct.cfm?partnumber=PM100USB
    """
    
    ## ENUMS ##
    
    class SensorFlags(IntEnum):
        is_power_sensor = 1
        is_energy_sensor = 2
        response_settable = 16
        wavelength_settable = 32
        tau_settable = 64
        has_temperature_sensor = 256
        
    # We will cheat and also represent things by a named tuple over bools.
    # TODO: make a flagtuple into a new type in util_fns, copying this out
    #       as a starting point.
    _SensorFlags = namedtuple("SensorFlags", [
        flag.name for flag in SensorFlags
    ])
        
    ## INNER CLASSES ##
    
    def Sensor(object):
        def __init__(self, parent):
            self._parent = parent
            
            # Pull details about the sensor from SYST:SENSOR:IDN?
            sensor_idn = parent.sendcmd("SYST:SENSOR:IDN?")
            (
                self._name, self._serial_number, self._calibration_message,
                self._sensor_type, self._sensor_subtype, self._flags
            ) = sensor_idn.split(",")
            
            # Normalize things to enums as appropriate.
            # We want flags to be a named tuple over bools.
            self._flags = self._SensorFlags(**{
                e.name: bool(e & self._flags)
                for e in self.SensorFlags
            })
            
        @property
        def name(self):
            return self._name
        @property
        def serial_number(self):
            return self._serial_number
        @property
        def calibration_message(self):
            return self._calibration_message
        @property
        def type(self):
            return (self._sensor_type, self._sensor_subtype)
        @property
        def flags(self):
            return self._flags
       
    ## SENSOR PROPERTIES ##
    
    @property
    def sensor(self):
        """
        Returns information about the currently connected sensor.
        
        :type: :class:`PM100USB.Sensor`
        """
        return self.Sensor(self)
       
    ## SENSING CONFIGURATION PROPERTIES ##
    
    @property
    def averaging_count(self):
        """
        Integer specifying how many samples to collect and average over for
        each measurement, with each sample taking approximately 3 ms.
        """
        return int(self.query("SENS:AVER:COUN?"))
    @averaging_count.setter
    def averaging_count(self, newval):
        if newval < 1:
            raise ValueError("Must count at least one time.")
        self.sendcmd("SENS:AVER:COUN {}".format(newval))
    
    
    ## METHODS ##
    
    def read(self):
        # TODO: wrap in something that will add units!
        #       Doing so will take access to an actual device, however, since
        #       the ThorLabs manual is pathetically incomplete on that point.
        #       Specifically, what does "CONF?" return?
        return float(self.query('READ?'))
        
