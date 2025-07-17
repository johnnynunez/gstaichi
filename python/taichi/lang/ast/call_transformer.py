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