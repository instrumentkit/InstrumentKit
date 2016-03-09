#!/usr/bin/python
from sys import platform as _platform

import instruments as ik
from quantities import second, nanosecond
import time

def main():
    if _platform == "linux" or _platform == "linux2":
        cc1 = ik.qubitekk.CC1.open_serial('/dev/ttyUSB0', 19200, timeout=1)
    else:
        cc1 = ik.qubitekk.CC1.open_serial('COM8', 19200, timeout=1)
    print cc1.firmware
    cc1.dwell_time = 1.0 * second
    print cc1.dwell_time
    cc1.delay = 0.0 * nanosecond
    print cc1.delay
    cc1.window = 3.0 * nanosecond
    print cc1.window
    cc1.trigger = cc1.TriggerMode.start_stop
    print cc1.trigger
    print "Fetching Counts"
    counts_fetched = False
    while not counts_fetched:
        try:
            print cc1.channel[0].count
            print cc1.channel[1].count
            print cc1.channel[2].count
            counts_fetched = True
        except AttributeError as error_msg:
            print "Encountered issue: " + str(error_msg) + ". Waiting."
            print str(cc1)
            # self.initialize_coin_counter()
            time.sleep(cc1.dwell_time)
            counts_fetched = False
    print "Fetched Counts"

if __name__ == "__main__":
    while True:
        main()
