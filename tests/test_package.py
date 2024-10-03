"""
Module containing tests for the base instruments package
"""

# IMPORTS ####################################################################

import instruments._version as ik_version_file


# TEST CASES #################################################################


def test_package_has_version():
    assert hasattr(ik_version_file, "version")
    assert hasattr(ik_version_file, "version_tuple")
