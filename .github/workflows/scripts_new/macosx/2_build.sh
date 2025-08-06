#!/bin/bash

set -ex

export GSTAICHI_CMAKE_ARGS="-DTI_WITH_VULKAN:BOOL=OFF -DTI_WITH_METAL:BOOL=ON"
./build.py wheel
