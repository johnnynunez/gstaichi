import os
from .fast_caching_types import FunctionSourceInfo, HashedFunctionSourceInfo
from typing import Iterable, Sequence, cast, TYPE_CHECKING
# import hashlib
from .hash_utils import hash_string


if TYPE_CHECKING:
    from gstaichi.lang.kernel_impl import GsTaichiCallable


def pure(fn: "GsTaichiCallable") -> "GsTaichiCallable":
    fn.is_pure = True
    return fn


def _hash_function(function_info: FunctionSourceInfo) -> str:
    with open(function_info.filepath) as f:
        contents = f.read().split("\n")
    lines = contents[function_info.start_lineno: function_info.end_lineno]
    _hash = hash_string("\n".join(lines))
    return _hash


def hash_functions(function_infos: Iterable[FunctionSourceInfo]) -> list[HashedFunctionSourceInfo]:
    results = []
    for f_info in function_infos:
        _hash = _hash_function(f_info)
        print(f_info.function_name, _hash)
        results.append(HashedFunctionSourceInfo(function_source_info=f_info, hash=_hash))
        # f_info.hash = _hash
    print("len(function_infos)", len(results))
    return results


def hash_kernel(kernel_info: FunctionSourceInfo) -> str:
    return _hash_function(kernel_info)


def dump_stats() -> None:
    print('function hasher dump stats')


def validate_hashed_function_info(hashed_function_info: HashedFunctionSourceInfo) -> bool:
    """
    Checks the hash
    """
    if not os.path.isfile(hashed_function_info.function_source_info.filepath):
        return False
    _hash = _hash_function(hashed_function_info.function_source_info)
    return _hash == hashed_function_info.hash
