import taichi as ti
import ast
import pytest
from taichi.lang.ast.call_transformer import CallTransformer
from tests import test_utils
import dataclasses


@dataclasses.dataclass
class MyStructAB:
    a: ti.types.NDArray[ti.i32, 1]
    b: ti.types.NDArray[ti.i32, 1]


def dump_ast_list(nodes: list[ast.AST]) -> str:
    res_l = []
    for node in nodes:
        res_l.append(ast.dump(node, indent=2))
    return "[\n" + ",\n".join(res_l) + "\n]"


@pytest.mark.parametrize(
    "args_in, expected_args_out", [
        (
        [
            ast.Name(id='my_struct_ab', ctx=ast.Load(), ptr=MyStructAB)
        ],
        [
            ast.Name(id='__ti_my_struct_ab__ti_a', ctx=ast.Load()),
            ast.Name(id='__ti_my_struct_ab__ti_b', ctx=ast.Load()),
        ]
        ),
    ]
)
@test_utils.test()
def test_expand_Call_dataclass_args(args_in: list[ast.AST], expected_args_out: list[ast.AST]) -> None:
    for arg in args_in:
        arg.lineno = 1
        arg.endlineno = 2
        arg.col_offset = 1
        arg.end_col_offset = 2
    # args_in_obj = ast.Call(
    #     func=ast.Name(id='f2', ctx=ast.Load()),
    #     args=[
    #         ast.Name(id='my_struct_b', ctx=ast.Load(), ptr=123)
    #     ],
    #     keywords=[]
    # )
    print("args_in", dump_ast_list(args_in))
    # print("args_in_obj", ast.dump(args_in, indent=2))
    print("args_in_obj.args[0].ptr", args_in[0].ptr)
    # args_in_obj = eval(args_in)
    # expected_args_out_obj = eval(expected_args_out)
    args_out = CallTransformer._expand_Call_dataclass_args(args_in)
    print("args_in", dump_ast_list(args_in))
    print("args_out", dump_ast_list(args_out))
    print("expected_args_out", dump_ast_list(expected_args_out))
    # print("args_in", ast.dump(args_in, indent=2))
    # print("expected_args", ast.dump(expected_args_out, indent=2))
    # print("args_out", ast.dump(args_out, indent=2))
    assert dump_ast_list(expected_args_out) == dump_ast_list(args_out)
