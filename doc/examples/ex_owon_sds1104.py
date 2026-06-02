#!/usr/bin/env python
"""
Minimal example for connecting to an OWON SDS1104-family oscilloscope.
"""

import instruments as ik


def main():
    """
    Open the scope over raw USB, print a few stable values, and read the
    current CH1 screen waveform.
    """
    scope = ik.owon.OWONSDS1104.open_usb()

    print(f"Identity: {scope.name}")
    print(f"Timebase scale: {scope.timebase_scale}")
    print(f"CH1 displayed: {scope.channel[0].display}")
    print(f"CH1 coupling: {scope.channel[0].coupling}")
    time_s, voltage_v = scope.channel[0].read_waveform()
    print(f"CH1 waveform samples: {len(voltage_v)}")
    print(f"First sample: t={time_s[0]!r}, v={voltage_v[0]!r}")


if __name__ == "__main__":
    main()
