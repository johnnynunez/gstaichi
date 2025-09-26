import os
import pathlib
import subprocess
import sys

import pytest

import gstaichi as ti

from tests import test_utils

RET_SUCCESS = 42


def config_debug_dump_path_child(args: list[str]) -> None:
    print("args", args)
    arch = args[0]
    tmp_path = args[1]
    specify_path = args[2].lower() == "true"
    print("tmp_path", tmp_path)
    if specify_path:
        ti.init(debug_dump_path=tmp_path, arch=getattr(ti, arch), offline_cache=False)
    else:
        ti.init(arch=getattr(ti, arch), offline_cache=False)

    @ti.kernel(pure=True)
    def k1():
        print("hello")

    k1()
    sys.exit(RET_SUCCESS)


@pytest.mark.parametrize("specify_path", [False, True])
@test_utils.test()
def test_config_debug_dump_path(specify_path: bool, tmp_path: pathlib.Path):
    if not specify_path and sys.platform == "win32":
        pytest.skip("Default debug_dump_path for windows not supported")
    assert ti.lang is not None
    arch = ti.lang.impl.current_cfg().arch.name
    cmd_line = [sys.executable, __file__, config_debug_dump_path_child.__name__, arch, str(tmp_path), str(specify_path)]
    print(cmd_line)
    env = dict(os.environ)
    env["PYTHONPATH"] = "."
    env["TI_DUMP_KERNEL_CHECKSUMS"] = "1"
    proc = subprocess.run(
        cmd_line,
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != RET_SUCCESS:
        print(" ".join(cmd_line))
        print(proc.stdout)  # needs to do this to see error messages
        print("-" * 100)
        print(proc.stderr)
    assert proc.returncode == RET_SUCCESS
    if specify_path:
        assert len(list(tmp_path.glob("*"))) > 0


# The following lines are critical for the tests to work. If they are missing, the test will
# incorrectly pass, without doing anything.
if __name__ == "__main__":
    globals()[sys.argv[1]](sys.argv[2:])
