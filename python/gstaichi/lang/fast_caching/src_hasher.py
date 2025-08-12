import json
from typing import Any, Callable, Iterable, Sequence
from . import args_hasher, function_hasher
from gstaichi.lang import impl
from .fast_caching_types import FunctionSourceInfo, HashedFunctionSourceInfo
from gstaichi.lang import impl
from .hash_utils import hash_string
from .pyside_cache import PysideCache
import pydantic
import dataclasses
from pydantic import BaseModel



# def hash_source(kernel_source_info: FunctionSourceInfo, function_source_infos: Sequence[FunctionSourceInfo], args: Sequence[Any]) -> str | None:
#     """
#     create a cache key from kernel_source_info, function_source_infos and args, if possible (ie no args that violate constraints etc)
#     if anything about the function or args violates enforced constraints, then return None instead
#     of cache key

#     This function will get hash values for each of the fucntion source infos, and store these in a python side
#     cache, for verifiaction later
#     """
#     cache_key = create_cache_key(kernel_source_info, args)
#     if not cache_key:
#         return None
#     hashed_function_infos = function_hasher.hash_functions(function_source_infos)
#     store(kernel_source_info, args, hashed_function_infos)
#     print("cache_key", cache_key)
#     return cache_key


# def hash_source(fn: Callable, args: Sequence[Any]) -> str | None:
#     args_hash = args_hasher.hash_args(args)
#     if args_hash is None:
#         return None
#     return None
#     return args_hash
#     # fn_hash = function_hasher.hash_kernel(fn)
#     # if fn_hash is None:
#     #     return None
#     # src_hash = hashlib.sha256(f"{fn_hash}_{args_hash}_{impl.current_cfg().arch.name}".encode('utf-8')).hexdigest()
#     # return src_hash


def create_cache_key(kernel_source_info: FunctionSourceInfo, args: Sequence[Any]) -> str | None:
    """
    cache key takes into account:
    - arg types
    - kernel function (but not sub functions)
    """
    args_hash = args_hasher.hash_args(args)
    # print("args_hash", args_hash)
    if args_hash is None:
        return None
    # print("kernel_source_info", kernel_source_info)
    kernel_hash = function_hasher.hash_kernel(kernel_source_info)
    arch = impl.get_runtime().prog.config().arch
    cache_key = hash_string(f"{kernel_hash}_{args_hash}_{arch}")
    return cache_key


class CacheValue(BaseModel):
    # kernel_source_info: FunctionSourceInfo
    hashed_function_source_infos: list[HashedFunctionSourceInfo]


def store(cache_key: str, function_source_infos: Iterable[FunctionSourceInfo]) -> None:
    """
    Note that unlike other caches, this cache is not going to store the actual value we want. This cache is only used for verification
    that our cache key is valid. Big picture:
    - we have a cache key, based on args and top level kernel function
    - we want to use this to look up LLVM IR, in C++ side cache
    - however, before doing that, we first want to validate that the source code didn't change
        - i.e. is our cache key still valid?
    - the python side cache contains information we will use to verify that our cache key is valid
        - ie the list of function source infos
    """
    # cache_key = create_cache_key(kernel_source_info, args)
    if not cache_key:
        return
    cache = PysideCache()
    hashed_function_source_infos = function_hasher.hash_functions(function_source_infos)
    cache_value_obj = CacheValue(hashed_function_source_infos=list(hashed_function_source_infos))
    cache_value_json = cache_value_obj.json()
    cache.store(cache_key, cache_value_json)


def try_load(cache_key: str) -> Sequence[HashedFunctionSourceInfo] | None:
    cache = PysideCache()
    maybe_cache_value_json = cache.try_load(cache_key)
    if maybe_cache_value_json is None:
        return None
    cache_value_obj = CacheValue.parse_raw(maybe_cache_value_json)
    return cache_value_obj.hashed_function_source_infos


def validate_cache_key(cache_key: str) -> bool:
    """
    loads function source infos from cache, if available
    checks the hashes against the current source code
    """
    maybe_hashed_function_source_infos = try_load(cache_key)
    if not maybe_hashed_function_source_infos:
        return False
    for function_info in maybe_hashed_function_source_infos:
        if not function_hasher.validate_hashed_function_info(function_info):
            return False
    return True


def dump_stats() -> None:
    print("dump stats")
    args_hasher.dump_stats()
    function_hasher.dump_stats()
