import sys as _sys
import importlib as _importlib
_mod = _importlib.import_module('core_lib.cache')
from core_lib.cache import *  # noqa: F401,F403
_sys.modules[__name__] = _mod
