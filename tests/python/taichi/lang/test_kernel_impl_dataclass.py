"""
I want to migrate all tests to match the directory structure of the code under test,
but let's just start with a few tests using this structure/architecture, as a prototype/PoC.
"""
from tests import test_utils
import ast
import pytest
from ast import (
    Attribute,
    Name,
    Load
)
import taichi.lang._kernel_impl_dataclass as _kernel_impl_dataclass


__all__ = [
    'Attribute',
    'Name',
    'Load',
]


@pytest.mark.parametrize(
    "ast_in, struct_locals, expected_ast", [
        (
            """
    Attribute(
        value=Name(id='my_struct_ab', ctx=Load()),
        attr='a',
        ctx=Load())""",
        {"__ti_my_struct_ab__ti_a"},
        "Name(id='__ti_my_struct_ab__ti_a', ctx=Load())"
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
        "Name(id='__ti_my_struct_ab__ti_struct_cd__ti_d', ctx=Load())"
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
        "Name(id='__ti_my_struct_ab__ti_struct_cd__ti_struct_ef__ti_f', ctx=Load())"
        ),
    ]
)
@test_utils.test()
def test_unpack_ast_struct_expressions(ast_in: str, struct_locals: set[str], expected_ast: str) -> None:
    ast_in_obj = eval(ast_in.strip())
    expected_ast_obj = eval(expected_ast.strip())
    new_ast_obj = _kernel_impl_dataclass.unpack_ast_struct_expressions(ast_in_obj, struct_locals)
    assert ast.dump(new_ast_obj) == ast.dump(expected_ast_obj)
