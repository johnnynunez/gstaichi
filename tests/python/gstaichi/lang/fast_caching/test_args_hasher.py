from typing import Any
import gstaichi as ti
from tests import test_utils
import numpy as np
import pytest
from gstaichi.lang.fast_caching import args_hasher


@test_utils.test()
def test_args_hasher_numeric() -> None:
    seen = set()
    for arg in [3, 5.3, np.int32(3), np.int64(5), np.float32(2), np.float64(2)]:
        for it in [0, 1]:
            hash = args_hasher.hash_args([arg])
            assert hash is not None
            if it == 0:
                assert hash not in seen
                seen.add(hash)
            else:
                assert hash in seen


@test_utils.test()
def test_args_hasher_unsupported() -> None:
    for arg in [
        ti.math.vec3(0, 0, 0),
        ti.math.mat3([0] * 9),
        ti.ndarray(ti.types.vector(3, ti.i32), (3,)),
        ti.field(ti.types.vector(3, ti.i32), (3,))
    ]:
        # for now, we don't support, so hash should be None
        hash = args_hasher.hash_args([arg])
        assert hash is None


@test_utils.test()
def test_args_hasher_ndarray() -> None:
    seen = set()
    for dtype in [ti.i32, ti.i64, ti.f32, ti.f64]:
        for ndim in [0, 1, 2]:
            arg = ti.ndarray(dtype, [1] * ndim)
            for it in [0, 1]:
                hash = args_hasher.hash_args([arg])
                assert hash is not None
                if it == 0:
                    assert hash not in seen
                    seen.add(hash)
                else:
                    assert hash in seen


@test_utils.test()
def test_args_hasher_field() -> None:
    seen = set()
    for dtype in [ti.i32, ti.i64, ti.f32, ti.f64]:
        for ndim in [0, 1, 2]:
            arg = ti.field(dtype, [1] * ndim)
            for it in [0, 1]:
                hash = args_hasher.hash_args([arg])
                assert hash is not None
                if it == 0:
                    assert hash not in seen
                    seen.add(hash)
                else:
                    assert hash in seen


@test_utils.test()
def test_args_hasher_field_vs_ndarray() -> None:
    a_ndarray = ti.ndarray(ti.i32, 1)
    a_field = ti.field(ti.i32, 1)
    ndarray_hash = args_hasher.hash_args([a_ndarray])
    field_hash = args_hasher.hash_args([a_field])
    assert ndarray_hash is not None
    assert field_hash is not None
    assert ndarray_hash != field_hash
