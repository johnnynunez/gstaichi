import ast
import dataclasses
import functools
import inspect
import json
import operator
import os
import pathlib
import re
import sys
import textwrap
import time
import types
import typing
import warnings
from typing import Any, Callable, Type

import numpy as np

import taichi.lang
import taichi.lang._ndarray
import taichi.lang._texture
from taichi.lang.ast.ast_transformer import ASTTransformer
from taichi.lang.ast.function_def_transformer import FunctionDefTransformer
import taichi.types.annotations
from taichi import _logging
from taichi._lib import core as _ti_core
from taichi._lib.core.taichi_python import (
    ASTBuilder,
    FunctionKey,
    KernelCxx,
    KernelLaunchContext,
)
from taichi.lang import _kernel_impl_dataclass, impl, ops, runtime_ops
from taichi.lang._template_mapper import TemplateMapper
from taichi.lang._wrap_inspect import getsourcefile, getsourcelines
from taichi.lang.any_array import AnyArray
from taichi.lang.argpack import ArgPack, ArgPackType
from taichi.lang.ast import (
    ASTTransformerContext,
    KernelSimplicityASTChecker,
    transform_tree,
)
from taichi.lang.ast.ast_transformer_utils import ReturnStatus
from taichi.lang.exception import (
    TaichiCompilationError,
    TaichiRuntimeError,
    TaichiRuntimeTypeError,
    TaichiSyntaxError,
    TaichiTypeError,
    handle_exception_from_cpp,
)
from taichi.lang.expr import Expr
from taichi.lang.kernel_arguments import ArgMetadata
from taichi.lang.matrix import MatrixType
from taichi.lang.shell import _shell_pop_print
from taichi.lang.struct import StructType
from taichi.lang.util import cook_dtype, has_paddle, has_pytorch
from taichi.types import (
    ndarray_type,
    primitive_types,
    sparse_matrix_builder,
    template,
    texture_type,
)
from taichi.types.compound_types import CompoundType
from taichi.types.enums import AutodiffMode, Layout
from taichi.types.utils import is_signed
from taichi.lang.fast_caching.fast_cacher import FastCacher

CompiledKernelKeyType = tuple[Callable, int, AutodiffMode]


fast_cacher = FastCacher()


class BoundFunc:
    def __init__(self, fn: Callable, instance: Any, taichi_callable: "TaichiCallable"):
        self.fn = fn
        self.instance = instance
        self.taichi_callable = taichi_callable

    def __call__(self, *args, **kwargs):
        return self.fn(self.instance, *args, **kwargs)

    def __getattr__(self, k: str) -> Any:
        res = getattr(self.taichi_callable, k)
        return res

    def __setattr__(self, k: str, v: Any) -> None:
        if k in ("fn", "instance", "taichi_callable"):
            object.__setattr__(self, k, v)
        else:
            setattr(self.taichi_callable, k, v)


class TaichiCallable:
    def __init__(self, fn: Callable, wrapper: Callable) -> None:
        # self.func: Func | None = None
        self.fn = fn
        self.wrapper = wrapper
        self._is_real_function = False
        self._is_taichi_function = False
        self._is_wrapped_kernel = False
        self._is_classkernel = False
        self._primal: Kernel | None = None
        self._adjoint: Kernel | None = None
        self.grad: Kernel | None = None
        self._is_staticmethod = False
        self.is_pure = False
        functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):
        return self.wrapper.__call__(*args, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundFunc(self.wrapper, instance, self)


def func(fn: Callable, is_real_function=False) -> TaichiCallable:
    """Marks a function as callable in Taichi-scope.

    This decorator transforms a Python function into a Taichi one. Taichi
    will JIT compile it into native instructions.

    Args:
        fn (Callable): The Python function to be decorated
        is_real_function (bool): Whether the function is a real function

    Returns:
        Callable: The decorated function

    Example::

        >>> @ti.func
        >>> def foo(x):
        >>>     return x + 2
        >>>
        >>> @ti.kernel
        >>> def run():
        >>>     print(foo(40))  # 42
    """
    is_classfunc = _inside_class(level_of_class_stackframe=3 + is_real_function)

    fun = Func(fn, _classfunc=is_classfunc, is_real_function=is_real_function)
    taichi_callable = TaichiCallable(
        fn,
        fun,
    )
    taichi_callable._is_taichi_function = True
    taichi_callable._is_real_function = is_real_function
    return taichi_callable


def real_func(fn: Callable) -> TaichiCallable:
    return func(fn, is_real_function=True)


def pyfunc(fn: Callable) -> TaichiCallable:
    """Marks a function as callable in both Taichi and Python scopes.

    When called inside the Taichi scope, Taichi will JIT compile it into
    native instructions. Otherwise it will be invoked directly as a
    Python function.

    See also :func:`~taichi.lang.kernel_impl.func`.

    Args:
        fn (Callable): The Python function to be decorated

    Returns:
        Callable: The decorated function
    """
    is_classfunc = _inside_class(level_of_class_stackframe=3)
    fun = Func(fn, _classfunc=is_classfunc, _pyfunc=True)
    taichi_callable = TaichiCallable(
        fn,
        fun,
    )
    taichi_callable._is_taichi_function = True
    taichi_callable._is_real_function = False
    return taichi_callable


def _populate_global_vars_for_templates(
    template_slot_locations: list[int],
    argument_metas: list[ArgMetadata],
    global_vars: dict[str, Any],
    fn: Callable,
    py_args: tuple[Any, ...],
):
    # inject template parameters into globals
    for i in template_slot_locations:
        template_var_name = argument_metas[i].name
        global_vars[template_var_name] = py_args[i]
    parameters = inspect.signature(fn).parameters
    for i, (parameter_name, parameter) in enumerate(parameters.items()):
        if dataclasses.is_dataclass(parameter.annotation):
            _kernel_impl_dataclass.populate_global_vars_from_dataclass(
                parameter_name,
                parameter.annotation,
                py_args[i],
                global_vars=global_vars,
            )


def _get_tree_and_ctx(
    self: "Func | Kernel",
    args: tuple[Any, ...],
    excluded_parameters=(),
    is_kernel: bool = True,
    arg_features=None,
    ast_builder: ASTBuilder | None = None,
    is_real_function: bool = False,
) -> tuple[ast.Module, ASTTransformerContext]:
    file = getsourcefile(self.func)
    src, start_lineno = getsourcelines(self.func)
    src = [textwrap.fill(line, tabsize=4, width=9999) for line in src]
    tree = ast.parse(textwrap.dedent("\n".join(src)))

    func_body = tree.body[0]
    func_body.decorator_list = []  # type: ignore , kick that can down the road...

    global_vars = _get_global_vars(self.func)

    if is_kernel or is_real_function:
        _populate_global_vars_for_templates(
            template_slot_locations=self.template_slot_locations,
            argument_metas=self.arg_metas,
            global_vars=global_vars,
            fn=self.func,
            py_args=args,
        )

    return tree, ASTTransformerContext(
        excluded_parameters=excluded_parameters,
        is_kernel=is_kernel,
        func=self,
        arg_features=arg_features,
        global_vars=global_vars,
        argument_data=args,
        src=src,
        start_lineno=start_lineno,
        file=file,
        ast_builder=ast_builder,
        is_real_function=is_real_function,
    )


def _process_args(self: "Func | Kernel", is_func: bool, py_args: tuple[Any, ...], py_kwargs) -> tuple[Any, ...]:
    """
    used for both Func and Kernel
    """

    if is_func:
        self.arg_metas = _kernel_impl_dataclass.expand_func_arguments(self.arg_metas)

    fused_args: list[Any] = [argument.default for argument in self.arg_metas]

    len_py_args = len(py_args)
    if len_py_args > len(fused_args):
        print("too many arguments")
        arg_str = ", ".join([str(arg) for arg in py_args])
        expected_str = ", ".join([f"{arg.name} : {arg.annotation}" for arg in self.arg_metas])
        msg = f"Too many arguments. Expected ({expected_str}), got ({arg_str})."
        raise TaichiSyntaxError(msg)

    for i, py_arg in enumerate(py_args):
        fused_args[i] = py_arg

    for key, value in py_kwargs.items():
        found = False
        for i, py_arg in enumerate(self.arg_metas):
            if key == py_arg.name:
                if i < len_py_args:
                    raise TaichiSyntaxError(f"Multiple values for argument '{key}'.")
                fused_args[i] = value
                found = True
                break
        if not found:
            raise TaichiSyntaxError(f"Unexpected argument '{key}'.")

    for i, py_arg in enumerate(fused_args):
        if py_arg is inspect.Parameter.empty:
            if self.arg_metas[i].annotation is inspect._empty:
                raise TaichiSyntaxError(f"Parameter `{self.arg_metas[i].name}` missing.")
            else:
                raise TaichiSyntaxError(
                    f"Parameter `{self.arg_metas[i].name} : {self.arg_metas[i].annotation}` missing."
                )

    fused_args_tuple = tuple(fused_args)
    return fused_args_tuple


class Func:
    function_counter = 0

    def __init__(self, _func: Callable, _classfunc=False, _pyfunc=False, is_real_function=False) -> None:
        self.func = _func
        self.func_id = Func.function_counter
        Func.function_counter += 1
        self.compiled = {}
        self.classfunc = _classfunc
        self.pyfunc = _pyfunc
        self.is_real_function = is_real_function
        self.arg_metas: list[ArgMetadata] = []
        self.orig_arguments: list[ArgMetadata] = []
        self.return_type: tuple[Type, ...] | None = None
        self.extract_arguments()
        self.template_slot_locations: list[int] = []
        for i, arg in enumerate(self.arg_metas):
            if arg.annotation == template or isinstance(arg.annotation, template):
                self.template_slot_locations.append(i)
        self.mapper = TemplateMapper(self.arg_metas, self.template_slot_locations)
        self.taichi_functions = {}  # The |Function| class in C++
        self.has_print = False

    def __call__(self: "Func", *args, **kwargs) -> Any:
        args = _process_args(self, is_func=True, py_args=args, py_kwargs=kwargs)

        if not impl.inside_kernel():
            if not self.pyfunc:
                raise TaichiSyntaxError("Taichi functions cannot be called from Python-scope.")
            return self.func(*args)

        if self.is_real_function:
            current_kernel = impl.get_runtime().current_kernel
            assert current_kernel is not None
            if current_kernel.autodiff_mode != AutodiffMode.NONE:
                raise TaichiSyntaxError("Real function in gradient kernels unsupported.")
            instance_id, arg_features = self.mapper.lookup(args)
            key = _ti_core.FunctionKey(self.func.__name__, self.func_id, instance_id)
            if key.instance_id not in self.compiled:
                self.do_compile(key=key, args=args, arg_features=arg_features)
            return self.func_call_rvalue(key=key, args=args)
        current_kernel = impl.get_runtime().current_kernel
        assert current_kernel is not None
        tree, ctx = _get_tree_and_ctx(
            self,
            is_kernel=False,
            args=args,
            ast_builder=current_kernel.ast_builder(),
            is_real_function=self.is_real_function,
        )

        struct_locals = _kernel_impl_dataclass.populate_struct_locals(ctx)

        tree = _kernel_impl_dataclass.unpack_ast_struct_expressions(tree, struct_locals=struct_locals)
        ret = transform_tree(tree, ctx)
        if not self.is_real_function:
            if self.return_type and ctx.returned != ReturnStatus.ReturnedValue:
                raise TaichiSyntaxError("Function has a return type but does not have a return statement")
        return ret

    def func_call_rvalue(self, key: FunctionKey, args: tuple[Any, ...]) -> Any:
        # Skip the template args, e.g., |self|
        assert self.is_real_function
        non_template_args = []
        dbg_info = _ti_core.DebugInfo(impl.get_runtime().get_current_src_info())
        for i, kernel_arg in enumerate(self.arg_metas):
            anno = kernel_arg.annotation
            if not isinstance(anno, template):
                if id(anno) in primitive_types.type_ids:
                    non_template_args.append(ops.cast(args[i], anno))
                elif isinstance(anno, primitive_types.RefType):
                    non_template_args.append(_ti_core.make_reference(args[i].ptr, dbg_info))
                elif isinstance(anno, ndarray_type.NdarrayType):
                    if not isinstance(args[i], AnyArray):
                        raise TaichiTypeError(
                            f"Expected ndarray in the kernel argument for argument {kernel_arg.name}, got {args[i]}"
                        )
                    non_template_args += _ti_core.get_external_tensor_real_func_args(args[i].ptr, dbg_info)
                else:
                    non_template_args.append(args[i])
        non_template_args = impl.make_expr_group(non_template_args)
        compiling_callable = impl.get_runtime().compiling_callable
        assert compiling_callable is not None
        func_call = compiling_callable.ast_builder().insert_func_call(
            self.taichi_functions[key.instance_id], non_template_args, dbg_info
        )
        if self.return_type is None:
            return None
        func_call = Expr(func_call)
        ret = []

        for i, return_type in enumerate(self.return_type):
            if id(return_type) in primitive_types.type_ids:
                ret.append(
                    Expr(
                        _ti_core.make_get_element_expr(
                            func_call.ptr, (i,), _ti_core.DebugInfo(impl.get_runtime().get_current_src_info())
                        )
                    )
                )
            elif isinstance(return_type, (StructType, MatrixType)):
                ret.append(return_type.from_taichi_object(func_call, (i,)))
            else:
                raise TaichiTypeError(f"Unsupported return type for return value {i}: {return_type}")
        if len(ret) == 1:
            return ret[0]
        return tuple(ret)

    def do_compile(self, key: FunctionKey, args: tuple[Any, ...], arg_features: tuple[Any, ...]) -> None:
        tree, ctx = _get_tree_and_ctx(
            self, is_kernel=False, args=args, arg_features=arg_features, is_real_function=self.is_real_function
        )
        prog = impl.get_runtime().prog
        assert prog is not None
        fn = prog.create_function(key)

        def func_body():
            old_callable = impl.get_runtime().compiling_callable
            impl.get_runtime().compiling_callable = fn
            ctx.ast_builder = fn.ast_builder()
            transform_tree(tree, ctx)
            impl.get_runtime().compiling_callable = old_callable

        self.taichi_functions[key.instance_id] = fn
        self.compiled[key.instance_id] = func_body
        self.taichi_functions[key.instance_id].set_function_body(func_body)

    def extract_arguments(self) -> None:
        sig = inspect.signature(self.func)
        if sig.return_annotation not in (inspect.Signature.empty, None):
            self.return_type = sig.return_annotation
            if (
                isinstance(self.return_type, (types.GenericAlias, typing._GenericAlias))  # type: ignore
                and self.return_type.__origin__ is tuple  # type: ignore
            ):
                self.return_type = self.return_type.__args__  # type: ignore
            if self.return_type is None:
                return
            if not isinstance(self.return_type, (list, tuple)):
                self.return_type = (self.return_type,)
            for i, return_type in enumerate(self.return_type):
                if return_type is Ellipsis:
                    raise TaichiSyntaxError("Ellipsis is not supported in return type annotations")
        params = sig.parameters
        arg_names = params.keys()
        for i, arg_name in enumerate(arg_names):
            param = params[arg_name]
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                raise TaichiSyntaxError("Taichi functions do not support variable keyword parameters (i.e., **kwargs)")
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise TaichiSyntaxError("Taichi functions do not support variable positional parameters (i.e., *args)")
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                raise TaichiSyntaxError("Taichi functions do not support keyword parameters")
            if param.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD:
                raise TaichiSyntaxError('Taichi functions only support "positional or keyword" parameters')
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                if i == 0 and self.classfunc:
                    annotation = template()
                # TODO: pyfunc also need type annotation check when real function is enabled,
                #       but that has to happen at runtime when we know which scope it's called from.
                elif not self.pyfunc and self.is_real_function:
                    raise TaichiSyntaxError(
                        f"Taichi function `{self.func.__name__}` parameter `{arg_name}` must be type annotated"
                    )
            else:
                if isinstance(annotation, ndarray_type.NdarrayType):
                    pass
                elif isinstance(annotation, MatrixType):
                    pass
                elif isinstance(annotation, StructType):
                    pass
                elif id(annotation) in primitive_types.type_ids:
                    pass
                elif type(annotation) == taichi.types.annotations.Template:
                    pass
                elif isinstance(annotation, template):
                    pass
                elif isinstance(annotation, primitive_types.RefType):
                    pass
                elif isinstance(annotation, type) and hasattr(annotation, "__dataclass_fields__"):
                    pass
                else:
                    raise TaichiSyntaxError(f"Invalid type annotation (argument {i}) of Taichi function: {annotation}")
            self.arg_metas.append(ArgMetadata(annotation, param.name, param.default))
            self.orig_arguments.append(ArgMetadata(annotation, param.name, param.default))


def _get_global_vars(_func: Callable) -> dict[str, Any]:
    # Discussions: https://github.com/taichi-dev/taichi/issues/282
    global_vars = _func.__globals__.copy()

    freevar_names = _func.__code__.co_freevars
    closure = _func.__closure__
    if closure:
        freevar_values = list(map(lambda x: x.cell_contents, closure))
        for name, value in zip(freevar_names, freevar_values):
            global_vars[name] = value

    return global_vars


class Kernel:
    counter = 0

    def __init__(self, _func: Callable, autodiff_mode: AutodiffMode, _classkernel=False) -> None:
        self.taichi_callable: TaichiCallable | None = None
        self.func = _func
        self.kernel_counter = Kernel.counter
        Kernel.counter += 1
        assert autodiff_mode in (
            AutodiffMode.NONE,
            AutodiffMode.VALIDATION,
            AutodiffMode.FORWARD,
            AutodiffMode.REVERSE,
        )
        self.autodiff_mode = autodiff_mode
        self.grad: "Kernel | None" = None
        self.arg_metas: list[ArgMetadata] = []
        self.return_type = None
        self.classkernel = _classkernel
        self.extract_arguments()
        self.template_slot_locations = []
        for i, arg in enumerate(self.arg_metas):
            if arg.annotation == template or isinstance(arg.annotation, template):
                self.template_slot_locations.append(i)
        self.mapper = TemplateMapper(self.arg_metas, self.template_slot_locations)
        impl.get_runtime().kernels.append(self)
        self.reset()
        self.kernel_cpp = None
        self.compiled_kernels: dict[CompiledKernelKeyType, KernelCxx] = {}
        self.has_print = False

    def ast_builder(self) -> ASTBuilder:
        assert self.kernel_cpp is not None
        return self.kernel_cpp.ast_builder()

    def reset(self) -> None:
        self.runtime = impl.get_runtime()
        self.compiled_kernels = {}

    def expand_dataclasses(self, params: dict[str, Any]) -> dict[str, Any]:
        new_params = {}
        arg_names = params.keys()
        for i, arg_name in enumerate(arg_names):
            param = params[arg_name]
            annotation = param.annotation
            if isinstance(annotation, type) and hasattr(annotation, "__dataclass_fields__"):
                for field in dataclasses.fields(annotation):
                    # Create a new inspect.Parameter for each dataclass field
                    field_name = "__ti_" + field.name
                    new_param = inspect.Parameter(
                        name=field_name,
                        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=inspect.Parameter.empty,
                        annotation=field.type,
                    )
                    new_params[field_name] = new_param
            else:
                new_params[arg_name] = param
        return new_params

    def extract_arguments(self) -> None:
        sig = inspect.signature(self.func)
        if sig.return_annotation not in (inspect._empty, None):
            self.return_type = sig.return_annotation
            if (
                isinstance(self.return_type, (types.GenericAlias, typing._GenericAlias))  # type: ignore
                and self.return_type.__origin__ is tuple
            ):
                self.return_type = self.return_type.__args__
            if not isinstance(self.return_type, (list, tuple)):
                self.return_type = (self.return_type,)
            for return_type in self.return_type:
                if return_type is Ellipsis:
                    raise TaichiSyntaxError("Ellipsis is not supported in return type annotations")
        params = dict(sig.parameters)
        arg_names = params.keys()
        for i, arg_name in enumerate(arg_names):
            param = params[arg_name]
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                raise TaichiSyntaxError("Taichi kernels do not support variable keyword parameters (i.e., **kwargs)")
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise TaichiSyntaxError("Taichi kernels do not support variable positional parameters (i.e., *args)")
            if param.default is not inspect.Parameter.empty:
                raise TaichiSyntaxError("Taichi kernels do not support default values for arguments")
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                raise TaichiSyntaxError("Taichi kernels do not support keyword parameters")
            if param.kind != inspect.Parameter.POSITIONAL_OR_KEYWORD:
                raise TaichiSyntaxError('Taichi kernels only support "positional or keyword" parameters')
            annotation = param.annotation
            if param.annotation is inspect.Parameter.empty:
                if i == 0 and self.classkernel:  # The |self| parameter
                    annotation = template()
                else:
                    raise TaichiSyntaxError("Taichi kernels parameters must be type annotated")
            else:
                if isinstance(
                    annotation,
                    (
                        template,
                        ndarray_type.NdarrayType,
                        texture_type.TextureType,
                        texture_type.RWTextureType,
                    ),
                ):
                    pass
                elif id(annotation) in primitive_types.type_ids:
                    pass
                elif isinstance(annotation, sparse_matrix_builder):
                    pass
                elif isinstance(annotation, MatrixType):
                    pass
                elif isinstance(annotation, StructType):
                    pass
                elif isinstance(annotation, ArgPackType):
                    pass
                elif annotation == template:
                    pass
                elif isinstance(annotation, type) and hasattr(annotation, "__dataclass_fields__"):
                    pass
                else:
                    raise TaichiSyntaxError(f"Invalid type annotation (argument {i}) of Taichi kernel: {annotation}")
            self.arg_metas.append(ArgMetadata(annotation, param.name, param.default))

    def materialize(self, key: CompiledKernelKeyType | None, args: tuple[Any, ...], arg_features):
        start = time.time()
        if key is None:
            key = (self.func, 0, self.autodiff_mode)
        self.runtime.materialize()

        self.compiled_kernel_data = None
        self.fast_checksum = None
        if self.taichi_callable and self.taichi_callable.is_pure:
            print("pure function:", self.func.__name__)
            self.fast_checksum = fast_cacher.walk_functions(self.func)
            if self.func.__name__ not in ["ndarray_to_ext_arr", "ext_arr_to_ndarray", "ndarray_matrix_to_ext_arr", "ext_arr_to_ndarray_matrix"]:
                print('fast_checksum', self.fast_checksum)
                print(self.func.__name__)
                print('elapsed', time.time() - start)
                print("key", key)
                # return

            prog = impl.get_runtime().prog
            # compiled_kernel_data = prog.load_fast_cache(self.fast_checksum)
            print("dir(self.func)", dir(self.func), self)
            # if getattr(self, "enable_fast_cache", False):
            print("check fast cache")
            print("prog.config()", prog.config())
            print("prog.get_device_caps()", prog.get_device_caps())
            self.compiled_kernel_data = prog.load_fast_cache(
                self.fast_checksum,
                self.func.__name__,
                prog.config(),
                prog.get_device_caps(),
            )
            if self.compiled_kernel_data:
                print("loaded from fast cache: compiled_kernel_data", self.compiled_kernel_data)
    #           const std::string &checksum,
    #   const std::string &kernel_name,
    #   const CompileConfig &compile_config,
    #   const DeviceCapabilityConfig &caps);

        # print("compiled_kernel_data", compiled_kernel_data)
        # if self.compiled_kernel_data:
        #     self.compiled_kernels[key] = self.compiled_kernel_data
        #     ...

        if key in self.compiled_kernels:
            return

        kernel_name = f"{self.func.__name__}_c{self.kernel_counter}_{key[1]}"
        _logging.trace(f"Compiling kernel {kernel_name} in {self.autodiff_mode}...")
        tree, ctx = _get_tree_and_ctx(
            self,
            args=args,
            excluded_parameters=self.template_slot_locations,
            arg_features=arg_features,
        )

        if self.autodiff_mode != AutodiffMode.NONE:
            KernelSimplicityASTChecker(self.func).visit(tree)

        # Do not change the name of 'taichi_ast_generator'
        # The warning system needs this identifier to remove unnecessary messages
        def taichi_ast_generator(kernel_cxx: KernelCxx):
            nonlocal tree
            if self.runtime.inside_kernel:
                raise TaichiSyntaxError(
                    "Kernels cannot call other kernels. I.e., nested kernels are not allowed. "
                    "Please check if you have direct/indirect invocation of kernels within kernels. "
                    "Note that some methods provided by the Taichi standard library may invoke kernels, "
                    "and please move their invocations to Python-scope."
                )
            self.kernel_cpp = kernel_cxx
            self.runtime.inside_kernel = True
            self.runtime.current_kernel = self
            assert self.runtime.compiling_callable is None
            self.runtime.compiling_callable = kernel_cxx
            try:
                ctx.ast_builder = kernel_cxx.ast_builder()

                def ast_to_dict(node: ast.AST | list | primitive_types._python_primitive_types):
                    if isinstance(node, ast.AST):
                        fields = {k: ast_to_dict(v) for k, v in ast.iter_fields(node)}
                        return {
                            "type": node.__class__.__name__,
                            "fields": fields,
                            "lineno": getattr(node, "lineno", None),
                            "col_offset": getattr(node, "col_offset", None),
                        }
                    if isinstance(node, list):
                        return [ast_to_dict(x) for x in node]
                    return node  # Basic types (str, int, None, etc.)

                if os.environ.get("TI_DUMP_AST", "") == "1":
                    target_dir = pathlib.Path("/tmp/ast")
                    target_dir.mkdir(parents=True, exist_ok=True)

                    start = time.time()
                    ast_str = ast.dump(tree, indent=2)
                    output_file = target_dir / f"{kernel_name}_ast.txt"
                    output_file.write_text(ast_str)
                    elapsed_txt = time.time() - start

                    start = time.time()
                    json_str = json.dumps(ast_to_dict(tree), indent=2)
                    output_file = target_dir / f"{kernel_name}_ast.json"
                    output_file.write_text(json_str)
                    elapsed_json = time.time() - start

                    output_file = target_dir / f"{kernel_name}_gen_time.json"
                    output_file.write_text(
                        json.dumps({"elapsed_txt": elapsed_txt, "elapsed_json": elapsed_json}, indent=2)
                    )
                if True:
                    struct_locals = _kernel_impl_dataclass.populate_struct_locals(ctx)
                    tree = _kernel_impl_dataclass.unpack_ast_struct_expressions(tree, struct_locals=struct_locals)
                    ctx.only_parse_function_def = self.compiled_kernel_data is not None
                    start = time.time()
                    transform_tree(tree, ctx)
                    elapsed = time.time() - start
                    # print("transform tree time", elapsed)
                    if not ctx.is_real_function:
                        if self.return_type and ctx.returned != ReturnStatus.ReturnedValue:
                            raise TaichiSyntaxError("Kernel has a return type but does not have a return statement")
                else:
                    class FunctionDefWalker(ast.NodeTransformer):
                        def visit_FunctionDef(self, node: ast.FunctionDef):
                            print("got functiondef ", node.name)
                            # ast_transformer.build_FunctionDef(ctx, node)
                            # ast_transformer.
                            function_def_transformer._transform_as_kernel(ctx, node, node.args)
                            return self.generic_visit(node)

                    ast_transformer = ASTTransformer()
                    function_def_transformer = FunctionDefTransformer()
                    function_def_walker = FunctionDefWalker()
                    function_def_walker.visit(tree)
                    asdasdf
                    # ast.fix_missing_locations(new_tree)
            finally:
                self.runtime.inside_kernel = False
                self.runtime.current_kernel = None
                self.runtime.compiling_callable = None

        prog = impl.get_runtime().prog
        assert prog is not None
        # print("prog.create_kernel")
        taichi_kernel = prog.create_kernel(taichi_ast_generator, kernel_name, self.autodiff_mode)
        assert key not in self.compiled_kernels
        self.compiled_kernels[key] = taichi_kernel

    def launch_kernel(self, t_kernel: KernelCxx, *args) -> Any:
        assert len(args) == len(self.arg_metas), f"{len(self.arg_metas)} arguments needed but {len(args)} provided"

        tmps = []
        callbacks = []

        actual_argument_slot = 0
        launch_ctx = t_kernel.make_launch_context()
        max_arg_num = 64
        exceed_max_arg_num = False

        def set_arg_ndarray(indices: tuple[int, ...], v: taichi.lang._ndarray.Ndarray) -> None:
            v_primal = v.arr
            v_grad = v.grad.arr if v.grad else None
            if v_grad is None:
                launch_ctx.set_arg_ndarray(indices, v_primal)  # type: ignore , solvable probably, just not today
            else:
                launch_ctx.set_arg_ndarray_with_grad(indices, v_primal, v_grad)  # type: ignore

        def set_arg_texture(indices: tuple[int, ...], v: taichi.lang._texture.Texture) -> None:
            launch_ctx.set_arg_texture(indices, v.tex)

        def set_arg_rw_texture(indices: tuple[int, ...], v: taichi.lang._texture.Texture) -> None:
            launch_ctx.set_arg_rw_texture(indices, v.tex)

        def set_arg_ext_array(indices: tuple[int, ...], v: Any, needed: ndarray_type.NdarrayType) -> None:
            # v is things like torch Tensor and numpy array
            # Not adding type for this, since adds additional dependencies
            #
            # Element shapes are already specialized in Taichi codegen.
            # The shape information for element dims are no longer needed.
            # Therefore we strip the element shapes from the shape vector,
            # so that it only holds "real" array shapes.
            is_soa = needed.layout == Layout.SOA
            array_shape = v.shape
            if functools.reduce(operator.mul, array_shape, 1) > np.iinfo(np.int32).max:
                warnings.warn("Ndarray index might be out of int32 boundary but int64 indexing is not supported yet.")
            if needed.dtype is None or id(needed.dtype) in primitive_types.type_ids:
                element_dim = 0
            else:
                element_dim = needed.dtype.ndim
                array_shape = v.shape[element_dim:] if is_soa else v.shape[:-element_dim]
            if isinstance(v, np.ndarray):
                if v.flags.c_contiguous:
                    launch_ctx.set_arg_external_array_with_shape(indices, int(v.ctypes.data), v.nbytes, array_shape, 0)
                elif v.flags.f_contiguous:
                    # TODO: A better way that avoids copying is saving strides info.
                    tmp = np.ascontiguousarray(v)
                    # Purpose: DO NOT GC |tmp|!
                    tmps.append(tmp)

                    def callback(original, updated):
                        np.copyto(original, np.asfortranarray(updated))

                    callbacks.append(functools.partial(callback, v, tmp))
                    launch_ctx.set_arg_external_array_with_shape(
                        indices, int(tmp.ctypes.data), tmp.nbytes, array_shape, 0
                    )
                else:
                    raise ValueError(
                        "Non contiguous numpy arrays are not supported, please call np.ascontiguousarray(arr) "
                        "before passing it into taichi kernel."
                    )
            elif has_pytorch():
                import torch  # pylint: disable=C0415

                if isinstance(v, torch.Tensor):
                    if not v.is_contiguous():
                        raise ValueError(
                            "Non contiguous tensors are not supported, please call tensor.contiguous() before "
                            "passing it into taichi kernel."
                        )
                    prog = self.runtime.prog
                    assert prog is not None
                    taichi_arch = prog.config().arch

                    def get_call_back(u, v):
                        def call_back():
                            u.copy_(v)

                        return call_back

                    # FIXME: only allocate when launching grad kernel
                    if v.requires_grad and v.grad is None:
                        v.grad = torch.zeros_like(v)

                    if v.requires_grad:
                        if not isinstance(v.grad, torch.Tensor):
                            raise ValueError(
                                f"Expecting torch.Tensor for gradient tensor, but getting {v.grad.__class__.__name__} instead"
                            )
                        if not v.grad.is_contiguous():
                            raise ValueError(
                                "Non contiguous gradient tensors are not supported, please call tensor.grad.contiguous() before passing it into taichi kernel."
                            )

                    tmp = v
                    if (str(v.device) != "cpu") and not (
                        str(v.device).startswith("cuda") and taichi_arch == _ti_core.Arch.cuda
                    ):
                        # Getting a torch CUDA tensor on Taichi non-cuda arch:
                        # We just replace it with a CPU tensor and by the end of kernel execution we'll use the
                        # callback to copy the values back to the original CUDA tensor.
                        host_v = v.to(device="cpu", copy=True)
                        tmp = host_v
                        callbacks.append(get_call_back(v, host_v))

                    launch_ctx.set_arg_external_array_with_shape(
                        indices,
                        int(tmp.data_ptr()),
                        tmp.element_size() * tmp.nelement(),
                        array_shape,
                        int(v.grad.data_ptr()) if v.grad is not None else 0,
                    )
                else:
                    raise TaichiRuntimeTypeError(f"Argument {needed} cannot be converted into required type {v}")
            elif has_paddle():
                # Do we want to continue to support paddle? :thinking_face:
                import paddle  # pylint: disable=C0415  # type: ignore

                if isinstance(v, paddle.Tensor):
                    # For now, paddle.fluid.core.Tensor._ptr() is only available on develop branch
                    def get_call_back(u, v):
                        def call_back():
                            u.copy_(v, False)

                        return call_back

                    tmp = v.value().get_tensor()
                    prog = self.runtime.prog
                    assert prog is not None
                    taichi_arch = prog.config().arch
                    if v.place.is_gpu_place():
                        if taichi_arch != _ti_core.Arch.cuda:
                            # Paddle cuda tensor on Taichi non-cuda arch
                            host_v = v.cpu()
                            tmp = host_v.value().get_tensor()
                            callbacks.append(get_call_back(v, host_v))
                    elif v.place.is_cpu_place():
                        if taichi_arch == _ti_core.Arch.cuda:
                            # Paddle cpu tensor on Taichi cuda arch
                            gpu_v = v.cuda()
                            tmp = gpu_v.value().get_tensor()
                            callbacks.append(get_call_back(v, gpu_v))
                    else:
                        # Paddle do support many other backends like XPU, NPU, MLU, IPU
                        raise TaichiRuntimeTypeError(f"Taichi do not support backend {v.place} that Paddle support")
                    launch_ctx.set_arg_external_array_with_shape(
                        indices, int(tmp._ptr()), v.element_size() * v.size, array_shape, 0
                    )
                else:
                    raise TaichiRuntimeTypeError(f"Argument {needed} cannot be converted into required type {v}")
            else:
                raise TaichiRuntimeTypeError(f"Argument {needed} cannot be converted into required type {v}")

        def set_arg_matrix(indices: tuple[int, ...], v, needed) -> None:
            def cast_float(x: float | np.floating | np.integer | int) -> float:
                if not isinstance(x, (int, float, np.integer, np.floating)):
                    raise TaichiRuntimeTypeError(
                        f"Argument {needed.dtype.to_string()} cannot be converted into required type {type(x)}"
                    )
                return float(x)

            def cast_int(x: int | np.integer) -> int:
                if not isinstance(x, (int, np.integer)):
                    raise TaichiRuntimeTypeError(
                        f"Argument {needed.dtype.to_string()} cannot be converted into required type {type(x)}"
                    )
                return int(x)

            cast_func = None
            if needed.dtype in primitive_types.real_types:
                cast_func = cast_float
            elif needed.dtype in primitive_types.integer_types:
                cast_func = cast_int
            else:
                raise ValueError(f"Matrix dtype {needed.dtype} is not integer type or real type.")

            if needed.ndim == 2:
                v = [cast_func(v[i, j]) for i in range(needed.n) for j in range(needed.m)]
            else:
                v = [cast_func(v[i]) for i in range(needed.n)]
            v = needed(*v)
            needed.set_kernel_struct_args(v, launch_ctx, indices)

        def set_arg_sparse_matrix_builder(indices: tuple[int, ...], v) -> None:
            # Pass only the base pointer of the ti.types.sparse_matrix_builder() argument
            launch_ctx.set_arg_uint(indices, v._get_ndarray_addr())

        set_later_list = []

        def recursive_set_args(needed: Type, provided: Type, v: Any, indices: tuple[int, ...]) -> int:
            in_argpack = len(indices) > 1
            nonlocal actual_argument_slot, exceed_max_arg_num, set_later_list
            if actual_argument_slot >= max_arg_num:
                exceed_max_arg_num = True
                return 0
            actual_argument_slot += 1
            if isinstance(needed, ArgPackType):
                if not isinstance(v, ArgPack):
                    raise TaichiRuntimeTypeError.get(indices, str(needed), str(provided))
                idx_new = 0
                for j, (name, anno) in enumerate(needed.members.items()):
                    idx_new += recursive_set_args(anno, type(v[name]), v[name], indices + (idx_new,))
                launch_ctx.set_arg_argpack(indices, v._ArgPack__argpack)  # type: ignore
                return 1
            # Note: do not use sth like "needed == f32". That would be slow.
            if id(needed) in primitive_types.real_type_ids:
                if not isinstance(v, (float, int, np.floating, np.integer)):
                    raise TaichiRuntimeTypeError.get(indices, needed.to_string(), provided)
                if in_argpack:
                    return 1
                launch_ctx.set_arg_float(indices, float(v))
                return 1
            if id(needed) in primitive_types.integer_type_ids:
                if not isinstance(v, (int, np.integer)):
                    raise TaichiRuntimeTypeError.get(indices, needed.to_string(), provided)
                if in_argpack:
                    return 1
                if is_signed(cook_dtype(needed)):
                    launch_ctx.set_arg_int(indices, int(v))
                else:
                    launch_ctx.set_arg_uint(indices, int(v))
                return 1
            if isinstance(needed, sparse_matrix_builder):
                if in_argpack:
                    set_later_list.append((set_arg_sparse_matrix_builder, (v,)))
                    return 0
                set_arg_sparse_matrix_builder(indices, v)
                return 1
            if dataclasses.is_dataclass(needed):
                assert provided == needed
                dataclass_type = needed
                idx = 0
                for j, field in enumerate(dataclasses.fields(dataclass_type)):
                    field_name = field.name
                    field_type = field.type
                    assert not isinstance(field_type, str)
                    field_value = getattr(v, field_name)
                    idx += recursive_set_args(field_type, field_type, field_value, (indices[0] + idx,))
                return idx
            if isinstance(needed, ndarray_type.NdarrayType) and isinstance(v, taichi.lang._ndarray.Ndarray):
                if in_argpack:
                    set_later_list.append((set_arg_ndarray, (v,)))
                    return 0
                set_arg_ndarray(indices, v)
                return 1
            if isinstance(needed, texture_type.TextureType) and isinstance(v, taichi.lang._texture.Texture):
                if in_argpack:
                    set_later_list.append((set_arg_texture, (v,)))
                    return 0
                set_arg_texture(indices, v)
                return 1
            if isinstance(needed, texture_type.RWTextureType) and isinstance(v, taichi.lang._texture.Texture):
                if in_argpack:
                    set_later_list.append((set_arg_rw_texture, (v,)))
                    return 0
                set_arg_rw_texture(indices, v)
                return 1
            if isinstance(needed, ndarray_type.NdarrayType):
                if in_argpack:
                    set_later_list.append((set_arg_ext_array, (v, needed)))
                    return 0
                set_arg_ext_array(indices, v, needed)
                return 1
            if isinstance(needed, MatrixType):
                if in_argpack:
                    return 1
                set_arg_matrix(indices, v, needed)
                return 1
            if isinstance(needed, StructType):
                if in_argpack:
                    return 1
                if not isinstance(v, needed):  # type: ignore Might be invalid? Maybe should rewrite as: not needed.__instancecheck__(v) ?
                    raise TaichiRuntimeTypeError(f"Argument {provided} cannot be converted into required type {needed}")
                needed.set_kernel_struct_args(v, launch_ctx, indices)
                return 1
            if isinstance(needed, template) or needed == template:
                return 0
            raise ValueError(f"Argument type mismatch. Expecting {needed}, got {type(v)}.")

        template_num = 0
        i_out = 0
        for i_in, val in enumerate(args):
            needed_ = self.arg_metas[i_in].annotation
            if needed_ == template or isinstance(needed_, template):
                template_num += 1
                i_out += 1
                continue
            i_out += recursive_set_args(needed_, type(val), val, (i_out - template_num,))

        for i, (set_arg_func, params) in enumerate(set_later_list):
            set_arg_func((len(args) - template_num + i,), *params)

        if exceed_max_arg_num:
            raise TaichiRuntimeError(
                f"The number of elements in kernel arguments is too big! Do not exceed {max_arg_num} on {_ti_core.arch_name(impl.current_cfg().arch)} backend."
            )

        try:
            prog = impl.get_runtime().prog
            assert prog is not None
            # print("prog.compile_kernel")
            # Compile kernel (& Online Cache & Offline Cache)
            if not self.compiled_kernel_data:
                # print("no compiled kernel data => compiling, or loading from cache")
                self.compiled_kernel_data = prog.compile_kernel(prog.config(), prog.get_device_caps(), t_kernel)
                if self.fast_checksum:
                    # print("storing to fast cache", self.fast_checksum)
                    prog.store_fast_cache(
                        self.fast_checksum,
                        self.kernel_cpp,
                        prog.config(),
                        prog.get_device_caps(),
                        self.compiled_kernel_data
                    )
            # else:
                # print("using ckd from warm cache")
            # prog.dump_cache_data_to_disk()
            # Launch kernel
            # print("launching...")
            prog.launch_kernel(self.compiled_kernel_data, launch_ctx)
            # print("... launched")
        except Exception as e:
            e = handle_exception_from_cpp(e)
            if impl.get_runtime().print_full_traceback:
                raise e
            raise e from None

        ret = None
        ret_dt = self.return_type
        has_ret = ret_dt is not None

        if has_ret or self.has_print:
            runtime_ops.sync()

        if has_ret:
            ret = []
            for i, ret_type in enumerate(ret_dt):
                ret.append(self.construct_kernel_ret(launch_ctx, ret_type, (i,)))
            if len(ret_dt) == 1:
                ret = ret[0]
        if callbacks:
            for c in callbacks:
                c()

        return ret

    def construct_kernel_ret(self, launch_ctx: KernelLaunchContext, ret_type: Any, index: tuple[int, ...] = ()):
        if isinstance(ret_type, CompoundType):
            return ret_type.from_kernel_struct_ret(launch_ctx, index)
        if ret_type in primitive_types.integer_types:
            if is_signed(cook_dtype(ret_type)):
                return launch_ctx.get_struct_ret_int(index)
            return launch_ctx.get_struct_ret_uint(index)
        if ret_type in primitive_types.real_types:
            return launch_ctx.get_struct_ret_float(index)
        raise TaichiRuntimeTypeError(f"Invalid return type on index={index}")

    def ensure_compiled(self, *args: tuple[Any, ...]) -> tuple[Callable, int, AutodiffMode]:
        instance_id, arg_features = self.mapper.lookup(args)
        key = (self.func, instance_id, self.autodiff_mode)
        self.materialize(key=key, args=args, arg_features=arg_features)
        return key

    # For small kernels (< 3us), the performance can be pretty sensitive to overhead in __call__
    # Thus this part needs to be fast. (i.e. < 3us on a 4 GHz x64 CPU)
    @_shell_pop_print
    def __call__(self, *args, **kwargs) -> Any:
        args = _process_args(self, is_func=False, py_args=args, py_kwargs=kwargs)

        # Transform the primal kernel to forward mode grad kernel
        # then recover to primal when exiting the forward mode manager
        if self.runtime.fwd_mode_manager and not self.runtime.grad_replaced:
            # TODO: if we would like to compute 2nd-order derivatives by forward-on-reverse in a nested context manager fashion,
            # i.e., a `Tape` nested in the `FwdMode`, we can transform the kernels with `mode_original == AutodiffMode.REVERSE` only,
            # to avoid duplicate computation for 1st-order derivatives
            self.runtime.fwd_mode_manager.insert(self)

        # Both the class kernels and the plain-function kernels are unified now.
        # In both cases, |self.grad| is another Kernel instance that computes the
        # gradient. For class kernels, args[0] is always the kernel owner.

        # No need to capture grad kernels because they are already bound with their primal kernels
        if (
            self.autodiff_mode in (AutodiffMode.NONE, AutodiffMode.VALIDATION)
            and self.runtime.target_tape
            and not self.runtime.grad_replaced
        ):
            self.runtime.target_tape.insert(self, args)

        if self.autodiff_mode != AutodiffMode.NONE and impl.current_cfg().opt_level == 0:
            _logging.warn("""opt_level = 1 is enforced to enable gradient computation.""")
            impl.current_cfg().opt_level = 1
        key = self.ensure_compiled(*args)
        # print("getting kernel_cpp from compiled kernels using key", key)
        kernel_cpp = self.compiled_kernels[key]
        # print("got kernel_cpp", kernel_cpp)
        return self.launch_kernel(kernel_cpp, *args)


# For a Taichi class definition like below:
#
# @ti.data_oriented
# class X:
#   @ti.kernel
#   def foo(self):
#     ...
#
# When ti.kernel runs, the stackframe's |code_context| of Python 3.8(+) is
# different from that of Python 3.7 and below. In 3.8+, it is 'class X:',
# whereas in <=3.7, it is '@ti.data_oriented'. More interestingly, if the class
# inherits, i.e. class X(object):, then in both versions, |code_context| is
# 'class X(object):'...
_KERNEL_CLASS_STACKFRAME_STMT_RES = [
    re.compile(r"@(\w+\.)?data_oriented"),
    re.compile(r"class "),
]


def _inside_class(level_of_class_stackframe: int) -> bool:
    try:
        maybe_class_frame = sys._getframe(level_of_class_stackframe)
        statement_list = inspect.getframeinfo(maybe_class_frame)[3]
        if statement_list is None:
            return False
        first_statment = statement_list[0].strip()
        for pat in _KERNEL_CLASS_STACKFRAME_STMT_RES:
            if pat.match(first_statment):
                return True
    except:
        pass
    return False


def _kernel_impl(_func: Callable, level_of_class_stackframe: int, verbose: bool = False) -> TaichiCallable:
    # Can decorators determine if a function is being defined inside a class?
    # https://stackoverflow.com/a/8793684/12003165
    is_classkernel = _inside_class(level_of_class_stackframe + 1)

    if verbose:
        print(f"kernel={_func.__name__} is_classkernel={is_classkernel}")
    primal = Kernel(_func, autodiff_mode=AutodiffMode.NONE, _classkernel=is_classkernel)
    adjoint = Kernel(_func, autodiff_mode=AutodiffMode.REVERSE, _classkernel=is_classkernel)
    # Having |primal| contains |grad| makes the tape work.
    primal.grad = adjoint

    wrapped: TaichiCallable
    if is_classkernel:
        # For class kernels, their primal/adjoint callables are constructed
        # when the kernel is accessed via the instance inside
        # _BoundedDifferentiableMethod.
        # This is because we need to bind the kernel or |grad| to the instance
        # owning the kernel, which is not known until the kernel is accessed.
        #
        # See also: _BoundedDifferentiableMethod, data_oriented.
        @functools.wraps(_func)
        def wrapped_classkernel(*args, **kwargs):
            # If we reach here (we should never), it means the class is not decorated
            # with @ti.data_oriented, otherwise getattr would have intercepted the call.
            clsobj = type(args[0])
            assert not hasattr(clsobj, "_data_oriented")
            raise TaichiSyntaxError(f"Please decorate class {clsobj.__name__} with @ti.data_oriented")

        wrapped = TaichiCallable(
            _func,
            wrapped_classkernel,
        )
    else:

        @functools.wraps(_func)
        def wrapped_func(*args, **kwargs):
            try:
                return primal(*args, **kwargs)
            except (TaichiCompilationError, TaichiRuntimeError) as e:
                if impl.get_runtime().print_full_traceback:
                    raise e
                raise type(e)("\n" + str(e)) from None

        wrapped = TaichiCallable(
            _func,
            wrapped_func,
        )
        wrapped.grad = adjoint

    wrapped._is_wrapped_kernel = True
    wrapped._is_classkernel = is_classkernel
    wrapped._primal = primal
    wrapped._adjoint = adjoint
    primal.taichi_callable = wrapped
    return wrapped


def kernel(fn: Callable):
    """Marks a function as a Taichi kernel.

    A Taichi kernel is a function written in Python, and gets JIT compiled by
    Taichi into native CPU/GPU instructions (e.g. a series of CUDA kernels).
    The top-level ``for`` loops are automatically parallelized, and distributed
    to either a CPU thread pool or massively parallel GPUs.

    Kernel's gradient kernel would be generated automatically by the AutoDiff system.

    See also https://docs.taichi-lang.org/docs/syntax#kernel.

    Args:
        fn (Callable): the Python function to be decorated

    Returns:
        Callable: The decorated function

    Example::

        >>> x = ti.field(ti.i32, shape=(4, 8))
        >>>
        >>> @ti.kernel
        >>> def run():
        >>>     # Assigns all the elements of `x` in parallel.
        >>>     for i in x:
        >>>         x[i] = i
    """
    return _kernel_impl(fn, level_of_class_stackframe=3)


class _BoundedDifferentiableMethod:
    def __init__(self, kernel_owner: Any, wrapped_kernel_func: TaichiCallable | BoundFunc):
        clsobj = type(kernel_owner)
        if not getattr(clsobj, "_data_oriented", False):
            raise TaichiSyntaxError(f"Please decorate class {clsobj.__name__} with @ti.data_oriented")
        self._kernel_owner = kernel_owner
        self._primal = wrapped_kernel_func._primal
        self._adjoint = wrapped_kernel_func._adjoint
        self._is_staticmethod = wrapped_kernel_func._is_staticmethod
        self.__name__: str | None = None

    def __call__(self, *args, **kwargs):
        try:
            assert self._primal is not None
            if self._is_staticmethod:
                return self._primal(*args, **kwargs)
            return self._primal(self._kernel_owner, *args, **kwargs)

        except (TaichiCompilationError, TaichiRuntimeError) as e:
            if impl.get_runtime().print_full_traceback:
                raise e
            raise type(e)("\n" + str(e)) from None

    def grad(self, *args, **kwargs) -> Kernel:
        assert self._adjoint is not None
        return self._adjoint(self._kernel_owner, *args, **kwargs)


def data_oriented(cls):
    """Marks a class as Taichi compatible.

    To allow for modularized code, Taichi provides this decorator so that
    Taichi kernels can be defined inside a class.

    See also https://docs.taichi-lang.org/docs/odop

    Example::

        >>> @ti.data_oriented
        >>> class TiArray:
        >>>     def __init__(self, n):
        >>>         self.x = ti.field(ti.f32, shape=n)
        >>>
        >>>     @ti.kernel
        >>>     def inc(self):
        >>>         for i in self.x:
        >>>             self.x[i] += 1.0
        >>>
        >>> a = TiArray(32)
        >>> a.inc()

    Args:
        cls (Class): the class to be decorated

    Returns:
        The decorated class.
    """

    def _getattr(self, item):
        method = cls.__dict__.get(item, None)
        is_property = method.__class__ == property
        is_staticmethod = method.__class__ == staticmethod
        if is_property:
            x = method.fget
        else:
            x = super(cls, self).__getattribute__(item)
        if hasattr(x, "_is_wrapped_kernel"):
            if inspect.ismethod(x):
                wrapped = x.__func__
            else:
                wrapped = x
            assert isinstance(wrapped, (BoundFunc, TaichiCallable))
            wrapped._is_staticmethod = is_staticmethod
            if wrapped._is_classkernel:
                ret = _BoundedDifferentiableMethod(self, wrapped)
                ret.__name__ = wrapped.__name__  # type: ignore
                if is_property:
                    return ret()
                return ret
        if is_property:
            return x(self)
        return x

    cls.__getattribute__ = _getattr
    cls._data_oriented = True

    return cls


__all__ = ["data_oriented", "func", "kernel", "pyfunc", "real_func"]
