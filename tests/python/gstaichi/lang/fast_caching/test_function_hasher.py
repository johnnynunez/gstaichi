# import gstaichi as ti
import pytest
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
@pytest.mark.parametrize(
    "set_name", [
        'call_child_child_static', 'call_static_pair', 'call_child_child1', 'call_child1', 'basic1',
        'static_ndrange', 'static_range',
        pytest.param('call_fn_pointer', marks=pytest.mark.xfail),
    ]
)
def test_function_hasher_filesets(set_name: str) -> None:
    """
    we use 'same' vs 'base' to check that the hashes do actually match: we arent just returning a random
    hash, or file-path based hash, or similar
    we use 'diff' vs 'base' to check that we can detect the relevant difference

    files often have commented text such as `# same` or `# base` in. This is to check we aren't just comparing
    the contents of the entire files, but only the functions in question.
    """
    h = function_hasher.hash_kernel
    import sys
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    if test_files_path not in sys.path:
        sys.path.append(test_files_path)
    print(sys.path)

    base = importlib.import_module(f"{set_name}_base")
    same = importlib.import_module(f"{set_name}_same")
    diff = importlib.import_module(f"{set_name}_diff")

    assert h(base.entry) == h(same.entry)
    assert h(base.entry) != h(diff.entry)

    sys.path.remove(test_files_path)
