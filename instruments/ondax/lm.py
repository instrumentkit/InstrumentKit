#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the Ondax LM Laser.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from enum import IntEnum

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import convert_temperature

# CLASSES #####################################################################


class LM(Instrument):
    """
    The LM is the Ondax SureLock VHG-stabilized laser diode.

    The user manual can be found here:
    http://www.ondax.com/Downloads/SureLock/Compact%20laser%20module%20manual.pdf
    """

    def __init__(self, filelike):
        super(LM, self).__init__(filelike)
        self.terminator = "\r"
        self.apc = self.AutomaticPowerControl(self)
        self.acc = self.AutomaticCurrentControl(self)
        self.tec = self.ThermoElectricCooler(self)
        self.modulation = self.Modulation(self)

    # ENUMS #
    class Status(IntEnum):
        """
        Enum containing the states of the laser
        """
        normal = 1
        inner_modulation = 2
        power_scan = 3
        calibrate = 4
        shutdown_current = 5
        shutdown_overheat = 6
        waiting_stable_temperature = 7
        waiting = 8

    # INNER CLASSES #

    class AutomaticCurrentControl(object):
        """
        Options and functions relatde to the laser diode's automatic current
        control driver
        """
        def __init__(self, parent):
            self.parent = parent

        @property
        def target(self):
            """
            The ACC target current
            :return: Current ACC of the Laser
            :rtype: quantities.mA
            """
            response = float(self.parent.query("rstli?"))
            return response*pq.mA

        def enable(self):
            """
            Enable the ACC driver
            """
            self.parent.sendcmd("lcen")

        def disable(self):
            """
            Disable the ACC driver
            """
            self.parent.sendcmd("lcdis")

        def on(self):
            """
            Turn on the ACC driver
            """
            self.parent.sendcmd("lcon")

        def off(self):
            """
            Turn off the ACC driver
            """
            self.parent.sendcmd("lcoff")

    class AutomaticPowerControl(object):
        """
        Options and functions related to the laser diode's automatic power
        control driver.
        """
        def __init__(self, parent):
            self.parent = parent

        @property
        def target(self):
            """
            Return the target laser power in mW
            :return: the target laser power
            :rtype: quantities.mW
            """
            response = self.parent.query("rslp?")
            return float(response)*pq.mW

        def enable(self):
            """
            Enable the APC driver
            """
            self.parent.sendcmd("len")

        def disable(self):
            """
            Disable the APC driver
            :return:
            """
            self.parent.sendcmd("ldis")

        def start(self):
            """
            Start the APC scan
            :return:
            """
            self.parent.sendcmd("sps")

        def stop(self):
            """
            Stop the APC scan
            :return:
            """
            self.parent.sendcmd("cps")

    class Modulation(object):
        """
        Options and functions related to the laser's optical output modulation.
        """
        def __init__(self, parent):
            self.parent = parent

        @property
        def on_time(self):
            """
            Get the on time of TTL modulation, in mS
            :return: the on time in the TTL modulation.
            :rtype: quantities.mS
            """
            response = self.parent.query("stsont?")
            return float(response)*pq.mS

        @on_time.setter
        def on_time(self, newval):
            """
            Set the on time og TTL modulation, in mS.
            :param newval: the modulation on time, in mS.
            :type newval: quantities.mS
            """
            newval = newval.rescale('mS').magnitude
            self.parent.sendcmd("stsont:"+str(newval))

        @property
        def off_time(self):
            """
            Get the off time of TTL modulation, in mS
            :return: the off time in the TTL modulation.
            :rtype: quantities.mS
            """
            response = self.parent.query("stsofft?")
            return float(response)*pq.mS

        @off_time.setter
        def off_time(self, newval):
            """
            Set the off time og TTL modulation, in mS.
            :param newval: the modulation off time, in mS.
            :type newval: quantities.mS
            """
            newval = newval.rescale('mS').magnitude
            self.parent.sendcmd("stsofft:"+str(newval))

        def start(self):
            """
            Start TTL modulation.
            """
            self.parent.sendcmd("stm")

        def stop(self):
            """
            Stop TTl modulation.
            """
            self.parent.sendcmd("ctm")

    class ThermoElectricCooler(object):
        """
        Options and functions relating to the laser diode's thermo electric
        cooler.
        """
        def __init__(self, parent):
            self.parent = parent

        @property
        def current(self):
            """
            Get the current TEC current
            :return: the TEC current
            :rtype: quantities.mA
            """
            response = self.parent.query("rti?")
            return float(response)*pq.mA

        @property
        def target(self):
            """
            Return the TEC target temperature
            :return: The target temperature
            :rtype: quantities.degC
            """
            response = self.parent.query("rstt?")
            return float(response)*pq.degC

        def enable(self):
            """
            Enable TEC control
            """
            self.parent.sendcmd("tecon")

        def shutdown(self):
            """
            Shut down TEC control
            """
            self.parent.sendcmd("tecoff")

    def _ack_expected(self, msg=""):
        if msg.find("?") > 0:
            return None
        else:
            return "OK"

    @property
    def firmware(self):
        """
        Return the laser system firmware version.
        :return: The laser system firmware.
        :rtype: str
        """
        response = self.query("rsv?")
        return response

    @property
    def current(self):
        """
        The laser diode current, in mA.
        :return: The laser diode current.
        :rtype: pq.mA
        """
        response = self.query("rli?")
        return float(response)*pq.mA

    @current.setter
    def current(self, newval):
        """
        Set the laser diode current.
        :param newval: the
        """
        newval = newval.rescale('mA').magnitude
        self.sendcmd("slc:"+str(newval))

    @property
    def maximum_current(self):
        """
        Read the maximum laser diode current in mA.
        :return: The maximum laser diode current.
        :rtype: pq.mA
        """
        response = self.query("rlcm?")
        return float(response)*pq.mA

    @maximum_current.setter
    def maximum_current(self, newval):
        """
        Set the maximum laser diode current in
        mA, if the current is over the limit the laser
        will shut down.

        :param newval: the new current.
        :type newval: quantities.mA
        """
        newval = newval.rescale("mA").magnitude
        self.sendcmd("smlc:" + str(newval))

    @property
    def power(self):
        """
        The laser's optical power.
        :return: the laser power, in mW
        :rtype: quantities.mW
        """
        response = self.query("rlp?")
        return float(response)*pq.mW

    @power.setter
    def power(self, newval):
        """
        Set the optical power.
        :param newval: the new power, in mW.
        :type newval: quantities.mW
        """
        newval = newval.rescale('mW').magnitude
        self.sendcmd("slp:"+str(newval))

    @property
    def serial_number(self):
        """
        Return the laser controller serial number
        :return: the serial number, as a string.
        :rtype: str
        """
        response = self.query("rsn?")
        return response

    @property
    def status(self):
        """
        Read laser controller run status.
        :return: The status.
        :rtype: LM.Status
        """
        response = self.query("rlrs?")
        return self.Status(int(response))

    @property
    def temperature(self):
        """
        Get the current laser diode temperature.
        :return: The current laser diode temperature.
        :rtype: quantity.degC
        """
        response = self.query("rtt?")
        return float(response)*pq.degC

    @temperature.setter
    def temperature(self, newval):
        """
        Set the laser diode temperature
        :param newval: the new temperature.
        :type newval: quantities.degC
        """
        newval = convert_temperature(newval, pq.degC).magnitude
        self.sendcmd("stt:"+str(newval))

    def enable(self):
        """
        Enable laser emission.
        """
        self.sendcmd("lon")

    def disable(self):
        """
        Disable laser emission.
        """
        self.sendcmd("loff")

    def save(self):
        """
        Save current settings in flash memory.
        """
        self.sendcmd("ssc")

    def reset(self):
        """
        Reset the laser controller.
        """
        self.sendcmd("reset")
