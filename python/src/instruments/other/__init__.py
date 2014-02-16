# Provide the classes that used to be in instruments.other by importing them
# from their new homes.
from instruments.oxford import OxfordITC503
from instruments.picowatt import PicowattAVS47
from instruments.yokogawa import (
    Yokogawa7651,
)
from instruments.newport import (
    NewportESP301, NewportESP301Axis, NewportError, NewportESP301HomeSearchMode
)
from instruments.phasematrix import PhaseMatrixFSW0020
from instruments.holzworth import HolzworthHS9000

'''
def __deprecation_warning(cls, newpkg):
    """
    Adds a deprecation warning to the given class. Note that, as a side-effect,
    this breaks checks like ``isinstance``, but given the nature of what we're
    doing here (namely, discouraging the continued use of ``instruments.other``)
    I'm not sure that's a critical problem.
    """
    
    import warnings # <- import here to keep warnings from leaking.
    
    def new(*args, **kwargs):
        warnings.warn(
            "The instruments.other package has been deprecated. "
            "Please import from instruments.{} instead.".format(newpkg),
            UserWarning
        )
        return cls(*args, **kwargs)

    # Copy over all class methods.
    for attrname in dir(cls):
        attr = getattr(cls, attrname)
        if hasattr(attr, '__self__') and getattr(attr, '__self__') is cls:
            setattr(new, attrname, attr)
        
    new.__doc__ = cls.__doc__
    return new
    
OxfordITC503 = __deprecation_warning(OxfordITC503, "oxford")
PicowattAVS47 = __deprecation_warning(PicowattAVS47, "picowatt")
Yokogawa7651 = __deprecation_warning(Yokogawa7651, "yokogawa")

NewportESP301 = __deprecation_warning(NewportESP301, "newport")
NewportESP301Axis = __deprecation_warning(NewportESP301Axis, "newport")
NewportError = __deprecation_warning(NewportError, "newport")
NewportESP301HomeSearchMode = __deprecation_warning(NewportESP301HomeSearchMode, "newport")
PhaseMatrixFSW0020 = __deprecation_warning(PhaseMatrixFSW0020, "phasematrix")
HolzworthHS9000 = __deprecation_warning(HolzworthHS9000, "holzworth")
'''
