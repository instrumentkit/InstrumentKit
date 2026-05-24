#!/usr/bin/env python

import instruments as ik

psu = ik.kiprim.DC310S.open_serial("COM8", baud=115200, timeout=0.5)

print(psu.name)
print(f"Setpoint: {psu.voltage}, {psu.current}, output={psu.output}")
print(f"Measured: {psu.voltage_sense}, {psu.current_sense}, {psu.power_sense}")

# Uncomment to configure the supply explicitly.
# psu.voltage = 5 * ik.units.volt
# psu.current = 0.25 * ik.units.ampere
# psu.output = True
