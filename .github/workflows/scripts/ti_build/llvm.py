# -*- coding: utf-8 -*-

# -- stdlib --
import os
import platform

# -- third party --
# -- own --
from .bootstrap import get_cache_home
from .cmake import cmake_args
from .dep import download_dep
from .misc import banner, get_cache_home


# -- code --
@banner("Setup LLVM")
def setup_llvm() -> None:
    """
    Download and install LLVM.
    """
    u = platform.uname()
    if (u.system, u.machine) == ("Linux", "x86_64"):
        if cmake_args.get_effective("TI_WITH_AMDGPU"):
            out = get_cache_home() / "llvm15-amdgpu-005"
            url = "https://github.com/GaleSeLee/assets/releases/download/v0.0.5/taichi-llvm-15.0.0-linux.zip"
        else:
            out = get_cache_home() / "llvm15.0.7-x86"
            url = "https://github.com/Genesis-Embodied-AI/gstaichi-sdk-builds/releases/download/llvm-15.0.7-hp-johnny-minus-mlir-202509152023/taichi-llvm-15.0.7-linux-x86_64.zip"
        download_dep(url, out, strip=1)
    elif (u.system, u.machine) in (("Linux", "arm64"), ("Linux", "aarch64")):
        out = get_cache_home() / "llvm-arm-15.0.7"
        url = "https://github.com/Genesis-Embodied-AI/gstaichi-sdk-builds/releases/download/llvm-15.0.7-hp-johnny-minus-mlir-202509152023/taichi-llvm-15.0.7-linux-aarch64.zip"
        download_dep(url, out, strip=1)
    elif (u.system, u.machine) == ("Darwin", "arm64"):
        out = get_cache_home() / "llvm15-m1-nozstd"
        url = "https://github.com/Genesis-Embodied-AI/gstaichi-sdk-builds/releases/download/llvm-15.0.7-hp-johnny-minus-mlir-202509152023/taichi-llvm-15.0.7-macos-arm64.zip"
        download_dep(url, out, strip=1)
    elif (u.system, u.machine) == ("Windows", "AMD64"):
        out = get_cache_home() / "llvm15"
        url = "https://github.com/Genesis-Embodied-AI/gstaichi-sdk-builds/releases/download/llvm-15.0.7-hp-johnny-minus-mlir-202509152023/taichi-llvm-15.0.7-windows-amd64.zip"
        download_dep(url, out, strip=0)
    else:
        raise RuntimeError(f"Unsupported platform: {u.system} {u.machine}")

    # We should use LLVM toolchains shipped with OS.
    # path_prepend('PATH', out / 'bin')
    os.environ["LLVM_DIR"] = str(out)
