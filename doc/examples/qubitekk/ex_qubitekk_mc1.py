from sys import platform
from time import sleep
from serial.tools import list_ports
from instruments.qubitekk import MC1

HARDWARE_ID = [5824, 1155]#[1027, 24577]


def find_port():
    com_port = None
    found_port = False
    for port in list_ports.comports():
        try:
            vid = port.vid
            pid = port.pid
            serial_number = port.serial_number
            device = port.device
        except Exception as e:
            if port[2] == 'n/a':
                continue
            serial_number = port[2].split("=")[2]
            vid = int(port[2].split("=")[1].split(":")[0], 16)
            pid = int(port[2].split("=")[1].split(":")[1].split(" ")[0], 16)
            device = port[0]
        print(vid, pid, serial_number, device)
        if len(HARDWARE_ID) == 2:
            if vid == HARDWARE_ID[0] and pid == HARDWARE_ID[1]:
                found_port = True
                com_port = device
                break
        else:
            if serial_number == HARDWARE_ID[2]:
                found_port = True
                com_port = device
                break
    if not found_port:
        raise RuntimeError("device matching ids for motor controller not found")
    return com_port


def main():
    port = find_port()
    mc1 = MC1.open_serial(port, 9600, timeout=1)

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
    for x_pos in mc1.range:
        print(str(mc1.position)+" "+str(mc1.direction))
        mc1.move(x_pos)
        while mc1.move_timeout > 0:
            sleep(0.5)
        sleep(1)


if __name__ == "__main__":
    main()