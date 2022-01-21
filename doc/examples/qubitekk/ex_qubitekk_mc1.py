#!/usr/bin/python
# Qubitekk Motor controller example
from time import sleep

from instruments.qubitekk import MC1
import instruments.units as u


if __name__ == "__main__":

    mc1 = MC1.open_serial(vid=1027, pid=24577, baud=9600, timeout=1)
    mc1.step_size = 25 * u.ms
    mc1.inertia = 10 * u.ms
    print("step size:", mc1.step_size)
    print("inertial force: ", mc1.inertia)

    print("Firmware", mc1.firmware)
    print("Motor controller type: ", mc1.controller)
    print("centering")

    mc1.center()
    while mc1.is_centering():
        print(str(mc1.metric_position) + " " + str(mc1.direction))
        pass

    print("Stage Centered")
    # for the motor in the mechanical delay line, the travel is limited from
    # the full range of travel. Here's how to set the limits.
    mc1.lower_limit = -260 * u.ms
    mc1.upper_limit = 300 * u.ms
    mc1.increment = 5 * u.ms
    x_pos = mc1.lower_limit
    while x_pos <= mc1.upper_limit:
        print(str(mc1.metric_position) + " " + str(mc1.direction))
        mc1.move(x_pos)
        while mc1.move_timeout > 0:
            sleep(0.5)
        sleep(1)
        x_pos += mc1.increment
