#!/usr/bin/python
# Qubitekk Coincidence Counter example

from sys import platform as _platform

import instruments as ik
import instruments.units as u


if __name__ == "__main__":
    # open connection to coincidence counter. If you are using Windows, this will be a com port. On linux, it will show
    # up in /dev/ttyusb
    if _platform == "linux" or _platform == "linux2":
        cc = ik.qubitekk.CC1.open_serial("/dev/ttyUSB0", 19200, timeout=1)
    else:
        cc = ik.qubitekk.CC1.open_serial("COM8", 19200, timeout=1)

    print("Initializing Coincidence Counter")
    cc.dwell_time = 1.0 * u.s
    cc.delay = 0.0 * u.ns
    cc.window = 3.0 * u.ns
    cc.trigger = cc.TriggerMode.start_stop
    print(f"ch1 counts: {str(cc.channel[0].count)}")
    print(f"ch2 counts: {str(cc.channel[1].count)}")
    print(f"counts counts: {str(cc.channel[2].count)}")

    print("Finished Initializing Coincidence Counter")
