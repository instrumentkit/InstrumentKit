#Thorlabs Liquid Crystal Controller example

import instruments as ik
lcc = ik.thorlabs.LCC25.open_serial('COM10', 115200,timeout=1)
#put model in voltage1 setting:
lcc.mode = int(ik.thorlabs.LCC25mode.voltage2)
#another way to do this is:
lcc.mode = 2
print("The current frequency is: ",lcc.frequency)
print("The current voltage is: ",lcc.voltage1)
