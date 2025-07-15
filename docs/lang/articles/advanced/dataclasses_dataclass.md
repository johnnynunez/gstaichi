# dataclasses.dataclass

dataclasses.dataclass - henceforth referred to as 'dataclass' in this doc - allows you to create heterogeneous structs containing:
- ndarray
- fields
- primitive types

This struct:
- can be passed into kernels (`@ti.kernel`)
- can be passed into sub-functions (`@ti.func`)
- can be combined with other parameters, in the function signature of such calls
- does not affect runtime performance, compared to passing in the elements directly, as parameters

The members are read-only. However, ndarrays and fields are stored as references (pointers), so the contents of the ndarrays and fields can be freely mutated by the kernels and ti.func's.

## Limitations:
- `@ti.real_func` not supported currently
- nested dataclasses are not supported currently
- automatic differentiation not supported currently

## Usage:

Example:

```
import taichi as ti
from dataclasses import dataclass

ti.init(arch=ti.gpu)

a = ti.ndarray(ti.i32, shape=(55,))
b = ti.ndarray(ti.i32, shape=(57,))

@ti.kernel
def k1(my_struct: MyStruct) -> None:
    my_struct.a[35] += 3
    my_struct.b[37] += 5

my_struct = MyStruct(a=a, b=b)
k1(my_struct)
print("my_struct.a[35]", my_struct.a[35])
print("my_struct.b[37]", my_struct.b[37])
```

Output:
```
my_struct.a[35] 3
my_struct.b[37] 5
```
