from distutils.core import setup

setup(
    name='InstrumentKit Communication Library',
    version='1.0beta1',
    url='https://github.com/Galvant/InstrumentKit/',
    author='Steven Casagrande and Chris Granade',
    author_email='scasagrande@galvant.ca',
    package_dir={'': 'src'},
    packages=[
        'instruments',
        'instruments.abstract_instruments',
        'instruments.agilent',
        'instruments.hp',
        'instruments.generic_scpi',
        'instruments.keithley',
        'instruments.lakeshore',
        'instruments.other',
        'instruments.rigol',
        'instruments.srs',
        'instruments.tektronix',  
        'instruments.thorlabs',
    ]
)
