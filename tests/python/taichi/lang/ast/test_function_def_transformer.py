from typing import Any, cast
import pytest
import taichi as ti
import ast
import pytest
from taichi.lang.ast.function_def_transformer import FunctionDefTransformer
from tests import test_utils
import dataclasses


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


class NDArrayBuilder:
    def __init__(self, dtype: Any, shape: tuple[int, ...]) -> None:
        self.dtype = dtype
        self.shape = shape
    
    def build(self) -> ti.types.NDArray:
        return ti.ndarray(self.dtype, self.shape)


def build_struct(struct_type: Any) -> Any:
    member_objects = {}
    for field in dataclasses.fields(struct_type):
        if isinstance(field.type, ti.types.NDArray):
            print("got ndarray")
            ndarray_type = cast(ti.types.ndarray, field.type)
            shape = tuple([10] * ndarray_type.ndim)
            child_obj = ti.ndarray(ndarray_type.dtype, shape=shape)
        elif dataclasses.is_dataclass(field.type):
            child_obj = build_struct(field.type)
        else:
            raise Exception("unknown type ", field.type)
        member_objects[field.name] = child_obj
    # DataclassClass = dataclasses.make_dataclass(struct_name, declaration_type_by_name)
    dataclass_object = struct_type(**member_objects)
    return dataclass_object


@pytest.mark.parametrize(
    "argument_name, argument_type, expected_variables", [
        (
            "my_struct_1",
            MyStructAB,
            {
                "__ti_my_struct_1__ti_a": ti.types.NDArray[ti.i32, 1],
                "__ti_my_struct_1__ti_b": ti.types.NDArray[ti.i32, 1],
            }
        ),
    ]
)
@test_utils.test()
def test_process_func_arg(argument_name: str, argument_type: Any, expected_variables: dict[str, Any]) -> None:
    class MockContext:
        def __init__(self) -> None:
            self.variables: dict[str, Any] = {}

        def create_variable(self, name: str, data: Any) -> None:
            assert name not in self.variables
            self.variables[name] = data
    
    data = build_struct(argument_type)
    print("data", data)
    ctx = MockContext()
    FunctionDefTransformer._process_func_arg(
        ctx,
        argument_name,
        argument_type,
        data,
    )
    print("output variables", ctx.variables)
    print("epected variables", expected_variables)
    # since these should both be flat, we can just loop over both
    assert set(ctx.variables.keys()) == set(expected_variables.keys())
