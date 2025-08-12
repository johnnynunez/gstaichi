import gstaichi as ti
from tests import test_utils
import sys
import importlib
from gstaichi.lang.fast_caching import src_hasher
from gstaichi._test_tools import ti_init_same_arch
from gstaichi.lang._wrap_inspect import get_source_info_and_src


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
