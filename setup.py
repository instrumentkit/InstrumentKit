#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python setup.py file for the InstrumentKit project
"""

# IMPORTS ####################################################################

import codecs
import os
import re

from setuptools import setup, find_packages

# SETUP VALUES ###############################################################

NAME = "instruments"
PACKAGES = find_packages()
META_PATH = os.path.join("instruments", "__init__.py")
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: GNU Affero General Public License v3",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Manufacturing",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    "Topic :: Software Development :: Libraries"
]
INSTALL_REQUIRES = [
    "numpy",
    "pyserial",
    "quantities",
    "enum34",
    "future"
]
EXTRAS_REQUIRE = {
    'USBTMC': ["python-usbtmc"],
    'VISA': ["pyvisa"],
    'USB': ["pyusb"]
}
LONG_DESCRIPTION = """
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
"""

# HELPER FUNCTONS ############################################################

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))

# MAIN #######################################################################

if __name__ == "__main__":
    setup(
        name=find_meta("title"),
        version=find_meta("version"),
        url=find_meta("uri"),
        author=find_meta("author"),
        author_email=find_meta("email"),
        packages=PACKAGES,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        description=find_meta("description"),
        long_description=LONG_DESCRIPTION,
        classifiers=CLASSIFIERS
    )
