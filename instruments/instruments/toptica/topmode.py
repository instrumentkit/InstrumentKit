#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the Toptica Topmode diode laser.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from builtins import range
from enum import IntEnum

import quantities as pq

from instruments.toptica.toptica_utils import convert_toptica_boolean as ctbool
from instruments.toptica.toptica_utils import convert_toptica_datetime as ctdate

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class TopMode(Instrument):

    """
    Communicates with a `Toptica Topmode`_ instrument.

    The TopMode is a diode laser with active stabilization, produced by Toptica.

    Example usage:

    >>> import instruments as ik
    >>> tm = ik.toptica.TopMode.open_serial('/dev/ttyUSB0', 115200)
    >>> print(tm.laser[0].wavelength)
    """

    def __init__(self, filelike):
        super(TopMode, self).__init__(filelike)
        self.prompt = "> "
        self._ack_expected = self._return_msg
        self.terminator = "\n"

    def _return_msg(self, msg=""): # pylint: disable=no-self-use
        return msg+"\r"

    # ENUMS #

    class CharmStatus(IntEnum):

        """
        Enum containing valid charm statuses for the lasers
        """
        un_initialized = 0
        in_progress = 1
        success = 2
        failure = 3

    # INNER CLASSES #

    class Laser(object):

        """
        Class representing a laser on the Toptica Topmode.

        .. warning:: This class should NOT be manually created by the user. It
        is designed to be initialized by the `Topmode` class.
        """

        def __init__(self, parent, idx):
            self.parent = parent
            self.name = "laser{}".format(idx + 1)

        # PROPERTIES #

        @property
        def serial_number(self):
            """
            Gets the serial number of the laser

            :return: The serial number of the specified laser
            :type: `str`
            """
            return self.parent.reference(self.name + ":serial-number")

        @property
        def model(self):
            """
            Gets the model type of the laser

            :return: The model of the specified laser
            :type: `str`
            """
            return self.parent.reference(self.name + ":model")

        @property
        def wavelength(self):
            """
            Gets the wavelength of the laser

            :return: The wavelength of the specified laser
            :units: Nanometers (nm)
            :type: `~quantities.quantity.Quantity`
            """
            return float(self.parent.reference(self.name + ":wavelength")) * pq.nm

        @property
        def production_date(self):
            """
            Gets the production date of the laser

            :return: The production date of the specified laser
            :type: `str`
            """
            return self.parent.reference(self.name + ":production-date")

        @property
        def enable(self):
            """
            Gets/sets the enable/disable status of the laser. Value of `True`
            is for enabled, and `False` for disabled.

            :return: Enable status of the specified laser
            :type: `bool`
            """
            return ctbool(self.parent.reference(self.name + ":emission"))

        @enable.setter
        def enable(self, newval):
            if not isinstance(newval, bool):
                raise TypeError(
                    "Laser emmission must be a boolean, got: {}".format(newval))
            self.parent.set(self.name + ":enable-emission", newval)

        @property
        def on_time(self):
            """
            Gets the 'on time' value for the laser

            :return: The 'on time' value for the specified laser
            :units: Seconds (s)
            :type: `~quantities.quantity.Quantity`
            """
            return float(self.parent.reference(self.name + ":ontime")) * pq.s

        @property
        def charm_status(self):
            """
            Gets the 'charm status' of the laser

            :return: The 'charm status' of the specified laser
            :type: `bool`
            """
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 7) % 2 == 1

        @property
        def temperature_control_status(self):
            """
            Gets the temperature control status of the laser

            :return: The temperature control status of the specified laser
            :type: `bool`
            """
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 5) % 2 == 1

        @property
        def current_control_status(self):
            """
            Gets the current control status of the laser

            :return: The current control status of the specified laser
            :type: `bool`
            """
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 6) % 2 == 1

        @property
        def tec_status(self):
            """
            Gets the TEC status of the laser

            :return: The TEC status of the specified laser
            :type: `bool`
            """
            return ctbool(self.parent.reference(self.name + ":tec:ready"))

        @property
        def intensity(self):
            """
            Gets the intensity of the laser. This property is unitless.

            :return: the intensity of the specified laser
            :units: Unitless
            :type: `float`
            """
            return float(self.parent.reference(self.name + ":intensity"))

        @property
        def mode_hop(self):
            """
            Gets whether the laser has mode-hopped

            :return: Mode-hop status of the specified laser
            :type: `bool`
            """
            return ctbool(self.parent.reference(self.name + ":charm:reg:mh-occured"))

        @property
        def lock_start(self):
            """
            Gets the date and time of the start of mode-locking

            :return: The datetime of start of mode-locking for specified laser
            :type: `datetime`
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:started"))

        @property
        def first_mode_hop_time(self):
            """
            Gets the date and time of the first mode hop

            :return: The datetime of the first mode hop for the specified laser
            :type: `datetime`
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:first-mh"))

        @property
        def latest_mode_hop_time(self):
            """
            Gets the date and time of the latest mode hop

            :return: The datetime of the latest mode hop for the
                specified laser
            :type: `datetime`
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:latest-mh"))

        @property
        def correction_status(self):
            """
            Gets the correction status of the laser

            :return: The correction status of the specified laser
            :type: `~TopMode.CharmStatus`
            """
            value = self.parent.reference(
                self.name + ":charm:correction-status")
            return TopMode.CharmStatus(int(value))

        # METHODS #

        def correction(self):
            """
            Run the correction against the specified laser
            """
            if self.correction_status == TopMode.CharmStatus.un_initialized:
                self.parent.execute(
                    self.name + ":charm:start-correction-initial")
            else:
                self.parent.execute(self.name + ":charm:start-correction")

    # TOPMODE CONTROL LANGUAGE #

    def execute(self, command):
        """
        Sends an execute command to the Topmode. This is used to automatically
        append (exec ' + command + ) to your command.

        :param str command: The command to be executed.
        """
        self.sendcmd("(exec '" + command + ")")

    def set(self, param, value):
        """
        Sends a param-set command to the Topmode. This is used to automatically
        handle appending "param-set!" and the rest of the param-set message
        structure to your message.

        :param str param: Parameter that will be set
        :param value: Value that the parameter will be set to
        :type value: `str`, `tuple`, `list`, or `bool`
        """

        if isinstance(value, str):
            self.query("(param-set! '{} \"{}\")".format(param, value))
        elif isinstance(value, tuple) or isinstance(value, list):
            self.query(
                "(param-set! '{} '({}))".format(param, " ".join(value)))
        elif isinstance(value, bool):
            value = "t" if value else "f"
            self.query("(param-set! '{} #{})".format(param, value))

    def reference(self, param):
        """
        Sends a reference commands to the Topmode. This is effectively a query
        request. It will append the required (param-ref ' + param + ).

        :param str param: Parameter that should be queried
        :return: Response to the reference request
        :rtype: `str`
        """
        return self.query("(param-ref '{})".format(param))

    def display(self, param):
        """
        Sends a display command to the Topmode.

        :param str param: Parameter that will be sent with a display request
        :return: Response to the display request
        """
        return self.query("(param-disp '{})".format(param))

    # PROPERTIES #

    @property
    def laser(self):
        """
        Gets a specific Topmode laser object. The desired laser is
        specified like one would access a list.

        For example, the following would print the wavelength from laser 1:

        >>> import instruments as ik
        >>> import quantities as pq
        >>> tm = ik.toptica.TopMode.open_serial('/dev/ttyUSB0', 115200)
        >>> print(tm.laser[0].wavelength)

        :rtype: `~TopMode.Laser`
        """
        return ProxyList(self, self.Laser, range(2))

    @property
    def enable(self):
        """
        is the laser lasing?
        :return:
        """
        return ctbool(self.reference("emission"))

    @enable.setter
    def enable(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Emission status must be a boolean, "
                            "got: {}".format(type(newval)))
        self.set("enable-emission", newval)

    @property
    def locked(self):
        """
        Gets the key switch lock status

        :return: `True` if key switch is locked, `False` otherwise
        :type: `bool`
        """
        return ctbool(self.reference("front-key-locked"))

    @property
    def interlock(self):
        """
        Gets the interlock switch open state

        :return: `True` if interlock switch is open, `False` otherwise
        :type: `bool`
        """
        return ctbool(self.reference("interlock-open"))

    @property
    def fpga_status(self):
        """
        Gets the FPGA health status

        :return: `False` if there has been a failure for the FPGA,
            `True` otherwise
        :type: `bool`
        """
        response = self.reference("system-health")
        if response.find("#f") >= 0:
            return False
        response = int(response)
        return False if response % 2 else True

    @property
    def temperature_status(self):
        """
        Gets the temperature controller board health status

        :return: `False` if there has been a failure for the temperature
            controller board, `True` otherwise
        :type: `bool`
        """
        response = int(self.reference("system-health"))
        return False if (response >> 1) % 2 else True

    @property
    def current_status(self):
        """
        Gets the current controller board health status

        :return: `False` if there has been a failure for the current controller
            board, `True` otherwise
        :type: `bool`
        """
        response = int(self.reference("system-health"))
        return False if (response >> 2) % 2 else True

    # METHODS #

    def reboot(self):
        """
        Reboots the system (note that the serial connect might have to be
        re-opened after this)
        """
        self.execute("reboot-system")
