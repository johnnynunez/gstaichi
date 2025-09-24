#!/bin/bash

set -ex

PLATFORM=$(uname -m)
if [ "$PLATFORM" = "x86_64" ]; then
    PLATFORM="x86_64"
    inc_subdir="x86_64-redhat-linux"
elif [ "$PLATFORM" = "aarch64" ]; then
    PLATFORM="aarch64"
    inc_subdir="aarch64-redhat-linux"
else
    echo "Unsupported architecture: $PLATFORM"
    exit 1
fi

echo "Detected platform: $PLATFORM"

# Add Taichi LLVM toolchain to PATH
export PATH="$PWD/taichi-llvm-15.0.7-linux-${PLATFORM}/bin:$PATH"

# Taichi build options
export GSTAICHI_CMAKE_ARGS="-DTI_WITH_VULKAN:BOOL=ON -DTI_WITH_CUDA:BOOL=ON -DTI_BUILD_TESTS:BOOL=ON"

# GCC toolset include paths
inc_base="/opt/rh/gcc-toolset-14/root/usr/include/c++/14"
extra="$inc_base:$inc_base/$inc_subdir:$inc_base/backward"

export CPLUS_INCLUDE_PATH="${CPLUS_INCLUDE_PATH:+$CPLUS_INCLUDE_PATH:}$extra"
export CPATH="${CPATH:+$CPATH:}/opt/rh/gcc-toolset-14/root/usr/include"

./build.py wheel
