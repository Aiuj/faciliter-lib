# Backwards-compatibility shim for legacy imports
# Redirects faciliter_lib.* to core_lib.*
import sys as _sys
import importlib as _importlib

# Import the new core package
import core_lib as _core_lib

# Expose top-level symbols
from core_lib import *  # noqa: F401,F403

# Ensure "faciliter_lib" points to the same module as core_lib
_sys.modules[__name__] = _core_lib
