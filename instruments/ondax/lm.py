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
from instruments.util_fns import convert_temperature, assume_units


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
        self.apc = self._AutomaticPowerControl(self)
        self.acc = self._AutomaticCurrentControl(self)
        self.tec = self._ThermoElectricCooler(self)
        self.modulation = self._Modulation(self)
        self._enabled = None

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

    class _AutomaticCurrentControl(object):
        """
        Options and functions related to the laser diode's automatic current
        control driver
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = None

        @property
        def target(self):
            """
            The ACC target current
            :return: Current ACC of the Laser
            :rtype: ~quantities.Quantity
            """
            response = float(self._parent.query("rstli?"))
            return response*pq.mA

        @property
        def enabled(self):
            """
            Get/Set the enabled state of the ACC driver

            :return: The enabled state of the ACC driver
            :rtype: bool
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if newval:
                self._parent.sendcmd("lcen")
            else:
                self._parent.sendcmd("lcdis")
            self._enabled = newval

        def on(self):
            """
            Turn on the ACC driver
            """
            self._parent.sendcmd("lcon")

        def off(self):
            """
            Turn off the ACC driver
            """
            self._parent.sendcmd("lcoff")

    class _AutomaticPowerControl(object):
        """
        Options and functions related to the laser diode's automatic power
        control driver.
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = None

        @property
        def target(self):
            """
            Return the target laser power in mW
            :return: the target laser power
            :rtype: ~quantities.Quantities
            """
            response = self._parent.query("rslp?")
            return float(response)*pq.mW

        @property
        def enabled(self):
            """
            Get/Set the enabled state of the APC driver
            :return: The enabled state of the APC driver
            :rtype: bool
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if newval:
                self._parent.sendcmd("len")
            else:
                self._parent.sendcmd("ldis")
            self._enabled = newval

        def start(self):
            """
            Start the APC scan.
            """
            self._parent.sendcmd("sps")

        def stop(self):
            """
            Stop the APC scan.
            """
            self._parent.sendcmd("cps")

    class _Modulation(object):
        """
        Options and functions related to the laser's optical output modulation.
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = None

        @property
        def on_time(self):
            """
            Get/Set the on time of TTL modulation, in mS
            :return: the on time in the TTL modulation.
            :rtype: ~quantities.Quantity
            """
            response = self._parent.query("stsont?")
            return float(response)*pq.mS

        @on_time.setter
        def on_time(self, newval):
            newval = assume_units(newval, pq.ms).rescale('mS').magnitude
            self._parent.sendcmd("stsont:"+str(newval))

        @property
        def off_time(self):
            """
            Get/Set the off time of TTL modulation, in mS
            :return: the off time in the TTL modulation.
            :rtype: ~quantities.Quantity
            """
            response = self._parent.query("stsofft?")
            return float(response)*pq.mS

        @off_time.setter
        def off_time(self, newval):
            newval = assume_units(newval, pq.ms).rescale('mS').magnitude
            self._parent.sendcmd("stsofft:"+str(newval))

        @property
        def enabled(self):
            """
            Get/Set the TTL modulation output state.
            :return: the TTL modulation state
            :rtype: bool
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if newval:
                self._parent.sendcmd("stm")
            else:
                self._parent.sendcmd("ctm")
            self._enabled = newval

    class _ThermoElectricCooler(object):
        """
        Options and functions relating to the laser diode's thermo electric
        cooler.
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = None

        @property
        def current(self):
            """
            Get the current TEC current
            :return: the TEC current
            :rtype: ~quantities.Quantity
            """
            response = self._parent.query("rti?")
            return float(response)*pq.mA

        @property
        def target(self):
            """
            Get the TEC target temperature
            :return: The target temperature
            :rtype: ~quantities.Quantity
            """
            response = self._parent.query("rstt?")
            return float(response)*pq.degC

        @property
        def enabled(self):
            """
            Get/Set the enable state fo the TEC.
            :return: The TEC's enabled state.
            :rtype: bool
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if newval:
                self._parent.sendcmd("tecon")
            else:
                self._parent.sendcmd("tecoff")
            self._enabled = newval

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
        Get/Set the laser diode current, in mA.
        :return: The laser diode current.
        :rtype: ~quantities.Quantity
        """
        response = self.query("rli?")
        return float(response)*pq.mA

    @current.setter
    def current(self, newval):
        newval = assume_units(newval, pq.mA).rescale('mA').magnitude
        self.sendcmd("slc:"+str(newval))

    @property
    def maximum_current(self):
        """
        Get/Set the maximum laser diode current in mA. If the current is set
        over the limit, the laser will shut down.

        :return: The maximum laser diode current.
        :rtype: ~quantities.Quantity
        """
        response = self.query("rlcm?")
        return float(response)*pq.mA

    @maximum_current.setter
    def maximum_current(self, newval):
        newval = assume_units(newval, pq.mA).rescale('mA').magnitude
        self.sendcmd("smlc:" + str(newval))

    @property
    def power(self):
        """
        Get/Set the laser's optical power.
        :return: the laser power, in mW
        :rtype: ~quantities.Quantity
        """
        response = self.query("rlp?")
        return float(response)*pq.mW

    @power.setter
    def power(self, newval):
        newval = assume_units(newval, pq.mW).rescale('mW').magnitude
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
        Get/Set the current laser diode temperature.
        :return: The current laser diode temperature.
        :rtype: ~quantities.Quantity
        """
        response = self.query("rtt?")
        return float(response)*pq.degC

    @temperature.setter
    def temperature(self, newval):
        newval = convert_temperature(newval, pq.degC).magnitude
        self.sendcmd("stt:"+str(newval))

    @property
    def enabled(self):
        """
        Enable/disable laser emission.
        :return: True for enabled, False for disabled.
        :rtype: bool
        """
        return self._enabled

    @enabled.setter
    def enabled(self, newval):
        if newval:
            self.sendcmd("lon")
        else:
            self.sendcmd("loff")
        self._enabled = newval

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
