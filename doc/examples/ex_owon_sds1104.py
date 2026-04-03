#!/usr/bin/env python
"""
Minimal example for connecting to an OWON SDS1104-family oscilloscope.
"""

import instruments as ik
from instruments.units import ureg as u


def main():
    """
    Open the scope over raw USB, print a few stable values, and read the
    current CH1 screen waveform. The trigger example below only uses the
    conservative trigger paths promoted in the driver.
    """
    scope = ik.owon.OWONSDS1104.open_usb(
        enable_scpi=False,
        ignore_scpi_failure=True,
        settle_time=0.1,
    )
    try:
        print(f"Identity: {scope.name}")
        print(f"Timebase scale: {scope.timebase_scale}")
        print(f"CH1 displayed: {scope.channel[0].display}")
        print(f"CH1 coupling: {scope.channel[0].coupling}")
        print(f"Trigger type: {scope.trigger_type}")
        print(f"Single trigger mode: {scope.single_trigger_mode}")

        scope.stop()
        scope.single_trigger_mode = scope.SingleTriggerMode.edge
        scope.trigger_source = scope.TriggerSource.ch1
        scope.trigger_coupling = scope.TriggerCoupling.dc
        scope.trigger_slope = scope.TriggerSlope.rise
        scope.trigger_level = 25 * u.millivolt
        scope.trigger_holdoff = 100 * u.nanosecond
        print(f"Trigger snapshot: {scope.read_trigger_configuration()}")

        time_s, voltage_v = scope.channel[0].read_waveform()
        print(f"CH1 waveform samples: {len(voltage_v)}")
        print(f"First sample: t={time_s[0]!r}, v={voltage_v[0]!r}")
    finally:
        scope.close()


if __name__ == "__main__":
    main()
