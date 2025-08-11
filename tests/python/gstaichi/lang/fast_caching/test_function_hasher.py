import gstaichi as ti
import pytest
from tests import test_utils

from gstaichi.lang.fast_caching import function_hasher


@test_utils.test()
def test_function_hasher_simple() -> None:
    class one:
        @staticmethod
        def foo(a: int, b: int):
            return a + b

        @staticmethod
        def foo2(a: int, b: int):
            return a + b

    class two:
        @staticmethod
        def foo(a: int, b: int):
            return a + b

        @staticmethod
        def foo2(a: int, b: int):
            return a + b

    class diff1:
        @staticmethod
        def foo(a: int, b: int):
            return a + b + 3

        @staticmethod
        def foo2(a: int, b: int):
            return a + b + 5

    class diff2:
        @staticmethod
        def foo(a: int, b: float):
            return a + b

    h = function_hasher.hash_kernel
    print(h(one.foo))
    print(h(two.foo))
    print(h(one.foo))
    print(h(two.foo))
    print(h(one.foo2))
    print(h(two.foo2))

    assert h(one.foo) == h(two.foo)
    assert h(one.foo2) == h(two.foo2)
    assert h(one.foo) != h(two.foo2)

    assert h(one.foo) != h(diff1.foo)
    assert h(one.foo2) != h(diff1.foo2)

    assert h(one.foo) != h(diff2.foo)


@test_utils.test()
def test_function_hasher_using_test_files() -> None:
    h = function_hasher.hash_kernel

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import basic1_base, basic1_same, basic1_diff
    print(h(basic1_base.entry))
    print(h(basic1_same.entry))
    print(h(basic1_diff.entry))

    assert h(basic1_base.entry) == h(basic1_same.entry)
    assert h(basic1_base.entry) != h(basic1_diff.entry)


@test_utils.test()
def test_function_hasher_child_func() -> None:
    h = function_hasher.hash_kernel

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import call_child1_base, call_child1_same, call_child1_diff

    assert h(call_child1_base.entry) == h(call_child1_same.entry)
    assert h(call_child1_base.entry) != h(call_child1_diff.entry)


@test_utils.test()
def test_function_hasher_child_child_func() -> None:
    h = function_hasher.hash_kernel

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import call_child_child1_base, call_child_child1_same, call_child_child1_diff

    assert h(call_child_child1_base.entry) == h(call_child_child1_same.entry)
    assert h(call_child_child1_base.entry) != h(call_child_child1_diff.entry)


@test_utils.test()
def test_function_hasher_child_child_static_func() -> None:
    h = function_hasher.hash_kernel

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import call_child_child_static_base, call_child_child_static_same, call_child_child_static_diff

    assert h(call_child_child_static_base.entry) == h(call_child_child_static_same.entry)
    assert h(call_child_child_static_base.entry) != h(call_child_child_static_diff.entry)
