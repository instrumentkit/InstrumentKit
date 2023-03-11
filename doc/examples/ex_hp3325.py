import logging

import instruments as ik

fcngen = ik.hp.HP3325a.open_gpibusb("COM4", 17, model="pl")
logging.basicConfig(level=logging.DEBUG)
fcngen._file.debug = True

fcngen.amplitude = 2.0  # V
fcngen.frequency = 512.53  # Hz
fcngen.function = fcngen.Function.square

print(f"Actual voltage={fcngen.amplitude} V")
print(f"Actual frequency={fcngen.frequency} Hz")