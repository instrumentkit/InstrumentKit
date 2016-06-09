import instruments as ik
import matplotlib.pyplot as plt

tek = ik.tektronix.TekTDS224.open_usbtmc(idVendor=0x0699, idProduct=0x0365)
tek.terminator = '\n'
x, y = tek.channel[0].read_waveform()
plt.scatter(x, y)
plt.xlim(min(x), max(x))
plt.ylim(min(y), max(y))
plt.show()
