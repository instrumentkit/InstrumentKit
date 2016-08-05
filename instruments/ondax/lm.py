#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the Ondax LM Laser temperature controller.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import range, map
from enum import IntEnum, Enum

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import convert_temperature
from instruments.util_fns import enum_property, unitful_property, int_property

# CLASSES #####################################################################


class LM(Instrument):

    """
    The LM is the Laser to power the QES
    It can output date over an RS232 connection at the Back of the device.
    a PID control to keep the temperature at a set value.

    The user manual can be found here:
    http://www.ondax.com/Downloads/SureLock/Compact%20laser%20module%20manual.pdf
    """

    def __init__(self, filelike):
        super(LM, self).__init__(filelike)
        self.terminator = "\r"
        self.prompt = "> "

    def _ack_expected(self, msg=""):
        return msg

    @property
    def power(self):
        """

        :return: the laser power, in mW
        """
        response = self.query("rlp?")
        return response

    @power.setter
    def power(self, newval):
        """
        sets the power
        :param newval:
        :return: Nothing
        """
        self.sendcmd("slp:"+str(newval))

    @property
    def set_temperature(self):
        """

        :return: The Laser temperature (in C)
        """
        response = self.query("rstt? ")
        return response

    @property
    def temperature(self):
        response = self.query("rtt?")
        return response

    @temperature.setter
    def temperature(self, newval):
        """
        sets the temperature. (im C)
        :param newval:
        :return:
        """
        self.sendcmd("stt:"+str(newval))

    @property
    def current(self):
        response = self.query("rli?")
        return response

    @property
    def set_current(self):
        """

        :return: Current ACC of the Laser
        """
        response = self.query("rstli? ")
        return response

    @current.setter
    def current(self, newval):
        """
        Sets the Current ACC val.
        :param newval:
        :return:
        """
        self.sendcmd("slc:"+str(newval))

    @property
    def tec_current(self):
        response = self.query("rti?")
        return response

    def enableapc(self):
        """
        Enable laser APC driver
        :return:
        """
        self.sendcmd("len")

    def disableapc(self):
        """
        Disable laser APC driver
        :return:
        """
        self.sendcmd("ldis")

    def enableemission(self):
        """
        Turn on the laser emission output power
        :return:
        """
        self.sendcmd("lon")

    def disableemission(self):
        """
        Turn off the laser emission output power
        :return:
        """
        self.sendcmd("loff")

    def calibrate(self, newval):
        """
        Calibrate the laser power/Set the laser full power value in mW
        :param newval:
        :return:
        """
        self.sendcmd("clfp:"+str(newval))

    def start(self):
        """
        Start inner TTL modulation
        :return:
        """
        self.sendcmd("stm")


    def stop(self):
        """
        Stop inner TTl modulation
        :return:
        """
        self.sendcmd("ctm")

    def enabletec(self):
        """
        Enable TEC control
        :return:
        """
        self.sendcmd("tecon")

    def shutdowntec(self):
        """
        Shut down TEC control
        :return:
        """
        self.sendcmd("tecoff")

    def startapc(self):
        """
        Start APC power scan
        :return:
        """
        self.sendcmd("sps")

    def stopapc(self):
        """
        Stop APC power scan
        :return:
        """
        self.sendcmd("cps")

    def setfullpower(self, newval):
        """
        Set the laser output power from 0.0 to full power(Default: Full power)

        :param newval:
        :return:
        """
        self.sendcmd("slp:"+ newval)

    @property
    def firmware(self):
        """
        Return the laser system firmware version
        :return:
        """
        response = self.query("rsv?")
        return response

    @property
    def mod_on_time(self, newval):
        """
        Set inner TTL modulation on time, no less than 0.01ms
        :param newval:
        :return:
        """
        self.sendcmd("stont:"+ newval)

    @property
    def mod_off_time(self, newval):
        """
        Set inner TTL modulation off time, no less than 0.01ms
        :param newval:
        :return:
        """
        self.sendcmd("stofft:"+ newval)

    @property
    def power_scan_on_time(self, newval):
        """
        Set power scan on time in ms, no less than 0.01
        :param newval:
        :return:
        """
        self.sendcmd("stsont:"+ newval)

    @property
    def power_scan_off_time(self, newval):
        """
        Set power scan off time in ms, no less than 0.01
        :param newval:
        :return:
        """
        self.sendcmd("stsofft:"+ newval)

    @power_scan_step.setter
    def power_scan_step(self, newval):
        """
        Set APC power scan step
        :param newval:
        :return:
        """
        self.sendcmd("ssps:"+ newval)


    def rslp(self):
        """
        Return the present laser setting power in mW

        :return:
        """
        response = self.query("rslp?")
        return response

    def rclp(self):
        """
        Return the present laser full power
        :return:
        """
        response = self.query("rclp?")
        return response

    def rstt(self):
        """
        Return the TEC set up temperature
        :return:
        """
        response = self.query("rstt?")
        return response

    def rstli(self):
        """
        Return the ACC set up current in mA
        :return:
        """
        response = self.query("rstli?")
        return response

    def ssc(self):
        """
        Save the setting to the flash memory so
        the laser system can operate in the same
        setting after repower it
        :return:
        """
        self.sendcmd("ssc")

    def rlrs(self):
        """
        Read laser controller run status
        1, Laser controller runs normally
        2, Inner TTL modulation
        3, Laser power scan
        4, Waiting for calibrate laser power
        5, Over laser current shutdown
        6, TEC over temperature shutdown
        7, Waiting temperature stable
        8, Waiting 30 seconds
        :return:
        """
        response = self.query("rlrs?")
        return response

    def smlc(self, newval):
        """
        Set the maximum laser diode current in
        mA, if the current is over the limit the laser
        will shut down.

        :param newval:
        :return:
        """
        self.sendcmd("smlc:"+ newval)

    def rlcm(self):
        """
        Read the maximum laser current in mA
        :return:
        """
        response = self.query("rlcm?")
        return response

    def reset(self):
        """
        Reset the laser controller
        :return:
        """
        self.sendcmd("reset")

    def rsn(self):
        """
        Return the laser controller serial number
        :return:
        """
        response = self.query("rsn?")
        return response

    def lcen(self):
        """
        Enable ACC laser driver
        :return:
        """
        self.sendcmd("lcen")

    def lcdis(self):
        """
        Disable ACC laser driver
        :return:
        """
        self.sendcmd("lcdis")

    def lcon(self):
        """
        Turn on ACC laser driver
        :return:
        """
        self.sendcmd("lcon")

    def lcoff(self):
        """
        Turn off ACC laser driver
        :return:
        """
        self.sendcmd("lcoff")