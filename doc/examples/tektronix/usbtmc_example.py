'''
from usbtmc import Instrument
instr = Instrument(0x0699, 0x0365)
print(instr.ask("*IDN?"))
'''
from instruments.tektronix import TekTDS224
tek = TekTDS224.open_usbtmc(idVendor=0x0699, idProduct=0x0365)
print(tek.query("*IDN?"))
