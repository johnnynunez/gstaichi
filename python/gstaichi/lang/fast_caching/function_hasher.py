from .fast_caching_types import FunctionSourceInfo
from typing import Iterable, Sequence, cast, TYPE_CHECKING
import hashlib


if TYPE_CHECKING:
    from gstaichi.lang.kernel_impl import GsTaichiCallable


def pure(fn: "GsTaichiCallable") -> "GsTaichiCallable":
    fn.is_pure = True
    return fn


def _hash_funcion(function_info: FunctionSourceInfo) -> str:
    with open(function_info.filepath) as f:
        contents = f.read().split("\n")
    lines = contents[function_info.start_lineno: function_info.end_lineno]
    _hash = hashlib.sha256("\n".join(lines).encode('utf-8')).hexdigest()
    return _hash


def hash_functions(function_infos: Iterable[FunctionSourceInfo]) -> list[tuple[FunctionSourceInfo, str]]:
    results = []
    for f_info in function_infos:
        _hash = _hash_funcion(f_info)
        print(f_info.function_name, _hash)
        results.append((f_info, _hash))
    print("len(function_infos)", len(results))
    return results


def hash_kernel(kernel_info: FunctionSourceInfo) -> str:
    return _hash_funcion(kernel_info)
