#!/usr/bin/env python
"""
Provides support for the Tektronix AWG2000 series arbitrary wave generators.
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.generic_scpi import SCPIInstrument
from instruments.optional_dep_finder import numpy
from instruments.units import ureg as u
from instruments.util_fns import assume_units, ProxyList

# CLASSES #####################################################################


class TekAWG2000(SCPIInstrument):

    """
    Communicates with a Tektronix AWG2000 series instrument using the SCPI
    commands documented in the user's guide.
    """

    # INNER CLASSES #

    class Channel:

        """
        Class representing a physical channel on the Tektronix AWG 2000

        .. warning:: This class should NOT be manually created by the user. It
        is designed to be initialized by the `TekAWG2000` class.
        """

        def __init__(self, tek, idx):
            self._tek = tek
            # Zero-based for pythonic convienence, so we need to convert to
            # Tektronix's one-based notation here.
            self._name = f"CH{idx + 1}"

            # Remember what the old data source was for use as a context manager
            self._old_dsrc = None

        # PROPERTIES #

        @property
        def name(self):
            """
            Gets the name of this AWG channel

            :type: `str`
            """
            return self._name

        @property
        def amplitude(self):
            """
            Gets/sets the amplitude of the specified channel.

            :units: As specified (if a `~pint.Quantity`) or assumed to be
                of units Volts.
            :type: `~pint.Quantity` with units Volts peak-to-peak.
            """
            return u.Quantity(
                float(self._tek.query(f"FG:{self._name}:AMPL?").strip()), u.V
            )

        @amplitude.setter
        def amplitude(self, newval):
            self._tek.sendcmd(
                "FG:{}:AMPL {}".format(
                    self._name, assume_units(newval, u.V).to(u.V).magnitude
                )
            )

        @property
        def offset(self):
            """
            Gets/sets the offset of the specified channel.

            :units: As specified (if a `~pint.Quantity`) or assumed to be
                of units Volts.
            :type: `~pint.Quantity` with units Volts.
            """
            return u.Quantity(
                float(self._tek.query(f"FG:{self._name}:OFFS?").strip()), u.V
            )

        @offset.setter
        def offset(self, newval):
            self._tek.sendcmd(
                "FG:{}:OFFS {}".format(
                    self._name, assume_units(newval, u.V).to(u.V).magnitude
                )
            )

        @property
        def frequency(self):
            """
            Gets/sets the frequency of the specified channel when using the built-in
            function generator.

            ::units: As specified (if a `~pint.Quantity`) or assumed to be
                of units Hertz.
            :type: `~pint.Quantity` with units Hertz.
            """
            return u.Quantity(float(self._tek.query("FG:FREQ?").strip()), u.Hz)

        @frequency.setter
        def frequency(self, newval):
            self._tek.sendcmd(
                f"FG:FREQ {assume_units(newval, u.Hz).to(u.Hz).magnitude}HZ"
            )

        @property
        def polarity(self):
            """
            Gets/sets the polarity of the specified channel.

            :type: `TekAWG2000.Polarity`
            """
            return TekAWG2000.Polarity(self._tek.query(f"FG:{self._name}:POL?").strip())

        @polarity.setter
        def polarity(self, newval):
            if not isinstance(newval, TekAWG2000.Polarity):
                raise TypeError(
                    "Polarity settings must be a "
                    "`TekAWG2000.Polarity` value, got {} "
                    "instead.".format(type(newval))
                )

            self._tek.sendcmd(f"FG:{self._name}:POL {newval.value}")

        @property
        def shape(self):
            """
            Gets/sets the waveform shape of the specified channel. The AWG will
            use the internal function generator for these shapes.

            :type: `TekAWG2000.Shape`
            """
            return TekAWG2000.Shape(
                self._tek.query(f"FG:{self._name}:SHAP?").strip().split(",")[0]
            )

        @shape.setter
        def shape(self, newval):
            if not isinstance(newval, TekAWG2000.Shape):
                raise TypeError(
                    "Shape settings must be a `TekAWG2000.Shape` "
                    "value, got {} instead.".format(type(newval))
                )
            self._tek.sendcmd(f"FG:{self._name}:SHAP {newval.value}")

    # ENUMS #

    class Polarity(Enum):
        """
        Enum containing valid polarity modes for the AWG2000
        """

        normal = "NORMAL"
        inverted = "INVERTED"

    class Shape(Enum):
        """
        Enum containing valid waveform shape modes for hte AWG2000
        """

        sine = "SINUSOID"
        pulse = "PULSE"
        ramp = "RAMP"
        square = "SQUARE"
        triangle = "TRIANGLE"

    # Properties #

    @property
    def waveform_name(self):
        """
        Gets/sets the destination waveform name for upload.

        This is the file name that will be used on the AWG for any following
        waveform data that is uploaded.

        :type: `str`
        """
        return self.query("DATA:DEST?").strip()

    @waveform_name.setter
    def waveform_name(self, newval):
        if not isinstance(newval, str):
            raise TypeError("Waveform name must be specified as a string.")
        self.sendcmd(f'DATA:DEST "{newval}"')

    @property
    def channel(self):
        """
        Gets a specific channel on the AWG2000. The desired channel is accessed
        like one would access a list.

        Example usage:

        >>> import instruments as ik
        >>> inst = ik.tektronix.TekAWG2000.open_gpibusb("/dev/ttyUSB0", 1)
        >>> print(inst.channel[0].frequency)

        :return: A channel object for the AWG2000
        :rtype: `TekAWG2000.Channel`
        """
        return ProxyList(self, self.Channel, range(2))

    # METHODS #

    def upload_waveform(self, yzero, ymult, xincr, waveform):
        """
        Uploads a waveform from the PC to the instrument.

        :param yzero: Y-axis origin offset
        :type yzero: `float` or `int`

        :param ymult: Y-axis data point multiplier
        :type ymult: `float` or `int`

        :param xincr: X-axis data point increment
        :type xincr: `float` or `int`

        :param `numpy.ndarray` waveform: Numpy array of values representing the
            waveform to be uploaded. This array should be normalized. This means
            that all absolute values contained within the array should not
            exceed 1.
        """
        if numpy is None:
            raise ImportError(
                "Missing optional dependency numpy, which is required"
                "for uploading waveforms."
            )

        if not isinstance(yzero, float) and not isinstance(yzero, int):
            raise TypeError("yzero must be specified as a float or int")

        if not isinstance(ymult, float) and not isinstance(ymult, int):
            raise TypeError("ymult must be specified as a float or int")

        if not isinstance(xincr, float) and not isinstance(xincr, int):
            raise TypeError("xincr must be specified as a float or int")

        if not isinstance(waveform, numpy.ndarray):
            raise TypeError("waveform must be specified as a numpy array")

        if numpy.max(numpy.abs(waveform)) > 1:
            raise ValueError("The max value for an element in waveform is 1.")

        self.sendcmd(f"WFMP:YZERO {yzero}")
        self.sendcmd(f"WFMP:YMULT {ymult}")
        self.sendcmd(f"WFMP:XINCR {xincr}")

        waveform *= 2 ** 12 - 1
        waveform = waveform.astype("<u2").tobytes()
        wfm_header_2 = str(len(waveform))
        wfm_header_1 = len(wfm_header_2)

        bin_str = f"#{wfm_header_1}{wfm_header_2}{waveform}"

        self.sendcmd(f"CURVE {bin_str}")
