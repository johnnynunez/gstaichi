import pytest

import taichi as ti
from tests import test_utils


@ti.kernel
def some_kernel(a: ti.types.Field[ti.i32, 1], b: ti.types.Field[ti.i32, 1]) -> None:
    a[None] = b[None] + 2


@test_utils.test()
def test_template_no_braces():
    a = ti.field(int, shape=())
    b = ti.field(int, shape=())
    b[None] = 5
    some_kernel(a, b)
    assert a[None] == 5 + 2


@ti.func
def sub1(a: ti.template, b: ti.types.Field[ti.i32, 1]) -> None:
    a[None] = b[None] + 2


@ti.kernel
def some_kernel_more_typing(a: ti.types.Field[ti.i32, 1], b: ti.types.Field[ti.i32, 1]) -> None:
    a[None] = b[None] + 2
    sub1(a, b)


@test_utils.test()
def test_template_with_type():
    a = ti.field(int, shape=())
    b = ti.field(int, shape=())
    b[None] = 5
    some_kernel_more_typing(a, b)
    assert a[None] == 5 + 2
