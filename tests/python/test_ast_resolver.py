import ast
from collections import namedtuple

from gstaichi.lang.ast.symbol_resolver import ASTResolver


def test_ast_resolver_basic():
    # import within the function to avoid polluting the global scope
    import gstaichi as ti

    ti.init()
    node = ast.parse("ti.kernel", mode="eval").body
    assert ASTResolver.resolve_to(node, ti.kernel, locals())


def test_ast_resolver_direct_import():
    import gstaichi as ti

    ti.init()
    from gstaichi import kernel

    node = ast.parse("kernel", mode="eval").body
    assert ASTResolver.resolve_to(node, kernel, locals())


def test_ast_resolver_alias():
    import gstaichi

    gstaichi.init()
    node = ast.parse("gstaichi.kernel", mode="eval").body
    assert ASTResolver.resolve_to(node, gstaichi.kernel, locals())

    import gstaichi as tc

    node = ast.parse("tc.kernel", mode="eval").body
    assert ASTResolver.resolve_to(node, tc.kernel, locals())


def test_ast_resolver_chain():
    import gstaichi as ti

    ti.init()
    node = ast.parse("ti.lang.ops.atomic_add", mode="eval").body
    assert ASTResolver.resolve_to(node, ti.atomic_add, locals())


def test_ast_resolver_wrong_ti():
    import gstaichi

    gstaichi.init()
    fake_ti = namedtuple("FakeTi", ["kernel"])
    ti = fake_ti(kernel="fake")
    node = ast.parse("ti.kernel", mode="eval").body
    assert not ASTResolver.resolve_to(node, gstaichi.kernel, locals())
