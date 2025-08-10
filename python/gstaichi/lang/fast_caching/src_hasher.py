import hashlib
from typing import Any, Callable, Sequence
from . import function_hacher, args_hasher


def hash_source(fn: Callable, args: Sequence[Any]) -> str:
    args_hash = args_hasher.hash_args(args)
    fn_hash = function_hacher.hash_kernel(fn)
    src_hash = hashlib.sha256(f"{fn_hash}_{args_hash}".encode('utf-8')).hexdigest()
    return src_hash
