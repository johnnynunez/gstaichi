"""
I want to migrate all tests to match the directory structure of the code under test,
but let's just start with a few tests using this structure/architecture, as a prototype/PoC.
"""

import ast
import dataclasses
from ast import Attribute, Call, Constant, Load, Name, Subscript
from typing import Any

import pytest

import taichi as ti
import taichi.lang._kernel_impl_dataclass as _kernel_impl_dataclass
import taichi.test_tools.dataclass_test_tools as dataclass_test_tools
from taichi.lang.kernel_arguments import ArgMetadata
from tests import test_utils

__all__ = [
    "Attribute",
    "Name",
    "Load",
    "Call",
    "Subscript",
    "Constant",
]


@dataclasses.dataclass
class MyStructAB:
    a: ti.types.NDArray[ti.i32, 1]
    b: ti.types.NDArray[ti.i32, 1]


@dataclasses.dataclass
class MyStructCD:
    c: ti.types.NDArray[ti.i32, 1]
    d: ti.types.NDArray[ti.i32, 1]
    my_struct_ab: MyStructAB


@dataclasses.dataclass
class MyStructEF:
    e: ti.types.NDArray[ti.i32, 1]
    f: ti.types.NDArray[ti.i32, 1]
    my_struct_cd: MyStructCD


@dataclasses.dataclass
class MyStructFieldAB:
    a: ti.Template
    b: ti.template()


@dataclasses.dataclass
class MyStructFieldCD:
    c: ti.Template
    d: ti.template()
    my_struct_ab: MyStructFieldAB


@dataclasses.dataclass
class MyStructFieldEF:
    e: ti.Template
    f: ti.template()
    my_struct_cd: MyStructFieldCD


@pytest.mark.parametrize(
    "ast_in, struct_locals, expected_ast",
    [
        (
            """
    Attribute(
        value=Name(id='my_struct_ab', ctx=Load()),
        attr='a',
        ctx=Load())""",
            {"__ti_my_struct_ab__ti_a"},
            "Name(id='__ti_my_struct_ab__ti_a', ctx=Load())",
        ),
        (
            """
    Attribute(
        value=Attribute(
            value=Name(id='my_struct_ab', ctx=Load()),
            attr='struct_cd',
            ctx=Load()),
        attr='d',
        ctx=Load())
""",
            {"__ti_my_struct_ab__ti_struct_cd__ti_d"},
            "Name(id='__ti_my_struct_ab__ti_struct_cd__ti_d', ctx=Load())",
        ),
        (
            """
    Attribute(
        value=Attribute(
            value=Attribute(
            value=Name(id='my_struct_ab', ctx=Load()),
            attr='struct_cd',
            ctx=Load()),
            attr='struct_ef',
            ctx=Load()),
        attr='f',
        ctx=Load())""",
            {"__ti_my_struct_ab__ti_struct_cd__ti_struct_ef__ti_f"},
            "Name(id='__ti_my_struct_ab__ti_struct_cd__ti_struct_ef__ti_f', ctx=Load())",
        ),
        (
            """
            Attribute(
              value=Attribute(
                value=Name(id='my_struct_ab', ctx=Load()),
                attr='a',
                ctx=Load()
              ),
              attr='shape',
              ctx=Load()
            )
            """,
            {"__ti_my_struct_ab__ti_a"},
            """
            Attribute(
              value=Name(id='__ti_my_struct_ab__ti_a', ctx=Load()),
              attr='shape',
              ctx=Load()
            )
            """,
        ),
        (
            """
          Call(
            func=Attribute(
              value=Subscript(
                value=Attribute(
                  value=Attribute(
                    value=Name(id='collider_state', ctx=Load()),
                    attr='contact_cache',
                    ctx=Load()),
                  attr='normal',
                  ctx=Load()),
                slice=Constant(value=0),
                ctx=Load()),
              attr='fill',
              ctx=Load()),
                args=[
              Constant(value=0.0)],
            keywords=[])
""",
            {"__ti_collider_state__ti_contact_cache__ti_normal"},
            """
          Call(
            func=Attribute(
              value=Subscript(
                value=Name(id='__ti_collider_state__ti_contact_cache__ti_normal', ctx=Load()),
                slice=Constant(value=0),
                ctx=Load()),
              attr='fill',
              ctx=Load()),
            args=[
              Constant(value=0.0)],
            keywords=[])
""",
        ),
    ],
)
@test_utils.test()
def test_unpack_ast_struct_expressions(ast_in: str, struct_locals: set[str], expected_ast: str) -> None:
    ast_in_obj = eval(ast_in.strip())
    expected_ast_obj = eval(expected_ast.strip())
    new_ast_obj = _kernel_impl_dataclass.unpack_ast_struct_expressions(ast_in_obj, struct_locals)
    print("new_ast_obj", ast.dump(new_ast_obj, indent=2))
    print("expected_ast_obj", ast.dump(expected_ast_obj, indent=2))
    assert ast.dump(new_ast_obj) == ast.dump(expected_ast_obj)


@pytest.mark.parametrize(
    "in_meta, expected_meta",
    [
        (
            [ArgMetadata(MyStructAB, "my_struct_ab")],
            [
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ab__ti_a"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ab__ti_b"),
            ],
        ),
        (
            [ArgMetadata(MyStructCD, "my_struct_cd")],
            [
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_cd__ti_c"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_cd__ti_d"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_cd__ti_my_struct_ab__ti_a"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_cd__ti_my_struct_ab__ti_b"),
            ],
        ),
        (
            [ArgMetadata(MyStructEF, "my_struct_ef")],
            [
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_e"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_f"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_my_struct_cd__ti_c"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_my_struct_cd__ti_d"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_my_struct_cd__ti_my_struct_ab__ti_a"),
                ArgMetadata(ti.types.NDArray[ti.i32, 1], "__ti_my_struct_ef__ti_my_struct_cd__ti_my_struct_ab__ti_b"),
            ],
        ),
    ],
)
@test_utils.test()
def test_expand_func_arguments(in_meta: list[ArgMetadata], expected_meta: list[ArgMetadata]) -> None:
    out_meta = _kernel_impl_dataclass.expand_func_arguments(in_meta)
    print("in_meta", "\n".join([str(m) for m in in_meta]))
    print("out_meta", "\n".join([str(m) for m in out_meta]))
    print("expected_meta", "\n".join([str(m) for m in expected_meta]))
    out_names = [m.name for m in out_meta]
    expected_names = [m.name for m in expected_meta]
    print("out_names", out_names)
    print("expected_names", expected_names)
    assert out_names == expected_names

    out_dtypes = [m.annotation.dtype for m in out_meta]
    expected_dtypes = [m.annotation.dtype for m in expected_meta]
    assert out_dtypes == expected_dtypes


@pytest.mark.parametrize(
    "param_name, param_type, expected_global_args",
    [
        ("my_struct_ab", MyStructAB, {}),
        ("my_struct_cd", MyStructCD, {}),
        (
            "my_struct_ab",
            MyStructFieldAB,
            {
                "__ti_my_struct_ab__ti_a": ti.template,
                "__ti_my_struct_ab__ti_b": ti.template,
            },
        ),
        (
            "my_struct_cd",
            MyStructFieldCD,
            {
                "__ti_my_struct_cd__ti_c": ti.template,
                "__ti_my_struct_cd__ti_d": ti.template,
                "__ti_my_struct_cd__ti_my_struct_ab__ti_a": ti.template,
                "__ti_my_struct_cd__ti_my_struct_ab__ti_b": ti.template,
            },
        ),
        (
            "my_struct_ef",
            MyStructFieldEF,
            {
                "__ti_my_struct_ef__ti_e": ti.template,
                "__ti_my_struct_ef__ti_f": ti.template,
                "__ti_my_struct_ef__ti_my_struct_cd__ti_c": ti.template,
                "__ti_my_struct_ef__ti_my_struct_cd__ti_d": ti.template,
                "__ti_my_struct_ef__ti_my_struct_cd__ti_my_struct_ab__ti_a": ti.template,
                "__ti_my_struct_ef__ti_my_struct_cd__ti_my_struct_ab__ti_b": ti.template,
            },
        ),
    ],
)
@test_utils.test()
def test_populate_global_vars_from_dataclasses(
    param_name: str, param_type: Any, expected_global_args: dict[str, Any]
) -> None:
    py_arg = dataclass_test_tools.build_struct(param_type)
    print("py_arg", py_arg)
    global_vars = {}
    _kernel_impl_dataclass.populate_global_vars_from_dataclass(param_name, param_type, py_arg, global_vars)
    print("global vars names", list(global_vars.keys()))
    expected_names = set(expected_global_args.keys())
    actual_names = set(global_vars.keys())
    print("expected", expected_names)
    print("actual", actual_names)
    assert expected_names == actual_names
    for name in expected_names:
        expected_type = expected_global_args[name]
        actual_obj = global_vars[name]
        if isinstance(expected_type, ti.types.ndarray):
            assert isinstance(actual_obj, ti.ScalarNdarray)
            assert actual_obj.dtype == expected_type.dtype
            assert len(actual_obj.shape) == expected_type.ndim
        elif isinstance(expected_type, ti.Template) or expected_type == ti.Template:
            assert isinstance(actual_obj, ti.Field)
            assert len(actual_obj.shape) == 1
            assert actual_obj.dtype == ti.i32
        else:
            raise Exception("Unexpected expected type", expected_type)
