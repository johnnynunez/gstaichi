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
    def build_FunctionDef(ctx: ASTTransformerContext, node: ast.FunctionDef):
        if ctx.visited_funcdef:
            raise TaichiSyntaxError(
                f"Function definition is not allowed in 'ti.{'kernel' if ctx.is_kernel else 'func'}'."
            )
        ctx.visited_funcdef = True

        args = node.args
        assert args.vararg is None
        assert args.kwonlyargs == []
        assert args.kw_defaults == []
        assert args.kwarg is None

        def decl_and_create_variable(
            annotation, name, arg_features, invoke_later_dict, prefix_name, arg_depth
        ) -> tuple[bool, Any]:
            full_name = prefix_name + "_" + name
            if not isinstance(annotation, primitive_types.RefType):
                ctx.kernel_args.append(name)
            if isinstance(annotation, ArgPackType):
                kernel_arguments.push_argpack_arg(name)
                d = {}
                items_to_put_in_dict = []
                for j, (_name, anno) in enumerate(annotation.members.items()):
                    result, obj = decl_and_create_variable(
                        anno, _name, arg_features[j], invoke_later_dict, full_name, arg_depth + 1
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
                return True, ctx.global_vars[name]
            if isinstance(annotation, annotations.sparse_matrix_builder):
                return False, (
                    kernel_arguments.decl_sparse_matrix,
                    (
                        to_taichi_type(arg_features),
                        full_name,
                    ),
                )
            if isinstance(annotation, ndarray_type.NdarrayType):
                return False, (
                    kernel_arguments.decl_ndarray_arg,
                    (
                        to_taichi_type(arg_features[0]),
                        arg_features[1],
                        full_name,
                        arg_features[2],
                        arg_features[3],
                    ),
                )
            if isinstance(annotation, texture_type.TextureType):
                return False, (kernel_arguments.decl_texture_arg, (arg_features[0], full_name))
            if isinstance(annotation, texture_type.RWTextureType):
                return False, (
                    kernel_arguments.decl_rw_texture_arg,
                    (arg_features[0], arg_features[1], arg_features[2], full_name),
                )
            if isinstance(annotation, MatrixType):
                return True, kernel_arguments.decl_matrix_arg(annotation, name, arg_depth)
            if isinstance(annotation, StructType):
                return True, kernel_arguments.decl_struct_arg(annotation, name, arg_depth)
            return True, kernel_arguments.decl_scalar_arg(annotation, name, arg_depth)

        def transform_as_kernel() -> None:
            if node.returns is not None:
                if not isinstance(node.returns, ast.Constant):
                    for return_type in ctx.func.return_type:
                        kernel_arguments.decl_ret(return_type)
            impl.get_runtime().compiling_callable.finalize_rets()

            invoke_later_dict: dict[str, tuple[Any, str, Any]] = dict()
            create_variable_later = dict()
            for i, arg in enumerate(args.args):
                argument = ctx.func.arguments[i]
                if isinstance(argument.annotation, ArgPackType):
                    kernel_arguments.push_argpack_arg(argument.name)
                    d = {}
                    items_to_put_in_dict: list[tuple[str, str, Any]] = []
                    for j, (name, anno) in enumerate(argument.annotation.members.items()):
                        result, obj = decl_and_create_variable(
                            anno, name, ctx.arg_features[i][j], invoke_later_dict, "__argpack_" + name, 1
                        )
                        if not result:
                            d[name] = None
                            items_to_put_in_dict.append(("__argpack_" + name, name, obj))
                        else:
                            d[name] = obj
                    argpack = kernel_arguments.decl_argpack_arg(ctx.func.arguments[i].annotation, d)
                    for item in items_to_put_in_dict:
                        invoke_later_dict[item[0]] = argpack, item[1], *item[2]
                    create_variable_later[arg.arg] = argpack
                elif dataclasses.is_dataclass(argument.annotation):
                    arg_features = ctx.arg_features[i]
                    ctx.create_variable(argument.name, argument.annotation)
                    for field_idx, field in enumerate(dataclasses.fields(argument.annotation)):
                        flat_name = f"__ti_{argument.name}_{field.name}"
                        result, obj = decl_and_create_variable(
                            field.type,
                            flat_name,
                            arg_features[field_idx],
                            invoke_later_dict,
                            "",
                            0,
                        )
                        if result:
                            ctx.create_variable(flat_name, obj)
                        else:
                            decl_type_func, type_args = obj
                            obj = decl_type_func(*type_args)
                            ctx.create_variable(flat_name, obj)
                else:
                    result, obj = decl_and_create_variable(
                        argument.annotation,
                        argument.name,
                        ctx.arg_features[i] if ctx.arg_features is not None else None,
                        invoke_later_dict,
                        "",
                        0,
                    )
                    if result:
                        ctx.create_variable(arg.arg, obj)
                    else:
                        decl_type_func, type_args = obj
                        obj = decl_type_func(*type_args)
                        ctx.create_variable(arg.arg, obj)
            for k, v in invoke_later_dict.items():
                argpack, name, func, params = v
                argpack[name] = func(*params)
            for k, v in create_variable_later.items():
                ctx.create_variable(k, v)

            impl.get_runtime().compiling_callable.finalize_params()
            # remove original args
            node.args.args = []

        if ctx.is_kernel:  # ti.kernel
            transform_as_kernel()

        else:  # ti.func
            if ctx.is_real_function:
                transform_as_kernel()
            else:
                for data_i, data in enumerate(ctx.argument_data):
                    argument = ctx.func.arguments[data_i]
                    if isinstance(argument.annotation, annotations.template):
                        ctx.create_variable(argument.name, data)
                        continue

                    elif dataclasses.is_dataclass(argument.annotation):
                        dataclass_type = argument.annotation
                        for field in dataclasses.fields(dataclass_type):
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
                                    f"Argument {argument.name} of type {dataclass_type} {field.type} is not recognized."
                                )
                            field.type.check_matched(data_child.get_type(), field.name)
                            var_name = f"__ti_{argument.name}_{field.name}"
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
                            raise TaichiSyntaxError(
                                f"Argument {arg.arg} of type {argument.annotation} is not recognized."
                            )
                        argument.annotation.check_matched(data.get_type(), argument.name)
                        ctx.create_variable(argument.name, data)
                        continue

                    # Matrix arguments are passed by value.
                    if isinstance(argument.annotation, (MatrixType)):
                        var_name = argument.name
                        # "data" is expected to be an Expr here,
                        # so we simply call "impl.expr_init_func(data)" to perform:
                        #
                        # TensorType* t = alloca()
                        # assign(t, data)
                        #
                        # We created local variable "t" - a copy of the passed-in argument "data"
                        if not isinstance(data, expr.Expr) or not data.ptr.is_tensor():
                            raise TaichiSyntaxError(
                                f"Argument {var_name} of type {argument.annotation} is expected to be a Matrix, but got {type(data)}."
                            )

                        element_shape = data.ptr.get_rvalue_type().shape()
                        if len(element_shape) != argument.annotation.ndim:
                            raise TaichiSyntaxError(
                                f"Argument {var_name} of type {argument.annotation} is expected to be a Matrix with ndim {argument.annotation.ndim}, but got {len(element_shape)}."
                            )

                        assert argument.annotation.ndim > 0
                        if element_shape[0] != argument.annotation.n:
                            raise TaichiSyntaxError(
                                f"Argument {var_name} of type {argument.annotation} is expected to be a Matrix with n {argument.annotation.n}, but got {element_shape[0]}."
                            )

                        if argument.annotation.ndim == 2 and element_shape[1] != argument.annotation.m:
                            raise TaichiSyntaxError(
                                f"Argument {var_name} of type {argument.annotation} is expected to be a Matrix with m {argument.annotation.m}, but got {element_shape[0]}."
                            )

                        ctx.create_variable(var_name, impl.expr_init_func(data))
                        continue

                    if id(argument.annotation) in primitive_types.type_ids:
                        var_name = argument.name
                        ctx.create_variable(var_name, impl.expr_init_func(ti_ops.cast(data, argument.annotation)))
                        continue
                    # Create a copy for non-template arguments,
                    # so that they are passed by value.
                    var_name = argument.name
                    ctx.create_variable(var_name, impl.expr_init_func(data))
                for v in ctx.func.orig_arguments:
                    if dataclasses.is_dataclass(v.annotation):
                        ctx.create_variable(v.name, v.annotation)

        with ctx.variable_scope_guard():
            build_stmts(ctx, node.body)

        return None
