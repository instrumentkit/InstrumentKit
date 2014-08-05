#Thorlabs Shutter Controller example

import instruments as ik
sc = ik.thorlabs.SC10.open_serial('COM9', 9600,timeout=1)

print("The shutter open time is: ",sc.opentime)
print("The shutter closed time is: ",sc.shuttime)
