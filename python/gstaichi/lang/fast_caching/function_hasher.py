import ast
import hashlib
import importlib
import inspect
import re
import time
from typing import cast, TYPE_CHECKING


if TYPE_CHECKING:
    from gstaichi.lang.kernel_impl import GsTaichiCallable


indent_re = re.compile(r"^ +")


g_total_hash_kernel_time = 0


def pure(fn: "GsTaichiCallable") -> "GsTaichiCallable":
    # print('fn', fn, type(fn), "marking pure")
    fn.is_pure = True
    return fn


class FunctionHasher:
    def __init__(self) -> None:
        self.seen_full_paths = set()
        self.checksummed_paths = set()

    @staticmethod
    def _unindent(source):
        match_res = indent_re.match(source)
        # print('match_res', match_res)
        if not match_res:
            # print("no need for unindent")
            return source
        unindent_len = match_res.span()[1]
        source_l = source.split('\n')
        # print('unindent_len', unindent_len)
        new_source_l = []
        for line in source_l:
            new_source_l.append(line[unindent_len:])
        return "\n".join(new_source_l)

    @staticmethod
    def _flatten_name(att: ast.Attribute):
        child = att.value
        if isinstance(child, ast.Attribute):
            child_name = FunctionHasher._flatten_name(child)
        elif isinstance(child, ast.Name):
            child_name = child.id
        elif isinstance(child, ast.Call):
            child_name = ""
        elif isinstance(child, ast.Compare):
            child_name = "COMPARE"
        elif isinstance(child, ast.Subscript):
            child_name = "SUBSCRIPT"
        else:
            child_name = child.__class__.__name__
        self_name = att.attr
        return child_name + "." + self_name

    @staticmethod
    def _unwrap(fn):
        # print("fn", fn, "type(fn)", type(fn))
        from gstaichi.lang.kernel_impl import GsTaichiCallable
        if isinstance(fn, GsTaichiCallable):
            fn = fn.fn
        return fn

    def hash_function(self, fn) -> str:
        start = time.time()
        # print("walk_function", FastCacher.unwrap(fn))
        source = inspect.getsource(fn)
        source = FunctionHasher._unindent(source)
        # print(source)
        unwrap = FunctionHasher._unwrap

        parsed = ast.parse(source)
        # print('parsed', parsed)
        dumped = ast.dump(parsed, indent=2)
        function_checksum_l = [hashlib.sha256(dumped.encode('utf-8')).hexdigest()]
        # print('function_checksum', function_checksum_l)

        module_name = fn.__module__
        mod = importlib.import_module(module_name)
        # print("mod", mod)
        # print("mod dict", mod.__dict__.keys())

        to_visit = []

        for call in [node for node in ast.walk(parsed) if isinstance(node, ast.Call)]:
            # print('call', ast.dump(call, indent=2))
            if isinstance(call.func, ast.Name):
                # print("is ast.Name")
                func_name = call.func.id
                if func_name in ["range"]:
                    continue
                module_name = fn.__module__
                # print("module_name", module_name, type(module_name))
                # print("fn", fn.__dict__.keys(), type(fn), type(unwrap(fn)))
                func_obj = None
                closure = unwrap(fn).__closure__
                if closure:
                    freevars = unwrap(fn).__code__.co_freevars
                    closure_values = [cell.cell_contents for cell in closure]
                    closure_dict = dict(zip(freevars, closure_values))
                    if func_name in closure_dict:
                        func_obj = closure_dict[func_name]
                if func_obj is None:
                    # print("__globals__", unwrap(fn).__globals__.keys())
                    # print("func_name", func_name)
                    if func_name not in unwrap(fn).__globals__:
                        continue
                    func_obj = unwrap(fn).__globals__[func_name]
                if func_obj is not None:
                    # print('func_obj', func_obj, "type(func_obj)", type(func_obj))
                    # print("hasattr _is_in_gstaichi_scope", hasattr(func_obj, "_is_in_gstaichi_scope"))
                    if hasattr(func_obj, "_is_in_gstaichi_scope"):
                        continue
                    to_visit.append((module_name + "." + func_name, func_obj))
            elif isinstance(call.func, ast.Attribute):
                # print("is ast.Attribute")
                func = cast(ast.Attribute, call.func)
                flat_name = FunctionHasher._flatten_name(func)
                if flat_name in self.seen_full_paths:
                    continue
                self.seen_full_paths.add(flat_name)
                if flat_name in ["ti.Vector.zero", "ti.Vector", ".normalized", "gstaichi._kernels.static"]:
                    continue
                skip = False
                for prefix in ["COMPARE.", "ti."]:
                    if flat_name.startswith(prefix):
                        skip = True
                        break
                if skip:
                    continue
                # print("flat_name", flat_name)
                module_name, _, func_name = flat_name.rpartition(".")
                # print("module_name", module_name, "func_name", func_name)
                if func_name in ["norm"]:
                    continue
                # print("module_name", module_name, "func_name", func_name)
                # print("hasattr dict", hasattr(mod, "__dict__"))
                if not hasattr(mod, "__dict__") or module_name not in mod.__dict__:
                    print("skipping", module_name)
                    # with open("/tmp/skipped.txt", "a") as f:
                    #     f.write(module_name + "." + func_name + "\n")
                    continue
                mod = mod.__dict__[module_name]
                func_obj = getattr(mod, func_name, None)
                # print("hasattr _is_in_gstaichi_scope", hasattr(func_obj, "_is_in_gstaichi_scope"))
                if hasattr(func_obj, "_is_in_gstaichi_scope"):
                    continue
                to_visit.append((flat_name, func_obj))
            else:
                raise Exception("Unexpected function node type " + ast.dump(call.func))
        # print("to_visit", to_visit)
        for flat_name, func_obj in to_visit:
            if flat_name in self.seen_full_paths:
                continue
            # print("============================")
            # print(flat_name, getattr(func_obj, "fn", func_obj))
            self.seen_full_paths.add(flat_name)
            self.checksummed_paths.add(flat_name)
            function_checksum_l.append(self.hash_function(func_obj))
        checksum_concat = "".join(function_checksum_l)
        hash = hashlib.sha256(checksum_concat.encode('utf-8')).hexdigest()
        elapsed = time.time() - start
        # print(fn.__name__, 'elapsed', elapsed, 'hash', hash[:20])
        # for flat_name in self.checksummed_paths:
        #     print(flat_name)
        return hash

def hash_kernel(kernel_fn) -> str:
    global g_total_hash_kernel_time
    fast_cacher = FunctionHasher()
    start = time.time()
    res = fast_cacher.hash_function(kernel_fn)
    g_total_hash_kernel_time += time.time() - start
    return res


def dump_stats() -> None:
    print("functio_hasher dump stats")
    print("g_total_hash_kernel_time", g_total_hash_kernel_time)
