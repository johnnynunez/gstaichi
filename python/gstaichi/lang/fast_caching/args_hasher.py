import hashlib
from typing import Any, Sequence
from gstaichi.types.compound_types import vector, matrix
import numpy as np
from gstaichi.lang._ndarray import ScalarNdarray
from gstaichi.lang.matrix import VectorNdarray
from gstaichi.lang.field import ScalarField


def to_representative_str(arg: Any) -> str | None:
    """
    string should somehow represent the type of arg. Doesnt have to be hashed, nor does it have
    to be the actual python type string, just something representative of the type, and won't collide
    with different (allowed) types
    """
    arg_type = type(arg)
    if arg_type in [int, float, np.float32, np.float64, np.int32, np.int64]:
        return str(arg_type)
    if arg_type in [vector, matrix]:
        return None
    if arg_type == ScalarNdarray:
        assert isinstance(arg, ScalarNdarray)
        return f"[ndarray-{arg.dtype}-{len(arg.shape)}]"
    if arg_type == VectorNdarray:
        assert isinstance(arg, VectorNdarray)
        return f"[ndarray-vec-{arg.n}-{arg.dtype}-{len(arg.shape)}]"
    if arg_type == ScalarField:
        assert isinstance(arg, ScalarField)
        return f"[field-{arg.snode._id}-{arg.dtype}-{arg.shape}]"
    return None


def hash_args(args: Sequence[Any]) -> str | None:
    hash_l = []
    for arg in args:
        _hash = to_representative_str(arg)
        if not _hash:
            return None
        hash_l.append(_hash)
    return hashlib.sha256("_".join(hash_l).encode('utf-8')).hexdigest()
