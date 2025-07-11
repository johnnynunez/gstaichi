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

ti.init(arch=ti.cpu, offline_cache=False, debug=False)

print("================== before creating 4 x ndarrays")
a = ti.ndarray(ti.i32, shape=(55,))
b = ti.ndarray(ti.i32, shape=(57,))
c = ti.ndarray(ti.i32, shape=(211,))
d = ti.ndarray(ti.i32, shape=(223,))
e = ti.ndarray(ti.i32, shape=(227,))

f1_param = ti.field(ti.i32, shape=(41,))

print("================== before MyStruct declaration")
@dataclass
class MyStruct:
    a: ti.types.NDArray[ti.i32, 1]
    b: ti.types.NDArray[ti.i32, 1]
    c: ti.types.NDArray[ti.i32, 1]
    f1: ti.template()

@ti.func
def s2(z3: ti.types.NDArray[ti.i32, 1], my_struct3: MyStruct, bar3: ti.types.NDArray[ti.i32, 1]) -> None:
    z3[24] += 89
    my_struct3.a[46] += 32
    my_struct3.b[48] += 33
    my_struct3.f1[42] += 34
    bar3[112] += 125

@ti.func
def s1(z2: ti.types.NDArray[ti.i32, 1], my_struct2: MyStruct, bar2: ti.types.NDArray[ti.i32, 1]) -> None:
    z2[22] += 88
    my_struct2.a[45] += 22
    my_struct2.b[47] += 23
    my_struct2.f1[41] += 24
    bar2[111] += 123
    s2(z2, my_struct2, bar2)

print("================== before ti.kernel declaration")
@ti.kernel
def k1(z: ti.types.NDArray[ti.i32, 1], my_struct: MyStruct, bar: ti.types.NDArray[ti.i32, 1]) -> None:
    z[33] += 2
    my_struct.a[35] += 3
    my_struct.b[37] += 5
    my_struct.c[51] += 17
    my_struct.f1[7] += 61
    bar[222] = 41
    s1(z, my_struct, bar)

print("================== before creating MyStruct instance")
my_struct = MyStruct(a=a, b=b, c=c, f1=f1_param)
print("================== before running k1")
k1(d, my_struct, e)
print("d[33]", d[33])
print("a[35]", a[35])
print("b[37]", b[37])
print("c[51]", c[51])
print("e[222]", e[222])
print("f1[7]", f1_param[7])

print("")
print("d[22]", d[22])
print("a[45]", a[45])
print("b[47]", b[47])
print("f1_param[41]", f1_param[41])
print("e[111]", e[111])

print("")
print("d[24]", d[24])
print("a[46]", a[46])
print("b[48]", b[48])
print("f1_param[42]", f1_param[42])
print("e[112]", e[112])
```

Output:
```
================== before creating 4 x ndarrays
================== before MyStruct declaration
================== before ti.kernel declaration
================== before creating MyStruct instance
================== before running k1
d[33] 2
a[35] 3
b[37] 5
c[51] 17
e[222] 41
f1[7] 61

d[22] 88
a[45] 22
b[47] 23
f1_param[41] 24
e[111] 123

d[24] 89
a[46] 32
b[48] 33
f1_param[42] 34
e[112] 125
```
