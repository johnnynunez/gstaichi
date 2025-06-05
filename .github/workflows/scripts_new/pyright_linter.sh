#!/bin/bash

set -ex

# note: will split this up at some point

# looks like we need to first build the dll...
# easiest way to do that is to build the wheel
# at some point, we should probably have a separate wheel building thing
# that will upload to somewhere
# and other runners can use that pre-built wheel?

sudo apt update
sudo apt install -y \
    freeglut3-dev \
    libglfw3-dev \
    libglm-dev \
    libglu1-mesa-dev \
    libwayland-dev \
    libx11-xcb-dev \
    libxcb-dri3-dev \
    libxcb-ewmh-dev \
    libxcb-keysyms1-dev \
    libxcb-randr0-dev \
    libxcursor-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev \
    pybind11-dev \
    libc++-15-dev \
    libc++abi-15-dev \
    clang-15 \
    libclang-common-15-dev \
    libclang-cpp15 \
    libclang1-15 \
    cmake \
    ninja-build \
    python3-dev \
    python3-pip

pip3 install scikit-build

./build.py wheel

pip3 install dist/*.whl
python -c "import taichi as ti; ti.init(arch=ti.cpu)"


pip install pyright pybind11-stubgen

pybind11-stubgen taichi._lib.core.taichi_python --ignore-all-errors

pyright
