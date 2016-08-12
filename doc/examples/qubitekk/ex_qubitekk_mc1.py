#!/usr/bin/python
# Qubitekk Motor controller example
from time import sleep

from instruments import Device
from instruments.qubitekk import MC1


if __name__ == "__main__":
    hardware = Device(vid=1027, pid=24577)
    mc1 = MC1.open_serial(hardware.port, baud=9600, timeout=1)
    print("Firmware", mc1.firmware)
    print("Motor controller type: ", mc1.controller)
    print("centering")

    mc1.center()
    while mc1.is_centering():
        print(str(mc1.position)+" "+str(mc1.direction))
        pass

    print("Stage Centered")
    # for the motor in the mechanical delay line, the travel is limited from
    # the full range of travel. Here's how to set the limits.
    mc1.lower_limit = -260
    mc1.upper_limit = 300
    mc1.increment = 5
    for x_pos in range(mc1.lower_limit, mc1.upper_limit, step=mc1.increment):
        print(str(mc1.position)+" "+str(mc1.direction))
        mc1.move(x_pos)
        while mc1.move_timeout > 0:
            sleep(0.5)
        sleep(1)
