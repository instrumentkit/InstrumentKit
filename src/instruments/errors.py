#!/usr/bin/env python
"""
Module containing custom exception errors used by various instruments.
"""

# IMPORTS #####################################################################


# CLASSES #####################################################################


class AcknowledgementError(IOError):
    """
    This error is raised when an instrument fails to send the expected
    acknowledgement string.
    """


class PromptError(IOError):
    """
    This error is raised when an instrument fails to send a "prompt"
    character when one is expected. Typically most instruments do not send
    these characters, but some do in a misguided attempt to be more "user
    friendly".
    """
