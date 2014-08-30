import instruments as ik
psu = ik.hp.HP6632b.open_gpibusb('/dev/ttyUSB0', 5)
print psu.name
psu.display_textmode=True
psu.display_text("HPIB TEST")
psu.voltage = 10
print psu.voltage
print psu.voltage_sense
print psu.overvoltage
print psu.current
print psu.current_sense
print psu.overcurrent
print psu.output
psu.output = True
print psu.voltage
print psu.voltage_sense
print psu.overvoltage
print psu.current
print psu.current_sense
print psu.overcurrent
print psu.output
psu.output = False
print psu.current_sense_range
print psu.output_dfi_source
psu.output_dfi_source = 'OPER'
print psu.output_dfi_source
print psu.output_remote_inhibit
print psu.digital_function
print psu.digital_data
print psu.sense_sweep_points
print psu.sense_sweep_interval
print psu.sense_window
print psu.output_protection_delay
