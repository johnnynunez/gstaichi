import gstaichi as ti
from tests import test_utils
import sys
import importlib
from gstaichi.lang.fast_caching import src_hasher
from gstaichi._test_tools import ti_init_same_arch
from gstaichi.lang._wrap_inspect import get_source_info_and_src
from gstaichi.lang.fast_caching import function_hasher
from gstaichi.lang import _wrap_inspect
from gstaichi.lang.fast_caching.fast_caching_types import HashedFunctionSourceInfo


@test_utils.test()
def test_create_cache_key_vary_config() -> None:
    @ti.kernel
    def f1() -> None:
        pass

    ti_init_same_arch()
    kernel_info, _src = get_source_info_and_src(f1.fn)
    cache_key_base = src_hasher.create_cache_key(kernel_info, [])

    ti_init_same_arch()
    kernel_info, _src = get_source_info_and_src(f1.fn)
    cache_key_same = src_hasher.create_cache_key(kernel_info, [])

    ti_init_same_arch(options={"offline_cache_max_size_of_files": 123})
    kernel_info, _src = get_source_info_and_src(f1.fn)
    cache_key_diff = src_hasher.create_cache_key(kernel_info, [])

    assert cache_key_base == cache_key_same
    assert cache_key_same != cache_key_diff


@test_utils.test()
def test_create_cache_key_vary_fn(monkeypatch) -> None:
    test_files_path = "tests/python/gstaichi/lang/fast_caching/test_files"
    monkeypatch.syspath_prepend(test_files_path)

    def get_cache_key(name: str) -> _wrap_inspect.FunctionSourceInfo:
        mod = importlib.import_module(name)
        info, _src = _wrap_inspect.get_source_info_and_src(mod.f1.fn)
        cache_key = src_hasher.create_cache_key(info, [])
        return cache_key

    key_base = get_cache_key("f1_base")
    print(key_base)
    key_same = get_cache_key("f1_same")
    print(key_same)
    key_diff = get_cache_key("f1_diff")
    print(key_diff)

    assert key_base is not None
    assert key_base != ""
    assert key_base == key_same
    assert key_base != key_diff
