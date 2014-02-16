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
        'instruments.generic_scpi',
        'instruments.holzworth',
        'instruments.hp',
        'instruments.keithley',
        'instruments.lakeshore',
        'instruments.newport',
        'instruments.other',
        'instruments.oxford',
        'instruments.phasematrix',
        'instruments.picowatt',
        'instruments.rigol',
        'instruments.srs',
        'instruments.tektronix',  
        'instruments.thorlabs',
        'instruments.yokogawa',
    ]
)
