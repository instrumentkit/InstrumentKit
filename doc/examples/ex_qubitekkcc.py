#!/usr/bin/python
from sys import platform as _platform

import instruments as ik
from quantities import second, nanosecond


def main():
    cc = ik.qubitekk.CC1.open_serial(vid=1027, pid=24577, baud=19200,
                                     timeout=10)
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
