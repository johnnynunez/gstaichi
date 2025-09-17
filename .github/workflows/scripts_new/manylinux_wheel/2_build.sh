#!/bin/bash

set -ex

export PATH=$PWD/taichi-llvm-15.0.7-linux-x86_64/bin:$PATH

export GSTAICHI_CMAKE_ARGS="-DTI_WITH_VULKAN:BOOL=ON -DTI_WITH_CUDA:BOOL=ON -DTI_BUILD_TESTS:BOOL=ON"
./build.py wheel
