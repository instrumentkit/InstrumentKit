# Import sys and add the path so we can check that the package imports
# correctly, and so that we can grab the version from the package.
import __main__, os, sys
sys.path.insert(0, os.path.join(
    # Try to get the name of this file. If we can't, go with the CWD.
    os.path.dirname(os.path.abspath(__main__.__file__))
    if hasattr(__main__, '__file__') else
    os.getcwd(), 
    'src'
))
import instruments as ik

# Now that we have ik loaded, go on and install it.
from distutils.core import setup

setup(
    name='InstrumentKit Communication Library',
    version=ik.__version__,
    url='https://github.com/Galvant/InstrumentKit/',
    author='Steven Casagrande and Chris Granade',
    author_email='scasagrande@galvant.ca',
    package_dir={'': 'src'},
    packages=[
        'instruments',
        'instruments.abstract_instruments',
        'instruments.abstract_instruments.signal_generator',
        'instruments.abstract_instruments.comm',
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
        'instruments.qubitekk',
        'instruments.rigol',
        'instruments.srs',
        'instruments.tektronix',  
        'instruments.thorlabs',
        'instruments.yokogawa',
    ],
    extras_require = {
        'USBTMC' : ["python-usbtmc"],
        'VISA' : ["pyvisa"],
        'USB' : ["pyusb"]
    }
)
