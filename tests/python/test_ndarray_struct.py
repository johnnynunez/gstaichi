from dataclasses import dataclass

import taichi as ti
from tests import test_utils


@test_utils.test()
def test_ndarray_struct_l1():
    a = ti.ndarray(ti.i32, shape=(55,))
    b = ti.ndarray(ti.i32, shape=(57,))
    c = ti.ndarray(ti.i32, shape=(211,))
    d = ti.ndarray(ti.i32, shape=(223,))
    e = ti.ndarray(ti.i32, shape=(227,))

    @dataclass
    class MyStruct:
        a: ti.types.NDArray[ti.i32, 1]
        b: ti.types.NDArray[ti.i32, 1]
        c: ti.types.NDArray[ti.i32, 1]

    @ti.kernel
    def k1(z: ti.types.NDArray[ti.i32, 1], my_struct: MyStruct, bar: ti.types.NDArray[ti.i32, 1]) -> None:
        z[33] += 2
        my_struct.a[35] += 3
        my_struct.b[37] += 5
        my_struct.c[51] += 17
        bar[222] = 41

    my_struct = MyStruct(a=a, b=b, c=c)
    k1(d, my_struct, e)
    assert d[33] == 2
    assert a[35] == 3
    assert b[37] == 5
    assert c[51] == 17
    assert e[222] == 41


@test_utils.test()
def test_ndarray_struct_l2():
    a = ti.ndarray(ti.i32, shape=(55,))
    b = ti.ndarray(ti.i32, shape=(57,))
    c = ti.ndarray(ti.i32, shape=(211,))
    d = ti.ndarray(ti.i32, shape=(223,))
    e = ti.ndarray(ti.i32, shape=(227,))

    @dataclass
    class MyStruct:
        a: ti.types.NDArray[ti.i32, 1]
        b: ti.types.NDArray[ti.i32, 1]
        c: ti.types.NDArray[ti.i32, 1]

    @ti.func
    def s1(z2: ti.types.NDArray[ti.i32, 1], my_struct2: MyStruct, bar2: ti.types.NDArray[ti.i32, 1]) -> None:
        z2[22] += 88
        my_struct2.a[45] += 22
        my_struct2.b[47] += 23
        my_struct2.c[41] += 24
        bar2[111] += 123

    @ti.kernel
    def k1(z: ti.types.NDArray[ti.i32, 1], my_struct: MyStruct, bar: ti.types.NDArray[ti.i32, 1]) -> None:
        z[33] += 2
        my_struct.a[35] += 3
        my_struct.b[37] += 5
        my_struct.c[51] += 17
        bar[222] = 41
        s1(z, my_struct, bar)

    my_struct = MyStruct(a=a, b=b, c=c)
    k1(d, my_struct, e)
    assert d[33] == 2
    assert a[35] == 3
    assert b[37] == 5
    assert c[51] == 17

    assert d[22] == 88
    assert a[45] == 22
    assert b[47] == 23
    assert c[41] == 24
    assert e[111] == 123


@test_utils.test()
def test_ndarray_struct_l3():
    a = ti.ndarray(ti.i32, shape=(55,))
    b = ti.ndarray(ti.i32, shape=(57,))
    c = ti.ndarray(ti.i32, shape=(211,))
    d = ti.ndarray(ti.i32, shape=(223,))
    e = ti.ndarray(ti.i32, shape=(227,))

    @dataclass
    class MyStruct:
        a: ti.types.NDArray[ti.i32, 1]
        b: ti.types.NDArray[ti.i32, 1]
        c: ti.types.NDArray[ti.i32, 1]

    @ti.func
    def s2(z3: ti.types.NDArray[ti.i32, 1], my_struct3: MyStruct, bar3: ti.types.NDArray[ti.i32, 1]) -> None:
        z3[24] += 89
        my_struct3.a[46] += 32
        my_struct3.b[48] += 33
        my_struct3.c[42] += 34
        bar3[112] += 125

    @ti.func
    def s1(z2: ti.types.NDArray[ti.i32, 1], my_struct2: MyStruct, bar2: ti.types.NDArray[ti.i32, 1]) -> None:
        z2[22] += 88
        my_struct2.a[45] += 22
        my_struct2.b[47] += 23
        my_struct2.c[41] += 24
        bar2[111] += 123
        s2(z2, my_struct2, bar2)

    @ti.kernel
    def k1(z: ti.types.NDArray[ti.i32, 1], my_struct: MyStruct, bar: ti.types.NDArray[ti.i32, 1]) -> None:
        z[33] += 2
        my_struct.a[35] += 3
        my_struct.b[37] += 5
        my_struct.c[51] += 17
        bar[222] = 41
        s1(z, my_struct, bar)

    my_struct = MyStruct(a=a, b=b, c=c)
    k1(d, my_struct, e)
    assert d[33] == 2
    assert a[35] == 3
    assert b[37] == 5
    assert c[51] == 17

    assert d[22] == 88
    assert a[45] == 22
    assert b[47] == 23
    assert c[41] == 24
    assert e[111] == 123

    assert d[24] == 89
    assert a[46] == 32
    assert b[48] == 33
    assert c[42] == 34
    assert e[112] == 125


@test_utils.test()
def test_ndarray_struct_l4():
    a = ti.ndarray(ti.i32, shape=(55,))
    b = ti.ndarray(ti.i32, shape=(57,))
    c = ti.ndarray(ti.i32, shape=(211,))
    d = ti.ndarray(ti.i32, shape=(223,))
    e = ti.ndarray(ti.i32, shape=(227,))

    @dataclass
    class MyStruct:
        a: ti.types.NDArray[ti.i32, 1]
        b: ti.types.NDArray[ti.i32, 1]
        c: ti.types.NDArray[ti.i32, 1]

    @ti.func
    def s4(a: ti.types.NDArray[ti.i32, 1], b: ti.types.NDArray[ti.i32, 1]) -> None:
        a[1] += 888
        b[2] += 999

    @ti.func
    def s3(z3: ti.types.NDArray[ti.i32, 1], my_struct3: MyStruct, bar3: ti.types.NDArray[ti.i32, 1]) -> None:
        z3[25] += 90
        my_struct3.a[47] += 42
        my_struct3.b[49] += 43
        my_struct3.c[43] += 44
        bar3[113] += 125
        s4(my_struct3.a, my_struct3.b)

    @ti.func
    def s2(z3: ti.types.NDArray[ti.i32, 1], my_struct3: MyStruct, bar3: ti.types.NDArray[ti.i32, 1]) -> None:
        z3[24] += 89
        my_struct3.a[46] += 32
        my_struct3.b[48] += 33
        my_struct3.c[42] += 34
        bar3[112] += 125
        s3(z3, my_struct3, bar3)

    @ti.func
    def s1(z2: ti.types.NDArray[ti.i32, 1], my_struct2: MyStruct, bar2: ti.types.NDArray[ti.i32, 1]) -> None:
        z2[22] += 88
        my_struct2.a[45] += 22
        my_struct2.b[47] += 23
        my_struct2.c[41] += 24
        bar2[111] += 123
        s2(z2, my_struct2, bar2)

    @ti.kernel
    def k1(z: ti.types.NDArray[ti.i32, 1], my_struct: MyStruct, bar: ti.types.NDArray[ti.i32, 1]) -> None:
        z[33] += 2
        my_struct.a[35] += 3
        my_struct.b[37] += 5
        my_struct.c[51] += 17
        bar[222] = 41
        s1(z, my_struct, bar)

    my_struct = MyStruct(a=a, b=b, c=c)
    k1(d, my_struct, e)
    assert d[33] == 2
    assert a[35] == 3
    assert b[37] == 5
    assert c[51] == 17

    assert d[22] == 88
    assert a[45] == 22
    assert b[47] == 23
    assert c[41] == 24
    assert e[111] == 123

    assert d[24] == 89
    assert a[46] == 32
    assert b[48] == 33
    assert c[42] == 34
    assert e[112] == 125

    assert d[25] == 90
    assert a[47] == 42
    assert b[49] == 43
    assert c[43] == 44
    assert e[113] == 125

    assert a[1] == 888
    assert b[2] == 999
