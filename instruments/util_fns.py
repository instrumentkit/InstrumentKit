#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing various utility functions
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import re

from enum import Enum, IntEnum
import quantities as pq

# CONSTANTS ###################################################################

_IDX_REGEX = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\[(-?[0-9]*)\]')

# FUNCTIONS ###################################################################


# pylint: disable=too-many-arguments
def assume_units(value, units):
    """
    If units are not provided for ``value`` (that is, if it is a raw
    `float`), then returns a `~quantities.Quantity` with magnitude
    given by ``value`` and units given by ``units``.

    :param value: A value that may or may not be unitful.
    :param units: Units to be assumed for ``value`` if it does not already
        have units.

    :return: A unitful quantity that has either the units of ``value`` or
        ``units``, depending on if ``value`` is unitful.
    :rtype: `Quantity`
    """
    if not isinstance(value, pq.Quantity):
        value = pq.Quantity(value, units)
    return value


def setattr_expression(target, name_expr, value):
    """
    Recursively calls getattr/setattr for attribute
    names that are miniature expressions with subscripting.
    For instance, of the form ``a[0].b``.
    """
    # Allow "." in attribute names so that we can set attributes
    # recursively.
    if '.' in name_expr:
        # Recursion: We have to strip off a level of getattr.
        head, name_expr = name_expr.split('.', 1)
        match = _IDX_REGEX.match(head)
        if match:
            head_name, head_idx = match.groups()
            target = getattr(target, head_name)[int(head_idx)]
        else:
            target = getattr(target, head)

        setattr_expression(target, name_expr, value)
    else:
        # Base case: We're in the last part of a dot-expression.
        match = _IDX_REGEX.match(name_expr)
        if match:
            name, idx = match.groups()
            getattr(target, name)[int(idx)] = value
        else:
            setattr(target, name_expr, value)


def convert_temperature(temperature, base):
    """
    Convert the temperature to the specified base. This is needed because
    the package `quantities` does not differentiate between ``degC`` and
    ``degK``.

    :param temperature: A quantity with units of Kelvin, Celsius, or Fahrenheit
    :type temperature: `quantities.Quantity`
    :param base: A temperature unit to convert to
    :type base: `unitquantity.UnitTemperature`

    :return: The converted temperature
    :rtype: `quantities.Quantity`
    """
    # quantities reports equivalence between degC and degK, so a string
    # comparison is needed
    newval = assume_units(temperature, pq.degC)
    if newval.units == pq.degF and str(base).split(" ")[1] == 'degC':
        return_val = ((newval.magnitude - 32.0) * 5.0 / 9.0) * base
    elif str(newval.units).split(" ")[1] == 'K' and str(base).split(" ")[1] == 'degC':
        return_val = (newval.magnitude - 273.15) * base
    elif str(newval.units).split(" ")[1] == 'K' and base == pq.degF:
        return_val = (newval.magnitude / 1.8 - 459 / 57) * base
    elif str(newval.units).split(" ")[1] == 'degC' and base == pq.degF:
        return_val = (newval.magnitude * 9.0 / 5.0 + 32.0) * base
    elif newval.units == pq.degF and str(base).split(" ")[1] == 'K':
        return_val = ((newval.magnitude + 459.57) * 5.0 / 9.0) * base
    elif str(newval.units).split(" ")[1] == 'degC' and str(base).split(" ")[1] == 'K':
        return_val = (newval.magnitude + 273.15) * base
    elif str(newval.units).split(" ")[1] == 'degC' and str(base).split(" ")[1] == 'degC':
        return_val = newval
    elif newval.units == pq.degF and base == pq.degF:
        return_val = newval
    elif str(newval.units).split(" ")[1] == 'K' and str(base).split(" ")[1] == 'K':
        return_val = newval
    else:
        raise ValueError(
            "Unable to convert " + str(newval.units) + " to " + str(base))
    return return_val


def split_unit_str(s, default_units=pq.dimensionless, lookup=None):
    """
    Given a string of the form "12 C" or "14.7 GHz", returns a tuple of the
    numeric part and the unit part, irrespective of how many (if any) whitespace
    characters appear between.

    By design, the tuple should be such that it can be unpacked into
    :func:`pq.Quantity`::

        >>> pq.Quantity(*split_unit_str("1 s"))
        array(1) * s

    For this reason, the second element of the tuple may be a unit or
    a string, depending, since the quantity constructor takes either.

    :param str s: Input string that will be split up
    :param default_units: If no units are specified, this argument is given
        as the units.
    :param callable lookup: If specified, this function is called on the
        units part of the input string. If `None`, no lookup is performed.
        Lookups are never performed on the default units.
    :rtype: `tuple` of a `float` and a `str` or `pq.Quantity`
    """
    if lookup is None:
        lookup = lambda x: x

    # Borrowed from:
    # http://stackoverflow.com/questions/430079/how-to-split-strings-into-text-and-number
    # Reg exp tweaked on May 30, 2015 by scasagrande to match on input with
    # scientific notation. General flow borrowed from:
    # http://www.regular-expressions.info/floatingpoint.html
    regex = r"([-+]?[0-9]*\.?[0-9]+)([eE][-+]?[0-9]+)?\s*([a-z]+)?"
    match = re.match(regex, str(s).strip(), re.I)
    if match:
        if match.groups()[1] is None:
            val, _, units = match.groups()
        else:
            val = float(match.groups()[0]) * 10**float(match.groups()[1][1:])
            units = match.groups()[2]

        if units is None:
            return float(val), default_units

        return float(val), lookup(units)

    else:
        try:
            return float(s), default_units
        except ValueError:
            raise ValueError("Could not split '{}' into value "
                             "and units.".format(repr(s)))


def rproperty(fget=None, fset=None, doc=None, readonly=False, writeonly=False):
    """
    Creates and returns a new property based on the input parameters.

    :param function fget: Function to be called for the new property's getter
    :param function fset: Function to be called for the new property's setter
    :param str doc: Docstring for the new property
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    """
    if readonly and writeonly:
        raise ValueError("Properties cannot be both read- and write-only.")
    if readonly:
        return property(fget=fget, fset=None, doc=doc)
    elif writeonly:
        return property(fget=None, fset=fset, doc=doc)

    return property(fget=fget, fset=fset, doc=doc)


def bool_property(command, set_cmd=None, inst_true="ON", inst_false="OFF",
                  doc=None, readonly=False, writeonly=False, set_fmt="{} {}"):
    """
    Called inside of SCPI classes to instantiate boolean properties
    of the device cleanly.
    For example:

    >>> my_property = bool_property(
    ...     "BEST:PROPERTY",
    ...     inst_true="ON",
    ...     inst_false="OFF"
    ... ) # doctest: +SKIP

    This will result in "BEST:PROPERTY ON" or "BEST:PROPERTY OFF" being sent
    when setting, and "BEST:PROPERTY?" being sent when getting.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param str inst_true: String returned and accepted by the instrument for
        `True` values.
    :param str inst_false: String returned and accepted by the instrument for
        `False` values.
    :param str doc: Docstring to be associated with the new property.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}" which places a
        space between the SCPI command the associated parameter. By switching
        to "{}={}" an equals sign would instead be used as the separator.
    """

    def _getter(self):
        return self.query(command + "?").strip() == inst_true

    def _setter(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Bool properties must be specified with a "
                            "boolean value")
        self.sendcmd(set_fmt.format(
            command if set_cmd is None else set_cmd,
            inst_true if newval else inst_false
        ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)


def enum_property(command, enum, set_cmd=None, doc=None, input_decoration=None,
                  output_decoration=None, readonly=False, writeonly=False,
                  set_fmt="{} {}"):
    """
    Called inside of SCPI classes to instantiate Enum properties
    of the device cleanly.
    The decorations can be functions which modify the incoming and outgoing
    values for dumb instruments that do stuff like include superfluous quotes
    that you might not want in your enum.
    Example:
    my_property = bool_property("BEST:PROPERTY", enum_class)

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param type enum: Class derived from `Enum` representing valid values.
    :param callable input_decoration: Function called on responses from
        the instrument before passing to user code.
    :param callable output_decoration: Function called on commands to the
        instrument.
    :param str doc: Docstring to be associated with the new property.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}" which places a
        space between the SCPI command the associated parameter. By switching
        to "{}={}" an equals sign would instead be used as the separator.
    :param str get_cmd: If not `None`, this parameter sets the command string
        to be used when reading/querying from the instrument. If used, the name
        parameter is still used to set the command for pure-write commands to
        the instrument.
    """
    def _in_decor_fcn(val):
        if input_decoration is None:
            return val
        elif hasattr(input_decoration, "__get__"):
            return input_decoration.__get__(None, object)(val)
        return input_decoration(val)

    def _out_decor_fcn(val):
        if output_decoration is None:
            return val
        elif hasattr(output_decoration, "__get__"):
            return output_decoration.__get__(None, object)(val)
        return output_decoration(val)

    def _getter(self):
        return enum(_in_decor_fcn(self.query("{}?".format(command)).strip()))

    def _setter(self, newval):
        try:  # First assume newval is Enum.value
            newval = enum[newval]
        except KeyError:  # Check if newval is Enum.name instead
            try:
                newval = enum(newval)
            except ValueError:
                raise ValueError("Enum property new value not in enum.")
        self.sendcmd(set_fmt.format(
            command if set_cmd is None else set_cmd,
            _out_decor_fcn(enum(newval).value)
        ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)


def unitless_property(command, set_cmd=None, format_code='{:e}', doc=None,
                      readonly=False, writeonly=False, set_fmt="{} {}"):
    """
    Called inside of SCPI classes to instantiate properties with unitless
    numeric values.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param str format_code: Argument to `str.format` used in sending values
        to the instrument.
    :param str doc: Docstring to be associated with the new property.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}" which places a
        space between the SCPI command the associated parameter. By switching
        to "{}={}" an equals sign would instead be used as the separator.
    """

    def _getter(self):
        raw = self.query("{}?".format(command))
        return float(raw)

    def _setter(self, newval):
        if isinstance(newval, pq.Quantity):
            if newval.units == pq.dimensionless:
                newval = float(newval.magnitude)
            else:
                raise ValueError
        strval = format_code.format(newval)
        self.sendcmd(set_fmt.format(
            command if set_cmd is None else set_cmd,
            strval
        ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)


def int_property(command, set_cmd=None, format_code='{:d}', doc=None,
                 readonly=False, writeonly=False, valid_set=None,
                 set_fmt="{} {}"):
    """
    Called inside of SCPI classes to instantiate properties with unitless
    numeric values.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param str format_code: Argument to `str.format` used in sending values
        to the instrument.
    :param str doc: Docstring to be associated with the new property.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param valid_set: Set of valid values for the property, or `None` if all
        `int` values are valid.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}" which places a
        space between the SCPI command the associated parameter. By switching
        to "{}={}" an equals sign would instead be used as the separator.
    """

    def _getter(self):
        raw = self.query("{}?".format(command))
        return int(raw)
    if valid_set is None:
        def _setter(self, newval):
            strval = format_code.format(newval)
            self.sendcmd(set_fmt.format(
                command if set_cmd is None else set_cmd,
                strval
            ))
    else:
        def _setter(self, newval):
            if newval not in valid_set:
                raise ValueError(
                    "{} is not an allowed value for this property; "
                    "must be one of {}.".format(newval, valid_set)
                )
            strval = format_code.format(newval)
            self.sendcmd(set_fmt.format(
                command if set_cmd is None else set_cmd,
                strval
            ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)


def unitful_property(command, units, set_cmd=None, format_code='{:e}', doc=None,
                     input_decoration=None, output_decoration=None,
                     readonly=False, writeonly=False, set_fmt="{} {}",
                     valid_range=(None, None)):
    """
    Called inside of SCPI classes to instantiate properties with unitful numeric
    values. This function assumes that the instrument only accepts
    and returns magnitudes without unit annotations, such that all unit
    information is provided by the ``units`` argument. This is not suitable
    for instruments where the units can change dynamically due to front-panel
    interaction or due to remote commands.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param units: Units to assume in sending and receiving magnitudes to and
        from the instrument.
    :param str format_code: Argument to `str.format` used in sending the
        magnitude of values to the instrument.
    :param str doc: Docstring to be associated with the new property.
    :param callable input_decoration: Function called on responses from
        the instrument before passing to user code.
    :param callable output_decoration: Function called on commands to the
        instrument.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}" which places a
        space between the SCPI command the associated parameter. By switching
        to "{}={}" an equals sign would instead be used as the separator.
    :param valid_range: Tuple containing min & max values when setting
        the property. Index 0 is minimum value, index 1 is maximum value.
        Setting `None` in either disables bounds checking for that end of the
        range. The default of `(None, None)` has no min or max constraints.
        The valid set is inclusive of the values provided.
    :type valid_range: `tuple` or `list` of `int` or `float`
    """
    def _in_decor_fcn(val):
        if input_decoration is None:
            return val
        elif hasattr(input_decoration, "__get__"):
            return input_decoration.__get__(None, object)(val)
        return input_decoration(val)

    def _out_decor_fcn(val):
        if output_decoration is None:
            return val
        elif hasattr(output_decoration, "__get__"):
            return output_decoration.__get__(None, object)(val)
        return output_decoration(val)

    def _getter(self):
        raw = _in_decor_fcn(self.query("{}?".format(command)))
        return pq.Quantity(*split_unit_str(raw, units)).rescale(units)

    def _setter(self, newval):
        min_value, max_value = valid_range
        if min_value is not None:
            if hasattr(min_value, '__call__'):
                min_value = min_value(self)
            if newval < min_value:
                raise ValueError("Unitful quantity is too low. Got {}, minimum "
                                 "value is {}".format(newval, min_value))
        if max_value is not None:
            if hasattr(max_value, '__call__'):
                max_value = max_value(self)
            if newval > max_value:
                raise ValueError("Unitful quantity is too high. Got {}, maximum"
                                 " value is {}".format(newval, max_value))
        # Rescale to the correct unit before printing. This will also
        # catch bad units.
        strval = format_code.format(
            assume_units(newval, units).rescale(units).item())
        self.sendcmd(set_fmt.format(
            command if set_cmd is None else set_cmd,
            _out_decor_fcn(strval)
        ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)


def bounded_unitful_property(command, units, min_fmt_str="{}:MIN?",
                             max_fmt_str="{}:MAX?",
                             valid_range=("query", "query"), **kwargs):
    """
    Called inside of SCPI classes to instantiate properties with unitful numeric
    values which have upper and lower bounds. This function in turn calls
    `unitful_property` where all kwargs for this function are passed on to.
    See `unitful_property` documentation for information about additional
    parameters that will be passed on.

    Compared to `unitful_property`, this function will return 3 properties:
    the one created by `unitful_property`, one for the minimum value, and one
    for the maximum value.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param units: Units to assume in sending and receiving magnitudes to and
        from the instrument.
    :param str min_fmt_str: Specify the string format to use when sending a
        minimum value query. The default is ``"{}:MIN?"`` which will place
        the property name in before the colon. Eg: ``"MOCK:MIN?"``
    :param str max_fmt_str: Specify the string format to use when sending a
        maximum value query. The default is ``"{}:MAX?"`` which will place
        the property name in before the colon. Eg: ``"MOCK:MAX?"``
    :param valid_range: Tuple containing min & max values when setting
        the property. Index 0 is minimum value, index 1 is maximum value.
        Setting `None` in either disables bounds checking for that end of the
        range. The default of ``("query", "query")`` will query the instrument
        for min and max parameter values. The valid set is inclusive of
        the values provided.
    :type valid_range: `list` or `tuple` of `int`, `float`, `None`, or the
        string ``"query"``.
    :param kwargs: All other keyword arguments are passed onto
        `unitful_property`
    :return: Returns a `tuple` of 3 properties: first is as returned by
        `unitful_property`, second is a property representing the minimum
        value, and third is a property representing the maximum value
    """

    def _min_getter(self):
        if valid_range[0] == "query":
            return pq.Quantity(*split_unit_str(self.query(min_fmt_str.format(command)), units))

        return assume_units(valid_range[0], units).rescale(units)

    def _max_getter(self):
        if valid_range[1] == "query":
            return pq.Quantity(*split_unit_str(self.query(max_fmt_str.format(command)), units))

        return assume_units(valid_range[1], units).rescale(units)

    new_range = (
        None if valid_range[0] is None else _min_getter,
        None if valid_range[1] is None else _max_getter
    )

    return (
        unitful_property(command, units, valid_range=new_range, **kwargs),
        property(_min_getter) if valid_range[0] is not None else None,
        property(_max_getter) if valid_range[1] is not None else None
    )


def string_property(command, set_cmd=None, bookmark_symbol='"', doc=None,
                    readonly=False, writeonly=False, set_fmt="{} {}{}{}"):
    """
    Called inside of SCPI classes to instantiate properties with a string value.

    :param str command: Name of the SCPI command corresponding to this property.
        If parameter set_cmd is not specified, then this parameter is also used
        for both getting and setting.
    :param str set_cmd: If not `None`, this parameter sets the command string
        to be used when sending commands with no return values to the
        instrument. This allows for non-symmetric properties that have different
        strings for getting vs setting a property.
    :param str doc: Docstring to be associated with the new property.
    :param bool readonly: If `True`, the returned property does not have a
        setter.
    :param bool writeonly: If `True`, the returned property does not have a
        getter. Both readonly and writeonly cannot both be `True`.
    :param str set_fmt: Specify the string format to use when sending a
        non-query to the instrument. The default is "{} {}{}{}" which places a
        space between the SCPI command the associated parameter, and places
        the bookmark symbols on either side of the parameter.
    :param str bookmark_symbol: The symbol that will flank both sides of the
        parameter to be sent to the instrument. By default this is ``"``.
    """
    bookmark_length = len(bookmark_symbol)

    def _getter(self):
        string = self.query("{}?".format(command))
        string = string[
            bookmark_length:-bookmark_length] if bookmark_length > 0 else string
        return string

    def _setter(self, newval):
        self.sendcmd(set_fmt.format(
            command if set_cmd is None else set_cmd,
            bookmark_symbol, newval, bookmark_symbol
        ))

    return rproperty(fget=_getter, fset=_setter, doc=doc, readonly=readonly,
                     writeonly=writeonly)

# CLASSES #####################################################################


class ProxyList(object):
    """
    This is a special class used to generate lists of objects where the valid
    keys are defined by the `valid_set` init parameter. This allows an
    instrument to have a single property through which all of its various
    identical input/ouput channels can be accessed.

    Search the code base of existing examples of how this is used for plenty
    of different examples.

    :param parent: The "parent" or "owner" of the of the proxy classes. In
        dev work, this is typically ``self``.
    :param proxy_cls: The child class that will be returned when the returned
        object is iterated through. These are usually objects that represent
        an entire channel/sensor/input/output, of which an instrument might
        have more than one but each are individually addressed. An example is
        an oscilloscope channel.
    :param valid_set: The set of valid keys by which the proxy class objects
        are accessed. Typically this is something like `range`, but can be
        any generator, list, enum, etc.
    """

    def __init__(self, parent, proxy_cls, valid_set):
        self._parent = parent
        self._proxy_cls = proxy_cls
        self._valid_set = valid_set

        # FIXME: This only checks the next level up the chain!
        if hasattr(valid_set, '__bases__'):
            self._isenum = (Enum in valid_set.__bases__) or (
                IntEnum in valid_set.__bases__)
        else:
            self._isenum = False

    def __iter__(self):
        for idx in self._valid_set:
            yield self._proxy_cls(self._parent, idx)

    def __getitem__(self, idx):
        # If we have an enum, try to normalize by using getitem. This will
        # allow for things like 'x' to be used instead of enum.x.
        if self._isenum:
            try:
                idx = self._valid_set[idx]
            except KeyError:
                try:
                    idx = self._valid_set(idx)
                except ValueError:
                    pass
            if not isinstance(idx, self._valid_set):
                raise IndexError("Index out of range. Must be "
                                 "in {}.".format(self._valid_set))
            else:
                idx = idx.value
        else:
            if idx not in self._valid_set:
                raise IndexError("Index out of range. Must be "
                                 "in {}.".format(self._valid_set))
        return self._proxy_cls(self._parent, idx)

    def __len__(self):
        return len(self._valid_set)
