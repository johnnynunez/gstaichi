from .fast_caching_types import FunctionSourceInfo
from typing import Iterable, Sequence, cast, TYPE_CHECKING
import hashlib


if TYPE_CHECKING:
    from gstaichi.lang.kernel_impl import GsTaichiCallable


def pure(fn: "GsTaichiCallable") -> "GsTaichiCallable":
    fn.is_pure = True
    return fn


def hash_functions(function_infos: Iterable[FunctionSourceInfo]) -> list[tuple[FunctionSourceInfo, str]]:
    results = []
    for f_info in function_infos:
        # print('-------------------------')
        with open(f_info.filepath) as f:
            contents = f.read().split("\n")
        lines = contents[f_info.start_lineno: f_info.end_lineno]
        # print('lines[')
        # print("\n".join(lines))
        # print(']')
        _hash = hashlib.sha256("\n".join(lines).encode('utf-8')).hexdigest()
        print(f_info.function_name, _hash)
        results.append((f_info, _hash))
    print("len(function_infos)", len(results))
    return results
