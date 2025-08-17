from typing import Union

from gstaichi._lib import core as ti_python_core

# ========================================
# real types

# ----------------------------------------

float16_cxx = ti_python_core.DataType_f16
"""16-bit precision floating point data type.
"""

# ----------------------------------------

f16_cxx = float16_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.float16`
"""

# ----------------------------------------

float32_cxx = ti_python_core.DataType_f32
"""32-bit single precision floating point data type.
"""

# ----------------------------------------

f32_cxx = float32_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.float32`
"""

# ----------------------------------------

float64_cxx = ti_python_core.DataType_f64
"""64-bit double precision floating point data type.
"""

# ----------------------------------------

f64_cxx = float64_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.float64`
"""
# ----------------------------------------

# ========================================
# Integer types

# ----------------------------------------

int8_cxx = ti_python_core.DataType_i8
"""8-bit signed integer data type.
"""

# ----------------------------------------

i8_cxx = int8_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.int8`
"""

# ----------------------------------------

int16_cxx = ti_python_core.DataType_i16
"""16-bit signed integer data type.
"""

# ----------------------------------------

i16_cxx = int16_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.int16`
"""

# ----------------------------------------

int32_cxx = ti_python_core.DataType_i32
"""32-bit signed integer data type.
"""

# ----------------------------------------

i32_cxx = int32_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.int32`
"""

# ----------------------------------------

int64_cxx = ti_python_core.DataType_i64
"""64-bit signed integer data type.
"""

# ----------------------------------------

i64_cxx = int64_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.int64`
"""

# ----------------------------------------

uint8_cxx = ti_python_core.DataType_u8
"""8-bit unsigned integer data type.
"""

# ----------------------------------------

uint1_cxx = ti_python_core.DataType_u1
"""1-bit unsigned integer data type. Same as booleans.
"""

# ----------------------------------------

u1_cxx = uint1_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.uint1`
"""

# ----------------------------------------

u8_cxx = uint8_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.uint8`
"""

# ----------------------------------------

uint16_cxx = ti_python_core.DataType_u16
"""16-bit unsigned integer data type.
"""

# ----------------------------------------

u16_cxx = uint16_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.uint16`
"""

# ----------------------------------------

uint32_cxx = ti_python_core.DataType_u32
"""32-bit unsigned integer data type.
"""

# ----------------------------------------

u32_cxx = uint32_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.uint32`
"""

# ----------------------------------------

uint64_cxx = ti_python_core.DataType_u64
"""64-bit unsigned integer data type.
"""

# ----------------------------------------

u64_cxx = uint64_cxx
"""Alias for :const:`~gstaichi.types.primitive_types.uint64`
"""

# ----------------------------------------


class RefType:
    def __init__(self, tp):
        self.tp = tp


def ref(tp):
    return RefType(tp)


class PrimitiveBase:
    pass


class i32(PrimitiveBase):
    cxx = i32_cxx

class f16(PrimitiveBase):
    cxx = f16_cxx

class f32(PrimitiveBase):
    cxx = f32_cxx

class f64(PrimitiveBase):
    cxx = f64_cxx

class i8(PrimitiveBase):
    cxx = i8_cxx

class i16(PrimitiveBase):
    cxx = i16_cxx

class i64(PrimitiveBase):
    cxx = i64_cxx

class u1(PrimitiveBase):
    cxx = u1_cxx

class u8(PrimitiveBase):
    cxx = u8_cxx

class u16(PrimitiveBase):
    cxx = u16_cxx

class u32(PrimitiveBase):
    cxx = u32_cxx

class u64(PrimitiveBase):
    cxx = u64_cxx


int8 = i8
int16 = i16
int32 = i32
int64 = i64

uint1 = u1
uint8 = u8
uint16 = u16
uint32 = u32
uint64 = u64

float16 = f16
float32 = f32
float64 = f64

real_types = [f16, f32, f64, float]
real_type_ids = [id(t) for t in real_types]

integer_types = [i8, i16, i32, i64, u1, u8, u16, u32, u64, int, bool]
integer_type_ids = [id(t) for t in integer_types]

all_types = real_types + integer_types
type_ids = [id(t) for t in all_types]

_python_primitive_types = Union[int, float, bool, str, None]

__all__ = [
    "float32",
    "f32",
    "float64",
    "f64",
    "float16",
    "f16",
    "int8",
    "i8",
    "int16",
    "i16",
    "int32",
    "i32",
    "int64",
    "i64",
    "uint1",
    "u1",
    "uint8",
    "u8",
    "uint16",
    "u16",
    "uint32",
    "u32",
    "uint64",
    "u64",
    "ref",
    "_python_primitive_types",
    # "I32",
]
