import importlib
import pathlib
import shutil
from typing import Callable

from gstaichi.lang import _wrap_inspect
from gstaichi.lang.fast_caching import function_hasher
from gstaichi.lang.fast_caching.fast_caching_types import HashedFunctionSourceInfo

from tests import test_utils


@test_utils.test()
def test_function_hasher_hash_kernel(monkeypatch) -> None:
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    monkeypatch.syspath_prepend(test_files_path)

    def get_hash(name: str) -> _wrap_inspect.FunctionSourceInfo:
        mod = importlib.import_module(name)
        info, _src = _wrap_inspect.get_source_info_and_src(mod.f1.fn)
        hash = function_hasher.hash_kernel(info)
        return hash

    f1_base_hash = get_hash("f1_base")
    f1_same_hash = get_hash("f1_same")
    f1_diff_hash = get_hash("f1_diff")

    assert f1_base_hash is not None and f1_base_hash != ""
    assert f1_base_hash == f1_same_hash
    assert f1_base_hash != f1_diff_hash


@test_utils.test()
def test_function_hasher_hash_functions(monkeypatch) -> None:
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    monkeypatch.syspath_prepend(test_files_path)

    def get_infos(name: str) -> list[HashedFunctionSourceInfo]:
        mod = importlib.import_module(name)
        info, _src = _wrap_inspect.get_source_info_and_src(mod.f1.fn)
        hashed_infos = function_hasher.hash_functions([info])
        return hashed_infos

    f1_base_hashed_infos = get_infos("f1_base")
    f1_same_hashed_infos = get_infos("f1_same")
    f1_diff_hashed_infos = get_infos("f1_diff")

    assert len(f1_base_hashed_infos) == len(f1_same_hashed_infos) == len(f1_diff_hashed_infos) == 1
    assert f1_base_hashed_infos[0].hash is not None and f1_base_hashed_infos[0].hash != ""
    assert f1_base_hashed_infos[0].hash == f1_same_hashed_infos[0].hash
    assert f1_base_hashed_infos[0].hash != f1_diff_hashed_infos[0].hash


@test_utils.test()
def test_function_hasher_validate_hashed_function_infos(monkeypatch, tmp_path: pathlib.Path) -> None:
    test_files_path = pathlib.Path("tests/python/gstaichi/lang/fast_caching/test_files")
    monkeypatch.syspath_prepend(str(tmp_path))

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

    setup_folder("child_diff_same.py")
    assert function_hasher.validate_hashed_function_infos(hashed_fileinfos)
