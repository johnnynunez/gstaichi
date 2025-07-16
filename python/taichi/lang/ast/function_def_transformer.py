import ast
import dataclasses
from typing import Any, Callable

from taichi.lang import (
    _ndarray,
    any_array,
    expr,
    impl,
    kernel_arguments,
    matrix,
)
from taichi.lang import ops as ti_ops
from taichi.lang.argpack import ArgPackType
from taichi.lang.ast.ast_transformer_utils import (
    ASTTransformerContext,
)
from taichi.lang.exception import (
    TaichiSyntaxError,
)
from taichi.lang.matrix import MatrixType
from taichi.lang.struct import StructType
from taichi.lang.util import to_taichi_type
from taichi.types import annotations, ndarray_type, primitive_types, texture_type


class FunctionDefTransformer:
    @staticmethod
    def _decl_and_create_variable(
        ctx: ASTTransformerContext,
        annotation: Any,
        name: str,
        this_arg_features: tuple[tuple[Any, ...], ...] | None,
        invoke_later_dict: dict[str, tuple[Any, str, Callable, list[Any]]],
        prefix_name: str,
        arg_depth: int,
    ) -> tuple[bool, Any]:
        full_name = prefix_name + "_" + name
        print("decl_and_create_variable fullname", full_name, "prefix_name", prefix_name, "annotation", annotation)
        if not isinstance(annotation, primitive_types.RefType):
            ctx.kernel_args.append(name)
        if isinstance(annotation, ArgPackType):
            assert this_arg_features is not None
            kernel_arguments.push_argpack_arg(name)
            d = {}
            items_to_put_in_dict = []
            for j, (_name, anno) in enumerate(annotation.members.items()):
                result, obj = FunctionDefTransformer._decl_and_create_variable(
                    ctx, anno, _name, this_arg_features[j], invoke_later_dict, full_name, arg_depth + 1
                )
                if not result:
                    d[_name] = None
                    items_to_put_in_dict.append((full_name + "_" + _name, _name, obj))
                else:
                    d[_name] = obj
            argpack = kernel_arguments.decl_argpack_arg(annotation, d)
            for item in items_to_put_in_dict:
                invoke_later_dict[item[0]] = argpack, item[1], *item[2]
            return True, argpack
        if annotation == annotations.template or isinstance(annotation, annotations.template):
            assert ctx.global_vars is not None
            return True, ctx.global_vars[name]
        if isinstance(annotation, annotations.sparse_matrix_builder):
            return False, (
                kernel_arguments.decl_sparse_matrix,
                (
                    to_taichi_type(this_arg_features),
                    full_name,
                ),
            )
        if isinstance(annotation, ndarray_type.NdarrayType):
            assert this_arg_features is not None
            call_params = [
                to_taichi_type(this_arg_features[0]),
                this_arg_features[1],
                full_name,
                this_arg_features[2],
                this_arg_features[3],
            ]
            print(
                "    decl_and_create_variable is_ndarray_type returning ",
                kernel_arguments.decl_ndarray_arg,
                call_params,
            )
            return False, (
                kernel_arguments.decl_ndarray_arg,
                (
                    to_taichi_type(this_arg_features[0]),
                    this_arg_features[1],
                    full_name,
                    this_arg_features[2],
                    this_arg_features[3],
                ),
            )
        if isinstance(annotation, texture_type.TextureType):
            assert this_arg_features is not None
            return False, (kernel_arguments.decl_texture_arg, (this_arg_features[0], full_name))
        if isinstance(annotation, texture_type.RWTextureType):
            assert this_arg_features is not None
            return False, (
                kernel_arguments.decl_rw_texture_arg,
                (this_arg_features[0], this_arg_features[1], this_arg_features[2], full_name),
            )
        if dataclasses.is_dataclass(annotation):
            print("found dataclass argument!")
            """
            So, what needs to happen now is ...
            - we'll need to expand out the nested struct too
            - eg if we have:
            @ti.kernel
            def f1(some_struct: SomeStruct):
                ...

            and SomeStruct is:
            @dataclasses.dataclass
            class SomeStruct:
                a: ti.types.NDArray[ti.32, 1]
                child: ChildStruct

            and ChildStruct is:
            @datatclasses.dataclass
            class ChildStruct:
                b: ti.types.NDArray[ti.32, 1]

            ... so we'll expand the paramters to:
            - __ti_some_struct_a: ti.types.NDArray[ti.32, 1]
            - __ti_some_struct__ti_child__ti_b: ti.types.NDArray[ti.32, 1]
            (or sometihng smilar ish)

            So... we'll loop over the fields, and send those each to
            """
        if isinstance(annotation, MatrixType):
            return True, kernel_arguments.decl_matrix_arg(annotation, name, arg_depth)
        if isinstance(annotation, StructType):
            return True, kernel_arguments.decl_struct_arg(annotation, name, arg_depth)
        return True, kernel_arguments.decl_scalar_arg(annotation, name, arg_depth)

    @staticmethod
    def _process_kernel_arg(
        ctx: ASTTransformerContext,
        invoke_later_dict: dict[str, tuple[Any, str, Callable, list[Any]]],
        create_variable_later: dict[str, Any],
        argument_name: str,
        argument_type: Any,
        this_arg_features: tuple[Any, ...],
    ) -> None:
        # assert ctx.arg_features is not None
        if isinstance(argument_type, ArgPackType):
            # assert this_arg_features is not None
            kernel_arguments.push_argpack_arg(argument_name)
            d = {}
            items_to_put_in_dict: list[tuple[str, str, Any]] = []
            for j, (name, anno) in enumerate(argument_type.members.items()):
                result, obj = FunctionDefTransformer._decl_and_create_variable(
                    ctx, anno, name, this_arg_features[j], invoke_later_dict, "__argpack_" + name, 1
                )
                if not result:
                    d[name] = None
                    items_to_put_in_dict.append(("__argpack_" + name, name, obj))
                else:
                    d[name] = obj
            argpack = kernel_arguments.decl_argpack_arg(argument_type, d)
            for item in items_to_put_in_dict:
                invoke_later_dict[item[0]] = argpack, item[1], *item[2]
            create_variable_later[argument_name] = argpack
        elif dataclasses.is_dataclass(argument_type):
            print("     transform_as_kernel got dataclass")
            dataclass_type = argument_type
            # assert this_arg_features is not None
            # arg_features = ctx.arg_features[i]
            ctx.create_variable(argument_name, dataclass_type)
            for field_idx, field in enumerate(dataclasses.fields(dataclass_type)):
                # TODO: change names to add __ti_ before field.name
                flat_name = f"{argument_name}__ti_{field.name}"
                if not flat_name.startswith("__ti_"):
                    flat_name = f"__ti_{flat_name}"
                print("     transform_as_kernel   field_name", field.name, field.type, "flat_name", flat_name)
                # print("ctx.arg_features[i]", ctx.arg_features[i])
                # if a field is a dataclass, then feed back into process_kernel_arg recursively
                # and see what happens
                if dataclasses.is_dataclass(field.type):
                    # child_name = flat_name
                    FunctionDefTransformer._process_kernel_arg(
                        ctx,
                        invoke_later_dict,
                        create_variable_later,
                        flat_name,
                        field.type,
                        this_arg_features[field_idx],
                    )
                else:
                    result, obj = FunctionDefTransformer._decl_and_create_variable(
                        ctx,
                        field.type,
                        flat_name,
                        this_arg_features[field_idx],
                        invoke_later_dict,
                        "",
                        0,
                    )
                    print("     transform_as_kernel calling ctx.create_variable", flat_name, str(obj)[:100])
                    ctx.create_variable(flat_name, obj if result else obj[0](*obj[1]))
        else:
            call_params = [
                argument_type,
                argument_name,
                this_arg_features,
                invoke_later_dict,
                "",
                0,
            ]
            print("transform_as_kernel() calling decl_and_create_variable, params", call_params)
            result, obj = FunctionDefTransformer._decl_and_create_variable(
                ctx,
                argument_type,
                argument_name,
                this_arg_features,
                invoke_later_dict,
                "",
                0,
            )
            print("obj returned by decl_and_create_variable obj", obj)
            print("transform_as_kernel() calling ctx.create_variable", argument_name, obj)
            ctx.create_variable(argument_name, obj if result else obj[0](*obj[1]))

    @staticmethod
    def _transform_as_kernel(ctx: ASTTransformerContext, node: ast.FunctionDef, args: ast.arguments) -> None:
        assert ctx.func is not None
        assert ctx.arg_features is not None
        if node.returns is not None:
            if not isinstance(node.returns, ast.Constant):
                assert ctx.func.return_type is not None
                for return_type in ctx.func.return_type:
                    kernel_arguments.decl_ret(return_type)
        compiling_callable = impl.get_runtime().compiling_callable
        assert compiling_callable is not None
        compiling_callable.finalize_rets()

        invoke_later_dict: dict[str, tuple[Any, str, Callable, list[Any]]] = dict()
        create_variable_later: dict[str, Any] = dict()
        print(
            "transform_as_kernel iterate args len(args.args)",
            len(args.args),
            "len(ctx.func.arguments)",
            len(ctx.func.arguments),
        )
        for i, arg in enumerate(args.args):
            argument = ctx.func.arguments[i]
            print(" arg i", i, "arg", ast.dump(arg), type(arg))
            FunctionDefTransformer._process_kernel_arg(
                ctx,
                invoke_later_dict,
                create_variable_later,
                argument.name,
                argument.annotation,
                ctx.arg_features[i] if ctx.arg_features is not None else (),
            )
        for k, v in invoke_later_dict.items():
            argpack, name, func, params = v
            print("v", v)
            print("func", func, "argpack", argpack, "name", name, "params", params)
            argpack[name] = func(*params)
        for k, v in create_variable_later.items():
            ctx.create_variable(k, v)
        compiling_callable.finalize_params()
        # remove original args
        node.args.args = []

    @staticmethod
    def _transform_as_func(ctx: ASTTransformerContext, node: ast.FunctionDef, args: ast.arguments) -> None:
        print("  build_FunctionDef args.args", args.args, "ctx.argument_data", ctx.argument_data)
        print("args. args:")
        assert ctx.argument_data is not None
        assert ctx.func is not None
        for arg in args.args:
            print("    ", arg, ast.dump(arg))
        print("ctx.argument_data:")
        for arg in ctx.argument_data:
            print("    ", arg)
        print("ctx.func.arguments")
        for arg in ctx.func.arguments:
            print("    ", arg, arg.annotation, arg.name)
        # assert len(args.args) == len(ctx.argument_data)
        print("ti.func iterate args")
        # args_offset = 0
        for data_i, data in enumerate(ctx.argument_data):
            # for i, (arg, data) in enumerate(zip(args.args, ctx.argument_data)):
            argument = ctx.func.arguments[data_i]
            print("  ti.func arg data_i", data_i, "data", str(data)[:100])
            # annotation = argument.annotation
            print("  annotation", argument.annotation, type(argument.annotation))
            # Template arguments are passed by reference.
            if isinstance(argument.annotation, annotations.template):
                ctx.create_variable(argument.name, data)
                continue

            elif dataclasses.is_dataclass(argument.annotation):
                print("got dataclass")
                dataclass_type = argument.annotation
                # print("******* creating var name", argument.name, "value", dataclass_type)
                for field in dataclasses.fields(dataclass_type):
                    flat_name = f"__ti_{argument.name}_{field.name}"
                    print("field_name", field.name, field.type, "new_field_name", flat_name)
                    data_child = getattr(data, field.name)
                    if not isinstance(
                        data_child,
                        (
                            _ndarray.ScalarNdarray,
                            matrix.VectorNdarray,
                            matrix.MatrixNdarray,
                            any_array.AnyArray,
                        ),
                    ):
                        raise TaichiSyntaxError(
                            f"Argument {field.name}: {field.type} of type {dataclass_type} {field.type} is not recognized."
                        )
                    field.type.check_matched(data_child.get_type(), field.name)
                    var_name = f"__ti_{argument.name}_{field.name}"
                    print("    creating var", var_name, "=", str(data_child)[:50])
                    print("        ctx.arg_features", ctx.arg_features)
                    ctx.create_variable(var_name, data_child)
                continue

            # Ndarray arguments are passed by reference.
            if isinstance(argument.annotation, (ndarray_type.NdarrayType)):
                if not isinstance(
                    data,
                    (
                        _ndarray.ScalarNdarray,
                        matrix.VectorNdarray,
                        matrix.MatrixNdarray,
                        any_array.AnyArray,
                    ),
                ):
                    raise TaichiSyntaxError(f"Argument {argument} of type {argument.annotation} is not recognized.")
                argument.annotation.check_matched(data.get_type(), argument.name)
                ctx.create_variable(argument.name, data)
                continue

            # Matrix arguments are passed by value.
            if isinstance(argument.annotation, (MatrixType)):
                # "data" is expected to be an Expr here,
                # so we simply call "impl.expr_init_func(data)" to perform:
                #
                # TensorType* t = alloca()
                # assign(t, data)
                #
                # We created local variable "t" - a copy of the passed-in argument "data"
                if not isinstance(data, expr.Expr) or not data.ptr.is_tensor():
                    raise TaichiSyntaxError(
                        f"Argument {argument} of type {argument.annotation} is expected to be a Matrix, but got {type(data)}."
                    )

                element_shape = data.ptr.get_rvalue_type().shape()
                if len(element_shape) != argument.annotation.ndim:
                    raise TaichiSyntaxError(
                        f"Argument {argument} of type {argument.annotation} is expected to be a Matrix with ndim {argument.annotation.ndim}, but got {len(element_shape)}."
                    )

                assert argument.annotation.ndim > 0
                if element_shape[0] != argument.annotation.n:
                    raise TaichiSyntaxError(
                        f"Argument {argument} of type {argument.annotation} is expected to be a Matrix with n {argument.annotation.n}, but got {element_shape[0]}."
                    )

                if argument.annotation.ndim == 2 and element_shape[1] != argument.annotation.m:
                    raise TaichiSyntaxError(
                        f"Argument {argument} of type {argument.annotation} is expected to be a Matrix with m {argument.annotation.m}, but got {element_shape[0]}."
                    )

                ctx.create_variable(argument.name, impl.expr_init_func(data))
                continue

            if id(argument.annotation) in primitive_types.type_ids:
                ctx.create_variable(argument.name, impl.expr_init_func(ti_ops.cast(data, argument.annotation)))
                continue
            # Create a copy for non-template arguments,
            # so that they are passed by value.
            var_name = argument.name
            ctx.create_variable(var_name, impl.expr_init_func(data))
        # deal with dataclasses
        print("")
        print("********* iterate over args.args")
        # sig = inspect.signature(ctx.func.func)
        # for k, v in sig.parameters.items():
        # pylint: disable=import-outside-toplevel
        from taichi.lang.kernel_impl import (
            Func,
        )

        assert isinstance(ctx.func, Func)
        for v in ctx.func.orig_arguments:
            # k = arg.name
            # v = arg.annotation
            # print("    ", k, v, type(v), v.annotation)
            print("    ", v.name, v.annotation)
            if dataclasses.is_dataclass(v.annotation):
                print("found dataclass")
                print("create variabele", v.name, "=", v.annotation)
                ctx.create_variable(v.name, v.annotation)
        # print([(arg.name, arg.annotation) for arg in sig.parameters])
        for arg in args.args:
            # val = arg.ptr
            val = ctx.get_var_by_name(arg.arg)
            print("  arg", ast.dump(arg), "val", val)
        # asdfdf

    @staticmethod
    def build_FunctionDef(
        ctx: ASTTransformerContext,
        node: ast.FunctionDef,
        build_stmts: Callable[[ASTTransformerContext, list[ast.stmt]], None],
    ) -> None:
        print("build_FunctionDef node", ast.dump(node))
        if ctx.visited_funcdef:
            raise TaichiSyntaxError(
                f"Function definition is not allowed in 'ti.{'kernel' if ctx.is_kernel else 'func'}'."
            )
        ctx.visited_funcdef = True

        args = node.args
        # print("args", args)
        assert args.vararg is None
        assert args.kwonlyargs == []
        assert args.kw_defaults == []
        assert args.kwarg is None

        if ctx.is_kernel:  # ti.kernel
            FunctionDefTransformer._transform_as_kernel(ctx, node, args)

        else:  # ti.func
            assert ctx.argument_data is not None
            assert ctx.func is not None
            if ctx.is_real_function:
                FunctionDefTransformer._transform_as_kernel(ctx, node, args)
            else:
                FunctionDefTransformer._transform_as_func(ctx, node, args)

        with ctx.variable_scope_guard():
            build_stmts(ctx, node.body)
