#!/usr/bin/env python
"""
Module containing tests for the Qubitekk CC1
"""

# IMPORTS ####################################################################

from io import BytesIO
import pytest
from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol, unit_eq


# TESTS ######################################################################


def test_init_os_error(mocker):
    """Initialize with acknowledgements already turned off.

    This raises an OSError in the read which must pass without an issue.
    """
    stdout = BytesIO(b":ACKN OF\nFIRM?\n")
    stdin = BytesIO(b"Firmware v2.010\n")
    mock_read = mocker.patch.object(ik.qubitekk.CC1, "read")
    mock_read.side_effect = OSError
    _ = ik.qubitekk.CC1.open_test(stdin, stdout)
    mock_read.assert_called_with(-1)


def test_cc1_count():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "COUN:C1?"],
        ["", "Firmware v2.010", "20"],
        sep="\n",
    ) as cc:
        assert cc.channel[0].count == 20.0


def test_cc1_count_valule_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "COUN:C1?"],
        ["", "Firmware v2.010", "bad_count", "try1" "try2" "try3" "try4" "try5"],
        sep="\n",
    ) as cc:
        with pytest.raises(IOError) as err_info:
            _ = cc.channel[0].count
        err_msg = err_info.value.args[0]
        assert err_msg == "Could not read the count of channel C1."


def test_cc1_window():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "WIND?", ":WIND 7"],
        [
            "",
            "Firmware v2.010",
            "2",
        ],
        sep="\n",
    ) as cc:
        unit_eq(cc.window, u.Quantity(2, "ns"))
        cc.window = 7


def test_cc1_window_error():
    with pytest.raises(ValueError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":WIND 10"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.window = 10


def test_cc1_delay():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "DELA?", ":DELA 2"],
        ["", "Firmware v2.010", "8", ""],
        sep="\n",
    ) as cc:
        unit_eq(cc.delay, u.Quantity(8, "ns"))
        cc.delay = 2


def test_cc1_delay_error1():
    with pytest.raises(ValueError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":DELA -1"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.delay = -1


def test_cc1_delay_error2():
    with pytest.raises(ValueError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":DELA 1"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.delay = 1


def test_cc1_dwell_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "DWEL?", ":DWEL 2"],
        ["Unknown Command", "Firmware v2.001", "8000", ""],
        sep="\n",
    ) as cc:
        unit_eq(cc.dwell_time, u.Quantity(8, "s"))
        cc.dwell_time = 2


def test_cc1_dwell_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "DWEL?", ":DWEL 2"],
        ["", "Firmware v2.010", "8"],
        sep="\n",
    ) as cc:
        unit_eq(cc.dwell_time, u.Quantity(8, "s"))
        cc.dwell_time = 2


def test_cc1_dwell_time_error():
    with pytest.raises(ValueError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":DWEL -1"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.dwell_time = -1


def test_cc1_firmware():
    with expected_protocol(
        ik.qubitekk.CC1, [":ACKN OF", "FIRM?"], ["", "Firmware v2.010"], sep="\n"
    ) as cc:
        assert cc.firmware == (2, 10, 0)


def test_cc1_firmware_2():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?"],
        ["Unknown Command", "Firmware v2"],
        sep="\n",
    ) as cc:
        assert cc.firmware == (2, 0, 0)


def test_cc1_firmware_3():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?"],
        ["Unknown Command", "Firmware v2.010.1"],
        sep="\n",
    ) as cc:
        assert cc.firmware == (2, 10, 1)


def test_cc1_firmware_repeat_query():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "FIRM?"],
        ["Unknown Command", "Unknown", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        assert cc.firmware == (2, 10, 0)


def test_cc1_gate_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "GATE?", ":GATE:ON", ":GATE:OFF"],
        ["", "Firmware v2.010", "ON"],
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False


def test_cc1_gate_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "GATE?", ":GATE 1", ":GATE 0"],
        ["Unknown Command", "Firmware v2.001", "1", "", ""],
        sep="\n",
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False


def test_cc1_gate_error():
    with pytest.raises(TypeError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":GATE blo"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.gate = "blo"


def test_cc1_subtract_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "SUBT?", ":SUBT:ON", ":SUBT:OFF"],
        ["", "Firmware v2.010", "ON", ":SUBT:OFF"],
        sep="\n",
    ) as cc:
        assert cc.subtract is True
        cc.subtract = True
        cc.subtract = False


def test_cc1_subtract_error():
    with pytest.raises(TypeError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":SUBT blo"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.subtract = "blo"


def test_cc1_trigger_mode():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "TRIG?", ":TRIG:MODE CONT", ":TRIG:MODE STOP"],
        ["", "Firmware v2.010", "MODE STOP"],
        sep="\n",
    ) as cc:
        assert cc.trigger_mode is cc.TriggerMode.start_stop
        cc.trigger_mode = cc.TriggerMode.continuous
        cc.trigger_mode = cc.TriggerMode.start_stop


def test_cc1_trigger_mode_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "TRIG?", ":TRIG 0", ":TRIG 1"],
        ["Unknown Command", "Firmware v2.001", "1", "", ""],
        sep="\n",
    ) as cc:
        assert cc.trigger_mode == cc.TriggerMode.start_stop
        cc.trigger_mode = cc.TriggerMode.continuous
        cc.trigger_mode = cc.TriggerMode.start_stop


def test_cc1_trigger_mode_error():
    with pytest.raises(ValueError), expected_protocol(
        ik.qubitekk.CC1, [":ACKN OF", "FIRM?"], ["", "Firmware v2.010"], sep="\n"
    ) as cc:
        cc.trigger_mode = "blo"


def test_cc1_clear():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", "CLEA"],
        ["", "Firmware v2.010"],
        sep="\n",
    ) as cc:
        cc.clear_counts()


def test_acknowledge():
    with expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?", ":ACKN ON", "CLEA", ":ACKN OF", "CLEA"],
        ["", "Firmware v2.010", "CLEA", ":ACKN OF"],
        sep="\n",
    ) as cc:
        assert not cc.acknowledge
        cc.acknowledge = True
        assert cc.acknowledge
        cc.clear_counts()
        cc.acknowledge = False
        assert not cc.acknowledge
        cc.clear_counts()


def test_acknowledge_notimplementederror():
    with pytest.raises(NotImplementedError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?"],
        ["Unknown Command", "Firmware v2.001"],
        sep="\n",
    ) as cc:
        cc.acknowledge = True


def test_acknowledge_not_implemented_error():  # pylint: disable=protected-access
    with pytest.raises(NotImplementedError), expected_protocol(
        ik.qubitekk.CC1,
        [":ACKN OF", "FIRM?"],
        ["Unknown Command", "Firmware v2.001"],
        sep="\n",
    ) as cc:
        cc.acknowledge = True
