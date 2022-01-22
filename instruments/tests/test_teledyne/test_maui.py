#!/usr/bin/env python
"""
Module containing tests for the Thorlabs TC200
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import (
    expected_protocol,
    iterable_eq,
)
from instruments.units import ureg as u

# TESTS ######################################################################


# pylint: disable=too-many-lines,redefined-outer-name,protected-access


# PYTEST FIXTURES FOR INITIALIZATION #


@pytest.fixture
def init():
    """Returns the initialization command that is sent to MAUI Scope."""
    return "COMM_HEADER OFF"


# TEST ENUM GENERATION #


def test_create_trigger_source_enum(init):
    """Generate trigger source enum when number of channels changes."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        osc.number_channels = 42

        # existence of new channels, but not more
        assert "c41" in osc.TriggerSource.__members__
        assert "c42" not in osc.TriggerSource.__members__

        # proper name generation
        assert osc.TriggerSource["c41"].value == "C42"


# TEST DATA SOURCE CLASS #


def test_maui_data_source_name(init):
    """Return the name of the channel in the data source."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        assert osc.math[0].name == "F1"
        assert osc.channel[1].name == "C2"


def test_maui_data_source_read_waveform(init):
    """Return a numpy array of a waveform."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "TRMD?",
            "TRMD SINGLE",
            "C1:INSPECT? 'SIMPLE'",
            "C1:INSPECT? 'HORIZ_OFFSET'",
            "C1:INSPECT? 'HORIZ_INTERVAL'",
            "TRMD AUTO",
        ],
        [
            "AUTO",
            '"  1.   2.   3.   4.  "',
            "HORIZ_OFFSET       : 0.   ",
            "HORIZ_INTERVAL     : 2.5        ",
        ],
        sep="\n",
    ) as osc:
        if numpy:
            expected_wf = numpy.array([[0.0, 2.5, 5.0, 7.5], [1.0, 2.0, 3.0, 4.0]])
        else:
            expected_wf = ((0.0, 2.5, 5.0, 7.5), (1.0, 2.0, 3.0, 4.0))
        actual_wf = osc.channel[0].read_waveform()
        iterable_eq(actual_wf, expected_wf)


def test_maui_data_source_read_waveform_different_length(init):
    """BF: Stacking return arrays with different length.

    Depending on rounding issues, time and data arrays can have
    different lengths. Shorten to the shorter one by cutting the longer
    one from the end.
    """
    faulty_dataset_str = []
    faulty_dataset_int = []
    for it in range(402):  # 402 datapoints will make the error
        faulty_dataset_str.append(str(it))
        faulty_dataset_int.append(it)
    return_data_string = '"   ' + "   ".join(faulty_dataset_str) + '   "'

    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "TRMD?",
            "TRMD SINGLE",
            "C1:INSPECT? 'SIMPLE'",
            "C1:INSPECT? 'HORIZ_OFFSET'",
            "C1:INSPECT? 'HORIZ_INTERVAL'",
            "TRMD AUTO",
        ],
        [
            "AUTO",
            return_data_string,
            "HORIZ_OFFSET       : 9.8895e-06   ",
            "HORIZ_INTERVAL     : 5e-10        ",
        ],
        sep="\n",
    ) as osc:
        h_offset = 9.8895e-06
        h_interval = 5e-10

        if numpy:
            # create the signal that we want to get returned
            signal = numpy.array(faulty_dataset_int)
            timebase = numpy.arange(
                h_offset, h_offset + h_interval * (len(signal)), h_interval
            )

            # now cut timebase to the length of the signal
            timebase = timebase[0 : len(signal)]
            # create return dataset
            dataset_return = numpy.stack((timebase, signal))
        else:
            signal = tuple(faulty_dataset_int)
            timebase = tuple(
                float(val) * h_interval + h_offset for val in range(len(signal))
            )
            timebase = timebase[0 : len(signal)]
            dataset_return = timebase, signal

        actual_wf = osc.channel[0].read_waveform()
        iterable_eq(actual_wf, dataset_return)


def test_maui_data_source_read_waveform_math(init):
    """Return a numpy array of a waveform for multiple sweeps."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "C1:INSPECT? 'SIMPLE'",
            "C1:INSPECT? 'HORIZ_OFFSET'",
            "C1:INSPECT? 'HORIZ_INTERVAL'",
        ],
        [
            '"  1.   2.   3.   4.  "',
            "HORIZ_OFFSET       : 0.   ",
            "HORIZ_INTERVAL     : 2.5        ",
        ],
        sep="\n",
    ) as osc:
        if numpy:
            expected_wf = numpy.array([[0.0, 2.5, 5.0, 7.5], [1.0, 2.0, 3.0, 4.0]])
        else:
            expected_wf = ((0.0, 2.5, 5.0, 7.5), (1.0, 2.0, 3.0, 4.0))
        actual_wf = osc.channel[0].read_waveform(single=False)
        iterable_eq(actual_wf, expected_wf)


def test_maui_data_source_read_waveform_bin_format(init):
    """Raise a not implemented error."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        with pytest.raises(NotImplementedError):
            osc.channel[0].read_waveform(bin_format=True)


def test_maui_data_source_trace(init):
    """Get / Set the on/off status of a trace."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:TRA?", "C1:TRA ON", "C3:TRA OFF"], ["ON"], sep="\n"
    ) as osc:
        assert osc.math[0].trace
        osc.channel[0].trace = True
        osc.channel[2].trace = False


# TEST CHANNEL CLASS #


def test_maui_channel_init(init):
    """Initialize a MAUI Channel."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        assert osc.channel[0]._idx == 1
        assert isinstance(osc.channel[0]._parent, ik.teledyne.MAUI)


def test_maui_channel_coupling(init):
    """Get / Set MAUI Channel coupling."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "C3:CPL?", "C3:CPL A1M"], ["D50"], sep="\n"
    ) as osc:
        assert osc.channel[2].coupling == osc.channel[2].Coupling.dc50
        osc.channel[2].coupling = osc.channel[2].Coupling.ac1M


def test_maui_channel_offset(init):
    """Get / Set MAUI Channel offset."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "C1:OFST?", "C1:OFST 0.2", "C3:OFST 2"],
        ["1"],
        sep="\n",
    ) as osc:
        assert osc.channel[0].offset == u.Quantity(1, u.V)
        osc.channel[0].offset = u.Quantity(200, u.mV)
        osc.channel[2].offset = 2


def test_maui_channel_scale(init):
    """Get / Set MAUI Channel scale."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "C2:VDIV?", "C1:VDIV 2.0", "C2:VDIV 0.4"],
        ["1"],
        sep="\n",
    ) as osc:
        assert osc.channel[1].scale == u.Quantity(1, u.V)
        osc.channel[0].scale = u.Quantity(2000, u.mV)
        osc.channel[1].scale = 0.4


# TEST MATH CLASS #


def test_maui_math_init(init):
    """Initialize math channel."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        assert osc.math[0]._idx == 1
        assert isinstance(osc.math[0]._parent, ik.teledyne.MAUI)


def test_maui_math_clear_sweeps(init):
    """Clears math channel sweeps."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "CLEAR_SWEEPS"], [], sep="\n"
    ) as osc:
        osc.math[0].clear_sweeps()


# TEST MATH CLASS OPERATORS #


def test_maui_math_op_current_settings(init):
    """Return the current settings as oscilloscope string."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "F1:DEF?"],
        ["bla bla bla"],  # answer unimportant
        sep="\n",
    ) as osc:
        assert osc.math[0].operator.current_setting == "bla bla bla"


def test_maui_math_op_absolute(init):
    """Set math channel, absolute operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'ABS(C1)'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.absolute(0)


def test_maui_math_op_average(init):
    """Set math channel, average operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'AVG(C1)',AVERAGETYPE,SUMMED,SWEEPS,1000",
            "F1:DEFINE EQN,'AVG(C2)',AVERAGETYPE,CONTINUOUS,SWEEPS,100",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.average(0)
        osc.math[0].operator.average(1, average_type="continuous", sweeps=100)


def test_maui_math_op_derivative(init):
    """Set math channel, derivative operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'DERI(C1)',VERSCALE,1000000.0,"
            "VEROFFSET,0,ENABLEAUTOSCALE,ON",
            "F1:DEFINE EQN,'DERI(C3)',VERSCALE,5.0,"
            "VEROFFSET,1.0,ENABLEAUTOSCALE,OFF",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.derivative(0)
        osc.math[0].operator.derivative(
            2,
            vscale=u.Quantity(5000, u.mV / u.s),
            voffset=u.Quantity(60, u.V / u.min),
            autoscale=False,
        )


def test_maui_math_op_difference(init):
    """Set math channel, difference operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'C1-C3',VERSCALEVARIABLE,FALSE",
            "F1:DEFINE EQN,'C1-C3',VERSCALEVARIABLE,TRUE",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.difference(0, 2)
        osc.math[0].operator.difference(0, 2, vscale_variable=True)


def test_maui_math_op_envelope(init):
    """Set math channel, envelope operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'EXTR(C1)',SWEEPS,1000,LIMITNUMSWEEPS,True",
            "F1:DEFINE EQN,'EXTR(F2)',SWEEPS,10,LIMITNUMSWEEPS,False",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.envelope(0)
        osc.math[0].operator.envelope(("f", 1), sweeps=10, limit_sweeps=False)


def test_maui_math_op_eres(init):
    """Set math channel, eres operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'ERES(C1)',BITS,0.5",
            "F1:DEFINE EQN,'ERES(C1)',BITS,3",
            "F1:DEFINE EQN,'ERES(C1)',BITS,0.5",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.eres(0)
        osc.math[0].operator.eres(0, 3)
        osc.math[0].operator.eres(0, 28)


def test_maui_math_op_fft(init):
    """Set math channel, fft operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'FFT(C1)',TYPE,powerspectrum,"
            "WINDOW,vonhann,SUPPRESSDC,ON",
            "F1:DEFINE EQN,'FFT(C1)',TYPE,real," "WINDOW,flattop,SUPPRESSDC,OFF",
            "F1:DEFINE EQN,'FFT(C1)',TYPE,powerspectrum,"
            "WINDOW,vonhann,SUPPRESSDC,ON",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.fft(0)
        osc.math[0].operator.fft(0, type="real", window="flattop", suppress_dc=False)
        osc.math[0].operator.fft(0, type="inv str", window="inv str", suppress_dc=1)


def test_maui_math_op_floor(init):
    """Set math channel, floor operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'FLOOR(C1)',SWEEPS,1000,LIMITNUMSWEEPS,True",
            "F1:DEFINE EQN,'FLOOR(C1)',SWEEPS,10,LIMITNUMSWEEPS,False",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.floor(0)
        osc.math[0].operator.floor(0, sweeps=10, limit_sweeps=False)


def test_maui_math_op_integral(init):
    """Set math channel, integral operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'INTG(C1),MULTIPLIER,1,ADDER,0,"
            "VERSCALE,0.001,VEROFFSET,0",
            "F1:DEFINE EQN,'INTG(C4),MULTIPLIER,10,ADDER,0.5,"
            "VERSCALE,1,VEROFFSET,0.001",
            "F1:DEFINE EQN,'INTG(C4),MULTIPLIER,10,ADDER,0.5,"
            "VERSCALE,1,VEROFFSET,0.001",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.integral(0)
        osc.math[0].operator.integral(
            3,
            multiplier=10,
            adder=0.5,
            vscale=u.Quantity(1, u.Wb),
            voffset=u.Quantity(0.001, u.Wb),
        )
        osc.math[0].operator.integral(
            3, multiplier=10, adder=0.5, vscale=1, voffset=0.001
        )


def test_maui_math_op_invert(init):
    """Set math channel, invert operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'-C1'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.invert(0)


def test_maui_math_op_product(init):
    """Set math channel, product operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'C1*C3'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.product(0, 2)


def test_maui_math_op_ratio(init):
    """Set math channel, ratio operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'C1/C3'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.ratio(0, 2)


def test_maui_math_op_reciprocal(init):
    """Set math channel, reciprocal operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'1/C3'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.reciprocal(2)


def test_maui_math_op_rescale(init):
    """Set math channel, rescale operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'RESC(C3)',MULTIPLIER,1,ADDER,0",
            "F1:DEFINE EQN,'RESC(C3)',MULTIPLIER,10.3,ADDER,1.3",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.rescale(2)
        osc.math[0].operator.rescale(2, multiplier=10.3, adder=1.3)


def test_maui_math_op_sinx(init):
    """Set math channel, sin(x)/x operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'SINX(C3)'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.sinx(2)


def test_maui_math_op_square(init):
    """Set math channel, square operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'SQR(C3)'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.square(2)


def test_maui_math_op_square_root(init):
    """Set math channel, square root operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'SQRT(C3)'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.square_root(2)


def test_maui_math_op_sum(init):
    """Set math channel, sum operator."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "F1:DEFINE EQN,'C3+C1'"], [], sep="\n"
    ) as osc:
        osc.math[0].operator.sum(2, 0)


def test_maui_math_op_trend(init):
    """Set math channel, trend operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'TREND(C1)',VERSCALE,1,CENTER,0," "AUTOFINDSCALE,ON",
            "F1:DEFINE EQN,'TREND(C2)',VERSCALE,2,CENTER,1," "AUTOFINDSCALE,OFF",
            "F1:DEFINE EQN,'TREND(C2)',VERSCALE,2,CENTER,1," "AUTOFINDSCALE,ON",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.trend(0)
        osc.math[0].operator.trend(
            1, vscale=u.Quantity(2, u.V), center=u.Quantity(1, u.V), autoscale=False
        )
        osc.math[0].operator.trend(1, vscale=2, center=1, autoscale=True)


def test_maui_math_op_roof(init):
    """Set math channel, roof operator."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [
            init,
            "F1:DEFINE EQN,'ROOF(C1)',SWEEPS,1000,LIMITNUMSWEEPS,True",
            "F1:DEFINE EQN,'ROOF(C1)',SWEEPS,10,LIMITNUMSWEEPS,False",
        ],
        [],
        sep="\n",
    ) as osc:
        osc.math[0].operator.roof(0)
        osc.math[0].operator.roof(0, sweeps=10, limit_sweeps=False)


# TEST MEASUREMENT CLASS #


def test_maui_measurement_init(init):
    """Initialize measurement class."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        assert osc.measurement[0]._idx == 1
        assert isinstance(osc.measurement[0]._parent, ik.teledyne.MAUI)


def test_maui_measurement_state(init):
    """Get / Set measurement state."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "PARM?", "PARM CUST,HISTICON"], ["CUST,OFF"], sep="\n"
    ) as osc:
        assert osc.measurement[0].measurement_state == osc.measurement[0].State.off
        osc.measurement[0].measurement_state = osc.measurement[0].State.histogram_icon


def test_maui_measurement_statistics_error(init):
    """Raise ValueError if statistics cannot be gathered."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "PAST? CUST, P1"],
        [
            "CUST,P1,NULL,C3,AVG,UNDEF,HIGH,UNDEF,LAST,UNDEF,LOW,UNDEF,"
            "SIGMA,UNDEF,SWEEPS,0"
        ],
        sep="\n",
    ) as osc:
        with pytest.raises(ValueError):
            print(osc.measurement[0].statistics)


def test_maui_measurement_statistics(init):
    """Get statistics for given measurement."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "PAST? CUST, P1"],
        ["CUST,P1,MEAN,C3,AVG,10,HIGH,20,LAST,30,LOW,40,SIGMA,50," "SWEEPS,42"],
        sep="\n",
    ) as osc:
        assert osc.measurement[0].statistics == (10.0, 40.0, 20.0, 50.0, 42.0)


def test_maui_measurement_delete(init):
    """Delete a given measurement."""
    with expected_protocol(ik.teledyne.MAUI, [init, "PADL 1"], [], sep="\n") as osc:
        osc.measurement[0].delete()


def test_maui_measurement_set_parameter(init):
    """Set a specific parameter."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "PACU 1,AMPL,C3"], [], sep="\n"
    ) as osc:
        osc.measurement[0].set_parameter(osc.MeasurementParameters.amplitude, 2)


def test_maui_measurement_set_invalid_parameter(init):
    """Set a specific parameter."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        with pytest.raises(AttributeError):
            osc.measurement[0].set_parameter("amplitude", 2)


# TEST CLASS PROPERTIES AND METHODS #


def test_maui_ref(init):
    """Reference class in oscillioscope is not implemented."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        with pytest.raises(NotImplementedError):
            assert osc.ref


def test_maui_number_channels(init):
    """Set / Get number of channels."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        osc.number_channels = 42
        assert osc.number_channels == 42


def test_maui_number_functions(init):
    """Set / Get number of functions."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        osc.number_functions = 42
        assert osc.number_functions == 42


def test_maui_number_measurements(init):
    """Set / Get number of measurements."""
    with expected_protocol(ik.teledyne.MAUI, [init], [], sep="\n") as osc:
        osc.number_measurements = 42
        assert osc.number_measurements == 42


def test_maui_self_test(init):
    """Runs an oscilloscope self test."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "*TST?"], ["*TST 0"], sep="\n"
    ) as osc:
        assert osc.self_test == "*TST 0"  # Status: OK


def test_maui_show_id(init):
    """Displays oscilloscope ID."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "*IDN?"],
        ["*IDN LECROY,WAVEMASTER,WM01000,3.3.0"],
        sep="\n",
    ) as osc:
        assert osc.show_id == "*IDN LECROY,WAVEMASTER,WM01000,3.3.0"


def test_maui_show_options(init):
    """Displays oscilloscope options."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "*OPT?"], ["*OPT 0"], sep="\n"
    ) as osc:
        assert osc.show_options == "*OPT 0"  # no options installed


def test_maui_time_div(init):
    """Get / Set time per division."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "TDIV?", "TDIV 0.001"], ["1"], sep="\n"
    ) as osc:
        assert osc.time_div == u.Quantity(1, u.s)
        osc.time_div = u.Quantity(1, u.ms)


def test_maui_trigger_state(init):
    """Get / Set trigger state."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "TRMD?", "TRMD SINGLE"], ["AUTO"], sep="\n"
    ) as osc:
        assert osc.trigger_state == osc.TriggerState.auto
        osc.trigger_state = osc.TriggerState.single


def test_maui_trigger_delay(init):
    """Get / Set trigger delay."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "TRDL?", "TRDL 0.001", "TRDL 1"], ["0.001"], sep="\n"
    ) as osc:
        assert osc.trigger_delay == u.Quantity(1, u.ms)
        osc.trigger_delay = u.Quantity(1, u.ms)
        osc.trigger_delay = 1


def test_maui_trigger_source(init):
    """Get / Set trigger source."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "TRIG_SELECT?", "TRIG_SELECT?", "TRIG_SELECT EDGE,SR,EX"],
        ["EDGE,SR,C1,HT,OFF", "EDGE,SR,C1,HT,OFF"],
        sep="\n",
    ) as osc:
        assert osc.trigger_source == osc.TriggerSource.c0
        osc.trigger_source = osc.TriggerSource.ext


def test_maui_trigger_type(init):
    """Get / Set trigger type."""
    with expected_protocol(
        ik.teledyne.MAUI,
        [init, "TRIG_SELECT?", "TRIG_SELECT?", "TRIG_SELECT EDGE,SR,C3"],
        ["RUNT,SR,C3,HT,OFF", "EDGE,SR,C3,HT,OFF"],
        sep="\n",
    ) as osc:
        assert osc.trigger_type == osc.TriggerType.runt
        osc.trigger_type = osc.TriggerType.edge


def test_maui_clear_sweeps(init):
    """Clear the sweeps."""
    with expected_protocol(
        ik.teledyne.MAUI, [init, "CLEAR_SWEEPS"], [], sep="\n"
    ) as osc:
        osc.clear_sweeps()


def test_maui_force_trigger(init):
    """Force a trigger."""
    with expected_protocol(ik.teledyne.MAUI, [init, "ARM"], [], sep="\n") as osc:
        osc.force_trigger()


def test_maui_run(init):
    """Run the measurement in automatic trigger state."""
    with expected_protocol(ik.teledyne.MAUI, [init, "TRMD AUTO"], [], sep="\n") as osc:
        osc.run()


def test_maui_stop(init):
    """Stop the acquisition."""
    with expected_protocol(ik.teledyne.MAUI, [init, "STOP"], [], sep="\n") as osc:
        osc.stop()


# STATIC FUNCTIONS #


def test_source_stichting_integer():
    """Source stiching when an integer is given."""
    assert ik.teledyne.maui._source(3) == "C4"


def test_source_stiching_tuple():
    """Source stiching when a tuple is given."""
    assert ik.teledyne.maui._source(("p", 0)) == "P1"
    assert ik.teledyne.maui._source(("P", 0)) == "P1"


def test_source_stiching_value_error():
    """Raise a value error if anything else."""
    with pytest.raises(ValueError):
        ik.teledyne.maui._source(3.14)
