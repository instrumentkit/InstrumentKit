#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing support for loading instruments from configuration files.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import warnings

try:
    import yaml
except ImportError:
    yaml = None

# FUNCTIONS ###################################################################


def walk_dict(d, path):
    """
    Given a "path" in a dictionary, returns the element specified by that path.
    For instance, given ``{'a': {'b': 42, 'c': {'d': ['foo']}}}`,
    the path ``"/"`` returns the whole dictionary, ``"/a"`` returns
    ``{'b': 42, 'c': {'d': ['foo']}}`` and ``/a/c/d"`` returns ``['foo']``.

    If ``path`` is a list, it is treated identically to
    ``"/" + "/".join(path)``.

    :param dict d: The dictionary to walk through

    :param path: The walking path through the dictionary
    :type path: `str` or `list`
    """
    # Treat as a base case that the path is empty.
    if not path:
        return d
    if isinstance(path, str):
        path = path.split("/")
    if not path[0]:
        # If the first part of the path is empty, do nothing.
        return walk_dict(d, path[1:])
    else:
        # Otherwise, resolve that segment and recurse.
        return walk_dict(d[path[0]], path[1:])


def load_instruments(conf_file_name, conf_path="/"):
    """
    Given the path to a YAML-formatted configuration file and a path within
    that file, loads the instruments described in that configuration file.
    The subsection of the configuration file is expected to look like a map from
    names to YAML nodes giving the class and instrument URI for each instrument.
    For example::

        ddg:
            class: !!python/name:instruments.srs.SRSDG645
            uri: gpib+usb://COM7/15

    Loading instruments from this configuration will result in a dictionary of
    the form
    ``{'ddg': instruments.srs.SRSDG645.open_from_uri('gpib+usb://COM7/15')}``.

    By specifying a path within the configuration file, one can load only a part
    of the given file. For instance, consider the configuration::

        instruments:
            ddg:
                class: !!python/name:instruments.srs.SRSDG645
                uri: gpib+usb://COM7/15
        prefs:
            ...

    Then, specifying ``"/instruments"`` as the configuration path will cause
    this function to load the instruments named in that block, and ignore
    all other keys in the YAML file.

    :param str conf_file_name: Name of the configuration file to load
        instruments from.
    :param str conf_path: ``"/"`` separated path to the section in the
        configuration file to load.

    :rtype: `dict`

    .. warning::
        The configuration file must be trusted, as the class name references
        allow for executing arbitrary code. Do not load instruments from
        configuration files sent over network connections.

        Note that keys in sections excluded by the ``conf_path`` argument are
        still processed, such that any side effects that may occur due to
        such processing will occur independently of the value of ``conf_path``.
    """

    if yaml is None:
        raise ImportError("Could not import PyYAML, which is required "
                          "for this function.")

    with open(conf_file_name, 'r') as f:
        conf_dict = yaml.load(f)

    conf_dict = walk_dict(conf_dict, conf_path)

    inst_dict = {}
    for name, value in conf_dict.iteritems():
        try:
            inst_dict[name] = value["class"].open_from_uri(value["uri"])
        except IOError as ex:
            # FIXME: need to subclass Warning so that repeated warnings
            #        aren't ignored.
            warnings.warn("Exception occured loading device URI "
                          "{}:\n\t{}.".format(value["uri"], ex), RuntimeWarning)
            inst_dict[name] = None

    return inst_dict
