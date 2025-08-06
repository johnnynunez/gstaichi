# type: ignore

"""GsTaichi's AOT (ahead of time) module.

Users can use GsTaichi as a GPU compute shader/kernel compiler by compiling their
GsTaichi kernels into an AOT module.
"""

import gstaichi.aot.conventions
from gstaichi.aot._export import export, export_as
from gstaichi.aot.conventions.gfxruntime140 import GfxRuntime140
from gstaichi.aot.module import Module
