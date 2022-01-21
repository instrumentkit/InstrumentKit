#!/usr/bin/python
from instruments.minghe import MHS5200
import instruments.units as u

mhs = MHS5200.open_serial(vid=6790, pid=29987, baud=57600)
print(mhs.serial_number)
mhs.channel[0].frequency = 3000000 * u.Hz
print(mhs.channel[0].frequency)
mhs.channel[0].function = MHS5200.Function.sawtooth_down
print(mhs.channel[0].function)
mhs.channel[0].amplitude = 9.0 * u.V
print(mhs.channel[0].amplitude)
mhs.channel[0].offset = -0.5
print(mhs.channel[0].offset)
mhs.channel[0].phase = 90
print(mhs.channel[0].phase)

mhs.channel[1].frequency = 2000000 * u.Hz
print(mhs.channel[1].frequency)
mhs.channel[1].function = MHS5200.Function.square
print(mhs.channel[1].function)
mhs.channel[1].amplitude = 2.0 * u.V
print(mhs.channel[1].amplitude)
mhs.channel[1].offset = 0.0
print(mhs.channel[1].offset)
mhs.channel[1].phase = 15
print(mhs.channel[1].phase)
