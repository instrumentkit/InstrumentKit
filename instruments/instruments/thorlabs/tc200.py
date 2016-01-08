#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lcc25.py: class for the Thorlabs LCC25 Liquid Crystal Controller
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
# TC200 Class contributed by Catherine Holloway
#
## IMPORTS #####################################################################

import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class TC200(Instrument):
    """
    The TC200 is is a controller for the voltage across a heating element. It can also read in the temperature off of a
    thermistor and implements a PID control to keep the temperature at a set value.
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/12500/TC200-Manual.pdf
    """
    def __init__(self, filelike):
        super(TC200, self).__init__(filelike)
        self.terminator = "\r"
        self.prompt = ">"
        self.echo = True

    ## ENUMS ##

    class Mode(IntEnum):
        normal = 0
        cycle = 1

    class Sensor(IntEnum):
        PTC100 = 0
        PTC1000 = 1
        TH10K = 2

    ## PROPERTIES ##

    def name(self):
        """
        gets the name and version number of the device
        """
        response = self.query("*idn?")
        if response is "CMD_NOT_DEFINED":
            self.name()
        else:
            return response

    @property
    def mode(self):
        """
        Gets/sets the output mode of the TC200

        :type: `TC200.Mode`
        """
        response = self.query("stat?")
        if not response is "CMD_NOT_DEFINED":
            response_code = (int(response) << 1) % 2
            return TC200.Mode[response_code]

    @mode.setter
    def mode(self, newval):
        if newval.enum is not TC200.Mode:
            raise TypeError("Mode setting must be a `TC200.Mode` value, "
                "got {} instead.".format(type(newval)))
        response = self.query("mode={}".format(newval.name))
        print response

    @property
    def enable(self):
        """
        Gets/sets the heater enable status.

        If output enable is on (`True`), there is a voltage on the output.

        :rtype: `bool`
        """
        response = self.query("stat?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) % 2 is 1 else False

    @enable.setter
    def enable(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("TC200 enable property must be specified with a "
                            "boolean.")
        # the "ens" command is a toggle, we need to track two different cases, when it should be on and it is off,
        # and when it is off and should be on
        if newval and not self.enable:
            self.query("ens")
        elif not newval and self.enable:
            self.query("ens")

    @property
    def temperature(self):
        """
        Gets/sets the temperature

        :return: the temperature (in degrees C)
        :rtype: float
        """
        response = self.query("tact?").replace(" C","")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.degC

    @temperature.setter
    def temperature(self, newval):
        newval = assume_units(newval, pq.degC).rescale(self.degrees).magnitude
        print "new temperature: "+str(newval)

        if newval < 20.0:
            raise ValueError("Temperature is too low.")
        if newval > self.max_temperature:
            raise ValueError("Temperature is too high")
        self.query("tset={}".format(newval))


    @property
    def p(self):
        """
        Gets/sets the pgain

        :return: the gain (in nnn)
        :rtype: int
        """
        response = self.query("pid?")
        if not response is "CMD_NOT_DEFINED":
            return int(response.split(" ")[0])

    @p.setter
    def p(self, newval):
        if newval < 1:
            raise ValueError("P-Value is too low.")
        if newval > 250:
            raise ValueError("P-Value is too high")
        self.query("pgain={}".format(newval))

    @property
    def i(self):
        """
        Gets/sets the igain

        :return: the gain (in nnn)
        :rtype: int
        """
        response = self.query("pid?")
        if not response is "CMD_NOT_DEFINED":
            return int(response.split(" ")[1])

    @i.setter
    def i(self, newval):
        if newval < 0:
            raise ValueError("I-Value is too low.")
        if newval > 250:
            raise ValueError("I-Value is too high")
        self.query("igain={}".format(newval))

    @property
    def d(self):
        """
        Gets/sets the dgain

        :return: the gain (in nnn)
        :rtype: int
        """
        response = self.query("pid?")#.replace(self.end_terminator, "")
        if not response is "CMD_NOT_DEFINED":
            return int(response.split(" ")[2])

    @d.setter
    def d(self, newval):
        if newval < 0:
            raise ValueError("D-Value is too low.")
        if newval > 250:
            raise ValueError("D-Value is too high")
        self.query("dgain={}".format(newval))

    @property
    def degrees(self):
        """
        Gets/sets the mode of the temperature measurement.

        :type: `~quantities.unitquantity.UnitTemperature`
        """
        response = self.query("stat?")#.replace(self.end_terminator, "")
        response = int(response)
        if not response is "CMD_NOT_DEFINED":
            if (response >> 4 ) % 2:
                return pq.degC
            elif (response >> 5) % 2:
                return pq.degF
            else:
                return pq.degK

    @degrees.setter
    def degrees(self, newval):
        if newval is pq.degC:
            self.query("unit=c")
        elif newval is pq.degF:
            self.query("unit=f")
        elif newval is pq.degK:
            self.query("unit=k")
        else:
            raise TypeError("Invalid temperature type")

    @property
    def sensor(self):
        """
        Gets/sets the current thermistor type. Used for converting resistances to temperatures.

        :rtype: TC200.Sensor

        """
        response = self.query("sns?")#.replace(self.end_terminator, "")
        response = response.replace("Sensor = ", '').replace(self.terminator, "").replace(" ", "")
        if not response is "CMD_NOT_DEFINED":
            return TC200.Sensor(response)

    @sensor.setter
    def sensor(self, newval):
        if newval.enum is not TC200.Sensor:
            raise TypeError("Sensor setting must be a `TC200.Sensor` value, "
                "got {} instead.".format(type(newval)))
        self.query("sns={}".format(newval.name))

    @property
    def beta(self):
        """
        Gets/sets the beta value of the thermistor curve.

        :return: the gain (in nnn)
        :rtype: int
        """
        response = self.query("beta?")#.replace(self.end_terminator, "")
        if not response is "CMD_NOT_DEFINED":
            return int(response)

    @beta.setter
    def beta(self, newval):
        if newval < 2000:
            raise ValueError("Beta Value is too low.")
        if newval > 6000:
            raise ValueError("Beta Value is too high")
        self.query("beta={}".format(newval))

    @property
    def max_power(self):
        """
        Gets/sets the maximum power

        :return: the maximum power (in Watts)
        :rtype: `~quantities.Quantity`
        """
        response = self.query("pmax?")#.replace(self.end_terminator, "")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.W

    @max_power.setter
    def max_power(self, newval):
        newval = assume_units(newval, pq.W).rescale(pq.W).magnitude
        if newval < 0.1:
            raise ValueError("Power is too low.")
        if newval > 18.0:
            raise ValueError("Power is too high")
        self.query("PMAX={}".format(newval))

    @property
    def max_temperature(self):
        """
        Gets/sets the maximum temperature

        :return: the maximum temperature (in deg C)
        :rtype: `~quantities.Quantity`
        """
        response = self.query("tmax?").replace(" C","")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.degC

    @max_temperature.setter
    def max_temperature(self, newval):
        newval = assume_units(newval, pq.degC).rescale(pq.degC).magnitude
        if newval < 20:
            raise ValueError("Temperature is too low.")
        if newval > 205.0:
            raise ValueError("Temperature is too high")
        self.query("TMAX={}".format(newval))

    # The Cycles functionality of the TC200 is currently unimplemented, as it is complex, and its functionality is
    # redundant given a python interface to TC200
