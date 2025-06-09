"""
This module defines data types in Taichi:

- primitive: int, float, etc.
- compound: matrix, vector, struct.
- template: for reference types.
- ndarray: for arbitrary arrays.
- quant: for quantized types, see "https://yuanming.taichi.graphics/publication/2021-quantaichi/quantaichi.pdf"
"""

print('types.__init__ >>>')
print('types.__init__ quant')
from taichi.types import quant
print('types.__init__ annotations')
from taichi.types.annotations import *
print('types.__init__ compound types')
from taichi.types.compound_types import *
from taichi.types.ndarray_type import *
from taichi.types.primitive_types import *
from taichi.types.texture_type import *
from taichi.types.utils import *
print('types.__init__ finished <<<')
