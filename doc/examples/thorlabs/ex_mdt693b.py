"""
An example script for interacting with the thorlabs MDT693B piezo driver.
"""
import quantities as pq
from instruments.thorlabs import MDT693B


mdt = MDT693B.open_serial(vid=1027, pid=24577, baud=115200)

for i in range(0, 3):
    print("The voltage on ", i, " is ", mdt.channel[i].voltage)
    print("The minimum on ", i, " is ", mdt.channel[i].minimum)
    print("The maximum on ", i, " is ", mdt.channel[i].maximum)

mdt.master_scan_voltage = 1*pq.V
mdt.master_scan_enable = True