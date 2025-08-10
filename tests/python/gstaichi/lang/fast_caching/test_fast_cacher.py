import gstaichi as ti
import pytest
from tests import test_utils

from gstaichi.lang.fast_caching import fast_cacher


@test_utils.test()
def test_fast_cacher_simple() -> None:
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

    fc = fast_cacher.FastCacher()
    print(fc._hash_function(one.foo))
    print(fc._hash_function(two.foo))
    print(fc._hash_function(one.foo))
    print(fc._hash_function(two.foo))
    print(fc._hash_function(one.foo2))
    print(fc._hash_function(two.foo2))

    h = fc._hash_function

    assert h(one.foo) == h(two.foo)
    assert h(one.foo2) == h(two.foo2)
    assert h(one.foo) != h(two.foo2)

    assert h(one.foo) != h(diff1.foo)
    assert h(one.foo2) != h(diff1.foo2)

    assert h(one.foo) != h(diff2.foo)


@test_utils.test()
@pytest.mark.xfail(reason="Not implemented yet")
def test_fast_cacher_reject_template() -> None:
    """
    Templates will be allowed at some point, but for now should cause rejection of fast caching
    """
    class one:
        @staticmethod
        def foo(a: int, b: ti.Template) -> int:
            return a + b[0]

    fc = fast_cacher.FastCacher()

    h = fc._hash_function

    assert h(one.foo) is None


@test_utils.test()
@pytest.mark.xfail(reason="Not implemented yet")
def test_fast_cacher_reject_missing_ndarray_typing() -> None:
    """
    NDarray should state clearly the element type and number of dimensions
    """
    class one:
        @staticmethod
        def foo(a: int, b: ti.types.NDArray) -> int:
            return a + b[0]

    fc = fast_cacher.FastCacher()

    h = fc._hash_function

    assert h(one.foo) is None


@test_utils.test()
def test_fast_cacher_ndarray_ndim_mismatch() -> None:
    """
    NDarray ndim and type should match, otherwise has should be different

    Seems this is supported naturally, since the source code is different.
    """
    class one:
        @staticmethod
        def foo(a: int, b: ti.types.NDArray[ti.i32, 1]) -> int:
            return a + b[0]

    class should_match:
        @staticmethod
        def foo(a: int, b: ti.types.NDArray[ti.i32, 1]) -> int:
            return a + b[0]

    class diff_ndim:
        @staticmethod
        def foo(a: int, b: ti.types.NDArray[ti.i32, 2]) -> int:
            return a + b[0]

    class diff_type:
        @staticmethod
        def foo(a: int, b: ti.types.NDArray[ti.f32, 1]) -> int:
            return a + b[0]

    fc = fast_cacher.FastCacher()
    h = fc._hash_function

    assert h(one.foo) == h(should_match.foo)
    assert h(one.foo) != h(diff_ndim.foo)
    assert h(one.foo) != h(diff_type.foo)


@test_utils.test()
def test_fast_cacher_using_test_files() -> None:
    fc = fast_cacher.FastCacher()
    h = fc._hash_function

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import basic1_base, basic1_same, basic1_diff
    print(h(basic1_base.entry))
    print(h(basic1_same.entry))
    print(h(basic1_diff.entry))

    assert h(basic1_base.entry) == h(basic1_same.entry)
    assert h(basic1_base.entry) != h(basic1_diff.entry)


@test_utils.test()
def test_fast_cacher_child_func() -> None:
    # fc = fast_cacher.FastCacher()
    h = fast_cacher.hash_kernel

    import sys
    sys.path.append("tests/python/gstaichi/lang/fast_caching/test_files")
    import call_child1_base, call_child1_same, call_child1_diff
    # print(call_child1_base.entry)
    print(h(call_child1_base.entry))
    # print(call_child1_base.entry)
    print(h(call_child1_base.entry))
    # print(call_child1_base.entry)
    print(h(call_child1_same.entry))
    print(h(call_child1_same.entry))
    print(h(call_child1_diff.entry))
    print(h(call_child1_diff.entry))

    print(h(call_child1_base.entry))
    print(h(call_child1_same.entry))
    print(h(call_child1_diff.entry))

    assert h(call_child1_base.entry) == h(call_child1_same.entry)
    assert h(call_child1_base.entry) != h(call_child1_diff.entry)
