import hashlib
from typing import Any, Callable, Sequence
from . import args_hasher, function_hasher
from gstaichi.lang import impl


def hash_source(fn: Callable, args: Sequence[Any]) -> str | None:
    args_hash = args_hasher.hash_args(args)
    if args_hash is None:
        return None
    fn_hash = function_hasher.hash_kernel(fn)
    if fn_hash is None:
        return None
    src_hash = hashlib.sha256(f"{fn_hash}_{args_hash}_{impl.current_cfg().arch.name}".encode('utf-8')).hexdigest()
    return src_hash


def dump_stats() -> None:
    print("dump stats")
    args_hasher.dump_stats()
    function_hasher.dump_stats()
