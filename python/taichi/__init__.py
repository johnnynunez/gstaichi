print('init funcs')
from taichi._funcs import *
print('init lib')
from taichi._lib import core as _ti_core
print('init _lib.utils')
from taichi._lib.utils import warn_restricted_version
print('init _logging')
from taichi._logging import *
print('init _snode')
from taichi._snode import *
print('init lang')
from taichi.lang import *  # pylint: disable=W0622 # TODO(archibate): It's `taichi.lang.core` overriding `taichi.core`
print('init annotations')
from taichi.types.annotations import *

# Provide a shortcut to types since they're commonly used.
print('init types.primitive_types')
from taichi.types.primitive_types import *


print('init ad, etc')
from taichi import ad, algorithms, experimental, graph, linalg, math, sparse, tools, types
print('init gu')
from taichi.ui import GUI, hex_to_rgb, rgb_to_hex, ui

# Issue#2223: Do not reorder, or we're busted with partially initialized module
print('init aot')
from taichi import aot  # isort:skip
print('taichi.__init__ finished <<<')


def __getattr__(attr):
    if attr == "cfg":
        return None if lang.impl.get_runtime().prog is None else lang.impl.current_cfg()
    raise AttributeError(f"module '{__name__}' has no attribute '{attr}'")


__version__ = (
    _ti_core.get_version_major(),
    _ti_core.get_version_minor(),
    _ti_core.get_version_patch(),
)

del _ti_core

warn_restricted_version()
del warn_restricted_version
