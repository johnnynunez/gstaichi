import ast
import dataclasses
import inspect
import math
import operator
import re
import warnings
from collections import ChainMap

import numpy as np

from taichi.lang import (
    expr,
    impl,
    matrix,
)
from taichi.lang import ops as ti_ops
from taichi.lang.ast.ast_transformer_utils import (
    ASTTransformerContext,
    get_decorator,
)
from taichi.lang.exception import (
    TaichiSyntaxError,
    TaichiTypeError,
)
from taichi.lang.expr import Expr
from taichi.lang.matrix import Matrix, Vector
from taichi.lang.util import is_taichi_class
from taichi.types import primitive_types


class CallTransformer:

    @staticmethod
    def build_call_if_is_builtin(ctx: ASTTransformerContext, node, args, keywords):
        from taichi.lang import matrix_ops  # pylint: disable=C0415

        func = node.func.ptr
        replace_func = {
            id(print): impl.ti_print,
            id(min): ti_ops.min,
            id(max): ti_ops.max,
            id(int): impl.ti_int,
            id(bool): impl.ti_bool,
            id(float): impl.ti_float,
            id(any): matrix_ops.any,
            id(all): matrix_ops.all,
            id(abs): abs,
            id(pow): pow,
            id(operator.matmul): matrix_ops.matmul,
        }

        # Builtin 'len' function on Matrix Expr
        if id(func) == id(len) and len(args) == 1:
            if isinstance(args[0], Expr) and args[0].ptr.is_tensor():
                node.ptr = args[0].get_shape()[0]
                return True

        if id(func) in replace_func:
            node.ptr = replace_func[id(func)](*args, **keywords)
            return True
        return False

    @staticmethod
    def build_call_if_is_type(ctx: ASTTransformerContext, node, args, keywords):
        func = node.func.ptr
        if id(func) in primitive_types.type_ids:
            if len(args) != 1 or keywords:
                raise TaichiSyntaxError("A primitive type can only decorate a single expression.")
            if is_taichi_class(args[0]):
                raise TaichiSyntaxError("A primitive type cannot decorate an expression with a compound type.")

            if isinstance(args[0], expr.Expr):
                if args[0].ptr.is_tensor():
                    raise TaichiSyntaxError("A primitive type cannot decorate an expression with a compound type.")
                node.ptr = ti_ops.cast(args[0], func)
            else:
                node.ptr = expr.Expr(args[0], dtype=func)
            return True
        return False

    @staticmethod
    def is_external_func(ctx: ASTTransformerContext, func) -> bool:
        if ctx.is_in_static_scope():  # allow external function in static scope
            return False
        if hasattr(func, "_is_taichi_function") or hasattr(func, "_is_wrapped_kernel"):  # taichi func/kernel
            return False
        if hasattr(func, "__module__") and func.__module__ and func.__module__.startswith("taichi."):
            return False
        return True

    @staticmethod
    def warn_if_is_external_func(ctx: ASTTransformerContext, node):
        func = node.func.ptr
        if not CallTransformer.is_external_func(ctx, func):
            return
        name = unparse(node.func).strip()
        warnings.warn_explicit(
            f"\x1b[38;5;226m"  # Yellow
            f'Calling non-taichi function "{name}". '
            f"Scope inside the function is not processed by the Taichi AST transformer. "
            f"The function may not work as expected. Proceed with caution! "
            f"Maybe you can consider turning it into a @ti.func?"
            f"\x1b[0m",  # Reset
            SyntaxWarning,
            ctx.file,
            node.lineno + ctx.lineno_offset,
            module="taichi",
        )

    @staticmethod
    # Parses a formatted string and extracts format specifiers from it, along with positional and keyword arguments.
    # This function produces a canonicalized formatted string that includes solely empty replacement fields, e.g. 'qwerty {} {} {} {} {}'.
    # Note that the arguments can be used multiple times in the string.
    # e.g.:
    # origin input: 'qwerty {1} {} {1:.3f} {k:.4f} {k:}'.format(1.0, 2.0, k=k)
    # raw_string: 'qwerty {1} {} {1:.3f} {k:.4f} {k:}'
    # raw_args: [1.0, 2.0]
    # raw_keywords: {'k': <ti.Expr>}
    # return value: ['qwerty {} {} {} {} {}', 2.0, 1.0, ['__ti_fmt_value__', 2.0, '.3f'], ['__ti_fmt_value__', <ti.Expr>, '.4f'], <ti.Expr>]
    def canonicalize_formatted_string(raw_string: str, *raw_args: list, **raw_keywords: dict):
        raw_brackets = re.findall(r"{(.*?)}", raw_string)
        brackets = []
        unnamed = 0
        for bracket in raw_brackets:
            item, spec = bracket.split(":") if ":" in bracket else (bracket, None)
            if item.isdigit():
                item = int(item)
            # handle unnamed positional args
            if item == "":
                item = unnamed
                unnamed += 1
            # handle empty spec
            if spec == "":
                spec = None
            brackets.append((item, spec))

        # check for errors in the arguments
        max_args_index = max([t[0] for t in brackets if isinstance(t[0], int)], default=-1)
        if max_args_index + 1 != len(raw_args):
            raise TaichiSyntaxError(
                f"Expected {max_args_index + 1} positional argument(s), but received {len(raw_args)} instead."
            )
        brackets_keywords = [t[0] for t in brackets if isinstance(t[0], str)]
        for item in brackets_keywords:
            if item not in raw_keywords:
                raise TaichiSyntaxError(f"Keyword '{item}' not found.")
        for item in raw_keywords:
            if item not in brackets_keywords:
                raise TaichiSyntaxError(f"Keyword '{item}' not used.")

        # reorganize the arguments based on their positions, keywords, and format specifiers
        args = []
        for item, spec in brackets:
            new_arg = raw_args[item] if isinstance(item, int) else raw_keywords[item]
            if spec is not None:
                args.append(["__ti_fmt_value__", new_arg, spec])
            else:
                args.append(new_arg)
        # put the formatted string as the first argument to make ti.format() happy
        args.insert(0, re.sub(r"{.*?}", "{}", raw_string))
        return args

    @staticmethod
    def expand_Call_dataclass_args(args: tuple[ast.AST]) -> tuple[ast.AST]:
        args_new = []
        for i, arg in enumerate(args):
            val = arg.ptr
            print("  i", i, "arg", ast.dump(arg), "val", val)
            if dataclasses.is_dataclass(val):
                print("found dataclass val", val)
                dataclass_type = val
                for field in dataclasses.fields(dataclass_type):
                    # field_val = getattr(val, field_name)
                    child_name = f"__ti_{arg.id}__ti_{field.name}"
                    print("child_name", child_name)
                    load_ctx = ast.Load()
                    # module = ast.parse(f"def func({child_name}):\n    pass")
                    # arg_node = module.body[0].args.args[0]
                    arg_node = ast.Name(
                        id=child_name,
                        ctx=load_ctx,
                        lineno=arg.lineno,
                        end_lineno=arg.end_lineno,
                        col_offset=arg.col_offset,
                        end_col_offset=arg.end_col_offset,
                    )
                    print("arg_node", ast.dump(arg_node), arg_node.__dict__)
                    # ast_str = ast.dump(arg_node)
                    # print("ast_str", ast_str)
                    args_new.append(arg_node)
            else:
                args_new.append(arg)
        return tuple(args_new)
