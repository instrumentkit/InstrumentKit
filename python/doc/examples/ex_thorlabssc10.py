#Thorlabs Shutter Controller example

import instruments as ik
#if the baud mode is set to 1, then the baud rate is 115200
#otherwise, the baud rate is 9600
sc = ik.thorlabs.SC10.open_serial('COM9', 115200,timeout=1)


print("It is a: ", sc.identity)
print("Setting shutter open time to 10 ms")
sc.opentime = 10
print("The shutter open time is: ",sc.opentime)
print("Setting shutter open time to 50 ms")
sc.opentime = 50
print("The shutter open time is: ",sc.opentime)
print("Setting shutter close time to 10 ms")
sc.opentime = 10
print("The shutter close time is: ",sc.opentime)
print("Setting shutter close time to 50 ms")
sc.opentime = 50
print("The shutter close time is: ",sc.opentime)

print("Setting repeat count  to 4")
sc.repeat = 4
print("The repeat count is: ",sc.repeat)
print("Setting repeat count to 8")
sc.repeat = 8
print("The repeat count is: ",sc.repeat)

