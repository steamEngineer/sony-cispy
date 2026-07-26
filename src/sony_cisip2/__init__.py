"""Sony CIS-IP2 Protocol Library for Python.

A modern Python library for controlling Sony Audio/Video Receivers (AVRs) and Soundbars
that support the CIS-IP2 protocol over Ethernet/IP.
"""

from .client import SonyCISIP2
from .commandset import commands_dict
from .variables import variables_dict

__version__ = "0.1.0a0"
__all__ = ["SonyCISIP2", "commands_dict", "variables_dict", "__version__"]
