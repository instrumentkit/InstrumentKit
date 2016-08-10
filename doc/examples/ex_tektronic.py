from instruments.tektronix import TekTDS224
tek = TekTDS224.open_usbtmc(idVendor=0x0699, idProduct=0x0365)
print(tek.query("*IDN?"))

for i in range(0, 3):
    print(i)
    print(tek.channel[i].frequency())
    print(tek.channel[i].positive_width())
    print(tek.channel[i].rise_time())