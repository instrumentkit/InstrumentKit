..
    TODO: put documentation license header here.
    
.. currentmodule: instruments.abstract_instruments.axis
    
============
Virtual Axes
============

.. note::

    The functionality described here is very much so a work-in-progress,
    such that the documentation really serves as a kind of design document.

Introduction
============

Many of the instruments supported by InstrumentKit expose one or more axes.
For example, instruments such as the Newport ESP-301 control one to three
stepper motors or servos, each of which can be moved independently.
InstrumentKit exposes controllable axes in a way that is abstracted from the
instrument that powers each axis, so that control software is independent of the
exact configuration, allowing for experimental flexibility.

Additionally, by abstracting axes in this way, different axes can be grouped
together. For instance, if one pair of motors is used to control a position in
the :math:`xy`-plane, and another stage is used to control the :math:`z`-axis,
then these can be combined using a :class:`PerpendicularAC` to make a single
object that addresses a point in the full volume.
Other examples of combining axes include rotating coordinate frames or using
pairing devices for fine and coarse controls.

One consequence of the fact that axes may be combined in these ways, however,
is that it may no longer make sense to individually address a particular axis.
That is, instead, moving to a position on an axis may involve controlling two
or more physical devices. Thus, InstrumentKit's axis support is centered around
the :class:`AxisCollection` class that represents a group of axes.

:class:`AxisCollection`
=======================

:class:`Axis` and :class:`AxisList`
===================================

To simplify the creation of :class:`AxisCollection` subclasses in cases where
axes may be defined individually, the :class:`AxisList` class provides a
concrete implementation of ``AxisCollection`` that delegates to one or more
:class:`Axis` objects.



