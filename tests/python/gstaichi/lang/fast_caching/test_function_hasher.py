# import gstaichi as ti
# import pytest
import importlib
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
def test_function_hasher_filesets() -> None:
    h = function_hasher.hash_kernel
    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")

    for set in [
        'call_child_child_static', 'call_static_pair', 'call_child_child1', 'call_child1', 'basic1',
        'static_ndrange',
    ]:
        base = importlib.import_module(f"{set}_base")
        same = importlib.import_module(f"{set}_same")
        diff = importlib.import_module(f"{set}_diff")

        assert h(base.entry) == h(same.entry)
        assert h(base.entry) != h(diff.entry)
