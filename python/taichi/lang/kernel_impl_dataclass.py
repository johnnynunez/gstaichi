import ast
import dataclasses
import inspect
from taichi.lang.ast import (
    ASTTransformerContext,
)
from taichi.lang.kernel_arguments import KernelArgument


def _populate_struct_locals_from_params_dict(basename: str, struct_locals, struct_type) -> None:
    """
    We are populating struct locals from a type included in function parameters, or one of their subtypes

    struct_locals will be a list of all possible unpacked variable names we can form from the struct.
    basename is used to take into account the parent struct's name. For example, lets say we have:

    @dataclasses.dataclass
    class StructAB:
        a:
        b:
        struct_cd: StructCD

    @dataclasses.dataclass
    class StructCD:
        c:
        d:
        struct_ef: StructEF

    @dataclasses.dataclass
    class StructEF:
        e:
        f:

    ... and the function parameters look like: `def foo(struct_ab: StructAB)`
        
    then all possible variables we could form from this are:
    - struct_ab.a
    - struct_ab.b
    - struct_ab.struct_cd.c
    - struct_ab.struct_cd.d
    - struct_ab.struct_cd.strucdt_ef.e
    - struct_ab.struct_cd.strucdt_ef.f

    And the members of struct_locals should be:
    - __ti_struct_ab__ti_a
    - __ti_struct_ab__ti_b
    - __ti_struct_ab__ti_struct_cd__ti_c
    - __ti_struct_ab__ti_struct_cd__ti_d
    - __ti_struct_ab__ti_struct_cd__ti_struct_ef__ti_e
    - __ti_struct_ab__ti_struct_cd__ti_struct_ef__ti_f


    """
    print("_populate_struct_locals_from_params_dict struct_type", struct_type)
    for field in dataclasses.fields(struct_type):
        print('field.name', field.name, "field.type", field.type)
        child_name = f"{basename}__ti_{field.name}"
        if dataclasses.is_dataclass(field.type):
            print("found dataclass")
            _populate_struct_locals_from_params_dict(child_name, struct_locals, field.type)
        else:
            struct_locals.add(child_name)
    print("struct_locals", struct_locals)

def populate_struct_locals(ctx: ASTTransformerContext) -> set[str]:
    struct_locals = set()
    assert ctx.func is not None
    sig = inspect.signature(ctx.func.func)
    parameters = sig.parameters
    print("calculating struct locals")
    for param_name, parameter in parameters.items():
        print('param_name', param_name, "parameter.annotation", parameter.annotation)
        if dataclasses.is_dataclass(parameter.annotation):
            print("found dataclass")
            for field in dataclasses.fields(parameter.annotation):
                child_name = f"__ti_{param_name}__ti_{field.name}"
                if dataclasses.is_dataclass(field.type):
                    _populate_struct_locals_from_params_dict(child_name, struct_locals, field.type)
                    continue
                print("child_name", child_name)
                struct_locals.add(child_name)
    print("struct_locals", struct_locals)
    return struct_locals


def expand_func_arguments(arguments: list[KernelArgument]) -> list[KernelArgument]:
    new_arguments = []
    for i, argument in enumerate(arguments):
        print("i", i, "argument", argument, "annotation", argument.annotation)
        if dataclasses.is_dataclass(argument.annotation):
            print("found dataclass")
            for field in dataclasses.fields(argument.annotation):
                field_name = field.name
                field_type = field.type
                print("field_name", field_name, field_type)
                # field_value = getattr(arg, field.name)
                new_argument = KernelArgument(
                    _annotation=field_type,
                    _name=f"__ti_{argument.name}_{field_name}",
                )
                # print("new_argument", new_argument)
                # asdfad
                new_arguments.append(new_argument)
        else:
            new_arguments.append(argument)
    return new_arguments


def unpack_ndarray_struct(tree: ast.Module, struct_locals: set[str]) -> ast.Module:
    print("struct_locals", struct_locals)
    class AttributeToNameTransformer(ast.NodeTransformer):
        def visit_Attribute(self, node):
            if isinstance(node.value, ast.Attribute):
                return node
            if not isinstance(node.value, ast.Name):
                return node
            base_id = node.value.id
            print("base_id", base_id)
            # if base_id in ["ti", "ops"]:
            #     return node
            attr_name = node.attr
            # print("attr.name", attr.name)
            new_id = "__ti_" + base_id + "_" + attr_name
            # return node
            if new_id not in struct_locals:
                return node
            print("updating ast for new_id", new_id)
            # asdf
            return ast.copy_location(ast.Name(id=new_id, ctx=node.ctx), node)
    transformer = AttributeToNameTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    # asddf
    return new_tree
