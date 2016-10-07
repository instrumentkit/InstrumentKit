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

    The user manual can be found on the `Ondax website`_.

    .. _Ondax website: http://www.ondax.com/Downloads/SureLock/Compact%20laser%20module%20manual.pdf
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
        Enum containing the valid states of the laser
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
        control driver.

        .. warning:: This class is not designed to be accessed directly. It
            should be interfaced via `LM.acc`
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = False

        @property
        def target(self):
            """
            Gets the automatic current control target setting.

            This property is accessed via the `LM.acc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.acc.target)

            :return: Current ACC of the Laser
            :units: mA
            :type: `~quantities.Quantity`
            """
            response = float(self._parent.query("rstli?"))
            return response*pq.mA

        @property
        def enabled(self):
            """
            Get/Set the enabled state of the ACC driver.

            This property is accessed via the `LM.acc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.acc.enabled)
            >>> laser.acc.enabled = True

            :type: `bool`
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("ACC driver enabled property must be specified"
                                "with a boolean, got {}.".format(type(newval)))
            if newval:
                self._parent.sendcmd("lcen")
            else:
                self._parent.sendcmd("lcdis")
            self._enabled = newval

        def on(self):
            """
            Turns on the automatic current control driver.

            This function is accessed via the `LM.acc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> laser.acc.on()
            """
            self._parent.sendcmd("lcon")

        def off(self):
            """
            Turn off the automatic current control driver.

            This function is accessed via the `LM.acc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> laser.acc.off()
            """
            self._parent.sendcmd("lcoff")

    class _AutomaticPowerControl(object):
        """
        Options and functions related to the laser diode's automatic power
        control driver.

        .. warning:: This class is not designed to be accessed directly. It
            should be interfaced via `LM.apc`
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = False

        @property
        def target(self):
            """
            Gets the target laser power of the automatic power control in mW.

            This property is accessed via the `LM.apc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.apc.target)

            :return: the target laser power
            :units: mW
            :type: `~quantities.Quantities`
            """
            response = self._parent.query("rslp?")
            return float(response)*pq.mW

        @property
        def enabled(self):
            """
            Get/Set the enabled state of the automatic power control driver.

            This property is accessed via the `LM.apc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.apc.enabled)
            >>> laser.apc.enabled = True

            :type: `bool`
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("APC driver enabled property must be specified "
                                "with a boolean, got {}.".format(type(newval)))
            if newval:
                self._parent.sendcmd("len")
            else:
                self._parent.sendcmd("ldis")
            self._enabled = newval

        def start(self):
            """
            Start the automatic power control scan.

            This function is accessed via the `LM.apc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> laser.apc.start()
            """
            self._parent.sendcmd("sps")

        def stop(self):
            """
            Stop the automatic power control scan.

            This function is accessed via the `LM.apc` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> laser.apc.stop()
            """
            self._parent.sendcmd("cps")

    class _Modulation(object):
        """
        Options and functions related to the laser's optical output modulation.

        .. warning:: This class is not designed to be accessed directly. It
            should be interfaced via `LM.modulation`
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = False

        @property
        def on_time(self):
            """
            Gets/sets the TTL modulation on time, in milliseconds.

            This property is accessed via the `LM.modulation` namespace.

            Example usage:

            >>> import instruments as ik
            >>> import quantities as pq
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.modulation.on_time)
            >>> laser.modulation.on_time = 1 * pq.ms

            :return: The TTL modulation on time
            :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units milliseconds.
            :type: `~quantities.Quantity`
            """
            response = self._parent.query("stsont?")
            return float(response)*pq.ms

        @on_time.setter
        def on_time(self, newval):
            newval = assume_units(newval, pq.ms).rescale(pq.ms).magnitude
            self._parent.sendcmd("stsont:"+str(newval))

        @property
        def off_time(self):
            """
            Gets/sets the TTL modulation off time, in milliseconds.

            This property is accessed via the `LM.modulation` namespace.

            Example usage:

            >>> import instruments as ik
            >>> import quantities as pq
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.modulation.on_time)
            >>> laser.modulation.on_time = 1 * pq.ms

            :return: The TTL modulation off time.
            :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units milliseconds.
            :type: `~quantities.Quantity`
            """
            response = self._parent.query("stsofft?")
            return float(response)*pq.ms

        @off_time.setter
        def off_time(self, newval):
            newval = assume_units(newval, pq.ms).rescale(pq.ms).magnitude
            self._parent.sendcmd("stsofft:"+str(newval))

        @property
        def enabled(self):
            """
            Get/Set the TTL modulation output state.

            This property is accessed via the `LM.modulation` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.modulation.enabled)
            >>> laser.modulation.enabled = True

            :type: `bool`
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("Modulation enabled property must be specified "
                                "with a boolean, got {}.".format(type(newval)))
            if newval:
                self._parent.sendcmd("stm")
            else:
                self._parent.sendcmd("ctm")
            self._enabled = newval

    class _ThermoElectricCooler(object):
        """
        Options and functions relating to the laser diode's thermo electric
        cooler.

        .. warning:: This class is not designed to be accessed directly. It
            should be interfaced via `LM.tec`
        """
        def __init__(self, parent):
            self._parent = parent
            self._enabled = False

        @property
        def current(self):
            """
            Gets the thermoelectric cooler current setting.

            This property is accessed via the `LM.tec` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.tec.current)

            :units: mA
            :type: `~quantities.Quantity`
            """
            response = self._parent.query("rti?")
            return float(response)*pq.mA

        @property
        def target(self):
            """
            Gets the thermoelectric cooler target temperature.

            This property is acccessed via the `LM.tec` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.tec.target)

            :units: Degrees Celcius
            :type: `~quantities.Quantity`
            """
            response = self._parent.query("rstt?")
            return float(response)*pq.degC

        @property
        def enabled(self):
            """
            Gets/sets the enable state for the thermoelectric cooler.

            This property is accessed via the `LM.tec` namespace.

            Example usage:

            >>> import instruments as ik
            >>> laser = ik.ondax.LM.open_serial('/dev/ttyUSB0', baud=1234)
            >>> print(laser.tec.enabled)
            >>> laser.tec.enabled = True

            :type: `bool`
            """
            return self._enabled

        @enabled.setter
        def enabled(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("TEC enabled property must be specified with "
                                "a boolean, got {}.".format(type(newval)))
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
        Gets the laser system firmware version.

        :type: `str`
        """
        response = self.query("rsv?")
        return response

    @property
    def current(self):
        """
        Gets/sets the laser diode current, in mA.

        :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units mA.
        :type: `~quantities.Quantity`
        """
        response = self.query("rli?")
        return float(response)*pq.mA

    @current.setter
    def current(self, newval):
        newval = assume_units(newval, pq.mA).rescale(pq.mA).magnitude
        self.sendcmd("slc:"+str(newval))

    @property
    def maximum_current(self):
        """
        Get/Set the maximum laser diode current in mA. If the current is set
        over the limit, the laser will shut down.

        :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units mA.
        :type: `~quantities.Quantity`
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
        Get/Set the laser's optical power in mW.

        :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units mW.
        :rtype: `~quantities.Quantity`
        """
        response = self.query("rlp?")
        return float(response)*pq.mW

    @power.setter
    def power(self, newval):
        newval = assume_units(newval, pq.mW).rescale(pq.mW).magnitude
        self.sendcmd("slp:"+str(newval))

    @property
    def serial_number(self):
        """
        Gets the laser controller serial number

        :type: `str`
        """
        response = self.query("rsn?")
        return response

    @property
    def status(self):
        """
        Read laser controller run status.

        :type: `LM.Status`
        """
        response = self.query("rlrs?")
        return self.Status(int(response))

    @property
    def temperature(self):
        """
        Gets/sets laser diode temperature.

        :units: As specified (if a `~quantities.Quantity`) or assumed
                to be of units degrees celcius.
        :type: `~quantities.Quantity`
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
        Gets/sets the laser emission enabled status.

        :type: `bool`
        """
        return self._enabled

    @enabled.setter
    def enabled(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Laser module enabled property must be specified "
                            "with a boolean, got {}.".format(type(newval)))
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
