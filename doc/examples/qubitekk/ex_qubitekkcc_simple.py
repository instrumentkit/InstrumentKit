#!/usr/bin/python
# Qubitekk Coincidence Counter example

from sys import platform as _platform

import instruments as ik
import quantities


if __name__ == "__main__":
    hardware = ik.Device(vid=1027, pid=24577)
    cc = ik.qubitekk.CC1.open_serial(hardware.port, baud=19200, timeout=1)

    print("Initializing Coincidence Counter")
    cc.dwell_time = 1.0*quantities.s
    cc.delay = 0.0*quantities.ns
    cc.window = 3.0*quantities.ns
    cc.trigger = cc.TriggerMode.start_stop
    print("ch1 counts: " + str(cc.channel[0].count))
    print("ch2 counts: " + str(cc.channel[1].count))
    print("counts counts: " + str(cc.channel[2].count))

    print("Finished Initializing Coincidence Counter")
