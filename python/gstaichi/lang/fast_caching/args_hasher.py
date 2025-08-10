import hashlib
import time
from typing import Any, Sequence
from gstaichi.types.compound_types import vector, matrix
import numpy as np
from gstaichi.lang._ndarray import ScalarNdarray
from gstaichi.lang.matrix import VectorNdarray, MatrixNdarray, MatrixField
from gstaichi.lang.field import ScalarField
import torch


g_num_calls = 0
g_num_args = 0
g_hashing_time = 0
g_repr_time = 0
g_num_ignored_calls = 0


def to_representative_str(arg: Any) -> str | None:
    """
    string should somehow represent the type of arg. Doesnt have to be hashed, nor does it have
    to be the actual python type string, just something representative of the type, and won't collide
    with different (allowed) types
    """
    arg_type = type(arg)
    if isinstance(arg, ScalarNdarray):
        return f"[nd-{arg.dtype}-{len(arg.shape)}]"
    if isinstance(arg, VectorNdarray):
        return f"[ndv-{arg.n}-{arg.dtype}-{len(arg.shape)}]"
    if isinstance(arg, ScalarField):
        return f"[f-{arg.snode._id}-{arg.dtype}-{arg.shape}]"
    if isinstance(arg, MatrixNdarray):
        return f"[ndm-{arg.m}-{arg.n}-{arg.dtype}-{len(arg.shape)}]"
    if isinstance(arg, torch.Tensor):
        return f"[pt-{arg.dtype}-{arg.ndim}]"
    if isinstance(arg, np.ndarray):
        return f"[np-{arg.dtype}-{arg.ndim}]"
    if isinstance(arg, MatrixField):
        return f"[fm-{arg.m}-{arg.n}-{arg.snode._id}-{arg.dtype}-{arg.shape}]"
    if arg_type in [int, float, np.float32, np.float64, np.int32, np.int64]:
        return str(arg_type)
    print("arg not recognized", type(arg))
    return None
    # return "#"


def hash_args(args: Sequence[Any]) -> str | None:
    global g_num_calls, g_num_args, g_hashing_time, g_repr_time, g_num_ignored_calls
    g_num_calls += 1
    g_num_args += len(args)
    hash_l = []
    for arg in args:
        start = time.time()
        _hash = to_representative_str(arg)
        g_repr_time += time.time() - start
        if not _hash:
            g_num_ignored_calls += 1
            return None
        hash_l.append(_hash)
    start = time.time()
    res = hashlib.sha256("_".join(hash_l).encode('utf-8')).hexdigest()
    g_hashing_time += time.time() - start
    return res


def dump_stats() -> None:
    print("args hasher dump stats")
    print("total calls", g_num_calls)
    print("ignored calls", g_num_ignored_calls)
    print("total args", g_num_args)
    print("hashing time", g_hashing_time)
    print("arg representation time", g_repr_time)
