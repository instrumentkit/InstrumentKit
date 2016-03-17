#!/usr/bin/python
from sys import platform as _platform

import instruments as ik
from quantities import second, nanosecond


def main():
    if _platform == "linux" or _platform == "linux2":
        cc1 = ik.qubitekk.CC1v2001.open_serial('/dev/ttyUSB0', 19200, timeout=1)
    else:
        cc1 = ik.qubitekk.CC1v2001.open_serial('COM8', 19200, timeout=1)
    cc1.dwell_time = 1.0 * second
    print cc1.dwell_time
    cc1.delay = 0.0 * nanosecond
    print cc1.delay
    cc1.window = 3.0 * nanosecond
    print cc1.window
    cc1.trigger = ik.qubitekk.TriggerModeInt.start_stop
    print cc1.trigger
    print "Fetching Counts"
    print cc1.channel[0].count
    print cc1.channel[1].count
    print cc1.channel[2].count
    print "Fetched Counts"

if __name__ == "__main__":
    while True:
        main()
