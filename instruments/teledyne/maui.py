#!/usr/bin/env python
"""
Provides support for the Teledyne-Lecroy Oscilloscopes that use the
MAUI interface.

Development follows the IEEE 488.2 Command Reference from the MAUI
Oscilloscopes Remote Control and Automation Manual, document number
maui-remote-control-automation_10mar20.pdf

Where possible, commands are sent using the enum_property, ... that
are usually used for SCPI classes, even though, this is not an SCPI
class.
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.abstract_instruments import Oscilloscope
from instruments.optional_dep_finder import numpy
from instruments.units import ureg as u
from instruments.util_fns import assume_units, enum_property, bool_property, ProxyList

# CLASSES #####################################################################


# pylint: disable=too-many-lines,arguments-differ


class MAUI(Oscilloscope):

    """
    Medium to high-end Teledyne-Lecroy Oscilloscopes are shipped with
    the MAUI user interface. This class can be used to communicate with
    these instruments.

    By default, the IEEE 488.2 commands are used. However, commands
    based on MAUI's `app` definition can be submitted too using the
    appropriate send / query commands.

    Your scope must be set up to communicate via LXI (VXI11) to be used
    with pyvisa. Make sure that either the pyvisa-py or the NI-VISA
    backend is installed. Please see the pyvisa documentation for more
    information.

    This class inherits from: `Oscilloscope`

    Example usage (more examples below):
        >>> import instruments as ik
        >>> import instruments.units as u
        >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
        >>> # start the trigger in automatic mode
        >>> inst.run()
        >>> print(inst.trigger_state)  # print the trigger state
        <TriggerState.auto: 'AUTO'>
        >>> # set timebase to 20 ns per division
        >>> inst.time_div = u.Quantity(20, u.ns)
        >>> # call the first oscilloscope channel
        >>> channel = inst.channel[0]
        >>> channel.trace = True  # turn the trace on
        >>> channel.coupling = channel.Coupling.dc50  # coupling to 50 Ohm
        >>> channel.scale = u.Quantity(1, u.V)  # vertical scale to 1V/division
        >>> # transfer a waveform into xdat and ydat:
        >>> xdat, ydat = channel.read_waveform()
    """

    # CONSTANTS #

    # number of horizontal and vertical divisions on the scope
    # HOR_DIVS = 10
    # VERT_DIVS = 8

    def __init__(self, filelike):
        super().__init__(filelike)

        # turn off command headers -> for SCPI like behavior
        self.sendcmd("COMM_HEADER OFF")

        # constants
        self._number_channels = 4
        self._number_functions = 2
        self._number_measurements = 6

    # ENUMS #

    class MeasurementParameters(Enum):
        """
        Enum containing valid measurement parameters that only require
        one or more sources. Only single source parameters are currently
        implemented.
        """

        amplitude = "AMPL"
        area = "AREA"
        base = "BASE"
        delay = "DLY"
        duty_cycle = "DUTY"
        fall_time_80_20 = "FALL82"
        fall_time_90_10 = "FALL"
        frequency = "FREQ"
        maximum = "MAX"
        minimum = "MIN"
        mean = "MEAN"
        none = "NULL"
        overshoot_pos = "OVSP"
        overshoot_neg = "OVSN"
        peak_to_peak = "PKPK"
        period = "PER"
        phase = "PHASE"
        rise_time_20_80 = "RISE28"
        rise_time_10_90 = "RISE"
        rms = "RMS"
        stdev = "SDEV"
        top = "TOP"
        width_50_pos = "WID"
        width_50_neg = "WIDN"

    class TriggerState(Enum):

        """
        Enum containing valid trigger state for the oscilloscope.
        """

        auto = "AUTO"
        normal = "NORM"
        single = "SINGLE"
        stop = "STOP"

    class TriggerType(Enum):
        """Enum containing valid trigger state.

        Availability depends on oscilloscope options. Please consult
        your manual. Only simple types are currently included.

        .. warning:: Some of the trigger types are untested and might
            need further parameters in order to be appropriately set.
        """

        dropout = "DROPOUT"
        edge = "EDGE"
        glitch = "GLIT"
        interval = "INTV"
        pattern = "PA"
        runt = "RUNT"
        slew_rate = "SLEW"
        width = "WIDTH"
        qualified = "TEQ"
        tv = "TV"

    class TriggerSource(Enum):
        """Enum containing valid trigger sources.

        This is an enum for the default values.

        .. note:: This class is initialized like this for four channels,
            which is the default setting. If you change the number of
            channels, `TriggerSource` will be recreated using the
            routine `_create_trigger_source_enum`. This will make
            further channels available to you or remove channels that
            are not present in your setup.
        """

        c0 = "C1"
        c1 = "C2"
        c2 = "C3"
        c3 = "C4"
        ext = "EX"
        ext5 = "EX5"
        ext10 = "EX10"
        etm10 = "ETM10"
        line = "LINE"

    def _create_trigger_source_enum(self):
        """Create an Enum for the trigger source class.

        Needs to be dynamically generated, in case channel number
        changes!

        .. note:: Not all trigger sources are available on all scopes.
            Please consult the manual for your oscilloscope.
        """
        names = ["ext", "ext5", "ext10", "etm10", "line"]
        values = ["EX", "EX5", "EX10", "ETM10", "LINE"]
        # now add the channels
        for it in range(self._number_channels):
            names.append(f"c{it}")
            values.append(f"C{it + 1}")  # to send to scope
        # create and store the enum
        self.TriggerSource = Enum("TriggerSource", zip(names, values))

    # CLASSES #

    class DataSource(Oscilloscope.DataSource):

        """
        Class representing a data source (channel, math, ref) on a MAUI
        oscilloscope.

        .. warning:: This class should NOT be manually created by the
            user. It is designed to be initialized by the `MAUI` class.
        """

        # PROPERTIES #

        @property
        def name(self):
            return self._name

        # METHODS #

        def read_waveform(self, bin_format=False, single=True):
            """
            Reads the waveform and returns an array of floats with the
            data.

            :param bin_format: Not implemented, always False
            :type bin_format: bool
            :param single: Run a single trigger? Default True. In case
                a waveform from a channel is required, this option
                is recommended to be set to True. This means that the
                acquisition system is first stopped, a single trigger
                is issued, then the waveform is transfered, and the
                system is set back into the state it was in before.
                If sampling math with multiple samples, set this to
                false, otherwise the sweeps are cleared by the
                oscilloscope prior when a single trigger command is
                issued.
            :type single: bool

            :return: Data (time, signal) where time is in seconds and
                signal in V
            :rtype: `tuple`[`tuple`[`~pint.Quantity`, ...], `tuple`[`~pint.Quantity`, ...]]
                or if numpy is installed, `tuple`[`numpy.array`, `numpy.array`]

            :raises NotImplementedError: Bin format was chosen, but
                it is not implemented.

            Example usage:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> channel = inst.channel[0]  # set up channel
                >>> xdat, ydat = channel.read_waveform()  # read waveform
            """
            if bin_format:
                raise NotImplementedError(
                    "Bin format reading is currently "
                    "not implemented for the MAUI "
                    "routine."
                )

            if single:
                # get current trigger state (to reset after read)
                trig_state = self._parent.trigger_state
                # trigger state to single
                self._parent.trigger_state = self._parent.TriggerState.single

            # now read the data
            retval = self.query("INSPECT? 'SIMPLE'")  # pylint: disable=E1101

            # read the parameters to create time-base array
            horiz_off = self.query("INSPECT? 'HORIZ_OFFSET'")  # pylint: disable=E1101
            horiz_int = self.query("INSPECT? 'HORIZ_INTERVAL'")  # pylint: disable=E1101

            if single:
                # reset trigger
                self._parent.trigger_state = trig_state

            # format the string to appropriate data
            retval = retval.replace('"', "").split()
            if numpy:
                dat_val = numpy.array(retval, dtype=numpy.float)  # Convert to ndarray
            else:
                dat_val = tuple(map(float, retval))

            # format horizontal data into floats
            horiz_off = float(horiz_off.replace('"', "").split(":")[1])
            horiz_int = float(horiz_int.replace('"', "").split(":")[1])

            # create time base
            if numpy:
                dat_time = numpy.arange(
                    horiz_off, horiz_off + horiz_int * (len(dat_val)), horiz_int
                )
            else:
                dat_time = tuple(
                    val * horiz_int + horiz_off for val in range(len(dat_val))
                )

            # fix length bug, sometimes dat_time is longer than dat_signal
            if len(dat_time) > len(dat_val):
                dat_time = dat_time[0 : len(dat_val)]
            else:  # in case the opposite is the case
                dat_val = dat_val[0 : len(dat_time)]

            if numpy:
                return numpy.stack((dat_time, dat_val))
            else:
                return dat_time, dat_val

        trace = bool_property(
            command="TRA",
            doc="""
            Gets/Sets if a given trace is turned on or off.

            Example usage:

            >>> import instruments as ik
            >>> address = "TCPIP0::192.168.0.10::INSTR"
            >>> inst = inst = ik.teledyne.MAUI.open_visa(address)
            >>> channel = inst.channel[0]
            >>> channel.trace = False
            """,
        )

    class Channel(DataSource, Oscilloscope.Channel):

        """
        Class representing a channel on a MAUI oscilloscope.

        .. warning:: This class should NOT be manually created by the
            user. It is designed to be initialized by the `MAUI` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # 1-based

            # Initialize as a data source with name C{}.
            super(MAUI.Channel, self).__init__(self._parent, f"C{self._idx}")

        # ENUMS #

        class Coupling(Enum):
            """
            Enum containing valid coupling modes for the oscilloscope
            channel. 1 MOhm and 50 Ohm are included.
            """

            ac1M = "A1M"
            dc1M = "D1M"
            dc50 = "D50"
            ground = "GND"

        coupling = enum_property(
            "CPL",
            Coupling,
            doc="""
            Gets/sets the coupling for the specified channel.

            Example usage:

            >>> import instruments as ik
            >>> address = "TCPIP0::192.168.0.10::INSTR"
            >>> inst = inst = ik.teledyne.MAUI.open_visa(address)
            >>> channel = inst.channel[0]
            >>> channel.coupling = channel.Coupling.dc50
            """,
        )

        # PROPERTIES #

        @property
        def offset(self):
            """
            Sets/gets the vertical offset of the specified input
            channel.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> channel = inst.channel[0]  # set up channel
                >>> channel.offset = u.Quantity(-1, u.V)
            """
            return u.Quantity(float(self.query("OFST?")), u.V)

        @offset.setter
        def offset(self, newval):
            newval = assume_units(newval, "V").to(u.V).magnitude
            self.sendcmd(f"OFST {newval}")

        @property
        def scale(self):
            """
            Sets/Gets the vertical scale of the channel.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> channel = inst.channel[0]  # set up channel
                >>> channel.scale = u.Quantity(20, u.mV)
            """
            return u.Quantity(float(self.query("VDIV?")), u.V)

        @scale.setter
        def scale(self, newval):
            newval = assume_units(newval, "V").to(u.V).magnitude
            self.sendcmd(f"VDIV {newval}")

        # METHODS #

        def sendcmd(self, cmd):
            """
            Wraps commands sent from property factories in this class
            with identifiers for the specified channel.

            :param str cmd: Command to send to the instrument
            """
            self._parent.sendcmd(f"C{self._idx}:{cmd}")

        def query(self, cmd, size=-1):
            """
            Executes the given query. Wraps commands sent from property
            factories in this class with identifiers for the specified
            channel.

            :param str cmd: String containing the query to
                execute.
            :param int size: Number of bytes to be read. Default is read
                until termination character is found.
            :return: The result of the query as returned by the
                connected instrument.
            :rtype: `str`
            """
            return self._parent.query(f"C{self._idx}:{cmd}", size=size)

    class Math(DataSource):

        """
        Class representing a function on a MAUI oscilloscope.

        .. warning:: This class should NOT be manually created by the
            user. It is designed to be initialized by the `MAUI` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # 1-based

            # Initialize as a data source with name C{}.
            super(MAUI.Math, self).__init__(self._parent, f"F{self._idx}")

        # CLASSES #

        class Operators:
            """
            Sets the operator for a given channel.
            Most operators need a source `src`. If the source is given
            as an integer, it is assume that the a signal channel is
            requested. If you want to select another math channel for
            example, you will need to specify the source as a tuple:
            Example: `src=('f', 0)` would represent the first function
            channel (called F1 in the MAUI manual). A channel could be
            selected by calling `src=('c', 1)`, which would request the
            second channel (oscilloscope channel 2). Please consult the
            oscilloscope manual / the math setup itself for further
            possibilities.

            .. note:: Your oscilloscope might not have all functions
            that are described here. Also: Not all possibilities are
            currently implemented. However, extension of this
            functionality should be simple when following the given
            structure
            """

            def __init__(self, parent):
                self._parent = parent

            # PROPERTIES #

            @property
            def current_setting(self):
                """
                Gets the current setting and returns it as the full
                command, as sent to the scope when setting an operator.
                """
                return self._parent.query("DEF?")

            # METHODS - OPERATORS #

            def absolute(self, src):
                """
                Absolute of wave form.

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                send_str = f"'ABS({src_str})'"
                self._send_operator(send_str)

            def average(self, src, average_type="summed", sweeps=1000):
                """
                Average of wave form.

                :param int,tuple src: Source, see info above
                :param str average_type: `summed` or `continuous`
                :param int sweeps: In summed mode, how many sweeps to
                    collect. In `continuous` mode the weight of each
                    sweep is equal to 1/`1`sweeps`
                """
                src_str = _source(src)

                avgtp_str = "SUMMED"
                if average_type == "continuous":
                    avgtp_str = "CONTINUOUS"

                send_str = "'AVG({})',AVERAGETYPE,{},SWEEPS,{}".format(
                    src_str, avgtp_str, sweeps
                )

                self._send_operator(send_str)

            def derivative(self, src, vscale=1e6, voffset=0, autoscale=True):
                """
                Derivative of waveform using subtraction of adjacent
                samples. If vscale and voffset are unitless, V/s are
                assumed.

                :param int,tuple src: Source, see info above
                :param float vscale: vertical units to display (V/s)
                :param float voffset: vertical offset (V/s)
                :param bool autoscale: auto scaling of vscale, voffset?
                """
                src_str = _source(src)

                vscale = assume_units(vscale, u.V / u.s).to(u.V / u.s).magnitude

                voffset = assume_units(voffset, u.V / u.s).to(u.V / u.s).magnitude

                autoscale_str = "OFF"
                if autoscale:
                    autoscale_str = "ON"

                send_str = (
                    "'DERI({})',VERSCALE,{},VEROFFSET,{},"
                    "ENABLEAUTOSCALE,{}".format(src_str, vscale, voffset, autoscale_str)
                )

                self._send_operator(send_str)

            def difference(self, src1, src2, vscale_variable=False):
                """
                Difference between two sources, `src1`-`src2`.

                :param int,tuple src1: Source 1, see info above
                :param int,tuple src2: Source 2, see info above
                :param bool vscale_variable: Horizontal and vertical
                    scale for addition and subtraction must be
                    identical. Allow for variable vertical scale in
                    result?
                """
                src1_str = _source(src1)
                src2_str = _source(src2)

                opt_str = "FALSE"
                if vscale_variable:
                    opt_str = "TRUE"

                send_str = "'{}-{}',VERSCALEVARIABLE,{}".format(
                    src1_str, src2_str, opt_str
                )

                self._send_operator(send_str)

            def envelope(self, src, sweeps=1000, limit_sweeps=True):
                """
                Highest and lowest Y values at each X in N sweeps.

                :param int,tuple src: Source, see info above
                :param int sweeps: Number of sweeps
                :param bool limit_sweeps: Limit the number of sweeps?
                """
                src_str = _source(src)
                send_str = "'EXTR({})',SWEEPS,{},LIMITNUMSWEEPS,{}".format(
                    src_str, sweeps, limit_sweeps
                )
                self._send_operator(send_str)

            def eres(self, src, bits=0.5):
                """
                Smoothing function defined by extra bits of resolution.

                :param int,tuple src: Source, see info above
                :param float bits: Number of bits. Possible values are
                    (0.5, 1.0, 1.5, 2.0, 2.5, 3.0). If not in list,
                    default to 0.5.
                """
                src_str = _source(src)

                bits_possible = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
                if bits not in bits_possible:
                    bits = 0.5

                send_str = f"'ERES({src_str})',BITS,{bits}"

                self._send_operator(send_str)

            def fft(
                self, src, type="powerspectrum", window="vonhann", suppress_dc=True
            ):
                """
                Fast Fourier Transform of signal.

                :param int,tuple src: Source, see info above
                :param str type: Type of power spectrum. Possible
                    options are: ['real', 'imaginary', 'magnitude',
                    'phase', 'powerspectrum', 'powerdensity'].
                    Default: 'powerspectrum'
                :param str window: Window. Possible options are:
                    ['blackmanharris', 'flattop', 'hamming',
                    'rectangular', 'vonhann']. Default: 'vonhann'
                :param bool suppress_dc: Supress DC?
                """
                src_str = _source(src)

                type_possible = [
                    "real",
                    "imaginary",
                    "magnitude",
                    "phase",
                    "powerspectrum",
                    "powerdensity",
                ]
                if type not in type_possible:
                    type = "powerspectrum"

                window_possible = [
                    "blackmanharris",
                    "flattop",
                    "hamming",
                    "rectangular",
                    "vonhann",
                ]
                if window not in window_possible:
                    window = "vonhann"

                if suppress_dc:
                    opt = "ON"
                else:
                    opt = "OFF"

                send_str = "'FFT({})',TYPE,{},WINDOW,{},SUPPRESSDC,{}".format(
                    src_str, type, window, opt
                )

                self._send_operator(send_str)

            def floor(self, src, sweeps=1000, limit_sweeps=True):
                """
                Lowest vertical value at each X value in N sweeps.

                :param int,tuple src: Source, see info above
                :param int sweeps: Number of sweeps
                :param bool limit_sweeps: Limit the number of sweeps?
                """
                src_str = _source(src)
                send_str = "'FLOOR({})',SWEEPS,{},LIMITNUMSWEEPS,{}".format(
                    src_str, sweeps, limit_sweeps
                )
                self._send_operator(send_str)

            def integral(self, src, multiplier=1, adder=0, vscale=1e-3, voffset=0):
                """
                Integral of waveform.

                :param int,tuple src: Source, see info above
                :param float multiplier: 0 to 1e15
                :param float adder: 0 to 1e15
                :param float vscale: vertical units to display (Wb)
                :param float voffset: vertical offset (Wb)
                """
                src_str = _source(src)

                vscale = assume_units(vscale, u.Wb).to(u.Wb).magnitude

                voffset = assume_units(voffset, u.Wb).to(u.Wb).magnitude

                send_str = (
                    "'INTG({}),MULTIPLIER,{},ADDER,{},VERSCALE,{},"
                    "VEROFFSET,{}".format(src_str, multiplier, adder, vscale, voffset)
                )

                self._send_operator(send_str)

            def invert(self, src):
                """
                Inversion of waveform (-waveform).

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                self._send_operator(f"'-{src_str}'")

            def product(self, src1, src2):
                """
                Product of two sources, `src1`*`src2`.

                :param int,tuple src1: Source 1, see info above
                :param int,tuple src2: Source 2, see info above
                """
                src1_str = _source(src1)
                src2_str = _source(src2)

                send_str = f"'{src1_str}*{src2_str}'"

                self._send_operator(send_str)

            def ratio(self, src1, src2):
                """
                Ratio of two sources, `src1`/`src2`.

                :param int,tuple src1: Source 1, see info above
                :param int,tuple src2: Source 2, see info above
                """
                src1_str = _source(src1)
                src2_str = _source(src2)

                send_str = f"'{src1_str}/{src2_str}'"

                self._send_operator(send_str)

            def reciprocal(self, src):
                """
                Reciprocal of waveform (1/waveform).

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                self._send_operator(f"'1/{src_str}'")

            def rescale(self, src, multiplier=1, adder=0):
                """
                Rescales the waveform (w) in the style.
                multiplier * w + adder

                :param int,tuple src: Source, see info above
                :param float multiplier: multiplier
                :param float adder: addition in V or assuming V
                """
                src_str = _source(src)

                adder = assume_units(adder, u.V).to(u.V).magnitude

                send_str = "'RESC({})',MULTIPLIER,{},ADDER,{}".format(
                    src_str, multiplier, adder
                )

                self._send_operator(send_str)

            def sinx(self, src):
                """
                Sin(x)/x interpolation to produce 10x output samples.

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                self._send_operator(f"'SINX({src_str})'")

            def square(self, src):
                """
                Square of the input waveform.

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                self._send_operator(f"'SQR({src_str})'")

            def square_root(self, src):
                """
                Square root of the input waveform.

                :param int,tuple src: Source, see info above
                """
                src_str = _source(src)
                self._send_operator(f"'SQRT({src_str})'")

            def sum(self, src1, src2):
                """
                Product of two sources, `src1`+`src2`.

                :param int,tuple src1: Source 1, see info above
                :param int,tuple src2: Source 2, see info above
                """
                src1_str = _source(src1)
                src2_str = _source(src2)

                send_str = f"'{src1_str}+{src2_str}'"

                self._send_operator(send_str)

            def trend(self, src, vscale=1, center=0, autoscale=True):
                """
                Trend of the values of a paramter

                :param float vscale: vertical units to display (V)
                :param float center: center (V)
                """
                src_str = _source(src)

                vscale = assume_units(vscale, u.V).to(u.V).magnitude

                center = assume_units(center, u.V).to(u.V).magnitude

                if autoscale:
                    auto_str = "ON"
                else:
                    auto_str = "OFF"

                send_str = (
                    "'TREND({})',VERSCALE,{},CENTER,{},"
                    "AUTOFINDSCALE,{}".format(src_str, vscale, center, auto_str)
                )

                self._send_operator(send_str)

            def roof(self, src, sweeps=1000, limit_sweeps=True):
                """
                Highest vertical value at each X value in N sweeps.

                :param int,tuple src: Source, see info above
                :param int sweeps: Number of sweeps
                :param bool limit_sweeps: Limit the number of sweeps?
                """
                src_str = _source(src)
                send_str = "'ROOF({})',SWEEPS,{},LIMITNUMSWEEPS,{}".format(
                    src_str, sweeps, limit_sweeps
                )
                self._send_operator(send_str)

            def _send_operator(self, cmd):
                """
                Set the operator in the scope.
                """
                self._parent.sendcmd("{},{}".format("DEFINE EQN", cmd))

        # PROPERTIES #

        @property
        def operator(self):
            """Get an operator object to set use to do math.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> channel = inst.channel[0]  # set up channel
                >>> # set up the first math function
                >>> function = inst.math[0]
                >>> function.trace = True  # turn the trace on
                >>> # set function to average the first oscilloscope channel
                >>> function.operator.average(0)
            """
            return self.Operators(self)

        # METHODS #

        def clear_sweeps(self):
            """Clear the sweeps in a measurement."""
            self._parent.clear_sweeps()  # re-implemented because handy

        def sendcmd(self, cmd):
            """
            Wraps commands sent from property factories in this class
            with identifiers for the specified channel.

            :param str cmd: Command to send to the instrument
            """
            self._parent.sendcmd(f"F{self._idx}:{cmd}")

        def query(self, cmd, size=-1):
            """
            Executes the given query. Wraps commands sent from property
            factories in this class with identifiers for the specified
            channel.

            :param str cmd: String containing the query to
                execute.
            :param int size: Number of bytes to be read. Default is read
                until termination character is found.
            :return: The result of the query as returned by the
                connected instrument.
            :rtype: `str`
            """
            return self._parent.query(f"F{self._idx}:{cmd}", size=size)

    class Measurement:

        """
        Class representing a measurement on a MAUI oscilloscope.

        .. warning:: This class should NOT be manually created by the
            user. It is designed to be initialized by the `MAUI` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1  # 1-based

        # CLASSES #

        class State(Enum):
            """
            Enum class for Measurement Parameters. Required to turn it
            on or off.
            """

            statistics = "CUST,STAT"
            histogram_icon = "CUST,HISTICON"
            both = "CUST,BOTH"
            off = "CUST,OFF"

        # PROPERTIES #

        measurement_state = enum_property(
            command="PARM",
            enum=State,
            doc="""
                Sets / Gets the measurement state. Valid values are
                'statistics', 'histogram_icon', 'both', 'off'.

                Example:
                    >>> import instruments as ik
                    >>> import instruments.units as u
                    >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                    >>> msr1 = inst.measurement[0]  # set up first measurement
                    >>> msr1.measurement_state = msr1.State.both  # set to `both`
                """,
        )

        @property
        def statistics(self):
            """
            Gets the statistics for the selected parameter. The scope
            must be in `My_Measure` mode.

            :return tuple: (average, low, high, sigma, sweeps)
            :return type: (float, float, float, float, float)
            """
            ret_str = self.query(f"PAST? CUST, P{self._idx}").rstrip().split(",")
            # parse the return string -> put into dictionary:
            ret_dict = {
                ret_str[it]: ret_str[it + 1] for it in range(0, len(ret_str), 2)
            }
            try:
                stats = (
                    float(ret_dict["AVG"]),
                    float(ret_dict["LOW"]),
                    float(ret_dict["HIGH"]),
                    float(ret_dict["SIGMA"]),
                    float(ret_dict["SWEEPS"]),
                )
            except ValueError:  # some statistics did not return
                raise ValueError(
                    "Some statistics did not return useful "
                    "values. The return string is {}. Please "
                    "ensure that statistics is properly turned "
                    "on.".format(ret_str)
                )
            return stats

        # METHODS #

        def delete(self):
            """
            Deletes the given measurement parameter.
            """
            self.sendcmd(f"PADL {self._idx}")

        def set_parameter(self, param, src):
            """
            Sets a given parameter that should be measured on this
            given channel.

            :param `inst.MeasurementParameters` param: The parameter
                to set from the given enum list.
            :param int,tuple src: Source, either as an integer if a
                channel is requested (e.g., src=0 for Channel 1) or as
                a tuple in the form, e.g., ('F', 1). Here 'F' refers
                to a mathematical function and 1 would take the second
                mathematical function `F2`.

            :raises AttributeError: The chosen parameter is invalid.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> msr1 = inst.measurement[0]  # set up first measurement
                >>> # setup to measure the 10 - 90% rise time on first channel
                >>> msr1.set_parameter(inst.MeasurementParameters.rise_time_10_90, 0)
            """
            if not isinstance(param, self._parent.MeasurementParameters):
                raise AttributeError(
                    "Parameter must be selected from {}.".format(
                        self._parent.MeasurementParameters
                    )
                )

            send_str = f"PACU {self._idx},{param.value},{_source(src)}"

            self.sendcmd(send_str)

        def sendcmd(self, cmd):
            """
            Wraps commands sent from property factories in this class
            with identifiers for the specified channel.

            :param str cmd: Command to send to the instrument
            """
            self._parent.sendcmd(cmd)

        def query(self, cmd, size=-1):
            """
            Executes the given query. Wraps commands sent from property
            factories in this class with identifiers for the specified
            channel.

            :param str cmd: String containing the query to
                execute.
            :param int size: Number of bytes to be read. Default is read
                until termination character is found.
            :return: The result of the query as returned by the
                connected instrument.
            :rtype: `str`
            """
            return self._parent.query(cmd, size=size)

    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets an iterator or list for easy Pythonic access to the various
        channel objects on the oscilloscope instrument.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> channel = inst.channel[0]  # get first channel
        """
        return ProxyList(self, self.Channel, range(self.number_channels))

    @property
    def math(self):
        """
        Gets an iterator or list for easy Pythonic access to the various
        math data sources objects on the oscilloscope instrument.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> math = inst.math[0]  # get first math function
        """
        return ProxyList(self, self.Math, range(self.number_functions))

    @property
    def measurement(self):
        """
        Gets an iterator or list for easy Pythonic access to the various
        measurement data sources objects on the oscilloscope instrument.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> msr = inst.measurement[0]  # get first measurement parameter
        """
        return ProxyList(self, self.Measurement, range(self.number_measurements))

    @property
    def ref(self):
        raise NotImplementedError

    # PROPERTIES

    @property
    def number_channels(self):
        """
        Sets/Gets the number of channels available on the specific
        oscilloscope. Defaults to 4.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.number_channel = 2  # for a oscilloscope with 2 channels
            >>> inst.number_channel
            2
        """
        return self._number_channels

    @number_channels.setter
    def number_channels(self, newval):
        self._number_channels = newval
        # create new trigger source enum
        self._create_trigger_source_enum()

    @property
    def number_functions(self):
        """
        Sets/Gets the number of functions available on the specific
        oscilloscope. Defaults to 2.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.number_functions = 4  # for a oscilloscope with 4 math functions
            >>> inst.number_functions
            4
        """
        return self._number_functions

    @number_functions.setter
    def number_functions(self, newval):
        self._number_functions = newval

    @property
    def number_measurements(self):
        """
        Sets/Gets the number of measurements available on the specific
        oscilloscope. Defaults to 6.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.number_measurements = 4  # for a oscilloscope with 4 measurements
            >>> inst.number_measurements
            4
        """
        return self._number_measurements

    @number_measurements.setter
    def number_measurements(self, newval):
        self._number_measurements = newval

    @property
    def self_test(self):
        """
        Runs an oscilloscope's internal self test and returns the
        result. The self-test includes testing the hardware of all
        channels, the timebase and the trigger circuits.
        Hardware failures are identified by a unique binary code in the
        returned <status> number. A status of 0 indicates that no
        failures occurred.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.self_test()
        """
        # increase timeout x 10 to allow for enough time to test
        self.timeout *= 10
        retval = self.query("*TST?")
        self.timeout /= 10
        return retval

    @property
    def show_id(self):
        """
        Gets the scope information and returns it. The response
        comprises manufacturer, oscilloscope model, serial number,
        and firmware revision level.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.show_id()
        """
        return self.query("*IDN?")

    @property
    def show_options(self):
        """
        Gets and returns oscilloscope options: installed software or
        hardware that is additional to the standard instrument
        configuration. The response consists of a series of response
        fields listing all the installed options.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.show_options()
        """
        return self.query("*OPT?")

    @property
    def time_div(self):
        """
        Sets/Gets the time per division, modifies the timebase setting.
        Unitful.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.time_div = u.Quantity(200, u.ns)
        """
        return u.Quantity(float(self.query("TDIV?")), u.s)

    @time_div.setter
    def time_div(self, newval):
        newval = assume_units(newval, "s").to(u.s).magnitude
        self.sendcmd(f"TDIV {newval}")

    # TRIGGER PROPERTIES

    trigger_state = enum_property(
        command="TRMD",
        enum=TriggerState,
        doc="""
            Sets / Gets the trigger state. Valid values are are defined
            in `TriggerState` enum class.

            Example:
                >>> import instruments as ik
                >>> import instruments.units as u
                >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
                >>> inst.trigger_state = inst.TriggerState.normal
            """,
    )

    @property
    def trigger_delay(self):
        """
        Sets/Gets the trigger offset with respect to time zero (i.e.,
        a horizontal shift). Unitful.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.trigger_delay = u.Quantity(60, u.ns)

        """
        return u.Quantity(float(self.query("TRDL?")), u.s)

    @trigger_delay.setter
    def trigger_delay(self, newval):
        newval = assume_units(newval, "s").to(u.s).magnitude
        self.sendcmd(f"TRDL {newval}")

    @property
    def trigger_source(self):
        """Sets / Gets the trigger source.

        .. note:: The `TriggerSource` class is dynamically generated
        when the number of channels is switched. The above shown class
        is only the default! Channels are added and removed, as
        required.

        .. warning:: If a trigger type is currently set on the
            oscilloscope that is not implemented in this class,
            setting the source will fail. The oscilloscope is set up
            such that the the trigger type and source are set at the
            same time. However, for convenience, these two properties
            are split apart here.

        :return: Trigger source.
        :rtype: Member of `TriggerSource` class.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.trigger_source = inst.TriggerSource.ext  # external trigger
        """
        retval = self.query("TRIG_SELECT?").split(",")[2]
        return self.TriggerSource(retval)

    @trigger_source.setter
    def trigger_source(self, newval):
        curr_trig_typ = self.trigger_type
        cmd = f"TRIG_SELECT {curr_trig_typ.value},SR,{newval.value}"
        self.sendcmd(cmd)

    @property
    def trigger_type(self):
        """Sets / Gets the trigger type.

        .. warning:: If a trigger source is currently set on the
            oscilloscope that is not implemented in this class,
            setting the source will fail. The oscilloscope is set up
            such that the the trigger type and source are set at the
            same time. However, for convenience, these two properties
            are split apart here.

        :return: Trigger type.
        :rtype: Member of `TriggerType` enum class.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.trigger_type = inst.TriggerType.edge  # trigger on edge
        """
        retval = self.query("TRIG_SELECT?").split(",")[0]
        return self.TriggerType(retval)

    @trigger_type.setter
    def trigger_type(self, newval):
        curr_trig_src = self.trigger_source
        cmd = f"TRIG_SELECT {newval.value},SR,{curr_trig_src.value}"
        self.sendcmd(cmd)

    # METHODS #

    def clear_sweeps(self):
        """Clears the sweeps in a measurement.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.clear_sweeps()
        """
        self.sendcmd("CLEAR_SWEEPS")

    def force_trigger(self):
        """Forces a trigger event to occur on the attached oscilloscope.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.force_trigger()
        """
        self.sendcmd("ARM")

    def run(self):
        """Enables the trigger for the oscilloscope and sets it to auto.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.run()
        """
        self.trigger_state = self.TriggerState.auto

    def stop(self):
        """Disables the trigger for the oscilloscope.

        Example:
            >>> import instruments as ik
            >>> import instruments.units as u
            >>> inst = ik.teledyne.MAUI.open_visa("TCPIP0::192.168.0.10::INSTR")
            >>> inst.stop()
        """
        self.sendcmd("STOP")


# STATICS #


def _source(src):
    """Stich the source together properly and return it."""
    if isinstance(src, int):
        return f"C{src + 1}"
    elif isinstance(src, tuple) and len(src) == 2:
        return f"{src[0].upper()}{int(src[1]) + 1}"
    else:
        raise ValueError(
            "An invalid source was specified. "
            "Source must be an integer or a tuple of "
            "length 2."
        )
