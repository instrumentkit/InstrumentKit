from distutils.core import setup

setup(
    name='GPIB-USB Instrument Communication Library',
    version='1.0beta1',
    url='https://github.com/Galvant/gpibusb-comm_code/',
    author='Steven Casagrande and Chris Granade',
    author_email='scasagrande@galvant.ca',
    package_dir={'': 'src'},
    packages=[
        'instruments',
        'instruments.abstract_instruments',
        'instruments.agilent',
        'instruments.generic_scpi',
        'instruments.keithley',
        'instruments.lakeshore',
        'instruments.other',
        'instruments.srs',
        'instruments.tektronix',  
        'instruments.thorlabs',
    ]
)
