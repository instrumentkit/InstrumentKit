from time import sleep

from instruments.tektronix import TekTDS224
import matplotlib.pyplot as plt
import quantities as pq
tek = TekTDS224.open_usbtmc(idVendor=0x0699, idProduct=0x0365)
print(tek.query("*IDN?"))

tek.time_scale = 25*pq.ns
sleep(2)
print(tek.time_scale)
x1, y1 = tek.channel[0].read_waveform()
print(min(x1), max(x1))
tek.time_scale = 25*pq.us
print(tek.time_scale)
sleep(2)
x2, y2 = tek.channel[0].read_waveform()
print(min(x2), max(x2))
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(x1, y1, label="scale 25 ns")
ax.plot(x1, y2, label="scale 25 ms")
ax.legend()
plt.show()

for i in range(0, 3):
    print(i)
    print(tek.channel[i].frequency())
    print(tek.channel[i].positive_width())
    print(tek.channel[i].rise_time())