#Thorlabs Temperature Controller example

import instruments as ik
tc = ik.thorlabs.TC200.open_serial('/dev/tc200', 115200)

print("The current mode is: ", tc.mode)
print("The current enabled state is: ", tc.enable)
print("The current p gain is: ", tc.p)
print("The current i gain is: ", tc.i)
print("The current d gain is: ", tc.d)
print("The current degrees settings is: ", tc.degrees)
print("The current sensor setting is: ", tc.sensor)
print("The current beta settings is: ", tc.beta)
print("The current temperature is: ", tc.temperature)
print("The current max temperature setting is: ", tc.max_temperature)
print("The current max power setting is: ", tc.max_power)


