import os
import pathlib
from typing import Callable
import gstaichi as ti
import pytest
import shutil
import importlib
from tests import test_utils

from gstaichi.lang.fast_caching import function_hasher
from gstaichi.lang import _wrap_inspect
from gstaichi.lang.fast_caching.fast_caching_types import HashedFunctionSourceInfo


# @test_utils.test()
# def test_function_hasher_simple() -> None:
#     class one:
#         @staticmethod
#         def foo(a: int, b: int):
#             return a + b

#         @staticmethod
#         def foo2(a: int, b: int):
#             return a + b

#     class two:
#         @staticmethod
#         def foo(a: int, b: int):
#             return a + b

#         @staticmethod
#         def foo2(a: int, b: int):
#             return a + b

#     class diff1:
#         @staticmethod
#         def foo(a: int, b: int):
#             return a + b + 3

#         @staticmethod
#         def foo2(a: int, b: int):
#             return a + b + 5

#     class diff2:
#         @staticmethod
#         def foo(a: int, b: float):
#             return a + b

#     h = function_hasher.hash_kernel
#     print(h(one.foo))
#     print(h(two.foo))
#     print(h(one.foo))
#     print(h(two.foo))
#     print(h(one.foo2))
#     print(h(two.foo2))

#     assert h(one.foo) == h(two.foo)
#     assert h(one.foo2) == h(two.foo2)
#     assert h(one.foo) != h(two.foo2)

#     assert h(one.foo) != h(diff1.foo)
#     assert h(one.foo2) != h(diff1.foo2)

#     assert h(one.foo) != h(diff2.foo)


# @test_utils.test()
# @pytest.mark.parametrize(
#     "set_name", [
#         'call_child_child_static', 'call_static_pair', 'call_child_child1', 'call_child1', 'basic1',
#         'static_ndrange', 'static_range',
#         pytest.param('call_fn_pointer', marks=pytest.mark.xfail),
#     ]
# )
# def test_function_hasher_filesets(set_name: str) -> None:
#     """
#     we use 'same' vs 'base' to check that the hashes do actually match: we arent just returning a random
#     hash, or file-path based hash, or similar
#     we use 'diff' vs 'base' to check that we can detect the relevant difference

#     files often have commented text such as `# same` or `# base` in. This is to check we aren't just comparing
#     the contents of the entire files, but only the functions in question.
#     """
#     h = function_hasher.hash_kernel
#     import sys
#     test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
#     if test_files_path not in sys.path:
#         sys.path.append(test_files_path)
#     print(sys.path)

#     base = importlib.import_module(f"{set_name}_base")
#     same = importlib.import_module(f"{set_name}_same")
#     diff = importlib.import_module(f"{set_name}_diff")

#     assert h(base.entry) == h(same.entry)
#     assert h(base.entry) != h(diff.entry)

#     sys.path.remove(test_files_path)



@test_utils.test()
def test_function_hasher_hash_kernel() -> None:
    import sys
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    if test_files_path not in sys.path:
        sys.path.append(test_files_path)

    f1_base = importlib.import_module("f1_base")
    f1_same = importlib.import_module("f1_same")
    f1_diff = importlib.import_module("f1_diff")

    f1_base_info, _src = _wrap_inspect.get_source_info_and_src(f1_base.f1.fn)
    f1_base_hash = function_hasher.hash_kernel(f1_base_info)

    f1_same_info, _src = _wrap_inspect.get_source_info_and_src(f1_same.f1.fn)
    f1_same_hash = function_hasher.hash_kernel(f1_same_info)

    f1_diff_info, _src = _wrap_inspect.get_source_info_and_src(f1_diff.f1.fn)
    f1_diff_hash = function_hasher.hash_kernel(f1_diff_info)

    assert f1_base_hash is not None and f1_base_hash != ""
    assert f1_base_hash == f1_same_hash
    assert f1_base_hash != f1_diff_hash

    sys.path.remove(test_files_path)


@test_utils.test()
def test_function_hasher_hash_functions() -> None:
    import sys
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    if test_files_path not in sys.path:
        sys.path.append(test_files_path)

    f1_base = importlib.import_module("f1_base")
    f1_same = importlib.import_module("f1_same")
    f1_diff = importlib.import_module("f1_diff")

    f1_base_info, _src = _wrap_inspect.get_source_info_and_src(f1_base.f1.fn)
    f1_base_hashed_infos = function_hasher.hash_functions([f1_base_info])

    f1_same_info, _src = _wrap_inspect.get_source_info_and_src(f1_same.f1.fn)
    f1_same_hashed_infos = function_hasher.hash_functions([f1_same_info])

    f1_diff_info, _src = _wrap_inspect.get_source_info_and_src(f1_diff.f1.fn)
    f1_diff_hashed_infos = function_hasher.hash_functions([f1_diff_info])

    assert len(f1_base_hashed_infos) == len(f1_same_hashed_infos) == len(f1_diff_hashed_infos) == 1
    assert f1_base_hashed_infos[0].hash is not None and f1_base_hashed_infos[0].hash != ""
    assert f1_base_hashed_infos[0].hash == f1_same_hashed_infos[0].hash
    assert f1_base_hashed_infos[0].hash != f1_diff_hashed_infos[0].hash

    sys.path.remove(test_files_path)


@test_utils.test()
def test_function_hasher_validate_hashed_function_infos(tmp_path: pathlib.Path) -> None:
    import sys
    test_files_path = pathlib.Path("tests/python/gstaichi/lang/fast_caching/test_files")
    sys.path.append(str(tmp_path))

    def setup_folder(filename: str) -> None:
        shutil.copy2(test_files_path / filename, tmp_path / "child_diff.py")

    setup_folder("child_diff_base.py")
    mod = importlib.import_module("child_diff")

    def get_fileinfos(functions: list[Callable]) -> list[_wrap_inspect.FunctionSourceInfo]:
        fileinfos = []
        for f in functions:
            file_info, _src = _wrap_inspect.get_source_info_and_src(f)
            fileinfos.append(file_info)
        return fileinfos

    fileinfos = get_fileinfos([mod.f1.fn, mod.f2.fn])
    hashed_fileinfos = function_hasher.hash_functions(fileinfos)
    assert function_hasher.validate_hashed_function_infos(hashed_fileinfos)

    setup_folder("child_diff_same.py")
    assert function_hasher.validate_hashed_function_infos(hashed_fileinfos)

    setup_folder("child_diff_diff.py")
    assert not function_hasher.validate_hashed_function_infos(hashed_fileinfos)

    sys.path.remove(str(tmp_path))
