# type: ignore

"""
This module defines data types in Taichi:

- primitive: int, float, etc.
- compound: matrix, vector, struct.
- template: for reference types.
- ndarray: for arbitrary arrays.
- quant: for quantized types, see "https://yuanming.taichi.graphics/publication/2021-quantaichi/quantaichi.pdf"
"""

from taichi.types import quant
from taichi.types.annotations import *
from taichi.types.compound_types import *
from taichi.types.ndarray_type import *
from taichi.types.primitive_types import *
from taichi.types.texture_type import *
from taichi.types.utils import *

T = TypeVar("T")

class Field(T):
    def __init__(self, dtype=None, ndim: int):
        self.dtype = dtype
        self.ndim = ndim

    def __class_getitem__(cls, params):
        if isinstance(params, tuple):
            dtype, ndim = params
        else:
            dtype = params
            ndim = 0

        class SpecializedField(cls):
            def __init__(self):
                super().__init__(dtype=dtype, ndim=ndim)

        return SpecializedField
