"""
Small module to obtain handles to optional dependencies
"""

# pylint: disable=unused-import
try:
    import numpy

    _numpy_installed = True
except ImportError:
    numpy = None
    _numpy_installed = False
