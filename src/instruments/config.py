#!/usr/bin/env python
"""
Module containing support for loading instruments from configuration files.
"""

# IMPORTS #####################################################################


import warnings

try:
    import ruamel.yaml as yaml
except ImportError:
    # Some versions of ruamel.yaml are named ruamel_yaml, so try that
    # too.
    #
    # In either case, we've observed issues with pylint where it will raise
    # a false positive from its import-error checker, so we locally disable
    # it here. Once the cause for the false positive has been identified,
    # the import-error check should be re-enabled.
    import ruamel_yaml as yaml  # pylint: disable=import-error

from instruments.units import ureg as u
from instruments.util_fns import setattr_expression, split_unit_str

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
    if not isinstance(path, list):
        path = path.split("/")

    if not path[0]:
        # If the first part of the path is empty, do nothing.
        return walk_dict(d, path[1:])

    # Otherwise, resolve that segment and recurse.
    return walk_dict(d[path[0]], path[1:])


def quantity_constructor(loader, node):
    """
    Constructs a `u.Quantity` instance from a PyYAML
    node tagged as ``!Q``.
    """
    # Follows the example of http://stackoverflow.com/a/43081967/267841.
    value = loader.construct_scalar(node)
    return u.Quantity(*split_unit_str(value))


# We avoid having to register !Q every time by doing as soon as the
# relevant constructor is defined.
yaml.add_constructor("!Q", quantity_constructor)


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

    Each instrument configuration section can also specify one or more attributes
    to set. These attributes are specified using a ``attrs`` section as well as the
    required ``class`` and ``uri`` sections. For instance, the following
    dictionary creates a ThorLabs APT motor controller instrument with a single motor
    model configured::

        rot_stage:
            class: !!python/name:instruments.thorabsapt.APTMotorController
            uri: serial:///dev/ttyUSB0?baud=115200
            attrs:
                channel[0].motor_model: PRM1-Z8

    Unitful attributes can be specified by using the ``!Q`` tag to quickly create
    instances of `u.Quantity`. In the example above, for instance, we can set a motion
    timeout as a unitful quantity::

        attrs:
            motion_timeout: !Q 1 minute

    When using the ``!Q`` tag, any text before a space is taken to be the magnitude
    of the quantity, and text following is taken to be the unit specification.

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
        instruments from. Alternatively, a file-like object may be provided.
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
        raise ImportError(
            "Could not import ruamel.yaml, which is required " "for this function."
        )

    if isinstance(conf_file_name, str):
        with open(conf_file_name) as f:
            conf_dict = yaml.load(f, Loader=yaml.Loader)
    else:
        conf_dict = yaml.load(conf_file_name, Loader=yaml.Loader)

    conf_dict = walk_dict(conf_dict, conf_path)

    inst_dict = {}
    for name, value in conf_dict.items():
        try:
            inst_dict[name] = value["class"].open_from_uri(value["uri"])

            if "attrs" in value:
                # We have some attrs we can set on the newly created instrument.
                for attr_name, attr_value in value["attrs"].items():
                    setattr_expression(inst_dict[name], attr_name, attr_value)

        except OSError as ex:
            # FIXME: need to subclass Warning so that repeated warnings
            #        aren't ignored.
            warnings.warn(
                "Exception occured loading device with URI "
                "{}:\n\t{}.".format(value["uri"], ex),
                RuntimeWarning,
            )
            inst_dict[name] = None

    return inst_dict
