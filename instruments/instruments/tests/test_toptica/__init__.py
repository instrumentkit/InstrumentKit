import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq
from nose.tools import raises
from flufl.enum import IntEnum
import quantities as pq

def test_convert_boolean():
    assert ik.toptica.convert_toptica_boolean("bloof") == False
    assert ik.toptica.convert_toptica_boolean("boot") == True

@raises(ValueError)
def test_convert_boolean_value():
    ik.toptica.convert_toptica_boolean("blo")


def test_serial_number():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:serial-number)", "(param-ref 'laser2:serial-number)"],
        ["bloop1>", "bloop2>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.serial_number == "bloop1"
        assert tm.laser2.serial_number == "bloop2"


def test_model():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:model)", "(param-ref 'laser2:model)"],
        ["bloop1>", "bloop2>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.model == "bloop1"
        assert tm.laser2.model == "bloop2"


def test_wavelength():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:wavelength)", "(param-ref 'laser2:wavelength)"],
        ["640>", "405.3>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.wavelength == 640*pq.nm
        assert tm.laser2.wavelength == 405.3*pq.nm


def test_laser_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:emission)", "(param-set! 'laser1:enable-emission #t)"],
        ["#f>", ">"],
        sep="\n"
    ) as tm:
        assert tm.laser1.enable == False
        tm.laser1.enable = True


def test_laser_ontime():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:ontime)"],
        ["10000>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.on_time == 10000*pq.s


def test_laser_charm_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.charm_status == 1


def test_laser_temperature_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.temperature_control_status == 1


def test_laser_current_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.current_control_status == 1