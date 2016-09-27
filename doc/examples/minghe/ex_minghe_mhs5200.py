#!/usr/bin/python
from time import sleep

from instruments.minghe import MHS5200
import quantities as pq

mhs = MHS5200.open_serial(vid=6790, pid=29987, baud=57600)
print(mhs.serial_number)
mhs.channel[0].frequency = 3000000*pq.Hz
print(mhs.channel[0].frequency)
mhs.channel[0].wave_type = MHS5200.WaveType.sawtooth_down
print(mhs.channel[0].wave_type)
mhs.channel[0].amplitude = 9.0*pq.V
print(mhs.channel[0].amplitude)
mhs.channel[0].offset = -0.5
print(mhs.channel[0].offset)
mhs.channel[0].phase = 90
print(mhs.channel[0].phase)
mhs.channel[0].duty_cycle = 0.1
print(mhs.channel[0].duty_cycle)

mhs.channel[1].wave_type = MHS5200.WaveType.sawtooth_up
