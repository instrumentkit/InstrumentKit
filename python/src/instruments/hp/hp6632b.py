#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# hp6632b.py: Python class for the HP6632b power supply
##
# © 2014 Willem Dijkstra (wpd@xs4all.nl).

from flufl.enum import Enum
import quantities as pq

from instruments.hp.hp6652a import HP6652a
from instruments.util_fns import unitful_property, unitless_property, bool_property, enum_property, int_property

class HP6632b(HP6652a):
    """
    The HP6632b is a system dc power supply with an output rating of 0-20V/0-5A,
    precision low current measurement and low output noise.

    According to the manual this class MIGHT be usable for any HP power supply
    with a model number HP663Xb where X in {1, 2, 3, 4}, HP661Xc with X in {1,
    2, 3, 4} and HP663X2A with X in {1, 3}.

    HOWEVER, it has only been tested by the author with a HP6632b power supply.

    Example usage:
    >>> import instruments as ik
    >>> psu = ik.hp.HP6632b.open_gpibusb('/dev/ttyUSB0', 6)
    >>> psu.voltage = 10 # Sets voltage to 10V.

    """

    def __init__(self, filelike):
        super(HP6632b, self).__init__(filelike)

    class DigitalFunction(Enum):
        remote_inhibit = 'RIDF'
        data = 'DIG'

    class DFISource(Enum):
        questionable = 'QUES'
        operation = 'OPER'
        event_status_bit = 'ESB'
        request_service_bit = 'RQS'
        off = 'OFF'

    class RemoteInhibit(Enum):
        latching = 'LATC'
        live = 'LIVE'
        off = 'OFF'

    class SenseWindow(Enum):
        hanning = 'HANN'
        rectangular = 'RECT'

    current_sense_range = unitful_property(
        'SENS:CURR:RANGE',
        pq.ampere,
        doc="""
        Get/set the sense current range by the current max value.

        A current of 20mA or less selects the low-current range, a current
        value higher than that selects the high-current range. The low current
        range increases the low current measurement sensitivity and accuracy.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """)

    output_dfi = bool_property(
        'OUTP:DFI',
        '1',
        '0',
        doc="""
        Get/set the discrete fault indicator (DFI) output from the dc
        source. The DFI is an open-collector logic signal connected to the read
        panel FLT connection, that can be used to signal external devices when
        a fault is detected.
        """)

    output_dfi_source = enum_property(
        "OUTP:DFI:SOUR",
        DFISource,
        doc="""
        Get/set the source for discrete fault indicator (DFI) events.
        """)

    output_remote_inhibit = enum_property(
        "OUTP:RI:MODE",
        RemoteInhibit,
        doc="""
        Get/set the remote inhibit signal. Remote inhibit is an external,
        chassis-referenced logic signal routed through the rear panel INH
        connection, which allows an external device to signal a fault.
        """)

    digital_function = enum_property(
        "DIG:FUNC",
        DigitalFunction,
        doc="""
        Get/set the inhibit+fault port to digital in+out or vice-versa.
        """)

    digital_data = int_property(
        "DIG:DATA",
        doc="""
        Get/set digital in+out port to data. Data can be an integer from 0-7.
        """,
        valid_set = range(0,8))

    sense_sweep_points = unitless_property(
        "SENS:SWE:POIN",
        doc="""
        Get/set the number of points in a measurement sweep.
        """)

    sense_sweep_interval = unitful_property(
        "SENS:SWE:TINT",
        pq.s,
        doc="""
        Get/set the digitizer sample spacing. Can be set from 15.6 us to 31200
        seconds, the interval will be rounded to the nearest 15.6 us increment.
        """)

    sense_window = enum_property(
        "SENS:WIND",
        SenseWindow,
        doc="""
        Get/set the measurement window function.
        """)

    output_protection_delay = unitful_property(
        "OUTP:PROT:DEL",
        pq.s,
        doc="""
        Get/set the time between programming of an output change that produces
        a constant current condition and the recording of that condigition in
        the Operation Status Condition register. This command also delays over
        current protection, but not overvoltage protection.
        """)
