# Optional environment variables supported by setup.py:
#   {DEBUG, RELWITHDEBINFO, MINSIZEREL}
#     build the C++ gstaichi_python extension with various build types.
#
#   GSTAICHI_CMAKE_ARGS
#     extra cmake args for C++ gstaichi_python extension.

import glob
import multiprocessing
import os
import pathlib
import platform
import shutil
import subprocess
import sys
from distutils.command.clean import clean
from distutils.dir_util import remove_tree

from setuptools import find_packages
from setuptools.command.develop import develop
from skbuild import setup
from skbuild.command.egg_info import egg_info
from wheel.bdist_wheel import bdist_wheel

root_dir = os.path.dirname(os.path.abspath(__file__))

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Topic :: Software Development :: Compilers",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Games/Entertainment :: Simulation",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]


project_name = os.getenv("PROJECT_NAME", "gstaichi")

data_files = glob.glob("python/_lib/runtime/*")
print(data_files)
packages = find_packages("python")
print(packages)

# Our python package root dir is python/
package_dir = "python"


def get_version():
    try:
        from setuptools_scm import get_version as scm_get_version

        version = scm_get_version()
        # Parse version string (e.g., "1.2.3" or "1.2.3.dev0+g1234567")
        version_parts = version.split("+")[0].split(".dev")[0].split(".")
        major = version_parts[0] if len(version_parts) > 0 else "0"
        minor = version_parts[1] if len(version_parts) > 1 else "0"
        patch = version_parts[2] if len(version_parts) > 2 else "0"
    except Exception:
        major, minor, patch = "0", "0", "0"
    return major, minor, patch


def remove_tmp(gstaichi_dir):
    shutil.rmtree(os.path.join(gstaichi_dir, "assets"), ignore_errors=True)


class EggInfo(egg_info):
    def finalize_options(self, *args, **kwargs):
        if "" not in self.distribution.package_dir:
            # Issue#4975: skbuild loses the root package dir
            self.distribution.package_dir[""] = package_dir
        return super().finalize_options(*args, **kwargs)


def copy_assets():
    gstaichi_dir = os.path.join(package_dir, "gstaichi")
    remove_tmp(gstaichi_dir)

    shutil.copytree("external/assets", os.path.join(gstaichi_dir, "assets"))


class Clean(clean):
    def run(self):
        super().run()
        self.build_temp = os.path.join(root_dir, "_skbuild")
        if os.path.exists(self.build_temp):
            remove_tree(self.build_temp, dry_run=self.dry_run)
        generated_folders = (
            "bin",
            "dist",
            "python/gstaichi/assets",
            "python/gstaichi/_lib/runtime",
            "python/gstaichi/_lib/c_api",
            "gstaichi.egg-info",
            "python/gstaichi.egg-info",
            "build",
        )
        for d in generated_folders:
            if os.path.exists(d):
                remove_tree(d, dry_run=self.dry_run)
        generated_files = ["gstaichi/common/commit_hash.h", "gstaichi/common/version.h"]
        generated_files += glob.glob("gstaichi/runtime/llvm/runtime_*.bc")
        generated_files += glob.glob("python/gstaichi/_lib/core/*.so")
        generated_files += glob.glob("python/gstaichi/_lib/core/*.pyd")
        for f in generated_files:
            if os.path.exists(f):
                print(f"removing generated file {f}")
                if not self.dry_run:
                    os.remove(f)


def postprocess_stubs(stub_path: str) -> None:
    from ruamel.yaml import YAML

    stub_lines = stub_path.read_text().split("\n")
    yaml = YAML()
    with open("stub_replacements_funcs.yaml") as f:
        replacements_funcs = yaml.load(f)
    with open("stub_replacements_global.yaml") as f:
        replacements_global = yaml.load(f)
    new_stub_lines = []
    for line in stub_lines:
        func_name = line.lstrip().partition("(")[0]
        if func_name in replacements_funcs:
            print("func_name", func_name)
            print("found func_name replacing with ", replacements_funcs[func_name])
            line = replacements_funcs[func_name]
        for src, dst in replacements_global.items():
            line = line.replace(src, dst)
        new_stub_lines.append(line)
    stub_path.write_text("\n".join(new_stub_lines))
    print("stub_path", stub_path)


def generate_pybind11_stubs(build_lib: str):
    build_lib_path = pathlib.Path(build_lib).resolve()
    gstaichi_path = build_lib_path.parent.parent / "cmake-install" / "python"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(gstaichi_path) + os.pathsep + env.get("PYTHONPATH", "")

    # command that works:
    # PYTHONPATH=_skbuild/linux-x86_64-3.10/cmake-install/python pybind11-stubgen \
    #     gstaichi._lib.core.gstaichi_python --ignore-all-errors
    cmd_line = ["pybind11-stubgen", "gstaichi._lib.core.gstaichi_python", "--ignore-all-errors"]
    print(" ".join(cmd_line))
    subprocess.check_call(cmd_line, env=env)
    stub_filepath = pathlib.Path("stubs/gstaichi/_lib/core/gstaichi_python.pyi")
    postprocess_stubs(stub_filepath)

    target_filepath = build_lib_path / "gstaichi" / "_lib" / "core" / "gstaichi_python.pyi"
    py_typed_dst = build_lib_path / "gstaichi" / "_lib" / "core" / "py.typed"
    os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
    print("copying ", stub_filepath, "to", target_filepath)
    shutil.copy(stub_filepath, target_filepath)
    with open(py_typed_dst, "w"):
        pass  # creates an empty file


class DevelopWithStubs(develop):
    def run(self):
        super().run()
        build_lib = self.get_finalized_command("build_py").build_lib
        generate_pybind11_stubs(build_lib)


class BDistWheelWithStubs(bdist_wheel):
    def run(self):
        build_lib = self.get_finalized_command("build_py").build_lib
        generate_pybind11_stubs(build_lib)
        super().run()


def get_cmake_args():
    import shlex

    num_threads = os.getenv("BUILD_NUM_THREADS", multiprocessing.cpu_count())
    cmake_args = shlex.split(os.getenv("GSTAICHI_CMAKE_ARGS", "").strip())

    use_msbuild = False
    use_xcode = False

    if os.getenv("DEBUG", "0") in ("1", "ON"):
        cfg = "Debug"
    elif os.getenv("RELWITHDEBINFO", "0") in ("1", "ON"):
        cfg = "RelWithDebInfo"
    elif os.getenv("MINSIZEREL", "0") in ("1", "ON"):
        cfg = "MinSizeRel"
    else:
        cfg = None
    build_options = []
    if cfg:
        build_options.extend(["--build-type", cfg])
    if sys.platform == "win32":
        if os.getenv("GSTAICHI_USE_MSBUILD", "0") in ("1", "ON"):
            use_msbuild = True
        if use_msbuild:
            build_options.extend(["-G", "Visual Studio 17 2022"])
        else:
            build_options.extend(["-G", "Ninja", "--skip-generator-test"])
    if sys.platform == "darwin":
        if os.getenv("GSTAICHI_USE_XCODE", "0") in ("1", "ON"):
            use_xcode = True
        if use_xcode:
            build_options.extend(["-G", "Xcode", "--skip-generator-test"])
    sys.argv[2:2] = build_options

    major, minor, patch = get_version()
    cmake_args += [
        f"-DTI_VERSION_MAJOR={major}",
        f"-DTI_VERSION_MINOR={minor}",
        f"-DTI_VERSION_PATCH={patch}",
    ]

    if sys.platform == "darwin" and use_xcode:
        os.environ["SKBUILD_BUILD_OPTIONS"] = f"-jobs {num_threads}"
    elif sys.platform != "win32":
        os.environ["SKBUILD_BUILD_OPTIONS"] = f"-j{num_threads}"
    elif use_msbuild:
        # /M uses multi-threaded build (similar to -j)
        os.environ["SKBUILD_BUILD_OPTIONS"] = f"/M"
    if sys.platform == "darwin":
        if platform.machine() == "arm64":
            cmake_args += ["-DCMAKE_OSX_ARCHITECTURES=arm64"]
        else:
            cmake_args += ["-DCMAKE_OSX_ARCHITECTURES=x86_64"]
    return cmake_args


# Control files to be included in package data
BLACKLISTED_FILES = [
    "libSPIRV-Tools-shared.so",
    "libSPIRV-Tools-shared.dll",
]

WHITELISTED_FILES = [
    "libMoltenVK.dylib",
]


def cmake_install_manifest_filter(manifest_files):
    def should_include(f):
        basename = os.path.basename(f)
        if basename in WHITELISTED_FILES:
            return True
        if basename in BLACKLISTED_FILES:
            return False
        return f.endswith((".so", "pyd", ".dll", ".bc", ".h", ".dylib", ".cmake", ".hpp", ".lib"))

    return [f for f in manifest_files if should_include(f)]


def sign_development_for_apple_m1():
    """
    Apple enforces codesigning for arm64 targets even for local development
    builds. See discussion here:
        https://github.com/supercollider/supercollider/issues/5603
    """
    if sys.platform == "darwin" and platform.machine() == "arm64":
        try:
            for path in glob.glob("python/gstaichi/_lib/core/*.so"):
                print(f"signing {path}..")
                subprocess.check_call(["codesign", "--force", "--deep", "--sign", "-", path])
            for path in glob.glob("python/gstaichi/_lib/c_api/lib/*.so"):
                print(f"signing {path}..")
                subprocess.check_call(["codesign", "--force", "--deep", "--sign", "-", path])
        except:
            print("cannot sign python shared library for macos arm64 build")


copy_assets()

force_plat_name = os.getenv("GSTAICHI_FORCE_PLAT_NAME", "").strip()
if force_plat_name:
    from skbuild.constants import set_skbuild_plat_name

    set_skbuild_plat_name(force_plat_name)

setup(
    name=project_name,
    packages=packages,
    package_dir={"": package_dir},
    description="The GsTaichi Programming Language",
    author="GsTaichi developers",
    url="https://github.com/Genesis-Embedded-AI/gstaichi",
    python_requires=">=3.10,<4.0",
    setup_requires=["setuptools_scm>=6.0"],
    use_scm_version={
        "write_to": "python/gstaichi/_version.py",
        "write_to_template": "__version__ = '{version}'\n",
    },
    install_requires=[
        "numpy",
        "colorama",
        "dill",
        "rich",
        "setuptools>=68.0.0",  # Required for Python 3.12+ compatibility
        "cffi>=1.16.0",
    ],
    extras_require={
        "docs": [
            "sphinx",
            "sphinx-copybutton",
            "myst_parser",
            "sphinx-subfigure",
            "sphinxcontrib-video",
            "sphinx-togglebutton",
            "sphinx-design",
            "pydata-sphinx-theme",
            "sphinx-autoapi",
        ],
    },
    data_files=[
        (os.path.join("_lib", "runtime"), data_files),
    ],
    package_data={
        "gstaichi._lib.core": ["gstaichi_python.pyi", "py.typed"],
    },
    keywords=["graphics", "simulation"],
    license="Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)",
    license_files=("LICENSE",),
    include_package_data=True,
    classifiers=classifiers,
    cmake_args=get_cmake_args(),
    cmake_process_manifest_hook=cmake_install_manifest_filter,
    cmdclass={
        "egg_info": EggInfo,
        "clean": Clean,
        "bdist_wheel": BDistWheelWithStubs,
        "develop": DevelopWithStubs,
    },
    has_ext_modules=lambda: True,
)

sign_development_for_apple_m1()
