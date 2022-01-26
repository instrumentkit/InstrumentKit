#!/usr/bin/env python
"""
Provides support for the Newport Agilis Controller AG-UC2 only (currently).

Agilis controllers are piezo driven motors that do not have support for units.
All units used in this document are given as steps.

Currently I only have a AG-PR100 rotation stage available for testing. This
device does not contain a limit switch and certain routines are therefore
completely untested! These are labeled in their respective docstring with:
    `UNTESTED: SEE COMMENT ON TOP`

The governing document for the commands and implementation is:

Agilis Series, Piezo Motor Driven Components, User's Manual, v2.2.x,
by Newport, especially chapter 4.7: "ASCII Command Set"
Document number from footer: EDH0224En5022 — 10/12

Routines not implemented at all:
- Measure current position (MA command):
  This routine interrupts the communication and
  restarts it afterwards. It can, according to the documentation, take up to
  2 minutes to complete. It is furthermore only available on stages with limit
  switches. I currently do not have the capability to implement this therefore.
- Absolute Move (PA command):
  Exactly the same reason as for MA command.
"""

# IMPORTS #####################################################################

import time

from enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class AGUC2(Instrument):

    """
    Handles the communication with the AGUC2 controller using the serial
    connection.

    Example usage:

    >>> import instruments as ik
    >>> agl = ik.newport.AGUC2.open_serial(port='COM5', baud=921600)

    This loads a controller into the instance `agl`. The two axis are
    called 'X' (axis 1) and 'Y' (axis 2). Controller commands and settings
    can be executed as following, as examples:

    Reset the controller:

    >>> agl.reset_controller()

    Print the firmware version:

    >>> print(agl.firmware_version)

    Individual axes can be controlled and queried as following:

    Relative move by 1000 steps:

    >>> agl.axis["X"].move_relative(1000)

    Activate jogging in mode 3:

    >>> agl.axis["X"].jog(3)

    Jogging will continue until the axis is stopped

    >>> agl.axis["X"].stop()

    Query the step amplitude, then set the postive one to +10 and the
    negative one to -20

    >>> print(agl.axis["X"].step_amplitude)
    >>> agl.axis["X"].step_amplitude = 10
    >>> agl.axis["X"].step_amplitude = -20
    """

    def __init__(self, filelike):
        super().__init__(filelike)

        # Instrument requires '\r\n' line termination
        self.terminator = "\r\n"

        # Some local variables
        self._remote_mode = False
        self._sleep_time = 0.25

    class Axis:

        """
        Class representing one axis attached to a Controller. This will likely
        work with the AG-UC8 controller as well.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by a Controller class
        """

        def __init__(self, cont, ax):
            if not isinstance(cont, AGUC2):
                raise TypeError("Don't do that.")

            # set axis integer
            if isinstance(ax, AGUC2.Axes):
                self._ax = ax.value
            else:
                self._ax = ax

            # set controller
            self._cont = cont

        # PROPERTIES #

        @property
        def axis_status(self):
            """
            Returns the status of the current axis.
            """
            resp = self._cont.ag_query(f"{int(self._ax)} TS")
            if resp.find("TS") == -1:
                return "Status code query failed."

            resp = int(resp.replace(str(int(self._ax)) + "TS", ""))
            status_message = agilis_status_message(resp)
            return status_message

        @property
        def jog(self):
            """
            Start jog motion / get jog mode
            Defined jog steps are defined with `step_amplitude` function (default
            16). If a jog mode is supplied, the jog motion is started. Otherwise
            the current jog mode is queried. Valid jog modes are:

            -4 — Negative direction, 666 steps/s at defined step amplitude.
            -3 — Negative direction, 1700 steps/s at max. step amplitude.
            -2 — Negative direction, 100 step/s at max. step amplitude.
            -1 — Negative direction, 5 steps/s at defined step amplitude.
             0 — No move, go to READY state.
             1 — Positive direction, 5 steps/s at defined step amplitude.
             2 — Positive direction, 100 steps/s at max. step amplitude.
             3 — Positive direction, 1700 steps/s at max. step amplitude.
             4 — Positive direction, 666 steps/s at defined step amplitude.

            :return: Jog motion set
            :rtype: `int`
            """
            resp = self._cont.ag_query(f"{int(self._ax)} JA?")
            return int(resp.split("JA")[1])

        @jog.setter
        def jog(self, mode):
            mode = int(mode)
            if mode < -4 or mode > 4:
                raise ValueError("Jog mode out of range. Must be between -4 and " "4.")

            self._cont.ag_sendcmd(f"{int(self._ax)} JA {mode}")

        @property
        def number_of_steps(self):
            """
            Returns the number of accumulated steps in forward direction minus
            the number of steps in backward direction since powering the
            controller or since the last ZP (zero position) command, whatever
            was last.

            Note:
            The step size of the Agilis devices are not 100% repeatable and
            vary between forward and backward direction. Furthermore, the step
            size can be modified using the SU command. Consequently, the TP
            command provides only limited information about the actual position
            of the device. In particular, an Agilis device can be at very
            different positions even though a TP command may return the same
            result.

            :return: Number of steps
            :rtype: int
            """
            resp = self._cont.ag_query(f"{int(self._ax)} TP")
            return int(resp.split("TP")[1])

        @property
        def move_relative(self):
            """
            Moves the axis by nn steps / Queries the status of the axis.
            Steps must be given a number that can be converted to a signed integer
            between -2,147,483,648 and 2,147,483,647.
            If queried, command returns the current target position. At least this
            is the expected behaviour, never worked with the rotation stage.
            """
            resp = self._cont.ag_query(f"{int(self._ax)} PR?")
            return int(resp.split("PR")[1])

        @move_relative.setter
        def move_relative(self, steps):
            steps = int(steps)
            if steps < -2147483648 or steps > 2147483647:
                raise ValueError(
                    "Number of steps are out of range. They must be "
                    "between -2,147,483,648 and 2,147,483,647"
                )

            self._cont.ag_sendcmd(f"{int(self._ax)} PR {steps}")

        @property
        def move_to_limit(self):
            """
            UNTESTED: SEE COMMENT ON TOP

            The  command functions properly only with devices that feature a
            limit switch like models AG-LS25, AG-M050L and AG-M100L.

            Starts a jog motion at a defined speed to the limit and stops
            automatically when the limit is activated. See `jog` command for
            details on available modes.

            Returns the distance of the current position to the limit in
            1/1000th of the total travel.
            """
            resp = self._cont.ag_query(f"{int(self._ax)} MA?")
            return int(resp.split("MA")[1])

        @move_to_limit.setter
        def move_to_limit(self, mode):
            mode = int(mode)
            if mode < -4 or mode > 4:
                raise ValueError("Jog mode out of range. Must be between -4 and " "4.")

            self._cont.ag_sendcmd(f"{int(self._ax)} MA {mode}")

        @property
        def step_amplitude(self):
            """
            Sets / Gets the step_amplitude.

            Sets the step amplitude (step size) in positive and / or negative
            direction. If the parameter is positive, it will set the step
            amplitude in the forward direction. If the parameter is negative,
            it will set the step amplitude in the backward direction. You can also
            provide a tuple or list of two values (one positive, one negative),
            which will set both values.
            Valid values are between -50 and 50, except for 0.

            :return: Tuple of first negative, then positive step amplitude
                response.
            :rtype: (`int`, `int`)
            """
            resp_neg = self._cont.ag_query(f"{int(self._ax)} SU-?")
            resp_pos = self._cont.ag_query(f"{int(self._ax)} SU+?")
            return int(resp_neg.split("SU")[1]), int(resp_pos.split("SU")[1])

        @step_amplitude.setter
        def step_amplitude(self, nns):
            if not isinstance(nns, tuple) and not isinstance(nns, list):
                nns = [nns]

            # check all values for validity
            for nn in nns:
                nn = int(nn)
                if nn < -50 or nn > 50 or nn == 0:
                    raise ValueError(
                        "Step amplitude {} outside the valid range. "
                        "It must be between -50 and -1 or between "
                        "1 and 50.".format(nn)
                    )

            for nn in nns:
                self._cont.ag_sendcmd(f"{int(self._ax)} SU {int(nn)}")

        @property
        def step_delay(self):
            """
            Sets/gets the step delay of stepping mode. The delay applies for both
            positive and negative directions. The delay is programmed as multiple
            of 10µs. For example, a delay of 40 is equivalent to
            40 x 10 µs = 400 µs. The maximum value of the parameter is equal to a
            delay of 2 seconds between pulses. By default, after reset, the value
            is 0.
            Setter: value must be integer between 0 and 200000 included

            :return: Step delay
            :rtype: `int`
            """
            resp = self._cont.ag_query(f"{int(self._ax)} DL?")
            return int(resp.split("DL")[1])

        @step_delay.setter
        def step_delay(self, nn):
            nn = int(nn)
            if nn < 0 or nn > 200000:
                raise ValueError(
                    "Step delay is out of range. It must be between " "0 and 200000."
                )

            self._cont.ag_sendcmd(f"{int(self._ax)} DL {nn}")

        # MODES #

        def am_i_still(self, max_retries=5):
            """
            Function to test if an axis stands still. It queries the status of
            the given axis and returns True (if axis is still) or False if it is
            moving.
            The reason this routine is implemented is because the status messages
            can time out. If a timeout occurs, this routine will retry the query
            until `max_retries` is reached. If query is still not successful, an
            IOError will be raised.

            :param int max_retries: Maximum number of retries

            :return: True if the axis is still, False if the axis is moving
            :rtype: bool
            """
            retries = 0

            while retries < max_retries:
                status = self.axis_status
                if status == agilis_status_message(0):
                    return True
                elif (
                    status == agilis_status_message(1)
                    or status == agilis_status_message(2)
                    or status == agilis_status_message(3)
                ):
                    return False
                else:
                    retries += 1

            raise OSError(
                "The function `am_i_still` ran out of maximum retries. "
                "Could not query the status of the axis."
            )

        def stop(self):
            """
            Stops the axis. This is useful to interrupt a jogging motion.
            """
            self._cont.ag_sendcmd(f"{int(self._ax)} ST")

        def zero_position(self):
            """
            Resets the step counter to zero. See `number_of_steps` for details.
            """
            self._cont.ag_sendcmd(f"{int(self._ax)} ZP")

    # ENUMS #

    class Axes(IntEnum):
        """
        Enumeration of valid delay channels for the AG-UC2 controller.
        """

        X = 1
        Y = 2

    # INNER CLASSES #

    # PROPERTIES #

    @property
    def axis(self):
        """
        Gets a specific axis object.

        The desired axis is accessed by passing an EnumValue from
        `~AGUC2.Channels`. For example, to access the X axis (axis 1):

        >>> import instruments as ik
        >>> agl = ik.newport.AGUC2.open_serial(port='COM5', baud=921600)
        >>> agl.axis["X"].move_relative(1000)

        See example in `AGUC2` for a more details

        :rtype: `AGUC2.Axis`
        """
        self.enable_remote_mode = True
        return ProxyList(self, self.Axis, AGUC2.Axes)

    @property
    def enable_remote_mode(self):
        """
        Gets / sets the status of remote mode.
        """
        return self._remote_mode

    @enable_remote_mode.setter
    def enable_remote_mode(self, newval):
        if newval and not self._remote_mode:
            self._remote_mode = True
            self.ag_sendcmd("MR")
        elif not newval and self._remote_mode:
            self._remote_mode = False
            self.ag_sendcmd("ML")

    @property
    def error_previous_command(self):
        """
        Retrieves the error of the previous command and translates it into a
        string. The string is returned
        """
        resp = self.ag_query("TE")

        if resp.find("TE") == -1:
            return "Error code query failed."

        resp = int(resp.replace("TE", ""))
        error_message = agilis_error_message(resp)
        return error_message

    @property
    def firmware_version(self):
        """
        Returns the firmware version of the controller
        """
        resp = self.ag_query("VE")
        return resp

    @property
    def limit_status(self):
        """
        PARTLY UNTESTED: SEE COMMENT ABOVE

        Returns the limit switch status of the controller. Possible returns
        are:
        - PH0: No limit switch is active
        - PH1: Limit switch of axis #1 (X) is active,
               limit switch of axis #2 (Y)  is not active
        - PH2: Limit switch of axis #2 (Y) is active,
               limit switch of axis #1 (X) is not active
        - PH3: Limit switches of axis #1 (X) and axis #2 (Y) are active

        If device has no limit switch, this routine always returns PH0
        """
        self.enable_remote_mode = True
        resp = self.ag_query("PH")
        return resp

    @property
    def sleep_time(self):
        """
        The device often times out. Therefore a sleep time can be set. The
        routine will wait for this amount (in seconds) every time after a
        command or a query are sent.
        Setting the sleep time: Give time in seconds
        If queried: Returns the sleep time in seconds as a float
        """
        return self._sleep_time

    @sleep_time.setter
    def sleep_time(self, t):
        if t < 0:
            raise ValueError("Sleep time must be >= 0.")

        self._sleep_time = float(t)

    # MODES #

    def reset_controller(self):
        """
        Resets the controller. All temporary settings are reset to the default
        value. Controller is put into local model.
        """
        self._remote_mode = False
        self.ag_sendcmd("RS")

    # SEND COMMAND AND QUERY ROUTINES AGILIS STYLE #

    def ag_sendcmd(self, cmd):
        """
        Sends the command, then sleeps
        """
        self.sendcmd(cmd)
        time.sleep(self._sleep_time)

    def ag_query(self, cmd, size=-1):
        """
        This runs the query command. However, the query command often times
        out for this device. The response of all queries are always strings.
        If timeout occurs, the response will be:
        "Query timed out."
        """
        try:
            resp = self.query(cmd, size=size)
        except OSError:
            resp = "Query timed out."

        # sleep
        time.sleep(self._sleep_time)

        return resp


def agilis_error_message(error_code):
    """
    Returns a string with th error message for a given Agilis error code.

    :param int error_code: error code as an integer

    :return: error message
    :rtype: string
    """
    if not isinstance(error_code, int):
        return "Error code is not an integer."

    error_dict = {
        0: "No error",
        -1: "Unknown command",
        -2: "Axis out of range (must be 1 or 2, or must not be specified)",
        -3: "Wrong format for parameter nn (or must not be specified)",
        -4: "Parameter nn out of range",
        -5: "Not allowed in local mode",
        -6: "Not allowed in current state",
    }

    if error_code in error_dict.keys():
        return error_dict[error_code]
    else:
        return "An unknown error occurred."


def agilis_status_message(status_code):
    """
    Returns a string with the status message for a given Agilis status
    code.

    :param int status_code: status code as returned

    :return: status message
    :rtype: string
    """
    if not isinstance(status_code, int):
        return "Status code is not an integer."

    status_dict = {
        0: "Ready (not moving).",
        1: "Stepping (currently executing a `move_relative` command).",
        2: "Jogging (currently executing a `jog` command with command"
        "parameter different than 0).",
        3: "Moving to limit (currently executing `measure_current_position`, "
        "`move_to_limit`, or `move_absolute` command).",
    }

    if status_code in status_dict.keys():
        return status_dict[status_code]
    else:
        return "An unknown status occurred."
