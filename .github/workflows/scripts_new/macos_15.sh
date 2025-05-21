#!/bin/bash

set -ex

echo hello from macos_15.sh
pwd
sw_vers
clang++ --version
uname -a
clang --version
# free -m
ls -la
python -V
brew install molten-vk
brew install llvm@15
./build.py --shell
