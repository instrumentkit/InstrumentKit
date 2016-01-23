#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# tc200.py: class for the Thorlabs TC200 Temperature Controller
#
# © 2016 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#
# TC200 Class contributed by Catherine Holloway
#

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units, convert_temperature

# CLASSES #####################################################################


class TC200(Instrument):

    """
    The TC200 is is a controller for the voltage across a heating element.
    It can also read in the temperature off of a thermistor and implements
    a PID control to keep the temperature at a set value.

    The user manual can be found here:
    http://www.thorlabs.com/thorcat/12500/TC200-Manual.pdf
    """

    def __init__(self, filelike):
        super(TC200, self).__init__(filelike)
        self.terminator = "\r"
        self.prompt = ">"

    def _ack_expected(self, msg=""):
        return msg

    # ENUMS #

    class Mode(IntEnum):
        normal = 0
        cycle = 1

    class Sensor(IntEnum):
        ptc100 = 0
        ptc1000 = 1
        th10k = 2
        ntc10k = 3

    # PROPERTIES #

    def name(self):
        """
        Gets the name and version number of the device

        :return: the name string of the device
        :rtype: str
        """
        response = self.query("*idn?")
        return response

    @property
    def mode(self):
        """
        Gets/sets the output mode of the TC200

        :type: `TC200.Mode`
        """
        response = self.query("stat?")
        response_code = (int(response) >> 1) % 2
        return TC200.Mode[response_code]

    @mode.setter
    def mode(self, newval):
        if not hasattr(newval, 'enum'):
            raise TypeError("Mode setting must be a `TC200.Mode` value, "
                            "got {} instead.".format(type(newval)))
        if newval.enum is not TC200.Mode:
            raise TypeError("Mode setting must be a `TC200.Mode` value, "
                            "got {} instead.".format(type(newval)))
        out_query = "mode={}".format(newval.name)
        self.sendcmd(out_query)

    @property
    def enable(self):
        """
        Gets/sets the heater enable status.

        If output enable is on (`True`), there is a voltage on the output.

        :type: `bool`
        """
        response = self.query("stat?")
        return True if int(response) % 2 is 1 else False

    @enable.setter
    def enable(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("TC200 enable property must be specified with a "
                            "boolean.")
        # the "ens" command is a toggle, we need to track two different cases,
        # when it should be on and it is off, and when it is off and
        # should be on
        if newval and not self.enable:
            self.sendcmd("ens")
        elif not newval and self.enable:
            self.sendcmd("ens")

    @property
    def temperature(self):
        """
        Gets/sets the temperature

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units degrees C.
        :type: `~quantities.quantity.Quantity` or `int`
        :return: the temperature (in degrees C)
        :rtype: `~quantities.quantity.Quantity`
        """
        response = self.query("tact?").replace(
            " C", "").replace(" F", "").replace(" K", "")
        return float(response) * pq.degC

    @temperature.setter
    def temperature(self, newval):
        # the set temperature is always in celsius
        newval = convert_temperature(newval, pq.degC).magnitude
        if newval < 20.0 or newval > self.max_temperature:
            raise ValueError("Temperature is out of range.")
        out_query = "tset={}".format(newval)
        self.sendcmd(out_query)

    @property
    def p(self):
        """
        Gets/sets the p-gain. Valid numbers are [1,250].

        :return: the p-gain (in nnn)
        :rtype: `int`
        """
        response = self.query("pid?")
        return int(response.split(" ")[0])

    @p.setter
    def p(self, newval):
        if newval < 1:
            raise ValueError("P-Value is too low.")
        if newval > 250:
            raise ValueError("P-Value is too high")
        self.sendcmd("pgain={}".format(newval))

    @property
    def i(self):
        """
        Gets/sets the i-gain. Valid numbers are [1,250]

        :return: the i-gain (in nnn)
        :rtype: `int`
        """
        response = self.query("pid?")
        return int(response.split(" ")[1])

    @i.setter
    def i(self, newval):
        if newval < 0:
            raise ValueError("I-Value is too low.")
        if newval > 250:
            raise ValueError("I-Value is too high")
        self.sendcmd("igain={}".format(newval))

    @property
    def d(self):
        """
        Gets/sets the d-gain. Valid numbers are [0, 250]

        :return: the d-gain (in nnn)
        :type: `int`
        """
        response = self.query("pid?")
        return int(response.split(" ")[2])

    @d.setter
    def d(self, newval):
        if newval < 0:
            raise ValueError("D-Value is too low.")
        if newval > 250:
            raise ValueError("D-Value is too high")
        self.sendcmd("dgain={}".format(newval))

    @property
    def degrees(self):
        """
        Gets/sets the units of the temperature measurement.

        :return: The temperature units (degC/F/K) the TC200 is measuring in
        :type: `~quantities.unitquantity.UnitTemperature`
        """
        response = self.query("stat?")
        response = int(response)
        if (response >> 4) % 2 and (response >> 5) % 2:
            return pq.degC
        elif (response >> 5) % 2:
            return pq.degK
        else:
            return pq.degF

    @degrees.setter
    def degrees(self, newval):
        if newval is pq.degC:
            self.sendcmd("unit=c")
        elif newval is pq.degF:
            self.sendcmd("unit=f")
        elif newval is pq.degK:
            self.sendcmd("unit=k")
        else:
            raise TypeError("Invalid temperature type")

    @property
    def sensor(self):
        """
        Gets/sets the current thermistor type. Used for converting resistances
        to temperatures.

        :return: The thermistor type
        :type: `TC200.Sensor`
        """
        response = self.query("sns?")
        response = response.split(",")[0].replace(
            "Sensor = ", '').replace(self.terminator, "").replace(" ", "")
        return TC200.Sensor(response.lower())

    @sensor.setter
    def sensor(self, newval):
        if not hasattr(newval, 'enum'):
            raise TypeError("Sensor setting must be a `TC200.Sensor` value, "
                            "got {} instead.".format(type(newval)))

        if newval.enum is not TC200.Sensor:
            raise TypeError("Sensor setting must be a `TC200.Sensor` value, "
                            "got {} instead.".format(type(newval)))
        self.sendcmd("sns={}".format(newval.name))

    @property
    def beta(self):
        """
        Gets/sets the beta value of the thermistor curve.

        :return: the gain (in nnn)
        :type: `int`
        """
        response = self.query("beta?")
        return int(response)

    @beta.setter
    def beta(self, newval):
        if newval < 2000:
            raise ValueError("Beta Value is too low.")
        if newval > 6000:
            raise ValueError("Beta Value is too high")
        self.sendcmd("beta={}".format(newval))

    @property
    def max_power(self):
        """
        Gets/sets the maximum power

        :return: The maximum power
        :units: Watts (linear units)
        :type: `~quantities.quantity.Quantity`
        """
        response = self.query("pmax?")
        return float(response) * pq.W

    @max_power.setter
    def max_power(self, newval):
        newval = assume_units(newval, pq.W).rescale(pq.W).magnitude
        if newval < 0.1:
            raise ValueError("Power is too low.")
        if newval > 18.0:
            raise ValueError("Power is too high")
        self.sendcmd("PMAX={}".format(newval))

    @property
    def max_temperature(self):
        """
        Gets/sets the maximum temperature

        :return: the maximum temperature (in deg C)
        :units: As specified or assumed to be degree Celsius. Returns with
            units degC.
        :rtype: `~quantities.quantity.Quantity`
        """
        response = self.query("tmax?").replace(" C", "")
        return float(response) * pq.degC

    @max_temperature.setter
    def max_temperature(self, newval):
        newval = convert_temperature(newval, pq.degC).magnitude
        if newval < 20:
            raise ValueError("Temperature is too low.")
        if newval > 205.0:
            raise ValueError("Temperature is too high")
        self.sendcmd("TMAX={}".format(newval))
