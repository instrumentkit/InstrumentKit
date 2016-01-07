# Import sys and add the path so we can check that the package imports
# correctly, and so that we can grab the version from the package.
import __main__, os, sys
sys.path.insert(0, os.path.join(
    # Try to get the name of this file. If we can't, go with the CWD.
    os.path.dirname(os.path.abspath(__main__.__file__))
    if hasattr(__main__, '__file__') else
    os.getcwd(), 
    'instruments'
))
import instruments as ik

# Now that we have ik loaded, go on and install it.
from distutils.core import setup

setup(
    name='InstrumentKit Communication Library',
    version=ik.__version__,
    url='https://github.com/Galvant/InstrumentKit/',
    author='Steven Casagrande',
    author_email='scasagrande@galvant.ca',
    package_dir={'': ''},
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
    install_requires = [
        "numpy",
        "pyserial",
        "quantities",
        "flufl.enum"
    ],
    extras_require = {
        'USBTMC' : ["python-usbtmc"],
        'VISA' : ["pyvisa"],
        'USB' : ["pyusb"]
    },
    description='Test and measurement communication library',
    long_description='''
        InstrumentKit
        -------------
        
        InstrumentKit is an open source Python library designed to help the
        end-user get straight into communicating with their equipment via a PC.
        InstrumentKit aims to accomplish this by providing a connection- and
        vendor-agnostic API. Users can freely swap between a variety of
        connection types (ethernet, gpib, serial, usb) without impacting their
        code. Since the API is consistent across similar instruments, a user
        can, for example, upgrade from their 1980's multimeter using GPIB to a
        modern Keysight 34461a using ethernet with only a single line change.
        
        This version requires Python 2.7; support for Python 3 is planned for a
        future release.
    ''',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development :: Libraries"
    ]
)
