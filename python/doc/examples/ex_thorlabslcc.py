#Thorlabs Liquid Crystal Controller example

import instruments as ik
lcc = ik.thorlabs.LCC25.open_serial('/dev/ttyUSB0', 115200,timeout=1)

print("The current frequency is: ",lcc.frequency)
print("The current voltage is: ",lcc.voltage1)
