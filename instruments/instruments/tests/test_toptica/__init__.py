import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq
from nose.tools import raises
from flufl.enum import IntEnum
import quantities as pq
import datetime


def test_convert_boolean():
    assert ik.toptica.convert_toptica_boolean("bloof") == False
    assert ik.toptica.convert_toptica_boolean("boot") == True
    assert ik.toptica.convert_toptica_boolean("Error: -3") == None

@raises(ValueError)
def test_convert_boolean_value():
    ik.toptica.convert_toptica_boolean("blo")

def test_convert_toptica_datetime():
    blo = datetime.datetime.now()
    blo_str = datetime.datetime.now().strftime("%b %d %Y %I:%M%p")
    assert ik.toptica.convert_toptica_datetime('""\r') == None
    blo2 = ik.toptica.convert_toptica_datetime(blo_str)
    diff = blo - blo2
    assert diff.seconds < 60


def test_serial_number():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:serial-number)", "(param-ref 'laser2:serial-number)"],
        ["(param-ref 'laser1:serial-number)\nbloop1>", "(param-ref 'laser2:serial-number)\nbloop2>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.serial_number == "bloop1"
        assert tm.laser2.serial_number == "bloop2"


def test_model():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:model)", "(param-ref 'laser2:model)"],
        ["(param-ref 'laser1:model)\nbloop1>", "(param-ref 'laser2:model)\nbloop2>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.model == "bloop1"
        assert tm.laser2.model == "bloop2"


def test_wavelength():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:wavelength)", "(param-ref 'laser2:wavelength)"],
        ["(param-ref 'laser1:wavelength)\n640>", "(param-ref 'laser2:wavelength)\n405.3>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.wavelength == 640*pq.nm
        assert tm.laser2.wavelength == 405.3*pq.nm


def test_laser_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:emission)", "(param-set! 'laser1:enable-emission #t)"],
        ["(param-ref 'laser1:emission)\n#f>", "(param-set! 'laser1:enable-emission #t)\n>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.enable == False
        tm.laser1.enable = True


@raises(TypeError)
def test_laser_enable_error():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-set! 'laser1:enable-emission #t)"],
        ["(param-set! 'laser1:enable-emission #t)\n>"],
        sep="\n"
    ) as tm:
        tm.laser1.enable = 'True'


def test_laser_tec_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:tec:ready)"],
        ["(param-ref 'laser1:tec:ready)\n#f>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.tec_status == False


def test_laser_intensity():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:intensity)"],
        ["(param-ref 'laser1:intensity)\n0.666>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.intensity == 0.666


def test_laser_mode_hop():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:reg:mh-occured)"],
        ['(param-ref \'laser1:charm:reg:mh-occured)\n#f>'],
        sep="\n"
    ) as tm:
        assert tm.laser1.mode_hop == False


def test_laser_lock_start():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:reg:started)"],
        ['(param-ref \'laser1:charm:reg:started)\n""\r>'],
        sep="\n"
    ) as tm:
        assert tm.laser1.lock_start is None


def test_laser_first_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:reg:first-mh)"],
        ['(param-ref \'laser1:charm:reg:first-mh)\n""\r>'],
        sep="\n"
    ) as tm:
        assert tm.laser1.first_mode_hop_time is None


def test_laser_latest_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:reg:latest-mh)"],
        ['(param-ref \'laser1:charm:reg:latest-mh)\n""\r>'],
        sep="\n"
    ) as tm:
        assert tm.laser1.latest_mode_hop_time is None


def test_laser_correction_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:correction-status)"],
        ['(param-ref \'laser1:charm:correction-status)\n0>'],
        sep="\n"
    ) as tm:
        assert tm.laser1.correction_status == ik.toptica.TopMode.CharmStatus.un_initialized


def test_laser_correction():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:charm:correction-status)", "(exec 'laser1:charm:start-correction-initial)",
         "(param-ref 'laser1:charm:correction-status)", "(exec 'laser1:charm:start-correction)"],
        ['(param-ref \'laser1:charm:correction-status)\n0>', "(exec 'laser1:charm:start-correction-initial)\n>",
         '(param-ref \'laser1:charm:correction-status)\n1>', "(exec 'laser1:charm:start-correction)\n>"],
        sep="\n"
    ) as tm:
        tm.laser1.correction()
        tm.laser1.correction()

def test_reboot_system():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(exec 'reboot-system)"],
        ['(exec \'reboot-system)\n>'],
        sep="\n"
    ) as tm:
        tm.reboot()


def test_laser_ontime():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:ontime)"],
        ["(param-ref 'laser1:ontime)\n10000>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.on_time == 10000*pq\
            .s


def test_laser_charm_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["(param-ref 'laser1:health)\n230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.charm_status == 1


def test_laser_temperature_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["(param-ref 'laser1:health)\n230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.temperature_control_status == 1


def test_laser_current_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:health)"],
        ["(param-ref 'laser1:health)\n230>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.current_control_status == 1


def test_laser_production_date():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'laser1:production-date)"],
        ["(param-ref 'laser1:production-date)\n2016-01-16>"],
        sep="\n"
    ) as tm:
        assert tm.laser1.production_date == '2016-01-16'


def test_set_str():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-set! \'blo \"blee\")"],
        ["(param-set! \'blo \"blee\")\n>"],
        sep="\n"
    ) as tm:
        tm.set('blo', 'blee')


def test_set_list():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-set! \'blo \'(blee blo))"],
        ["(param-set! \'blo \'(blee blo))\n>"],
        sep="\n"
    ) as tm:
        tm.set('blo', ['blee','blo'])


def test_display():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-disp \'blo)"],
        ["(param-disp \'blo)\n>bloop\n>"],
        sep="\n"
    ) as tm:
        assert tm.display('blo') == "bloop"


def test_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-set! \'enable-emission #f)"],
        ["(param-set! \'enable-emission #f)\n>"],
        sep="\n"
    ) as tm:
        tm.enable = False


@raises(TypeError)
def test_enable_error():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-set! \'enable-emission #f)"],
        ["(param-set! \'enable-emission #f)\n>"],
        sep="\n"
    ) as tm:
        tm.enable = "False"


def test_front_key():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'front-key-locked)"],
        ["(param-ref 'front-key-locked)\n#f>"],
        sep="\n"
    ) as tm:
        assert tm.locked == False


def test_interlock():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'interlock-open)"],
        ["(param-ref 'interlock-open)\n#f>"],
        sep="\n"
    ) as tm:
        assert tm.interlock == False


def test_fpga_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'system-health)"],
        ["(param-ref 'system-health)\n0>"],
        sep="\n"
    ) as tm:
        assert tm.fpga_status == True


def test_temperature_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'system-health)"],
        ["(param-ref 'system-health)\n2>"],
        sep="\n"
    ) as tm:
        assert tm.temperature_status == False



def test_current_status():
    with expected_protocol(
        ik.toptica.TopMode,
        ["(param-ref 'system-health)"],
        ["(param-ref 'system-health)\n4>"],
        sep="\n"
    ) as tm:
        assert tm.current_status == False