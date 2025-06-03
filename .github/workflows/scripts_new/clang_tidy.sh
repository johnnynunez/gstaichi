#!/bin/bash

# we need to generate a special file "compile_commands.json"
# to do this, we need to run cmake with the following options:
# -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
# I'm fairly sure that we don't need to run the actual build,
# but it's not obvious to me how to do this. So, I'm just going 
# to run a full build for now, and we can FIXME this later.

sudo apt-get update
sudo apt-get install -y clang-tidy-18
git submodule update --init --recursive
pip install scikit-build
export TAICHI_CMAKE_ARGS="-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
./build.py wheel
python ./scripts/run_clang_tidy.py $PWD/taichi -clang-tidy-binary clang-tidy-18 -header-filter=$PWD/taichi -j2
